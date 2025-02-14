# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import time
from sqlalchemy import or_, desc, asc
import requests
import uvicorn
import os
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError  
from pydantic import BaseModel  

class LoadMoviesRequest(BaseModel):
    start_page: int
    num_pages: int = 10

from . import models, schemas
from .database import SessionLocal, engine, Base, get_db
from .recommender.engine import router as recommender_router, MovieRecommender
from .auth_utils import get_current_active_user
from .routers.auth import router as auth_router

# Load environment variables
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Movie Recommender")

# Initialize recommender system
recommender = MovieRecommender()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Vite dev server
        "http://localhost:8000",    # FastAPI server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "https://movie-recommender-two-zeta.vercel.app",
        "https://movie-recommender-git-main-dio27073s-projects.vercel.app",
        "https://movie-recommender-mpu1s9qgh-dio27073s-projects.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Added this line
    allow_origin_regex="https://.*\.vercel\.app/?.*"  # This will allow all vercel.app subdomains
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

# API Base URLs
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
OMDB_BASE_URL = "http://www.omdbapi.com"
LAST_PROCESSED_PAGE = 0

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

async def fetch_streaming_platforms(tmdb_id: int, region: str = "US") -> list[str]:
    """Fetch accurate streaming platform data from TMDB."""
    try:
        # Add rate limiting
        time.sleep(0.25)  # 250ms delay between requests
        
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/watch/providers",
            params={"api_key": TMDB_API_KEY}
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", {})
            region_data = results.get(region, {})
            
            # Get flatrate (subscription) streaming services
            streaming_platforms = []
            if "flatrate" in region_data:
                for provider in region_data["flatrate"]:
                    provider_name = provider.get("provider_name")
                    # Map TMDB provider names to your platform names
                    platform_mapping = {
                        "Netflix": "Netflix",
                        "Amazon Prime Video": "Prime Video",
                        "Disney Plus": "Disney+",
                        "Hulu": "Hulu",
                        "HBO Max": "HBO Max",
                        "Max": "HBO Max",  # Add this line
                        "Apple TV Plus": "Apple TV+",
                        "Peacock": "Peacock"
                    }
                    if provider_name in platform_mapping:
                        streaming_platforms.append(platform_mapping[provider_name])
            
            return list(set(streaming_platforms))  # Remove duplicates
            
    except Exception as e:
        print(f"Error fetching streaming platforms for movie {tmdb_id}: {str(e)}")
        return []
    
