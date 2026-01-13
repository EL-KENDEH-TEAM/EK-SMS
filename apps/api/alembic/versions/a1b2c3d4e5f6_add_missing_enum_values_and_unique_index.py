"""add missing enum values and unique partial index for race condition prevention

Revision ID: a1b2c3d4e5f6
Revises: 8f70c12efe02
Create Date: 2026-01-13 12:00:00.000000

This migration addresses two critical issues:
1. Adds missing UNDER_REVIEW and MORE_INFO_REQUESTED values to application_status enum
2. Creates a unique partial index to prevent race conditions on duplicate submissions

The unique partial index ensures that only one pending application can exist for
a given (school_name, city) combination, preventing concurrent submissions from
creating duplicates.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "8f70c12efe02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing enum values and unique partial index."""
    # Add missing enum values to application_status
    # PostgreSQL requires ALTER TYPE to add new values
    op.execute("ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'UNDER_REVIEW'")
    op.execute("ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'MORE_INFO_REQUESTED'")

    # Create unique partial index to prevent race conditions on duplicate applications
    # This ensures only one pending application can exist for a school name + city combination
    # The LOWER() functions make the comparison case-insensitive
    op.execute(
        """
        CREATE UNIQUE INDEX ix_school_applications_unique_pending
        ON school_applications (LOWER(school_name), LOWER(city))
        WHERE status NOT IN ('APPROVED', 'REJECTED', 'EXPIRED')
        """
    )

    # Add composite index on (application_id, token_type) for efficient token lookups
    # This optimizes the get_valid_token_for_application query
    op.create_index(
        "ix_verification_tokens_app_type",
        "verification_tokens",
        ["application_id", "token_type"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the unique partial index and composite index.

    Note: PostgreSQL does not support removing enum values, so those changes
    are not reverted. The enum values will remain but be unused.
    """
    op.drop_index("ix_verification_tokens_app_type", table_name="verification_tokens")
    op.drop_index("ix_school_applications_unique_pending", table_name="school_applications")
