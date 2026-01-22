"""Add ON DELETE behavior to foreign keys

Revision ID: g4h5i6j7k8l9
Revises: f3g4h5i6j7k8
Create Date: 2026-01-21

This migration adds explicit ON DELETE behavior to foreign key constraints
to ensure data integrity and prevent orphaned records or unexpected errors:

1. users.school_id FK -> ON DELETE SET NULL
   - When a school is deleted, associated users remain but lose their school_id
   - This preserves user accounts and allows reassignment if needed

2. schools.application_id FK -> ON DELETE SET NULL
   - When an application is deleted, the school remains but loses the reference
   - This is a historical reference only, so SET NULL is appropriate
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "g4h5i6j7k8l9"
down_revision = "f3g4h5i6j7k8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop and recreate users.school_id FK with ON DELETE SET NULL
    op.drop_constraint(
        "fk_users_school_id",
        "users",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_users_school_id",
        "users",
        "schools",
        ["school_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Drop and recreate schools.application_id FK with ON DELETE SET NULL
    op.drop_constraint(
        "fk_schools_application_id",
        "schools",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_schools_application_id",
        "schools",
        "school_applications",
        ["application_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Revert users.school_id FK (remove ON DELETE)
    op.drop_constraint(
        "fk_users_school_id",
        "users",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_users_school_id",
        "users",
        "schools",
        ["school_id"],
        ["id"],
    )

    # Revert schools.application_id FK (remove ON DELETE)
    op.drop_constraint(
        "fk_schools_application_id",
        "schools",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_schools_application_id",
        "schools",
        "school_applications",
        ["application_id"],
        ["id"],
    )
