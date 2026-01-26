"""
School Applications Router

API endpoints for the school registration flow.
These endpoints are public (no authentication required) since they
are used before any school or user account exists.

Endpoints:
- POST /school-applications - Submit a new registration application
- POST /school-applications/verify-applicant - Verify applicant email
- POST /school-applications/confirm-principal - Principal confirms application
- POST /school-applications/resend-verification - Resend verification email
- GET /school-applications/{id}/status - Get application status
- GET /school-applications/countries - List supported countries

Security:
- Rate limiting applied via Redis for resend-verification endpoint
- Email validation prevents unauthorized status access
- Input validation via Pydantic schemas
- XSS prevention in email templates
- CSRF protection not needed (stateless API)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.modules.school_applications import service
from app.modules.school_applications.schemas import (
    ApplicationStatusResponse,
    ConfirmPrincipalRequest,
    ConfirmPrincipalResponse,
    Country,
    CountryListResponse,
    PrincipalViewResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    SchoolApplicationCreate,
    SchoolApplicationResponse,
    VerifyApplicationRequest,
    VerifyApplicationResponse,
)
from app.modules.school_applications.service import (
    AlreadyVerifiedError,
    ApplicationNotFoundError,
    ApplicationServiceError,
    DuplicateApplicationError,
    InvalidApplicationStateError,
    InvalidEmailError,
    InvalidTokenError,
    RateLimitExceededError,
    TokenAlreadyUsedError,
    TokenExpiredError,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Targeting West Africa Countries for MVP
SUPPORTED_COUNTRIES = [
    Country(code="LR", name="Liberia"),
    Country(code="SL", name="Sierra Leone"),
    Country(code="GN", name="Guinea"),
    Country(code="GH", name="Ghana"),
    Country(code="CI", name="Côte d'Ivoire"),
    Country(code="NG", name="Nigeria"),
    Country(code="SN", name="Senegal"),
    Country(code="GM", name="Gambia"),
]

# Country code to name mapping for quick lookups
COUNTRY_CODE_TO_NAME = {country.code: country.name for country in SUPPORTED_COUNTRIES}


def get_country_name(country_code: str) -> str:
    """Get country name from country code."""
    return COUNTRY_CODE_TO_NAME.get(country_code, country_code)


@router.post(
    "",
    response_model=SchoolApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit School Registration Application",
    description="""
Submit a new school registration application.

This endpoint initiates the school registration process. After submission:
1. A verification email is sent to the applicant
2. The applicant must verify their email within 72 hours
3. If the applicant is not the principal, the principal must also confirm
4. Once verified, the application enters the admin review queue

**Duplicate Prevention:**
- Only one pending application allowed per applicant email + school name
- Only one pending application allowed per school name + city combination

**Response:**
Returns the application ID and status. The applicant should check their
email for the verification link.
""",
    responses={
        201: {
            "description": "Application created successfully",
            "model": SchoolApplicationResponse,
        },
        400: {
            "description": "Validation error - invalid input data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "At least one of school_phone or school_email is required"
                    }
                }
            },
        },
        409: {
            "description": "Duplicate application detected",
            "content": {
                "application/json": {
                    "example": {
                        "error": "DUPLICATE_APPLICATION",
                        "message": "You already have a pending application for Example School.",
                    }
                }
            },
        },
        422: {
            "description": "Validation error - request body format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "school", "name"],
                                "msg": "field required",
                                "type": "value_error.missing",
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def submit_application(
    data: SchoolApplicationCreate,
    db: AsyncSession = Depends(get_db),
) -> SchoolApplicationResponse:
    """
    Submit a new school registration application.

    Creates an application record and sends a verification email to the applicant.
    The applicant must verify their email within 72 hours to proceed.

    Args:
        data: Application data including school info, location, contacts, and details
        db: Database session (injected)

    Returns:
        Application ID, status, and verification expiration time

    Raises:
        HTTPException 409: If a duplicate application exists
        HTTPException 400: If validation fails
    """
    # Validate country code is in supported list
    if data.location.country_code not in COUNTRY_CODE_TO_NAME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_COUNTRY",
                "message": f"Country code '{data.location.country_code}' is not supported. "
                f"Supported countries: {', '.join(COUNTRY_CODE_TO_NAME.keys())}",
            },
        )

    try:
        response = await service.submit_application(db, data)

        logger.info(
            f"Application submitted successfully: id={response.id}, school={data.school.name}"
        )

        return response

    except DuplicateApplicationError as e:
        logger.warning(f"Duplicate application rejected: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except ApplicationServiceError as e:
        logger.error(f"Application service error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except HTTPException:
        # Re-raise HTTPExceptions without wrapping
        raise
    except Exception as e:
        logger.exception(f"Unexpected error submitting application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            },
        ) from e


@router.get(
    "/countries",
    response_model=CountryListResponse,
    summary="List Supported Countries",
    description="""
