"""add schools table and update users

Revision ID: e2f3g4h5i6j7
Revises: d1e2f3g4h5i6
Create Date: 2026-01-21 12:00:00.000000

This migration:
1. Creates the schools table for multi-tenant school management
2. Adds school_id foreign key to users table for tenant isolation
3. Adds must_change_password field to users table

The schools table is created BEFORE adding the foreign key to users
to ensure referential integrity.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e2f3g4h5i6j7"
down_revision: str | Sequence[str] | None = "d1e2f3g4h5i6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create schools table and update users table."""
    # Create the school_status enum type (only if it doesn't exist)
    school_status_enum = postgresql.ENUM(
        "active",
        "suspended",
        "deactivated",
        name="school_status",
        create_type=False,  # Don't auto-create, we'll do it manually with checkfirst
    )
    school_status_enum.create(op.get_bind(), checkfirst=True)

    # Create the schools table
    op.create_table(
        "schools",
        # Primary key and timestamps (from BaseModel)
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Basic information
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("year_established", sa.Integer(), nullable=False),
        sa.Column("school_type", sa.String(length=50), nullable=False),
        sa.Column("student_population", sa.String(length=50), nullable=False),
        # Location
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        # Contact information
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        # Principal information
        sa.Column("principal_name", sa.String(length=200), nullable=False),
        sa.Column("principal_email", sa.String(length=255), nullable=False),
        sa.Column("principal_phone", sa.String(length=20), nullable=True),
        # Online presence (JSONB array)
        sa.Column(
            "online_presence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        # Status
        sa.Column(
            "status",
            school_status_enum,
            nullable=False,
            server_default="active",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Reference to original application (unique to prevent duplicates)
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["school_applications.id"],
            name="fk_schools_application_id",
        ),
        sa.UniqueConstraint("application_id", name="uq_schools_application_id"),
    )

    # Create indexes on schools table
    op.create_index(op.f("ix_schools_name"), "schools", ["name"], unique=False)
    op.create_index(op.f("ix_schools_country_code"), "schools", ["country_code"], unique=False)

    # Add school_id column to users table
    op.add_column(
        "users",
        sa.Column(
            "school_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),
    )

    # Create foreign key constraint from users to schools
    op.create_foreign_key(
        "fk_users_school_id",
        "users",
        "schools",
        ["school_id"],
        ["id"],
    )

    # Create index on users.school_id for efficient tenant queries
    op.create_index(op.f("ix_users_school_id"), "users", ["school_id"], unique=False)

    # Add must_change_password column to users table
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    """Remove schools table and revert users changes."""
    # Remove must_change_password column from users
    op.drop_column("users", "must_change_password")

    # Remove school_id foreign key and column from users
    op.drop_index(op.f("ix_users_school_id"), table_name="users")
    op.drop_constraint("fk_users_school_id", "users", type_="foreignkey")
    op.drop_column("users", "school_id")

    # Drop indexes on schools table
    op.drop_index(op.f("ix_schools_country_code"), table_name="schools")
    op.drop_index(op.f("ix_schools_name"), table_name="schools")

    # Drop schools table
    op.drop_table("schools")

    # Drop the school_status enum type
    school_status_enum = postgresql.ENUM(
        "active",
        "suspended",
        "deactivated",
        name="school_status",
    )
    school_status_enum.drop(op.get_bind(), checkfirst=True)
