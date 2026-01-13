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

from app.core.email import (
    send_applicant_verification,
    send_application_under_review,
    send_principal_confirmation,
)
from app.modules.school_applications import repository
from app.modules.school_applications.models import (
    ApplicationStatus,
    SchoolApplication,
    TokenType,
    VerificationToken,
)
from app.modules.school_applications.schemas import (
    ConfirmPrincipalResponse,
    SchoolApplicationCreate,
    SchoolApplicationResponse,
    VerifyApplicationResponse,
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


class InvalidTokenError(ApplicationServiceError):
    """Raised when a verification token is invalid or not found."""

    def __init__(self, message: str = "Invalid or missing verification token."):
        super().__init__(
            message=message,
            error_code="INVALID_TOKEN",
            status_code=400,
        )


class TokenExpiredError(ApplicationServiceError):
    """Raised when a verification token has expired."""

    def __init__(self):
        super().__init__(
            message="This verification link has expired. Please request a new one.",
            error_code="TOKEN_EXPIRED",
            status_code=400,
        )


class TokenAlreadyUsedError(ApplicationServiceError):
    """Raised when a verification token has already been used."""

    def __init__(self):
        super().__init__(
            message="This verification link has already been used.",
            error_code="TOKEN_ALREADY_USED",
            status_code=409,
        )


class InvalidApplicationStateError(ApplicationServiceError):
    """Raised when an application is not in the expected state for an operation."""

    def __init__(self, message: str, expected_state: str | None = None):
        detail = message
        if expected_state:
            detail = f"{message} Expected state: {expected_state}"
        super().__init__(
            message=detail,
            error_code="INVALID_APPLICATION_STATE",
            status_code=409,
        )


class InvalidEmailError(ApplicationServiceError):
    """Raised when the provided email doesn't match the application."""

    def __init__(self):
        super().__init__(
            message="Email does not match the application",
            error_code="INVALID_EMAIL",
            status_code=403,
        )


class AlreadyVerifiedError(ApplicationServiceError):
    """Raised when attempting to resend verification for an already verified application."""

    def __init__(self):
        super().__init__(
            message="This application has already been verified",
            error_code="ALREADY_VERIFIED",
            status_code=409,
        )


class RateLimitExceededError(ApplicationServiceError):
    """Raised when rate limit for resend verification is exceeded."""

    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        minutes = max(1, retry_after_seconds // 60)
        super().__init__(
            message=f"Too many resend requests. Please try again in {minutes} minute(s).",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )


# Rate limiting constants
RESEND_RATE_LIMIT_MAX_REQUESTS = 3
RESEND_RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour


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


def _mask_email(email: str) -> str:
    """
    Mask an email address for privacy display.

    Example: john.doe@example.com -> j***@example.com

    Args:
        email: The email address to mask

    Returns:
        Masked email string
    """
    if "@" not in email:
        return "***"

    local, domain = email.split("@", 1)
    masked_local = "*" if len(local) <= 1 else f"{local[0]}***"
    return f"{masked_local}@{domain}"


def _get_designated_admin_name(application: SchoolApplication) -> str:
    """
    Get the name of the designated admin based on admin_choice.

    Args:
        application: The school application

    Returns:
        Name of the person who will be the school admin
    """
    from app.modules.school_applications.models import AdminChoice

    if application.applicant_is_principal:
        return application.principal_name

    if application.admin_choice == AdminChoice.PRINCIPAL:
        return application.principal_name

    # AdminChoice.APPLICANT or default
    return application.applicant_name or application.principal_name


async def _validate_token(
    db: AsyncSession,
    token_string: str,
    expected_type: TokenType,
) -> tuple[VerificationToken, SchoolApplication]:
    """
    Validate a verification token and return it with its associated application.

    Args:
        db: Database session
        token_string: The token string to validate
        expected_type: The expected token type

    Returns:
        Tuple of (VerificationToken, SchoolApplication)

    Raises:
        InvalidTokenError: If token not found or wrong type
        TokenExpiredError: If token has expired
        TokenAlreadyUsedError: If token was already used
        ApplicationNotFoundError: If associated application not found
    """
    # Get the token
    verification_token = await repository.get_by_token(db, token_string)

    if not verification_token:
        logger.warning(f"Token not found: {token_string[:10]}...")
        raise InvalidTokenError()

    # Verify token type
    if verification_token.token_type != expected_type:
        logger.warning(
            f"Token type mismatch: expected {expected_type}, got {verification_token.token_type}"
        )
        raise InvalidTokenError("Invalid token type for this operation.")

    # Check if already used
    if verification_token.used_at is not None:
        logger.warning(f"Token already used: {token_string[:10]}...")
        raise TokenAlreadyUsedError()

    # Check if expired
    if datetime.now(UTC) > verification_token.expires_at:
        logger.warning(f"Token expired: {token_string[:10]}...")
        raise TokenExpiredError()

    # Get the associated application
    application = await repository.get_by_id(db, verification_token.application_id)

    if not application:
        logger.error(f"Application not found for token: {verification_token.application_id}")
        raise ApplicationNotFoundError(verification_token.application_id)

    return verification_token, application


async def verify_applicant(
    db: AsyncSession,
    token_string: str,
    country_name_lookup: dict[str, str] | None = None,
) -> VerifyApplicationResponse:
    """
    Verify the applicant's email address.

    This function handles two scenarios:
    1. If applicant IS the principal: Move directly to pending_review
    2. If applicant is NOT the principal: Send confirmation to principal

    Args:
        db: Database session
        token_string: The verification token from the email
        country_name_lookup: Optional dict mapping country codes to names

    Returns:
        VerifyApplicationResponse with next steps

    Raises:
        InvalidTokenError: If token is invalid
        TokenExpiredError: If token has expired
        TokenAlreadyUsedError: If token was already used
        InvalidApplicationStateError: If application not in correct state
    """
    logger.info("Processing applicant verification")

    # Validate the token (we don't need the token object, just the validation)
    _, application = await _validate_token(db, token_string, TokenType.APPLICANT_VERIFICATION)

    # Verify application is in correct state
    if application.status != ApplicationStatus.AWAITING_APPLICANT_VERIFICATION:
        logger.warning(
            f"Application {application.id} not in AWAITING_APPLICANT_VERIFICATION state: "
            f"{application.status}"
        )
        raise InvalidApplicationStateError(
            "This application has already been verified.",
            expected_state=ApplicationStatus.AWAITING_APPLICANT_VERIFICATION.value,
        )

    # Mark token as used
    await repository.mark_token_used(db, token_string)
    logger.info(f"Marked verification token as used for application {application.id}")

    # Update applicant_verified_at timestamp
    now = datetime.now(UTC)

    if application.applicant_is_principal:
        # Scenario 1: Applicant IS the principal - move directly to pending_review
        await repository.update_status(
            db,
            application.id,
            ApplicationStatus.PENDING_REVIEW,
            applicant_verified_at=now,
            principal_confirmed_at=now,  # Auto-confirm since same person
        )
        logger.info(
            f"Application {application.id} moved to PENDING_REVIEW (applicant is principal)"
        )

        # Send "under review" email
        try:
            await send_application_under_review(
                to_email=application.principal_email,
                applicant_name=application.principal_name,
                school_name=application.school_name,
                application_id=str(application.id),
            )
        except Exception as e:
            logger.error(f"Failed to send under review email: {e}")

        return VerifyApplicationResponse(
            id=application.id,
            status=ApplicationStatus.PENDING_REVIEW,
            message="Email verified. Your application is now under review.",
            requires_principal_confirmation=False,
        )

    else:
        # Scenario 2: Applicant is NOT the principal - need principal confirmation
        await repository.update_status(
            db,
            application.id,
            ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION,
            applicant_verified_at=now,
        )
        logger.info(f"Application {application.id} moved to AWAITING_PRINCIPAL_CONFIRMATION")

        # Generate new token for principal confirmation
        principal_token = _generate_secure_token()
        principal_token_expiry = _calculate_token_expiry()

        await repository.create_token(
            db=db,
            application_id=application.id,
            token=principal_token,
            token_type=TokenType.PRINCIPAL_CONFIRMATION,
            expires_at=principal_token_expiry,
        )
        logger.info(f"Created principal confirmation token for application {application.id}")

        # Get country name for email
        country_name = application.country_code
        if country_name_lookup:
            country_name = country_name_lookup.get(
                application.country_code, application.country_code
            )

        # Send confirmation email to principal
        try:
            await send_principal_confirmation(
                to_email=application.principal_email,
                principal_name=application.principal_name,
                school_name=application.school_name,
                applicant_name=application.applicant_name or "Unknown",
                applicant_role=application.applicant_role or "Staff",
                city=application.city,
                country=country_name,
                designated_admin=_get_designated_admin_name(application),
                token=principal_token,
            )
        except Exception as e:
            logger.error(f"Failed to send principal confirmation email: {e}")

        return VerifyApplicationResponse(
            id=application.id,
            status=ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION,
            message="Email verified. The principal has been notified to confirm.",
            requires_principal_confirmation=True,
            principal_email_hint=_mask_email(application.principal_email),
        )


async def confirm_principal(
    db: AsyncSession,
    token_string: str,
) -> ConfirmPrincipalResponse:
    """
    Confirm the application as the principal.

    This completes the verification process and moves the application to review.

    Args:
        db: Database session
        token_string: The confirmation token from the email

    Returns:
        ConfirmPrincipalResponse with confirmation details

    Raises:
        InvalidTokenError: If token is invalid
        TokenExpiredError: If token has expired
        TokenAlreadyUsedError: If token was already used
        InvalidApplicationStateError: If application not in correct state
    """
    logger.info("Processing principal confirmation")

    # Validate the token (we don't need the token object, just the validation)
    _, application = await _validate_token(db, token_string, TokenType.PRINCIPAL_CONFIRMATION)

    # Verify application is in correct state
    if application.status != ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION:
        logger.warning(
            f"Application {application.id} not in AWAITING_PRINCIPAL_CONFIRMATION state: "
            f"{application.status}"
        )
        raise InvalidApplicationStateError(
            "This application is not awaiting principal confirmation.",
            expected_state=ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION.value,
        )

    # Mark token as used
    await repository.mark_token_used(db, token_string)
    logger.info(f"Marked principal confirmation token as used for application {application.id}")

    # Update status to pending_review
    now = datetime.now(UTC)
    await repository.update_status(
        db,
        application.id,
        ApplicationStatus.PENDING_REVIEW,
        principal_confirmed_at=now,
    )
    logger.info(f"Application {application.id} moved to PENDING_REVIEW")

    # Get the effective applicant email for notification
    applicant_email = application.applicant_email or application.principal_email
    applicant_name = application.applicant_name or application.principal_name

    # Send "under review" email to applicant
    try:
        await send_application_under_review(
            to_email=applicant_email,
            applicant_name=applicant_name,
            school_name=application.school_name,
            application_id=str(application.id),
        )
    except Exception as e:
        logger.error(f"Failed to send under review email: {e}")

    return ConfirmPrincipalResponse(
        id=application.id,
        status=ApplicationStatus.PENDING_REVIEW,
        message="Application confirmed. It is now under review by our team.",
        school_name=application.school_name,
    )
