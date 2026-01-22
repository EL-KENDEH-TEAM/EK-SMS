"""
School Applications Admin Router

API endpoints for platform administrators to manage school applications.
All endpoints require authentication and platform_admin role.

Endpoints:
- GET /admin/applications - List applications with filters and pagination
- GET /admin/applications/stats - Get dashboard statistics
- GET /admin/applications/{id} - Get application details
- POST /admin/applications/{id}/start-review - Start reviewing application
- POST /admin/applications/{id}/request-info - Request more information
- POST /admin/applications/{id}/notes - Add internal note
- POST /admin/applications/{id}/approve - Approve and provision school
- POST /admin/applications/{id}/reject - Reject application

Security:
- All endpoints require valid JWT token with platform_admin role
- Input validation via Pydantic schemas
- Comprehensive error handling with structured responses
- Audit logging for all admin actions
- Rate limiting on action endpoints to prevent abuse
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AdminUser, get_current_admin_user
from app.core.database import get_db
from app.core.rate_limit import RateLimitExceeded, check_rate_limit
from app.modules.school_applications import service
from app.modules.school_applications.models import ApplicationStatus
from app.modules.school_applications.schemas import (
    AddNoteRequest,
    AddNoteResponse,
    ApplicationDetailResponse,
    ApplicationListItem,
    ApplicationListResponse,
    ApproveResponse,
    DashboardStats,
    InternalNote,
    RejectRequest,
    RejectResponse,
    RequestInfoRequest,
    RequestInfoResponse,
    StartReviewResponse,
)
from app.modules.school_applications.service import (
    ApplicationNotFoundError,
    ApplicationServiceError,
    CannotDecideApplicationError,
    CannotReviewApplicationError,
    SchoolProvisioningError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Rate Limiting Configuration
# ============================================

# Rate limits for admin action endpoints (prevent abuse)
RATE_LIMIT_APPROVE = (10, 60)  # 10 approvals per minute
RATE_LIMIT_REJECT = (10, 60)  # 10 rejections per minute
RATE_LIMIT_REQUEST_INFO = (20, 60)  # 20 info requests per minute
RATE_LIMIT_NOTES = (30, 60)  # 30 notes per minute
RATE_LIMIT_START_REVIEW = (30, 60)  # 30 review starts per minute


async def _check_admin_rate_limit(
    admin: AdminUser,
    action: str,
    limit: int,
    window_seconds: int,
) -> None:
    """
    Check rate limit for an admin action.

    Args:
        admin: The authenticated admin user
        action: Action name (e.g., "approve", "reject")
        limit: Maximum requests allowed
        window_seconds: Time window in seconds

    Raises:
        RateLimitExceeded: If rate limit is exceeded
    """
    key = f"admin:{action}:{admin.id}"
    allowed = await check_rate_limit(key, limit, window_seconds)

    if not allowed:
        logger.warning(
            f"Rate limit exceeded for admin {admin.id} on action '{action}': "
            f"{limit}/{window_seconds}s"
        )
        raise RateLimitExceeded(limit, window_seconds)


# ============================================
# Helper Functions
# ============================================


def _handle_service_error(e: ApplicationServiceError) -> None:
    """Convert service errors to HTTPExceptions."""
    raise HTTPException(
        status_code=e.status_code,
        detail={
            "error": e.error_code,
            "message": e.message,
        },
    )


def _application_to_list_item(app) -> ApplicationListItem:
    """Convert SchoolApplication model to ApplicationListItem schema."""
    return ApplicationListItem(
        id=app.id,
        school_name=app.school_name,
        school_type=app.school_type,
        student_population=app.student_population,
        country_code=app.country_code,
        city=app.city,
        status=app.status,
        submitted_at=app.submitted_at,
        applicant_verified_at=app.applicant_verified_at,
        principal_confirmed_at=app.principal_confirmed_at,
        reviewed_at=app.reviewed_at,
        reviewed_by=app.reviewed_by,
    )


def _application_to_detail(app) -> ApplicationDetailResponse:
    """Convert SchoolApplication model to ApplicationDetailResponse schema."""
    # Convert internal_notes from JSON to InternalNote schemas
    internal_notes = None
    if app.internal_notes:
        internal_notes = [
            InternalNote(
                note=note["note"],
                created_by=UUID(note["created_by"]),
                created_at=datetime.fromisoformat(note["created_at"].replace("Z", "+00:00")),
            )
            for note in app.internal_notes
        ]

    return ApplicationDetailResponse(
        id=app.id,
        school_name=app.school_name,
        year_established=app.year_established,
        school_type=app.school_type,
        student_population=app.student_population,
        country_code=app.country_code,
        city=app.city,
        address=app.address,
        school_phone=app.school_phone,
        school_email=app.school_email,
        principal_name=app.principal_name,
        principal_email=app.principal_email,
        principal_phone=app.principal_phone,
        applicant_is_principal=app.applicant_is_principal,
        applicant_name=app.applicant_name,
        applicant_email=app.applicant_email,
        applicant_phone=app.applicant_phone,
        applicant_role=app.applicant_role,
        admin_choice=app.admin_choice,
        online_presence=app.online_presence,
        reasons=app.reasons,
        other_reason=app.other_reason,
        status=app.status,
        submitted_at=app.submitted_at,
        applicant_verified_at=app.applicant_verified_at,
        principal_confirmed_at=app.principal_confirmed_at,
        reviewed_at=app.reviewed_at,
        reviewed_by=app.reviewed_by,
        decision_reason=app.decision_reason,
        internal_notes=internal_notes,
    )


# ============================================
# List & Stats Endpoints (Task 5)
# ============================================


@router.get(
    "",
    response_model=ApplicationListResponse,
    summary="List Applications",
    description="""
