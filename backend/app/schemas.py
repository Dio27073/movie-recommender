from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

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


class MovieCreate(MovieBase):
    pass

class Movie(MovieBase):
    id: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class Rating(BaseModel):
    movie_id: int
    rating: float  # 1-5 stars
    
# Add this new class
class PaginatedMovieResponse(BaseModel):
    items: List[Movie]
    total: int
    page: int
    total_pages: int
    has_next: bool
    has_prev: bool