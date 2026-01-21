"""
Schools module - School tenant management.
"""

from app.modules.schools.models import School, SchoolStatus
from app.modules.schools.repository import SchoolRepository

__all__ = ["School", "SchoolStatus", "SchoolRepository"]
