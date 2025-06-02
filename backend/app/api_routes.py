from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, text, or_, desc, asc, and_, any_
from sqlalchemy.dialects.postgresql import array
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from . import models, schemas
from .database import get_db
from .auth_utils import get_current_active_user
from .movie_processing import get_recommender
from .external_apis import get_trending_movies_from_tmdb
from .movie_operations import create_movie_with_external_data

router = APIRouter()
logger = logging.getLogger(__name__)

# ========== UTILITY FUNCTIONS ==========

def serialize_movie(movie: models.Movie) -> Dict[str, Any]:
    """Centralized movie serialization to eliminate code duplication"""
    return {
        "id": movie.id,
        "title": movie.title,
        "description": movie.description,
        "release_year": movie.release_year,
        "average_rating": movie.average_rating,
        "imageurl": movie.imageurl,
        "genres": movie.genres or [],
        "imdb_id": movie.imdb_id,
        "imdb_rating": movie.imdb_rating,
        "imdb_votes": movie.imdb_votes,
        "trailer_url": movie.trailer_url,
        "cast": movie.cast or [],
        "crew": movie.crew or [],
        "content_rating": movie.content_rating,
        "mood_tags": movie.mood_tags or [],
        "streaming_platforms": movie.streaming_platforms or []
    }

def build_movie_filters(
    query,
    genres: Optional[str] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    cast_crew: Optional[str] = None,
    search: Optional[str] = None,
    search_type: Optional[str] = None,
    content_rating: Optional[str] = None,
    mood_tags: Optional[str] = None,
    streaming_platforms: Optional[str] = None,
    release_date_lte: Optional[str] = None
):
    """Centralized filter building with fixed array operations"""
    
    # Search filters
    if search and search_type:
        search_lower = search.lower()
        if search_type == "cast_crew":
            # Use array operations for better performance
            query = query.filter(
                or_(
                    func.array_to_string(models.Movie.cast, ',').ilike(f"%{search_lower}%"),
                    func.array_to_string(models.Movie.crew, ',').ilike(f"%{search_lower}%")
                )
            )
        elif search_type == "title":
            query = query.filter(models.Movie.title.ilike(f"%{search_lower}%"))
    
    # Legacy cast_crew filter (for backward compatibility)
    if cast_crew:
        cast_crew_lower = cast_crew.lower()
        query = query.filter(
            or_(
                func.array_to_string(models.Movie.cast, ',').ilike(f"%{cast_crew_lower}%"),
                func.array_to_string(models.Movie.crew, ',').ilike(f"%{cast_crew_lower}%")
            )
        )
    
    # FIXED: Genre filter using proper array operations
    if genres:
        genre_list = [g.strip() for g in genres.split(',')]
        # Use OR conditions to match any of the genres
        conditions = [models.Movie.genres.any(genre) for genre in genre_list]
        query = query.filter(or_(*conditions))
    
    # Year filters
    if min_year:
        query = query.filter(models.Movie.release_year >= min_year)
    if max_year:
        query = query.filter(models.Movie.release_year <= max_year)
    
    # Rating filters
    if min_rating is not None:
        query = query.filter(models.Movie.imdb_rating >= min_rating)
    if max_rating is not None:
        query = query.filter(models.Movie.imdb_rating <= max_rating)
    
    # Content rating filter
    if content_rating:
        content_rating_list = [cr.strip() for cr in content_rating.split(',')]
        query = query.filter(models.Movie.content_rating.in_(content_rating_list))
    
    # FIXED: Mood tags filter using proper array operations
    if mood_tags:
        mood_list = [m.strip() for m in mood_tags.split(',')]
        # Use OR conditions to match any of the mood tags
        conditions = [models.Movie.mood_tags.any(mood) for mood in mood_list]
        query = query.filter(or_(*conditions))
    
    # FIXED: Streaming platforms filter using proper array operations
    if streaming_platforms:
        platform_list = [p.strip() for p in streaming_platforms.split(',')]
        # Use OR conditions to match any of the streaming platforms
        conditions = [models.Movie.streaming_platforms.any(platform) for platform in platform_list]
        query = query.filter(or_(*conditions))
    
    # Release date filter
    if release_date_lte:
        try:
            release_date = datetime.strptime(release_date_lte, '%Y-%m-%d')
            query = query.filter(models.Movie.release_date <= release_date)
        except ValueError:
            logger.warning(f"Invalid date format: {release_date_lte}")
    
    return query

