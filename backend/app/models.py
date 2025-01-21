# models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Table
from sqlalchemy.orm import relationship
from .database import Base

# User-Movie Rating Association Table remains the same
user_movie_ratings = Table(
    'user_movie_ratings',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('movie_id', Integer, ForeignKey('movies.id'), primary_key=True),
    Column('rating', Float)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    ratings = relationship("Movie", secondary=user_movie_ratings, back_populates="rated_by")
    
class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    genres = Column(String)  # Store as comma-separated values
    release_year = Column(Integer)
    average_rating = Column(Float, default=0.0)
    imageUrl = Column(String)  # Added this line for movie posters
    
    # Relationships
    rated_by = relationship("User", secondary=user_movie_ratings, back_populates="ratings")