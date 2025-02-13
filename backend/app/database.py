from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text  
import os
import time

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL environment variable set")

# Extract host from DATABASE_URL for logging
try:
    print(f"Attempting to connect to database...")
    
    # Configure engine for Supabase with SSL required
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,  # Reduced pool size
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 60,  # Increased timeout
            "application_name": "movie_recommender",
            "sslmode": "require",
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "options": "-c timezone=utc"
        }
    )

except Exception as e:
    print(f"Error configuring database engine: {str(e)}")
    raise

# Add event listeners for debugging
@event.listens_for(engine, 'connect')
def receive_connect(dbapi_connection, connection_record):
    print("Database connection established")
    cursor = dbapi_connection.cursor()
    cursor.execute('SELECT version()')
    version = cursor.fetchone()
    print(f"Connected to: {version}")

@event.listens_for(engine, 'checkout')
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    print("Database connection checked out from pool")

@event.listens_for(engine, 'checkin')
def receive_checkin(dbapi_connection, connection_record):
    print("Database connection returned to pool")

@event.listens_for(engine, "engine_connect")
def engine_connect(conn, branch):
    print("Engine level connection established")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session with proper resource management"""
    db = None
    try:
        db = SessionLocal()
        # Test connection
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        if db:
            db.close()
        raise
    finally:
        if db:
            db.close()

# Additional helper for explicit context management if needed
@contextmanager
def get_db_context():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        print(f"Database context error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()