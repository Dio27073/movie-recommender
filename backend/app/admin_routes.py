# backend/app/admin_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text, or_
from pydantic import BaseModel
import time

from . import models, schemas
from .database import get_db
from .movie_processing import load_initial_movies_optimized
from .external_apis import fetch_imdb_data

router = APIRouter()

class LoadMoviesRequest(BaseModel):
    start_page: int
    num_pages: int = 10

@router.post("/load-more-movies", response_model=dict)
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
        
        total_processed, total_skipped = await load_initial_movies_optimized(db, request.num_pages)
        
        # Get updated last processed page
        last_page_config = db.query(models.Configuration).filter(
            models.Configuration.key == "last_processed_page"
        ).first()
        new_last_page = int(last_page_config.value) if last_page_config else current_page
        
        # REMOVED: Recommender functionality
        print(f"Movie loading completed: {total_processed} processed, {total_skipped} skipped")
            
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

@router.post("/update-imdb-data")
async def update_missing_imdb_data(db: Session = Depends(get_db)):
    try:
        # Get all movies with missing IMDB data
        movies = db.query(models.Movie).filter(
            or_(
                models.Movie.imdb_id.is_(None),
                models.Movie.imdb_rating.is_(None)
            )
        ).all()
        
        print(f"Found {len(movies)} movies with missing IMDB data")
        
        updated_count = 0
        failed_count = 0
        duplicate_count = 0
        
        for movie in movies:
            try:
                print(f"Processing {movie.title} ({movie.release_year})...")
                
                # Start a new transaction for each movie
                db.begin_nested()
                
                imdb_data = await fetch_imdb_data(movie.title, movie.release_year)
                
                if imdb_data and imdb_data["imdb_id"]:
                    # Check if this IMDB ID already exists
                    existing_movie = db.query(models.Movie).filter(
                        models.Movie.imdb_id == imdb_data["imdb_id"],
                        models.Movie.id != movie.id  # Exclude current movie
                    ).first()
                    
                    if existing_movie:
                        print(f"Duplicate found for {movie.title}. Existing movie: {existing_movie.title}")
                        duplicate_count += 1
                        
                        # If the existing movie has better data, keep it and delete the current one
                        if (existing_movie.imdb_rating is not None and 
                            (movie.imdb_rating is None or existing_movie.imdb_rating > movie.imdb_rating)):
                            db.delete(movie)
                            print(f"Deleted duplicate movie: {movie.title}")
                        else:
                            # Current movie has better data, update it and delete the existing one
                            movie.imdb_id = imdb_data["imdb_id"]
                            movie.imdb_rating = imdb_data["imdb_rating"]
                            movie.imdb_votes = imdb_data["imdb_votes"]
                            db.delete(existing_movie)
                            print(f"Updated current movie and deleted duplicate: {existing_movie.title}")
                            updated_count += 1
                    else:
                        # No duplicate, just update
                        movie.imdb_id = imdb_data["imdb_id"]
                        movie.imdb_rating = imdb_data["imdb_rating"]
                        movie.imdb_votes = imdb_data["imdb_votes"]
                        updated_count += 1
                        print(f"Updated {movie.title} with IMDB rating: {imdb_data['imdb_rating']}")
                else:
                    failed_count += 1
                    print(f"Could not find IMDB data for {movie.title}")
                
                # Commit this movie's transaction
                db.commit()
                
                # Add a small delay to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"Error updating {movie.title}: {str(e)}")
                db.rollback()
                failed_count += 1
                continue
        
        return {
            "status": "success",
            "total_processed": len(movies),
            "updated": updated_count,
            "failed": failed_count,
            "duplicates_handled": duplicate_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating IMDB data: {str(e)}"
        )

@router.post("/cleanup-duplicates")
async def cleanup_duplicate_movies(db: Session = Depends(get_db)):
    try:
        # Find movies with the same title and release year
        duplicate_query = """
            WITH duplicates AS (
                SELECT title, release_year, COUNT(*) as cnt,
                       array_agg(id) as ids,
                       array_agg(imdb_rating) as ratings
                FROM movies
                GROUP BY title, release_year
                HAVING COUNT(*) > 1
            )
            SELECT * FROM duplicates;
        """
        
        result = db.execute(text(duplicate_query))
        duplicates = result.fetchall()
        
        cleaned_count = 0
        
        for dup in duplicates:
            try:
                # Get all duplicate movies
                movies = db.query(models.Movie).filter(
                    models.Movie.id.in_(dup.ids)
                ).all()
                
                # Keep the one with the highest IMDB rating or most complete data
                best_movie = max(movies, key=lambda m: (
                    (m.imdb_rating or 0),
                    1 if m.imdb_id else 0,
                    1 if m.trailer_url else 0,
                    len(m.genres) if m.genres else 0  # FIXED: Handle array properly
                ))
                
                # Delete others
                for movie in movies:
                    if movie.id != best_movie.id:
                        db.delete(movie)
                        cleaned_count += 1
                
                db.commit()
                print(f"Cleaned up duplicates for: {dup.title} ({dup.release_year})")
                
            except Exception as e:
                print(f"Error cleaning up {dup.title}: {str(e)}")
                db.rollback()
                continue
        
        return {
            "status": "success",
            "duplicates_found": len(duplicates),
            "movies_removed": cleaned_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up duplicates: {str(e)}"
        )