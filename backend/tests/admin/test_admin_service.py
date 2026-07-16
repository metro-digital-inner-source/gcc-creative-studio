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

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from src.admin.admin_service import AdminService
from src.admin.dto.admin_response_dto import (
    AdminOverviewStats,
    AdminMediaOverTime,
    AdminWorkspaceStats,
    AdminActiveRole,
    AdminGenerationHealth,
    AdminMonthlyActiveUsers,
    UserProvisioningStatus,
)
from src.groups.schema.group_model import GroupModel
from src.users.user_model import UserModel, UserRoleEnum


@pytest.mark.asyncio
async def test_get_overview_stats():
    mock_repo = MagicMock()
    mock_repo.get_overview_stats = AsyncMock(
        return_value=AdminOverviewStats(
            total_users=10,
            total_workspaces=5,
            images_generated=100,
            videos_generated=50,
            audios_generated=25,
            total_media=175,
            user_uploaded_media=2,
            overall_total_media=177,
        )
    )

    service = AdminService(admin_repo=mock_repo)
    result = await service.get_overview_stats()

    assert result.total_users == 10
    assert result.total_workspaces == 5
    assert result.images_generated == 100
    assert result.videos_generated == 50
    assert result.audios_generated == 25
    assert result.total_media == 175


@pytest.mark.asyncio
async def test_get_media_over_time():
    mock_repo = MagicMock()
    mock_repo.get_media_over_time = AsyncMock(
        return_value=[
            AdminMediaOverTime(
                date="2026-04", total_generated=10, images=5, videos=3, audios=2
            )
        ]
    )

    service = AdminService(admin_repo=mock_repo)
    result = await service.get_media_over_time()
    assert len(result) == 1
    assert result[0].date == "2026-04"
    assert result[0].total_generated == 10


@pytest.mark.asyncio
async def test_get_workspace_stats():
    mock_repo = MagicMock()
    mock_repo.get_workspace_stats = AsyncMock(
        return_value=[
            AdminWorkspaceStats(
                workspace_id=1,
                workspace_name="Test Workspace",
                total_media=10,
                images=5,
                videos=3,
                audios=2,
            )
        ]
    )

    service = AdminService(admin_repo=mock_repo)
    result = await service.get_workspace_stats()
    assert len(result) == 1
    assert result[0].workspace_id == 1
    assert result[0].total_media == 10


@pytest.mark.asyncio
async def test_get_active_roles():
    mock_repo = MagicMock()
    mock_repo.get_active_roles = AsyncMock(
        return_value=[AdminActiveRole(role="ADMIN", count=2)]
    )

    service = AdminService(admin_repo=mock_repo)
    result = await service.get_active_roles()
    assert len(result) == 1
    assert result[0].role == "ADMIN"
    assert result[0].count == 2


@pytest.mark.asyncio
async def test_get_generation_health():
    mock_repo = MagicMock()
    mock_repo.get_generation_health = AsyncMock(
        return_value=[AdminGenerationHealth(status="COMPLETED", count=8)]
    )

    service = AdminService(admin_repo=mock_repo)
    result = await service.get_generation_health()
    assert len(result) == 1
    assert result[0].status == "COMPLETED"
    assert result[0].count == 8


@pytest.mark.asyncio
async def test_get_active_users_monthly():
    mock_repo = MagicMock()
    mock_repo.get_active_users_monthly_counts = AsyncMock(
        return_value={"2026-04": 3}
    )

    service = AdminService(admin_repo=mock_repo)
    result = await service.get_active_users_monthly()
    assert len(result) == 7  # Default 180 days should yield 7 months


@pytest.mark.asyncio
async def test_cleanup_stuck_jobs():
    mock_repo = MagicMock()
    mock_repo.cleanup_stuck_jobs = AsyncMock(return_value=5)

    service = AdminService(admin_repo=mock_repo)
    result = await service.cleanup_stuck_jobs()
    assert result == 5


