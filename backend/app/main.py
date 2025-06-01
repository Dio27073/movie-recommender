from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from . import models
from .database import engine
from .movie_processing import init_recommender_async
from .recommender.engine import router as recommender_router
from .routers.auth import router as auth_router
from .api_routes import router as api_router
from .admin_routes import router as admin_router

# Load environment variables
load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Global flag to track if heavy initialization is complete
initialization_complete = False

async def background_initialization():
    """Run heavy initialization in background after API is ready"""
    global initialization_complete
    try:
        print("Starting background initialization...")
        await init_recommender_async()
        initialization_complete = True
        print("Background initialization completed!")
    except Exception as e:
        print(f"Background initialization failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - only essential services
    print("Starting essential services...")
    
    # Start heavy initialization in background (non-blocking)
    asyncio.create_task(background_initialization())
    
    yield
    
    # Shutdown
    print("Shutting down...")

app = FastAPI(title="Movie Recommender", lifespan=lifespan)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8000", 
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "https://cineverse1.vercel.app",
        "https://cineverse-lo6nex0fh-dio27073s-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept", "Accept-Language", "Content-Language", "Content-Type",
        "Authorization", "X-Requested-With", "Origin",
        "Access-Control-Request-Method", "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
    max_age=3600
)

@app.options("/{path:path}")
async def preflight_handler():
    return {"message": "OK"}

@app.get("/")
async def root():
    return {"message": "Movie Recommender API", "status": "running"}

# Enhanced health check with initialization status
@app.get("/health")
async def enhanced_health_check():
    global initialization_complete
    return {
        "status": "healthy",
        "database": "connected", 
        "initialization_complete": initialization_complete,
        "timestamp": datetime.utcnow().isoformat()
    }

# Keep-alive endpoint for preventing cold starts
@app.get("/keep-alive")
async def keep_alive():
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

# Include routers
app.include_router(recommender_router, prefix="/api/recommender", tags=["recommender"])
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(api_router, prefix="", tags=["movies"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)