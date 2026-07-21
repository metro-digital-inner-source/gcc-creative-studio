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

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bootstrap.bootstrap import (
    _has_admin_role,
    ensure_bootstrap_admin_workspaces,
    ensure_personal_private_workspace,
    resolve_bootstrap_admin_email,
)
from src.users.user_model import UserRoleEnum


class TestResolveBootstrapAdminEmail:
    def test_uses_admin_user_email_when_set(self):
        with patch("bootstrap.bootstrap.config_service") as mock_config:
            mock_config.ADMIN_USER_EMAIL = "Admin@Example.com"
            mock_config.ADMIN_OWNER_EMAILS = {"owner@example.com"}

            assert resolve_bootstrap_admin_email() == "admin@example.com"

    def test_uses_first_owner_email_when_system_admin(self):
        with patch("bootstrap.bootstrap.config_service") as mock_config:
            mock_config.ADMIN_USER_EMAIL = "system"
            mock_config.ADMIN_OWNER_EMAILS = {
                "zeta@example.com",
                "alpha@example.com",
            }

            assert resolve_bootstrap_admin_email() == "alpha@example.com"

    def test_returns_none_when_unconfigured(self):
        with patch("bootstrap.bootstrap.config_service") as mock_config:
            mock_config.ADMIN_USER_EMAIL = "system"
            mock_config.ADMIN_OWNER_EMAILS = set()

            assert resolve_bootstrap_admin_email() is None


class TestHasAdminRole:
    def test_detects_admin_role(self):
        assert _has_admin_role([UserRoleEnum.USER, UserRoleEnum.ADMIN]) is True
        assert _has_admin_role(["user"]) is False


@pytest.mark.asyncio
async def test_ensure_bootstrap_admin_workspaces_provisions_group_and_personal_workspace():
    admin_user = SimpleNamespace(
        id=1,
        email="admin@example.com",
        roles=[UserRoleEnum.USER, UserRoleEnum.ADMIN],
    )
    db = AsyncMock()
    ai_enabler_group = SimpleNamespace(id=99, name="AI Enabler")

    with patch(
        "bootstrap.bootstrap.ensure_admin_user_has_admin_role",
        new=AsyncMock(return_value=admin_user),
    ) as mock_promote, patch(
        "bootstrap.bootstrap.build_group_service",
    ) as mock_build_group_service, patch(
        "bootstrap.bootstrap.ensure_personal_private_workspace",
        new=AsyncMock(),
    ) as mock_personal:
        group_service = MagicMock()
        group_service.ensure_admin_access_to_ai_enabler = AsyncMock(
            return_value=ai_enabler_group
        )
        mock_build_group_service.return_value = group_service

        await ensure_bootstrap_admin_workspaces(db, admin_user)

        mock_promote.assert_awaited_once_with(db, admin_user)
        group_service.ensure_admin_access_to_ai_enabler.assert_awaited_once_with(
            admin_user
        )
        mock_personal.assert_awaited_once_with(db, admin_user)


@pytest.mark.asyncio
async def test_ensure_personal_private_workspace_creates_missing_workspace():
    admin_user = SimpleNamespace(
        id=7,
        email="Admin@Example.com",
    )
    workspace_service = MagicMock()
    workspace_service.workspace_repo.find_by_name = AsyncMock(return_value=None)
    workspace_service.create_workspace = AsyncMock(
        return_value=SimpleNamespace(id=42)
    )

    with patch(
        "bootstrap.bootstrap.build_workspace_service",
        return_value=workspace_service,
    ):
        await ensure_personal_private_workspace(AsyncMock(), admin_user)

    workspace_service.create_workspace.assert_awaited_once()
    create_dto = workspace_service.create_workspace.await_args.args[1]
    assert create_dto.name == "admin@example.com"
