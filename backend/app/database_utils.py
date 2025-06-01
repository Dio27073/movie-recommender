# backend/app/database_utils.py
import asyncio
import time
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import SessionLocal

# Global flag to control the keep alive thread
keep_alive_running = True

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

async def db_keep_alive():
    """Async background task to keep the database connection alive."""
    print("Starting database keep-alive task")
    await asyncio.sleep(10)  # Initial wait

    global keep_alive_running
    while keep_alive_running:
        try:
            # Use async context manager with proper session handling
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                print(f"Keep-alive ping executed at {datetime.utcnow().isoformat()}")
            finally:
                db.close()
        except Exception as e:
            print(f"Database keep-alive error: {str(e)}")

        await asyncio.sleep(120)  # Ping every 2 minutes instead of 10

async def startup_database():
    """Initialize database connection and start keep-alive task"""
    retries = 5
    db = None
    for i in range(retries):
        try:
            db = SessionLocal()
            # Test the connection with proper SQL text
            db.execute(text("SELECT 1"))
            print("Successfully connected to database")
            break
        except Exception as e:
            if i == retries - 1:
                print(f"Failed to initialize database after {retries} attempts: {str(e)}")
                await asyncio.sleep(5)
                raise
            print(f"Database connection attempt {i + 1} failed, retrying in 5 seconds...")
            time.sleep(5)
    
    try:
        # Start the keep-alive task
        asyncio.create_task(db_keep_alive())
        print("Database keep-alive task started")
    except Exception as e:
        print(f"Error during database startup: {str(e)}")
        raise
    finally:
        if db:
            db.close()

async def shutdown_database():
    """Shutdown database connections"""
    global keep_alive_running
    keep_alive_running = False
    print("Shutting down database keep-alive thread")