async def load_initial_movies(db: Session, pages: int = 10):
    """Load initial set of movies during startup"""
    # Get last processed page from database
    last_page_config = db.query(models.Configuration).filter(
        models.Configuration.key == "last_processed_page"
    ).first()
    
    last_page = int(last_page_config.value) if last_page_config else 0
    start_page = last_page + 1
    end_page = start_page + pages - 1

    print(f"Starting movie import process from page {start_page} to {end_page}...")
    processed_movies = set()
    total_processed = 0
    total_skipped = 0
    page_failures = 0
    max_page_failures = 5

    for page in range(start_page, end_page + 1):
        page_processed = 0
        page_skipped = 0
        
        try:
            print(f"\nProcessing page {page}")
            
            # Add rate limiting between pages
            time.sleep(1)
            
            response = requests.get(
                f"{TMDB_BASE_URL}/movie/popular",
                params={
                    "api_key": TMDB_API_KEY,
                    "language": "en-US",
                    "page": page
                },
                timeout=10
            )
            
            if response.status_code == 429:
                print(f"Rate limit hit on page {page}. Waiting 10 seconds...")
                time.sleep(10)
                page_failures += 1
                if page_failures >= max_page_failures:
                    print("Too many consecutive failures. Aborting import.")
                    break
                continue
                
            if response.status_code != 200:
                print(f"Error on page {page}: Status code {response.status_code}")
                page_failures += 1
                if page_failures >= max_page_failures:
                    print("Too many consecutive failures. Aborting import.")
                    break
                continue

            movies_data = response.json().get("results", [])
            if not movies_data:
                print(f"No movies found on page {page}")
                continue

            page_failures = 0
            
            for movie_data in movies_data:
                try:
                    if not all(key in movie_data for key in ["title", "release_date", "id"]):
                        print(f"Skipping movie with missing required data: {movie_data.get('title', 'Unknown')}")
                        page_skipped += 1
                        continue

                    if movie_data["id"] in processed_movies:
                        print(f"Skipping duplicate movie: {movie_data.get('title')}")
                        page_skipped += 1
                        continue

                    try:
                        release_year = int(movie_data["release_date"][:4])
                    except (ValueError, IndexError):
                        print(f"Invalid release date for movie {movie_data.get('title')}")
                        page_skipped += 1
                        continue

                    # Get IMDB data with retry logic
                    imdb_data = await fetch_imdb_data(movie_data["title"], release_year)
                    
                    if imdb_data and imdb_data["imdb_id"]:
                        existing_movie = db.query(models.Movie).filter(
                            models.Movie.imdb_id == imdb_data["imdb_id"]
                        ).first()
                        
                        if existing_movie:
                            print(f"Movie already exists with IMDB ID {imdb_data['imdb_id']}")
                            page_skipped += 1
                            continue

                    # Get detailed movie info
                    details_response = requests.get(
                        f"{TMDB_BASE_URL}/movie/{movie_data['id']}",
                        params={"api_key": TMDB_API_KEY, "language": "en-US"},
                        timeout=10
                    )
                    
                    if details_response.status_code != 200:
                        print(f"Failed to get details for movie {movie_data.get('title')}")
                        page_skipped += 1
                        continue

                    movie_details = details_response.json()
                    
                    # Fetch additional data
                    cast_crew_data = await fetch_movie_cast_crew(movie_data["id"])
                    trailer_url = await fetch_movie_trailer(movie_data["id"])
                    streaming_platforms = await fetch_streaming_platforms(movie_data["id"])
                    
                    # Calculate rating
                    converted_rating = (
                        (imdb_data["imdb_rating"] / 2) if imdb_data and imdb_data["imdb_rating"]
                        else (movie_data["vote_average"] / 2)
                    )
                    converted_rating = min(max(converted_rating, 0), 5)
                    
                    # Process genres and mood tags
                    genres = [genre["name"] for genre in movie_details["genres"]]
                    mood_tags = []
                    genre_mood_mapping = {
                        "Comedy": ["Funny", "Feel-Good"],
                        "Horror": ["Dark", "Intense"],
                        "Romance": ["Romantic", "Feel-Good"],
                        "Drama": ["Thought-Provoking", "Intense"],
                        "Action": ["Intense", "Exciting"],
                        "Family": ["Feel-Good", "Relaxing"],
                        "Adventure": ["Exciting", "Feel-Good"],
                        "Animation": ["Feel-Good", "Relaxing"],
                        "Crime": ["Dark", "Intense"],
                        "Documentary": ["Thought-Provoking", "Relaxing"],
                        "Fantasy": ["Feel-Good", "Exciting"],
                        "Science Fiction": ["Thought-Provoking", "Exciting"],
                        "Thriller": ["Intense", "Dark"],
                        "Mystery": ["Thought-Provoking", "Intense"]
                    }

                    for genre in genres:
                        if genre in genre_mood_mapping:
                            mood_tags.extend(genre_mood_mapping[genre])
                    mood_tags = list(set(mood_tags))

                    # Create movie record
                    movie = models.Movie(
                        title=movie_data["title"],
                        description=movie_data["overview"],
                        genres=",".join(genres),
                        release_year=release_year,
                        release_date=datetime.strptime(movie_data["release_date"], '%Y-%m-%d'),
                        average_rating=converted_rating,
                        imageurl=f"{TMDB_IMAGE_BASE_URL}{movie_data['poster_path']}" if movie_data.get('poster_path') else None,
                        imdb_id=imdb_data["imdb_id"] if imdb_data else None,
                        imdb_rating=imdb_data["imdb_rating"] if imdb_data else None,
                        imdb_votes=imdb_data["imdb_votes"] if imdb_data else None,
                        trailer_url=trailer_url,
                        cast=",".join(cast_crew_data["cast"]) if cast_crew_data["cast"] else None,
                        crew=",".join(cast_crew_data["crew"]) if cast_crew_data["crew"] else None,
                        popularity_score=movie_data.get("popularity", 0),
                        view_count=0,
                        completion_rate=0.0,
                        rating_count=0,
                        keywords=movie_details.get("tagline", ""),
                        mood_tags=",".join(mood_tags) if mood_tags else None,
                        streaming_platforms=",".join(streaming_platforms) if streaming_platforms else None
                    )

                    try:
                        db.add(movie)
                        db.flush()
                        processed_movies.add(movie_data["id"])
                        page_processed += 1
                        total_processed += 1
                        print(f"Successfully processed: {movie_data.get('title')}")
                    except IntegrityError as e:
                        db.rollback()
                        print(f"Duplicate movie detected: {str(e)}")
                        page_skipped += 1
                        continue

                except Exception as e:
                    print(f"Error processing movie {movie_data.get('title', 'Unknown')}: {str(e)}")
                    page_skipped += 1
                    continue

            if page_processed > 0:  # Only update if we successfully processed some movies
                # Update last processed page in database
                if last_page_config:
                    last_page_config.value = str(page)
                else:
                    last_page_config = models.Configuration(
                        key="last_processed_page",
                        value=str(page)
                    )
                    db.add(last_page_config)
                
                print(f"Updated last processed page to {page}")

            print(f"Page {page} summary: Processed {page_processed}, Skipped {page_skipped}")
            total_skipped += page_skipped
            
            try:
                db.commit()
                print(f"Successfully committed page {page}")
            except Exception as e:
                print(f"Error committing page {page}: {str(e)}")
                db.rollback()
                continue

            time.sleep(0.5)

        except Exception as e:
            print(f"Error processing page {page}: {str(e)}")
            continue

    print(f"\nImport process completed:")
    print(f"Total movies processed: {total_processed}")
    print(f"Total movies skipped: {total_skipped}")
    print(f"Last processed page: {last_page_config.value if last_page_config else 'None'}")
    return total_processed, total_skipped

