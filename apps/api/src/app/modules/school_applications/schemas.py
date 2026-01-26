"""
School Applications Schemas

Pydantic schemas for request validation and response serialization.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

# Re-use enums from models (they work with Pydantic too!)
from app.modules.school_applications.models import (
    AdminChoice,
    ApplicationStatus,
    SchoolType,
    StudentPopulation,
)


class OnlinePresenceItem(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    url: str = Field(..., min_length=1, max_length=500)


class SchoolInfo(BaseModel):
    """School information section."""

    name: str = Field(..., min_length=1, max_length=200)
    year_established: int = Field(..., ge=1000)
    school_type: SchoolType
    student_population: StudentPopulation


class LocationInfo(BaseModel):
    """Location information section."""

    country_code: str = Field(..., min_length=2, max_length=2)
    city: str = Field(..., min_length=1, max_length=100)
    address: str = Field(..., min_length=1, max_length=500)


class ContactInfo(BaseModel):
    """Contact information section."""

    school_phone: str | None = Field(None, max_length=20)
    school_email: EmailStr | None = None

    # Principal information
    principal_name: str = Field(..., min_length=1, max_length=200)
    principal_email: EmailStr
    principal_phone: str = Field(..., min_length=1, max_length=20)


class ApplicantInfo(BaseModel):
    """Applicant information section."""

    is_principal: bool
    name: str | None = Field(None, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20)
    role: str | None = Field(None, max_length=100)
    admin_choice: AdminChoice | None = None


class DetailsInfo(BaseModel):
    """Additional details section."""

    online_presence: list[OnlinePresenceItem] | None = None
    reasons: list[str] = Field(..., min_length=1)
    other_reason: str | None = Field(None, max_length=500)


class SchoolApplicationCreate(BaseModel):
    """Request body for POST /school-applications."""

    school: SchoolInfo
    location: LocationInfo
    contact: ContactInfo
    applicant: ApplicantInfo
    details: DetailsInfo

    @model_validator(mode="after")
    def validate_application(self) -> "SchoolApplicationCreate":
        """Validate conditional fields."""

        # Year established can't be in the future
        current_year = datetime.now().year
        if self.school.year_established > current_year:
            raise ValueError(f"year_established cannot be in the future (max: {current_year})")

        # At least one school contact required
        if not self.contact.school_phone and not self.contact.school_email:
            raise ValueError("At least one of school_phone or school_email is required")

        # If applicant is NOT the principal, applicant fields are required
        if not self.applicant.is_principal:
            if not self.applicant.name:
                raise ValueError("applicant.name is required when applicant is not the principal")
            if not self.applicant.email:
                raise ValueError("applicant.email is required when applicant is not the principal")
            if not self.applicant.phone:
                raise ValueError("applicant.phone is required when applicant is not the principal")
            if not self.applicant.role:
                raise ValueError("applicant.role is required when applicant is not the principal")
            if not self.applicant.admin_choice:
                raise ValueError(
                    "applicant.admin_choice is required when applicant is not the principal"
                )

        return self


class SchoolApplicationResponse(BaseModel):
    """Response after submitting a school application.

    Matches the API contract for POST /school-applications response.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ApplicationStatus
    applicant_email: str
    message: str = "Application submitted. Please check your email to verify."
    verification_expires_at: datetime


class VerifyApplicationRequest(BaseModel):
    """Request to verify applicant email."""

    token: str = Field(..., min_length=1)


class VerifyApplicationResponse(BaseModel):
    """Response after applicant verification."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ApplicationStatus
    message: str
    requires_principal_confirmation: bool
    principal_email_hint: str | None = None  # Only present if requires_principal_confirmation=True


class ConfirmPrincipalRequest(BaseModel):
    """Request to confirm principal."""

    token: str = Field(..., min_length=1)


class ConfirmPrincipalResponse(BaseModel):
    """Response after principal confirmation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ApplicationStatus
    message: str
    school_name: str


class ResendVerificationRequest(BaseModel):
    """Request to resend verification email."""

    application_id: UUID
    email: EmailStr


class ResendVerificationResponse(BaseModel):
    """Response after resending verification."""

    message: str = "Verification email sent successfully."
    expires_at: datetime


