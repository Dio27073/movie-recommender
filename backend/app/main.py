# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import time
from sqlalchemy import or_, desc, asc
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

from . import models, schemas
from .database import SessionLocal, engine, get_db
from .recommender.engine import router as recommender_router, MovieRecommender
from .auth_utils import get_current_active_user
from .routers.auth import router as auth_router

# Load environment variables
load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Movie Recommender")

# Initialize recommender system
recommender = MovieRecommender()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]  # Added this line
)

# Include routers
app.include_router(
    recommender_router,
    prefix="/api/recommender",
    tags=["recommender"]
)
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)

# API Keys
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "55975ac268099c9f0957d3aafb5eeae8")
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "f8ed048e")  # You'll need to get this from omdbapi.com

# API Base URLs
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
OMDB_BASE_URL = "http://www.omdbapi.com"

# Password hashing configuration


async def fetch_imdb_data(title: str, year: int, retry_count: int = 0) -> dict:
    """Fetch IMDB data for a movie using OMDB API with exponential backoff"""
    max_retries = 3
    base_delay = 0.5  # Start with 1 second delay
    
    try:
        if retry_count > 0:
            # Exponential backoff: 1s, 2s, 4s
            wait_time = base_delay * (2 ** (retry_count - 1))
            print(f"Retry #{retry_count} for {title}. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            time.sleep(base_delay)  # Regular delay for first attempt
        
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
            
            # Check for rate limit error
            if data.get("Response") == "False" and "limit reached" in data.get("Error", "").lower():
                if retry_count < max_retries:
                    print(f"Rate limit hit for {title}. Attempting retry #{retry_count + 1}")
                    return await fetch_imdb_data(title, year, retry_count + 1)
                else:
                    print(f"Max retries reached for {title}. Skipping IMDB data.")
                    return None
            
            if data.get("Response") == "True":
                return {
                    "imdb_id": data.get("imdbID"),
                    "imdb_rating": float(data.get("imdbRating", 0)) if data.get("imdbRating") != "N/A" else None,
                    "imdb_votes": int(data.get("imdbVotes", "0").replace(",", "")) if data.get("imdbVotes") != "N/A" else None
                }
            
            print(f"No IMDB data found for {title} (not a rate limit issue)")
            return None
            
    except Exception as e:
        print(f"Error fetching IMDB data for {title} ({year}): {str(e)}")
        if retry_count < max_retries:
            return await fetch_imdb_data(title, year, retry_count + 1)
        return None
    
async def fetch_movie_trailer(tmdb_id: int) -> Optional[str]:
    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/videos",
            params={
                "api_key": TMDB_API_KEY,
                "language": "en-US"
            }
        )
        if response.status_code == 200:
            videos = response.json().get("results", [])
            # Look for official trailers
            trailer = next(
                (
                    video for video in videos 
                    if video["type"].lower() == "trailer" 
                    and video["site"].lower() == "youtube"
                    and video["official"]
                ),
                None
            )
            if trailer:
                return f"https://www.youtube.com/watch?v={trailer['key']}"
    except Exception as e:
        print(f"Error fetching trailer: {str(e)}")
    return None

"""Fetch cast and crew data for a movie using TMDB API."""
async def fetch_movie_cast_crew(tmdb_id: int) -> dict:
    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits",
            params={"api_key": TMDB_API_KEY, "language": "en-US"}
        )
        if response.status_code == 200:
            credits = response.json()
            cast = [actor["name"] for actor in credits.get("cast", [])[:5]]  # Top 5 cast members
            crew = [member["name"] for member in credits.get("crew", []) if member["job"] == "Director"]  # Directors
            return {"cast": cast, "crew": crew}
    except Exception as e:
        print(f"Error fetching cast/crew for movie {tmdb_id}: {str(e)}")
    return {"cast": [], "crew": []}

