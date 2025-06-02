# backend/cleanup_database_arrays.py
"""
Script to clean up PostgreSQL array fields in the database.
This version handles array types correctly.
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from app.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_database_arrays():
    """Clean up PostgreSQL array fields correctly"""
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        logger.info("Starting array database cleanup...")
        
        # First, let's check the actual column types
        logger.info("Checking actual database schema...")
        schema_check = """
        SELECT column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_name = 'movies' 
        AND column_name IN ('streaming_platforms', 'mood_tags', 'genres', 'cast', 'crew', 'keywords', 'similar_movies')
        ORDER BY column_name;
        """
        
        result = db.execute(text(schema_check))
        columns_info = result.fetchall()
        
        logger.info("Database schema for array-like columns:")
        for row in columns_info:
            logger.info(f"  {row.column_name}: {row.data_type} ({row.udt_name})")
        
        # Array-compatible cleanup queries
        cleanup_queries = [
            # Handle array fields - set empty arrays to NULL
            '''
            UPDATE movies 
            SET streaming_platforms = NULL 
            WHERE streaming_platforms = ARRAY[]::text[] OR array_length(streaming_platforms, 1) IS NULL;
            ''',
            
            '''
            UPDATE movies 
            SET mood_tags = NULL 
            WHERE mood_tags = ARRAY[]::text[] OR array_length(mood_tags, 1) IS NULL;
            ''',
            
            '''
            UPDATE movies 
            SET genres = NULL 
            WHERE genres = ARRAY[]::text[] OR array_length(genres, 1) IS NULL;
            ''',
            
            # Handle "cast" column (reserved word - needs quotes)
            '''
            UPDATE movies 
            SET "cast" = NULL 
            WHERE "cast" = ARRAY[]::text[] OR array_length("cast", 1) IS NULL;
            ''',
            
            '''
            UPDATE movies 
            SET crew = NULL 
            WHERE crew = ARRAY[]::text[] OR array_length(crew, 1) IS NULL;
            ''',
            
            '''
            UPDATE movies 
            SET keywords = NULL 
            WHERE keywords = '' OR keywords IS NULL;
            ''',
            
            '''
            UPDATE movies 
            SET similar_movies = NULL 
            WHERE similar_movies = '' OR similar_movies IS NULL;
            '''
        ]
        
        # Execute cleanup queries with proper transaction handling
        for i, query in enumerate(cleanup_queries, 1):
            try:
                # Start fresh transaction for each query
                db.rollback()  # Clear any previous transaction state
                
                result = db.execute(text(query))
                rows_affected = result.rowcount
                db.commit()
                
                logger.info(f"Array cleanup query {i}: {rows_affected} rows updated")
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error in array cleanup query {i}: {e}")
                # Continue with next query
                continue
        
        # Verification query (array-compatible)
        try:
            verification_query = """
            SELECT 
                COUNT(*) as total_movies,
                COUNT(*) FILTER (WHERE streaming_platforms IS NULL OR array_length(streaming_platforms, 1) IS NULL) as null_streaming,
                COUNT(*) FILTER (WHERE mood_tags IS NULL OR array_length(mood_tags, 1) IS NULL) as null_moods,
                COUNT(*) FILTER (WHERE genres IS NULL OR array_length(genres, 1) IS NULL) as null_genres
            FROM movies;
            """
            
            result = db.execute(text(verification_query))
            stats = result.fetchone()
            
            logger.info("Post-cleanup statistics:")
            logger.info(f"  Total movies: {stats.total_movies}")
            logger.info(f"  NULL streaming_platforms: {stats.null_streaming}")
            logger.info(f"  NULL mood_tags: {stats.null_moods}")
            logger.info(f"  NULL genres: {stats.null_genres}")
            
        except Exception as e:
            logger.error(f"Error in verification: {e}")
        
        logger.info("Array database cleanup completed!")
        
    except Exception as e:
        logger.error(f"Error during database cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        cleanup_database_arrays()
        print("\n✅ Array database cleanup completed successfully!")
        print("You can now restart your FastAPI server.")
    except Exception as e:
        print(f"\n❌ Array database cleanup failed: {e}")
        sys.exit(1)