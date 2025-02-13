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

# Configure engine for Supabase
engine = create_engine(
   DATABASE_URL,
   poolclass=QueuePool,
   pool_size=20,
   max_overflow=10,
   pool_timeout=30,
   pool_recycle=1800,
   pool_pre_ping=True,
   connect_args={
       "connect_timeout": 30,
       "application_name": "movie_recommender",
       "keepalives": 1,
       "keepalives_idle": 30,
       "keepalives_interval": 10,
       "keepalives_count": 5
   }
)

# Add event listeners
@event.listens_for(engine, 'connect')
def receive_connect(dbapi_connection, connection_record):
   print("Database connection established")

@event.listens_for(engine, 'checkout')
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
   print("Database connection checked out from pool")

@event.listens_for(engine, 'checkin')
def receive_checkin(dbapi_connection, connection_record):
   print("Database connection returned to pool")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
   """Get database session with proper resource management"""
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()

# Additional helper for explicit context management if needed
@contextmanager
def get_db_context():
   """Context manager for database sessions"""
   db = SessionLocal()
   try:
       yield db
       db.commit()
   except Exception:
       db.rollback()
       raise
   finally:
       db.close()