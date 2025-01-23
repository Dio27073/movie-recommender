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
    description = Column(String(2000), nullable=True)  # Longer text for descriptions
    genres = Column(String(255), nullable=True)  # Store as comma-separated values
    release_year = Column(Integer, nullable=False)
    average_rating = Column(Float, default=0.0, nullable=False)
    imageUrl = Column(String(500), nullable=True)  # URLs can be long
    
    # Add constraints for valid values
    __table_args__ = (
        CheckConstraint('release_year >= 1888'),  # First movie ever made was in 1888
        CheckConstraint('average_rating >= 0 AND average_rating <= 5'),
    )
    
    # Relationships
    rated_by = relationship(
        "User", 
        secondary=user_movie_ratings, 
        back_populates="ratings",
        cascade="all, delete"
    )