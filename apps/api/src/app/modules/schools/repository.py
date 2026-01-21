"""
School Repository

Database operations for school management.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.schools.models import School, SchoolStatus

logger = logging.getLogger(__name__)


class SchoolRepository:
    """Repository for school database operations."""

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        name: str,
        year_established: int,
        school_type: str,
        student_population: str,
        country_code: str,
        city: str,
        address: str,
        principal_name: str,
        principal_email: str,
        principal_phone: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        online_presence: list | None = None,
        application_id: str | None = None,
    ) -> School:
        """
        Create a new school record.

        Args:
            db: Database session
            name: School name
            year_established: Year the school was established
            school_type: Type of school (public, private, etc.)
            student_population: Student population range
            country_code: 2-letter country code
            city: City name
            address: Full address
            principal_name: Name of the principal
            principal_email: Email of the principal
            principal_phone: Phone of the principal (optional)
            phone: School phone number (optional)
            email: School email address (optional)
            online_presence: List of online presence items (optional)
            application_id: ID of the original application (optional)

        Returns:
            Created School instance
        """
        school = School(
            name=name,
            year_established=year_established,
            school_type=school_type,
            student_population=student_population,
            country_code=country_code,
            city=city,
            address=address,
            principal_name=principal_name,
            principal_email=principal_email,
            principal_phone=principal_phone,
            phone=phone,
            email=email,
            online_presence=online_presence,
            application_id=application_id,
            status=SchoolStatus.ACTIVE,
            is_active=True,
        )

        db.add(school)
        await db.flush()
        await db.refresh(school)

        logger.info(f"Created school: {school.id} - {school.name}")
        return school

    @staticmethod
    async def get_by_id(db: AsyncSession, school_id: str | UUID) -> School | None:
        """
        Get a school by ID.

        Args:
            db: Database session
            school_id: School UUID

        Returns:
            School instance or None if not found
        """
        school_id_str = str(school_id)
        result = await db.execute(select(School).where(School.id == school_id_str))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_application_id(db: AsyncSession, application_id: str | UUID) -> School | None:
        """
        Get a school by its original application ID.

        Args:
            db: Database session
            application_id: Original application UUID

        Returns:
            School instance or None if not found
        """
        app_id_str = str(application_id)
        result = await db.execute(select(School).where(School.application_id == app_id_str))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_status(
        db: AsyncSession,
        school_id: str | UUID,
        status: SchoolStatus,
    ) -> School | None:
        """
        Update a school's status.

        Args:
            db: Database session
            school_id: School UUID
            status: New status

        Returns:
            Updated School instance or None if not found
        """
        school = await SchoolRepository.get_by_id(db, school_id)
        if not school:
            return None

        school.status = status
        school.is_active = status == SchoolStatus.ACTIVE

        await db.flush()
        await db.refresh(school)

        logger.info(f"Updated school {school_id} status to {status.value}")
        return school