@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    try:
        # Test query
        result = db.execute(text("SELECT COUNT(*) FROM movies")).scalar()
        return {"status": "ok", "movie_count": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection test failed: {str(e)}"
        )
    
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )
    
@app.on_event("startup")
async def startup_event():
    retries = 5
    db = None
    for i in range(retries):
        try:
            db = SessionLocal()
            # Test the connection with proper SQL text
            db.execute(text("SELECT 1"))
            print("Successfully connected to database")
            break
        except Exception as e:
            if i == retries - 1:
                print(f"Failed to initialize database after {retries} attempts: {str(e)}")
                raise
            print(f"Database connection attempt {i + 1} failed, retrying in 5 seconds...")
            time.sleep(5)
    
    try:
        # Initialize movies if database is empty
        movie_count = db.query(models.Movie).count()
        print(f"Current movie count in database: {movie_count}")
        
        if movie_count == 0:
            # Only load first 10 pages during startup
            await load_initial_movies(db, pages=10)
            
    except Exception as e:
        print(f"Error during startup: {str(e)}")
        raise
    finally:
        if db:
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
    cast_crew: str = None,  
    search: str = None,     
    search_type: str = None,
    content_rating: str = None,
    mood_tags: str = None,
    streaming_platforms: str = None,
    release_date_lte: str = None,  # Add this parameter
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
    
    # Content Rating filter
    if content_rating:
        content_rating_list = content_rating.split(',')
        query = query.filter(models.Movie.content_rating.in_(content_rating_list))
    
    # Mood Tags filter
    if mood_tags:
        mood_list = mood_tags.split(',')
        query = query.filter(
            or_(*[models.Movie.mood_tags.like(f"%{mood}%") for mood in mood_list])
        )
    
    # Streaming Platforms filter
    if streaming_platforms:
        platform_list = streaming_platforms.split(',')
        query = query.filter(
            or_(*[models.Movie.streaming_platforms.like(f"%{platform}%") for platform in platform_list])
        )
    if sort:
        if sort == "imdb_rating_desc":
            query = query.order_by(desc(models.Movie.imdb_rating))
        elif sort == "imdb_rating_asc":
            query = query.order_by(asc(models.Movie.imdb_rating))
        elif sort == "release_date_desc":
            query = query.order_by(desc(models.Movie.release_date))
        elif sort == "release_date_asc":
            query = query.order_by(asc(models.Movie.release_date))
        elif sort == "title_asc":
            query = query.order_by(asc(models.Movie.title))
        elif sort == "title_desc":
            query = query.order_by(desc(models.Movie.title))
    
    if release_date_lte:
        release_date = datetime.strptime(release_date_lte, '%Y-%m-%d')
        query = query.filter(models.Movie.release_date <= release_date)

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
            "imageurl": db_movie.imageurl,
            "genres": db_movie.genres.split(",") if db_movie.genres else [],
            "imdb_id": db_movie.imdb_id,
            "imdb_rating": db_movie.imdb_rating,
            "imdb_votes": db_movie.imdb_votes,
            "trailer_url": db_movie.trailer_url,
            "cast": db_movie.cast.split(",") if db_movie.cast else [],
            "crew": db_movie.crew.split(",") if db_movie.crew else [],
            "content_rating": db_movie.content_rating,
            "mood_tags": db_movie.mood_tags.split(",") if db_movie.mood_tags else [],
            "streaming_platforms": db_movie.streaming_platforms.split(",") if db_movie.streaming_platforms else []
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

