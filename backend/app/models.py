from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, String, Float, 
    CheckConstraint, DateTime, Text, Index  # REMOVED ARRAY from here
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON, ARRAY  # MOVED ARRAY to here
from .database import Base

class Configuration(Base):
    __tablename__ = "configuration"

    key = Column(String, primary_key=True)
    value = Column(String)
    
class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5'),
        # Composite index for user-movie lookups and user recommendations
        Index('ix_ratings_user_movie', 'user_id', 'movie_id', unique=True),
        Index('ix_ratings_movie_rating', 'movie_id', 'rating'),  # For average calculations
        Index('ix_ratings_created_at', 'created_at'),  # For recent ratings
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete='CASCADE'), nullable=False)
    rating = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="user_ratings")
    movie = relationship("Movie", back_populates="movie_ratings")
    
class ViewingHistory(Base):
    __tablename__ = "viewing_history"
    __table_args__ = (
        # Index for user's viewing history queries
        Index('ix_viewing_history_user_watched', 'user_id', 'watched_at'),
        # Index for movie popularity calculations
        Index('ix_viewing_history_movie_watched', 'movie_id', 'watched_at'),
        # Unique constraint to prevent duplicate entries
        Index('ix_viewing_history_user_movie', 'user_id', 'movie_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete='CASCADE'), nullable=False)
    watched_at = Column(DateTime(timezone=True), server_default=func.now())
    watch_duration = Column(Integer, nullable=True)  # Duration watched in seconds
    completed = Column(Boolean, default=False, nullable=False)
    last_position = Column(Integer, nullable=True)  # Last watched position in seconds
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="viewing_history")
    movie = relationship("Movie", back_populates="views")

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index('ix_users_email', 'email', unique=True),
        Index('ix_users_username', 'username', unique=True),
        Index('ix_users_active', 'is_active'),
    )

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Improved preference storage using JSON
    preferences = Column(JSON, nullable=True)  # Stores all preferences in structured format
    
    # Relationships
    user_ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    viewing_history = relationship("ViewingHistory", back_populates="user", cascade="all, delete-orphan")

class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (
        CheckConstraint('release_year >= 1888'),
        CheckConstraint('imdb_rating >= 0 AND imdb_rating <= 10'),
        CheckConstraint('average_rating >= 0 AND average_rating <= 5'),
        CheckConstraint('popularity_score >= 0'),
        CheckConstraint('completion_rate >= 0 AND completion_rate <= 1'),
        CheckConstraint('recommendation_count >= 0'),
        
        # Optimized indexes for common queries
        Index('ix_movies_title', 'title'),
        Index('ix_movies_release_year', 'release_year'),
        Index('ix_movies_imdb_rating', 'imdb_rating'),
        Index('ix_movies_average_rating', 'average_rating'),
        Index('ix_movies_popularity', 'popularity_score'),
        Index('ix_movies_imdb_id', 'imdb_id', unique=True),
        
        # Composite indexes for common filter combinations
        Index('ix_movies_year_rating', 'release_year', 'imdb_rating'),
        Index('ix_movies_content_rating', 'content_rating'),
        
        # GIN indexes for array and full-text search (PostgreSQL specific)
        Index('ix_movies_genres_gin', 'genres', postgresql_using='gin'),
        Index('ix_movies_cast_gin', 'cast', postgresql_using='gin'),
        Index('ix_movies_crew_gin', 'crew', postgresql_using='gin'),
        Index('ix_movies_mood_tags_gin', 'mood_tags', postgresql_using='gin'),
        Index('ix_movies_streaming_platforms_gin', 'streaming_platforms', postgresql_using='gin'),
    )

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    release_year = Column(Integer, nullable=False)
    release_date = Column(DateTime, nullable=True)
    imageurl = Column(String(500), nullable=True)
    
    # IMDB specific fields
    imdb_id = Column(String(20), unique=True, nullable=True)
    imdb_rating = Column(Float, nullable=True)
    imdb_votes = Column(Integer, nullable=True)
    trailer_url = Column(String(500), nullable=True)

    # Use PostgreSQL ARRAY type for better performance (much better than comma-separated strings)
    genres = Column(ARRAY(String), nullable=True)
    cast = Column(ARRAY(String), nullable=True)  # Remove cast_members duplicate
    crew = Column(ARRAY(String), nullable=True)
    mood_tags = Column(ARRAY(String), nullable=True)
    streaming_platforms = Column(ARRAY(String), nullable=True)
    keywords = Column(ARRAY(String), nullable=True)
    
    # Content Rating
    content_rating = Column(String(10), nullable=True)
    
    # Recommendation system specific fields
    popularity_score = Column(Float, default=0.0, nullable=False)
    average_rating = Column(Float, default=0.0, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    completion_rate = Column(Float, default=0.0, nullable=False)
    
    # Recommendation tracking
    last_recommended_at = Column(DateTime(timezone=True), nullable=True)
    recommendation_count = Column(Integer, default=0, nullable=False)
    similar_movies = Column(ARRAY(Integer), nullable=True)  # Array of movie IDs
    
    # Relationships
    movie_ratings = relationship("Rating", back_populates="movie", cascade="all, delete-orphan")
    views = relationship("ViewingHistory", back_populates="movie", cascade="all, delete-orphan")