# User registration endpoint
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        # Initialize movies if database is empty
        if db.query(models.Movie).count() == 0:
            total_pages = 200
            processed_movies = set()
            total_processed = 0
            total_skipped = 0

            print(f"Starting movie import process for {total_pages} pages...")

            for page in range(1, total_pages + 1):
                try:
                    print(f"\nProcessing page {page}/{total_pages}")
                    response = requests.get(
                        f"{TMDB_BASE_URL}/movie/popular",
                        params={
                            "api_key": TMDB_API_KEY,
                            "language": "en-US",
                            "page": page
                        }
                    )
                    
                    if response.status_code == 429:  # Too Many Requests
                        print(f"Rate limit hit on page {page}. Waiting 10 seconds...")
                        time.sleep(10)
                        continue
                        
                    if response.status_code != 200:
                        print(f"Error on page {page}: Status code {response.status_code}")
                        continue

                    movies_data = response.json().get("results", [])
                    if not movies_data:
                        print(f"No movies found on page {page}")
                        continue

                    page_processed = 0
                    page_skipped = 0
                    
                    for movie_data in movies_data:
                        try:
                            if movie_data["id"] in processed_movies:
                                print(f"Skipped duplicate movie: {movie_data.get('title')}")
                                page_skipped += 1
                                continue

                            if not all(key in movie_data for key in ["title", "overview", "release_date", "vote_average", "poster_path"]):
                                print(f"Skipped movie due to missing data: {movie_data.get('title')}")
                                page_skipped += 1
                                continue

                            if not movie_data["release_date"]:
                                print(f"Skipped movie due to missing release date: {movie_data.get('title')}")
                                page_skipped += 1
                                continue

                            # Get detailed movie info
                            details_response = requests.get(
                                f"{TMDB_BASE_URL}/movie/{movie_data['id']}",
                                params={"api_key": TMDB_API_KEY, "language": "en-US"}
                            )
                            
                            if details_response.status_code != 200:
                                print(f"Failed to get details for movie {movie_data.get('title')}: Status {details_response.status_code}")
                                page_skipped += 1
                                continue

                            movie_details = details_response.json()
                                
                            try:
                                release_year = int(movie_data["release_date"][:4])
                            except (ValueError, IndexError):
                                print(f"Invalid release date for movie {movie_data.get('title')}")
                                page_skipped += 1
                                continue

                            # Fetch IMDB data
                            imdb_data = await fetch_imdb_data(movie_data["title"], release_year)
                            if not imdb_data:
                                print(f"No IMDB data found for movie {movie_data.get('title')}")
                            
                            # Fetch cast and crew data
                            cast_crew_data = await fetch_movie_cast_crew(movie_data["id"])
                            if not cast_crew_data["cast"] and not cast_crew_data["crew"]:
                                print(f"No cast/crew data found for movie {movie_data.get('title')}")

                            # Calculate rating
                            if imdb_data and imdb_data["imdb_rating"]:
                                converted_rating = (imdb_data["imdb_rating"] / 2)
                            else:
                                converted_rating = (movie_data["vote_average"] / 2)
                            
                            converted_rating = min(max(converted_rating, 0), 5)
                            
                            # Fetch trailer URL
                            trailer_url = await fetch_movie_trailer(movie_data["id"])
                            if not trailer_url:
                                print(f"No trailer found for movie {movie_data.get('title')}")

                            # Initialize popularity metrics
                            popularity_score = movie_data.get("popularity", 0)
                            
                            # Create movie record
                            movie = models.Movie(
                                title=movie_data["title"],
                                description=movie_data["overview"],
                                genres=",".join([genre["name"] for genre in movie_details["genres"]]),
                                release_year=release_year,
                                average_rating=converted_rating,
                                imageUrl=f"{TMDB_IMAGE_BASE_URL}{movie_data['poster_path']}",
                                imdb_id=imdb_data["imdb_id"] if imdb_data else None,
                                imdb_rating=imdb_data["imdb_rating"] if imdb_data else None,
                                imdb_votes=imdb_data["imdb_votes"] if imdb_data else None,
                                trailer_url=trailer_url,
                                cast=",".join(cast_crew_data["cast"]),
                                crew=",".join(cast_crew_data["crew"]),
                                popularity_score=popularity_score,
                                view_count=0,
                                completion_rate=0.0,
                                rating_count=0,
                                keywords=movie_details.get("tagline", "")
                            )
                            db.add(movie)
                            processed_movies.add(movie_data["id"])
                            page_processed += 1
                            total_processed += 1
                            print(f"Successfully processed: {movie_data.get('title')}")

                        except Exception as e:
                            print(f"Error processing movie {movie_data.get('title', 'Unknown')}: {str(e)}")
                            page_skipped += 1
                            continue

                    print(f"Page {page} summary: Processed {page_processed}, Skipped {page_skipped}")
                    total_skipped += page_skipped
                    
                    # Commit after each page
                    try:
                        db.commit()
                    except Exception as e:
                        print(f"Error committing page {page}: {str(e)}")
                        db.rollback()
                        continue

                    # Rate limiting
                    time.sleep(0.5)

                except Exception as e:
                    print(f"Error processing page {page}: {str(e)}")
                    continue

            print(f"\nImport process completed:")
            print(f"Total movies processed: {total_processed}")
            print(f"Total movies skipped: {total_skipped}")
            print(f"Total unique movies: {len(processed_movies)}")
        
        # Initialize recommendation system
        print("\nInitializing recommendation system...")
        
        # Prepare movie data for content-based filtering
        movies = db.query(models.Movie).all()
        movies_data = [
            {
                "id": m.id,
                "title": m.title,
                "genres": m.genres,
                "director": m.crew.split(",")[0] if m.crew else "",
                "cast": m.cast,
                "description": m.description,
                "keywords": m.keywords
            } for m in movies
        ]
        
        print(f"Preparing content features for {len(movies_data)} movies...")
        recommender.prepare_content_features(movies_data)
        
        # Initialize collaborative filtering with viewing history
        viewing_history = db.query(models.ViewingHistory).all()
        if viewing_history:
            print(f"Training collaborative model with {len(viewing_history)} viewing records...")
            viewing_data = [
                {
                    "user_id": vh.user_id,
                    "movie_id": vh.movie_id,
                    "rating": 5.0 if vh.completed else (vh.watch_duration or 0) / 7200  # Convert duration to rating
                } for vh in viewing_history
            ]
            recommender.train_collaborative_model(viewing_data)
        else:
            print("No viewing history found for collaborative filtering")
        
        print("Recommendation system initialization completed successfully")
        
    except Exception as e:
        print(f"Error during startup: {str(e)}")
        raise
    finally:
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
    sort: str = "imdb_rating_desc",
    cast_crew: str = None,  # Add this parameter
    search: str = None,     # Add this for completeness
    search_type: str = None,# Add this for completeness
    db: Session = Depends(get_db)
    ):
    
    offset = (page - 1) * per_page
    query = db.query(models.Movie)
    
    # Add cast/crew filtering
    if cast_crew:
        query = query.filter(
            or_(
                models.Movie.cast.ilike(f"%{cast_crew}%"),
                models.Movie.crew.ilike(f"%{cast_crew}%")
            )
        )

    if search and search_type:
        if search_type == "cast_crew":
            query = query.filter(
                or_(
                    models.Movie.cast.ilike(f"%{search}%"),
                    models.Movie.crew.ilike(f"%{search}%")
                )
            )
        elif search_type == "title":
            query = query.filter(models.Movie.title.ilike(f"%{search}%"))
            
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
            "imdb_votes": db_movie.imdb_votes,
            "trailer_url": db_movie.trailer_url,
            "cast": db_movie.cast.split(",") if db_movie.cast else [],
            "crew": db_movie.crew.split(",") if db_movie.crew else []
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

