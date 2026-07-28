# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""create groups table

Revision ID: 6bd11c58f086
Revises: add_allowlist_001
Create Date: 2026-07-14 00:16:13.540613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bd11c58f086'
down_revision: Union[str, None] = 'add_allowlist_001'
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
