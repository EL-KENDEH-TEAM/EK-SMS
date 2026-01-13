"""
School Applications Repository

Database operations for school registration applications and verification tokens.
All operations are async and follow the repository pattern for clean separation
of concerns between data access and business logic.

Design Principles:
- All queries are parameterized (no SQL injection)
- Async operations for non-blocking I/O
- Single responsibility - only database operations, no business logic
- Timezone-aware datetime handling (UTC)
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ApplicationStatus, SchoolApplication, TokenType, VerificationToken
from .schemas import SchoolApplicationCreate


async def create(db: AsyncSession, data: SchoolApplicationCreate) -> SchoolApplication:
    """Create a new school application."""

    new_application = SchoolApplication(
        # School info
        school_name=data.school.name,
        year_established=data.school.year_established,
        school_type=data.school.school_type,
        student_population=data.school.student_population,
        # Location
        country_code=data.location.country_code,
        city=data.location.city,
        address=data.location.address,
        # Contact
        school_phone=data.contact.school_phone,
        school_email=data.contact.school_email,
        principal_name=data.contact.principal_name,
        principal_email=data.contact.principal_email,
        principal_phone=data.contact.principal_phone,
        # Applicant
        applicant_is_principal=data.applicant.is_principal,
        applicant_name=data.applicant.name,
        applicant_email=data.applicant.email,
        applicant_phone=data.applicant.phone,
        applicant_role=data.applicant.role,
        admin_choice=data.applicant.admin_choice,
        # Details
        online_presence=(
            [item.model_dump() for item in data.details.online_presence]
            if data.details.online_presence
            else None
        ),
        reasons=data.details.reasons,
        other_reason=data.details.other_reason,
    )

    db.add(new_application)
    await db.commit()
    await db.refresh(new_application)

    return new_application


async def get_by_id(db: AsyncSession, id: UUID) -> SchoolApplication | None:
    """Get application by ID."""
    return await db.get(SchoolApplication, id)


async def get_by_applicant_email(db: AsyncSession, email: str) -> list[SchoolApplication]:
    """
    Get all applications by the effective applicant email.

    This checks both:
    - applicant_email field (when applicant is NOT the principal)
    - principal_email field (when applicant IS the principal)

    This ensures duplicate detection works correctly regardless of who submitted.
    """
    result = await db.execute(
        select(SchoolApplication).where(
            or_(
                # Case 1: Applicant is not principal, check applicant_email
                SchoolApplication.applicant_email == email,
                # Case 2: Applicant is principal, check principal_email
                (SchoolApplication.applicant_is_principal == True)  # noqa: E712
                & (SchoolApplication.principal_email == email),
            )
        )
    )
    return list(result.scalars().all())


async def get_pending_by_school_and_city(
    db: AsyncSession, name: str, city: str
) -> SchoolApplication | None:
    """Get pending application for a school name + city combination."""
    pending_statuses = [
        ApplicationStatus.AWAITING_APPLICANT_VERIFICATION,
        ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION,
        ApplicationStatus.PENDING_REVIEW,
        ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.MORE_INFO_REQUESTED,
    ]

    result = await db.execute(
        select(SchoolApplication).where(
            SchoolApplication.school_name == name,
            SchoolApplication.city == city,
            SchoolApplication.status.in_(pending_statuses),
        )
    )
    return result.scalar_one_or_none()


# Valid status transitions - prevents invalid state changes
# This state machine ensures applications follow the correct workflow
VALID_STATUS_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.AWAITING_APPLICANT_VERIFICATION: {
        ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION,  # Applicant verified, need principal
        ApplicationStatus.PENDING_REVIEW,  # Applicant verified AND is principal
        ApplicationStatus.EXPIRED,  # Verification timed out
    },
    ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION: {
        ApplicationStatus.PENDING_REVIEW,  # Principal confirmed
        ApplicationStatus.EXPIRED,  # Confirmation timed out
    },
    ApplicationStatus.PENDING_REVIEW: {
        ApplicationStatus.UNDER_REVIEW,  # Admin started reviewing
        ApplicationStatus.APPROVED,  # Fast-track approval
        ApplicationStatus.REJECTED,  # Fast-track rejection
    },
    ApplicationStatus.UNDER_REVIEW: {
        ApplicationStatus.MORE_INFO_REQUESTED,  # Need more info
        ApplicationStatus.APPROVED,  # Approved after review
        ApplicationStatus.REJECTED,  # Rejected after review
    },
    ApplicationStatus.MORE_INFO_REQUESTED: {
        ApplicationStatus.UNDER_REVIEW,  # Info provided, back to review
        ApplicationStatus.EXPIRED,  # Timed out waiting for info
        ApplicationStatus.REJECTED,  # Rejected for non-response
    },
    # Terminal states - no transitions allowed
    ApplicationStatus.APPROVED: set(),
    ApplicationStatus.REJECTED: set(),
    ApplicationStatus.EXPIRED: set(),
}


class InvalidStatusTransitionError(ValueError):
    """Raised when an invalid status transition is attempted."""

    def __init__(
        self,
        current_status: ApplicationStatus,
        new_status: ApplicationStatus,
    ):
        self.current_status = current_status
        self.new_status = new_status
        valid_transitions = VALID_STATUS_TRANSITIONS.get(current_status, set())
        super().__init__(
            f"Invalid status transition: {current_status.value} -> {new_status.value}. "
            f"Valid transitions: {[s.value for s in valid_transitions]}"
        )


async def update_status(
    db: AsyncSession,
    id: UUID,
    status: ApplicationStatus,
    **kwargs,
) -> SchoolApplication:
    """
    Update application status and optional fields.

    Validates that the status transition is allowed by the state machine.
    This prevents invalid transitions like jumping directly from
    AWAITING_APPLICANT_VERIFICATION to APPROVED.

    Args:
        db: Database session
        id: Application UUID
        status: New status to set
        **kwargs: Additional fields to update (e.g., applicant_verified_at)

    Returns:
        Updated SchoolApplication

    Raises:
        ValueError: If application not found
        InvalidStatusTransitionError: If status transition is not allowed
    """
    application = await get_by_id(db, id)
    if not application:
        raise ValueError(f"Application {id} not found")

    # Validate status transition
    current_status = application.status
    valid_transitions = VALID_STATUS_TRANSITIONS.get(current_status, set())

    if status != current_status and status not in valid_transitions:
        raise InvalidStatusTransitionError(current_status, status)

    # Update status
    application.status = status

    # Update any additional fields passed in kwargs
    for key, value in kwargs.items():
        if hasattr(application, key):
            setattr(application, key, value)

    await db.commit()
    await db.refresh(application)

    return application


async def get_expired_unverified(
    db: AsyncSession, before_datetime: datetime
) -> list[SchoolApplication]:
    """Get applications that are still awaiting verification and submitted before the given datetime."""
    result = await db.execute(
        select(SchoolApplication).where(
            SchoolApplication.status == ApplicationStatus.AWAITING_APPLICANT_VERIFICATION,
            SchoolApplication.submitted_at < before_datetime,
        )
    )
    return list(result.scalars().all())


# ============================================
# VerificationToken Repository
# ============================================


async def create_token(
    db: AsyncSession,
    application_id: UUID,
    token: str,
    token_type: TokenType,
    expires_at: datetime,
) -> VerificationToken:
    """Create a new verification token."""

    new_token = VerificationToken(
        application_id=application_id,
        token=token,
        token_type=token_type,
        expires_at=expires_at,
    )

    db.add(new_token)
    await db.commit()
    await db.refresh(new_token)

    return new_token


async def get_by_token(db: AsyncSession, token: str) -> VerificationToken | None:
    """Get verification token by token string."""

    result = await db.execute(select(VerificationToken).where(VerificationToken.token == token))
    return result.scalar_one_or_none()


async def mark_token_used(db: AsyncSession, token: str) -> VerificationToken:
    """Mark a token as used."""

    verification_token = await get_by_token(db, token)

    if not verification_token:
        raise ValueError("Token not found")

    verification_token.used_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(verification_token)

    return verification_token


async def delete_tokens_for_application(
    db: AsyncSession,
    application_id: UUID,
    token_type: TokenType | None = None,
) -> None:
    """Delete tokens for an application, optionally filtered by type."""

    stmt = delete(VerificationToken).where(VerificationToken.application_id == application_id)

    if token_type:
        stmt = stmt.where(VerificationToken.token_type == token_type)

    await db.execute(stmt)
    await db.commit()


# ============================================
# Background Job Repository Methods
# ============================================


async def get_applications_needing_reminder(
    db: AsyncSession,
    submitted_before: datetime,
    status: ApplicationStatus,
) -> list[SchoolApplication]:
    """
    Get applications that need a reminder email.

    Finds applications that:
    1. Are in the specified status (awaiting verification or principal confirmation)
    2. Were submitted before the given datetime (e.g., 48 hours ago)
    3. Have NOT yet received a reminder (reminder_sent_at is NULL)

    This query is idempotent - running it multiple times will return the same
    results until applications are updated.

    Args:
        db: Database session
        submitted_before: Find applications submitted before this time
        status: The status to filter by (AWAITING_APPLICANT_VERIFICATION or
                AWAITING_PRINCIPAL_CONFIRMATION)

    Returns:
        List of applications that need a reminder
    """
    result = await db.execute(
        select(SchoolApplication).where(
            and_(
                SchoolApplication.status == status,
                SchoolApplication.submitted_at < submitted_before,
                SchoolApplication.reminder_sent_at.is_(None),
            )
        )
    )
    return list(result.scalars().all())


async def get_applications_to_expire(
    db: AsyncSession,
    submitted_before: datetime,
) -> list[SchoolApplication]:
    """
    Get applications that should be marked as expired.

    Finds applications that:
    1. Are still in AWAITING_APPLICANT_VERIFICATION or AWAITING_PRINCIPAL_CONFIRMATION status
    2. Were submitted before the given datetime (e.g., 72 hours ago)

    These applications have exceeded the verification window and should be expired.

    Args:
        db: Database session
        submitted_before: Find applications submitted before this time (72 hours ago)

    Returns:
        List of applications that should be expired
    """
    expirable_statuses = [
        ApplicationStatus.AWAITING_APPLICANT_VERIFICATION,
        ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION,
    ]

    result = await db.execute(
        select(SchoolApplication).where(
            and_(
                SchoolApplication.status.in_(expirable_statuses),
                SchoolApplication.submitted_at < submitted_before,
            )
        )
    )
    return list(result.scalars().all())


async def mark_reminder_sent(
    db: AsyncSession,
    application_id: UUID,
    sent_at: datetime | None = None,
) -> SchoolApplication | None:
    """
    Mark that a reminder has been sent for an application.

    Updates the reminder_sent_at field to prevent duplicate reminders.
    This is crucial for idempotency - the job can run multiple times
    without sending multiple reminders.

    Args:
        db: Database session
        application_id: UUID of the application
        sent_at: When the reminder was sent (defaults to now)

    Returns:
        The updated application, or None if not found
    """
    application = await get_by_id(db, application_id)

    if not application:
        return None

    application.reminder_sent_at = sent_at or datetime.now(UTC)

    await db.commit()
    await db.refresh(application)

    return application


async def mark_application_expired(
    db: AsyncSession,
    application_id: UUID,
) -> SchoolApplication | None:
    """
    Mark an application as expired.

    Updates the status to EXPIRED. This is a terminal state -
    the applicant must submit a new application to continue.

    Args:
        db: Database session
        application_id: UUID of the application

    Returns:
        The updated application, or None if not found
    """
    return await update_status(db, application_id, ApplicationStatus.EXPIRED)


async def get_valid_token_for_application(
    db: AsyncSession,
    application_id: UUID,
    token_type: TokenType,
) -> VerificationToken | None:
    """
    Get a valid (unused, unexpired) token for an application.

    Used by the reminder job to get the current token for inclusion
    in reminder emails.

    Args:
        db: Database session
        application_id: UUID of the application
        token_type: Type of token to find

    Returns:
        The valid token, or None if not found or expired
    """
    now = datetime.now(UTC)

    result = await db.execute(
        select(VerificationToken).where(
            and_(
                VerificationToken.application_id == application_id,
                VerificationToken.token_type == token_type,
                VerificationToken.used_at.is_(None),
                VerificationToken.expires_at > now,
            )
        )
    )
    return result.scalar_one_or_none()


async def get_principal_tokens_needing_reminder(
    db: AsyncSession,
    created_before: datetime,
) -> list[tuple[SchoolApplication, VerificationToken]]:
    """
    Get principal confirmation tokens that need a reminder email.

    This method uses TOKEN creation time (not application submission time)
    to correctly calculate when reminders should be sent for principal
    confirmation. The principal gets a fresh 72-hour window from when
    their token was created (after applicant verification).

    Finds tokens that:
    1. Are PRINCIPAL_CONFIRMATION type
    2. Were created before the given datetime (e.g., 48 hours ago)
    3. Are not yet used or expired
    4. Belong to applications that haven't received a reminder

    Args:
        db: Database session
        created_before: Find tokens created before this time (e.g., 48 hours ago)

    Returns:
        List of (application, token) tuples needing reminders
    """
    now = datetime.now(UTC)

    result = await db.execute(
        select(SchoolApplication, VerificationToken)
        .join(
            VerificationToken,
            SchoolApplication.id == VerificationToken.application_id,
        )
        .where(
            and_(
                SchoolApplication.status == ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION,
                SchoolApplication.reminder_sent_at.is_(None),
                VerificationToken.token_type == TokenType.PRINCIPAL_CONFIRMATION,
                VerificationToken.created_at < created_before,
                VerificationToken.used_at.is_(None),
                VerificationToken.expires_at > now,
            )
        )
    )
    # Convert Row objects to proper tuples
    return [(row[0], row[1]) for row in result.all()]


async def get_principal_tokens_to_expire(
    db: AsyncSession,
    created_before: datetime,
) -> list[tuple[SchoolApplication, VerificationToken]]:
    """
    Get applications with principal tokens that should be expired.

    This method uses TOKEN creation time (not application submission time)
    to correctly calculate when applications should expire. The principal
    gets a full 72-hour window from when their token was created.

    Finds applications where:
    1. Status is AWAITING_PRINCIPAL_CONFIRMATION
    2. Principal token was created more than 72 hours ago
    3. Token has not been used

    Args:
        db: Database session
        created_before: Find tokens created before this time (e.g., 72 hours ago)

    Returns:
        List of (application, token) tuples to expire
    """
    result = await db.execute(
        select(SchoolApplication, VerificationToken)
        .join(
            VerificationToken,
            SchoolApplication.id == VerificationToken.application_id,
        )
        .where(
            and_(
                SchoolApplication.status == ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION,
                VerificationToken.token_type == TokenType.PRINCIPAL_CONFIRMATION,
                VerificationToken.created_at < created_before,
                VerificationToken.used_at.is_(None),
            )
        )
    )
    # Convert Row objects to proper tuples
    return [(row[0], row[1]) for row in result.all()]
