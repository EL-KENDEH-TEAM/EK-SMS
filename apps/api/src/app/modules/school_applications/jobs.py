"""
School Applications Background Jobs

Scheduled tasks for managing school registration application lifecycle:
1. Send verification reminders at 48 hours
2. Expire unverified applications at 72 hours

Design Principles:
- Jobs are idempotent (safe to run multiple times)
- Jobs handle their own database sessions
- Jobs log all operations for auditing
- Jobs continue processing even if individual items fail
- Jobs use batching for large datasets

Schedule:
- Both jobs run hourly to catch applications as they become eligible
- Jobs can also be triggered manually via admin endpoints

Error Handling:
- Individual application failures don't stop the job
- All errors are logged for monitoring
- Email failures don't prevent database updates (with appropriate logging)
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from apscheduler.triggers.interval import IntervalTrigger

from app.core.database import async_session_maker
from app.core.email import (
    send_application_expired,
    send_verification_reminder,
)
from app.core.scheduler import register_job
from app.modules.school_applications import repository
from app.modules.school_applications.helpers import (
    get_effective_applicant_email_from_model,
    get_effective_applicant_name_from_model,
)
from app.modules.school_applications.models import (
    ApplicationStatus,
    SchoolApplication,
    TokenType,
    VerificationToken,
)

logger = logging.getLogger(__name__)

# Job configuration constants
REMINDER_THRESHOLD_HOURS = 48  # Send reminder after 48 hours
EXPIRY_THRESHOLD_HOURS = 72  # Expire after 72 hours
HOURS_REMAINING_AT_REMINDER = EXPIRY_THRESHOLD_HOURS - REMINDER_THRESHOLD_HOURS  # 24 hours

# Job IDs for registration and manual triggering
JOB_ID_SEND_REMINDERS = "school_applications_send_reminders"
JOB_ID_EXPIRE_APPLICATIONS = "school_applications_expire_applications"


async def _process_applicant_verification_reminder(
    application: SchoolApplication,
) -> dict[str, Any]:
    """
    Process a single application needing applicant verification reminder.

    Args:
        application: The application to process

    Returns:
        Dict with processing result
    """
    async with async_session_maker() as db:
        # Get the valid token for this application
        token = await repository.get_valid_token_for_application(
            db,
            application.id,
            TokenType.APPLICANT_VERIFICATION,
        )

        if not token:
            logger.warning(
                f"No valid token found for application {application.id}, "
                "skipping reminder (token may have expired)"
            )
            return {
                "application_id": str(application.id),
                "status": "skipped",
                "reason": "no_valid_token",
            }

        # Get applicant details
        applicant_email = get_effective_applicant_email_from_model(application)
        applicant_name = get_effective_applicant_name_from_model(application)

        # Send reminder email
        email_sent = await send_verification_reminder(
            to_email=applicant_email,
            applicant_name=applicant_name,
            school_name=application.school_name,
            token=token.token,
            hours_remaining=HOURS_REMAINING_AT_REMINDER,
        )

        if not email_sent:
            logger.error(f"Failed to send reminder email for application {application.id}")
            # Still mark as sent to prevent retry loops - the token is still valid
            # and they can use it if they find the original email

        # Mark reminder as sent (idempotency)
        await repository.mark_reminder_sent(db, application.id)

        logger.info(f"Processed applicant verification reminder for application {application.id}")

        return {
            "application_id": str(application.id),
            "status": "sent" if email_sent else "marked_sent_email_failed",
            "applicant_email": applicant_email,
        }


async def _process_principal_confirmation_reminder(
    application: SchoolApplication,
) -> dict[str, Any]:
    """
    Process a single application needing principal confirmation reminder.

    Args:
        application: The application to process

    Returns:
        Dict with processing result
    """
    async with async_session_maker() as db:
        # Get the valid token for this application
        token = await repository.get_valid_token_for_application(
            db,
            application.id,
            TokenType.PRINCIPAL_CONFIRMATION,
        )

        if not token:
            logger.warning(
                f"No valid principal token found for application {application.id}, "
                "skipping reminder"
            )
            return {
                "application_id": str(application.id),
                "status": "skipped",
                "reason": "no_valid_token",
            }

        # Send reminder email to principal
        email_sent = await send_verification_reminder(
            to_email=application.principal_email,
            applicant_name=application.principal_name,
            school_name=application.school_name,
            token=token.token,
            hours_remaining=HOURS_REMAINING_AT_REMINDER,
        )

        if not email_sent:
            logger.error(
                f"Failed to send principal reminder email for application {application.id}"
            )

        # Mark reminder as sent
        await repository.mark_reminder_sent(db, application.id)

        logger.info(f"Processed principal confirmation reminder for application {application.id}")

        return {
            "application_id": str(application.id),
            "status": "sent" if email_sent else "marked_sent_email_failed",
            "principal_email": application.principal_email,
        }


async def _process_principal_confirmation_reminder_with_token(
    application: SchoolApplication,
    token: VerificationToken,
) -> dict[str, Any]:
    """
    Process a single application needing principal confirmation reminder.

    This version takes the token directly (already retrieved from the
    token-based query) to avoid an extra database lookup.

    Args:
        application: The application to process
        token: The principal confirmation token

    Returns:
        Dict with processing result
    """
    async with async_session_maker() as db:
        # Send reminder email to principal
        email_sent = await send_verification_reminder(
            to_email=application.principal_email,
            applicant_name=application.principal_name,
            school_name=application.school_name,
            token=token.token,
            hours_remaining=HOURS_REMAINING_AT_REMINDER,
        )

        if not email_sent:
            logger.error(
                f"Failed to send principal reminder email for application {application.id}"
            )

        # Mark reminder as sent
        await repository.mark_reminder_sent(db, application.id)

        logger.info(f"Processed principal confirmation reminder for application {application.id}")

        return {
            "application_id": str(application.id),
            "status": "sent" if email_sent else "marked_sent_email_failed",
            "principal_email": application.principal_email,
        }


async def send_verification_reminders() -> dict[str, Any]:
    """
    Send verification reminder emails for applications at 48 hours.

    This job finds all applications that:
    1. Are awaiting applicant verification or principal confirmation
    2. Were submitted more than 48 hours ago
    3. Have not yet received a reminder

    The job is idempotent - it can safely run multiple times without
    sending duplicate reminders because it marks each application
    after processing.

    Returns:
        Dict with job execution summary including:
        - executed_at: When the job ran
        - applicant_reminders: Results for applicant verification reminders
        - principal_reminders: Results for principal confirmation reminders
        - total_processed: Total applications processed
        - total_errors: Number of processing errors
    """
    executed_at = datetime.now(UTC)
    reminder_threshold = executed_at - timedelta(hours=REMINDER_THRESHOLD_HOURS)

    logger.info(
        f"Starting verification reminder job. "
        f"Looking for applications submitted before {reminder_threshold.isoformat()}"
    )

    results = {
        "executed_at": executed_at.isoformat(),
        "applicant_reminders": [],
        "principal_reminders": [],
        "total_processed": 0,
        "total_errors": 0,
    }

    # Process applicant verification reminders
    async with async_session_maker() as db:
        applicant_applications = await repository.get_applications_needing_reminder(
            db,
            submitted_before=reminder_threshold,
            status=ApplicationStatus.AWAITING_APPLICANT_VERIFICATION,
        )

    logger.info(
        f"Found {len(applicant_applications)} applications needing applicant verification reminder"
    )

    for application in applicant_applications:
        try:
            result = await _process_applicant_verification_reminder(application)
            results["applicant_reminders"].append(result)
            results["total_processed"] += 1
        except Exception as e:
            logger.error(
                f"Error processing applicant reminder for application {application.id}: {e}",
                exc_info=True,
            )
            results["applicant_reminders"].append(
                {
                    "application_id": str(application.id),
                    "status": "error",
                    "error": str(e),
                }
            )
            results["total_errors"] += 1

    # Process principal confirmation reminders
    # NOTE: Uses TOKEN creation time, not application submission time
    # This ensures principals get a full 72-hour window from when their token was created
    async with async_session_maker() as db:
        principal_tokens = await repository.get_principal_tokens_needing_reminder(
            db,
            created_before=reminder_threshold,
        )

    logger.info(
        f"Found {len(principal_tokens)} applications needing principal confirmation reminder"
    )

    for application, token in principal_tokens:
        try:
            result = await _process_principal_confirmation_reminder_with_token(application, token)
            results["principal_reminders"].append(result)
            results["total_processed"] += 1
        except Exception as e:
            logger.error(
                f"Error processing principal reminder for application {application.id}: {e}",
                exc_info=True,
            )
            results["principal_reminders"].append(
                {
                    "application_id": str(application.id),
                    "status": "error",
                    "error": str(e),
                }
            )
            results["total_errors"] += 1

    logger.info(
        f"Verification reminder job completed. "
        f"Processed: {results['total_processed']}, Errors: {results['total_errors']}"
    )

    return results


async def _process_application_expiry(
    application: SchoolApplication,
) -> dict[str, Any]:
    """
    Process a single application that needs to be expired.

    Args:
        application: The application to expire

    Returns:
        Dict with processing result
    """
    async with async_session_maker() as db:
        # Mark application as expired
        await repository.mark_application_expired(db, application.id)

        # Get applicant details for notification
        applicant_email = get_effective_applicant_email_from_model(application)
        applicant_name = get_effective_applicant_name_from_model(application)

        # Send expiration notification
        email_sent = await send_application_expired(
            to_email=applicant_email,
            applicant_name=applicant_name,
            school_name=application.school_name,
        )

        if not email_sent:
            logger.error(f"Failed to send expiration email for application {application.id}")

        logger.info(f"Expired application {application.id} for school '{application.school_name}'")

        return {
            "application_id": str(application.id),
            "status": "expired",
            "email_sent": email_sent,
            "school_name": application.school_name,
            "previous_status": application.status.value,
        }


async def expire_unverified_applications() -> dict[str, Any]:
    """
    Expire applications that have not been verified within 72 hours.

    This job handles two cases with different timing logic:
    1. AWAITING_APPLICANT_VERIFICATION: Uses submission time (token created at submission)
    2. AWAITING_PRINCIPAL_CONFIRMATION: Uses token creation time (principal gets fresh 72h)

    This ensures principals get a full 72-hour window from when their token was
    created (after applicant verification), not from application submission.

    The job is idempotent - expired applications won't be selected
    again because their status changes.

    Returns:
        Dict with job execution summary including:
        - executed_at: When the job ran
        - applicant_expired: Applications expired for applicant verification timeout
        - principal_expired: Applications expired for principal confirmation timeout
        - total_expired: Total applications expired
        - total_errors: Number of processing errors
    """
    executed_at = datetime.now(UTC)
    expiry_threshold = executed_at - timedelta(hours=EXPIRY_THRESHOLD_HOURS)

    logger.info(f"Starting application expiry job. Threshold: {expiry_threshold.isoformat()}")

    results = {
        "executed_at": executed_at.isoformat(),
        "applicant_expired": [],
        "principal_expired": [],
        "total_expired": 0,
        "total_errors": 0,
    }

    # Part 1: Expire applicant verification timeouts (uses submitted_at)
    async with async_session_maker() as db:
        applicant_applications = await repository.get_expired_unverified(
            db,
            before_datetime=expiry_threshold,
        )

    logger.info(f"Found {len(applicant_applications)} applicant verifications to expire")

    for application in applicant_applications:
        try:
            result = await _process_application_expiry(application)
            results["applicant_expired"].append(result)
            results["total_expired"] += 1
        except Exception as e:
            logger.error(
                f"Error expiring application {application.id}: {e}",
                exc_info=True,
            )
            results["applicant_expired"].append(
                {
                    "application_id": str(application.id),
                    "status": "error",
                    "error": str(e),
                }
            )
            results["total_errors"] += 1

    # Part 2: Expire principal confirmation timeouts (uses token created_at)
    # This ensures principals get a full 72 hours from when their token was created
    async with async_session_maker() as db:
        principal_tokens = await repository.get_principal_tokens_to_expire(
            db,
            created_before=expiry_threshold,
        )

    logger.info(f"Found {len(principal_tokens)} principal confirmations to expire")

    for application, _token in principal_tokens:
        try:
            result = await _process_application_expiry(application)
            results["principal_expired"].append(result)
            results["total_expired"] += 1
        except Exception as e:
            logger.error(
                f"Error expiring application {application.id}: {e}",
                exc_info=True,
            )
            results["principal_expired"].append(
                {
                    "application_id": str(application.id),
                    "status": "error",
                    "error": str(e),
                }
            )
            results["total_errors"] += 1

    logger.info(
        f"Application expiry job completed. "
        f"Expired: {results['total_expired']}, Errors: {results['total_errors']}"
    )

    return results


def register_school_application_jobs() -> None:
    """
    Register all school application background jobs with the scheduler.

    This function should be called during application startup, before
    the scheduler is started.

    Registered jobs:
    1. send_verification_reminders - Runs every hour
    2. expire_unverified_applications - Runs every hour

    The hourly schedule ensures:
    - Applications get reminders promptly after 48 hours
    - Applications are expired promptly after 72 hours
    - Minimal delay between eligibility and action (max 1 hour)
    """
    logger.info("Registering school application background jobs...")

    # Register reminder job - runs every hour
    register_job(
        job_id=JOB_ID_SEND_REMINDERS,
        func=send_verification_reminders,
        trigger=IntervalTrigger(hours=1),
    )
    logger.info(f"Registered job: {JOB_ID_SEND_REMINDERS} (interval: 1 hour)")

    # Register expiry job - runs every hour
    register_job(
        job_id=JOB_ID_EXPIRE_APPLICATIONS,
        func=expire_unverified_applications,
        trigger=IntervalTrigger(hours=1),
    )
    logger.info(f"Registered job: {JOB_ID_EXPIRE_APPLICATIONS} (interval: 1 hour)")

    logger.info("School application background jobs registered successfully")