class PrincipalViewResponse(BaseModel):
    """Response for GET /school-applications/principal-view.

    Returns application summary for principal to review before confirming.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_name: str
    applicant_name: str
    admin_choice: AdminChoice


class StatusStep(BaseModel):
    """A single step in the application progress."""

    name: str
    completed: bool
    completed_at: datetime | None = None


class ApplicationStatusResponse(BaseModel):
    """Response for GET /school-applications/{id}/status."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_name: str
    status: ApplicationStatus
    status_label: str
    status_description: str
    submitted_at: datetime
    applicant_verified_at: datetime | None = None
    principal_confirmed_at: datetime | None = None
    steps: list[StatusStep]


class Country(BaseModel):
    """A supported country."""

    code: str
    name: str


class CountryListResponse(BaseModel):
    """List of supported countries."""

    countries: list[Country]


# ============================================
# Admin Dashboard Schemas
# ============================================


class InternalNote(BaseModel):
    """Internal admin note structure.

    Internal notes are only visible to platform administrators
    and are never shown to applicants.
    """

    model_config = ConfigDict(from_attributes=True)

    note: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Note content",
        json_schema_extra={"example": "Application looks complete. All docs verified."},
    )
    created_by: UUID = Field(
        ...,
        description="UUID of the admin who created the note",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the note was created",
    )


