from pydantic import BaseModel, EmailStr, Field, ConfigDict, validator, root_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import json

class MovieBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    genres: List[str] = Field(default_factory=list)
    release_year: int = Field(..., ge=1888, le=2030)
    average_rating: float = Field(default=0.0, ge=0, le=5)
    imageurl: Optional[str] = Field(None, max_length=500)
    imdb_id: Optional[str] = Field(None, max_length=20)
    imdb_rating: Optional[float] = Field(None, ge=0, le=10)
    imdb_votes: Optional[int] = Field(None, ge=0)
    trailer_url: Optional[str] = Field(None, max_length=500)
    cast: List[str] = Field(default_factory=list)
    crew: List[str] = Field(default_factory=list)
    content_rating: Optional[str] = Field(None, max_length=10)
    mood_tags: List[str] = Field(default_factory=list)
    streaming_platforms: List[str] = Field(default_factory=list)
    
    # Recommendation-related fields
    popularity_score: float = Field(default=0.0, ge=0)
    view_count: int = Field(default=0, ge=0)
    completion_rate: float = Field(default=0.0, ge=0, le=1)
    rating_count: int = Field(default=0, ge=0)
    keywords: List[str] = Field(default_factory=list)
    similar_movies: List[int] = Field(default_factory=list)

    @validator('genres', 'cast', 'crew', 'mood_tags', 'streaming_platforms', 'keywords', pre=True)
    def ensure_list(cls, v):
        """Convert comma-separated strings to lists for backward compatibility"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v or []

    @validator('similar_movies', pre=True)
    def ensure_int_list(cls, v):
        """Ensure similar_movies is a list of integers"""
        if isinstance(v, str):
            try:
                return [int(item.strip()) for item in v.split(',') if item.strip().isdigit()]
            except:
                return []
        return v or []

class MovieCreate(MovieBase):
    """Schema for creating new movies"""
    pass

class MovieUpdate(BaseModel):
    """Schema for updating existing movies"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    genres: Optional[List[str]] = None
    release_year: Optional[int] = Field(None, ge=1888, le=2030)
    imageurl: Optional[str] = Field(None, max_length=500)
    imdb_id: Optional[str] = Field(None, max_length=20)
    imdb_rating: Optional[float] = Field(None, ge=0, le=10)
    imdb_votes: Optional[int] = Field(None, ge=0)
    trailer_url: Optional[str] = Field(None, max_length=500)
    cast: Optional[List[str]] = None
    crew: Optional[List[str]] = None
    content_rating: Optional[str] = Field(None, max_length=10)
    mood_tags: Optional[List[str]] = None
    streaming_platforms: Optional[List[str]] = None

class Movie(MovieBase):
    """Full movie schema with database fields"""
    id: int
    release_date: Optional[datetime] = None
    last_recommended_at: Optional[datetime] = None
    recommendation_count: int = Field(default=0, ge=0)
    
    model_config = ConfigDict(from_attributes=True)

