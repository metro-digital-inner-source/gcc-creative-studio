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
