# backend/app/api_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from sqlalchemy import cast, Integer, text, or_, desc, asc
from typing import List, Optional
from datetime import datetime

from . import models, schemas
from .database import get_db
from .auth_utils import get_current_active_user
from .movie_processing import get_recommender
from .external_apis import get_trending_movies_from_tmdb, TMDB_IMAGE_BASE_URL
from .movie_operations import create_movie_with_external_data

router = APIRouter()

# Global flag to check if recommender is ready
recommender_ready = False

@router.get("/test-db")
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

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    global recommender_ready
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        # Check if recommender is ready
        try:
            recommender = get_recommender()
            recommender_ready = recommender is not None
        except:
            recommender_ready = False
        
        return {
            "status": "healthy",
            "database": "connected",
            "recommender_ready": recommender_ready,
            "initialization_complete": recommender_ready,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )

@router.get("/keep-alive")
async def keep_alive():
    """Lightweight endpoint to prevent cold starts"""
    return {
        "status": "alive", 
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Server is awake"
    }

@router.get("/movies/", response_model=schemas.PaginatedMovieResponse)
def get_movies(
    request: Request,
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
    release_date_lte: str = None,
    db: Session = Depends(get_db)
):
    """Enhanced movies endpoint with better error handling"""
    try:
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
        
        # Enhanced sorting with fallbacks
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
            elif sort == "random":
                # Get the random seed from query parameters
                random_seed = request.query_params.get('random_seed')
                if random_seed:
                    # Use the seed to create a deterministic random order
                    query = query.order_by(func.random(cast(random_seed, Integer)))
                else:
                    # If no seed provided, use regular random
                    query = query.order_by(func.random())
        
        if release_date_lte:
            release_date = datetime.strptime(release_date_lte, '%Y-%m-%d')
            query = query.filter(models.Movie.release_date <= release_date)

        # Get total count with timeout protection
        try:
            total_movies = query.count()
        except Exception as e:
            print(f"Count query failed: {e}")
            total_movies = 0
            
        total_pages = max(1, (total_movies + per_page - 1) // per_page)
        
        # Get movies with fallback
        try:
            movies = query.offset(offset).limit(per_page).all()
        except Exception as e:
            print(f"Movie query failed: {e}")
            movies = []
        
        # Format response
        movie_list = []
        for db_movie in movies:
            try:
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
            except Exception as e:
                print(f"Error formatting movie {db_movie.id}: {e}")
                continue
        
        return {
            "items": movie_list,
            "total": total_movies,
            "page": page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
    except Exception as e:
        print(f"Error in get_movies: {e}")
        # Return empty result instead of failing
        return {
            "items": [],
            "total": 0,
            "page": page,
            "total_pages": 1,
            "has_next": False,
            "has_prev": False
        }

@router.get("/movies/search/", response_model=schemas.PaginatedMovieResponse)
def search_movies_by_cast_crew(
    query: str,
    page: int = 1,
    per_page: int = 12,
    db: Session = Depends(get_db),
    search_type: str = "cast_crew"
):
    """Search movies by cast or crew members with error handling."""
    try:
        offset = (page - 1) * per_page
        query_lower = query.lower()
        
        # Search for movies where cast or crew contains the query
        db_query = db.query(models.Movie)
        if search_type == "cast_crew":
            db_query = db_query.filter(
                or_(
                    models.Movie.cast.ilike(f"%{query_lower}%"),
                    models.Movie.crew.ilike(f"%{query_lower}%")
                )
            )
        elif search_type == "title":
            db_query = db_query.filter(models.Movie.title.ilike(f"%{query_lower}%"))
        
        total_movies = db_query.count()
        total_pages = (total_movies + per_page - 1) // per_page
        movies = db_query.offset(offset).limit(per_page).all()
        
        movie_list = []
        for db_movie in movies:
            try:
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
            except Exception as e:
                print(f"Error formatting search result movie {db_movie.id}: {e}")
                continue
        
        return {
            "items": movie_list,
            "total": total_movies,
            "page": page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    except Exception as e:
        print(f"Error in search_movies_by_cast_crew: {e}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "total_pages": 1,
            "has_next": False,
            "has_prev": page > 1
        }

@router.get("/movies/recommended/", response_model=schemas.PaginatedMovieResponse)
async def get_recommended_movies(
    current_user: models.User = Depends(get_current_active_user),
    page: int = 1,
    per_page: int = 12,
    db: Session = Depends(get_db)
):
    """Recommendations with graceful fallback when recommender isn't ready"""
    global recommender_ready
    
    try:
        # Check if recommender is ready
        if not recommender_ready:
            print("Recommender not ready, falling back to popular movies")
            # Fallback to popular movies when recommender isn't ready
            fallback_movies = db.query(models.Movie)\
                .filter(models.Movie.imdb_rating >= 7.0)\
                .order_by(desc(models.Movie.imdb_rating))\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()
            
            movie_list = []
            for db_movie in fallback_movies:
                try:
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
                except Exception as e:
                    print(f"Error formatting fallback movie {db_movie.id}: {e}")
                    continue
            
            return {
                "items": movie_list,
                "total": len(movie_list),
                "page": page,
                "total_pages": 1,
                "has_next": False,
                "has_prev": page > 1
            }
        
        # Use actual recommender when ready
        recently_viewed = db.query(models.ViewingHistory)\
            .filter(models.ViewingHistory.user_id == current_user.id)\
            .order_by(desc(models.ViewingHistory.watched_at))\
            .limit(10)\
            .all()
        
        recently_viewed_ids = [vh.movie_id for vh in recently_viewed]
        
        recommender = get_recommender()
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
            try:
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
            except Exception as e:
                print(f"Error formatting recommended movie {db_movie.id}: {e}")
                continue
        
        return {
            "items": movie_list,
            "total": total_recommendations,
            "page": page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
    except Exception as e:
        print(f"Error in get_recommended_movies: {e}")
        # Return empty result gracefully
        return {
            "items": [],
            "total": 0,
            "page": page,
            "total_pages": 1,
            "has_next": False,
            "has_prev": page > 1
        }

@router.get("/movies/trending/", response_model=schemas.PaginatedMovieResponse)
def get_trending_movies(
    time_window: str = "month",
    page: int = 1,
    per_page: int = 30,
    db: Session = Depends(get_db)
):
    """Enhanced trending movies with better error handling"""
    try:
        tmdb_data = get_trending_movies_from_tmdb(time_window, page)
        
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

        # If no trending movies found, fall back to high-rated recent movies
        if not movie_list:
            print("No trending movies found, using fallback")
            fallback_movies = db.query(models.Movie)\
                .filter(models.Movie.imdb_rating >= 7.0)\
                .order_by(desc(models.Movie.release_date))\
                .limit(per_page)\
                .all()
            
            for movie in fallback_movies:
                try:
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
                    print(f"Error formatting trending fallback movie {movie.id}: {e}")
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
        # Graceful fallback - return popular movies from our database
        try:
            fallback_movies = db.query(models.Movie)\
                .filter(models.Movie.imdb_rating >= 6.0)\
                .order_by(desc(models.Movie.imdb_rating))\
                .limit(per_page)\
                .all()
            
            movie_list = []
            for movie in fallback_movies:
                try:
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
                    print(f"Error formatting final fallback movie {movie.id}: {e}")
                    continue
            
            return {
                "items": movie_list,
                "total": len(movie_list),
                "page": page,
                "total_pages": 1,
                "has_next": False,
                "has_prev": page > 1
            }
        except Exception as fallback_error:
            print(f"Fallback also failed: {fallback_error}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "total_pages": 1,
                "has_next": False,
                "has_prev": page > 1
            }

# User Library Routes
@router.get("/users/me/library")
async def get_user_library(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
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
            try:
                movie = db.query(models.Movie).filter(models.Movie.id == vh.movie_id).first()
                if movie:
                    viewed_movies_data.append({
                        "movie_id": vh.movie_id,
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
                        "crew": movie.crew.split(",") if movie.crew else [],
                        "watched_at": vh.watched_at,
                        "completed": vh.completed
                    })
            except Exception as e:
                print(f"Error processing viewed movie {vh.movie_id}: {e}")
                continue

        rated_movies_data = []
        for rm in rated_movies:
            try:
                movie = db.query(models.Movie).filter(models.Movie.id == rm.movie_id).first()
                if movie:
                    rated_movies_data.append({
                        "movie_id": rm.movie_id,
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
                        "crew": movie.crew.split(",") if movie.crew else [],
                        "rating": rm.rating,
                        "rated_at": rm.created_at
                    })
            except Exception as e:
                print(f"Error processing rated movie {rm.movie_id}: {e}")
                continue

        return {
            "viewed_movies": viewed_movies_data,
            "rated_movies": rated_movies_data
        }
    except Exception as e:
        print(f"Error in get_user_library: {e}")
        return {
            "viewed_movies": [],
            "rated_movies": []
        }

@router.post("/movies/{movie_id}/view")
async def record_movie_view(
    movie_id: int,
    completed: bool = False,
    watch_duration: Optional[int] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Check if movie exists
        movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Record viewing history
        view_history = models.ViewingHistory(
            user_id=current_user.id,
            movie_id=movie_id,
            completed=completed,
            watch_duration=watch_duration,
            watched_at=datetime.utcnow()
        )
        db.add(view_history)
        
        # Update movie popularity score
        movie.view_count += 1
        if completed:
            movie.completion_rate = (
                (movie.completion_rate * (movie.view_count - 1) + 1) / movie.view_count
            )
        
        db.commit()
        return {"status": "success", "message": "View recorded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error recording movie view: {e}")
        raise HTTPException(status_code=500, detail="Failed to record view")

@router.delete("/movies/{movie_id}/view")
async def remove_from_library(
    movie_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Delete the viewing history entry
        result = db.query(models.ViewingHistory).filter(
            models.ViewingHistory.user_id == current_user.id,
            models.ViewingHistory.movie_id == movie_id
        ).delete()
        
        if result == 0:
            raise HTTPException(status_code=404, detail="Movie not found in library")
        
        db.commit()
        return {"status": "success", "message": "Movie removed from library"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error removing from library: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove movie from library")

@router.post("/movies/{movie_id}/rate")
async def rate_movie(
    movie_id: int,
    rating: float,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Rate a movie (1-5 stars)"""
    try:
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
            
        # Check if movie exists
        movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Update or create rating
        user_rating = db.query(models.Rating).filter(
            models.Rating.user_id == current_user.id,
            models.Rating.movie_id == movie_id
        ).first()
        
        if user_rating:
            user_rating.rating = rating
            user_rating.updated_at = datetime.utcnow()
        else:
            user_rating = models.Rating(
                user_id=current_user.id,
                movie_id=movie_id,
                rating=rating
            )
            db.add(user_rating)
        
        # Update movie's average rating
        all_ratings = db.query(models.Rating).filter(
            models.Rating.movie_id == movie_id
        ).all()
        movie.average_rating = sum(r.rating for r in all_ratings) / len(all_ratings)
        movie.rating_count = len(all_ratings)
        
        db.commit()
        return {"status": "success", "message": "Rating recorded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error rating movie: {e}")
        raise HTTPException(status_code=500, detail="Failed to record rating")

@router.post("/movies/", response_model=schemas.Movie)
async def create_movie(
    movie: schemas.MovieCreate, 
    db: Session = Depends(get_db)
):
    """Create a new movie with external API data integration"""
    try:
        return await create_movie_with_external_data(movie, db)
    except Exception as e:
        print(f"Error creating movie: {e}")
        raise HTTPException(status_code=500, detail="Failed to create movie")