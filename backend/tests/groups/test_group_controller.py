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
"""Tests for Group Controller."""


from datetime import datetime, UTC
from unittest.mock import AsyncMock

import pytest
from main import app

from src.groups.group_service import GroupService
from src.groups.schema.group_model import GroupModel


@pytest.fixture(name="mock_group_service")
def fixture_mock_group_service():
    return AsyncMock()


@pytest.fixture(name="override_group_service", autouse=True)
def fixture_override_group_service(mock_group_service):
    app.dependency_overrides[GroupService] = lambda: mock_group_service
    yield
    if GroupService in app.dependency_overrides:
        del app.dependency_overrides[GroupService]


class TestGetMyGroups:
    """Tests for GET /api/groups/me."""

    def test_get_my_groups_includes_shared_workspace_id(
        self,
        api_client,
        mock_group_service,
    ):
        mock_group_service.get_user_groups.return_value = [
            GroupModel(
                id=1,
                name="Retail Team",
                country_code="DE",
                shared_workspace_id=77,
                members=[],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        ]

        response = api_client.get("/api/groups/me")

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["sharedWorkspaceId"] == 77
