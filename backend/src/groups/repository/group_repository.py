# Copyright 2025 Google LLC
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

from datetime import date, datetime

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.base_repository import BaseRepository
from src.database import get_db
from src.groups.schema.group_model import (
    Group,
    GroupMember,
    GroupMemberRoleEnum,
    GroupModel,
    GroupUsageDaily,
)
from src.users.user_model import User


class GroupRepository(BaseRepository[Group, GroupModel]):
    """Repository for all database operations related to groups."""

    def __init__(self, db: AsyncSession = Depends(get_db)):
        """Initializes the repository."""
        super().__init__(model=Group, schema=GroupModel, db=db)

    async def find_by_user_id(self, user_id: int) -> list[GroupModel]:
        """Finds all groups where the user is a member."""
        result = await self.db.execute(
            select(self.model)
            .join(GroupMember)
            .where(GroupMember.user_id == user_id)
            .order_by(self.model.name)
        )
        groups = result.scalars().all()
        return [self._map_to_schema(g) for g in groups]

    async def get_by_id_with_members(self, group_id: int) -> GroupModel | None:
        """Gets a group by ID with all members loaded."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == group_id)
        )
        group = result.scalar_one_or_none()
        if not group:
            return None
        return self._map_to_schema(group)

    async def create_group(
        self,
        name: str,
        shared_workspace_id: int,
        country_code: str | None = None,
    ) -> GroupModel:
        """Creates a new group."""
        db_group = self.model(
            name=name,
            country_code=country_code,
            shared_workspace_id=shared_workspace_id,
        )
        self.db.add(db_group)
        await self.db.commit()
        await self.db.refresh(db_group)
        return self._map_to_schema(db_group)

    async def add_member(
        self,
        group_id: int,
        user_id: int,
        role: GroupMemberRoleEnum = GroupMemberRoleEnum.MEMBER,
    ) -> bool:
        """Adds a member to a group. Returns True if added, False if already exists."""
        # Check if already a member
        result = await self.db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return False

        # Add new member
        db_member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            role=role.value,
        )
        self.db.add(db_member)
        await self.db.commit()
        return True

    async def is_member(self, group_id: int, user_id: int) -> bool:
        """Checks if a user is a member of a group."""
        result = await self.db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_admin(self, group_id: int, user_id: int) -> bool:
        """Checks if a user is an admin of a group."""
        result = await self.db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
                GroupMember.role == GroupMemberRoleEnum.ADMIN.value,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_all_groups(self) -> list[GroupModel]:
        """Gets all groups (admin use)."""
        result = await self.db.execute(
            select(self.model).order_by(self.model.name)
        )
        groups = result.scalars().all()
        return [self._map_to_schema(g) for g in groups]

    async def get_all_shared_workspace_ids(self) -> set[int]:
        """Gets all shared workspace IDs referenced by groups."""
        result = await self.db.execute(select(self.model.shared_workspace_id))
        return {row[0] for row in result.all()}

    async def delete_group(self, group_id: int) -> bool:
        """Deletes a group and all its members. Returns True if deleted, False if not found."""
        # First delete all group members
        await self.db.execute(
            select(GroupMember).where(GroupMember.group_id == group_id)
        )
        await self.db.execute(
            GroupMember.__table__.delete().where(
                GroupMember.group_id == group_id
            )
        )

        # Then delete the group
        result = await self.db.execute(
            select(self.model).where(self.model.id == group_id)
        )
        group = result.scalar_one_or_none()
        if not group:
            return False

        await self.db.delete(group)
        await self.db.commit()
        return True

    async def get_usage_for_user(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """Gets usage statistics for a specific user across their groups."""
        # Find user's groups
        group_result = await self.db.execute(
            select(GroupMember.group_id).where(GroupMember.user_id == user_id)
        )
        group_ids = [row[0] for row in group_result.all()]

        if not group_ids:
            return {
                "user_spend_usd": 0.0,
                "user_tokens_consumed": 0,
                "user_activity_count": 0,
            }

        # Build query for user's usage
        # Note: This is a placeholder. In reality, you'd query from audit logs
        # or a user_usage_daily table filtered by user_id
        # For now, return zeros as the aggregation logic needs to be implemented
        return {
            "user_spend_usd": 0.0,
            "user_tokens_consumed": 0,
            "user_activity_count": 0,
        }

    async def get_group_usage_summary(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """Gets aggregate usage summary across all groups."""
        usage_query = (
            select(
                func.coalesce(func.sum(GroupUsageDaily.spend_usd), 0).label(
                    "total_spend_usd"
                ),
                func.coalesce(
                    func.sum(GroupUsageDaily.tokens_consumed), 0
                ).label("total_tokens_consumed"),
            )
            .select_from(GroupUsageDaily)
        )

        if start_date:
            usage_query = usage_query.where(GroupUsageDaily.date >= start_date)
        if end_date:
            usage_query = usage_query.where(GroupUsageDaily.date <= end_date)

        usage_subquery = usage_query.subquery()

        query = select(
            select(func.count(Group.id)).scalar_subquery().label("total_groups"),
            select(func.count(func.distinct(GroupMember.user_id)))
            .scalar_subquery()
            .label("total_members"),
            usage_subquery.c.total_spend_usd,
            usage_subquery.c.total_tokens_consumed,
        )

        result = await self.db.execute(query)
        row = result.one()

        return {
            "total_groups": row.total_groups or 0,
            "total_members": row.total_members or 0,
            "total_spend_usd": float(row.total_spend_usd or 0),
            "total_tokens_consumed": int(row.total_tokens_consumed or 0),
        }

    async def get_group_usage_breakdown(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        """Gets per-group usage breakdown."""
        member_count_subquery = (
            select(
                GroupMember.group_id.label("group_id"),
                func.count(func.distinct(GroupMember.user_id)).label(
                    "member_count"
                ),
            )
            .group_by(GroupMember.group_id)
            .subquery()
        )

        usage_query = select(
            GroupUsageDaily.group_id.label("group_id"),
            func.coalesce(func.sum(GroupUsageDaily.spend_usd), 0).label(
                "spend_usd"
            ),
            func.coalesce(func.sum(GroupUsageDaily.tokens_consumed), 0).label(
                "tokens_consumed"
            ),
            func.coalesce(func.sum(GroupUsageDaily.activity_count), 0).label(
                "activity_count"
            ),
        )

        if start_date:
            usage_query = usage_query.where(GroupUsageDaily.date >= start_date)
        if end_date:
            usage_query = usage_query.where(GroupUsageDaily.date <= end_date)

        usage_subquery = usage_query.group_by(GroupUsageDaily.group_id).subquery()

        query = (
            select(
                Group.id.label("group_id"),
                Group.name.label("group_name"),
                Group.country_code.label("country_code"),
                func.coalesce(
                    member_count_subquery.c.member_count,
                    0,
                ).label("member_count"),
                func.coalesce(
                    usage_subquery.c.spend_usd,
                    0,
                ).label("spend_usd"),
                func.coalesce(
                    usage_subquery.c.tokens_consumed,
                    0,
                ).label("tokens_consumed"),
                func.coalesce(
                    usage_subquery.c.activity_count,
                    0,
                ).label("activity_count"),
            )
            .select_from(Group)
            .outerjoin(
                member_count_subquery,
                Group.id == member_count_subquery.c.group_id,
            )
            .outerjoin(usage_subquery, Group.id == usage_subquery.c.group_id)
            .order_by(Group.name)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "group_id": row.group_id,
                "group_name": row.group_name,
                "country_code": row.country_code,
                "member_count": row.member_count or 0,
                "spend_usd": float(row.spend_usd or 0),
                "tokens_consumed": int(row.tokens_consumed or 0),
                "activity_count": int(row.activity_count or 0),
            }
            for row in rows
        ]

    def _map_to_schema(self, group: Group) -> GroupModel:
        """Helper to map SQLAlchemy Group to Pydantic GroupModel."""
        # Map members
        from src.groups.schema.group_model import GroupMemberModel

        members = []
        for member in group.members:
            # Member.user is loaded via lazy="selectin"
            members.append(
                GroupMemberModel(
                    user_id=member.user_id,
                    email=member.user.email,
                    name=member.user.name or "",
                    role=GroupMemberRoleEnum(member.role),
                    joined_at=member.joined_at,
                )
            )

        group_dict = {
            "id": group.id,
            "name": group.name,
            "country_code": group.country_code,
            "shared_workspace_id": group.shared_workspace_id,
            "members": members,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
        }

        return self.schema.model_validate(group_dict)
