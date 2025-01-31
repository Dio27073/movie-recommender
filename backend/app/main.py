# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional  # Add Optional here
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from . import models, schemas
from .database import SessionLocal, engine
import time
from sqlalchemy import or_, desc, asc
import requests
import os
from dotenv import load_dotenv
from datetime import timedelta
from jose import JWTError, jwt

# Load environment variables
load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Movie Recommender")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Keys
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "55975ac268099c9f0957d3aafb5eeae8")
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "f8ed048e")  # You'll need to get this from omdbapi.com

# API Base URLs
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
OMDB_BASE_URL = "http://www.omdbapi.com"

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = "your-secret-key-keep-it-secret" # In production, use a proper secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Password verification
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# User authentication
def authenticate_user(db: Session, username_or_email: str, password: str):
    # Try to find user by email or username
    user = db.query(models.User).filter(
        or_(
            models.User.email == username_or_email,
            models.User.username == username_or_email
        )
    ).first()
    
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

# Token creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def fetch_imdb_data(title: str, year: int) -> dict:
    """Fetch IMDB data for a movie using OMDB API"""
    try:
        response = requests.get(
            OMDB_BASE_URL,
            params={
                "apikey": OMDB_API_KEY,
                "t": title,
                "y": year,
                "type": "movie"
            }
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "True":
                return {
                    "imdb_id": data.get("imdbID"),
                    "imdb_rating": float(data.get("imdbRating", 0)) if data.get("imdbRating") != "N/A" else None,
                    "imdb_votes": int(data.get("imdbVotes", "0").replace(",", "")) if data.get("imdbVotes") != "N/A" else None
                }
        return None
    except Exception as e:
        print(f"Error fetching IMDB data for {title} ({year}): {str(e)}")
        return None
    
async def fetch_movie_trailer(tmdb_id: int) -> Optional[str]:
    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/videos",
            params={
                "api_key": TMDB_API_KEY,
                "language": "en-US"
            }
        )
        if response.status_code == 200:
            videos = response.json().get("results", [])
            # Look for official trailers
            trailer = next(
                (
                    video for video in videos 
                    if video["type"].lower() == "trailer" 
                    and video["site"].lower() == "youtube"
                    and video["official"]
                ),
                None
            )
            if trailer:
                return f"https://www.youtube.com/watch?v={trailer['key']}"
    except Exception as e:
        print(f"Error fetching trailer: {str(e)}")
    return None

"""Fetch cast and crew data for a movie using TMDB API."""
async def fetch_movie_cast_crew(tmdb_id: int) -> dict:
    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits",
            params={"api_key": TMDB_API_KEY, "language": "en-US"}
        )
        if response.status_code == 200:
            credits = response.json()
            cast = [actor["name"] for actor in credits.get("cast", [])[:5]]  # Top 5 cast members
            crew = [member["name"] for member in credits.get("crew", []) if member["job"] == "Director"]  # Directors
            return {"cast": cast, "crew": crew}
    except Exception as e:
        print(f"Error fetching cast/crew for movie {tmdb_id}: {str(e)}")
    return {"cast": [], "crew": []}

# User registration endpoint
@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Login endpoint
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

# Get current active user dependency
async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Protected user profile endpoint example
@app.get("/users/me", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user)
):
    return current_user

