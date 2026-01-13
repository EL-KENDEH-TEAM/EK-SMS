"""
School Applications Service Layer

Business logic for school registration applications.
Orchestrates repository operations, token management, and email notifications.

This module implements the submission flow:
1. Validate no duplicate applications exist
2. Create the application record
3. Generate and store verification token
4. Send verification email to applicant
5. Return application details

Security considerations:
- Tokens use cryptographically secure random generation
- Token expiration enforced at 72 hours
- Email validation prevents unauthorized access
- Duplicate detection prevents abuse
"""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import send_applicant_verification
from app.modules.school_applications import repository
from app.modules.school_applications.models import (
    ApplicationStatus,
    SchoolApplication,
    TokenType,
    VerificationToken,
)
from app.modules.school_applications.schemas import (
    SchoolApplicationCreate,
    SchoolApplicationResponse,
)

logger = logging.getLogger(__name__)

# Constants
TOKEN_EXPIRY_HOURS = 72
TOKEN_LENGTH = 32  # 256 bits of entropy when using token_urlsafe


class ApplicationServiceError(Exception):
    """Base exception for application service errors."""

    def __init__(self, message: str, error_code: str, status_code: int = 400):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


class DuplicateApplicationError(ApplicationServiceError):
    """Raised when a duplicate application is detected."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="DUPLICATE_APPLICATION",
            status_code=409,
        )


class ApplicationNotFoundError(ApplicationServiceError):
    """Raised when an application is not found."""

    def __init__(self, application_id: UUID | None = None):
        message = (
            f"Application {application_id} not found" if application_id else "Application not found"
        )
        super().__init__(
            message=message,
            error_code="APPLICATION_NOT_FOUND",
            status_code=404,
        )


def _generate_secure_token() -> str:
    """
    Generate a cryptographically secure token for email verification.

    Uses secrets.token_urlsafe which generates URL-safe base64-encoded tokens
    with sufficient entropy for security-critical operations.

    Returns:
        A secure random token string (43 characters for 32 bytes of entropy)
    """
    return secrets.token_urlsafe(TOKEN_LENGTH)


def _calculate_token_expiry() -> datetime:
    """
    Calculate the expiration datetime for a verification token.

    Returns:
        Datetime 72 hours from now in UTC
    """
    return datetime.now(UTC) + timedelta(hours=TOKEN_EXPIRY_HOURS)


def _get_effective_applicant_email(data: SchoolApplicationCreate) -> str:
    """
    Get the effective applicant email based on is_principal flag.

    If the applicant is the principal, use the principal's email.
    Otherwise, use the applicant's email.

    Args:
        data: The application create request data

    Returns:
        The email address to use for the applicant
    """
    if data.applicant.is_principal:
        return data.contact.principal_email
    return data.applicant.email  # type: ignore - validated in schema


def _get_effective_applicant_name(data: SchoolApplicationCreate) -> str:
    """
    Get the effective applicant name based on is_principal flag.

    If the applicant is the principal, use the principal's name.
    Otherwise, use the applicant's name.

    Args:
        data: The application create request data

    Returns:
        The name to use for the applicant
    """
    if data.applicant.is_principal:
        return data.contact.principal_name
    return data.applicant.name  # type: ignore - validated in schema


async def _check_duplicate_by_applicant_email(
    db: AsyncSession,
    applicant_email: str,
    school_name: str,
) -> None:
    """
    Check if a pending application exists for the same applicant email and school.

    Args:
        db: Database session
        applicant_email: Email of the applicant
        school_name: Name of the school

    Raises:
        DuplicateApplicationError: If a pending application already exists
    """
    existing_applications = await repository.get_by_applicant_email(db, applicant_email)

    # Check for pending applications with the same school name
    pending_statuses = {
        ApplicationStatus.AWAITING_APPLICANT_VERIFICATION,
        ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION,
        ApplicationStatus.PENDING_REVIEW,
        ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.MORE_INFO_REQUESTED,
    }

    for app in existing_applications:
        if app.school_name == school_name and app.status in pending_statuses:
            logger.warning(
                f"Duplicate application attempt: email={applicant_email}, school={school_name}"
            )
            raise DuplicateApplicationError(
                f"You already have a pending application for {school_name}. "
                "Please check your email for the verification link or contact support."
            )


async def _check_duplicate_by_school_and_city(
    db: AsyncSession,
    school_name: str,
    city: str,
) -> None:
    """
    Check if a pending application exists for the same school name and city.

    Args:
        db: Database session
        school_name: Name of the school
        city: City where the school is located

    Raises:
        DuplicateApplicationError: If a pending application already exists
    """
    existing = await repository.get_pending_by_school_and_city(db, school_name, city)

    if existing:
        logger.warning(f"Duplicate school application attempt: school={school_name}, city={city}")
        raise DuplicateApplicationError(
            f"A school named '{school_name}' in {city} already has a pending application. "
            "If this is not a duplicate, please contact support."
        )


async def submit_application(
    db: AsyncSession,
    data: SchoolApplicationCreate,
) -> SchoolApplicationResponse:
    """
    Submit a new school registration application.

    This is the main entry point for school registration. It:
    1. Validates that no duplicate application exists
    2. Creates the application record with AWAITING_APPLICANT_VERIFICATION status
    3. Generates a secure verification token
    4. Sends verification email to the applicant

    Args:
        db: Database session
        data: Application data from the request

    Returns:
        SchoolApplicationResponse with application ID and status

    Raises:
        DuplicateApplicationError: If a duplicate application is detected
        HTTPException: If email sending fails (with warning, not blocking)
    """
    # Get effective applicant details
    applicant_email = _get_effective_applicant_email(data)
    applicant_name = _get_effective_applicant_name(data)
    school_name = data.school.name

    logger.info(f"Processing application submission for school: {school_name}")

    # Validate: Check for duplicate by applicant email + school name
    await _check_duplicate_by_applicant_email(db, applicant_email, school_name)

    # Validate: Check for duplicate by school name + city
    await _check_duplicate_by_school_and_city(db, school_name, data.location.city)

    # Create the application record
    application = await repository.create(db, data)
    logger.info(f"Created application {application.id} for school: {school_name}")

    # Generate verification token
    token = _generate_secure_token()
    token_expiry = _calculate_token_expiry()

    # Store the verification token
    await repository.create_token(
        db=db,
        application_id=application.id,
        token=token,
        token_type=TokenType.APPLICANT_VERIFICATION,
        expires_at=token_expiry,
    )
    logger.info(f"Created verification token for application {application.id}")

    # Send verification email (non-blocking - log error but don't fail the request)
    try:
        email_sent = await send_applicant_verification(
            to_email=applicant_email,
            applicant_name=applicant_name,
            school_name=school_name,
            token=token,
        )

        if not email_sent:
            logger.error(f"Failed to send verification email for application {application.id}")
    except Exception as e:
        logger.error(f"Exception sending verification email for application {application.id}: {e}")

    # Return response matching API contract
    return SchoolApplicationResponse(
        id=application.id,
        status=application.status,
        applicant_email=applicant_email,
        message="Application submitted. Please check your email to verify.",
        verification_expires_at=token_expiry,
    )


async def get_application_by_id(
    db: AsyncSession,
    application_id: UUID,
) -> SchoolApplication:
    """
    Get an application by ID.

    Args:
        db: Database session
        application_id: UUID of the application

    Returns:
        The SchoolApplication record

    Raises:
        ApplicationNotFoundError: If the application doesn't exist
    """
    application = await repository.get_by_id(db, application_id)

    if not application:
        raise ApplicationNotFoundError(application_id)

    return application


async def get_verification_token(
    db: AsyncSession,
    token: str,
) -> VerificationToken | None:
    """
    Get a verification token by its token string.

    Args:
        db: Database session
        token: The token string

    Returns:
        The VerificationToken if found, None otherwise
    """
    return await repository.get_by_token(db, token)


def is_token_valid(token: VerificationToken) -> bool:
    """
    Check if a verification token is valid (not expired and not used).

    Args:
        token: The verification token to check

    Returns:
        True if the token is valid, False otherwise
    """
    if token.used_at is not None:
        return False

    return datetime.now(UTC) <= token.expires_at
