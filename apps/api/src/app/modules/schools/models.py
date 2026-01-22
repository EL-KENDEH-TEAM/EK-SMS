"""
School Models

Database models for school (tenant) management.
Each school is a tenant in the multi-tenant architecture.
"""

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.shared import BaseModel

if TYPE_CHECKING:
    from app.modules.users.models import User


class SchoolStatus(str, Enum):
    """Status of a school tenant."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class School(BaseModel):
    """
    School tenant model.

    Each school is a tenant in the multi-tenant system. All school-scoped
    data (users, students, grades, etc.) will reference this model via school_id.

    Created when a school application is approved.
    """

    __tablename__ = "schools"

    # Basic information (from application)
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )
    year_established: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    school_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    student_population: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Location
    country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        index=True,
    )
    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Contact information
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Principal information
    principal_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    principal_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    principal_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Online presence (JSON array of {type, url} objects)
    online_presence: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Status
    status: Mapped[SchoolStatus] = mapped_column(
        ENUM(SchoolStatus, name="school_status", create_type=True),
        nullable=False,
        default=SchoolStatus.ACTIVE,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Reference to original application
    # ON DELETE SET NULL: If application is deleted, school remains but loses the reference
    application_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("school_applications.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="school",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<School(id={self.id}, name={self.name}, status={self.status.value})>"
