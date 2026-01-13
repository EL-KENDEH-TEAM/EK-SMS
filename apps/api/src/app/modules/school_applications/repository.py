from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
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
    """Get all applications by applicant email."""
    result = await db.execute(
        select(SchoolApplication).where(SchoolApplication.applicant_email == email)
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


async def update_status(
    db: AsyncSession,
    id: UUID,
    status: ApplicationStatus,
    **kwargs,
) -> SchoolApplication:
    """Update application status and optional fields."""
    application = await get_by_id(db, id)
    if not application:
        raise ValueError(f"Application {id} not found")

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
