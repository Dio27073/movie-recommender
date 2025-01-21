from pydantic import BaseModel, EmailStr
from typing import List, Optional

class MovieBase(BaseModel):
    title: str
    description: Optional[str] = None
    genres: List[str]  # Changed from str to List[str]
    release_year: int
    average_rating: float = 0.0
    imageUrl: Optional[str] = None  # Added this line


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