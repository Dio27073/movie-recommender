from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, String, Float, Table, 
    CheckConstraint, DateTime, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Configuration(Base):
    __tablename__ = "configuration"

    key = Column(String, primary_key=True)
    value = Column(String)
    
class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete='CASCADE'))
    rating = Column(Float, nullable=False)  # Rating value (e.g., 1-5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="user_ratings")
    movie = relationship("Movie", back_populates="movie_ratings")
    
class ViewingHistory(Base):
    __tablename__ = "viewing_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete='CASCADE'))
    watched_at = Column(DateTime(timezone=True), server_default=func.now())
    watch_duration = Column(Integer, nullable=True)  # Duration watched in seconds
    completed = Column(Boolean, default=False)  # Whether the movie was watched to completion
    
    # Relationships
    user = relationship("User", back_populates="viewing_history")
    movie = relationship("Movie", back_populates="views")
    last_position = Column(Integer, nullable=True)  # Last watched position in seconds
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Recommendation system preferences
    favorite_genres = Column(String(500), nullable=True)  # Comma-separated list of genres
    preferred_languages = Column(String(100), nullable=True)  # Comma-separated list
    content_preferences = Column(String(500), nullable=True)  # JSON string of preferences
    
    # Relationships
    user_ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    viewing_history = relationship("ViewingHistory", back_populates="user", cascade="all, delete-orphan")
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
    recommendation_preferences = Column(String(1000), nullable=True)  # JSON string for storing detailed preferences
    excluded_genres = Column(String(500), nullable=True) 

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(String(2000), nullable=True)
    genres = Column(String(255), nullable=True)
    release_year = Column(Integer, nullable=False)
    imageurl = Column(String(500), nullable=True)
    release_date = Column(DateTime, nullable=True)  # Add this line
    
    # IMDB specific fields
    imdb_id = Column(String(20), unique=True, nullable=True)
    imdb_rating = Column(Float, nullable=True)
    imdb_votes = Column(Integer, nullable=True)
    trailer_url = Column(String(500), nullable=True)

    # Cast and crew
    cast = Column(String(1000), nullable=True)
    cast_members = Column(String(1000), nullable=True)  # Changed from 'cast' to 'cast_members'
    crew = Column(String(1000), nullable=True)
    
    # Recommendation system specific fields
    popularity_score = Column(Float, default=0.0, nullable=False)  # Calculated popularity score
    average_rating = Column(Float, default=0.0, nullable=False)    # Local platform rating
    rating_count = Column(Integer, default=0, nullable=False)      # Number of ratings
    view_count = Column(Integer, default=0, nullable=False)        # Number of views
    completion_rate = Column(Float, default=0.0, nullable=False)   # Percentage of complete views
    
    # Movie features for content-based filtering
    keywords = Column(String(1000), nullable=True)  # Extracted keywords from description
    similar_movies = Column(String(500), nullable=True)  # Comma-separated IDs of similar movies
    
    # Relationships
    movie_ratings = relationship("Rating", back_populates="movie", cascade="all, delete-orphan")
    views = relationship("ViewingHistory", back_populates="movie", cascade="all, delete-orphan")

    # Track when movie was last recommended
    last_recommended_at = Column(DateTime(timezone=True), nullable=True)
    recommendation_count = Column(Integer, default=0, nullable=False) 

    # Content Rating fields
    content_rating = Column(String(10), nullable=True)  # e.g., 'G', 'PG', 'PG-13', 'R'
    
    # Mood tags (comma-separated)
    mood_tags = Column(String(500), nullable=True)  # e.g., 'feel-good,romantic,intense'
    
    # Streaming platforms (comma-separated)
    streaming_platforms = Column(String(500), nullable=True)  # e.g., 'netflix,hulu,prime'

    __table_args__ = (
        CheckConstraint('release_year >= 1888'),
        CheckConstraint('imdb_rating >= 0 AND imdb_rating <= 10'),
        CheckConstraint('average_rating >= 0 AND average_rating <= 5'),
        CheckConstraint('popularity_score >= 0'),
        CheckConstraint('completion_rate >= 0 AND completion_rate <= 1'),
        CheckConstraint('recommendation_count >= 0'),
    )
    