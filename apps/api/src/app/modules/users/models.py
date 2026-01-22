"""
User Models

Database models for user management and authentication.
"""

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.shared import BaseModel

if TYPE_CHECKING:
    from app.modules.schools.models import School


class UserRole(str, Enum):
    """User roles in the system."""

    SUPER_ADMIN = "super_admin"
    SCHOOL_ADMIN = "school_admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"
    EXAM_OFFICER = "exam_officer"
    FINANCE_OFFICER = "finance_officer"


class User(BaseModel):
    """
    User model for authentication and authorization.

    This is the core identity model. Role-specific data
    (Teacher, Student, Parent) will be in separate linked models.

    Multi-tenant: school_id is required for all roles except SUPER_ADMIN.
    SUPER_ADMIN users are platform-level and have no school_id.
    """

    __tablename__ = "users"

    # Multi-tenant: Link to school (NULL for platform admins)
    # ON DELETE SET NULL: If school is deleted, users remain but lose school association
    school_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("schools.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=True,
    )
    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Profile fields
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Role and permissions
    role: Mapped[UserRole] = mapped_column(
        ENUM(UserRole, name="user_role", create_type=True),
        nullable=False,
        default=UserRole.STUDENT,
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Password management
    must_change_password: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Two-factor authentication
    is_two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    two_factor_secret: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    # Relationships
    school: Mapped["School | None"] = relationship(
        "School",
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"

    @property
    def full_name(self) -> str:
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}"
