from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text  
import os
import time

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./movie_recommender.db")

# Print the database URL (with credentials removed) for debugging
safe_url = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
print(f"Connecting to database at: {safe_url}")

# Handle special Render PostgreSQL URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine based on database type
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration with connection pooling and retry
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 30,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session with retry logic"""
    retries = 5
    delay = 1
    last_exception = None
    
    for attempt in range(retries):
        try:
            db = SessionLocal()
            # Test the connection
            db.execute(text("SELECT 1"))
            return db
        except Exception as e:
            last_exception = e
            if attempt == retries - 1:
                print(f"Failed to connect to database after {retries} attempts: {str(e)}")
                raise
            print(f"Database connection attempt {attempt + 1} failed, retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff
        finally:
            if 'db' in locals():
                db.close()
    
    if last_exception:
        raise last_exception