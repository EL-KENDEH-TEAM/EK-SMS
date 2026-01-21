"""
School Applications Service Layer

Business logic for school registration applications.
Orchestrates repository operations, token management, and email notifications.

This module implements:
1. Application Submission Flow:
   - Validate no duplicate applications exist
   - Create the application record
   - Generate and store verification token
   - Send verification email to applicant

2. Verification Flow:
   - Verify applicant email tokens
   - Handle principal confirmation when applicant != principal
   - Transition applications through verification states

3. Resend Verification:
   - Rate-limited resend of verification emails (3/hour via Redis)
   - Deletes old tokens and creates new ones
   - Works for both applicant and principal verification

4. Status Checking:
   - Secure status retrieval with email validation
   - Progress step tracking through verification journey

Security considerations:
- Tokens use cryptographically secure random generation (secrets.token_urlsafe)
- Tokens are SHA-256 hashed before storage (database breach doesn't expose tokens)
- Token expiration enforced at 72 hours
- Email validation prevents unauthorized access to status
- Duplicate detection prevents abuse
- Rate limiting via Redis prevents email bombing (fail-closed if Redis unavailable)
- Case-insensitive email comparison for robustness
- No sensitive token data logged (prevents log exposure)
"""

import contextlib
import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import (
    send_applicant_verification,
    send_application_under_review,
    send_principal_confirmation,
)
from app.modules.school_applications import repository
from app.modules.school_applications.helpers import (
    get_effective_applicant_email_from_model,
    get_effective_applicant_email_from_schema,
    get_effective_applicant_name_from_model,
    get_effective_applicant_name_from_schema,
)
from app.modules.school_applications.models import (
    ApplicationStatus,
    SchoolApplication,
    TokenType,
    VerificationToken,
)
from app.modules.school_applications.schemas import (
    ApplicationStatusResponse,
    ConfirmPrincipalResponse,
    ResendVerificationResponse,
    SchoolApplicationCreate,
    SchoolApplicationResponse,
    StatusStep,
    VerifyApplicationResponse,
)

logger = logging.getLogger(__name__)

# Constants
TOKEN_EXPIRY_HOURS = 72
TOKEN_LENGTH = 32  # 256 bits of entropy when using token_urlsafe


