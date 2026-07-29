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
"""Tests for Group Service boundary and share/restore flows."""


from datetime import datetime, UTC
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.groups.dto.group_dto import RestoreItemsRequest, ShareItemsRequest
from src.groups.group_service import GroupService
from src.groups.schema.group_model import GroupModel
from src.workspaces.schema.workspace_model import WorkspaceModel


@pytest.fixture(name="mock_group_repo")
def fixture_mock_group_repo():
    return AsyncMock()


@pytest.fixture(name="mock_workspace_service")
def fixture_mock_workspace_service():
    service = AsyncMock()
    service.workspace_repo = AsyncMock()
    return service


@pytest.fixture(name="mock_media_repo")
def fixture_mock_media_repo():
    repo = AsyncMock()
    repo.db = AsyncMock()
    return repo


@pytest.fixture(name="mock_workspace_auth")
def fixture_mock_workspace_auth():
    auth = AsyncMock()
    auth.authorize = AsyncMock()
    return auth


@pytest.fixture(name="group_service")
def fixture_group_service(
    mock_group_repo,
    mock_workspace_service,
    mock_media_repo,
    mock_workspace_auth,
):
    return GroupService(
        group_repo=mock_group_repo,
        workspace_service=mock_workspace_service,
        media_repo=mock_media_repo,
        workspace_auth=mock_workspace_auth,
    )


