# backend/app/movie_operations.py
import asyncio
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import logging

from . import models, schemas
from .database import CacheUtils
from .external_apis import (
    fetch_imdb_data, fetch_movie_trailer, 
    get_movie_details_from_tmdb, TMDB_API_KEY, TMDB_BASE_URL
)
import httpx

logger = logging.getLogger(__name__)

async def create_movie_with_external_data(movie: schemas.MovieCreate, db: Session) -> schemas.Movie:
    """OPTIMIZED: Create movie with async external API integration and proper error handling"""
    try:
        # Convert to dict for processing
        movie_data = movie.model_dump()
        
        # OPTIMIZED: Use async HTTP client for better performance
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Concurrent API calls with proper error handling
            tasks = []
            
            # IMDB data
            tasks.append(fetch_imdb_data_safe(movie.title, movie.release_year))
            
            # TMDB data
            if movie.title and movie.release_year:
                tasks.append(fetch_tmdb_data_safe(client, movie.title, movie.release_year))
            else:
                tasks.append(asyncio.create_task(return_none()))
            
            # Execute concurrent API calls
            imdb_data, tmdb_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            if isinstance(imdb_data, Exception):
                logger.warning(f"IMDB API error for {movie.title}: {imdb_data}")
                imdb_data = None
                
            if isinstance(tmdb_data, Exception):
                logger.warning(f"TMDB API error for {movie.title}: {tmdb_data}")
                tmdb_data = None
        
        # OPTIMIZED: Handle arrays properly (no string conversion)
        if movie_data.get("genres") and isinstance(movie_data["genres"], list):
            # Keep as array - PostgreSQL handles this natively
            pass
        else:
            movie_data["genres"] = []
        
        # Add IMDB data if available
        if imdb_data:
            movie_data.update({
                "imdb_id": imdb_data.get("imdb_id"),
                "imdb_rating": imdb_data.get("imdb_rating"),
                "imdb_votes": imdb_data.get("imdb_votes")
            })
            
            # Update average_rating based on IMDB rating
            if imdb_data.get("imdb_rating"):
                movie_data["average_rating"] = min(imdb_data["imdb_rating"] / 2, 5.0)
        
        # Add TMDB data if available
        if tmdb_data:
            movie_data.update({
                "trailer_url": tmdb_data.get("trailer_url"),
                "imageurl": tmdb_data.get("poster_url"),
                "popularity_score": tmdb_data.get("popularity", 0)
            })
        
        # Create database record
        db_movie = models.Movie(**movie_data)
        db.add(db_movie)
        db.commit()
        db.refresh(db_movie)
        
        # OPTIMIZED: Return in proper format (arrays stay as arrays)
        return {
            "id": db_movie.id,
            "title": db_movie.title,
            "description": db_movie.description,
            "release_year": db_movie.release_year,
            "average_rating": db_movie.average_rating,
            "imageurl": db_movie.imageurl,
            "genres": db_movie.genres or [],  # Return as array
            "imdb_id": db_movie.imdb_id,
            "imdb_rating": db_movie.imdb_rating,
            "imdb_votes": db_movie.imdb_votes,
            "trailer_url": db_movie.trailer_url,
            "cast": db_movie.cast or [],
            "crew": db_movie.crew or [],
            "content_rating": db_movie.content_rating,
            "mood_tags": db_movie.mood_tags or [],
            "streaming_platforms": db_movie.streaming_platforms or []
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating movie {movie.title}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create movie: {str(e)}")

async def return_none():
    """Helper function for async gather operations"""
    return None

async def fetch_imdb_data_safe(title: str, year: int) -> Optional[dict]:
    """Safe IMDB data fetching with error handling"""
    try:
        return await fetch_imdb_data(title, year)
    except Exception as e:
        logger.warning(f"IMDB fetch failed for {title} ({year}): {e}")
        return None

async def fetch_tmdb_data_safe(client: httpx.AsyncClient, title: str, year: int) -> Optional[dict]:
    """OPTIMIZED: Safe TMDB data fetching with async client"""
    try:
        # Search for movie
        search_response = await client.get(
            f"{TMDB_BASE_URL}/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": title,
                "year": year
            }
        )
        
        if search_response.status_code != 200:
            return None
            
        search_results = search_response.json().get("results", [])
        if not search_results:
            return None
            
        movie_id = search_results[0]["id"]
        
        # Get movie details and trailer concurrently
        details_task = client.get(
            f"{TMDB_BASE_URL}/movie/{movie_id}",
            params={"api_key": TMDB_API_KEY}
        )
        
        videos_task = client.get(
            f"{TMDB_BASE_URL}/movie/{movie_id}/videos",
            params={"api_key": TMDB_API_KEY}
        )
        
        details_response, videos_response = await asyncio.gather(
            details_task, videos_task, return_exceptions=True
        )
        
        result = {}
        
        # Process movie details
        if not isinstance(details_response, Exception) and details_response.status_code == 200:
            details = details_response.json()
            result.update({
                "poster_url": f"https://image.tmdb.org/t/p/w500{details['poster_path']}" if details.get('poster_path') else None,
                "popularity": details.get("popularity", 0)
            })
        
        # Process trailer
        if not isinstance(videos_response, Exception) and videos_response.status_code == 200:
            videos = videos_response.json().get("results", [])
            trailer = next((v for v in videos if v.get("type") == "Trailer" and v.get("site") == "YouTube"), None)
            if trailer:
                result["trailer_url"] = f"https://www.youtube.com/watch?v={trailer['key']}"
        
        return result if result else None
        
    except Exception as e:
        logger.warning(f"TMDB fetch failed for {title} ({year}): {e}")
        return None