Get paginated list of school applications with optional filters.

**Filters:**
- `status`: Filter by application status
- `country_code`: Filter by 2-letter country code (e.g., "LR", "GH")
- `search`: Search in school name, school email, applicant email, principal email

**Sorting:**
- `sort_by`: Column to sort by (submitted_at, school_name). Default: submitted_at
- `sort_order`: Sort direction (asc, desc). Default: asc (oldest first for fairness)

**Pagination:**
- `skip`: Number of records to skip. Default: 0
- `limit`: Maximum records to return (1-100). Default: 20

**Access:** Platform admin only
""",
    responses={
        200: {
            "description": "List of applications with pagination",
            "model": ApplicationListResponse,
        },
        401: {
            "description": "Unauthorized - invalid or missing token",
        },
        403: {
            "description": "Forbidden - not a platform admin",
        },
    },
)
async def list_applications(
    status: ApplicationStatus | None = Query(
        None,
        description="Filter by application status",
    ),
    country_code: str | None = Query(
        None,
        min_length=2,
        max_length=2,
        description="Filter by 2-letter country code",
    ),
    search: str | None = Query(
        None,
        min_length=1,
        max_length=100,
        description="Search term for school/email",
    ),
    sort_by: str = Query(
        "submitted_at",
        description="Column to sort by",
    ),
    sort_order: str = Query(
        "asc",
        description="Sort direction (asc/desc)",
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Records to skip",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum records to return",
    ),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
) -> ApplicationListResponse:
    """
    List applications with filters and pagination.

    Returns a paginated list of applications for the admin dashboard.
    """
    try:
        result = await service.admin_get_applications_list(
            db,
            status=status,
            country_code=country_code,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit,
        )

        logger.info(
            f"Admin {admin.id} listed applications: "
            f"total={result['total']}, returned={len(result['applications'])}"
        )

        # Convert to schema objects
        applications = [_application_to_list_item(app) for app in result["applications"]]

        return ApplicationListResponse(
            applications=applications,
            total=result["total"],
            skip=result["skip"],
            limit=result["limit"],
        )

    except ApplicationServiceError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.exception(f"Error listing applications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        ) from e


@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Get Dashboard Statistics",
    description="""
