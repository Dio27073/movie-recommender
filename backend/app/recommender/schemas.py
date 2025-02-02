from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MovieBase(BaseModel):
    title: str
    release_year: int
    genres: str
    director: str
    cast: str
    description: str
    poster_url: Optional[str] = None
    imdb_rating: Optional[float] = None

class MovieCreate(MovieBase):
    pass

class Movie(MovieBase):
    id: int
    popularity_score: float
    average_rating: float

    class Config:
        from_attributes = True

class RatingBase(BaseModel):
    rating: float

class RatingCreate(RatingBase):
    movie_id: int

class Rating(RatingBase):
    id: int
    user_id: int
    movie_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MovieRecommendation(BaseModel):
    movie_id: int
    title: str
    confidence_score: float
    genres: Optional[str] = None
    poster_url: Optional[str] = None
    
class RecommendationResponse(BaseModel):
    recommendations: List[MovieRecommendation]
    generated_at: datetime = datetime.now()
    
class UserPreferences(BaseModel):
    favorite_genres: List[str] = []
    preferred_release_years: Optional[tuple[int, int]] = None
    minimum_rating: Optional[float] = None