Get the list of countries supported for school registration.

Currently targeting West African countries for MVP:
- Liberia, Sierra Leone, Guinea, Ghana
- Côte d'Ivoire, Nigeria, Senegal, Gambia

Returns ISO 3166-1 alpha-2 country codes and full names.
""",
    responses={
        200: {
            "description": "List of supported countries",
            "model": CountryListResponse,
        },
    },
)
async def list_countries() -> CountryListResponse:
    """
    Get list of supported countries for school registration.

    Returns:
        List of Country objects with code and name
    """
    return CountryListResponse(countries=SUPPORTED_COUNTRIES)


@router.post(
    "/verify-applicant",
    response_model=VerifyApplicationResponse,
    summary="Verify Applicant Email",
    description="""
Verify the applicant's email using the token from the verification email.

**Scenarios:**
1. If applicant IS the principal: Application moves directly to review queue
2. If applicant is NOT the principal: A confirmation email is sent to the principal

**Token Requirements:**
- Must be a valid, unused token
- Must not be expired (72 hours from creation)
- Must be of type APPLICANT_VERIFICATION
""",
    responses={
        200: {
            "description": "Email verified successfully",
            "model": VerifyApplicationResponse,
        },
        400: {
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {
                        "error": "TOKEN_EXPIRED",
                        "message": "This verification link has expired. Please request a new one.",
                    }
                }
            },
        },
        404: {
            "description": "Application not found",
        },
        409: {
            "description": "Already verified or token already used",
            "content": {
                "application/json": {
                    "example": {
                        "error": "TOKEN_ALREADY_USED",
                        "message": "This verification link has already been used.",
                    }
                }
            },
        },
    },
)
async def verify_applicant(
    data: VerifyApplicationRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyApplicationResponse:
    """
    Verify applicant email address.

    Uses the token from the verification email to confirm the applicant's email.
    If the applicant is the principal, moves to review. Otherwise, sends
    confirmation email to the principal.

    Args:
        data: Request containing the verification token
        db: Database session (injected)

    Returns:
        Verification result with next steps
    """
    try:
        response = await service.verify_applicant(
            db=db,
            token_string=data.token,
            country_name_lookup=COUNTRY_CODE_TO_NAME,
        )

        logger.info(f"Applicant verified for application {response.id}")

        return response

    except (InvalidTokenError, TokenExpiredError) as e:
        logger.warning(f"Token validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except TokenAlreadyUsedError as e:
        logger.warning(f"Token already used: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except InvalidApplicationStateError as e:
        logger.warning(f"Invalid application state: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except ApplicationServiceError as e:
        logger.error(f"Application service error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error verifying applicant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            },
        ) from e


@router.get(
    "/principal-view",
    response_model=PrincipalViewResponse,
    summary="Get Application Details for Principal",
    description="""
Get application summary for principal to review before confirming.

This endpoint is called when the principal clicks the confirmation link in their email.
It returns the application details so the principal can review before confirming.

**Token Requirements:**
- Must be a valid, unused token
- Must not be expired (72 hours from creation)
- Must be of type PRINCIPAL_CONFIRMATION
- Application must be in AWAITING_PRINCIPAL_CONFIRMATION state

