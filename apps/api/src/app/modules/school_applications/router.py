"""
School Applications Router

API endpoints for the school registration flow.
These endpoints are public (no authentication required) since they
are used before any school or user account exists.

Endpoints:
- POST /school-applications - Submit a new registration application
- POST /school-applications/verify-applicant - Verify applicant email
- POST /school-applications/confirm-principal - Principal confirms application
- GET /school-applications/countries - List supported countries

Security:
- Rate limiting should be applied at infrastructure level
- Input validation via Pydantic schemas
- XSS prevention in email templates
- CSRF protection not needed (stateless API)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.school_applications import service
from app.modules.school_applications.schemas import (
    ConfirmPrincipalRequest,
    ConfirmPrincipalResponse,
    Country,
    CountryListResponse,
    SchoolApplicationCreate,
    SchoolApplicationResponse,
    VerifyApplicationRequest,
    VerifyApplicationResponse,
)
from app.modules.school_applications.service import (
    ApplicationServiceError,
    DuplicateApplicationError,
    InvalidApplicationStateError,
    InvalidTokenError,
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
