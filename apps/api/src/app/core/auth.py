"""
Authentication and Authorization Module

Provides authentication dependencies for FastAPI endpoints.
This module handles JWT token validation and role-based access control
using the security utilities defined in security.py.

SECURITY NOTE:
- Development mode auth bypass is ONLY enabled when PYTHON_ENV=development
- Production environments MUST set PYTHON_ENV=production to disable test tokens
- The is_production check provides an additional safety layer
"""

import logging
import os
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.security import decode_token

logger = logging.getLogger(__name__)

# Security scheme for OpenAPI documentation
security = HTTPBearer(
    auto_error=True,
    description="JWT Bearer token for authentication",
)


@dataclass
class AdminUser:
    """
    Represents an authenticated platform admin user.

    Populated from JWT claims after token validation.

    Attributes:
        id: User's unique identifier (UUID)
        email: User's email address
        role: User's role (must be 'super_admin' for platform admin endpoints)
        name: User's display name (optional)
    """

    id: UUID
    email: str
    role: str
    name: str | None = None

    def __str__(self) -> str:
        return f"AdminUser(id={self.id}, email={self.email}, role={self.role})"


def _is_dev_mode_safe() -> bool:
    """
    Check if development mode is safe to enable.

    SECURITY: This function has multiple layers of protection to prevent
    development auth bypass from being enabled in production:

    1. settings.is_development must be True (PYTHON_ENV=development)
    2. settings.is_production must be False (double-check)
    3. PYTHON_ENV environment variable must not be "production" (triple-check)

    Returns:
        True only if ALL safety checks pass
    """
    env_var = os.getenv("PYTHON_ENV", "").lower()

    # Triple-check: must be development AND not production
    is_safe = (
        settings.is_development
        and not settings.is_production
        and env_var != "production"
        and env_var != "staging"
    )

    if is_safe:
        logger.warning(
            "SECURITY: Development auth mode is ENABLED. This MUST NOT be used in production!"
        )

    return is_safe


# Development mode flag - allows mock authentication for LOCAL testing ONLY
# SECURITY: Multiple checks prevent this from being enabled in production
_DEVELOPMENT_MODE = _is_dev_mode_safe()

# Development admin user for testing (only used when PYTHON_ENV=development)
_DEV_ADMIN = AdminUser(
    id=UUID("00000000-0000-0000-0000-000000000001"),
    email="admin@eksms.dev",
    role="super_admin",
    name="Development Admin",
)


async def _validate_jwt_token(token: str) -> AdminUser:
    """
    Validate JWT token and extract user claims.

    Uses the decode_token function from security.py which handles
    JWT signature verification, algorithm validation, and expiration checks.

    Args:
        token: JWT token string from Authorization header

    Returns:
        AdminUser object with claims from the token

    Raises:
        HTTPException 401: If token is invalid or expired
    """
    # In development mode, accept test tokens for easier local testing
    if _DEVELOPMENT_MODE:
        # Accept specific test tokens
        if token in ["dev-token", "test-token", "bearer"]:
            logger.debug("Development mode: Using test token")
            return _DEV_ADMIN

        # Accept UUID tokens as user IDs for testing
        try:
            user_id = UUID(token)
            return AdminUser(
                id=user_id,
                email=f"admin-{str(user_id)[:8]}@eksms.dev",
                role="super_admin",
                name="Test Admin",
            )
        except ValueError:
            pass

    # Decode and validate the JWT token using security.py
    payload = decode_token(token)

    if payload is None:
        logger.warning("Invalid or expired JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_TOKEN",
                "message": "Invalid or expired authentication token.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract required claims from token payload
    try:
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Missing 'sub' claim in token")

        user_id = UUID(user_id_str)
        email = payload.get("email", "")
        role = payload.get("role", "")
        name = payload.get("name")

        # Verify token type is access token
        token_type = payload.get("type", "access")
        if token_type != "access":
            logger.warning(f"Invalid token type: {token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "INVALID_TOKEN_TYPE",
                    "message": "This endpoint requires an access token.",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        return AdminUser(
            id=user_id,
            email=email,
            role=role,
            name=name,
        )

    except (ValueError, KeyError) as e:
        logger.warning(f"Invalid token claims: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_TOKEN_CLAIMS",
                "message": "Token contains invalid or missing claims.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AdminUser:
    """
    FastAPI dependency that validates the JWT token and returns the admin user.

    This dependency should be used on all admin endpoints to ensure
    the request is from an authenticated platform admin (super_admin role).

    Usage:
        @router.get("/admin/endpoint")
        async def admin_endpoint(
            admin: AdminUser = Depends(get_current_admin_user)
        ):
            # admin.id, admin.email, admin.role are available

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        AdminUser object representing the authenticated admin

    Raises:
        HTTPException 401: If token is missing, invalid, or expired
        HTTPException 403: If user is not a platform admin
    """
    token = credentials.credentials

    # Validate token and get user
    user = await _validate_jwt_token(token)

    # Verify user has super_admin role (platform admin)
    if user.role != "super_admin":
        logger.warning(
            f"Access denied: User {user.id} ({user.email}) has role '{user.role}', "
            "but 'super_admin' is required"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "ADMIN_ACCESS_REQUIRED",
                "message": "Platform admin access is required for this endpoint.",
            },
        )

    logger.debug(f"Authenticated admin: {user.id} ({user.email})")
    return user


async def get_optional_admin_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> AdminUser | None:
    """
    Optional authentication dependency.

    Returns the admin user if a valid token is provided, or None if no token.
    Useful for endpoints that have different behavior for authenticated vs
    unauthenticated requests.

    Args:
        credentials: Optional HTTP Bearer token

    Returns:
        AdminUser if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_admin_user(credentials)
    except HTTPException:
        return None


__all__ = [
    "AdminUser",
    "get_current_admin_user",
    "get_optional_admin_user",
]