**Note:** This endpoint does NOT mark the token as used. The token is only
marked as used when the principal confirms via POST /confirm-principal.
""",
    responses={
        200: {
            "description": "Application details retrieved successfully",
            "model": PrincipalViewResponse,
        },
        400: {
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {
                        "error": "TOKEN_EXPIRED",
                        "message": "This verification link has expired. Please request a new one.",
                    }
                }
            },
        },
        404: {
            "description": "Application not found",
        },
        409: {
            "description": "Token already used or application not in correct state",
            "content": {
                "application/json": {
                    "example": {
                        "error": "INVALID_APPLICATION_STATE",
                        "message": "This application is not awaiting principal confirmation.",
                    }
                }
            },
        },
    },
)
async def get_principal_view(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> PrincipalViewResponse:
    """
    Get application details for principal to review.

    Returns a summary of the application so the principal can review
    before confirming. Does not mark the token as used.

    Args:
        token: The confirmation token from the email
        db: Database session (injected)

    Returns:
        Application summary with school name, applicant name, and admin choice
    """
    try:
        response = await service.get_principal_view(
            db=db,
            token_string=token,
        )

        logger.info(f"Principal view retrieved for application {response.id}")

        return response

    except (InvalidTokenError, TokenExpiredError) as e:
        logger.warning(f"Token validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except TokenAlreadyUsedError as e:
        logger.warning(f"Token already used: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except InvalidApplicationStateError as e:
        logger.warning(f"Invalid application state: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except ApplicationServiceError as e:
        logger.error(f"Application service error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error getting principal view: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            },
        ) from e


@router.post(
    "/confirm-principal",
    response_model=ConfirmPrincipalResponse,
    summary="Principal Confirmation",
    description="""
Principal confirms the application using the token from their confirmation email.

This endpoint is only called when the applicant is different from the principal.
After confirmation, the application moves to the review queue.

**Token Requirements:**
- Must be a valid, unused token
- Must not be expired (72 hours from creation)
- Must be of type PRINCIPAL_CONFIRMATION
- Application must be in AWAITING_PRINCIPAL_CONFIRMATION state
""",
    responses={
        200: {
            "description": "Application confirmed, moved to review queue",
            "model": ConfirmPrincipalResponse,
        },
        400: {
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {
                        "error": "TOKEN_EXPIRED",
                        "message": "This verification link has expired. Please request a new one.",
                    }
                }
            },
        },
        404: {
            "description": "Application not found",
        },
        409: {
            "description": "Already confirmed or application not in correct state",
            "content": {
                "application/json": {
                    "example": {
                        "error": "INVALID_APPLICATION_STATE",
                        "message": "This application is not awaiting principal confirmation.",
                    }
                }
            },
        },
    },
)
async def confirm_principal(
    data: ConfirmPrincipalRequest,
    db: AsyncSession = Depends(get_db),
) -> ConfirmPrincipalResponse:
    """
    Principal confirms the application.

    Uses the token from the confirmation email to confirm the application.
    Moves the application to the review queue.

    Args:
        data: Request containing the confirmation token
        db: Database session (injected)

    Returns:
        Confirmation result with application details
    """
    try:
        response = await service.confirm_principal(
            db=db,
            token_string=data.token,
        )

        logger.info(f"Principal confirmed application {response.id}")

        return response

    except (InvalidTokenError, TokenExpiredError) as e:
        logger.warning(f"Token validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except TokenAlreadyUsedError as e:
        logger.warning(f"Token already used: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except InvalidApplicationStateError as e:
        logger.warning(f"Invalid application state: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except ApplicationServiceError as e:
        logger.error(f"Application service error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error confirming principal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            },
        ) from e


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    summary="Resend Verification Email",
    description="""
Resend the verification email for an application.

**Use Cases:**
- Applicant didn't receive the original verification email
- Verification link expired and applicant needs a new one
- Email was sent to spam folder and user wants to try again

