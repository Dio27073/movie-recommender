from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime

class MovieBase(BaseModel):
    title: str
    description: Optional[str] = None
    genres: List[str]
    release_year: int
    average_rating: float = Field(default=0.0, ge=0, le=5)
    imageUrl: Optional[str] = None
    imdb_id: Optional[str] = None
    imdb_rating: Optional[float] = Field(default=None, ge=0, le=10)
    imdb_votes: Optional[int] = None
    trailer_url: Optional[str] = None
    cast: Optional[List[str]] = None
    crew: Optional[List[str]] = None
    content_rating: Optional[str] = None
    mood_tags: Optional[List[str]] = None
    streaming_platforms: Optional[List[str]] = None
    
    # New recommendation-related fields
    popularity_score: float = Field(default=0.0, ge=0)
    view_count: int = Field(default=0, ge=0)
    completion_rate: float = Field(default=0.0, ge=0, le=1)
    rating_count: int = Field(default=0, ge=0)
    keywords: Optional[str] = None
    similar_movies: Optional[List[int]] = None

class MovieCreate(MovieBase):
    pass

class Movie(MovieBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserPreferences(BaseModel):
    favorite_genres: Optional[List[str]] = None
    preferred_languages: Optional[List[str]] = None
    content_preferences: Optional[Dict] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    preferences: Optional[UserPreferences] = None

class User(UserBase):
    id: int
    is_active: bool
    favorite_genres: Optional[str] = None
    preferred_languages: Optional[str] = None
    content_preferences: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ViewingHistory(BaseModel):
    movie_id: int
    user_id: int
    watched_at: datetime
    watch_duration: Optional[int] = None
    completed: bool = False

    model_config = ConfigDict(from_attributes=True)

class Rating(BaseModel):
    movie_id: int
    rating: float = Field(ge=0, le=5)
    timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class MovieRecommendation(BaseModel):
    movie_id: int
    title: str
    confidence_score: float = Field(ge=0, le=1)
    recommendation_type: str  # e.g., "content", "collaborative", "hybrid"
    reason: Optional[str] = None  # e.g., "Because you watched X"

class RecommendationResponse(BaseModel):
    recommendations: List[MovieRecommendation]
    generated_at: datetime
    metadata: Optional[Dict] = None

class PaginatedMovieResponse(BaseModel):
    items: List[Movie]
    total: int
    page: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    model_config = ConfigDict(from_attributes=True)

# New schema for recommendation requests
class RecommendationRequest(BaseModel):
    user_id: int
    limit: int = Field(default=10, ge=1, le=50)
    strategy: str = Field(default="hybrid")  # "content", "collaborative", or "hybrid"
    filters: Optional[Dict] = None
    exclude_watched: bool = True

# New schema for recording viewing history
class ViewingHistoryCreate(BaseModel):
    movie_id: int
    watch_duration: Optional[int] = None
    completed: bool = False