class ApplicationListItem(BaseModel):
    """Application summary for list view.

    Contains essential fields for the admin applications list table.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Application UUID")
    school_name: str = Field(..., description="Official school name")
    school_type: SchoolType = Field(..., description="Type of school")
    student_population: StudentPopulation = Field(..., description="Student population range")
    country_code: str = Field(..., description="2-letter country code (ISO 3166-1 alpha-2)")
    city: str = Field(..., description="City where school is located")
    status: ApplicationStatus = Field(..., description="Current application status")
    submitted_at: datetime = Field(..., description="When application was submitted")
    applicant_verified_at: datetime | None = Field(
        None, description="When applicant verified email"
    )
    principal_confirmed_at: datetime | None = Field(
        None, description="When principal confirmed application"
    )
    reviewed_at: datetime | None = Field(None, description="When review started or decision made")
    reviewed_by: UUID | None = Field(None, description="Admin who reviewed/is reviewing")


class ApplicationListResponse(BaseModel):
    """Paginated list of applications for admin dashboard.

    Returns applications with pagination metadata.
    """

    applications: list[ApplicationListItem] = Field(
        ..., description="List of application summaries"
    )
    total: int = Field(..., ge=0, description="Total number of applications matching filters")
    skip: int = Field(..., ge=0, description="Number of records skipped")
    limit: int = Field(..., ge=1, le=100, description="Maximum records per page")


class DashboardStats(BaseModel):
    """Dashboard statistics for admin overview.

    Aggregated statistics shown on the admin dashboard.
    """

    pending_review: int = Field(
        ...,
        ge=0,
        description="Count of applications awaiting admin action",
    )
    under_review: int = Field(
        ...,
        ge=0,
        description="Count of applications currently being reviewed",
    )
    more_info_requested: int = Field(
        ...,
        ge=0,
        description="Count of applications waiting for applicant response",
    )
    approved_this_week: int = Field(
        ...,
        ge=0,
        description="Count of applications approved in the last 7 days",
    )
    total_this_month: int = Field(
        ...,
        ge=0,
        description="Total applications received in the current month",
    )
    avg_review_time_days: float | None = Field(
        None,
        ge=0,
        description="Average days from submission to decision (past 30 days)",
    )


class ApplicationDetailResponse(BaseModel):
    """Complete application details for admin review.

    Contains all application fields including internal notes.
    """

    model_config = ConfigDict(from_attributes=True)

    # Application ID
    id: UUID = Field(..., description="Application UUID")

    # School information
    school_name: str = Field(..., description="Official school name")
    year_established: int = Field(..., description="Year school was established")
    school_type: SchoolType = Field(..., description="Type of school")
    student_population: StudentPopulation = Field(..., description="Student population range")

    # Location
    country_code: str = Field(..., description="2-letter country code")
    city: str = Field(..., description="City where school is located")
    address: str = Field(..., description="Full street address")

    # School contact
    school_phone: str | None = Field(None, description="School phone number")
    school_email: str | None = Field(None, description="School email address")

    # Principal information
    principal_name: str = Field(..., description="Principal's full name")
    principal_email: str = Field(..., description="Principal's email address")
    principal_phone: str = Field(..., description="Principal's phone number")

    # Applicant information
    applicant_is_principal: bool = Field(..., description="Whether applicant is the principal")
    applicant_name: str | None = Field(None, description="Applicant's name (if not principal)")
    applicant_email: str | None = Field(None, description="Applicant's email (if not principal)")
    applicant_phone: str | None = Field(None, description="Applicant's phone (if not principal)")
    applicant_role: str | None = Field(None, description="Applicant's role (if not principal)")
    admin_choice: AdminChoice | None = Field(
        None, description="Who will be school admin (applicant or principal)"
    )

    # Additional details
    online_presence: list[OnlinePresenceItem] | None = Field(
        None, description="School's online presence (website, social media)"
    )
    reasons: list[str] = Field(..., description="Reasons for registering")
    other_reason: str | None = Field(None, description="Additional reason (free text)")

    # Status and timeline
    status: ApplicationStatus = Field(..., description="Current application status")
    submitted_at: datetime = Field(..., description="When application was submitted")
    applicant_verified_at: datetime | None = Field(
        None, description="When applicant verified email"
    )
    principal_confirmed_at: datetime | None = Field(
        None, description="When principal confirmed application"
    )
    reviewed_at: datetime | None = Field(None, description="When review started or decision made")
    reviewed_by: UUID | None = Field(None, description="Admin who reviewed/is reviewing")
    decision_reason: str | None = Field(
        None, description="Reason for rejection or more info request"
    )

    # Admin-only fields
    internal_notes: list[InternalNote] | None = Field(
        None, description="Internal admin notes (admin-only)"
    )


# ============================================
# Admin Action Request Schemas
# ============================================


class RequestInfoRequest(BaseModel):
    """Request body for requesting more information from applicant."""

    message: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Message explaining what information is needed",
        json_schema_extra={
            "example": "Please provide a copy of your school's official registration certificate and recent enrollment records."
        },
    )


class RejectRequest(BaseModel):
    """Request body for rejecting an application."""

    reason: str = Field(
        ...,
        min_length=20,
        max_length=1000,
        description="Detailed reason for rejection",
        json_schema_extra={
            "example": "Unable to verify the school's registration with the Ministry of Education. Please provide official documentation."
        },
    )


class AddNoteRequest(BaseModel):
    """Request body for adding an internal note."""

    note: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Note content",
        json_schema_extra={
            "example": "Called the principal to verify. School is legitimate and registered with MoE."
        },
    )


# ============================================
# Admin Action Response Schemas
# ============================================


class StartReviewResponse(BaseModel):
    """Response after starting review of an application."""

    id: UUID = Field(..., description="Application UUID")
    status: ApplicationStatus = Field(..., description="Updated status (under_review)")
    reviewed_by: UUID = Field(..., description="Admin who started the review")
    reviewed_at: datetime = Field(..., description="When review started")
    message: str = Field(
        default="Application is now under review",
        description="Success message",
    )


class RequestInfoResponse(BaseModel):
    """Response after requesting more information."""

    id: UUID = Field(..., description="Application UUID")
    status: ApplicationStatus = Field(..., description="Updated status (more_info_requested)")
    message: str = Field(
        default="Information request sent to applicant",
        description="Success message",
    )


class ApproveResponse(BaseModel):
    """Response after approving an application.

    Contains IDs of newly created school and admin user.
    """

    id: UUID = Field(..., description="Application UUID")
    status: ApplicationStatus = Field(..., description="Updated status (approved)")
    school_id: UUID = Field(..., description="Newly created school UUID")
    admin_user_id: UUID = Field(..., description="Newly created admin user UUID")
    message: str = Field(
        default="Application approved. School and admin account created successfully.",
        description="Success message",
    )


class RejectResponse(BaseModel):
    """Response after rejecting an application."""

    id: UUID = Field(..., description="Application UUID")
    status: ApplicationStatus = Field(..., description="Updated status (rejected)")
    message: str = Field(
        default="Application rejected. Notification sent to applicant.",
        description="Success message",
    )


class AddNoteResponse(BaseModel):
    """Response after adding an internal note."""

    id: UUID = Field(..., description="Application UUID")
    note: InternalNote = Field(..., description="The newly added note")
    message: str = Field(
        default="Note added successfully",
        description="Success message",
    )
