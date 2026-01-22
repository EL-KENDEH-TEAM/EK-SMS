"""Authentication router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.modules.auth.schemas import LoginRequest, LoginResponse, UserResponse
from app.modules.users.repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate user and return JWT tokens.

    Args:
        credentials: Email and password
        db: Database session

    Returns:
        Access token, refresh token, and user info

    Raises:
        HTTPException 401: Invalid credentials
        HTTPException 403: Account inactive or unverified
    """
    # Find user by email
    user = await UserRepository.get_by_email(db, credentials.email)

    if not user:
        logger.warning(f"Login attempt for non-existent email: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_CREDENTIALS",
                "message": "Invalid email or password.",
            },
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Invalid password for user: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_CREDENTIALS",
                "message": "Invalid email or password.",
            },
        )

    # Check if account is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive account: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "ACCOUNT_INACTIVE",
                "message": "Your account has been deactivated.",
            },
        )

    # Create tokens with additional claims
    additional_claims = {
        "email": user.email,
        "role": user.role.value,
        "name": f"{user.first_name} {user.last_name}",
    }

    access_token = create_access_token(
        subject=str(user.id),
        additional_claims=additional_claims,
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info(f"User logged in: {user.email} (role: {user.role.value})")

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_two_factor_enabled=user.is_two_factor_enabled,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
        ),
    )