def _hash_token(token: str) -> str:
    """
    Hash a token for secure storage using SHA-256.

    Tokens are hashed before storage so that even if the database is
    compromised, the plain tokens cannot be recovered and used.

    Args:
        token: The plain text token to hash

    Returns:
        Hex-encoded SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


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
    applicant_email = get_effective_applicant_email_from_schema(data)
    applicant_name = get_effective_applicant_name_from_schema(data)
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

    # Store the verification token (hashed for security)
    # Plain token is sent via email, hashed version stored in DB
    await repository.create_token(
        db=db,
        application_id=application.id,
        token=_hash_token(token),  # Store hash, not plain token
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
    # Hash the incoming token to match stored hash
    token_hash = _hash_token(token_string)

    # Get the token by its hash
    verification_token = await repository.get_by_token(db, token_hash)

    if not verification_token:
        # Don't log token content - security best practice
        logger.warning("Token validation failed: token not found in database")
        raise InvalidTokenError()

    # Verify token type
    if verification_token.token_type != expected_type:
        logger.warning(
            f"Token type mismatch: expected {expected_type}, got {verification_token.token_type}"
        )
        raise InvalidTokenError("Invalid token type for this operation.")

    # Check if already used
    if verification_token.used_at is not None:
        logger.warning("Token validation failed: token already used")
        raise TokenAlreadyUsedError()

    # Check if expired
    if datetime.now(UTC) > verification_token.expires_at:
        logger.warning("Token validation failed: token expired")
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

    # Mark token as used (use hashed token for lookup)
    await repository.mark_token_used(db, _hash_token(token_string))
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

        # Store hashed token, send plain token via email
        await repository.create_token(
            db=db,
            application_id=application.id,
            token=_hash_token(principal_token),  # Store hash, not plain token
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

    # Mark token as used (use hashed token for lookup)
    await repository.mark_token_used(db, _hash_token(token_string))
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


async def _check_rate_limit(
    redis_client,
    application_id: UUID,
) -> None:
    """
    Check and enforce rate limiting for resend verification requests.

    Uses a sliding window counter pattern in Redis:
    - Key: resend_verification:{application_id}
    - Value: Count of requests in the current window
    - TTL: 1 hour (3600 seconds)

    Args:
        redis_client: Redis client instance
        application_id: UUID of the application

    Raises:
        RateLimitExceededError: If rate limit is exceeded
    """
    rate_limit_key = f"resend_verification:{application_id}"

    # Get current count
    current_count = await redis_client.get(rate_limit_key)

    if current_count is not None and int(current_count) >= RESEND_RATE_LIMIT_MAX_REQUESTS:
        # Get TTL to determine retry-after
        ttl = await redis_client.ttl(rate_limit_key)
        retry_after = max(ttl, 60)  # At least 60 seconds
        logger.warning(
            f"Rate limit exceeded for application {application_id}: "
            f"{current_count} requests in window"
        )
        raise RateLimitExceededError(retry_after_seconds=retry_after)

    # Increment counter with expiry
    pipe = redis_client.pipeline()
    pipe.incr(rate_limit_key)
    pipe.expire(rate_limit_key, RESEND_RATE_LIMIT_WINDOW_SECONDS)
    await pipe.execute()


async def resend_verification(
    db: AsyncSession,
    application_id: UUID,
    email: str,
    redis_client: Redis | None = None,
) -> ResendVerificationResponse:
    """
    Resend the verification email for an application.

    This function:
    1. Validates the application exists and email matches
    2. Validates the application is still awaiting verification
    3. Enforces rate limiting (max 3 requests per hour) - REQUIRES Redis
    4. Deletes old token and creates a new one
    5. Sends new verification email

    Args:
        db: Database session
        application_id: UUID of the application
        email: Email address (must match applicant email)
        redis_client: Redis client for rate limiting (required in production)

    Returns:
        ResendVerificationResponse with new expiration time

    Raises:
        ApplicationNotFoundError: If application doesn't exist
        InvalidEmailError: If email doesn't match
        AlreadyVerifiedError: If application is already verified
        RateLimitExceededError: If too many requests
        ApplicationServiceError: If Redis unavailable (fail-closed security)
    """
    logger.info(f"Processing resend verification for application {application_id}")

    # Get the application
    application = await repository.get_by_id(db, application_id)

    if not application:
        logger.warning(f"Application not found for resend: {application_id}")
        raise ApplicationNotFoundError(application_id)

    # Get effective applicant email
    effective_email = get_effective_applicant_email_from_model(application)

    # Validate email matches (case-insensitive comparison)
    if email.lower() != effective_email.lower():
        logger.warning(
            f"Email mismatch for application {application_id}: "
            f"provided={email}, expected={effective_email}"
        )
        raise InvalidEmailError()

    # Check application status - can only resend for awaiting verification states
    valid_resend_statuses = {
        ApplicationStatus.AWAITING_APPLICANT_VERIFICATION,
        ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION,
    }

    if application.status not in valid_resend_statuses:
        logger.warning(
            f"Cannot resend verification for application {application_id}: "
            f"status={application.status}"
        )
        raise AlreadyVerifiedError()

    # Check rate limit - fail closed if Redis unavailable (security)
    # This prevents email bombing attacks during Redis outages
    if redis_client is None:
        logger.error("Redis unavailable for rate limiting - failing request (security)")
        raise ApplicationServiceError(
            message="Service temporarily unavailable. Please try again later.",
            error_code="SERVICE_UNAVAILABLE",
            status_code=503,
        )
    await _check_rate_limit(redis_client, application_id)

    # Determine token type based on current status
    if application.status == ApplicationStatus.AWAITING_APPLICANT_VERIFICATION:
        token_type = TokenType.APPLICANT_VERIFICATION
        recipient_email = effective_email
        recipient_name = get_effective_applicant_name_from_model(application)
    else:
        # AWAITING_PRINCIPAL_CONFIRMATION - resend to principal
        token_type = TokenType.PRINCIPAL_CONFIRMATION
        recipient_email = application.principal_email
        recipient_name = application.principal_name

    # Delete existing tokens of this type for the application
    await repository.delete_tokens_for_application(db, application_id, token_type)
    logger.info(f"Deleted existing {token_type} tokens for application {application_id}")

    # Generate new token
    new_token = _generate_secure_token()
    new_token_expiry = _calculate_token_expiry()

    # Store hashed token, send plain token via email
    await repository.create_token(
        db=db,
        application_id=application_id,
        token=_hash_token(new_token),  # Store hash, not plain token
        token_type=token_type,
        expires_at=new_token_expiry,
    )
    logger.info(f"Created new {token_type} token for application {application_id}")

    # Send appropriate email based on token type
    try:
        if token_type == TokenType.APPLICANT_VERIFICATION:
            await send_applicant_verification(
                to_email=recipient_email,
                applicant_name=recipient_name,
                school_name=application.school_name,
                token=new_token,
            )
        else:
            # For principal confirmation, we need the full context
            from app.modules.school_applications.models import AdminChoice

            designated_admin = (
                application.principal_name
                if application.admin_choice == AdminChoice.PRINCIPAL
                else application.applicant_name or application.principal_name
            )

            await send_principal_confirmation(
                to_email=recipient_email,
                principal_name=recipient_name,
                school_name=application.school_name,
                applicant_name=application.applicant_name or "Staff",
                applicant_role=application.applicant_role or "Staff",
                city=application.city,
                country=application.country_code,
                designated_admin=designated_admin,
                token=new_token,
            )

        logger.info(f"Resent verification email for application {application_id}")
    except Exception as e:
        logger.error(f"Failed to resend verification email: {e}")
        # Still return success - token was created

    return ResendVerificationResponse(
        message="Verification email resent successfully.",
        expires_at=new_token_expiry,
    )


# Status label and description mappings
STATUS_LABELS: dict[ApplicationStatus, str] = {
    ApplicationStatus.AWAITING_APPLICANT_VERIFICATION: "Awaiting Email Verification",
    ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION: "Awaiting Principal Confirmation",
    ApplicationStatus.PENDING_REVIEW: "Pending Review",
    ApplicationStatus.UNDER_REVIEW: "Under Review",
    ApplicationStatus.MORE_INFO_REQUESTED: "More Information Requested",
    ApplicationStatus.APPROVED: "Approved",
    ApplicationStatus.REJECTED: "Rejected",
    ApplicationStatus.EXPIRED: "Expired",
}

STATUS_DESCRIPTIONS: dict[ApplicationStatus, str] = {
    ApplicationStatus.AWAITING_APPLICANT_VERIFICATION: (
        "Please check your email and click the verification link to continue."
    ),
    ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION: (
        "Your email has been verified. Waiting for the principal to confirm the application."
    ),
    ApplicationStatus.PENDING_REVIEW: (
        "Your application is in our review queue. We'll review it within 2-3 business days."
    ),
    ApplicationStatus.UNDER_REVIEW: ("Our team is currently reviewing your application."),
    ApplicationStatus.MORE_INFO_REQUESTED: (
        "We need additional information. Please check your email for details."
    ),
    ApplicationStatus.APPROVED: (
        "Congratulations! Your application has been approved. Check your email for login details."
    ),
    ApplicationStatus.REJECTED: (
        "Unfortunately, your application was not approved. You may reapply after 30 days."
    ),
    ApplicationStatus.EXPIRED: (
        "Your application has expired. Please submit a new application to continue."
    ),
}


def _build_status_steps(application: SchoolApplication) -> list[StatusStep]:
    """
    Build the progress steps for an application status response.

    The steps show the application's journey through the verification process:
    1. Application Submitted - always completed
    2. Email Verified - based on applicant_verified_at
    3. Principal Confirmed - based on principal_confirmed_at (skipped if applicant is principal)
    4. Under Review - based on status being past pending_review
    5. Decision - based on final status (approved/rejected)

    Args:
        application: The school application record

    Returns:
        List of StatusStep objects representing the progress
    """
    steps: list[StatusStep] = []

    # Step 1: Application Submitted (always completed)
    steps.append(
        StatusStep(
            name="Application Submitted",
            completed=True,
            completed_at=application.submitted_at,
        )
    )

    # Step 2: Email Verified
    steps.append(
        StatusStep(
            name="Email Verified",
            completed=application.applicant_verified_at is not None,
            completed_at=application.applicant_verified_at,
        )
    )

    # Step 3: Principal Confirmed (only if applicant is not the principal)
    if not application.applicant_is_principal:
        steps.append(
            StatusStep(
                name="Principal Confirmed",
                completed=application.principal_confirmed_at is not None,
                completed_at=application.principal_confirmed_at,
            )
        )

    # Step 4: Under Review
    review_statuses = {
        ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.MORE_INFO_REQUESTED,
        ApplicationStatus.APPROVED,
        ApplicationStatus.REJECTED,
    }
    under_review_completed = application.status in review_statuses
    steps.append(
        StatusStep(
            name="Under Review",
            completed=under_review_completed,
            completed_at=application.reviewed_at if under_review_completed else None,
        )
    )

    # Step 5: Decision
    decision_statuses = {ApplicationStatus.APPROVED, ApplicationStatus.REJECTED}
    decision_completed = application.status in decision_statuses
    steps.append(
        StatusStep(
            name="Decision",
            completed=decision_completed,
            completed_at=application.reviewed_at if decision_completed else None,
        )
    )

    return steps


async def get_application_status(
    db: AsyncSession,
    application_id: UUID,
    email: str,
) -> ApplicationStatusResponse:
    """
    Get the current status of an application.

    This provides a user-friendly status view including progress steps.
    The email is required for security - only the applicant should be able
    to view the application status.

    Args:
        db: Database session
        application_id: UUID of the application
        email: Email address (must match applicant email for security)

    Returns:
        ApplicationStatusResponse with detailed status information

    Raises:
        ApplicationNotFoundError: If application doesn't exist
        InvalidEmailError: If email doesn't match (prevents unauthorized access)
    """
    logger.info(f"Getting status for application {application_id}")

    # Get the application
    application = await repository.get_by_id(db, application_id)

    if not application:
        logger.warning(f"Application not found for status check: {application_id}")
        raise ApplicationNotFoundError(application_id)

    # Get effective applicant email
    effective_email = get_effective_applicant_email_from_model(application)

    # Validate email matches (case-insensitive comparison for security)
    if email.lower() != effective_email.lower():
        logger.warning(
            f"Unauthorized status check attempt for application {application_id}: "
            f"provided email does not match"
        )
        raise InvalidEmailError()

    # Build response
    return ApplicationStatusResponse(
        id=application.id,
        school_name=application.school_name,
        status=application.status,
        status_label=STATUS_LABELS.get(application.status, str(application.status.value)),
        status_description=STATUS_DESCRIPTIONS.get(
            application.status,
            "Please contact support for more information.",
        ),
        submitted_at=application.submitted_at,
        applicant_verified_at=application.applicant_verified_at,
        principal_confirmed_at=application.principal_confirmed_at,
        steps=_build_status_steps(application),
    )


# ============================================
# Admin Service Functions
# ============================================


class CannotReviewApplicationError(ApplicationServiceError):
    """Raised when application cannot be reviewed (wrong status)."""

    def __init__(self, current_status: str):
        super().__init__(
            message=f"Cannot review application in status: {current_status}. "
            "Application must be in 'pending_review' status.",
            error_code="CANNOT_REVIEW_APPLICATION",
            status_code=409,
        )


class CannotDecideApplicationError(ApplicationServiceError):
    """Raised when application cannot have a decision made (wrong status)."""

    def __init__(self, current_status: str, action: str):
        super().__init__(
            message=f"Cannot {action} application in status: {current_status}. "
            "Application must be in 'under_review' or 'more_info_requested' status.",
            error_code="CANNOT_DECIDE_APPLICATION",
            status_code=409,
        )


class SchoolProvisioningError(ApplicationServiceError):
    """Raised when school provisioning fails."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="SCHOOL_PROVISIONING_FAILED",
            status_code=500,
        )


