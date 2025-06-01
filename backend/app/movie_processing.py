# backend/app/movie_processing.py
import time
from datetime import datetime
from typing import Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from . import models
from .database import SessionLocal
from .external_apis import (
    fetch_imdb_data, fetch_movie_cast_crew, fetch_movie_trailer,
    fetch_streaming_platforms, get_popular_movies_from_tmdb,
    get_movie_details_from_tmdb, TMDB_IMAGE_BASE_URL
)
from .recommender.engine import MovieRecommender

# Global recommender instance
recommender = MovieRecommender()

def process_movie_genres_and_moods(genres: list) -> Tuple[list, list]:
    """Process genres and generate mood tags"""
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
    
    return genres, list(set(mood_tags))

async def load_initial_movies(db: Session, pages: int = 10) -> Tuple[int, int]:
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
            
            movies_data = get_popular_movies_from_tmdb(page)
            
            if not movies_data.get("results"):
                print(f"No movies found on page {page}")
                continue

            page_failures = 0
            
            for movie_data in movies_data["results"]:
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
                    movie_details = get_movie_details_from_tmdb(movie_data["id"])
                    
                    if not movie_details:
                        print(f"Failed to get details for movie {movie_data.get('title')}")
                        page_skipped += 1
                        continue
                    
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
                    genres, mood_tags = process_movie_genres_and_moods(genres)

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

async def init_recommender_async():
    """Initialize the recommender system asynchronously"""
    try:
        # Use regular session management instead of context manager
        db = SessionLocal()
        try:
            # Check if we need to load initial movies
            movie_count = db.query(models.Movie).count()
            print(f"Current movie count in database: {movie_count}")
            
            if movie_count == 0:
                # Only load first 2 pages for initial data
                await load_initial_movies(db, pages=2)
                
            # Initialize recommender with available data
            global recommender
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
            db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
    except Exception as e:
        print(f"Error in background initialization: {str(e)}")

def get_recommender():
    """Get the global recommender instance"""
    return recommender