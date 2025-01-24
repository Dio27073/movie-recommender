# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from . import models, schemas
from .database import SessionLocal, engine
import time
from sqlalchemy import or_, desc, asc
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Movie Recommender")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "55975ac268099c9f0957d3aafb5eeae8")
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "f8ed048e")  # You'll need to get this from omdbapi.com

# API Base URLs
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
OMDB_BASE_URL = "http://www.omdbapi.com"

# Auth setup remains the same
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def fetch_imdb_data(title: str, year: int) -> dict:
    """Fetch IMDB data for a movie using OMDB API"""
    try:
        response = requests.get(
            OMDB_BASE_URL,
            params={
                "apikey": OMDB_API_KEY,
                "t": title,
                "y": year,
                "type": "movie"
            }
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "True":
                return {
                    "imdb_id": data.get("imdbID"),
                    "imdb_rating": float(data.get("imdbRating", 0)) if data.get("imdbRating") != "N/A" else None,
                    "imdb_votes": int(data.get("imdbVotes", "0").replace(",", "")) if data.get("imdbVotes") != "N/A" else None
                }
        return None
    except Exception as e:
        print(f"Error fetching IMDB data for {title} ({year}): {str(e)}")
        return None

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    if db.query(models.Movie).count() == 0:
        total_pages = 50
        processed_movies = set()
        
        for page in range(1, total_pages + 1):
            response = requests.get(
                f"{TMDB_BASE_URL}/movie/popular",
                params={
                    "api_key": TMDB_API_KEY,
                    "language": "en-US",
                    "page": page
                }
            )
            movies_data = response.json()["results"]
            
            for movie_data in movies_data:
                try:
                    if movie_data["id"] in processed_movies:
                        continue

                    movie_details = requests.get(
                        f"{TMDB_BASE_URL}/movie/{movie_data['id']}",
                        params={"api_key": TMDB_API_KEY, "language": "en-US"}
                    ).json()
                    
                    if all(key in movie_data for key in ["title", "overview", "release_date", "vote_average", "poster_path"]):
                        if not movie_data["release_date"]:
                            continue
                            
                        try:
                            release_year = int(movie_data["release_date"][:4])
                        except (ValueError, IndexError):
                            continue

                        # Fetch IMDB data
                        imdb_data = await fetch_imdb_data(movie_data["title"], release_year)
                        
                        # If we have IMDB data, use it for the rating
                        if imdb_data and imdb_data["imdb_rating"]:
                            # Convert IMDB rating (0-10) to our scale (0-5)
                            converted_rating = (imdb_data["imdb_rating"] / 2)
                        else:
                            # Fallback to TMDB rating if no IMDB rating
                            converted_rating = (movie_data["vote_average"] / 2)
                        
                        # Ensure the rating is within our constraints
                        converted_rating = min(max(converted_rating, 0), 5)
                        
                        movie = models.Movie(
                            title=movie_data["title"],
                            description=movie_data["overview"],
                            genres=",".join([genre["name"] for genre in movie_details["genres"]]),
                            release_year=release_year,
                            average_rating=converted_rating,
                            imageUrl=f"{TMDB_IMAGE_BASE_URL}{movie_data['poster_path']}",
                            imdb_id=imdb_data["imdb_id"] if imdb_data else None,
                            imdb_rating=imdb_data["imdb_rating"] if imdb_data else None,
                            imdb_votes=imdb_data["imdb_votes"] if imdb_data else None
                        )
                        db.add(movie)
                        processed_movies.add(movie_data["id"])
                except Exception as e:
                    print(f"Error processing movie {movie_data.get('title', 'Unknown')}: {str(e)}")
                    continue
            
            db.commit()
            time.sleep(0.5)  # Rate limiting
    
    db.close()

@app.get("/movies/", response_model=schemas.PaginatedMovieResponse)
def get_movies(
    page: int = 1, 
    per_page: int = 12, 
    genres: str = None,
    min_year: int = None,
    max_year: int = None,
    min_rating: float = None,
    max_rating: float = None, 
    sort: str = "imdb_rating_desc",  # Changed default sort to IMDB rating
    db: Session = Depends(get_db)
    ):
    
    offset = (page - 1) * per_page
    query = db.query(models.Movie)
    
    if genres:
        genre_list = genres.split(',')
        query = query.filter(
            or_(*[models.Movie.genres.like(f"%{genre}%") for genre in genre_list])
        )
    
    if min_year:
        query = query.filter(models.Movie.release_year >= min_year)
    if max_year:
        query = query.filter(models.Movie.release_year <= max_year)
    
    if min_rating is not None:
        query = query.filter(models.Movie.imdb_rating >= min_rating)
    if max_rating is not None:
        query = query.filter(models.Movie.imdb_rating <= max_rating)
    
    # Updated sorting options to include IMDB ratings
    if sort:
        if sort == "imdb_rating_desc":
            query = query.order_by(desc(models.Movie.imdb_rating))
        elif sort == "imdb_rating_asc":
            query = query.order_by(asc(models.Movie.imdb_rating))
        elif sort == "release_date_desc":
            query = query.order_by(desc(models.Movie.release_year))
        elif sort == "release_date_asc":
            query = query.order_by(asc(models.Movie.release_year))
        elif sort == "title_asc":
            query = query.order_by(asc(models.Movie.title))
        elif sort == "title_desc":
            query = query.order_by(desc(models.Movie.title))
    
    total_movies = query.count()
    total_pages = (total_movies + per_page - 1) // per_page
    movies = query.offset(offset).limit(per_page).all()
    
    movie_list = []
    for db_movie in movies:
        movie_dict = {
            "id": db_movie.id,
            "title": db_movie.title,
            "description": db_movie.description,
            "release_year": db_movie.release_year,
            "average_rating": db_movie.average_rating,
            "imageUrl": db_movie.imageUrl,
            "genres": db_movie.genres.split(",") if db_movie.genres else [],
            "imdb_id": db_movie.imdb_id,
            "imdb_rating": db_movie.imdb_rating,
            "imdb_votes": db_movie.imdb_votes
        }
        movie_list.append(movie_dict)
    
    return {
        "items": movie_list,
        "total": total_movies,
        "page": page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

@app.post("/movies/", response_model=schemas.Movie)
async def create_movie(movie: schemas.MovieCreate, db: Session = Depends(get_db)):
    # Fetch IMDB data for the movie
    imdb_data = await fetch_imdb_data(movie.title, movie.release_year)
    
    # Convert the genres list to a comma-separated string for storage
    movie_data = movie.model_dump()
    movie_data["genres"] = ",".join(movie_data["genres"]) if movie_data["genres"] else ""
    
    # Add IMDB data if available
    if imdb_data:
        movie_data["imdb_id"] = imdb_data["imdb_id"]
        movie_data["imdb_rating"] = imdb_data["imdb_rating"]
        movie_data["imdb_votes"] = imdb_data["imdb_votes"]
        
        # Update average_rating based on IMDB rating
        if imdb_data["imdb_rating"]:
            movie_data["average_rating"] = imdb_data["imdb_rating"] / 2  # Convert 10-point to 5-point scale
    
    db_movie = models.Movie(**movie_data)
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    
    # Convert back to the format expected by the schema
    return {
        "id": db_movie.id,
        "title": db_movie.title,
        "description": db_movie.description,
        "release_year": db_movie.release_year,
        "average_rating": db_movie.average_rating,
        "imageUrl": db_movie.imageUrl,
        "genres": db_movie.genres.split(",") if db_movie.genres else [],
        "imdb_id": db_movie.imdb_id,
        "imdb_rating": db_movie.imdb_rating,
        "imdb_votes": db_movie.imdb_votes
    }