Get aggregated statistics for the admin dashboard.

**Statistics returned:**
- `pending_review`: Count of applications awaiting admin action
- `under_review`: Count of applications currently being reviewed
- `more_info_requested`: Count waiting for applicant response
- `approved_this_week`: Count approved in the last 7 days
- `total_this_month`: Total applications received this month
- `avg_review_time_days`: Average days from submission to decision (past 30 days)

**Access:** Platform admin only
""",
    responses={
        200: {
            "description": "Dashboard statistics",
            "model": DashboardStats,
        },
        401: {
            "description": "Unauthorized - invalid or missing token",
        },
        403: {
            "description": "Forbidden - not a platform admin",
        },
    },
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
) -> DashboardStats:
    """
    Get aggregated statistics for the admin dashboard.
    """
    try:
        stats = await service.admin_get_dashboard_stats(db)

        logger.info(f"Admin {admin.id} fetched dashboard stats")

        return DashboardStats(**stats)

    except ApplicationServiceError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.exception(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        ) from e


# ============================================
# Detail & Review Endpoints (Task 6)
# ============================================


@router.get(
    "/{application_id}",
    response_model=ApplicationDetailResponse,
    summary="Get Application Details",
    description="""
Get complete details of a school application for admin review.

Returns all application fields including:
- School information (name, type, population, contact)
- Location (country, city, address)
- Principal and applicant details
- Online presence and reasons for registering
- Status and timeline
- Internal admin notes (visible only to admins)

**Access:** Platform admin only
""",
    responses={
        200: {
            "description": "Complete application details",
            "model": ApplicationDetailResponse,
        },
        401: {
            "description": "Unauthorized - invalid or missing token",
        },
        403: {
            "description": "Forbidden - not a platform admin",
        },
        404: {
            "description": "Application not found",
        },
    },
)
async def get_application_detail(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
) -> ApplicationDetailResponse:
    """
    Get complete details of an application.
    """
    try:
        application = await service.admin_get_application_detail(db, application_id)

        logger.info(f"Admin {admin.id} viewed application {application_id}")

        return _application_to_detail(application)

    except ApplicationNotFoundError as e:
        logger.warning(f"Application not found: {application_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except ApplicationServiceError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.exception(f"Error getting application detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        ) from e


@router.post(
    "/{application_id}/start-review",
    response_model=StartReviewResponse,
    summary="Start Reviewing Application",
    description="""
Start reviewing an application.

Updates the application status from `pending_review` to `under_review`
and records which admin is reviewing.

**Requirements:**
- Application must be in `pending_review` status
- Admin must be authenticated with platform_admin role

**Effects:**
- Status changes to `under_review`
- `reviewed_by` set to current admin
- `reviewed_at` set to current timestamp

**Access:** Platform admin only
""",
    responses={
        200: {
            "description": "Review started successfully",
            "model": StartReviewResponse,
        },
        401: {
            "description": "Unauthorized - invalid or missing token",
        },
        403: {
            "description": "Forbidden - not a platform admin",
        },
        404: {
            "description": "Application not found",
        },
        409: {
            "description": "Application not in reviewable status",
        },
    },
)
async def start_review(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
) -> StartReviewResponse:
    """
    Start reviewing an application.
    """
    # Rate limiting: 30 review starts per minute per admin
    await _check_admin_rate_limit(admin, "start_review", *RATE_LIMIT_START_REVIEW)

    try:
        application = await service.admin_start_review(db, application_id, admin.id)

        logger.info(f"Admin {admin.id} started review of application {application_id}")

        return StartReviewResponse(
            id=application.id,
            status=application.status,
            reviewed_by=application.reviewed_by,
            reviewed_at=application.reviewed_at,
            message="Application is now under review",
        )

    except ApplicationNotFoundError as e:
        logger.warning(f"Application not found: {application_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except CannotReviewApplicationError as e:
        logger.warning(f"Cannot review application {application_id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except ApplicationServiceError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.exception(f"Error starting review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        ) from e


# ============================================
# Request Info & Notes Endpoints (Task 7)
# ============================================


@router.post(
    "/{application_id}/request-info",
    response_model=RequestInfoResponse,
    summary="Request More Information",
    description="""
