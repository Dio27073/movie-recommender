# backend/app/movie_processing.py
import asyncio
import time
from datetime import datetime
from typing import Set, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from . import models
from .database import SessionLocal, CacheUtils
from .external_apis import (
    fetch_imdb_data, fetch_movie_cast_crew, fetch_movie_trailer,
    fetch_streaming_platforms, get_popular_movies_from_tmdb,
    get_movie_details_from_tmdb, TMDB_IMAGE_BASE_URL
)
import logging

logger = logging.getLogger(__name__)

# HELPER FUNCTION: Convert arrays to comma-separated strings
def array_to_string(arr):
    """Convert array to comma-separated string, handling None and empty arrays"""
    if not arr or arr is None:
        return None  # Return None instead of empty string
    if isinstance(arr, list):
        # Filter out empty strings and join
        filtered = [str(item).strip() for item in arr if str(item).strip()]
        return ','.join(filtered) if filtered else None
    return str(arr) if str(arr).strip() else None

def process_movie_genres_and_moods(genres: list) -> Tuple[list, list]:
    """OPTIMIZED: Process genres and generate mood tags with caching"""
    cache_key = f"genre_mood_mapping_{hash(tuple(genres))}"
    cached_result = CacheUtils.get(cache_key)
    
    if cached_result:
        import json
        result = json.loads(cached_result)
        return result["genres"], result["mood_tags"]
    
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
    
    processed_genres = genres
    unique_mood_tags = list(set(mood_tags))
    
    # Cache result for 1 hour
    result = {"genres": processed_genres, "mood_tags": unique_mood_tags}
    import json
    CacheUtils.set(cache_key, json.dumps(result), 3600)
    
    return processed_genres, unique_mood_tags

