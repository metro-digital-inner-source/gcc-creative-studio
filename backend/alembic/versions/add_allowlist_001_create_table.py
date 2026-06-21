"""add_allowlist_table

Revision ID: add_allowlist_001
Revises: ae0287db1562
Create Date: 2025-06-21 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_allowlist_001"
down_revision = "ae0287db1562"  # Latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the allowlist_entries table
    op.create_table(
        "allowlist_entries",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("domain", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.String(), nullable=False, server_default=""),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_allowlist_email"),
    )
    
    # Create indexes for performance
    op.create_index(
        "ix_allowlist_email",
        "allowlist_entries",
        ["email"],
        unique=False,
    )
    op.create_index(
        "ix_allowlist_domain",
        "allowlist_entries",
        ["domain"],
        unique=False,
    )
    op.create_index(
        "ix_allowlist_is_active",
        "allowlist_entries",
        ["is_active"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("ix_allowlist_is_active", table_name="allowlist_entries")
    op.drop_index("ix_allowlist_domain", table_name="allowlist_entries")
    op.drop_index("ix_allowlist_email", table_name="allowlist_entries")
    
    # Drop table
    op.drop_table("allowlist_entries")