@app.get("/movies/search/", response_model=schemas.PaginatedMovieResponse)
def search_movies_by_cast_crew(
    query: str,
    page: int = 1,
    per_page: int = 12,
    db: Session = Depends(get_db),
    search_type: str = "cast_crew" # Add search type parameter
):
    """Search movies by cast or crew members."""
    offset = (page - 1) * per_page
    query = query.lower()
    
    # Search for movies where cast or crew contains the query
    db_query = db.query(models.Movie)
    if search_type == "cast_crew": # Filter by cast or crew
        # Search for movies where cast OR crew contains the query
        db_query = db_query.filter(
            or_(
                models.Movie.cast.ilike(f"%{query}%"), # Contains the name
                models.Movie.crew.ilike(f"%{query}%")
            )
        )
    elif search_type == "title": # Filter by title
        db_query = db_query.filter(models.Movie.title.ilike(f"%{query}%"))
    
    total_movies = db_query.count()
    total_pages = (total_movies + per_page - 1) // per_page
    movies = db_query.offset(offset).limit(per_page).all()
    
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
            "imdb_votes": db_movie.imdb_votes,
            "trailer_url": db_movie.trailer_url,
            "cast": db_movie.cast.split(",") if db_movie.cast else [],  # Return cast as a list
            "crew": db_movie.crew.split(",") if db_movie.crew else []  # Return crew as a list
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