def apply_sort(query, sort: str, request: Request):
    """Centralized sorting logic"""
    if sort == "imdb_rating_desc":
        return query.order_by(desc(models.Movie.imdb_rating))
    elif sort == "imdb_rating_asc":
        return query.order_by(asc(models.Movie.imdb_rating))
    elif sort == "release_date_desc":
        return query.order_by(desc(models.Movie.release_date))
    elif sort == "release_date_asc":
        return query.order_by(asc(models.Movie.release_date))
    elif sort == "title_asc":
        return query.order_by(asc(models.Movie.title))
    elif sort == "title_desc":
        return query.order_by(desc(models.Movie.title))
    elif sort == "popularity_desc":
        return query.order_by(desc(models.Movie.popularity_score))
    elif sort == "random":
        random_seed = request.query_params.get('random_seed')
        if random_seed:
            try:
                seed_int = int(random_seed)
                # Use PostgreSQL's setseed for deterministic random
                return query.order_by(func.random()).execution_options(
                    compiled_cache={},
                    before_cursor_execute=lambda conn, cursor, statement, parameters, context, executemany: 
                    conn.execute(text(f"SELECT setseed({seed_int / 1000000.0})"))
                )
            except ValueError:
                pass
        return query.order_by(func.random())
    else:
        # Default sort
        return query.order_by(desc(models.Movie.imdb_rating))

# ========== HEALTH CHECK ROUTES ==========

@router.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT COUNT(*) FROM movies")).scalar()
        return {"status": "ok", "movie_count": result}
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection test failed: {str(e)}")

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

# ========== MOVIE ROUTES ==========