class TestShareItemsToGroup:
    """Tests for GroupService.share_items_to_group."""

    @pytest.mark.anyio
    async def test_share_items_forbidden_for_non_member(
        self,
        group_service,
        mock_group_repo,
        mock_user,
    ):
        mock_group_repo.is_member.return_value = False
        request = ShareItemsRequest(group_id=10, media_item_ids=[101])

        with pytest.raises(HTTPException) as exc_info:
            await group_service.share_items_to_group(request, mock_user)

        assert exc_info.value.status_code == 403
        assert "must be a member" in exc_info.value.detail

    @pytest.mark.anyio
    async def test_share_items_moves_to_group_shared_workspace(
        self,
        group_service,
        mock_group_repo,
        mock_media_repo,
        mock_workspace_auth,
        mock_user,
    ):
        mock_group_repo.is_member.return_value = True
        mock_group_repo.get_by_id_with_members.return_value = GroupModel(
            id=10,
            name="Retail Team",
            country_code="DE",
            shared_workspace_id=501,
            members=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        media_item = SimpleNamespace(
            id=101,
            deleted_at=None,
            workspace_id=100,
            original_workspace_id=None,
            moved_to_group_id=None,
            user_id=mock_user.id,
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [media_item]
        mock_media_repo.db.execute.return_value = mock_result
        mock_workspace_auth.authorize.return_value = WorkspaceModel(
            id=100,
            name="Private WS",
            owner_id=mock_user.id,
        )

        request = ShareItemsRequest(group_id=10, media_item_ids=[101])
        response = await group_service.share_items_to_group(request, mock_user)

        assert response["shared_workspace_id"] == 501
        assert media_item.original_workspace_id == 100
        assert media_item.workspace_id == 501
        assert media_item.moved_to_group_id == 10
        mock_media_repo.db.commit.assert_called_once()


class TestRestoreItemsFromGroup:
    """Tests for GroupService.restore_items_from_group."""

    @pytest.mark.anyio
    async def test_restore_items_success(
        self,
        group_service,
        mock_media_repo,
        mock_workspace_auth,
        mock_user,
    ):
        media_item = SimpleNamespace(
            id=202,
            deleted_at=None,
            workspace_id=501,
            original_workspace_id=100,
            moved_to_group_id=10,
            user_id=mock_user.id,
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [media_item]
        mock_media_repo.db.execute.return_value = mock_result

        current_workspace = WorkspaceModel(
            id=501,
            name="Group Shared",
            owner_id=88,
        )
        original_workspace = WorkspaceModel(
            id=100,
            name="Private WS",
            owner_id=mock_user.id,
        )
        mock_workspace_auth.authorize.side_effect = [
            current_workspace,
            original_workspace,
        ]

        request = RestoreItemsRequest(media_item_ids=[202])
        response = await group_service.restore_items_from_group(
            request,
            mock_user,
        )

        assert response["item_count"] == 1
        assert media_item.workspace_id == 100
        assert media_item.moved_to_group_id is None
        mock_media_repo.db.commit.assert_called_once()


class TestEnsureAdminAccessToAIEnabler:
    """Tests for automatic admin access to AI Enabler group."""

    @pytest.mark.asyncio
    async def test_ensure_admin_access_creates_ai_enabler_on_first_admin(
        self,
        mock_group_repo,
        mock_workspace_service,
        mock_media_repo,
        mock_workspace_auth,
    ):
        """Test that first admin user creates AI Enabler group."""
        from src.users.user_model import UserRoleEnum

        group_service = GroupService(
            group_repo=mock_group_repo,
            workspace_service=mock_workspace_service,
            media_repo=mock_media_repo,
            workspace_auth=mock_workspace_auth,
        )

        admin_user = SimpleNamespace(
            id=1,
            email="admin@example.com",
            roles=[UserRoleEnum.ADMIN],
        )

        # AI Enabler doesn't exist yet
        mock_group_repo.find_ai_enabler_group.return_value = None

        # Mock workspace creation
        workspace = WorkspaceModel(
            id=999, 
            name="AI Enabler Workspace",
            owner_id=1,
        )
        mock_workspace_service.workspace_repo.find_by_name.return_value = None
        mock_workspace_service.create_workspace.return_value = workspace

        # Mock group creation
        ai_enabler_group = GroupModel(
            id=50,
            name="AI Enabler",
            shared_workspace_id=999,
            country_code=None,
            members=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_group_repo.create_group.return_value = ai_enabler_group

        # Mock get_by_id_with_members
        mock_group_repo.get_by_id_with_members.return_value = ai_enabler_group

        # Mock workspace_repo.add_member_to_workspace
        mock_workspace_service.workspace_repo.add_member_to_workspace = AsyncMock()

        result = await group_service.ensure_admin_access_to_ai_enabler(admin_user)

        assert result.id == 50
        assert result.name == "AI Enabler"
        mock_group_repo.find_ai_enabler_group.assert_called_once()
        mock_group_repo.create_group.assert_called_once_with(
            name="AI Enabler",
            shared_workspace_id=999,
            country_code=None,
        )
        mock_group_repo.add_member.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_admin_access_adds_existing_admin_to_ai_enabler(
        self,
        mock_group_repo,
        mock_workspace_service,
        mock_media_repo,
        mock_workspace_auth,
    ):
        """Test that existing admin user is added to existing AI Enabler group."""
        from src.users.user_model import UserRoleEnum
        from src.groups.schema.group_model import GroupMemberRoleEnum

        group_service = GroupService(
            group_repo=mock_group_repo,
            workspace_service=mock_workspace_service,
            media_repo=mock_media_repo,
            workspace_auth=mock_workspace_auth,
        )

        admin_user = SimpleNamespace(
            id=2,
            email="admin2@example.com",
            roles=[UserRoleEnum.ADMIN],
        )

        # AI Enabler already exists
        ai_enabler_group = GroupModel(
            id=50,
            name="AI Enabler",
            shared_workspace_id=999,
            country_code=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_group_repo.find_ai_enabler_group.return_value = ai_enabler_group

        # Mock upsert_group_member
        mock_group_repo.upsert_group_member = AsyncMock(return_value=True)

        # Mock workspace_repo.add_member_to_workspace
        mock_workspace_service.workspace_repo = AsyncMock()
        mock_workspace_service.workspace_repo.add_member_to_workspace = AsyncMock()

        # Mock get_by_id_with_members
        mock_group_repo.get_by_id_with_members.return_value = ai_enabler_group

        result = await group_service.ensure_admin_access_to_ai_enabler(admin_user)

        assert result.id == 50
        mock_group_repo.find_ai_enabler_group.assert_called_once()
        mock_group_repo.upsert_group_member.assert_called_once_with(
            group_id=50,
            user_id=2,
            role=GroupMemberRoleEnum.ADMIN,
        )

    @pytest.mark.asyncio
    async def test_ensure_admin_access_returns_none_for_non_admin(
        self,
        mock_group_repo,
        mock_workspace_service,
        mock_media_repo,
        mock_workspace_auth,
    ):
        """Test that non-admin users are not granted AI Enabler access."""
        from src.users.user_model import UserRoleEnum

        group_service = GroupService(
            group_repo=mock_group_repo,
            workspace_service=mock_workspace_service,
            media_repo=mock_media_repo,
            workspace_auth=mock_workspace_auth,
        )

        non_admin_user = SimpleNamespace(
            id=3,
            email="user@example.com",
            roles=[],  # Not an admin
        )

        result = await group_service.ensure_admin_access_to_ai_enabler(non_admin_user)

        assert result is None
        mock_group_repo.find_ai_enabler_group.assert_not_called()
