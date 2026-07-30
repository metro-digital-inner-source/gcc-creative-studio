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
from src.config.config_service import config_service
from src.users.user_model import UserRoleEnum, UserModel
from src.admin.admin_service import AdminService
from src.admin.dto.admin_request_dto import AddUserByEmailRequest
from src.admin.dto.admin_response_dto import (
    AdminOverviewStats,
    AdminMediaOverTime,
    AdminWorkspaceStats,
    AdminActiveRole,
    AdminGenerationHealth,
    AdminMonthlyActiveUsers,
    AddUserByEmailResponse,
)

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin Dashboard"],
    dependencies=[
        Depends(
            RoleChecker(
                allowed_roles=[UserRoleEnum.ADMIN],
                allowed_emails=config_service.ADMIN_OWNER_EMAILS,
            )
        )
    ],
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


# Group Management Endpoints replaced by Workspace Management


@router.get("/workspaces")
async def get_all_workspaces(admin_service: AdminService = Depends()):
    """Retrieves all workspaces with members (admin view)."""
    return await admin_service.get_all_workspaces()


@router.post("/workspaces")
async def create_team_workspace_admin(
    name: str,
    admin_service: AdminService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Creates a new team workspace (admin action)."""
    return await admin_service.create_team_workspace_admin(name, current_user)


@router.post("/workspaces/{workspace_id}/users")
async def add_user_to_workspace(
    workspace_id: int,
    user_id: int,
    role: str = "user",
    admin_service: AdminService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Adds a user to a workspace (admin action)."""
    return await admin_service.add_user_to_workspace(
        workspace_id, user_id, role, current_user
    )


@router.post(
    "/workspaces/{workspace_id}/users/by-email",
    response_model=AddUserByEmailResponse,
)
async def add_user_to_workspace_by_email(
    workspace_id: int,
    request: AddUserByEmailRequest,
    admin_service: AdminService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Creates/gets a user by email and assigns them to a team workspace."""
    return await admin_service.add_user_to_workspace_by_email(
        workspace_id=workspace_id,
        email=request.email,
        role="user",
        admin_user=current_user,
    )


@router.patch("/workspaces/{workspace_id}/users/{user_id}")
async def update_workspace_member_role(
    workspace_id: int,
    user_id: int,
    role: str,
    admin_service: AdminService = Depends(),
):
    """Updates a workspace member's role (user or admin)."""
    return await admin_service.update_workspace_member_role(
        workspace_id, user_id, role
    )


@router.delete("/workspaces/{workspace_id}/users/{user_id}")
async def remove_user_from_workspace(
    workspace_id: int,
    user_id: int,
    admin_service: AdminService = Depends(),
):
    """Removes a user from a workspace (admin action)."""
    return await admin_service.remove_user_from_workspace(workspace_id, user_id)


@router.delete("/workspaces/{workspace_id}")
async def delete_team_workspace_admin(
    workspace_id: int,
    admin_service: AdminService = Depends(),
):
    """Deletes a team workspace (admin action)."""
    deleted = await admin_service.delete_team_workspace_admin(workspace_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team workspace {workspace_id} not found",
        )
    return {"message": f"Workspace {workspace_id} deleted successfully"}


@router.post("/dev/reset-database")
async def dev_reset_database(
    current_user: UserModel = Depends(
        RoleChecker(allowed_roles=[UserRoleEnum.ADMIN])
    ),
    admin_service: AdminService = Depends(),
):
    """DEV ONLY: Reset all application data (truncate all tables).
    
    This endpoint is only available in dev/local environments and requires
    admin privileges. Use to start fresh testing after deployment.
    """
    if config_service.ENVIRONMENT not in ["development", "local"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development/local environments.",
        )

    return await admin_service.reset_dev_database()
