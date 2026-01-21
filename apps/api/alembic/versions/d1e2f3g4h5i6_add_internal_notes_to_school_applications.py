"""add internal_notes to school_applications

Revision ID: d1e2f3g4h5i6
Revises: c1d2e3f4g5h6
Create Date: 2026-01-21 10:00:00.000000

This migration adds the internal_notes JSONB column to the school_applications table.
The column stores an array of admin notes, where each note contains:
- note: str (the note content)
- created_by: UUID (admin who created the note)
- created_at: datetime (when the note was created)

The column is nullable and defaults to NULL (not an empty array) to save space
for applications that never receive notes.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d1e2f3g4h5i6"
down_revision: str | Sequence[str] | None = "c1d2e3f4g5h6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add internal_notes JSONB column to school_applications table.

    The column stores admin-only notes as a JSON array. Each note object contains:
    - note: string content of the note
    - created_by: UUID of the admin who created the note
    - created_at: ISO 8601 timestamp of when the note was created

    Example structure:
    [
        {
            "note": "Application looks complete. All docs verified.",
            "created_by": "550e8400-e29b-41d4-a716-446655440000",
            "created_at": "2026-01-14T12:30:00Z"
        }
    ]
    """
    op.add_column(
        "school_applications",
        sa.Column(
            "internal_notes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Admin-only internal notes stored as JSON array",
        ),
    )

    # Add a GIN index on internal_notes for efficient JSONB queries
    # This allows fast searching within the notes if needed in the future
    op.create_index(
        "ix_school_applications_internal_notes_gin",
        "school_applications",
        ["internal_notes"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Remove internal_notes column from school_applications table."""
    # Drop the GIN index first
    op.drop_index(
        "ix_school_applications_internal_notes_gin",
        table_name="school_applications",
    )

    # Drop the column
    op.drop_column("school_applications", "internal_notes")