# Update user profile endpoint
@app.put("/users/me", response_model=schemas.User)
async def update_user_profile(
    user_update: schemas.UserBase,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if new email already exists
    if user_update.email != current_user.email:
        db_user = db.query(models.User).filter(models.User.email == user_update.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if new username already exists
    if user_update.username != current_user.username:
        db_user = db.query(models.User).filter(models.User.username == user_update.username).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Update user profile
    current_user.email = user_update.email
    current_user.username = user_update.username
    db.commit()
    db.refresh(current_user)
    return current_user

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    if db.query(models.Movie).count() == 0:
        total_pages = 150
        processed_movies = set()
        
        for page in range(1, total_pages + 1):
            response = requests.get(
                f"{TMDB_BASE_URL}/movie/popular",
                params={
                    "api_key": TMDB_API_KEY,
                    "language": "en-US",
                    "page": page
                }
            )
            movies_data = response.json()["results"]
            
            for movie_data in movies_data:
                try:
                    if movie_data["id"] in processed_movies:
                        continue

                    movie_details = requests.get(
                        f"{TMDB_BASE_URL}/movie/{movie_data['id']}",
                        params={"api_key": TMDB_API_KEY, "language": "en-US"}
                    ).json()
                    
                    if all(key in movie_data for key in ["title", "overview", "release_date", "vote_average", "poster_path"]):
                        if not movie_data["release_date"]:
                            continue
                            
                        try:
                            release_year = int(movie_data["release_date"][:4])
                        except (ValueError, IndexError):
                            continue

                        # Fetch IMDB data
                        imdb_data = await fetch_imdb_data(movie_data["title"], release_year)
                        
                        cast_crew_data = await fetch_movie_cast_crew(movie_data["id"])

                        # If we have IMDB data, use it for the rating
                        if imdb_data and imdb_data["imdb_rating"]:
                            # Convert IMDB rating (0-10) to our scale (0-5)
                            converted_rating = (imdb_data["imdb_rating"] / 2)
                        else:
                            # Fallback to TMDB rating if no IMDB rating
                            converted_rating = (movie_data["vote_average"] / 2)
                        
                        # Ensure the rating is within our constraints
                        converted_rating = min(max(converted_rating, 0), 5)
                        
                        trailer_url = await fetch_movie_trailer(movie_data["id"])
                    
                        movie = models.Movie(
                            title=movie_data["title"],
                            description=movie_data["overview"],
                            genres=",".join([genre["name"] for genre in movie_details["genres"]]),
                            release_year=release_year,
                            average_rating=converted_rating,
                            imageUrl=f"{TMDB_IMAGE_BASE_URL}{movie_data['poster_path']}",
                            imdb_id=imdb_data["imdb_id"] if imdb_data else None,
                            imdb_rating=imdb_data["imdb_rating"] if imdb_data else None,
                            imdb_votes=imdb_data["imdb_votes"] if imdb_data else None,
                            trailer_url=trailer_url,
                            cast=",".join(cast_crew_data["cast"]),
                            crew=",".join(cast_crew_data["crew"])
                        )
                        db.add(movie)
                        processed_movies.add(movie_data["id"])
                except Exception as e:
                    print(f"Error processing movie {movie_data.get('title', 'Unknown')}: {str(e)}")
                    continue
            
            db.commit()
            time.sleep(0.5)  # Rate limiting
    
    db.close()

@app.get("/movies/", response_model=schemas.PaginatedMovieResponse)
def get_movies(
    page: int = 1, 
    per_page: int = 12, 
    genres: str = None,
    min_year: int = None,
    max_year: int = None,
    min_rating: float = None,
    max_rating: float = None, 
    sort: str = "imdb_rating_desc",
    cast_crew: str = None,  # Add this parameter
    search: str = None,     # Add this for completeness
    search_type: str = None,# Add this for completeness
    db: Session = Depends(get_db)
    ):
    
    offset = (page - 1) * per_page
    query = db.query(models.Movie)
    
    # Add cast/crew filtering
    if cast_crew:
        query = query.filter(
            or_(
                models.Movie.cast.ilike(f"%{cast_crew}%"),
                models.Movie.crew.ilike(f"%{cast_crew}%")
            )
        )

    if search and search_type:
        if search_type == "cast_crew":
            query = query.filter(
                or_(
                    models.Movie.cast.ilike(f"%{search}%"),
                    models.Movie.crew.ilike(f"%{search}%")
                )
            )
        elif search_type == "title":
            query = query.filter(models.Movie.title.ilike(f"%{search}%"))
            
    if genres:
        genre_list = genres.split(',')
        query = query.filter(
            or_(*[models.Movie.genres.like(f"%{genre}%") for genre in genre_list])
        )
    
    if min_year:
        query = query.filter(models.Movie.release_year >= min_year)
    if max_year:
        query = query.filter(models.Movie.release_year <= max_year)
    
    if min_rating is not None:
        query = query.filter(models.Movie.imdb_rating >= min_rating)
    if max_rating is not None:
        query = query.filter(models.Movie.imdb_rating <= max_rating)
    
    if sort:
        if sort == "imdb_rating_desc":
            query = query.order_by(desc(models.Movie.imdb_rating))
        elif sort == "imdb_rating_asc":
            query = query.order_by(asc(models.Movie.imdb_rating))
        elif sort == "release_date_desc":
            query = query.order_by(desc(models.Movie.release_year))
        elif sort == "release_date_asc":
            query = query.order_by(asc(models.Movie.release_year))
        elif sort == "title_asc":
            query = query.order_by(asc(models.Movie.title))
        elif sort == "title_desc":
            query = query.order_by(desc(models.Movie.title))
    
    total_movies = query.count()
    total_pages = (total_movies + per_page - 1) // per_page
    movies = query.offset(offset).limit(per_page).all()
    
    movie_list = []
    for db_movie in movies:
        movie_dict = {
            "id": db_movie.id,
            "title": db_movie.title,
            "description": db_movie.description,
            "release_year": db_movie.release_year,
            "average_rating": db_movie.average_rating,
            "imageUrl": db_movie.imageUrl,
            "genres": db_movie.genres.split(",") if db_movie.genres else [],
            "imdb_id": db_movie.imdb_id,
            "imdb_rating": db_movie.imdb_rating,
            "imdb_votes": db_movie.imdb_votes,
            "trailer_url": db_movie.trailer_url,
            "cast": db_movie.cast.split(",") if db_movie.cast else [],
            "crew": db_movie.crew.split(",") if db_movie.crew else []
        }
        movie_list.append(movie_dict)
    
    return {
        "items": movie_list,
        "total": total_movies,
        "page": page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

@app.get("/movies/search/", response_model=schemas.PaginatedMovieResponse)
def search_movies_by_cast_crew(
    query: str,
    page: int = 1,
    per_page: int = 12,
    db: Session = Depends(get_db),
    search_type: str = "cast_crew" # Add search type parameter
):
    """Search movies by cast or crew members."""
    offset = (page - 1) * per_page
    query = query.lower()
    
    # Search for movies where cast or crew contains the query
    db_query = db.query(models.Movie)
    if search_type == "cast_crew": # Filter by cast or crew
        # Search for movies where cast OR crew contains the query
        db_query = db_query.filter(
            or_(
                models.Movie.cast.ilike(f"%{query}%"), # Contains the name
                models.Movie.crew.ilike(f"%{query}%")
            )
        )
    elif search_type == "title": # Filter by title
        db_query = db_query.filter(models.Movie.title.ilike(f"%{query}%"))
    
    total_movies = db_query.count()
    total_pages = (total_movies + per_page - 1) // per_page
    movies = db_query.offset(offset).limit(per_page).all()
    
    movie_list = []
    for db_movie in movies:
        movie_dict = {
            "id": db_movie.id,
            "title": db_movie.title,
            "description": db_movie.description,
            "release_year": db_movie.release_year,
            "average_rating": db_movie.average_rating,
            "imageUrl": db_movie.imageUrl,
            "genres": db_movie.genres.split(",") if db_movie.genres else [],
            "imdb_id": db_movie.imdb_id,
            "imdb_rating": db_movie.imdb_rating,
            "imdb_votes": db_movie.imdb_votes,
            "trailer_url": db_movie.trailer_url,
            "cast": db_movie.cast.split(",") if db_movie.cast else [],  # Return cast as a list
            "crew": db_movie.crew.split(",") if db_movie.crew else []  # Return crew as a list
        }
        movie_list.append(movie_dict)
    
    return {
        "items": movie_list,
        "total": total_movies,
        "page": page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

@app.post("/movies/", response_model=schemas.Movie)
async def create_movie(movie: schemas.MovieCreate, db: Session = Depends(get_db)):
    # Fetch IMDB data for the movie
    imdb_data = await fetch_imdb_data(movie.title, movie.release_year)
    
    # Convert the genres list to a comma-separated string for storage
    movie_data = movie.model_dump()
    movie_data["genres"] = ",".join(movie_data["genres"]) if movie_data["genres"] else ""
    
    # Add IMDB data if available
    if imdb_data:
        movie_data["imdb_id"] = imdb_data["imdb_id"]
        movie_data["imdb_rating"] = imdb_data["imdb_rating"]
        movie_data["imdb_votes"] = imdb_data["imdb_votes"]
        
        # Update average_rating based on IMDB rating
        if imdb_data["imdb_rating"]:
            movie_data["average_rating"] = imdb_data["imdb_rating"] / 2  # Convert 10-point to 5-point scale
    
    # Fetch trailer URL
    try:
        tmdb_response = requests.get(
            f"{TMDB_BASE_URL}/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": movie.title,
                "year": movie.release_year
            }
        )
        if tmdb_response.status_code == 200:
            results = tmdb_response.json().get("results", [])
            if results:
                tmdb_id = results[0]["id"]
                trailer_url = await fetch_movie_trailer(tmdb_id)
                movie_data["trailer_url"] = trailer_url
    except Exception as e:
        print(f"Error fetching trailer for {movie.title}: {str(e)}")
    
    db_movie = models.Movie(**movie_data)
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    
    # Convert back to the format expected by the schema
    return {
        "id": db_movie.id,
        "title": db_movie.title,
        "description": db_movie.description,
        "release_year": db_movie.release_year,
        "average_rating": db_movie.average_rating,
        "imageUrl": db_movie.imageUrl,
        "genres": db_movie.genres.split(",") if db_movie.genres else [],
        "imdb_id": db_movie.imdb_id,
        "imdb_rating": db_movie.imdb_rating,
        "imdb_votes": db_movie.imdb_votes,
        "trailer_url": db_movie.trailer_url
    }