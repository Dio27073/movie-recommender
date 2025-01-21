# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from . import models, schemas
from .database import SessionLocal, engine

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Movie Recommender")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT settings
SECRET_KEY = "your-secret-key"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Add test data on startup
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    # Check if we already have movies
    if db.query(models.Movie).count() == 0:
        # Add some test movies
        test_movies = [
            {
                "title": "Inception",
                "description": "A thief enters dreams to steal secrets.",
                "genres": ["Action", "Sci-Fi"],
                "release_year": 2010,
                "average_rating": 4.8,
            },
            {
                "title": "The Shawshank Redemption",
                "description": "Two imprisoned men bond over several years.",
                "genres": ["Drama"],
                "release_year": 1994,
                "average_rating": 4.9,
            },
            {
                "title": "The Dark Knight",
                "description": "Batman faces his greatest challenge yet.",
                "genres": ["Action", "Drama", "Crime"],
                "release_year": 2008,
                "average_rating": 4.7,
            },
            {
                "title": "Pulp Fiction",
                "description": "Various interconnected crime stories in Los Angeles.",
                "genres": ["Crime", "Drama"],
                "release_year": 1994,
                "average_rating": 4.8,
            }
        ]
        
        for movie_data in test_movies:
            movie = models.Movie(
                title=movie_data["title"],
                description=movie_data["description"],
                genres=",".join(movie_data["genres"]),  # Join array to string
                release_year=movie_data["release_year"],
                average_rating=movie_data["average_rating"]
            )
            db.add(movie)
        
        db.commit()
    db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/movies/", response_model=List[schemas.Movie])
def get_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    movies = db.query(models.Movie).offset(skip).limit(limit).all()
    # Transform the movies to include genres as arrays
    for movie in movies:
        if movie.genres:
            movie.genres = [genre.strip() for genre in movie.genres.split(",")]
    return movies

@app.post("/movies/", response_model=schemas.Movie)
def create_movie(movie: schemas.MovieCreate, db: Session = Depends(get_db)):
    # Convert genres array to comma-separated string for storage
    movie_dict = movie.dict()
    if isinstance(movie_dict["genres"], list):
        movie_dict["genres"] = ",".join(movie_dict["genres"])
    
    db_movie = models.Movie(**movie_dict)
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    
    # Convert genres back to array for response
    if db_movie.genres:
        db_movie.genres = [genre.strip() for genre in db_movie.genres.split(",")]
    return db_movie

@app.post("/rate/")
def rate_movie(rating: schemas.Rating, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    movie = db.query(models.Movie).filter(models.Movie.id == rating.movie_id).first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Update movie's average rating (simplified version)
    movie.average_rating = rating.rating
    db.commit()
    
    return {"message": "Rating updated successfully"}
