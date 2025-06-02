from contextlib import contextmanager
from sqlalchemy import create_engine, event, text, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
import logging
from typing import Generator
import redis
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL environment variable set")

# OPTIMIZED: More conservative pool settings for free tier
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=2,  # Reduced from 3 for better resource management
    max_overflow=1,  # Allow minimal overflow
    pool_timeout=30,  # Increased timeout for stability
    pool_recycle=1800,  # 30 minutes - longer for fewer reconnections
    pool_pre_ping=True,
    
    connect_args={
        "sslmode": "require",
        "application_name": "movie_recommender",
        # OPTIMIZED: Simpler keepalive settings
        "keepalives": 1,
        "keepalives_idle": 600,  # 10 minutes
        "keepalives_interval": 30,
        "keepalives_count": 3,
        "connect_timeout": 10,
    },
    
    echo=False,
    echo_pool=False,
)

# OPTIMIZED: Apply connection settings only once, not on every connection
_connection_optimized = False

@event.listens_for(engine, "first_connect")
def set_postgresql_optimizations_once(dbapi_connection, connection_record):
    """Apply optimizations only on first connection"""
    global _connection_optimized
    if not _connection_optimized:
        try:
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SET default_statistics_target = 100")
                cursor.execute("SET random_page_cost = 1.1")
                cursor.execute("SET effective_cache_size = '128MB'")
                dbapi_connection.commit()
                logger.info("Applied PostgreSQL optimizations (one-time)")
                _connection_optimized = True
        except Exception as e:
            logger.warning(f"Could not set connection optimizations: {e}")

# Initialize Redis for caching
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    redis_client = None

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()

def get_db() -> Generator:
    """Optimized database dependency"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager with automatic handling"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database context error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

class CacheUtils:
    """Redis caching utilities"""
    
    @staticmethod
    def get(key: str):
        """Get value from cache"""
        if not redis_client:
            return None
        try:
            return redis_client.get(key)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    @staticmethod
    def set(key: str, value: str, ttl: int = 3600):
        """Set value in cache with TTL"""
        if not redis_client:
            return False
        try:
            return redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    @staticmethod
    def delete(key: str):
        """Delete key from cache"""
        if not redis_client:
            return False
        try:
            return redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False

class DatabaseUtils:
    """Optimized database utilities"""
    
    @staticmethod
    def get_table_stats():
        """Get cached database statistics"""
        cache_key = "db_stats"
        cached_stats = CacheUtils.get(cache_key)
        
        if cached_stats:
            import json
            return json.loads(cached_stats)
        
        try:
            with get_db_context() as db:
                stats = {}
                # Single query for all table counts
                result = db.execute(text("""
                    SELECT 
                        'movies' as table_name, COUNT(*) as count FROM movies
                    UNION ALL
                    SELECT 'users', COUNT(*) FROM users
                    UNION ALL  
                    SELECT 'ratings', COUNT(*) FROM ratings
                    UNION ALL
                    SELECT 'viewing_history', COUNT(*) FROM viewing_history
                """))
                
                for row in result:
                    stats[row.table_name] = row.count
                
                # Cache for 5 minutes
                import json
                CacheUtils.set(cache_key, json.dumps(stats), 300)
                return stats
        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return {}
    
    @staticmethod
    def check_connection_health():
        """Quick connection health check"""
        try:
            with get_db_context() as db:
                db.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# REMOVED: Keep-alive task is redundant with pool_pre_ping=True
async def startup_database():
    """Optimized database startup"""
    try:
        logger.info("Starting database initialization...")
        
        # Quick connection test
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_setting('server_version')"))
            version = result.scalar()
            logger.info(f"Connected to PostgreSQL {version}")
        
        # Get stats asynchronously
        stats = DatabaseUtils.get_table_stats()
        logger.info(f"Database ready. Stats: {stats}")
        
    except Exception as e:
        logger.error(f"Database startup failed: {e}")
        raise

async def shutdown_database():
    """Clean shutdown"""
    try:
        logger.info("Shutting down database...")
        engine.dispose()
        if redis_client:
            redis_client.close()
        logger.info("Database shutdown completed")
    except Exception as e:
        logger.error(f"Database shutdown error: {e}")