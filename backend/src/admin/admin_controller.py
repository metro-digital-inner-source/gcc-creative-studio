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

from fastapi import APIRouter, Depends, HTTPException, status
from src.auth.auth_guard import RoleChecker, get_current_user
from src.users.user_model import UserRoleEnum, UserModel
from src.admin.admin_service import AdminService
from src.admin.dto.admin_response_dto import (
    AdminOverviewStats,
    AdminMediaOverTime,
    AdminWorkspaceStats,
    AdminActiveRole,
    AdminGenerationHealth,
    AdminMonthlyActiveUsers,
)

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin Dashboard"],
    dependencies=[Depends(RoleChecker(allowed_roles=[UserRoleEnum.ADMIN]))],
)


@router.get("/overview-stats", response_model=AdminOverviewStats)
async def get_overview_stats(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    """Retrieves platform overview statistics.

    Includes total users, workspaces, and media generated counts.
    """
    return await admin_service.get_overview_stats(
        start_date=start_date, end_date=end_date
    )


@router.get("/media-over-time", response_model=list[AdminMediaOverTime])
async def get_media_over_time(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    """Retrieves media generation breakdown over time.

    Grouped by date and media type.
    """
    return await admin_service.get_media_over_time(
        start_date=start_date, end_date=end_date
    )


@router.get("/workspace-stats", response_model=list[AdminWorkspaceStats])
async def get_workspace_stats(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    """Retrieves statistics per workspace.

    Includes total media and breakdown by type for each workspace.
    """
    return await admin_service.get_workspace_stats(
        start_date=start_date, end_date=end_date
    )


@router.get("/active-roles", response_model=list[AdminActiveRole])
async def get_active_roles(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    """Retrieves distribution of active user roles.

    Counts users assigned to each role.
    """
    return await admin_service.get_active_roles(
        start_date=start_date, end_date=end_date
    )


@router.get("/generation-health", response_model=list[AdminGenerationHealth])
async def get_generation_health(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    """Retrieves health statistics for media generation jobs.

    Counts jobs by status (completed, failed, processing, stopped).
    """
    return await admin_service.get_generation_health(
        start_date=start_date, end_date=end_date
    )


@router.get(
    "/active-users-monthly", response_model=list[AdminMonthlyActiveUsers]
)
async def get_active_users_monthly(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    """Retrieves monthly active users evolution.

    Counts distinct users active per month.
    """
    return await admin_service.get_active_users_monthly(
        start_date=start_date, end_date=end_date
    )


@router.post("/cleanup-stuck-jobs")
async def cleanup_stuck_jobs(admin_service: AdminService = Depends()):
    """Cleans up stuck media generation jobs.

    Marks jobs with 'processing' status that are older than 1 hour as 'stopped'.
    """
    count = await admin_service.cleanup_stuck_jobs()
    return {"message": f"Cleaned up {count} stuck jobs", "count": count}


# Group Management Endpoints


@router.get("/groups")
async def get_all_groups(admin_service: AdminService = Depends()):
    """Retrieves all groups (admin view)."""
    return await admin_service.get_all_groups()


@router.post("/groups")
async def create_group_admin(
    name: str,
    country_code: str | None = None,
    admin_service: AdminService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Creates a new group (admin action)."""
    return await admin_service.create_group_admin(
        name,
        current_user,
        country_code,
    )


@router.post("/groups/{group_id}/users")
async def add_user_to_group(
    group_id: int,
    user_id: int,
    role: str = "member",
    admin_service: AdminService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Adds a user to a group (admin action)."""
    return await admin_service.add_user_to_group(
        group_id, user_id, role, current_user
    )


@router.delete("/groups/{group_id}")
async def delete_group_admin(
    group_id: int,
    admin_service: AdminService = Depends(),
):
    """Deletes a group and all its members (admin action)."""
    deleted = await admin_service.delete_group_admin(group_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )
    return {"message": f"Group {group_id} deleted successfully"}


@router.get("/groups/usage-summary")
async def get_group_usage_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    """Retrieves aggregate usage summary across all groups."""
    return await admin_service.get_group_usage_summary(start_date, end_date)


@router.get("/groups/usage-breakdown")
async def get_group_usage_breakdown(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    """Retrieves per-group usage breakdown."""
    return await admin_service.get_group_usage_breakdown(start_date, end_date)
