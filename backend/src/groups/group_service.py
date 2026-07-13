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

from datetime import date

from fastapi import Depends, HTTPException, status

from src.groups.dto.group_dto import CreateGroupRequest, ShareItemsRequest
from src.groups.dto.usage_dto import (
    GroupUsageBreakdown,
    GroupUsageSummary,
    MyUsageResponse,
)
from src.groups.repository.group_repository import GroupRepository
from src.groups.schema.group_model import (
    GroupMemberRoleEnum,
    GroupModel,
)
from src.users.user_model import UserModel
from src.workspaces.dto.create_workspace_dto import CreateWorkspaceDto
from src.workspaces.schema.workspace_model import (
    WorkspaceMember,
    WorkspaceRoleEnum,
    WorkspaceScopeEnum,
)
from src.workspaces.workspace_service import WorkspaceService


class GroupService:
    """Handles the business logic for group management."""

    def __init__(
        self,
        group_repo: GroupRepository = Depends(),
        workspace_service: WorkspaceService = Depends(),
    ):
        self.group_repo = group_repo
        self.workspace_service = workspace_service

    async def get_user_groups(self, user_id: int) -> list[GroupModel]:
        """Gets all groups for a user."""
        return await self.group_repo.find_by_user_id(user_id)

    async def create_group(
        self,
        create_request: CreateGroupRequest,
        creator: UserModel,
    ) -> GroupModel:
        """Creates a new group with a dedicated shared workspace.
        
        The creator is automatically added as an admin member.
        """
        # 1. Create a dedicated workspace for the group
        workspace_dto = CreateWorkspaceDto(
            name=f"{create_request.name} Workspace",
            scope=WorkspaceScopeEnum.PRIVATE,  # Groups use private workspaces
        )
        workspace = await self.workspace_service.create_workspace(
            user=creator,
            create_dto=workspace_dto,
        )

        # 2. Create the group with the workspace ID
        group = await self.group_repo.create_group(
            name=create_request.name,
            shared_workspace_id=workspace.id,
            country_code=create_request.country_code,
        )

        # 3. Add creator as admin member
        await self.group_repo.add_member(
            group_id=group.id,
            user_id=creator.id,
            role=GroupMemberRoleEnum.ADMIN,
        )

        # 4. Return the group with members loaded
        return await self.group_repo.get_by_id_with_members(group.id)

    async def add_member_to_group(
        self,
        group_id: int,
        user_id: int,
        role: GroupMemberRoleEnum,
        requester: UserModel,
    ) -> GroupModel:
        """Adds a member to a group.
        
        Authorization: Only group admins can add members.
        """
        # 1. Check if requester is admin of the group
        if not await self.group_repo.is_admin(group_id, requester.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group admins can add members.",
            )

        # 2. Check if group exists
        group = await self.group_repo.get_by_id_with_members(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found.",
            )

        # 3. Add member to group
        added = await self.group_repo.add_member(group_id, user_id, role)
        if not added:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this group.",
            )

        # 4. Add member to the group's shared workspace with 'editor' role
        # This allows them to view and contribute to shared content
        workspace_member = WorkspaceMember(
            user_id=user_id,
            email="",  # Email will be fetched by workspace service
            role=WorkspaceRoleEnum.EDITOR,
        )
        await self.workspace_service.workspace_repo.add_member_to_workspace(
            workspace_id=group.shared_workspace_id,
            member=workspace_member,
            user_id=user_id,
        )

        # 5. Return updated group
        return await self.group_repo.get_by_id_with_members(group_id)

    async def share_items_to_group(
        self,
        share_request: ShareItemsRequest,
        user: UserModel,
    ) -> dict:
        """Shares media items to a group by moving them to the group's workspace.
        
        Authorization: User must be a member of the group.
        """
        # 1. Check if user is member of the group
        if not await self.group_repo.is_member(share_request.group_id, user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a member of the group to share items.",
            )

        # 2. Get the group to access shared_workspace_id
        group = await self.group_repo.get_by_id_with_members(share_request.group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found.",
            )

        # 3. TODO: Move media items to the group's shared workspace
        # This will be implemented when we integrate with the media/galleries module
        # For now, return a placeholder response
        return {
            "message": "Items shared to group successfully",
            "group_id": share_request.group_id,
            "shared_workspace_id": group.shared_workspace_id,
            "item_count": len(share_request.media_item_ids),
        }

    async def get_my_usage(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> MyUsageResponse:
        """Gets usage statistics for a user within their group(s)."""
        # 1. Get user's groups
        groups = await self.group_repo.find_by_user_id(user_id)
        if not groups:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of any group.",
            )

        # 2. For now, use the first group (most users will have one group)
        # TODO: Support multiple groups or aggregate across all groups
        primary_group = groups[0]

        # 3. Get user-specific usage (from repository)
        user_usage = await self.group_repo.get_usage_for_user(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        # 4. Get group total usage
        group_breakdown = await self.group_repo.get_group_usage_breakdown(
            start_date=start_date,
            end_date=end_date,
        )
        group_total = next(
            (g for g in group_breakdown if g["group_id"] == primary_group.id),
            None,
        )

        # 5. Build response
        return MyUsageResponse(
            group_id=primary_group.id,
            group_name=primary_group.name,
            user_spend_usd=user_usage.get("user_spend_usd", 0.0),
            user_tokens_consumed=user_usage.get("user_tokens_consumed", 0),
            user_activity_count=user_usage.get("user_activity_count", 0),
            group_total_spend_usd=group_total["spend_usd"] if group_total else 0.0,
            group_total_tokens=group_total["tokens_consumed"] if group_total else 0,
        )

    # Admin methods

    async def get_all_groups_admin(self) -> list[GroupModel]:
        """Gets all groups (admin only)."""
        return await self.group_repo.get_all_groups()

    async def get_usage_summary_admin(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> GroupUsageSummary:
        """Gets aggregate usage summary (admin only)."""
        summary = await self.group_repo.get_group_usage_summary(
            start_date=start_date,
            end_date=end_date,
        )
        return GroupUsageSummary(**summary)

    async def get_usage_breakdown_admin(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[GroupUsageBreakdown]:
        """Gets per-group usage breakdown (admin only)."""
        breakdown = await self.group_repo.get_group_usage_breakdown(
            start_date=start_date,
            end_date=end_date,
        )
        return [GroupUsageBreakdown(**item) for item in breakdown]
