# models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Table, CheckConstraint
from sqlalchemy.orm import relationship
from .database import Base

# User-Movie Rating Association Table
user_movie_ratings = Table(
    'user_movie_ratings',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('movie_id', Integer, ForeignKey('movies.id', ondelete='CASCADE'), primary_key=True),
    Column('rating', Float, CheckConstraint('rating >= 0 AND rating <= 5')),  # Ensure rating is between 0 and 5
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    ratings = relationship(
        "Movie", 
        secondary=user_movie_ratings, 
        back_populates="rated_by",
        cascade="all, delete"
    )
    
class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(String(2000), nullable=True)
    genres = Column(String(255), nullable=True)
    release_year = Column(Integer, nullable=False)
    imageUrl = Column(String(500), nullable=True)
    
    # IMDB specific fields
    imdb_id = Column(String(20), unique=True, nullable=True)  # IMDB's unique identifier
    imdb_rating = Column(Float, nullable=True)  # IMDB's rating (0-10)
    imdb_votes = Column(Integer, nullable=True)  # Number of votes on IMDB
    trailer_url = Column(String(500), nullable=True)  # Store trailer URL from TMDB

    
    # Keep average_rating for compatibility, but now it will be derived from IMDB
    average_rating = Column(Float, default=0.0, nullable=False)
    
    __table_args__ = (
        CheckConstraint('release_year >= 1888'),
        CheckConstraint('imdb_rating >= 0 AND imdb_rating <= 10'),
        CheckConstraint('average_rating >= 0 AND average_rating <= 5'),
    )
    
    # Relationships
    rated_by = relationship(
        "User", 
        secondary=user_movie_ratings, 
        back_populates="ratings",
        cascade="all, delete"
    )