class UserPreferences(BaseModel):
    """User preference schema using structured data"""
    favorite_genres: List[str] = Field(default_factory=list)
    excluded_genres: List[str] = Field(default_factory=list)
    preferred_languages: List[str] = Field(default_factory=list)
    content_ratings: List[str] = Field(default_factory=list)
    streaming_platforms: List[str] = Field(default_factory=list)
    mood_preferences: List[str] = Field(default_factory=list)
    min_rating: Optional[float] = Field(None, ge=0, le=10)
    max_year: Optional[int] = Field(None, ge=1888, le=2030)
    min_year: Optional[int] = Field(None, ge=1888, le=2030)
    recommendation_weights: Dict[str, float] = Field(default_factory=dict)

    @validator('min_year', 'max_year')
    def validate_year_range(cls, v, values):
        """Ensure year ranges are logical"""
        if 'min_year' in values and values['min_year'] and v:
            if 'max_year' in values and v < values['min_year']:
                raise ValueError('max_year must be greater than min_year')
        return v

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    preferences: Optional[UserPreferences] = None

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_activity: Optional[datetime] = None
    preferences: Optional[UserPreferences] = None
    
    model_config = ConfigDict(from_attributes=True)

    @validator('preferences', pre=True)
    def parse_preferences(cls, v):
        """Parse JSON string preferences to structured data"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class ViewingHistoryBase(BaseModel):
    movie_id: int = Field(..., gt=0)
    watch_duration: Optional[int] = Field(None, ge=0)
    completed: bool = False
    last_position: Optional[int] = Field(None, ge=0)

class ViewingHistoryCreate(ViewingHistoryBase):
    """Schema for creating viewing history entries"""
    pass

class ViewingHistory(ViewingHistoryBase):
    id: int
    user_id: int
    watched_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class RatingBase(BaseModel):
    movie_id: int = Field(..., gt=0)
    rating: float = Field(..., ge=1, le=5)

class RatingCreate(RatingBase):
    """Schema for creating/updating ratings"""
    pass

class Rating(RatingBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class MovieRecommendation(BaseModel):
    movie_id: int
    title: str
    confidence_score: float = Field(ge=0, le=1)
    recommendation_type: str = Field(..., pattern=r'^(content|collaborative|hybrid|trending|popular)$')
    reason: Optional[str] = None
    movie_data: Optional[Movie] = None  # Include full movie data if needed

class RecommendationResponse(BaseModel):
    recommendations: List[MovieRecommendation]
    generated_at: datetime
    user_id: int
    strategy_used: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PaginationMeta(BaseModel):
    """Reusable pagination metadata"""
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=100)
    total_pages: int = Field(..., ge=0)
    has_next: bool
    has_prev: bool

class PaginatedMovieResponse(BaseModel):
    items: List[Movie]
    pagination: PaginationMeta
    
    # Backward compatibility - flatten pagination
    @property
    def total(self):
        return self.pagination.total
    
    @property
    def page(self):
        return self.pagination.page
    
    @property
    def total_pages(self):
        return self.pagination.total_pages
    
    @property
    def has_next(self):
        return self.pagination.has_next
    
    @property
    def has_prev(self):
        return self.pagination.has_prev
    
    model_config = ConfigDict(from_attributes=True)

class MovieFilterRequest(BaseModel):
    """Schema for movie filtering requests"""
    genres: Optional[List[str]] = None
    min_year: Optional[int] = Field(None, ge=1888, le=2030)
    max_year: Optional[int] = Field(None, ge=1888, le=2030)
    min_rating: Optional[float] = Field(None, ge=0, le=10)
    max_rating: Optional[float] = Field(None, ge=0, le=10)
    content_ratings: Optional[List[str]] = None
    mood_tags: Optional[List[str]] = None
    streaming_platforms: Optional[List[str]] = None
    cast_crew: Optional[str] = None
    search: Optional[str] = None
    search_type: Optional[str] = Field("title", pattern=r'^(title|cast_crew)$')
    sort: str = Field("imdb_rating_desc", pattern=r'^(imdb_rating_desc|imdb_rating_asc|release_date_desc|release_date_asc|title_asc|title_desc|popularity_desc|random)$')
    
    @validator('min_year', 'max_year')
    def validate_year_range(cls, v, values):
        if 'min_year' in values and values['min_year'] and v:
            if 'max_year' in values and v < values['min_year']:
                raise ValueError('max_year must be greater than min_year')
        return v

class RecommendationRequest(BaseModel):
    """Schema for recommendation requests"""
    limit: int = Field(default=10, ge=1, le=50)
    strategy: str = Field(default="hybrid", pattern=r'^(content|collaborative|hybrid)$')
    filters: Optional[MovieFilterRequest] = None
    exclude_watched: bool = True
    include_reasons: bool = False

class UserLibraryResponse(BaseModel):
    """Schema for user library data"""
    viewed_movies: List[Dict[str, Any]]  # Movies with viewing metadata
    rated_movies: List[Dict[str, Any]]   # Movies with rating metadata
    statistics: Dict[str, Any] = Field(default_factory=dict)

class HealthCheckResponse(BaseModel):
    """Health check response schema"""
    status: str
    database: str
    timestamp: datetime
    version: Optional[str] = None
    uptime: Optional[float] = None

class ApiResponse(BaseModel):
    """Generic API response wrapper"""
    status: str = Field(..., pattern=r'^(success|error)$')
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Cache-friendly schemas for high-performance endpoints
class MovieSummary(BaseModel):
    """Lightweight movie schema for listings"""
    id: int
    title: str
    release_year: int
    imdb_rating: Optional[float] = None
    imageurl: Optional[str] = None
    genres: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedMovieSummaryResponse(BaseModel):
    """Lightweight paginated response for better performance"""
    items: List[MovieSummary]
    pagination: PaginationMeta
    
    model_config = ConfigDict(from_attributes=True)