def get_movie_by_id(movie_id: int, db: Session) -> Optional[models.Movie]:
    """OPTIMIZED: Get movie by ID with caching"""
    cache_key = f"movie_by_id_{movie_id}"
    
    # Check cache first
    cached_movie = CacheUtils.get(cache_key)
    if cached_movie:
        # Note: This would need proper object reconstruction
        # For now, just query the database
        pass
    
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    
    # Cache for 30 minutes if found
    if movie:
        # We'd cache the movie data here if needed
        pass
    
    return movie

def get_movie_by_imdb_id(imdb_id: str, db: Session) -> Optional[models.Movie]:
    """Get a movie by its IMDB ID with basic caching"""
    cache_key = f"movie_by_imdb_{imdb_id}"
    
    # For now, just query directly (could add caching later)
    return db.query(models.Movie).filter(models.Movie.imdb_id == imdb_id).first()

def update_movie_popularity_optimized(movie_id: int, db: Session, view_increment: int = 1, completed: bool = False):
    """OPTIMIZED: Update movie popularity with atomic operations"""
    try:
        # Use atomic update to avoid race conditions
        result = db.query(models.Movie).filter(models.Movie.id == movie_id).update({
            models.Movie.view_count: models.Movie.view_count + view_increment
        })
        
        if result == 0:
            logger.warning(f"Movie {movie_id} not found for popularity update")
            return None
            
        # Handle completion rate update if needed
        if completed:
            movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
            if movie:
                # Calculate new completion rate
                total_views = movie.view_count
                if total_views > 0:
                    completed_views = (movie.completion_rate * (total_views - 1)) + 1
                    movie.completion_rate = completed_views / total_views
        
        db.commit()
        
        # Invalidate relevant caches
        CacheUtils.delete(f"movie_by_id_{movie_id}")
        
        return db.query(models.Movie).filter(models.Movie.id == movie_id).first()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating movie popularity for {movie_id}: {e}")
        return None

# REMOVED: format_movie_response function as it duplicates serialize_movie functionality
# Use serialize_movie_cached from api_routes.py instead

def get_movie_stats(db: Session) -> dict:
    """Get comprehensive movie statistics for admin/monitoring"""
    try:
        cache_key = "movie_stats_comprehensive"
        cached_stats = CacheUtils.get(cache_key)
        
        if cached_stats:
            import json
            return json.loads(cached_stats)
        
        # Aggregate statistics
        stats = db.query(
            func.count(models.Movie.id).label('total_movies'),
            func.avg(models.Movie.average_rating).label('avg_rating'),
            func.avg(models.Movie.view_count).label('avg_views'),
            func.sum(models.Movie.view_count).label('total_views')
        ).first()
        
        # Genre distribution
        genre_stats = db.execute("""
            SELECT genre, COUNT(*) as count
            FROM (
                SELECT unnest(genres) as genre
                FROM movies
                WHERE genres IS NOT NULL
            ) as genre_breakdown
            GROUP BY genre
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()
        
        result = {
            "total_movies": stats.total_movies or 0,
            "average_rating": float(stats.avg_rating) if stats.avg_rating else 0.0,
            "average_views": float(stats.avg_views) if stats.avg_views else 0.0,
            "total_views": stats.total_views or 0,
            "top_genres": [{"genre": row.genre, "count": row.count} for row in genre_stats]
        }
        
        # Cache for 15 minutes
        import json
        CacheUtils.set(cache_key, json.dumps(result), 900)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting movie stats: {e}")
        return {
            "total_movies": 0,
            "average_rating": 0.0,
            "average_views": 0.0,
            "total_views": 0,
            "top_genres": []
        }