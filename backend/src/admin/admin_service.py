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

from datetime import datetime, timedelta
from fastapi import Depends

from src.admin.repository.admin_repository import AdminRepository
from src.admin.dto.admin_response_dto import (
    AdminOverviewStats,
    AdminMediaOverTime,
    AdminWorkspaceStats,
    AdminActiveRole,
    AdminGenerationHealth,
    AdminMonthlyActiveUsers,
    AddUserByEmailResponse,
    UserProvisioningStatus,
)
from src.groups.group_service import GroupService
from src.groups.schema.group_model import GroupMemberRoleEnum
from src.users.user_model import UserModel
from src.users.user_service import UserService


class AdminService:
    def __init__(
        self,
        admin_repo: AdminRepository = Depends(),
        group_service: GroupService = Depends(),
        user_service: UserService = Depends(),
    ):
        self.admin_repo = admin_repo
        self.group_service = group_service
        self.user_service = user_service

    async def get_overview_stats(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> AdminOverviewStats:
        return await self.admin_repo.get_overview_stats(start_date, end_date)

    async def get_media_over_time(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> list[AdminMediaOverTime]:
        return await self.admin_repo.get_media_over_time(start_date, end_date)

    async def get_workspace_stats(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> list[AdminWorkspaceStats]:
        return await self.admin_repo.get_workspace_stats(start_date, end_date)

    async def get_active_roles(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> list[AdminActiveRole]:
        return await self.admin_repo.get_active_roles(start_date, end_date)

    async def get_generation_health(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> list[AdminGenerationHealth]:
        return await self.admin_repo.get_generation_health(start_date, end_date)

    async def get_active_users_monthly(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> list[AdminMonthlyActiveUsers]:
        result_dict = await self.admin_repo.get_active_users_monthly_counts(
            start_date, end_date
        )

        if start_date and end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(day=1)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.today()
            start_dt = (end_dt - timedelta(days=180)).replace(day=1)

        months = []
        curr_dt = start_dt
        while curr_dt <= end_dt:
            months.append(curr_dt.strftime("%Y-%m"))
            if curr_dt.month == 12:
                curr_dt = curr_dt.replace(year=curr_dt.year + 1, month=1)
            else:
                curr_dt = curr_dt.replace(month=curr_dt.month + 1)

        months = sorted(list(set(months)))

        return [
            AdminMonthlyActiveUsers(month=m, count=result_dict.get(m, 0))
            for m in months
        ]

    async def cleanup_stuck_jobs(self) -> int:
        return await self.admin_repo.cleanup_stuck_jobs()

    # Group Management Methods

    async def get_all_groups(self):
        """Gets all groups (admin view)."""
        return await self.group_service.get_all_groups_admin()

    async def create_group_admin(
        self,
        name: str,
        admin_user: UserModel,
        country_code: str | None = None,
    ):
        """Creates a new group as admin."""
        from src.groups.dto.group_dto import CreateGroupRequest

        request = CreateGroupRequest(name=name, country_code=country_code)
        return await self.group_service.create_group(request, admin_user)

    async def add_user_to_group(
        self,
        group_id: int,
        user_id: int,
        role: str,
        admin_user: UserModel,
    ):
        """Adds a user to a group (admin action)."""
        # Parse role
        try:
            member_role = GroupMemberRoleEnum(role)
        except ValueError:
            member_role = GroupMemberRoleEnum.MEMBER

        return await self.group_service.add_member_to_group(
            group_id,
            user_id,
            member_role,
            admin_user,
        )

    async def add_user_to_group_by_email(
        self,
        group_id: int,
        email: str,
        role: str,
        admin_user: UserModel,
    ) -> AddUserByEmailResponse:
        """Creates/gets a user by email and assigns them to a group."""
        try:
            member_role = GroupMemberRoleEnum(role)
        except ValueError:
            member_role = GroupMemberRoleEnum.MEMBER

        user, provisioning_status = (
            await self.user_service.create_or_restore_user_by_email_for_admin(
                email
            )
        )

        group = await self.group_service.add_member_to_group(
            group_id,
            user.id,
            member_role,
            admin_user,
        )

        return AddUserByEmailResponse(
            provisioning_status=UserProvisioningStatus(provisioning_status),
            created_new_user=provisioning_status == "created",
            user_id=user.id,
            email=user.email,
            group=group,
        )

    async def delete_group_admin(self, group_id: int) -> bool:
        """Deletes a group (admin action). Returns True if deleted, False if not found."""
        return await self.group_service.group_repo.delete_group(group_id)

    async def get_group_usage_summary(
        self, start_date: str | None = None, end_date: str | None = None
    ):
        """Gets aggregate usage summary."""
        from datetime import date as date_type

        start = date_type.fromisoformat(start_date) if start_date else None
        end = date_type.fromisoformat(end_date) if end_date else None

        return await self.group_service.get_usage_summary_admin(start, end)

    async def get_group_usage_breakdown(
        self, start_date: str | None = None, end_date: str | None = None
    ):
        """Gets per-group usage breakdown."""
        from datetime import date as date_type

        start = date_type.fromisoformat(start_date) if start_date else None
        end = date_type.fromisoformat(end_date) if end_date else None

        return await self.group_service.get_usage_breakdown_admin(start, end)
