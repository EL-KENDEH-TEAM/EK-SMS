"""remove users FK from school_applications

Revision ID: c1d2e3f4g5h6
Revises: a1b2c3d4e5f6
Create Date: 2026-01-16 22:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4g5h6"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove FK constraint to users table (users table not yet implemented)."""
    # Drop the FK constraint if it exists
    # Using batch mode for SQLite compatibility, works with PostgreSQL too
    with op.batch_alter_table("school_applications") as batch_op:
        batch_op.drop_constraint("school_applications_reviewed_by_fkey", type_="foreignkey")


def downgrade() -> None:
    """Re-add FK constraint to users table."""
    with op.batch_alter_table("school_applications") as batch_op:
        batch_op.create_foreign_key(
            "school_applications_reviewed_by_fkey",
            "users",
            ["reviewed_by"],
            ["id"],
        )
