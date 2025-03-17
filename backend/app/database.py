from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text  
import os

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL environment variable set")

print(f"Attempting to connect to database using session pooler...")

try:
    engine = create_engine(
        DATABASE_URL,
        # Session pooler specific settings
        pool_size=5,  # Increased for session pooler
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=180,  # 5 minutes
        pool_pre_ping=True,
        connect_args={
            "sslmode": "require",
            "application_name": "movie_recommender",
            # Session pooler specific keepalive settings
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    )
    
    # Verify connection
    with engine.connect() as connection:
        result = connection.execute(text("SELECT current_setting('server_version'), current_setting('server_version_num'), inet_server_addr()"))
        version, version_num, server_addr = result.fetchone()
        print(f"Successfully connected to PostgreSQL:")
        print(f"Version: {version}")
        print(f"Version Number: {version_num}")
        print(f"Server Address: {server_addr}")

except Exception as e:
    print(f"Error configuring database engine: {str(e)}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Simplified get_db function
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"Database session error: {str(e)}")
        raise
    finally:
        db.close()

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