"""create group members table

Revision ID: 2ed9a196f444
Revises: 6bd11c58f086
Create Date: 2026-07-14 00:16:38.278442

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ed9a196f444'
down_revision: Union[str, None] = '6bd11c58f086'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create group_members table
    op.create_table(
        'group_members',
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column(
            'joined_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['group_id'],
            ['groups.id'],
            name='group_members_group_id_fkey',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name='group_members_user_id_fkey',
        ),
        sa.PrimaryKeyConstraint('group_id', 'user_id'),
    )
    # Create index on user_id for reverse lookups (user -> groups)
    op.create_index(
        'ix_group_members_user_id',
        'group_members',
        ['user_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_group_members_user_id', table_name='group_members')
    op.drop_table('group_members')
