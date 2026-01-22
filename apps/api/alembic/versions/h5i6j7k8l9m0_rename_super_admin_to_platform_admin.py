"""Rename super_admin to platform_admin in user_role enum

Revision ID: h5i6j7k8l9m0
Revises: g4h5i6j7k8l9
Create Date: 2026-01-22

This migration renames the 'super_admin' enum value to 'platform_admin'
to match the specification requirements for the Admin Review Dashboard.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "h5i6j7k8l9m0"
down_revision = "g4h5i6j7k8l9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the enum value from 'SUPER_ADMIN' to 'PLATFORM_ADMIN'
    # PostgreSQL requires ALTER TYPE to rename enum values
    # Note: The database stores enum labels in uppercase
    op.execute("ALTER TYPE user_role RENAME VALUE 'SUPER_ADMIN' TO 'PLATFORM_ADMIN'")


def downgrade() -> None:
    # Revert: rename 'PLATFORM_ADMIN' back to 'SUPER_ADMIN'
    op.execute("ALTER TYPE user_role RENAME VALUE 'PLATFORM_ADMIN' TO 'SUPER_ADMIN'")
