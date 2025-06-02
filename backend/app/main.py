import os
import logging
import time
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv
import uvicorn

from . import models
from .database import engine, startup_database, shutdown_database, DatabaseUtils, CacheUtils
from .movie_processing import init_movie_system_async
from .routers.auth import router as auth_router
from .api_routes import router as api_router
from .admin_routes import router as admin_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Application state
app_state: Dict[str, Any] = {
    "startup_time": None,
    "database_initialized": False,
    "movie_system_initialized": False,
    "background_tasks_started": False
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """OPTIMIZED: Non-blocking application lifecycle management"""
    startup_start = time.time()
    logger.info("Starting Movie Recommender API...")
    
    try:
        # Quick database initialization
        logger.info("Initializing database...")
        await startup_database()
        app_state["database_initialized"] = True
        logger.info("Database initialized successfully")
        
        # OPTIMIZED: Create tables quickly without blocking
        logger.info("Creating database tables...")
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
        
        # OPTIMIZED: Start background initialization instead of blocking
        asyncio.create_task(background_initialization())
        
        # Log quick startup
        startup_time = time.time() - startup_start
        app_state["startup_time"] = startup_time
        logger.info(f"Quick startup completed in {startup_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Movie Recommender API...")
    try:
        await shutdown_database()
        logger.info("Shutdown completed successfully")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

async def background_initialization():
    """OPTIMIZED: Background initialization that doesn't block startup"""
    try:
        logger.info("Starting background initialization...")
        
        # Small delay to let the app start serving requests
        await asyncio.sleep(2)
        
        # Initialize movie system in background (no recommender)
        logger.info("Initializing movie system in background...")
        await init_movie_system_async()
        app_state["movie_system_initialized"] = True
        app_state["background_tasks_started"] = True
        logger.info("Background initialization completed")
        
        # Get and cache initial stats
        stats = DatabaseUtils.get_table_stats()
        logger.info(f"Background initialization done. Database stats: {stats}")
        
    except Exception as e:
        logger.error(f"Background initialization failed: {str(e)}")

# Create FastAPI application with optimized settings
app = FastAPI(
    title="Movie Recommender API",
    description="A sophisticated movie recommendation platform with hybrid filtering",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    # OPTIMIZED: Reduce response overhead
    generate_unique_id_function=lambda route: f"{route.tags[0]}-{route.name}" if route.tags else route.name
)

# ========== OPTIMIZED MIDDLEWARE CONFIGURATION ==========

# Trusted hosts (security)
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1", 
    "0.0.0.0",
    "cineverse1.vercel.app",
    "*.vercel.app",
    "movie-recommender-api-ghby.onrender.com",
    "*.onrender.com"
]

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)

# Gzip compression for better performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# OPTIMIZED: Response caching middleware
@app.middleware("http")
async def cache_control_middleware(request: Request, call_next):
    """Add caching headers for static content"""
    response = await call_next(request)
    
    # Cache static content
    if request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
        response.headers["Cache-Control"] = "public, max-age=3600"
    elif request.url.path in ["/health", "/", "/openapi.json"]:
        response.headers["Cache-Control"] = "public, max-age=300"
    elif request.url.path.startswith("/movies/trending"):
        response.headers["Cache-Control"] = "public, max-age=1800"  # 30 minutes
    else:
        response.headers["Cache-Control"] = "no-cache"
    
    return response

# CORS middleware - optimized configuration
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8000", 
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "https://cineverse1.vercel.app",
]

# Production environment
if os.getenv("ENV") == "production":
    CORS_ORIGINS = [
        "https://cineverse1.vercel.app",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ],
    max_age=3600
)

# OPTIMIZED: Request timing middleware with better logging
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Optimized request timing and monitoring"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    
    # Only log slow requests and errors
    if process_time > 2.0:  # 2 seconds threshold
        logger.warning(f"SLOW: {request.method} {request.url.path} took {process_time:.2f}s")
    elif response.status_code >= 400:
        logger.warning(f"ERROR: {request.method} {request.url.path} -> {response.status_code}")
    
    return response

