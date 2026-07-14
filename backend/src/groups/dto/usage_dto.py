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

"""DTOs for group usage analytics."""

from pydantic import ConfigDict, Field

from src.common.base_repository import BaseDocument


class GroupUsageSummary(BaseDocument):
    """Summary DTO for aggregate group usage statistics."""

    total_groups: int = Field(description="Total number of groups.")
    total_members: int = Field(
        description="Total number of group members across all groups."
    )
    total_spend_usd: float = Field(
        description="Total spend in USD across all groups."
    )
    total_tokens_consumed: int = Field(
        description="Total tokens consumed across all groups."
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class GroupUsageBreakdown(BaseDocument):
    """Breakdown DTO for per-group usage statistics."""

    group_id: int = Field(description="The group ID.")
    group_name: str = Field(description="The group name.")
    country_code: str | None = Field(
        None, description="The group's country code."
    )
    member_count: int = Field(description="Number of members in the group.")
    spend_usd: float = Field(description="Total spend in USD for this group.")
    tokens_consumed: int = Field(
        description="Total tokens consumed by this group."
    )
    activity_count: int = Field(
        description="Total activity count for this group."
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class MyUsageResponse(BaseDocument):
    """Response DTO for a user's personal usage within their group."""

    group_id: int = Field(description="The user's group ID.")
    group_name: str = Field(description="The user's group name.")
    user_spend_usd: float = Field(description="User's spend in USD.")
    user_tokens_consumed: int = Field(description="User's tokens consumed.")
    user_activity_count: int = Field(description="User's activity count.")
    group_total_spend_usd: float = Field(
        description="Group's total spend in USD."
    )
    group_total_tokens: int = Field(
        description="Group's total tokens consumed."
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )
