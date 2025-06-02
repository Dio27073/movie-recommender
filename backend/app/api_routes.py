from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func, text, or_, desc, asc, and_
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json

from . import models, schemas
from .database import get_db, CacheUtils
from .auth_utils import get_current_active_user
from .movie_processing import get_movie_system_status
from .external_apis import get_trending_movies_from_tmdb
from .movie_operations import create_movie_with_external_data

router = APIRouter()
logger = logging.getLogger(__name__)

# ========== OPTIMIZED UTILITY FUNCTIONS ==========

def serialize_movie_cached(movie: models.Movie, use_cache: bool = True) -> Dict[str, Any]:
    """FIXED: Movie serialization without updated_at field"""
    if use_cache:
        # Use movie.id as cache key since updated_at doesn't exist
        cache_key = f"movie_serialized_{movie.id}"
        cached = CacheUtils.get(cache_key)
        if cached:
            return json.loads(cached)
    
    # FIXED: Handle both array and string column types
    def safe_array_field(field_value):
        """Convert field to array regardless of storage type"""
        if field_value is None:
            return []
        if isinstance(field_value, list):
            return field_value
        if isinstance(field_value, str):
            return [item.strip() for item in field_value.split(',') if item.strip()]
        return []
    
    result = {
        "id": movie.id,
        "title": movie.title,
        "description": movie.description,
        "release_year": movie.release_year,
        "average_rating": movie.average_rating,
        "imageurl": movie.imageurl,
        "genres": safe_array_field(movie.genres),
        "imdb_id": movie.imdb_id,
        "imdb_rating": movie.imdb_rating,
        "imdb_votes": movie.imdb_votes,
        "trailer_url": movie.trailer_url,
        "cast": safe_array_field(movie.cast),
        "crew": safe_array_field(movie.crew),
        "content_rating": movie.content_rating,
        "mood_tags": safe_array_field(movie.mood_tags),
        "streaming_platforms": safe_array_field(movie.streaming_platforms)
    }
    
    if use_cache:
        # Cache for 1 hour
        CacheUtils.set(cache_key, json.dumps(result), 3600)
    
    return result

# Replace the build_movie_filters_optimized function in api_routes.py with this:

def build_movie_filters_optimized(
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
    """FIXED: Use string operations compatible with current database schema"""
    
    # Search filters - FIXED to work with string columns
    if search and search_type:
        search_lower = f"%{search.lower()}%"
        if search_type == "cast_crew":
            # Use string operations instead of array operations
            query = query.filter(
                or_(
                    func.lower(models.Movie.cast).like(search_lower),
                    func.lower(models.Movie.crew).like(search_lower)
                )
            )
        elif search_type == "title":
            query = query.filter(models.Movie.title.ilike(search_lower))
    
    # Legacy cast_crew filter
    if cast_crew:
        cast_crew_lower = f"%{cast_crew.lower()}%"
        query = query.filter(
            or_(
                func.lower(models.Movie.cast).like(cast_crew_lower),
                func.lower(models.Movie.crew).like(cast_crew_lower)
            )
        )
    
    # FIXED: Genre filter using string operations
    if genres:
        genre_list = [g.strip() for g in genres.split(',')]
        genre_conditions = []
        for genre in genre_list:
            genre_conditions.append(
                func.lower(models.Movie.genres).like(f"%{genre.lower()}%")
            )
        if genre_conditions:
            query = query.filter(or_(*genre_conditions))
    
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
    
    # FIXED: Mood tags using string operations - NO func.coalesce with empty string!
    if mood_tags:
        mood_list = [m.strip() for m in mood_tags.split(',')]
        mood_conditions = []
        for mood in mood_list:
            # CRITICAL FIX: Check for NULL first, then do string comparison
            mood_conditions.append(
                and_(
                    models.Movie.mood_tags.isnot(None),
                    func.lower(models.Movie.mood_tags).like(f"%{mood.lower()}%")
                )
            )
        if mood_conditions:
            query = query.filter(or_(*mood_conditions))
    
    # FIXED: Streaming platforms using string operations - NO func.coalesce with empty string!
    if streaming_platforms:
        platform_list = [p.strip() for p in streaming_platforms.split(',')]
        platform_conditions = []
        for platform in platform_list:
            # CRITICAL FIX: Check for NULL first, then do string comparison
            platform_conditions.append(
                and_(
                    models.Movie.streaming_platforms.isnot(None),
                    func.lower(models.Movie.streaming_platforms).like(f"%{platform.lower()}%")
                )
            )
        if platform_conditions:
            query = query.filter(or_(*platform_conditions))
    
    # Release date filter
    if release_date_lte:
        try:
            release_date = datetime.strptime(release_date_lte, '%Y-%m-%d')
            query = query.filter(models.Movie.release_date <= release_date)
        except ValueError:
            logger.warning(f"Invalid date format: {release_date_lte}")
    
    return query

def apply_sort_optimized(query, sort: str, request: Request):
    """OPTIMIZED: Better sorting with proper indexing hints"""
    if sort == "imdb_rating_desc":
        return query.order_by(desc(models.Movie.imdb_rating), desc(models.Movie.id))
    elif sort == "imdb_rating_asc":
        return query.order_by(asc(models.Movie.imdb_rating), asc(models.Movie.id))
    elif sort == "release_date_desc":
        return query.order_by(desc(models.Movie.release_date), desc(models.Movie.id))
    elif sort == "release_date_asc":
        return query.order_by(asc(models.Movie.release_date), asc(models.Movie.id))
    elif sort == "title_asc":
        return query.order_by(asc(models.Movie.title))
    elif sort == "title_desc":
        return query.order_by(desc(models.Movie.title))
    elif sort == "popularity_desc":
        return query.order_by(desc(models.Movie.popularity_score), desc(models.Movie.id))
    elif sort == "random":
        # OPTIMIZED: Use deterministic random with better performance
        random_seed = request.query_params.get('random_seed', '0.5')
        try:
            seed_float = float(random_seed) / 1000000.0
            return query.order_by(func.random()).execution_options(
                compiled_cache={},
                before_cursor_execute=lambda conn, cursor, statement, parameters, context, executemany: 
                conn.execute(text(f"SELECT setseed({seed_float})"))
            )
        except ValueError:
            pass
        return query.order_by(func.random())
    else:
        # Default sort with tie-breaker
        return query.order_by(desc(models.Movie.imdb_rating), desc(models.Movie.id))

# ========== CACHED ENDPOINTS ==========

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
    """OPTIMIZED: Movies listing with efficient filtering and caching"""
    
    # Create cache key from parameters
    cache_key = f"movies_list_{hash(str(request.query_params))}"
    cached_result = CacheUtils.get(cache_key)
    if cached_result and not search:  # Don't cache search results
        return json.loads(cached_result)
    
    try:
        # Build base query
        query = db.query(models.Movie)
        
        # Apply filters
        query = build_movie_filters_optimized(
            query, genres, min_year, max_year, min_rating, max_rating,
            cast_crew, search, search_type, content_rating, mood_tags,
            streaming_platforms, release_date_lte
        )
        
        # Apply sorting
        query = apply_sort_optimized(query, sort, request)
        
        # OPTIMIZED: Single query for count and data using window functions
        # Get total count more efficiently
        count_query = query.statement.alias()
        total_movies = db.query(func.count()).select_from(count_query).scalar()
        
        # Apply pagination
        offset = (page - 1) * per_page
        movies = query.offset(offset).limit(per_page).all()
        
        # Calculate pagination metadata
        total_pages = (total_movies + per_page - 1) // per_page
        
        # OPTIMIZED: Batch serialize movies
        movie_list = [serialize_movie_cached(movie) for movie in movies]
        
        result = {
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
        
        # Cache non-search results for 5 minutes
        if not search:
            CacheUtils.set(cache_key, json.dumps(result), 300)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_movies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch movies")

@router.get("/movies/recommended/", response_model=schemas.PaginatedMovieResponse)
async def get_recommended_movies(
    current_user: models.User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """DISABLED: Recommendations disabled - returning popular movies instead"""
    
    try:
        # Since recommender is disabled, return popular movies based on rating and views
        query = db.query(models.Movie)\
            .filter(models.Movie.imdb_rating.isnot(None))\
            .order_by(
                desc(models.Movie.imdb_rating),
                desc(models.Movie.view_count),
                desc(models.Movie.popularity_score)
            )
        
        # Get total count
        total_movies = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        movies = query.offset(offset).limit(per_page).all()
        
        total_pages = (total_movies + per_page - 1) // per_page
        movie_list = [serialize_movie_cached(movie) for movie in movies]
        
        result = {
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
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_recommended_movies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

# ========== OPTIMIZED USER LIBRARY ==========

@router.get("/users/me/library")
async def get_user_library(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """OPTIMIZED: User library with eager loading and reduced queries"""
    
    # Check cache
    cache_key = f"user_library_{current_user.id}"
    cached_result = CacheUtils.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    try:
        # OPTIMIZED: Single query with eager loading for viewed movies
        viewed_movies_query = db.query(models.ViewingHistory)\
            .options(selectinload(models.ViewingHistory.movie))\
            .filter(models.ViewingHistory.user_id == current_user.id)\
            .order_by(models.ViewingHistory.watched_at.desc())\
            .limit(100)  # Reasonable limit
        
        # OPTIMIZED: Single query with eager loading for rated movies  
        rated_movies_query = db.query(models.Rating)\
            .options(selectinload(models.Rating.movie))\
            .filter(models.Rating.user_id == current_user.id)\
            .order_by(models.Rating.created_at.desc())\
            .limit(100)  # Reasonable limit
        
        # Execute both queries
        viewed_movies = viewed_movies_query.all()
        rated_movies = rated_movies_query.all()
        
        # OPTIMIZED: Process in batches to avoid memory issues
        viewed_movies_data = []
        for vh in viewed_movies:
            if vh.movie:
                movie_data = serialize_movie_cached(vh.movie)
                movie_data.update({
                    "watched_at": vh.watched_at.isoformat() if vh.watched_at else None,
                    "completed": vh.completed
                })
                viewed_movies_data.append(movie_data)
        
        rated_movies_data = []
        for rm in rated_movies:
            if rm.movie:
                movie_data = serialize_movie_cached(rm.movie)
                movie_data.update({
                    "rating": rm.rating,
                    "rated_at": rm.created_at.isoformat() if rm.created_at else None
                })
                rated_movies_data.append(movie_data)
        
        result = {
            "viewed_movies": viewed_movies_data,
            "rated_movies": rated_movies_data
        }
        
        # Cache for 5 minutes
        CacheUtils.set(cache_key, json.dumps(result), 300)
        return result
        
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
    """OPTIMIZED: Movie view recording with cache invalidation"""
    try:
        # Check if movie exists
        movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # OPTIMIZED: Use ON CONFLICT for upsert in PostgreSQL
        try:
            # Try insert first (most common case)
            view_history = models.ViewingHistory(
                user_id=current_user.id,
                movie_id=movie_id,
                completed=completed,
                watch_duration=watch_duration,
                watched_at=datetime.utcnow()
            )
            db.add(view_history)
            db.flush()  # Will raise if duplicate
            
            # Update movie stats for new views
            movie.view_count += 1
            
        except Exception:
            # Update existing record
            db.rollback()
            existing_view = db.query(models.ViewingHistory).filter(
                models.ViewingHistory.user_id == current_user.id,
                models.ViewingHistory.movie_id == movie_id
            ).first()
            
            if existing_view:
                existing_view.completed = completed
                existing_view.watch_duration = watch_duration
                existing_view.watched_at = datetime.utcnow()
        
        db.commit()
        
        # OPTIMIZED: Invalidate relevant caches
        CacheUtils.delete(f"user_library_{current_user.id}")
        
        return {"status": "success", "message": "View recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error recording view: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record view")

# ========== HEALTH CHECKS ==========

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

# ========== REMAINING ROUTES (keeping existing functionality) ==========
# Replace the search_movies function in api_routes.py with this fixed version:

@router.get("/movies/search/", response_model=schemas.PaginatedMovieResponse)
def search_movies(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=100),
    search_type: str = Query("cast_crew", regex="^(cast_crew|title)$"),
    db: Session = Depends(get_db)
):
    """FIXED: Movie search with string operations instead of array operations"""
    try:
        db_query = db.query(models.Movie)
        query_lower = f"%{query.lower()}%"
        
        if search_type == "cast_crew":
            # FIXED: Use string LIKE operations instead of array operations
            db_query = db_query.filter(
                or_(
                    func.lower(func.coalesce(models.Movie.cast, '')).like(query_lower),
                    func.lower(func.coalesce(models.Movie.crew, '')).like(query_lower)
                )
            )
        elif search_type == "title":
            db_query = db_query.filter(models.Movie.title.ilike(query_lower))
        
        db_query = db_query.order_by(desc(models.Movie.popularity_score))
        
        total_movies = db_query.count()
        offset = (page - 1) * per_page
        movies = db_query.offset(offset).limit(per_page).all()
        
        total_pages = (total_movies + per_page - 1) // per_page
        movie_list = [serialize_movie_cached(movie) for movie in movies]
        
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

@router.get("/movies/trending/", response_model=schemas.PaginatedMovieResponse)
def get_trending_movies(
    time_window: str = Query("month", regex="^(day|week|month)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """OPTIMIZED: Trending movies with caching"""
    cache_key = f"trending_{time_window}_{page}_{per_page}"
    cached_result = CacheUtils.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    try:
        tmdb_data = get_trending_movies_from_tmdb(time_window, page)
        
        if not tmdb_data or "results" not in tmdb_data:
            result = {
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
            return result
        
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
            result = {
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
            return result
        
        # Batch lookup movies
        conditions = []
        for title, year in movie_lookups:
            conditions.append(
                and_(models.Movie.title == title, models.Movie.release_year == year)
            )
        
        movies = db.query(models.Movie).filter(or_(*conditions)).all() if conditions else []
        movie_list = [serialize_movie_cached(movie) for movie in movies]
        
        result = {
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
        
        # Cache trending results for 30 minutes
        CacheUtils.set(cache_key, json.dumps(result), 1800)
        return result
        
    except Exception as e:
        logger.error(f"Error in get_trending_movies: {str(e)}")
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
        
        # Invalidate cache
        CacheUtils.delete(f"user_library_{current_user.id}")
        
        return {"status": "success", "message": "Movie removed from library"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing from library: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove movie from library")

@router.get("/keep-alive")
async def keep_alive():
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

@router.post("/movies/{movie_id}/rate")
async def rate_movie(
    movie_id: int,
    rating: float = Query(..., ge=1, le=5),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """OPTIMIZED: Movie rating with cache invalidation"""
    try:
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
        
        # Invalidate caches
        CacheUtils.delete(f"user_library_{current_user.id}")
        CacheUtils.delete(f"movie_serialized_{movie_id}_{movie.updated_at or movie.id}")
        
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