async def process_single_movie(movie_data: Dict[str, Any], db: Session) -> bool:
    """FIXED: Process a single movie with proper string conversion"""
    try:
        if not all(key in movie_data for key in ["title", "release_date", "id"]):
            logger.debug(f"Skipping movie with missing data: {movie_data.get('title', 'Unknown')}")
            return False

        try:
            release_year = int(movie_data["release_date"][:4])
        except (ValueError, IndexError):
            logger.debug(f"Invalid release date for movie {movie_data.get('title')}")
            return False

        # Check if movie already exists by title and year (quick check)
        existing_movie = db.query(models.Movie).filter(
            models.Movie.title == movie_data["title"],
            models.Movie.release_year == release_year
        ).first()
        
        if existing_movie:
            logger.debug(f"Movie already exists: {movie_data.get('title')} ({release_year})")
            return False

        # OPTIMIZED: Fetch external data with timeouts and error handling
        try:
            # Use asyncio.gather for concurrent API calls with timeout
            async def fetch_with_timeout(coro, timeout=10):
                try:
                    return await asyncio.wait_for(coro, timeout=timeout)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout fetching data for {movie_data.get('title')}")
                    return None
                except Exception as e:
                    logger.warning(f"Error fetching data for {movie_data.get('title')}: {e}")
                    return None

            # Get movie details first (required)
            movie_details = get_movie_details_from_tmdb(movie_data["id"])
            if not movie_details:
                logger.debug(f"Failed to get details for {movie_data.get('title')}")
                return False

            # Fetch additional data concurrently with error handling
            tasks = [
                fetch_with_timeout(fetch_imdb_data(movie_data["title"], release_year)),
                fetch_with_timeout(fetch_movie_cast_crew(movie_data["id"])),
                fetch_with_timeout(fetch_movie_trailer(movie_data["id"])),
                fetch_with_timeout(fetch_streaming_platforms(movie_data["id"]))
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            imdb_data, cast_crew_data, trailer_url, streaming_platforms = results
            
            # Handle exceptions in results
            if isinstance(imdb_data, Exception):
                imdb_data = None
            if isinstance(cast_crew_data, Exception):
                cast_crew_data = {"cast": [], "crew": []}
            if isinstance(trailer_url, Exception):
                trailer_url = None
            if isinstance(streaming_platforms, Exception):
                streaming_platforms = []
                
        except Exception as e:
            logger.warning(f"Error fetching external data for {movie_data.get('title')}: {e}")
            # Continue with minimal data
            imdb_data = None
            cast_crew_data = {"cast": [], "crew": []}
            trailer_url = None
            streaming_platforms = []

        # Calculate rating with fallback
        converted_rating = 0.0
        if imdb_data and imdb_data.get("imdb_rating"):
            converted_rating = imdb_data["imdb_rating"] / 2
        elif movie_data.get("vote_average"):
            converted_rating = movie_data["vote_average"] / 2
        converted_rating = min(max(converted_rating, 0), 5)

        # Process genres and mood tags
        genres = [genre["name"] for genre in movie_details.get("genres", [])]
        genres, mood_tags = process_movie_genres_and_moods(genres)

        # FIXED: Convert arrays to comma-separated strings
        movie = models.Movie(
            title=movie_data["title"],
            description=movie_data.get("overview", ""),
            genres=array_to_string(genres),  # Convert to string
            release_year=release_year,
            release_date=datetime.strptime(movie_data["release_date"], '%Y-%m-%d'),
            average_rating=converted_rating,
            imageurl=f"{TMDB_IMAGE_BASE_URL}{movie_data['poster_path']}" if movie_data.get('poster_path') else None,
            imdb_id=imdb_data.get("imdb_id") if imdb_data else None,
            imdb_rating=imdb_data.get("imdb_rating") if imdb_data else None,
            imdb_votes=imdb_data.get("imdb_votes") if imdb_data else None,
            trailer_url=trailer_url,
            cast=array_to_string(cast_crew_data.get("cast", [])) if cast_crew_data else None,  # Convert to string
            crew=array_to_string(cast_crew_data.get("crew", [])) if cast_crew_data else None,  # Convert to string
            popularity_score=movie_data.get("popularity", 0),
            view_count=0,
            completion_rate=0.0,
            rating_count=0,
            keywords=movie_details.get("tagline", ""),
            mood_tags=array_to_string(mood_tags),  # Convert to string
            streaming_platforms=array_to_string(streaming_platforms)  # Convert to string
        )

        try:
            db.add(movie)
            db.flush()
            logger.debug(f"Successfully processed: {movie_data.get('title')}")
            return True
        except IntegrityError:
            db.rollback()
            logger.debug(f"Duplicate movie detected during insert: {movie_data.get('title')}")
            return False

    except Exception as e:
        logger.error(f"Error processing movie {movie_data.get('title', 'Unknown')}: {str(e)}")
        return False

async def load_initial_movies_optimized(db: Session, pages: int = 2) -> Tuple[int, int]:
    """OPTIMIZED: Load initial movies with better concurrency and error handling"""
    
    # Get last processed page
    last_page_config = db.query(models.Configuration).filter(
        models.Configuration.key == "last_processed_page"
    ).first()
    
    last_page = int(last_page_config.value) if last_page_config else 0
    start_page = max(1, last_page + 1)  # Start from page 1 if no previous page
    end_page = start_page + pages - 1

    logger.info(f"Loading movies from TMDB pages {start_page} to {end_page}")
    
    total_processed = 0
    total_skipped = 0
    
    for page in range(start_page, end_page + 1):
        try:
            logger.info(f"Processing TMDB page {page}")
            
            # Rate limiting
            await asyncio.sleep(0.5)
            
            # Get movies from TMDB
            movies_data = get_popular_movies_from_tmdb(page)
            if not movies_data or not movies_data.get("results"):
                logger.warning(f"No movies found on page {page}")
                continue
            
            # Process movies in smaller batches for better memory management
            batch_size = 5
            movies_batch = movies_data["results"][:20]  # Limit to 20 movies per page
            
            for i in range(0, len(movies_batch), batch_size):
                batch = movies_batch[i:i + batch_size]
                
                # Process batch with concurrency limit
                semaphore = asyncio.Semaphore(3)  # Limit concurrent processing
                
                async def process_with_semaphore(movie_data):
                    async with semaphore:
                        return await process_single_movie(movie_data, db)
                
                # Process batch concurrently
                batch_tasks = [process_with_semaphore(movie) for movie in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Count results
                for result in batch_results:
                    if isinstance(result, Exception):
                        total_skipped += 1
                        logger.warning(f"Exception in batch processing: {result}")
                    elif result:
                        total_processed += 1
                    else:
                        total_skipped += 1
                
                # Commit batch
                try:
                    db.commit()
                    logger.debug(f"Committed batch {i//batch_size + 1} for page {page}")
                except Exception as e:
                    logger.error(f"Error committing batch: {e}")
                    db.rollback()
                
                # Small delay between batches
                await asyncio.sleep(0.2)
            
            # Update last processed page
            if last_page_config:
                last_page_config.value = str(page)
            else:
                last_page_config = models.Configuration(
                    key="last_processed_page",
                    value=str(page)
                )
                db.add(last_page_config)
            
            db.commit()
            logger.info(f"Completed page {page}")
            
        except Exception as e:
            logger.error(f"Error processing page {page}: {str(e)}")
            db.rollback()
            continue

    logger.info(f"Movie loading completed: {total_processed} processed, {total_skipped} skipped")
    return total_processed, total_skipped

async def init_movie_system_async():
    """OPTIMIZED: Initialize movie system without recommender"""
    try:
        logger.info("Initializing movie system...")
        
        # Use connection pooling efficiently
        db = SessionLocal()
        try:
            # Check current movie count
            movie_count = db.query(models.Movie).count()
            logger.info(f"Current movie count: {movie_count}")
            
            # Only load movies if database is empty or has very few movies
            if movie_count < 50:
                logger.info("Loading initial movie data...")
                await load_initial_movies_optimized(db, pages=2)
                movie_count = db.query(models.Movie).count()
                logger.info(f"Movie count after loading: {movie_count}")
            
            logger.info(f"Movie system initialized with {movie_count} movies")
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in movie system initialization: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to initialize movie system: {str(e)}")

def get_movie_system_status():
    """Get movie system status for health checks"""
    try:
        db = SessionLocal()
        try:
            movie_count = db.query(models.Movie).count()
            return {
                "status": "ready" if movie_count > 0 else "initializing",
                "movies_loaded": movie_count
            }
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "error": str(e), "movies_loaded": 0}

async def periodic_movie_update():
    """Background task to periodically update movie database"""
    while True:
        try:
            # Wait 24 hours between updates
            await asyncio.sleep(24 * 60 * 60)
            
            logger.info("Starting periodic movie update...")
            db = SessionLocal()
            try:
                # Load 1 new page of movies
                await load_initial_movies_optimized(db, pages=1)
                logger.info("Periodic movie update completed")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in periodic movie update: {e}")
            # Continue the loop even if update fails
            continue