@app.post("/admin/load-more-movies", response_model=dict)
async def load_more_movies(
    request: LoadMoviesRequest,
    db: Session = Depends(get_db)
):
    try:
        # Get current last processed page
        last_page_config = db.query(models.Configuration).filter(
            models.Configuration.key == "last_processed_page"
        ).first()
        current_page = int(last_page_config.value) if last_page_config else 0
        
        total_processed, total_skipped = await load_initial_movies(db, request.num_pages)
        
        # Get updated last processed page
        last_page_config = db.query(models.Configuration).filter(
            models.Configuration.key == "last_processed_page"
        ).first()
        new_last_page = int(last_page_config.value) if last_page_config else current_page
        
        # Initialize recommendation system for new movies
        print("\nUpdating recommendation system...")
        movies = db.query(models.Movie).all()
        movies_data = [
            {
                "id": m.id,
                "title": m.title,
                "genres": m.genres,
                "director": m.crew.split(",")[0] if m.crew else "",
                "cast": m.cast,
                "description": m.description,
                "keywords": m.keywords,
                "mood_tags": m.mood_tags,
                "content_rating": m.content_rating,
                "streaming_platforms": m.streaming_platforms
            } for m in movies
        ]
        
        recommender.prepare_content_features(movies_data)
            
        return {
            "status": "success",
            "processed": total_processed,
            "skipped": total_skipped,
            "start_page": current_page + 1,
            "end_page": new_last_page,
            "next_page": new_last_page + 1
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
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
            "imageurl": db_movie.imageurl,
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
            "imageurl": db_movie.imageurl,
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
        "imageurl": db_movie.imageurl,
        "genres": db_movie.genres.split(",") if db_movie.genres else [],
        "imdb_id": db_movie.imdb_id,
        "imdb_rating": db_movie.imdb_rating,
        "imdb_votes": db_movie.imdb_votes,
        "trailer_url": db_movie.trailer_url
    }

