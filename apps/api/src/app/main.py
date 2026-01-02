"""
EK-SMS API - Main Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import async_session_maker, init_db, close_db
from app.core.redis import init_redis, close_redis, redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    print(f"Starting EK-SMS API in {settings.python_env} mode...")

    # Initialize Redis
    try:
        await init_redis()
        print("✓ Redis connected")
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        if settings.is_production:
            raise

    # Initialize Database
    try:
        await init_db()
        print("✓ Database connected")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        if settings.is_production:
            raise

    yield  # Application runs here

    # Shutdown
    print("Shutting down EK-SMS API...")
    await close_redis()
    await close_db()
    print("✓ Cleanup complete")


app = FastAPI(
    title="EK-SMS API",
    description="EL-KENDEH Smart School Management System API",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint - API welcome message."""
    return {
        "message": "Welcome to EK-SMS API",
        "status": "running",
        "environment": settings.python_env,
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for container orchestration."""
    return {"status": "healthy"}


@app.get("/ready", tags=["Health"])
async def readiness_check() -> dict[str, str]:
    """Readiness check endpoint."""
    return {"status": "ready"}


@app.get("/debug/db", tags=["Debug"])
async def debug_db():
    """Test database connection."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            return {"database": "connected", "result": result.scalar()}
    except Exception as e:
        return {"database": "error", "message": str(e)}


@app.get("/debug/redis", tags=["Debug"])
async def debug_redis():
    """Test Redis connection."""
    from app.core.redis import redis_client

    try:
        if redis_client:
            await redis_client.ping()
            return {"redis": "connected"}
        return {"redis": "not initialized"}
    except Exception as e:
        return {"redis": "error", "message": str(e)}
