from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from . import models
from .database import engine
from .database_utils import startup_database, shutdown_database
from .movie_processing import init_recommender_async
from .recommender.engine import router as recommender_router
from .routers.auth import router as auth_router
from .api_routes import router as api_router
from .admin_routes import router as admin_router

# Load environment variables
load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_database()
    await init_recommender_async()
    yield
    # Shutdown
    await shutdown_database()

app = FastAPI(title="Movie Recommender", lifespan=lifespan)

# CORS middleware configuration - MUST be before route includes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Vite dev server
        "http://localhost:8000",    # FastAPI server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "https://cineverse-lo6nex0fh-dio27073s-projects.vercel.app",  # FIXED: Correct domain
        "https://*.vercel.app",     # Allow all Vercel preview deployments
        "*"  # Temporary: allow all origins for debugging
    ],
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

# Add a simple OPTIONS handler to catch all preflight requests
@app.options("/{path:path}")
async def preflight_handler():
    return {"message": "OK"}

# Add a simple root endpoint
@app.get("/")
async def root():
    return {"message": "Movie Recommender API", "status": "running"}

# Include routers
app.include_router(
    recommender_router,
    prefix="/api/recommender",
    tags=["recommender"]
)
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)
app.include_router(
    api_router,
    prefix="",  # Remove /api prefix for movie routes
    tags=["movies"]
)
app.include_router(
    admin_router,
    prefix="/admin",
    tags=["admin"]
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)