# Valid statuses for starting a review
REVIEWABLE_STATUSES = {
    ApplicationStatus.PENDING_REVIEW,
}

# Valid statuses for making decisions (approve/reject/request info)
DECIDABLE_STATUSES = {
    ApplicationStatus.UNDER_REVIEW,
    ApplicationStatus.MORE_INFO_REQUESTED,
    ApplicationStatus.PENDING_REVIEW,  # Allow fast-track decisions
}


async def admin_get_applications_list(
    db: AsyncSession,
    *,
    status: ApplicationStatus | None = None,
    country_code: str | None = None,
    search: str | None = None,
    sort_by: str = "submitted_at",
    sort_order: str = "asc",
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """
    Get paginated list of applications for admin dashboard.

    Wraps repository function with parameter validation and response formatting.

    Args:
        db: Database session
        status: Filter by application status
        country_code: Filter by 2-letter country code
        search: Search term for school name/emails
        sort_by: Column to sort by
        sort_order: Sort direction (asc/desc)
        skip: Records to skip for pagination
        limit: Maximum records to return

    Returns:
        Dict with applications list, total count, skip, and limit
    """
    logger.info(
        f"Admin listing applications: status={status}, country={country_code}, "
        f"search={search}, sort={sort_by}:{sort_order}, skip={skip}, limit={limit}"
    )

    # Validate and cap limit
    limit = min(max(1, limit), 100)
    skip = max(0, skip)

    applications, total = await repository.get_applications_for_admin(
        db,
        status=status,
        country_code=country_code,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )

    logger.info(f"Found {total} applications, returning {len(applications)}")

    return {
        "applications": applications,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


async def admin_get_dashboard_stats(db: AsyncSession) -> dict:
    """
    Get aggregated statistics for admin dashboard.

    Returns:
        Dict with pending_review, under_review, more_info_requested,
        approved_this_week, total_this_month, avg_review_time_days
    """
    logger.info("Getting dashboard stats")
    stats = await repository.get_dashboard_stats(db)
    logger.info(f"Dashboard stats: {stats}")
    return stats


async def admin_get_application_detail(
    db: AsyncSession,
    application_id: UUID,
) -> SchoolApplication:
    """
    Get complete application details for admin review.

    Unlike the public status endpoint, this returns ALL fields including
    internal_notes. Requires admin authentication (enforced at router level).

    Args:
        db: Database session
        application_id: UUID of the application

    Returns:
        Complete SchoolApplication with all fields

    Raises:
        ApplicationNotFoundError: If application doesn't exist
    """
    logger.info(f"Admin getting application detail: {application_id}")

    application = await repository.get_by_id(db, application_id)

    if not application:
        logger.warning(f"Application not found: {application_id}")
        raise ApplicationNotFoundError(application_id)

    return application


async def admin_start_review(
    db: AsyncSession,
    application_id: UUID,
    admin_id: UUID,
) -> SchoolApplication:
    """
    Start reviewing an application.

    Updates status from PENDING_REVIEW to UNDER_REVIEW and records
    which admin started the review.

    Args:
        db: Database session
        application_id: UUID of the application
        admin_id: UUID of the admin starting the review

    Returns:
        Updated SchoolApplication

    Raises:
        ApplicationNotFoundError: If application doesn't exist
        CannotReviewApplicationError: If application not in reviewable status
    """
    logger.info(f"Admin {admin_id} starting review of application {application_id}")

    application = await repository.get_by_id(db, application_id)

    if not application:
        logger.warning(f"Application not found: {application_id}")
        raise ApplicationNotFoundError(application_id)

    if application.status not in REVIEWABLE_STATUSES:
        logger.warning(
            f"Cannot review application {application_id}: "
            f"status={application.status} not in {REVIEWABLE_STATUSES}"
        )
        raise CannotReviewApplicationError(application.status.value)

    try:
        updated = await repository.update_application_for_review(db, application_id, admin_id)
        logger.info(f"Application {application_id} now under review by {admin_id}")
        return updated
    except repository.InvalidStatusTransitionError as e:
        logger.error(f"Status transition error: {e}")
        raise CannotReviewApplicationError(application.status.value) from e


async def admin_request_more_info(
    db: AsyncSession,
    application_id: UUID,
    admin_id: UUID,
    message: str,
) -> SchoolApplication:
    """
    Request more information from the applicant.

    Updates status to MORE_INFO_REQUESTED, stores the message,
    and sends email notification to applicant.

    Args:
        db: Database session
        application_id: UUID of the application
        admin_id: UUID of the admin making the request
        message: Message explaining what information is needed

    Returns:
        Updated SchoolApplication

    Raises:
        ApplicationNotFoundError: If application doesn't exist
        CannotDecideApplicationError: If application not in decidable status
    """
    from app.core.email import send_more_info_requested

    logger.info(f"Admin {admin_id} requesting more info for application {application_id}")

    application = await repository.get_by_id(db, application_id)

    if not application:
        logger.warning(f"Application not found: {application_id}")
        raise ApplicationNotFoundError(application_id)

    if application.status not in DECIDABLE_STATUSES:
        logger.warning(
            f"Cannot request info for application {application_id}: status={application.status}"
        )
        raise CannotDecideApplicationError(application.status.value, "request info from")

    try:
        updated = await repository.update_application_decision(
            db,
            application_id,
            ApplicationStatus.MORE_INFO_REQUESTED,
            decision_reason=message,
            reviewed_by=admin_id,
        )
        logger.info(f"Application {application_id} status updated to more_info_requested")

        # Send email to applicant (non-blocking)
        try:
            applicant_email = get_effective_applicant_email_from_model(application)
            applicant_name = get_effective_applicant_name_from_model(application)

            await send_more_info_requested(
                to_email=applicant_email,
                applicant_name=applicant_name,
                school_name=application.school_name,
                admin_message=message,
                application_id=str(application_id),
            )
            logger.info(f"Sent more info request email to {applicant_email}")
        except Exception as e:
            logger.error(f"Failed to send more info request email: {e}", exc_info=True)
            # Don't fail the request - email is non-critical

        return updated

    except repository.InvalidStatusTransitionError as e:
        logger.error(f"Status transition error: {e}")
        raise CannotDecideApplicationError(application.status.value, "request info from") from e


async def admin_add_internal_note(
    db: AsyncSession,
    application_id: UUID,
    admin_id: UUID,
    note: str,
) -> dict:
    """
    Add an internal note to an application.

    Notes are visible only to admins and are stored in the internal_notes
    JSONB field as an array of note objects.

    Args:
        db: Database session
        application_id: UUID of the application
        admin_id: UUID of the admin adding the note
        note: Note content

    Returns:
        The newly created note object

    Raises:
        ApplicationNotFoundError: If application doesn't exist
    """
    logger.info(f"Admin {admin_id} adding note to application {application_id}")

    application = await repository.get_by_id(db, application_id)

    if not application:
        logger.warning(f"Application not found: {application_id}")
        raise ApplicationNotFoundError(application_id)

    new_note = await repository.add_internal_note(db, application_id, note, admin_id)

    logger.info(f"Note added to application {application_id}")
    return new_note


async def admin_reject_application(
    db: AsyncSession,
    application_id: UUID,
    admin_id: UUID,
    reason: str,
) -> SchoolApplication:
    """
    Reject an application.

    Updates status to REJECTED, stores the reason, and sends
    rejection notification email to applicant.

    Args:
        db: Database session
        application_id: UUID of the application
        admin_id: UUID of the admin rejecting
        reason: Detailed reason for rejection

    Returns:
        Updated SchoolApplication

    Raises:
        ApplicationNotFoundError: If application doesn't exist
        CannotDecideApplicationError: If application not in decidable status
    """
    from app.core.email import send_application_rejected

    logger.info(f"Admin {admin_id} rejecting application {application_id}")

    application = await repository.get_by_id(db, application_id)

    if not application:
        logger.warning(f"Application not found: {application_id}")
        raise ApplicationNotFoundError(application_id)

    if application.status not in DECIDABLE_STATUSES:
        logger.warning(f"Cannot reject application {application_id}: status={application.status}")
        raise CannotDecideApplicationError(application.status.value, "reject")

    try:
        updated = await repository.update_application_decision(
            db,
            application_id,
            ApplicationStatus.REJECTED,
            decision_reason=reason,
            reviewed_by=admin_id,
        )
        logger.info(f"Application {application_id} rejected")

        # Send rejection email (non-blocking)
        try:
            applicant_email = get_effective_applicant_email_from_model(application)
            applicant_name = get_effective_applicant_name_from_model(application)

            await send_application_rejected(
                to_email=applicant_email,
                applicant_name=applicant_name,
                school_name=application.school_name,
                rejection_reason=reason,
            )
            logger.info(f"Sent rejection email to {applicant_email}")
        except Exception as e:
            logger.error(f"Failed to send rejection email: {e}", exc_info=True)
            # Don't fail the request - email is non-critical

        return updated

    except repository.InvalidStatusTransitionError as e:
        logger.error(f"Status transition error: {e}")
        raise CannotDecideApplicationError(application.status.value, "reject") from e


async def admin_approve_application(
    db: AsyncSession,
    application_id: UUID,
    admin_id: UUID,
) -> dict:
    """
    Approve an application and provision the school.

    This is the CRITICAL atomic operation that:
    1. Validates application is in a decidable status
    2. Creates the school tenant record
    3. Creates the admin user account with temp password
    4. Updates application status to APPROVED
    5. Sends welcome email with credentials

    All database operations are atomic - if any step fails, everything
    rolls back. Email sending is outside the transaction.

    Args:
        db: Database session
        application_id: UUID of the application
        admin_id: UUID of the admin approving

    Returns:
        Dict with application_id, school_id, admin_user_id, message

    Raises:
        ApplicationNotFoundError: If application doesn't exist
        CannotDecideApplicationError: If application not in decidable status
        SchoolProvisioningError: If school creation fails
    """
    from app.core.email import send_application_approved

    logger.info(f"Admin {admin_id} approving application {application_id}")

    application = await repository.get_by_id(db, application_id)

    if not application:
        logger.warning(f"Application not found: {application_id}")
        raise ApplicationNotFoundError(application_id)

    if application.status not in DECIDABLE_STATUSES:
        logger.warning(f"Cannot approve application {application_id}: status={application.status}")
        raise CannotDecideApplicationError(application.status.value, "approve")

    # Determine who becomes the school admin
    from app.modules.school_applications.models import AdminChoice

    if application.applicant_is_principal or application.admin_choice == AdminChoice.PRINCIPAL:
        admin_name = application.principal_name
        admin_email = application.principal_email
    else:
        admin_name = application.applicant_name or application.principal_name
        admin_email = application.applicant_email or application.principal_email

    # Generate secure temporary password (24 bytes = 32 chars URL-safe)
    temp_password = secrets.token_urlsafe(24)

    try:
        # ============================================
        # ATOMIC TRANSACTION: All DB operations must succeed
        # ============================================
        from app.core.security import hash_password
        from app.modules.schools.repository import SchoolRepository
        from app.modules.users.models import UserRole
        from app.modules.users.repository import UserRepository

        # Check if admin email already exists (prevent duplicate accounts)
        existing_user = await UserRepository.get_by_email(db, admin_email)
        if existing_user:
            logger.warning(f"User with email {admin_email} already exists")
            raise SchoolProvisioningError(
                f"A user with email {admin_email} already exists. "
                "Please contact support or use a different email."
            )

        # Parse admin name into first/last name
        name_parts = admin_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Create the school record
        school = await SchoolRepository.create(
            db,
            name=application.school_name,
            year_established=application.year_established,
            school_type=application.school_type.value,
            student_population=application.student_population.value,
            country_code=application.country_code,
            city=application.city,
            address=application.address,
            principal_name=application.principal_name,
            principal_email=application.principal_email,
            principal_phone=application.principal_phone,
            phone=application.school_phone,
            email=application.school_email,
            online_presence=application.online_presence,
            application_id=str(application_id),
        )

        logger.info(f"Created school: {school.id} - {school.name}")

        # Create the admin user with hashed temp password
        hashed_password = hash_password(temp_password)

        admin_user = await UserRepository.create(
            db,
            email=admin_email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.SCHOOL_ADMIN,
            school_id=school.id,
            is_active=True,
            is_verified=True,
            must_change_password=True,
        )

        logger.info(f"Created admin user: {admin_user.id} - {admin_user.email}")

        # Update application status to APPROVED
        await repository.update_application_decision(
            db,
            application_id,
            ApplicationStatus.APPROVED,
            reviewed_by=admin_id,
        )

        logger.info(
            f"Application {application_id} approved. "
            f"School ID: {school.id}, Admin User ID: {admin_user.id}"
        )

        # ============================================
        # END ATOMIC TRANSACTION
        # ============================================

        school_id = school.id
        admin_user_id = admin_user.id

        # Send welcome email with credentials (outside transaction)
        try:
            await send_application_approved(
                to_email=admin_email,
                admin_name=admin_name,
                school_name=application.school_name,
                admin_email=admin_email,
                temp_password=temp_password,
            )
            logger.info(f"Sent welcome email to {admin_email}")
        except Exception as e:
            logger.error(
                f"Failed to send welcome email: {e}. "
                f"School {school_id} was created but email failed.",
                exc_info=True,
            )
            # Don't fail - school is created, admin can request password reset
            # Add internal note about email failure (best effort, ignore failures)
            with contextlib.suppress(Exception):
                await repository.add_internal_note(
                    db,
                    application_id,
                    f"SYSTEM: Welcome email failed to send. Error: {str(e)}",
                    admin_id,
                )

        return {
            "id": application_id,
            "school_id": school_id,
            "admin_user_id": admin_user_id,
            "message": "Application approved. School and admin account created successfully.",
        }

    except repository.InvalidStatusTransitionError as e:
        logger.error(f"Status transition error during approval: {e}")
        raise CannotDecideApplicationError(application.status.value, "approve") from e
    except Exception as e:
        logger.error(f"School provisioning failed: {e}", exc_info=True)
        # Add internal note about failure (best effort, ignore failures)
        with contextlib.suppress(Exception):
            await repository.add_internal_note(
                db,
                application_id,
                f"SYSTEM: Provisioning failed. Error: {str(e)}",
                admin_id,
            )

        raise SchoolProvisioningError(
            f"Failed to provision school: {str(e)}. Please try again or contact support."
        ) from e
