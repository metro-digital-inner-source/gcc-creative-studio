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

"""Add reversible group move provenance to media items.

Revision ID: 7c8d9e0f1a2b
Revises: 6186d6d560b8
Create Date: 2026-07-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c8d9e0f1a2b"
down_revision: Union[str, None] = "6186d6d560b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Record where media originated before it is moved to a group."""
    op.add_column(
        "media_items",
        sa.Column("original_workspace_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "media_items",
        sa.Column("moved_to_group_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_media_items_original_workspace_id_workspaces",
        "media_items",
        "workspaces",
        ["original_workspace_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_media_items_moved_to_group_id_groups",
        "media_items",
        "groups",
        ["moved_to_group_id"],
        ["id"],
    )
    op.create_index(
        "ix_media_items_moved_to_group_id",
        "media_items",
        ["moved_to_group_id"],
        unique=False,
    )
    op.execute(
        "UPDATE media_items "
        "SET original_workspace_id = workspace_id "
        "WHERE original_workspace_id IS NULL"
    )


def downgrade() -> None:
    """Remove group move provenance fields."""
    op.drop_index("ix_media_items_moved_to_group_id", table_name="media_items")
    op.drop_constraint(
        "fk_media_items_moved_to_group_id_groups",
        "media_items",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_media_items_original_workspace_id_workspaces",
        "media_items",
        type_="foreignkey",
    )
    op.drop_column("media_items", "moved_to_group_id")
    op.drop_column("media_items", "original_workspace_id")