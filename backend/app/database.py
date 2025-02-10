from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text  
import os
import time

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./movie_recommender.db")

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
    # PostgreSQL configuration with connection pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,  # Number of permanent connections
        max_overflow=10,  # Number of additional connections when pool is full
        pool_timeout=30,  # Timeout for getting connection from pool
        pool_recycle=1800,  # Recycle connections after 30 minutes
        pool_pre_ping=True,  # Enable connection health checks
    )

# Add connection retry logic
def get_db_with_retry(retries=5, backoff=1):
    for attempt in range(retries):
        try:
            db = SessionLocal()
            # Test the connection with proper SQL text
            db.execute(text("SELECT 1"))
            return db
        except Exception as e:
            if attempt == retries - 1:  # Last attempt
                raise Exception(f"Failed to connect to database after {retries} attempts: {str(e)}")
            time.sleep(backoff * (attempt + 1))
            continue

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = None
    try:
        db = get_db_with_retry()
        yield db
    finally:
        if db:
            db.close()