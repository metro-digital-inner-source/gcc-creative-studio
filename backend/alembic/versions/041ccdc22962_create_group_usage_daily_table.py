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

"""create group usage daily table

Revision ID: 041ccdc22962
Revises: 2ed9a196f444
Create Date: 2026-07-14 00:17:02.955647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '041ccdc22962'
down_revision: Union[str, None] = '2ed9a196f444'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create group_usage_daily table for analytics aggregation
    op.create_table(
        'group_usage_daily',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column(
            'spend_usd',
            sa.Numeric(precision=10, scale=2),
            server_default='0',
            nullable=False,
        ),
        sa.Column(
            'tokens_consumed',
            sa.BigInteger(),
            server_default='0',
            nullable=False,
        ),
        sa.Column(
            'activity_count',
            sa.Integer(),
            server_default='0',
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['group_id'],
            ['groups.id'],
            name='group_usage_daily_group_id_fkey',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'date', name='group_usage_daily_group_date_unique'),
    )
    # Create index for date-range queries
    op.create_index(
        'ix_group_usage_daily_date',
        'group_usage_daily',
        ['date'],
        unique=False,
    )
    # Create index for group lookups
    op.create_index(
        'ix_group_usage_daily_group_id',
        'group_usage_daily',
        ['group_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_group_usage_daily_group_id', table_name='group_usage_daily')
    op.drop_index('ix_group_usage_daily_date', table_name='group_usage_daily')
    op.drop_table('group_usage_daily')
