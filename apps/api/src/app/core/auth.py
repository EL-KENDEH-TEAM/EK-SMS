"""
Authentication and Authorization Module

Provides authentication dependencies for FastAPI endpoints.
This module handles JWT token validation and role-based access control.

Current Status: DEVELOPMENT PLACEHOLDER
---
This is a development-only placeholder that provides mock authentication.
It MUST be replaced with actual JWT validation before production deployment.

Production Implementation TODO:
1. JWT token validation using jose or python-jwt
2. Token refresh mechanism
3. Role-based access control (RBAC)
4. Session management with Redis
5. Rate limiting per user
6. Audit logging for security events

Security Considerations:
- Never log tokens or passwords
- Use constant-time comparison for token validation
- Implement token expiration and refresh
- Use HTTPS only in production
- Implement CSRF protection for cookie-based auth
"""

import logging
import os
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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

    In production, this would be populated from the JWT claims and
    validated against the database.

    Attributes:
        id: User's unique identifier (UUID)
        email: User's email address
        role: User's role (must be 'platform_admin' for admin endpoints)
        name: User's display name (optional)
    """

    id: UUID
    email: str
    role: str
    name: str | None = None

    def __str__(self) -> str:
        return f"AdminUser(id={self.id}, email={self.email}, role={self.role})"


# Development mode flag
# In production, this should be False and actual JWT validation should be used
_DEVELOPMENT_MODE = os.getenv("PYTHON_ENV", "development") == "development"

# Development admin user for testing
# This is ONLY used when PYTHON_ENV=development
_DEV_ADMIN = AdminUser(
    id=UUID("00000000-0000-0000-0000-000000000001"),
    email="admin@eksms.dev",
    role="platform_admin",
    name="Development Admin",
)


async def _validate_jwt_token(token: str) -> AdminUser:
    """
    Validate JWT token and extract user claims.

    TODO: Replace with actual JWT validation in production.

    Args:
        token: JWT token string from Authorization header

    Returns:
        AdminUser object with claims from the token

    Raises:
        HTTPException 401: If token is invalid or expired
        HTTPException 403: If user doesn't have required role
    """
    # PRODUCTION TODO: Implement actual JWT validation
    # Example implementation:
    # try:
    #     payload = jwt.decode(
    #         token,
    #         settings.JWT_SECRET,
    #         algorithms=["HS256"],
    #     )
    #     user_id = UUID(payload["sub"])
    #     email = payload["email"]
    #     role = payload["role"]
    #     exp = payload["exp"]
    #
    #     # Check expiration
    #     if datetime.now(UTC) > datetime.fromtimestamp(exp, UTC):
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail={"error": "TOKEN_EXPIRED", "message": "Token has expired"},
    #         )
    #
    #     return AdminUser(id=user_id, email=email, role=role)
    # except jwt.InvalidTokenError as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail={"error": "INVALID_TOKEN", "message": str(e)},
    #     )

    # Development mode: Accept any token and return dev admin
    if _DEVELOPMENT_MODE:
        logger.warning(
            "DEVELOPMENT MODE: Using mock authentication. "
            "Replace with actual JWT validation before production!"
        )
        # For development, accept specific test tokens
        if token in ["dev-token", "test-token", "bearer"]:
            return _DEV_ADMIN

        # Also accept any token that looks like a UUID (for testing)
        try:
            # If token is a valid UUID, treat it as a user ID
            user_id = UUID(token)
            return AdminUser(
                id=user_id,
                email=f"admin-{str(user_id)[:8]}@eksms.dev",
                role="platform_admin",
                name="Test Admin",
            )
        except ValueError:
            pass

        # For any other token in dev mode, return the default dev admin
        # This makes testing easier
        return _DEV_ADMIN

    # Production mode: Reject all tokens (not implemented)
    logger.error("JWT validation not implemented for production!")
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "AUTH_NOT_IMPLEMENTED",
            "message": "Authentication is not yet implemented for production.",
        },
    )


async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AdminUser:
    """
    FastAPI dependency that validates the JWT token and returns the admin user.

    This dependency should be used on all admin endpoints to ensure
    the request is from an authenticated platform admin.

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

    # Verify user has platform_admin role
    if user.role != "platform_admin":
        logger.warning(
            f"Access denied: User {user.id} ({user.email}) has role '{user.role}', "
            "but 'platform_admin' is required"
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


# Export for use in admin_router.py
__all__ = [
    "AdminUser",
    "get_current_admin_user",
    "get_optional_admin_user",
]
