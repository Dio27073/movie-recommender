from contextlib import contextmanager
from sqlalchemy import create_engine, event, text, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
import logging
from typing import Generator

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL environment variable set")

# Optimized engine configuration for cloud deployment
engine = create_engine(
    DATABASE_URL,
    # Optimized pooling for cloud/session pooler
    poolclass=QueuePool,
    pool_size=3,  # Reduced for free tier limits
    max_overflow=0,  # No overflow to prevent connection spikes
    pool_timeout=20,  # Shorter timeout for faster failure detection
    pool_recycle=300,  # 5 minutes - good for cloud connections
    pool_pre_ping=True,  # Essential for cloud reliability
    
    # Connection optimization
    connect_args={
        "sslmode": "require",
        "application_name": "movie_recommender",
        # TCP keepalive settings for cloud stability
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
        # Connection timeouts
        "connect_timeout": 10,
    },
    
    # Performance settings
    echo=False,  # Set to True only for debugging
    echo_pool=False,
    # REMOVED: Redundant execution_options that might conflict
)

# Add connection event listeners for better monitoring
@event.listens_for(engine, "connect")
def set_postgresql_optimizations(dbapi_connection, connection_record):
    """Optimize connection settings on connect"""
    try:
        # Set PostgreSQL-specific optimizations
        with dbapi_connection.cursor() as cursor:
            # Optimize for read-heavy workload
            cursor.execute("SET default_statistics_target = 100")
            cursor.execute("SET random_page_cost = 1.1")  # Good for SSD
            cursor.execute("SET effective_cache_size = '128MB'")  # Conservative for free tier
            dbapi_connection.commit()
            logger.debug("Applied PostgreSQL optimizations")
    except Exception as e:
        logger.warning(f"Could not set connection optimizations: {e}")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkout for monitoring"""
    logger.debug("Connection checked out from pool")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection checkin for monitoring"""
    logger.debug("Connection returned to pool")

# REMOVED: Connection test during module import - this was causing startup failure
# Connection test will be done during startup_database() function instead

# Optimized session configuration
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,  # Manual flush for better control
    bind=engine,
    expire_on_commit=False  # Keep objects usable after commit
)

Base = declarative_base()

# Optimized dependency injection
def get_db() -> Generator:
    """
    Optimized database dependency with proper error handling
    """
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
    """
    Context manager for database sessions with automatic commit/rollback
    """
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

# Database utilities for common operations
class DatabaseUtils:
    """Utility class for common database operations"""
    
    @staticmethod
    def get_table_stats():
        """Get basic statistics about database tables"""
        try:
            with get_db_context() as db:
                stats = {}
                # Get row counts for main tables
                tables = ['movies', 'users', 'ratings', 'viewing_history']
                for table in tables:
                    try:
                        result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        stats[table] = result.scalar()
                    except Exception as e:
                        logger.warning(f"Could not get count for table {table}: {e}")
                        stats[table] = 0
                
                # Get database size
                try:
                    result = db.execute(text("""
                        SELECT pg_size_pretty(pg_database_size(current_database())) as size
                    """))
                    stats['database_size'] = result.scalar()
                except Exception as e:
                    logger.warning(f"Could not get database size: {e}")
                    stats['database_size'] = 'unknown'
                
                return stats
        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return {}
    
    @staticmethod
    def optimize_database():
        """Run database optimization commands"""
        try:
            with get_db_context() as db:
                # Update table statistics
                db.execute(text("ANALYZE"))
                logger.info("Database optimization completed")
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
    
    @staticmethod
    def check_connection_health():
        """Check if database connection is healthy"""
        try:
            with get_db_context() as db:
                db.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Startup and shutdown functions
async def startup_database():
    """Initialize database connections and run startup tasks"""
    try:
        logger.info("Starting database initialization...")
        
        # Test connection and get database info
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT 
                    current_setting('server_version') as version,
                    current_database() as database_name,
                    current_user as user_name
            """))
            row = result.fetchone()
            logger.info(f"Successfully connected to PostgreSQL:")
            logger.info(f"Version: {row.version}")
            logger.info(f"Database: {row.database_name}")
            logger.info(f"User: {row.user_name}")
            
            # Test basic query performance
            result = connection.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
            table_count = result.scalar()
            logger.info(f"Database has {table_count} tables")
        
        # Get initial stats
        stats = DatabaseUtils.get_table_stats()
        logger.info(f"Database initialized. Stats: {stats}")
        
    except Exception as e:
        logger.error(f"Database startup failed: {e}")
        raise

async def shutdown_database():
    """Clean shutdown of database connections"""
    try:
        logger.info("Shutting down database connections...")
        engine.dispose()
        logger.info("Database shutdown completed")
    except Exception as e:
        logger.error(f"Database shutdown error: {e}")

# Connection monitoring
def get_pool_status():
    """Get current connection pool status"""
    try:
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }
    except Exception as e:
        logger.error(f"Error getting pool status: {e}")
        return {"error": str(e)}