Request additional information from the applicant.

Updates status to `more_info_requested` and sends an email to the applicant
with the admin's message explaining what information is needed.

**Requirements:**
- Application must be in `under_review`, `more_info_requested`, or `pending_review` status
- Message must be 10-1000 characters

**Effects:**
- Status changes to `more_info_requested`
- `decision_reason` stores the message
- Email sent to applicant with the message

**Access:** Platform admin only
""",
    responses={
        200: {
            "description": "Information request sent",
            "model": RequestInfoResponse,
        },
        401: {
            "description": "Unauthorized - invalid or missing token",
        },
        403: {
            "description": "Forbidden - not a platform admin",
        },
        404: {
            "description": "Application not found",
        },
        409: {
            "description": "Application not in valid status for this action",
        },
        422: {
            "description": "Validation error - message too short/long",
        },
    },
)
async def request_more_info(
    application_id: UUID,
    data: RequestInfoRequest,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
) -> RequestInfoResponse:
    """
    Request more information from applicant.
    """
    # Rate limiting: 20 info requests per minute per admin
    await _check_admin_rate_limit(admin, "request_info", *RATE_LIMIT_REQUEST_INFO)

    try:
        application = await service.admin_request_more_info(
            db, application_id, admin.id, data.message
        )

        logger.info(f"Admin {admin.id} requested info for application {application_id}")

        return RequestInfoResponse(
            id=application.id,
            status=application.status,
            message="Information request sent to applicant",
        )

    except ApplicationNotFoundError as e:
        logger.warning(f"Application not found: {application_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except CannotDecideApplicationError as e:
        logger.warning(f"Cannot request info for application {application_id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except ApplicationServiceError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.exception(f"Error requesting more info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        ) from e


@router.post(
    "/{application_id}/notes",
    response_model=AddNoteResponse,
    summary="Add Internal Note",
    description="""
Add an internal note to an application.

Internal notes are visible only to platform administrators and are never
shown to applicants. Useful for recording verification steps, concerns,
or communication with the applicant.

**Requirements:**
- Note must be 1-2000 characters
- Application must exist (any status)

**Effects:**
- Note added to `internal_notes` JSONB array
- Note includes admin ID and timestamp

**Access:** Platform admin only
""",
    responses={
        200: {
            "description": "Note added successfully",
            "model": AddNoteResponse,
        },
        401: {
            "description": "Unauthorized - invalid or missing token",
        },
        403: {
            "description": "Forbidden - not a platform admin",
        },
        404: {
            "description": "Application not found",
        },
        422: {
            "description": "Validation error - note too short/long",
        },
    },
)
async def add_note(
    application_id: UUID,
    data: AddNoteRequest,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
) -> AddNoteResponse:
    """
    Add an internal note to an application.
    """
    # Rate limiting: 30 notes per minute per admin
    await _check_admin_rate_limit(admin, "add_note", *RATE_LIMIT_NOTES)

    try:
        note_dict = await service.admin_add_internal_note(db, application_id, admin.id, data.note)

        logger.info(f"Admin {admin.id} added note to application {application_id}")

        # Convert dict to InternalNote schema
        note = InternalNote(
            note=note_dict["note"],
            created_by=UUID(note_dict["created_by"]),
            created_at=datetime.fromisoformat(note_dict["created_at"].replace("Z", "+00:00")),
        )

        return AddNoteResponse(
            id=application_id,
            note=note,
            message="Note added successfully",
        )

    except ApplicationNotFoundError as e:
        logger.warning(f"Application not found: {application_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except ApplicationServiceError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.exception(f"Error adding note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        ) from e


# ============================================
# Approve Endpoint (Task 8)
# ============================================


@router.post(
    "/{application_id}/approve",
    response_model=ApproveResponse,
    summary="Approve Application and Provision School",
    description="""