@router.get("/movies/", response_model=schemas.PaginatedMovieResponse)
def get_movies(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=100),
    genres: Optional[str] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    sort: str = "imdb_rating_desc",
    cast_crew: Optional[str] = None,
    search: Optional[str] = None,
    search_type: Optional[str] = None,
    content_rating: Optional[str] = None,
    mood_tags: Optional[str] = None,
    streaming_platforms: Optional[str] = None,
    release_date_lte: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Optimized movie listing with efficient filtering and pagination"""
    try:
        # Build base query
        query = db.query(models.Movie)
        
        # Apply filters
        query = build_movie_filters(
            query, genres, min_year, max_year, min_rating, max_rating,
            cast_crew, search, search_type, content_rating, mood_tags,
            streaming_platforms, release_date_lte
        )
        
        # Apply sorting
        query = apply_sort(query, sort, request)
        
        # Get total count before pagination
        total_movies = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        movies = query.offset(offset).limit(per_page).all()
        
        # Calculate pagination metadata
        total_pages = (total_movies + per_page - 1) // per_page
        
        # Serialize movies
        movie_list = [serialize_movie(movie) for movie in movies]
        
        # FIXED: Use nested pagination structure
        return {
            "items": movie_list,
            "pagination": {
                "total": total_movies,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        logger.error(f"Error in get_movies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch movies")

@router.get("/movies/search/", response_model=schemas.PaginatedMovieResponse)
def search_movies(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=100),
    search_type: str = Query("cast_crew", regex="^(cast_crew|title)$"),
    db: Session = Depends(get_db)
):
    """Optimized movie search with better performance"""
    try:
        # Build search query
        db_query = db.query(models.Movie)
        query_lower = query.lower()
        
        if search_type == "cast_crew":
            db_query = db_query.filter(
                or_(
                    func.array_to_string(models.Movie.cast, ',').ilike(f"%{query_lower}%"),
                    func.array_to_string(models.Movie.crew, ',').ilike(f"%{query_lower}%")
                )
            )
        elif search_type == "title":
            db_query = db_query.filter(models.Movie.title.ilike(f"%{query_lower}%"))
        
        # Order by relevance (could be enhanced with full-text search)
        db_query = db_query.order_by(desc(models.Movie.popularity_score))
        
        # Get total and paginate
        total_movies = db_query.count()
        offset = (page - 1) * per_page
        movies = db_query.offset(offset).limit(per_page).all()
        
        total_pages = (total_movies + per_page - 1) // per_page
        movie_list = [serialize_movie(movie) for movie in movies]
        
        # FIXED: Use nested pagination structure
        return {
            "items": movie_list,
            "pagination": {
                "total": total_movies,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        logger.error(f"Error in search_movies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search movies")

@router.get("/movies/recommended/", response_model=schemas.PaginatedMovieResponse)
async def get_recommended_movies(
    current_user: models.User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Optimized recommendations with better caching"""
    try:
        # Get user's viewing history with a single query
        recently_viewed = db.query(models.ViewingHistory.movie_id)\
            .filter(models.ViewingHistory.user_id == current_user.id)\
            .order_by(desc(models.ViewingHistory.watched_at))\
            .limit(10)\
            .all()
        
        recently_viewed_ids = [vh.movie_id for vh in recently_viewed]
        
        # Get recommendations
        recommender = get_recommender()
        recommended_ids = recommender.get_hybrid_recommendations(
            user_id=current_user.id,
            recently_viewed=recently_viewed_ids
        )
        
        # Paginate recommendations
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_recommended_ids = recommended_ids[start_idx:end_idx]
        
        if not page_recommended_ids:
            # FIXED: Use nested pagination structure
            return {
                "items": [],
                "pagination": {
                    "total": len(recommended_ids),
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (len(recommended_ids) + per_page - 1) // per_page,
                    "has_next": False,
                    "has_prev": page > 1
                }
            }
        
        # Fetch movie details in correct order
        movies_dict = {movie.id: movie for movie in 
                      db.query(models.Movie).filter(models.Movie.id.in_(page_recommended_ids)).all()}
        
        # Maintain recommendation order
        ordered_movies = [movies_dict[movie_id] for movie_id in page_recommended_ids if movie_id in movies_dict]
        
        total_recommendations = len(recommended_ids)
        total_pages = (total_recommendations + per_page - 1) // per_page
        movie_list = [serialize_movie(movie) for movie in ordered_movies]
        
        # FIXED: Use nested pagination structure
        return {
            "items": movie_list,
            "pagination": {
                "total": total_recommendations,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        logger.error(f"Error in get_recommended_movies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@router.get("/movies/trending/", response_model=schemas.PaginatedMovieResponse)
def get_trending_movies(
    time_window: str = Query("month", regex="^(day|week|month)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Optimized trending movies with better error handling"""
    try:
        tmdb_data = get_trending_movies_from_tmdb(time_window, page)
        
        if not tmdb_data or "results" not in tmdb_data:
            # FIXED: Use nested pagination structure
            return {
                "items": [],
                "pagination": {
                    "total": 0,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": 1,
                    "has_next": False,
                    "has_prev": page > 1
                }
            }
        
        # Extract titles and years for batch lookup
        movie_lookups = []
        for tmdb_movie in tmdb_data.get("results", [])[:per_page]:
            try:
                if tmdb_movie.get("release_date"):
                    release_year = int(tmdb_movie["release_date"][:4])
                    movie_lookups.append((tmdb_movie["title"], release_year))
            except (ValueError, TypeError):
                continue
        
        if not movie_lookups:
            # FIXED: Use nested pagination structure
            return {
                "items": [],
                "pagination": {
                    "total": 0,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": 1,
                    "has_next": False,
                    "has_prev": page > 1
                }
            }
        
        # Batch lookup movies
        conditions = []
        for title, year in movie_lookups:
            conditions.append(
                and_(models.Movie.title == title, models.Movie.release_year == year)
            )
        
        movies = db.query(models.Movie).filter(or_(*conditions)).all() if conditions else []
        movie_list = [serialize_movie(movie) for movie in movies]
        
        # FIXED: Use nested pagination structure
        return {
            "items": movie_list,
            "pagination": {
                "total": len(movie_list),
                "page": page,
                "per_page": per_page,
                "total_pages": tmdb_data.get("total_pages", 1),
                "has_next": page < tmdb_data.get("total_pages", 1),
                "has_prev": page > 1
            }
        }
    except Exception as e:
        logger.error(f"Error in get_trending_movies: {str(e)}")
        # FIXED: Use nested pagination structure
        return {
            "items": [],
            "pagination": {
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 1,
                "has_next": False,
                "has_prev": page > 1
            }
        }

# ========== USER LIBRARY ROUTES ==========

@router.get("/users/me/library")
async def get_user_library(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Optimized user library with eager loading"""
    try:
        # Get viewing history with movie details in a single query
        viewed_query = db.query(models.ViewingHistory)\
            .options(selectinload(models.ViewingHistory.movie))\
            .filter(models.ViewingHistory.user_id == current_user.id)\
            .order_by(models.ViewingHistory.watched_at.desc())
        
        # Get rated movies with movie details in a single query
        rated_query = db.query(models.Rating)\
            .options(selectinload(models.Rating.movie))\
            .filter(models.Rating.user_id == current_user.id)\
            .order_by(models.Rating.created_at.desc())
        
        viewed_movies = viewed_query.all()
        rated_movies = rated_query.all()
        
        # Serialize with movie details
        viewed_movies_data = []
        for vh in viewed_movies:
            if vh.movie:  # Ensure movie exists
                movie_data = serialize_movie(vh.movie)
                movie_data.update({
                    "watched_at": vh.watched_at,
                    "completed": vh.completed
                })
                viewed_movies_data.append(movie_data)
        
        rated_movies_data = []
        for rm in rated_movies:
            if rm.movie:  # Ensure movie exists
                movie_data = serialize_movie(rm.movie)
                movie_data.update({
                    "rating": rm.rating,
                    "rated_at": rm.created_at
                })
                rated_movies_data.append(movie_data)
        
        return {
            "viewed_movies": viewed_movies_data,
            "rated_movies": rated_movies_data
        }
    except Exception as e:
        logger.error(f"Error in get_user_library: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user library")

@router.post("/movies/{movie_id}/view")
async def record_movie_view(
    movie_id: int,
    completed: bool = False,
    watch_duration: Optional[int] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Optimized movie view recording with atomic updates"""
    try:
        # Check if movie exists
        movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Upsert viewing history (update if exists, create if not)
        existing_view = db.query(models.ViewingHistory).filter(
            models.ViewingHistory.user_id == current_user.id,
            models.ViewingHistory.movie_id == movie_id
        ).first()
        
        if existing_view:
            existing_view.completed = completed
            existing_view.watch_duration = watch_duration
            existing_view.watched_at = datetime.utcnow()
        else:
            view_history = models.ViewingHistory(
                user_id=current_user.id,
                movie_id=movie_id,
                completed=completed,
                watch_duration=watch_duration,
                watched_at=datetime.utcnow()
            )
            db.add(view_history)
            
            # Update movie stats (only for new views)
            movie.view_count += 1
        
        # Update completion rate if completed
        if completed:
            total_views = db.query(models.ViewingHistory)\
                .filter(models.ViewingHistory.movie_id == movie_id)\
                .count()
            completed_views = db.query(models.ViewingHistory)\
                .filter(
                    models.ViewingHistory.movie_id == movie_id,
                    models.ViewingHistory.completed == True
                ).count()
            
            movie.completion_rate = completed_views / total_views if total_views > 0 else 0
        
        db.commit()
        return {"status": "success", "message": "View recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error recording view: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record view")

@router.delete("/movies/{movie_id}/view")
async def remove_from_library(
    movie_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove movie from user's viewing history"""
    try:
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
        logger.error(f"Error removing from library: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove movie from library")

@router.post("/movies/{movie_id}/rate")
async def rate_movie(
    movie_id: int,
    rating: float = Query(..., ge=1, le=5),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Optimized movie rating with atomic average calculation"""
    try:
        # Check if movie exists
        movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Upsert rating
        existing_rating = db.query(models.Rating).filter(
            models.Rating.user_id == current_user.id,
            models.Rating.movie_id == movie_id
        ).first()
        
        if existing_rating:
            existing_rating.rating = rating
            existing_rating.updated_at = datetime.utcnow()
        else:
            user_rating = models.Rating(
                user_id=current_user.id,
                movie_id=movie_id,
                rating=rating
            )
            db.add(user_rating)
        
        # Recalculate movie's average rating efficiently
        avg_result = db.query(
            func.avg(models.Rating.rating).label('avg_rating'),
            func.count(models.Rating.id).label('rating_count')
        ).filter(models.Rating.movie_id == movie_id).first()
        
        movie.average_rating = float(avg_result.avg_rating) if avg_result.avg_rating else 0.0
        movie.rating_count = avg_result.rating_count
        
        db.commit()
        return {"status": "success", "message": "Rating recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error rating movie: {str(e)}")
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
        logger.error(f"Error creating movie: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create movie")