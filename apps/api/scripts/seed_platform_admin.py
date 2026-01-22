"""
Seed Platform Admin User

Creates the initial platform admin user for the EK-SMS system.
Run this script once to set up the admin account.

Usage:
    cd apps/api
    python scripts/seed_platform_admin.py
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.modules.schools.models import School  # noqa: F401 - needed for relationship resolution
from app.modules.users.models import User, UserRole


async def seed_platform_admin() -> None:
    """Create the platform admin user if it doesn't exist."""

    # Platform admin credentials
    email = "mansaraysaheedalpha@gmail.com"
    password = "Xfinity06@#$"
    first_name = "Saheed Alpha"
    last_name = "Mansaray"

    # Create async engine and session
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"Platform admin already exists: {email}")
            print(f"  ID: {existing_user.id}")
            print(f"  Role: {existing_user.role.value}")
            return

        # Create the platform admin user
        admin_user = User(
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=UserRole.PLATFORM_ADMIN,
            school_id=None,  # Platform admins have no school
            is_active=True,
            is_verified=True,  # Pre-verified
            must_change_password=False,
        )

        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)

        print("Platform admin created successfully!")
        print(f"  Email: {email}")
        print(f"  Name: {first_name} {last_name}")
        print(f"  ID: {admin_user.id}")
        print(f"  Role: {admin_user.role.value}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_platform_admin())
