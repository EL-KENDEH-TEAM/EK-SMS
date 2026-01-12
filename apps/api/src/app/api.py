from fastapi import APIRouter

from app.modules.school_applications import router as school_applications_router

api_router = APIRouter()

api_router.include_router(
    school_applications_router, prefix="/school_applications", tags=["School Applications"]
)