@pytest.mark.asyncio
async def test_add_user_to_group_by_email_created():
    mock_group_service = MagicMock()
    mock_user_service = MagicMock()
    mock_admin_repo = MagicMock()
    mock_workspace_service = MagicMock()
    mock_workspace_repo = MagicMock()

    provisioned_user = UserModel(
        id=10,
        email="new.user@example.com",
        roles=[UserRoleEnum.USER],
        name="New User",
    )
    group = GroupModel(
        id=2,
        name="Design",
        shared_workspace_id=20,
        members=[],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    admin_user = UserModel(
        id=1,
        email="owner@example.com",
        roles=[UserRoleEnum.ADMIN],
        name="Owner",
    )

    mock_user_service.create_or_restore_user_by_email_for_admin = AsyncMock(
        return_value=(provisioned_user, "created")
    )
    mock_group_service.add_member_to_group = AsyncMock(return_value=group)
    
    # Mock workspace methods
    mock_workspace_service.check_workspace_name_exists = AsyncMock(return_value=False)
    mock_workspace_service.create_workspace = AsyncMock(
        return_value=MagicMock(id=100, name="Design")
    )
    mock_workspace_repo.is_member = AsyncMock(return_value=False)
    mock_workspace_repo.add_member_to_workspace = AsyncMock()
    mock_workspace_repo.find_by_name = AsyncMock(return_value=None)
    mock_workspace_service.workspace_repo = mock_workspace_repo

    service = AdminService(
        admin_repo=mock_admin_repo,
        group_service=mock_group_service,
        user_service=mock_user_service,
        workspace_service=mock_workspace_service,
    )
    response = await service.add_user_to_group_by_email(
        group_id=2,
        email="new.user@example.com",
        role="member",
        admin_user=admin_user,
    )

    assert response.provisioning_status == UserProvisioningStatus.CREATED
    assert response.created_new_user is True
    assert response.user_id == 10
    assert response.email == "new.user@example.com"
    assert response.group.id == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        "existing",
        "restored",
    ],
)
async def test_add_user_to_group_by_email_existing_or_restored(status):
    mock_group_service = MagicMock()
    mock_user_service = MagicMock()
    mock_admin_repo = MagicMock()
    mock_workspace_service = MagicMock()
    mock_workspace_repo = MagicMock()

    provisioned_user = UserModel(
        id=11,
        email="existing.user@example.com",
        roles=[UserRoleEnum.USER],
        name="Existing User",
    )
    group = GroupModel(
        id=3,
        name="Marketing",
        shared_workspace_id=30,
        members=[],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    admin_user = UserModel(
        id=1,
        email="owner@example.com",
        roles=[UserRoleEnum.ADMIN],
        name="Owner",
    )

    mock_user_service.create_or_restore_user_by_email_for_admin = AsyncMock(
        return_value=(provisioned_user, status)
    )
    mock_group_service.add_member_to_group = AsyncMock(return_value=group)
    
    # Mock workspace methods
    mock_workspace_service.check_workspace_name_exists = AsyncMock(return_value=False)
    mock_workspace_service.create_workspace = AsyncMock(
        return_value=MagicMock(id=100, name="Marketing")
    )
    mock_workspace_repo.is_member = AsyncMock(return_value=False)
    mock_workspace_repo.add_member_to_workspace = AsyncMock()
    mock_workspace_repo.find_by_name = AsyncMock(return_value=None)
    mock_workspace_service.workspace_repo = mock_workspace_repo

    service = AdminService(
        admin_repo=mock_admin_repo,
        group_service=mock_group_service,
        user_service=mock_user_service,
        workspace_service=mock_workspace_service,
    )
    response = await service.add_user_to_group_by_email(
        group_id=3,
        email="existing.user@example.com",
        role="member",
        admin_user=admin_user,
    )

    expected_status = (
        UserProvisioningStatus.EXISTING
        if status == "existing"
        else UserProvisioningStatus.RESTORED
    )
    assert response.provisioning_status == expected_status
    assert response.created_new_user is False
    assert response.user_id == 11
    assert response.group.id == 3


@pytest.mark.asyncio
async def test_add_user_to_group_by_email_conflict_propagates():
    """Test that 409 CONFLICT is handled gracefully when user already in group.
    
    When add_member_to_group raises 409, the method should:
    1. Catch the 409
    2. Fetch the group directly to continue provisioning
    3. Ensure workspace provisioning continues without raising
    """
    import datetime
    
    mock_group_service = MagicMock()
    mock_user_service = MagicMock()
    mock_admin_repo = MagicMock()
    mock_workspace_service = MagicMock()

    provisioned_user = UserModel(
        id=12,
        email="duplicate@example.com",
        roles=[UserRoleEnum.USER],
        name="Duplicate User",
    )
    admin_user = UserModel(
        id=1,
        email="owner@example.com",
        roles=[UserRoleEnum.ADMIN],
        name="Owner",
    )
    
    group = GroupModel(
        id=3,
        name="Test Group",
        shared_workspace_id=10,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )

    mock_user_service.create_or_restore_user_by_email_for_admin = AsyncMock(
        return_value=(provisioned_user, "existing")
    )
    mock_group_service.add_member_to_group = AsyncMock(
        side_effect=HTTPException(
            status_code=409,
            detail="User is already a member of this group.",
        )
    )
    mock_group_service.group_repo = MagicMock()
    mock_group_service.group_repo.get_by_id_with_members = AsyncMock(
        return_value=group
    )
    
    # Mock workspace service methods to be non-blocking
    mock_workspace_service.workspace_repo = MagicMock()
    mock_workspace_service.workspace_repo.is_member = AsyncMock(return_value=True)
    mock_workspace_service.workspace_repo.find_by_name = AsyncMock(return_value=None)
    mock_workspace_service.create_workspace = AsyncMock(
        return_value=MagicMock(id=11, name="duplicate@example.com")
    )

    service = AdminService(
        admin_repo=mock_admin_repo,
        group_service=mock_group_service,
        user_service=mock_user_service,
        workspace_service=mock_workspace_service,
    )

    # Should NOT raise exception despite 409
    response = await service.add_user_to_group_by_email(
        group_id=3,
        email="duplicate@example.com",
        role="member",
        admin_user=admin_user,
    )

    # Verify the method completed successfully
    assert response.user_id == 12
    assert response.email == "duplicate@example.com"
    assert response.group.id == 3
    
    # Verify group was fetched after 409
    mock_group_service.group_repo.get_by_id_with_members.assert_called_once_with(3)
