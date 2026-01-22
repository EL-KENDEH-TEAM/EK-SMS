"""Add missing indexes to school_applications table

Revision ID: f3g4h5i6j7k8
Revises: e2f3g4h5i6j7
Create Date: 2026-01-21

This migration adds performance-critical indexes for the admin dashboard:
- country_code: For filtering applications by country
- submitted_at: For sorting applications (oldest first)
- school_email: For search functionality
- status + submitted_at: Composite index for filtered and sorted queries
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f3g4h5i6j7k8"
down_revision = "e2f3g4h5i6j7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add index on country_code for filtering
    op.create_index(
        "ix_school_applications_country_code",
        "school_applications",
        ["country_code"],
        unique=False,
    )

    # Add index on submitted_at for sorting
    op.create_index(
        "ix_school_applications_submitted_at",
        "school_applications",
        ["submitted_at"],
        unique=False,
    )

    # Add index on school_email for searching
    op.create_index(
        "ix_school_applications_school_email",
        "school_applications",
        ["school_email"],
        unique=False,
    )

    # Add composite index for status + submitted_at (common query pattern)
    op.create_index(
        "ix_school_applications_status_submitted",
        "school_applications",
        ["status", "submitted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_school_applications_status_submitted", table_name="school_applications")
    op.drop_index("ix_school_applications_school_email", table_name="school_applications")
    op.drop_index("ix_school_applications_submitted_at", table_name="school_applications")
    op.drop_index("ix_school_applications_country_code", table_name="school_applications")
