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

from fastapi import APIRouter, Depends, Query, status

from src.auth.auth_guard import get_current_user
from src.groups.dto.group_dto import (
    CreateGroupRequest,
    RestoreItemsRequest,
    ShareItemsRequest,
)
from src.groups.dto.usage_dto import MyUsageResponse
from src.groups.group_service import GroupService
from src.groups.schema.group_model import GroupModel
from src.users.user_model import UserModel

router = APIRouter(
    prefix="/api/groups",
    tags=["Groups"],
    dependencies=[
        Depends(get_current_user)
    ],  # All endpoints require authentication
)


@router.get(
    "/me",
    response_model=list[GroupModel],
    summary="Get My Groups",
)
async def get_my_groups(
    current_user: UserModel = Depends(get_current_user),
    group_service: GroupService = Depends(),
):
    """Retrieves all groups the current user is a member of."""
    return await group_service.get_user_groups(current_user.id)


@router.post(
    "",
    response_model=GroupModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Group",
)
async def create_group(
    create_request: CreateGroupRequest,
    current_user: UserModel = Depends(get_current_user),
    group_service: GroupService = Depends(),
):
    """Creates a new group with a dedicated shared workspace.

    The creator is automatically added as an admin member.
    """
    return await group_service.create_group(create_request, current_user)


@router.post(
    "/share-items",
    summary="Share Items to Group",
)
async def share_items_to_group(
    share_request: ShareItemsRequest,
    current_user: UserModel = Depends(get_current_user),
    group_service: GroupService = Depends(),
):
    """Shares media items to a group by moving them to the group's shared workspace.

    Authorization: User must be a member of the group.
    """
    return await group_service.share_items_to_group(share_request, current_user)


@router.post(
    "/restore-items",
    summary="Restore Items from Group",
)
async def restore_items_from_group(
    restore_request: RestoreItemsRequest,
    current_user: UserModel = Depends(get_current_user),
    group_service: GroupService = Depends(),
):
    """Restores moved media items to the workspace they originated from."""
    return await group_service.restore_items_from_group(
        restore_request,
        current_user,
    )


@router.get(
    "/my-usage",
    response_model=MyUsageResponse,
    summary="Get My Usage Statistics",
)
async def get_my_usage(
    start_date: date | None = Query(
        None, description="Start date for usage period"
    ),
    end_date: date | None = Query(
        None, description="End date for usage period"
    ),
    current_user: UserModel = Depends(get_current_user),
    group_service: GroupService = Depends(),
):
    """Retrieves usage statistics for the current user within their group."""
    return await group_service.get_my_usage(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
