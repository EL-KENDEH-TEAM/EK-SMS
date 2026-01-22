"""
EK-SMS API - Main Application Entry Point

This module initializes and configures the FastAPI application including:
- Database and Redis connections
- Background job scheduler
- CORS middleware
- API routing
- Health check endpoints
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import api_router
from app.core.config import settings
from app.core.database import async_session_maker, close_db, init_db
from app.core.redis import close_redis, init_redis, redis_client
from app.core.scheduler import start_scheduler, stop_scheduler
from app.modules.school_applications.jobs import register_school_application_jobs


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events including:
    - Redis connection
    - Database connection
    - Background job scheduler
    """
    # Startup
    print(f"Starting EK-SMS API in {settings.python_env} mode...")

    # Initialize Redis
    try:
        await init_redis()
        print("[OK] Redis connected")
    except Exception as e:
        print(f"[FAIL] Redis connection failed: {e}")
        if settings.is_production:
            raise

    # Initialize Database
    try:
        await init_db()
        print("[OK] Database connected")
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        if settings.is_production:
            raise

    # Initialize Background Job Scheduler
    try:
        # Register jobs before starting the scheduler
        register_school_application_jobs()

        # Start the scheduler
        await start_scheduler()
        print("[OK] Background scheduler started")
    except Exception as e:
        print(f"[FAIL] Background scheduler failed to start: {e}")
        if settings.is_production:
            raise

    yield  # Application runs here

    # Shutdown
    print("Shutting down EK-SMS API...")

    # Stop the scheduler first (wait for running jobs)
    await stop_scheduler()
    print("[OK] Background scheduler stopped")

    await close_redis()
    await close_db()
    print("[OK] Cleanup complete")


app = FastAPI(
    title="EK-SMS API",
    description="EL-KENDEH Smart School Management System API",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api/v1")

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

    try:
        if redis_client:
            await redis_client.ping()
            return {"redis": "connected"}
        return {"redis": "not initialized"}
    except Exception as e:
        return {"redis": "error", "message": str(e)}


# ============================================
# Background Job Debug Endpoints
# ============================================
# These endpoints allow manual triggering of background jobs for testing
# and debugging purposes. In production, jobs run automatically on schedule.


@app.get("/debug/jobs", tags=["Debug"])
async def list_jobs():
    """
    List all registered background jobs and their status.

    Returns:
        List of job information including next run time and pause status.
    """
    from app.core.scheduler import list_registered_jobs

    return {"jobs": list_registered_jobs()}


@app.post("/debug/jobs/{job_id}/trigger", tags=["Debug"])
async def trigger_job(job_id: str):
    """
    Manually trigger a background job for testing.

    This runs the job immediately, bypassing the normal schedule.
    Useful for testing job behavior without waiting for the scheduled time.

    Args:
        job_id: The ID of the job to trigger. Available jobs:
            - school_applications_send_reminders
            - school_applications_expire_applications

    Returns:
        Job execution result including status and any errors.

    Raises:
        HTTPException 400: If job_id is not found.
    """
    from fastapi import HTTPException

    from app.core.scheduler import trigger_job_manually

    try:
        result = await trigger_job_manually(job_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/debug/jobs/{job_id}/pause", tags=["Debug"])
async def pause_job_endpoint(job_id: str):
    """
    Pause a scheduled background job.

    The job will stop running on schedule but remains registered.
    Use /debug/jobs/{job_id}/resume to restart it.

    Args:
        job_id: The ID of the job to pause.

    Returns:
        Success status.
    """
    from app.core.scheduler import pause_job

    success = pause_job(job_id)
    return {"job_id": job_id, "paused": success}


@app.post("/debug/jobs/{job_id}/resume", tags=["Debug"])
async def resume_job_endpoint(job_id: str):
    """
    Resume a paused background job.

    Args:
        job_id: The ID of the job to resume.

    Returns:
        Success status.
    """
    from app.core.scheduler import resume_job

    success = resume_job(job_id)
    return {"job_id": job_id, "resumed": success}
