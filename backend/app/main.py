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

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Movie Recommender")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT settings
SECRET_KEY = "your-secret-key"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import requests

TMDB_API_KEY = "55975ac268099c9f0957d3aafb5eeae8"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    if db.query(models.Movie).count() == 0:
        # Fetch multiple pages of popular movies from TMDB
        total_pages = 50  # This will give us about 400 movies
        processed_movies = set()  # Keep track of movies we've already added
        
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
                    # Skip if we've already processed this movie
                    if movie_data["id"] in processed_movies:
                        continue

                    # Get additional movie details
                    movie_details = requests.get(
                        f"{TMDB_BASE_URL}/movie/{movie_data['id']}",
                        params={"api_key": TMDB_API_KEY, "language": "en-US"}
                    ).json()
                    
                    # Only add movies with complete data
                    if all(key in movie_data for key in ["title", "overview", "release_date", "vote_average", "poster_path"]):
                        # Add validation for release_date
                        if not movie_data["release_date"]:
                            print(f"Skipping movie {movie_data['title']}: Missing release date")
                            continue
                            
                        try:
                            release_year = int(movie_data["release_date"][:4])
                        except (ValueError, IndexError):
                            print(f"Skipping movie {movie_data['title']}: Invalid release date format")
                            continue

                        # Convert TMDB rating (0-10) to our scale (0-5)
                        converted_rating = (movie_data["vote_average"] / 2)
                        # Ensure the rating is within our constraints
                        converted_rating = min(max(converted_rating, 0), 5)
                        
                        movie = models.Movie(
                            title=movie_data["title"],
                            description=movie_data["overview"],
                            genres=",".join([genre["name"] for genre in movie_details["genres"]]),
                            release_year=release_year,
                            average_rating=converted_rating,
                            imageUrl=f"{TMDB_IMAGE_BASE_URL}{movie_data['poster_path']}"
                        )
                        db.add(movie)
                        # Mark this movie as processed
                        processed_movies.add(movie_data["id"])
                except Exception as e:
                    print(f"Error processing movie {movie_data.get('title', 'Unknown')}: {str(e)}")
                    continue
            
            # Commit after each page to avoid losing everything if there's an error
            db.commit()
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
    
    db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/movies/", response_model=schemas.PaginatedMovieResponse)
def get_movies(
    page: int = 1, 
    per_page: int = 12, 
    genres: str = None,
    min_year: int = None,
    max_year: int = None,
    min_rating: float = None,
    sort: str = "release_date_desc",  # Default sort
    db: Session = Depends(get_db)
    ):
    
    # Calculate offset based on page number and items per page
    offset = (page - 1) * per_page
    
    # Start with base query
    query = db.query(models.Movie)
    
    # Apply genre filtering if genres parameter is provided
    if genres:
        genre_list = genres.split(',')
        query = query.filter(
            or_(*[
                models.Movie.genres.like(f"%{genre}%")
                for genre in genre_list
            ])
        )
    
    # Apply year range filter
    if min_year:
        query = query.filter(models.Movie.release_year >= min_year)
    if max_year:
        query = query.filter(models.Movie.release_year <= max_year)
    
    # Apply rating filter
    if min_rating is not None:
        query = query.filter(models.Movie.average_rating >= min_rating)
    
    # Apply sorting
    if sort:
        if sort == "release_date_desc":
            query = query.order_by(desc(models.Movie.release_year))
        elif sort == "release_date_asc":
            query = query.order_by(asc(models.Movie.release_year))
        elif sort == "rating_desc":
            query = query.order_by(desc(models.Movie.average_rating))
        elif sort == "rating_asc":
            query = query.order_by(asc(models.Movie.average_rating))
        elif sort == "title_asc":
            query = query.order_by(asc(models.Movie.title))
        elif sort == "title_desc":
            query = query.order_by(desc(models.Movie.title))
    
    # Get total number of movies for pagination info
    total_movies = query.count()
    total_pages = (total_movies + per_page - 1) // per_page
    
    # Get movies for the current page
    movies = query.offset(offset).limit(per_page).all()
    
    # Convert each movie object to a compatible format
    movie_list = []
    for db_movie in movies:
        movie_dict = {
            "id": db_movie.id,
            "title": db_movie.title,
            "description": db_movie.description,
            "release_year": db_movie.release_year,
            "average_rating": db_movie.average_rating,
            "imageUrl": db_movie.imageUrl,
            "genres": db_movie.genres.split(",") if db_movie.genres else []
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
def create_movie(movie: schemas.MovieCreate, db: Session = Depends(get_db)):
    # Convert the genres list to a comma-separated string for storage
    movie_data = movie.model_dump()
    movie_data["genres"] = ",".join(movie_data["genres"]) if movie_data["genres"] else ""
    
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
        "genres": db_movie.genres.split(",") if db_movie.genres else []
    }

@app.post("/rate/")
def rate_movie(rating: schemas.Rating, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    movie = db.query(models.Movie).filter(models.Movie.id == rating.movie_id).first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Update movie's average rating (simplified version)
    movie.average_rating = rating.rating
    db.commit()
    
    return {"message": "Rating updated successfully"}