@app.post("/movies/{movie_id}/rate")
async def rate_movie(
    movie_id: int,
    rating: float,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Rate a movie (1-5 stars)"""
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
    # Check if movie exists
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Update or create rating
    user_rating = db.query(models.UserMovieRating).filter(
        models.UserMovieRating.user_id == current_user.id,
        models.UserMovieRating.movie_id == movie_id
    ).first()
    
    if user_rating:
        user_rating.rating = rating
        user_rating.rated_at = datetime.utcnow()
    else:
        user_rating = models.UserMovieRating(
            user_id=current_user.id,
            movie_id=movie_id,
            rating=rating
        )
        db.add(user_rating)
    
    # Update movie's average rating
    all_ratings = db.query(models.UserMovieRating).filter(
        models.UserMovieRating.movie_id == movie_id
    ).all()
    movie.average_rating = sum(r.rating for r in all_ratings) / len(all_ratings)
    movie.rating_count = len(all_ratings)
    
    db.commit()
    return {"status": "success", "message": "Rating recorded successfully"}

@app.get("/api/users/me/library")
async def get_user_library(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get viewing history
    viewed_movies = db.query(models.ViewingHistory)\
        .filter(models.ViewingHistory.user_id == current_user.id)\
        .order_by(models.ViewingHistory.watched_at.desc())\
        .all()
    
    # Get rated movies
    rated_movies = db.query(models.Rating)\
        .filter(models.Rating.user_id == current_user.id)\
        .order_by(models.Rating.created_at.desc())\
        .all()
    
    # Get movie details for each entry
    viewed_movies_data = []
    for vh in viewed_movies:
        movie = db.query(models.Movie).filter(models.Movie.id == vh.movie_id).first()
        if movie:
            viewed_movies_data.append({
                "movie_id": vh.movie_id,
                "title": movie.title,
                "imageurl": movie.imageurl,
                "watched_at": vh.watched_at,
                "completed": vh.completed
            })

    rated_movies_data = []
    for rm in rated_movies:
        movie = db.query(models.Movie).filter(models.Movie.id == rm.movie_id).first()
        if movie:
            rated_movies_data.append({
                "movie_id": rm.movie_id,
                "title": movie.title,
                "imageurl": movie.imageurl,
                "rating": rm.rating,
                "rated_at": rm.created_at
            })

    return {
        "viewed_movies": viewed_movies_data,
        "rated_movies": rated_movies_data
    }

@app.post("/api/movies/{movie_id}/view")
async def add_to_library(
    movie_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if movie exists
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Create viewing history entry
    viewing_history = models.ViewingHistory(
        user_id=current_user.id,
        movie_id=movie_id,
        watched_at=datetime.utcnow(),
        completed=True
    )
    
    # Add to database
    db.add(viewing_history)
    
    # Update movie stats
    movie.view_count += 1
    
    try:
        db.commit()
        return {"status": "success", "message": "Movie added to library"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add movie to library")
    
@app.get("/movies/trending/", response_model=schemas.PaginatedMovieResponse)
def get_trending_movies(
    time_window: str = "month",
    page: int = 1,
    per_page: int = 30,
    db: Session = Depends(get_db)
):
    try:
        # Call TMDB API for trending movies
        tmdb_response = requests.get(
            f"{TMDB_BASE_URL}/trending/movie/{time_window}",
            params={
                "api_key": TMDB_API_KEY,
                "page": page
            }
        )
        tmdb_response.raise_for_status()
        tmdb_data = tmdb_response.json()
        
        movie_list = []
        for tmdb_movie in tmdb_data.get("results", [])[:per_page]:
            try:
                release_year = int(tmdb_movie["release_date"][:4]) if tmdb_movie.get("release_date") else None
                
                if release_year:
                    movie = db.query(models.Movie).filter(
                        models.Movie.title == tmdb_movie["title"],
                        models.Movie.release_year == release_year
                    ).first()
                    
                    if movie:
                        movie_list.append({
                            "id": movie.id,
                            "title": movie.title,
                            "description": movie.description,
                            "release_year": movie.release_year,
                            "average_rating": movie.average_rating,
                            "imageurl": movie.imageurl,
                            "genres": movie.genres.split(",") if movie.genres else [],
                            "imdb_id": movie.imdb_id,
                            "imdb_rating": movie.imdb_rating,
                            "imdb_votes": movie.imdb_votes,
                            "trailer_url": movie.trailer_url,
                            "cast": movie.cast.split(",") if movie.cast else [],
                            "crew": movie.crew.split(",") if movie.crew else []
                        })
            except Exception as e:
                print(f"Error processing movie {tmdb_movie.get('title')}: {str(e)}")
                continue

        return {
            "items": movie_list,
            "total": len(movie_list),
            "page": page,
            "total_pages": tmdb_data.get("total_pages", 1),
            "has_next": page < tmdb_data.get("total_pages", 1),
            "has_prev": page > 1
        }
    except Exception as e:
        print(f"Error in get_trending_movies: {str(e)}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "total_pages": 1,
            "has_next": False,
            "has_prev": page > 1
        }
    
@app.delete("/api/movies/{movie_id}/view")
async def remove_from_library(
    movie_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Delete the viewing history entry
    result = db.query(models.ViewingHistory).filter(
        models.ViewingHistory.user_id == current_user.id,
        models.ViewingHistory.movie_id == movie_id
    ).delete()
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Movie not found in library")
    
    try:
        db.commit()
        return {"status": "success", "message": "Movie removed from library"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove movie from library")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)