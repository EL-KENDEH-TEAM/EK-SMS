"""
EK-SMS API - Main Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
  title="EK-SMS API",
  description="EL-KENDEH Smart School Management System API",
  version="0.1.0",
  docs_url="/docs",
  redoc_url="/redoc",
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["https://localhost:3000"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)

@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
  """Root endpoint - API welcome message."""
  return {"message": "Welcome to EK-SMS API", "status": "running"}

@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
  """Health check endpoint for container orchestration."""
  return {"status": "healthy"}

@app.get("/ready", tags=["Health"])
async def readiness_check() -> dict[str, str]:
    """
    Readiness check endpoint.
    TODO: Add database and Redis connection checks.
    """
    return {"status": "ready"}