# ========== OPTIMIZED EXCEPTION HANDLERS ==========

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors efficiently"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Validation failed",
            "errors": exc.errors()[:5],  # Limit error details
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error", 
            "message": exc.detail,
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Internal server error"
        }
    )

# ========== OPTIMIZED ROOT ENDPOINTS ==========

@app.get("/")
async def root():
    """OPTIMIZED: API root endpoint with cached status information"""
    cache_key = "api_root_status"
    cached_result = CacheUtils.get(cache_key)
    
    if cached_result:
        import json
        result = json.loads(cached_result)
        # Update uptime dynamically
        if app_state.get("startup_time"):
            result["uptime_seconds"] = round(time.time() - app_state["startup_time"], 2)
        return result
    
    uptime = time.time() - app_state.get("startup_time", time.time()) if app_state.get("startup_time") else 0
    
    result = {
        "message": "Movie Recommender API",
        "version": "2.0.0",
        "status": "running",
        "uptime_seconds": round(uptime, 2),
        "database_initialized": app_state.get("database_initialized", False),
        "movie_system_initialized": app_state.get("movie_system_initialized", False),
        "background_ready": app_state.get("background_tasks_started", False),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "movies": "/movies/",
            "auth": "/auth/",
            "admin": "/admin/"
        }
    }
    
    # Cache for 5 minutes
    import json
    CacheUtils.set(cache_key, json.dumps(result), 300)
    return result

@app.options("/{path:path}")
async def preflight_handler(path: str):
    """Handle CORS preflight requests efficiently"""
    return {}

@app.get("/health")
async def detailed_health_check():
    """OPTIMIZED: Comprehensive health check with caching"""
    cache_key = "health_check_detailed"
    cached_result = CacheUtils.get(cache_key)
    
    if cached_result:
        import json
        result = json.loads(cached_result)
        # Always update uptime and timestamp
        result["timestamp"] = time.time()
        if app_state.get("startup_time"):
            result["uptime_seconds"] = round(time.time() - app_state["startup_time"], 2)
        return JSONResponse(content=result, status_code=200 if result["status"] == "healthy" else 503)
    
    health_data = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0",
        "uptime_seconds": 0
    }
    
    # Calculate uptime
    if app_state.get("startup_time"):
        health_data["uptime_seconds"] = round(time.time() - app_state["startup_time"], 2)
    
    # Check database health
    try:
        if DatabaseUtils.check_connection_health():
            health_data["database"] = {
                "status": "healthy",
                "initialized": app_state.get("database_initialized", False)
            }
        else:
            health_data["database"] = {"status": "unhealthy"}
            health_data["status"] = "degraded"
    except Exception as e:
        logger.error(f"Health check database error: {e}")
        health_data["database"] = {"status": "error"}
        health_data["status"] = "unhealthy"
    
    # Check movie system
    health_data["movie_system"] = {
        "status": "ready" if app_state.get("movie_system_initialized") else "initializing",
        "initialized": app_state.get("movie_system_initialized", False)
    }
    
    # Background tasks status
    health_data["background_tasks"] = {
        "status": "ready" if app_state.get("background_tasks_started") else "starting"
    }
    
    # Determine overall status
    if health_data["database"].get("status") != "healthy":
        health_data["status"] = "unhealthy"
    
    # Cache for 30 seconds
    import json
    CacheUtils.set(cache_key, json.dumps(health_data), 30)
    
    status_code = 200 if health_data["status"] == "healthy" else 503
    return JSONResponse(content=health_data, status_code=status_code)

# ========== ROUTER INCLUSION ==========

# Include API routers with proper prefixes and tags
app.include_router(
    api_router,
    prefix="",  # Movie routes at root level
    tags=["movies"]
)

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)

app.include_router(
    admin_router,
    prefix="/admin", 
    tags=["administration"]
)

# ========== APPLICATION ENTRY POINT ==========

if __name__ == "__main__":
    # Configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 10000))
    workers = int(os.getenv("WORKERS", 1))
    
    # Development vs Production settings
    if os.getenv("ENV") == "development":
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=True,
            log_level="debug"
        )
    else:
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=workers,
            log_level="info",
            access_log=False  # Reduce logging overhead in production
        )