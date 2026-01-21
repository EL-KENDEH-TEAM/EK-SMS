"""
School Applications Models

Database models for school registration applications and verification tokens.
These are platform-level tables (no school_id) since they exist before a school tenant is created.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SchoolType(str, enum.Enum):
    """Types of schools."""

    PUBLIC = "public"
    PRIVATE = "private"
    MISSION = "mission"
    UNIVERSITY = "university"
    VOCATIONAL = "vocational"


class StudentPopulation(str, enum.Enum):
    """Student population ranges."""

    UNDER_100 = "under_100"
    FROM_100_TO_300 = "100_to_300"
    FROM_300_TO_500 = "300_to_500"
    OVER_500 = "over_500"


class ApplicationStatus(str, enum.Enum):
    """Status of a school application."""

    AWAITING_APPLICANT_VERIFICATION = "awaiting_applicant_verification"
    AWAITING_PRINCIPAL_CONFIRMATION = "awaiting_principal_confirmation"
    PENDING_REVIEW = "pending_review"
    UNDER_REVIEW = "under_review"
    MORE_INFO_REQUESTED = "more_info_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AdminChoice(str, enum.Enum):
    """Who will be the school admin."""

    APPLICANT = "applicant"
    PRINCIPAL = "principal"


class TokenType(str, enum.Enum):
    """Types of verification tokens."""

    APPLICANT_VERIFICATION = "applicant_verification"
    PRINCIPAL_CONFIRMATION = "principal_confirmation"


class SchoolApplication(Base):
    """
    School registration application.

    Stores all information submitted during the school registration process.
    Platform-level table - no school_id since school doesn't exist yet.
    """

    __tablename__ = "school_applications"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # School information
    school_name: Mapped[str] = mapped_column(String(200), nullable=False)
    year_established: Mapped[int] = mapped_column(Integer, nullable=False)
    school_type: Mapped[SchoolType] = mapped_column(
        Enum(SchoolType, name="school_type"), nullable=False
    )
    student_population: Mapped[StudentPopulation] = mapped_column(
        Enum(StudentPopulation, name="student_population"), nullable=False
    )

    # Location
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)

    # School contact (at least one required - validated in schema)
    school_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    school_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Principal information
    principal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    principal_email: Mapped[str] = mapped_column(String(255), nullable=False)
    principal_phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # Applicant information
    applicant_is_principal: Mapped[bool] = mapped_column(Boolean, nullable=False)
    applicant_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    applicant_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    applicant_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    applicant_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    admin_choice: Mapped[AdminChoice | None] = mapped_column(
        Enum(AdminChoice, name="admin_choice"), nullable=True
    )

    # Additional details
    online_presence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reasons: Mapped[list] = mapped_column(JSON, nullable=False)
    other_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        nullable=False,
        default=ApplicationStatus.AWAITING_APPLICANT_VERIFICATION,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    applicant_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    principal_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Note: FK constraint to users table removed until users module is implemented
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reminder tracking
    reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Internal admin notes (admin-only, never shown to applicants)
    # Stored as JSON array: [{note: str, created_by: UUID, created_at: datetime}, ...]
    internal_notes: Mapped[list | None] = mapped_column(
        JSON, nullable=True, comment="Admin-only internal notes stored as JSON array"
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    verification_tokens: Mapped[list["VerificationToken"]] = relationship(
        "VerificationToken", back_populates="application", cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_school_applications_status", "status"),
        Index("ix_school_applications_applicant_email", "applicant_email"),
        Index("ix_school_applications_principal_email", "principal_email"),
        Index(
            "ix_school_applications_school_city",
            "school_name",
            "city",
        ),
    )


class VerificationToken(Base):
    """
    Verification tokens for email verification and principal confirmation.

    Tokens expire after 72 hours.
    """

    __tablename__ = "verification_tokens"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to application
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Token details
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    token_type: Mapped[TokenType] = mapped_column(
        Enum(TokenType, name="token_type"), nullable=False
    )

    # Expiration and usage
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    application: Mapped["SchoolApplication"] = relationship(
        "SchoolApplication", back_populates="verification_tokens"
    )

    # Indexes
    __table_args__ = (Index("ix_verification_tokens_token", "token"),)