Approve an application and provision the school.

This is an atomic operation that:
1. Creates the school tenant record
2. Creates the admin user account with a temporary password
3. Updates application status to `approved`
4. Sends welcome email with login credentials

**Requirements:**
- Application must be in `under_review`, `more_info_requested`, or `pending_review` status

**Effects:**
- New School record created
- New User record created (school admin role)
- Application status set to `approved`
- Welcome email sent with temporary password

**IMPORTANT:** The admin user must change their password and set up 2FA on first login.

**Access:** Platform admin only
""",
    responses={
        200: {
            "description": "Application approved, school and admin created",
            "model": ApproveResponse,
        },
        401: {
            "description": "Unauthorized - invalid or missing token",
        },
        403: {
            "description": "Forbidden - not a platform admin",
        },
        404: {
            "description": "Application not found",
        },
        409: {
            "description": "Application not in valid status for approval",
        },
        500: {
            "description": "School provisioning failed",
        },
    },
)
async def approve_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
) -> ApproveResponse:
    """
    Approve application and provision school.
    """
    # Rate limiting: 10 approvals per minute per admin
    await _check_admin_rate_limit(admin, "approve", *RATE_LIMIT_APPROVE)

    try:
        result = await service.admin_approve_application(db, application_id, admin.id)

        logger.info(
            f"Admin {admin.id} approved application {application_id}. "
            f"School: {result['school_id']}, Admin: {result['admin_user_id']}"
        )

        return ApproveResponse(
            id=result["id"],
            status=ApplicationStatus.APPROVED,
            school_id=result["school_id"],
            admin_user_id=result["admin_user_id"],
            message=result["message"],
        )

    except ApplicationNotFoundError as e:
        logger.warning(f"Application not found: {application_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except CannotDecideApplicationError as e:
        logger.warning(f"Cannot approve application {application_id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except SchoolProvisioningError as e:
        logger.error(f"School provisioning failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except ApplicationServiceError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.exception(f"Error approving application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        ) from e


# ============================================
# Reject Endpoint (Task 9)
# ============================================


@router.post(
    "/{application_id}/reject",
    response_model=RejectResponse,
    summary="Reject Application",
    description="""
Reject an application.

Updates status to `rejected`, records the reason, and sends a notification
email to the applicant explaining why the application was not approved.

**Requirements:**
- Application must be in `under_review`, `more_info_requested`, or `pending_review` status
- Reason must be 20-1000 characters (detailed explanation required)

**Effects:**
- Status changes to `rejected`
- `decision_reason` stores the rejection reason
- Rejection email sent to applicant

**Note:** Rejected schools can reapply after 30 days.

**Access:** Platform admin only
""",
    responses={
        200: {
            "description": "Application rejected",
            "model": RejectResponse,
        },
        401: {
            "description": "Unauthorized - invalid or missing token",
        },
        403: {
            "description": "Forbidden - not a platform admin",
        },
        404: {
            "description": "Application not found",
        },
        409: {
            "description": "Application not in valid status for rejection",
        },
        422: {
            "description": "Validation error - reason too short/long",
        },
    },
)
async def reject_application(
    application_id: UUID,
    data: RejectRequest,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
) -> RejectResponse:
    """
    Reject an application.
    """
    # Rate limiting: 10 rejections per minute per admin
    await _check_admin_rate_limit(admin, "reject", *RATE_LIMIT_REJECT)

    try:
        application = await service.admin_reject_application(
            db, application_id, admin.id, data.reason
        )

        logger.info(f"Admin {admin.id} rejected application {application_id}")

        return RejectResponse(
            id=application.id,
            status=application.status,
            message="Application rejected. Notification sent to applicant.",
        )

    except ApplicationNotFoundError as e:
        logger.warning(f"Application not found: {application_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except CannotDecideApplicationError as e:
        logger.warning(f"Cannot reject application {application_id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except ApplicationServiceError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.exception(f"Error rejecting application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        ) from e
