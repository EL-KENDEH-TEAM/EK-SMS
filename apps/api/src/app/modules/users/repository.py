"""
User Repository

Database operations for user management.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User, UserRole

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user database operations."""

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        role: UserRole,
        school_id: str | None = None,
        phone: str | None = None,
        is_active: bool = True,
        is_verified: bool = False,
        must_change_password: bool = False,
    ) -> User:
        """
        Create a new user record.

        Args:
            db: Database session
            email: User's email address (unique)
            password_hash: Hashed password
            first_name: User's first name
            last_name: User's last name
            role: User's role
            school_id: School ID (required for non-platform_admin roles)
            phone: Phone number (optional)
            is_active: Whether user is active
            is_verified: Whether email is verified
            must_change_password: Whether user must change password on next login

        Returns:
            Created User instance
        """
        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=role,
            school_id=school_id,
            phone=phone,
            is_active=is_active,
            is_verified=is_verified,
            must_change_password=must_change_password,
        )

        db.add(user)
        await db.flush()
        await db.refresh(user)

        logger.info(f"Created user: {user.id} - {user.email} ({user.role.value})")
        return user

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str | UUID) -> User | None:
        """
        Get a user by ID.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            User instance or None if not found
        """
        user_id_str = str(user_id)
        result = await db.execute(select(User).where(User.id == user_id_str))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        """
        Get a user by email address.

        Args:
            db: Database session
            email: Email address

        Returns:
            User instance or None if not found
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def email_exists(db: AsyncSession, email: str) -> bool:
        """
        Check if an email address is already registered.

        Args:
            db: Database session
            email: Email address to check

        Returns:
            True if email exists, False otherwise
        """
        user = await UserRepository.get_by_email(db, email)
        return user is not None
