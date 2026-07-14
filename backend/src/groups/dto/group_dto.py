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

"""DTOs for group operations."""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.common.base_repository import BaseDocument
from src.groups.schema.group_model import GroupMemberRoleEnum


class CreateGroupRequest(BaseModel):
    """Request DTO for creating a new group."""

    name: str = Field(description="The name of the group.")
    country_code: str | None = Field(
        None, description="Optional country code for the group."
    )

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class AddMemberRequest(BaseModel):
    """Request DTO for adding a member to a group."""

    user_id: int = Field(description="The ID of the user to add.")
    role: GroupMemberRoleEnum = Field(
        default=GroupMemberRoleEnum.MEMBER,
        description="The role to assign to the member.",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class ShareItemsRequest(BaseModel):
    """Request DTO for sharing items to a group."""

    group_id: int = Field(description="The ID of the group to share items to.")
    media_item_ids: list[int] = Field(
        description="List of media item IDs to share."
    )

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class RestoreItemsRequest(BaseModel):
    """Request DTO for restoring media from a group workspace."""

    media_item_ids: list[int] = Field(
        description="List of media item IDs to restore to their original workspaces."
    )

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class GroupResponse(BaseDocument):
    """Response DTO for group data."""

    id: int
    name: str
    country_code: str | None = None
    shared_workspace_id: int
    member_count: int = Field(default=0, description="Number of members in the group.")
    created_at: str  # ISO datetime string
    updated_at: str  # ISO datetime string