# Add new endpoint for personalized recommendations
@app.get("/movies/recommended/", response_model=schemas.PaginatedMovieResponse)
async def get_recommended_movies(
    current_user: models.User = Depends(get_current_active_user),
    page: int = 1,
    per_page: int = 12,
    db: Session = Depends(get_db)
):
    # Get user's viewing history
    recently_viewed = db.query(models.ViewingHistory)\
        .filter(models.ViewingHistory.user_id == current_user.id)\
        .order_by(desc(models.ViewingHistory.watched_at))\
        .limit(10)\
        .all()
    
    recently_viewed_ids = [vh.movie_id for vh in recently_viewed]
    
    # Get recommendations
    recommended_ids = recommender.get_hybrid_recommendations(
        user_id=current_user.id,
        recently_viewed=recently_viewed_ids
    )
    
    # Paginate recommendations
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_recommended_ids = recommended_ids[start_idx:end_idx]
    
    # Fetch movie details
    recommended_movies = db.query(models.Movie)\
        .filter(models.Movie.id.in_(page_recommended_ids))\
        .all()
    
    # Format response
    total_recommendations = len(recommended_ids)
    total_pages = (total_recommendations + per_page - 1) // per_page
    
    movie_list = []
    for db_movie in recommended_movies:
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
            "imdb_votes": db_movie.imdb_votes,
            "trailer_url": db_movie.trailer_url,
            "cast": db_movie.cast.split(",") if db_movie.cast else [],
            "crew": db_movie.crew.split(",") if db_movie.crew else []
        }
        movie_list.append(movie_dict)
    
    return {
        "items": movie_list,
        "total": total_recommendations,
        "page": page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

# Add endpoint to record viewing history
@app.post("/movies/{movie_id}/view")
async def record_movie_view(
    movie_id: int,
    completed: bool = False,
    watch_duration: Optional[int] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if movie exists
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Record viewing history
    view_history = models.ViewingHistory(
        user_id=current_user.id,
        movie_id=movie_id,
        completed=completed,
        watch_duration=watch_duration
    )
    db.add(view_history)
    
    # Update movie popularity score
    movie.view_count += 1
    if completed:
        movie.completion_rate = (
            (movie.completion_rate * (movie.view_count - 1) + 1) / movie.view_count
        )
    
    # Commit changes
    db.commit()
    
    return {"status": "success", "message": "View recorded successfully"}

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
    
    # Fetch trailer URL
    try:
        tmdb_response = requests.get(
            f"{TMDB_BASE_URL}/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": movie.title,
                "year": movie.release_year
            }
        )
        if tmdb_response.status_code == 200:
            results = tmdb_response.json().get("results", [])
            if results:
                tmdb_id = results[0]["id"]
                trailer_url = await fetch_movie_trailer(tmdb_id)
                movie_data["trailer_url"] = trailer_url
    except Exception as e:
        print(f"Error fetching trailer for {movie.title}: {str(e)}")
    
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
        "imdb_votes": db_movie.imdb_votes,
        "trailer_url": db_movie.trailer_url
    }