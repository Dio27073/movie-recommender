import os
import logging
import time
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
from .database import engine, startup_database, shutdown_database, DatabaseUtils
from .movie_processing import init_recommender_async
from .recommender.engine import router as recommender_router
from .routers.auth import router as auth_router
from .api_routes import router as api_router
from .admin_routes import router as admin_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        # Add file handler for production
        # logging.FileHandler('app.log') if os.getenv('ENV') == 'production' else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Application state
app_state: Dict[str, Any] = {
    "startup_time": None,
    "database_initialized": False,
    "recommender_initialized": False
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Optimized application lifecycle management"""
    # Startup
    startup_start = time.time()
    logger.info("Starting Movie Recommender API...")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        await startup_database()
        app_state["database_initialized"] = True
        logger.info("Database initialized successfully")
        
        # Create database tables
        logger.info("Creating database tables...")
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
        
        # Initialize recommender system
        logger.info("Initializing recommender system...")
        await init_recommender_async()
        app_state["recommender_initialized"] = True
        logger.info("Recommender system initialized successfully")
        
        # Log startup stats
        startup_time = time.time() - startup_start
        app_state["startup_time"] = startup_time
        
        stats = DatabaseUtils.get_table_stats()
        logger.info(f"Startup completed in {startup_time:.2f}s. Database stats: {stats}")
        
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

# Create FastAPI application
app = FastAPI(
    title="Movie Recommender API",
    description="A sophisticated movie recommendation platform with hybrid filtering",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ========== MIDDLEWARE CONFIGURATION ==========

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

# CORS middleware - optimized configuration
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8000", 
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "https://cineverse1.vercel.app",
    "https://*.vercel.app"
]

# In production, be more restrictive
if os.getenv("ENV") == "production":
    CORS_ORIGINS = [
        "https://cineverse1.vercel.app",
        "https://*.vercel.app"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
    max_age=3600
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request timing and logging"""
    start_time = time.time()
    
    # Log request
    logger.debug(f"{request.method} {request.url}")
    
    response = await call_next(request)
    
    # Calculate process time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 1.0:  # Log requests slower than 1 second
        logger.warning(f"Slow request: {request.method} {request.url} took {process_time:.2f}s")
    
    return response

# ========== EXCEPTION HANDLERS ==========

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Validation failed",
            "errors": exc.errors(),
            "timestamp": time.time()
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP exception on {request.url}: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error", 
            "message": exc.detail,
            "timestamp": time.time()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error on {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Internal server error",
            "timestamp": time.time()
        }
    )

# ========== ROOT ENDPOINTS ==========

@app.get("/")
async def root():
    """API root endpoint with status information"""
    uptime = time.time() - app_state.get("startup_time", time.time()) if app_state.get("startup_time") else 0
    
    return {
        "message": "Movie Recommender API",
        "version": "2.0.0",
        "status": "running",
        "uptime_seconds": round(uptime, 2),
        "database_initialized": app_state.get("database_initialized", False),
        "recommender_initialized": app_state.get("recommender_initialized", False),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "movies": "/movies/",
            "auth": "/auth/",
            "recommendations": "/api/recommender/"
        }
    }

@app.options("/{path:path}")
async def preflight_handler(path: str):
    """Handle CORS preflight requests"""
    return {"message": "OK"}

@app.get("/health")
async def detailed_health_check():
    """Comprehensive health check endpoint"""
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
            
            # Add database stats
            stats = DatabaseUtils.get_table_stats()
            if stats:
                health_data["database"]["stats"] = stats
        else:
            health_data["database"] = {"status": "unhealthy"}
            health_data["status"] = "degraded"
    except Exception as e:
        logger.error(f"Health check database error: {e}")
        health_data["database"] = {"status": "error", "message": str(e)}
        health_data["status"] = "unhealthy"
    
    # Check recommender system
    health_data["recommender"] = {
        "status": "healthy" if app_state.get("recommender_initialized") else "initializing",
        "initialized": app_state.get("recommender_initialized", False)
    }
    
    # Determine overall status
    if health_data["database"].get("status") != "healthy":
        health_data["status"] = "unhealthy"
    
    # Return appropriate HTTP status
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
    recommender_router,
    prefix="/api/recommender",
    tags=["recommendations"]
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
            access_log=True
        )