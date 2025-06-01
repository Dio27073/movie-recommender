# backend/app/movie_operations.py
import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from . import models, schemas
from .external_apis import (
    fetch_imdb_data, fetch_movie_trailer, 
    TMDB_BASE_URL, TMDB_API_KEY
)

async def create_movie_with_external_data(movie: schemas.MovieCreate, db: Session) -> schemas.Movie:
    """Create a new movie with external API data integration"""
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

def get_movie_by_id(movie_id: int, db: Session) -> Optional[models.Movie]:
    """Get a movie by its ID"""
    return db.query(models.Movie).filter(models.Movie.id == movie_id).first()

def get_movie_by_imdb_id(imdb_id: str, db: Session) -> Optional[models.Movie]:
    """Get a movie by its IMDB ID"""
    return db.query(models.Movie).filter(models.Movie.imdb_id == imdb_id).first()

def update_movie_popularity(movie_id: int, db: Session, view_increment: int = 1, completed: bool = False):
    """Update movie popularity metrics"""
    movie = get_movie_by_id(movie_id, db)
    if movie:
        movie.view_count += view_increment
        if completed:
            # Calculate new completion rate
            total_views = movie.view_count
            completed_views = (movie.completion_rate * (total_views - 1)) + 1
            movie.completion_rate = completed_views / total_views
        db.commit()
    return movie

def format_movie_response(db_movie: models.Movie) -> dict:
    """Format a movie database object for API response"""
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
        "trailer_url": db_movie.trailer_url,
        "cast": db_movie.cast.split(",") if db_movie.cast else [],
        "crew": db_movie.crew.split(",") if db_movie.crew else [],
        "content_rating": db_movie.content_rating,
        "mood_tags": db_movie.mood_tags.split(",") if db_movie.mood_tags else [],
        "streaming_platforms": db_movie.streaming_platforms.split(",") if db_movie.streaming_platforms else []
    }