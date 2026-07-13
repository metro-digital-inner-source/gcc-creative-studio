"""create groups table

Revision ID: 6bd11c58f086
Revises: 5c8041789c36
Create Date: 2026-07-14 00:16:13.540613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bd11c58f086'
down_revision: Union[str, None] = '5c8041789c36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create groups table
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('country_code', sa.String(), nullable=True),
        sa.Column('shared_workspace_id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['shared_workspace_id'],
            ['workspaces.id'],
            name='groups_shared_workspace_id_fkey',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('shared_workspace_id', name='groups_shared_workspace_id_unique'),
    )
    # Create index on shared_workspace_id for query performance
    op.create_index(
        'ix_groups_shared_workspace_id',
        'groups',
        ['shared_workspace_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_groups_shared_workspace_id', table_name='groups')
    op.drop_table('groups')
