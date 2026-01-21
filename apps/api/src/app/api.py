from fastapi import APIRouter

from app.modules.school_applications import router as school_applications_router
from app.modules.school_applications.admin_router import router as admin_applications_router

api_router = APIRouter()

api_router.include_router(
    school_applications_router, prefix="/school-applications", tags=["School Applications"]
)

api_router.include_router(
    admin_applications_router,
    prefix="/admin/applications",
    tags=["Admin - Applications"],
)
