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
    """Response after submitting a school application."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ApplicationStatus
    school_name: str
    submitted_at: datetime
    message: str = "Application Submitted successfully. Please check your email to verify"
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