**Security:**
- Email must match the application's applicant email
- Rate limited to 3 requests per hour per application
- Only works for applications awaiting verification

**Rate Limiting:**
Returns 429 Too Many Requests if limit exceeded, with Retry-After header.
""",
    responses={
        200: {
            "description": "Verification email resent successfully",
            "model": ResendVerificationResponse,
        },
        403: {
            "description": "Email does not match application",
            "content": {
                "application/json": {
                    "example": {
                        "error": "INVALID_EMAIL",
                        "message": "Email does not match the application",
                    }
                }
            },
        },
        404: {
            "description": "Application not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "APPLICATION_NOT_FOUND",
                        "message": "Application not found",
                    }
                }
            },
        },
        409: {
            "description": "Application already verified",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ALREADY_VERIFIED",
                        "message": "This application has already been verified",
                    }
                }
            },
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many resend requests. Please try again in 45 minute(s).",
                    }
                }
            },
        },
    },
)
async def resend_verification(
    data: ResendVerificationRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ResendVerificationResponse:
    """
    Resend verification email for an application.

    Creates a new verification token, invalidates the old one, and sends
    a fresh verification email.

    Args:
        data: Request containing application_id and email
        response: FastAPI response object for headers
        db: Database session (injected)
        redis: Redis client for rate limiting (injected)

    Returns:
        Success message with new token expiration time
    """
    try:
        result = await service.resend_verification(
            db=db,
            application_id=data.application_id,
            email=data.email,
            redis_client=redis,
        )

        logger.info(f"Resent verification for application {data.application_id}")

        return result

    except ApplicationNotFoundError as e:
        logger.warning(f"Application not found for resend: {data.application_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except InvalidEmailError as e:
        logger.warning(f"Invalid email for resend: {data.application_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except AlreadyVerifiedError as e:
        logger.warning(f"Already verified for resend: {data.application_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except RateLimitExceededError as e:
        logger.warning(f"Rate limit exceeded for resend: {data.application_id}")
        response.headers["Retry-After"] = str(e.retry_after_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
            headers={"Retry-After": str(e.retry_after_seconds)},
        ) from e
    except ApplicationServiceError as e:
        logger.error(f"Application service error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error resending verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            },
        ) from e


@router.get(
    "/{application_id}/status",
    response_model=ApplicationStatusResponse,
    summary="Get Application Status",
    description="""
Get the current status of a school registration application.

**Security:**
The email query parameter is required and must match the applicant's email.
This prevents unauthorized access to application status.

**Response:**
Returns detailed status information including:
- Current status and human-readable label
- Description of what to expect next
- Progress steps showing verification journey
- Timestamps for completed steps
""",
    responses={
        200: {
            "description": "Application status retrieved successfully",
            "model": ApplicationStatusResponse,
        },
        403: {
            "description": "Email does not match application",
            "content": {
                "application/json": {
                    "example": {
                        "error": "INVALID_EMAIL",
                        "message": "Email does not match the application",
                    }
                }
            },
        },
        404: {
            "description": "Application not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "APPLICATION_NOT_FOUND",
                        "message": "Application not found",
                    }
                }
            },
        },
    },
)
async def get_application_status(
    application_id: UUID,
    email: str,
    db: AsyncSession = Depends(get_db),
) -> ApplicationStatusResponse:
    """
    Get the current status of an application.

    Provides a detailed view of the application status including
    progress steps and what to expect next.

    Args:
        application_id: UUID of the application
        email: Email address (must match applicant email for security)
        db: Database session (injected)

    Returns:
        Detailed application status with progress steps
    """
    try:
        result = await service.get_application_status(
            db=db,
            application_id=application_id,
            email=email,
        )

        logger.info(f"Retrieved status for application {application_id}")

        return result

    except ApplicationNotFoundError as e:
        logger.warning(f"Application not found for status: {application_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except InvalidEmailError as e:
        logger.warning(f"Invalid email for status check: {application_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except ApplicationServiceError as e:
        logger.error(f"Application service error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
            },
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error getting application status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            },
        ) from e
