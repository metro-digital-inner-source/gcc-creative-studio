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

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from src.auth.auth_guard import RoleChecker, get_current_user
from src.config.config_service import config_service
from src.users.user_model import UserModel, UserRoleEnum


@pytest.fixture(name="mock_user_service")
def fixture_mock_user_service():
    service = AsyncMock()
    # Mock create_user_if_not_exists to return a user
    service.create_user_if_not_exists.return_value = UserModel(
        id=1,
        email="test@example.com",
        roles=["user"],
        name="Test User",
    )
    return service


@pytest.fixture(name="mock_request")
def fixture_mock_request():
    class MockRequest:
        def __init__(self, headers=None):
            self.headers = headers or {}

    return MockRequest()


@pytest.fixture(autouse=True)
def fixture_reset_config_service():
    original_environment = config_service.ENVIRONMENT
    original_allowed_orgs = config_service.ALLOWED_ORGS_STR
    original_allowed_emails = config_service.ALLOWED_EMAILS_STR
    yield
    config_service.ENVIRONMENT = original_environment
    config_service.ALLOWED_ORGS_STR = original_allowed_orgs
    config_service.ALLOWED_EMAILS_STR = original_allowed_emails


@pytest.fixture(name="mock_allowlist_service")
def fixture_mock_allowlist_service():
    service = AsyncMock()
    service.check_email_allowed.return_value = False
    service.has_active_entries.return_value = False
    return service


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.anyio
    @patch("src.auth.auth_guard.auth.verify_id_token")
    async def test_get_current_user_local_success(
        self,
        mock_verify,
        mock_user_service,
        mock_request,
        mock_allowlist_service,
    ):
        # Setup: Local environment
        config_service.ENVIRONMENT = "local"
        config_service.ALLOWED_ORGS_STR = ""
        config_service.ALLOWED_EMAILS_STR = ""

        mock_allowlist_service.check_email_allowed.return_value = False
        mock_allowlist_service.has_active_entries.return_value = False

        # Mock token verification
        mock_verify.return_value = {
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://example.com/pic.jpg",
            "hd": "example.com",
        }

        user = await get_current_user(
            request=mock_request,
            token="valid_token",
            user_service=mock_user_service,
            allowlist_service=mock_allowlist_service,
        )

        assert user.email == "test@example.com"
        assert user.name == "Test User"
        mock_user_service.create_user_if_not_exists.assert_called_once_with(
            email="test@example.com",
            name="Test User",
            picture="http://example.com/pic.jpg",
        )

    @pytest.mark.anyio
    @patch("src.auth.auth_guard.auth.verify_id_token")
    async def test_get_current_user_no_email(
        self,
        mock_verify,
        mock_user_service,
        mock_request,
        mock_allowlist_service,
    ):
        config_service.ENVIRONMENT = "local"
        config_service.ALLOWED_ORGS_STR = ""
        config_service.ALLOWED_EMAILS_STR = ""
        mock_verify.return_value = {"name": "Test User"}  # Missing email

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request=mock_request,
                token="valid_token",
                user_service=mock_user_service,
                allowlist_service=mock_allowlist_service,
            )

        assert exc_info.value.status_code == 403
        assert "User identity could not be confirmed" in exc_info.value.detail

    @pytest.mark.anyio
    @patch("src.auth.auth_guard.auth.verify_id_token")
    async def test_get_current_user_allowed_orgs_fail(
        self,
        mock_verify,
        mock_user_service,
        mock_request,
        mock_allowlist_service,
    ):
        config_service.ENVIRONMENT = "local"
        config_service.ALLOWED_ORGS_STR = "allowed.com"
        config_service.ALLOWED_EMAILS_STR = ""
        mock_allowlist_service.check_email_allowed.return_value = False

        mock_verify.return_value = {
            "email": "test@example.com",
            "name": "Test User",
            "hd": "forbidden.com",
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request=mock_request,
                token="valid_token",
                user_service=mock_user_service,
                allowlist_service=mock_allowlist_service,
            )

        assert exc_info.value.status_code == 401
        assert (
            "User is not authorized to access this application."
            in exc_info.value.detail
        )

    @pytest.mark.anyio
    @patch("src.auth.auth_guard.auth.verify_id_token")
    async def test_get_current_user_db_allowlist_only_rejects_unlisted_user(
        self,
        mock_verify,
        mock_user_service,
        mock_request,
        mock_allowlist_service,
    ):
        config_service.ENVIRONMENT = "local"
        config_service.ALLOWED_ORGS_STR = ""
        config_service.ALLOWED_EMAILS_STR = ""
        mock_allowlist_service.check_email_allowed.return_value = False
        mock_allowlist_service.has_active_entries.return_value = True

        mock_verify.return_value = {
            "email": "test@example.com",
            "name": "Test User",
            "hd": "example.com",
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request=mock_request,
                token="valid_token",
                user_service=mock_user_service,
                allowlist_service=mock_allowlist_service,
            )

        assert exc_info.value.status_code == 401
        mock_user_service.create_user_if_not_exists.assert_not_called()

    @pytest.mark.anyio
    @patch("src.auth.auth_guard.auth.verify_id_token")
    async def test_get_current_user_db_allowlist_only_allows_listed_user(
        self,
        mock_verify,
        mock_user_service,
        mock_request,
        mock_allowlist_service,
    ):
        config_service.ENVIRONMENT = "local"
        config_service.ALLOWED_ORGS_STR = ""
        config_service.ALLOWED_EMAILS_STR = ""
        mock_allowlist_service.check_email_allowed.return_value = True

        mock_verify.return_value = {
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://example.com/pic.jpg",
            "hd": "example.com",
        }

        user = await get_current_user(
            request=mock_request,
            token="valid_token",
            user_service=mock_user_service,
            allowlist_service=mock_allowlist_service,
        )

        assert user.email == "test@example.com"
        mock_allowlist_service.has_active_entries.assert_not_called()

    @pytest.mark.anyio
    @patch("src.auth.auth_guard.auth.verify_id_token")
    async def test_get_current_user_env_fallback_allows_matching_email(
        self,
        mock_verify,
        mock_user_service,
        mock_request,
        mock_allowlist_service,
    ):
        config_service.ENVIRONMENT = "local"
        config_service.ALLOWED_ORGS_STR = ""
        config_service.ALLOWED_EMAILS_STR = "test@example.com"
        mock_allowlist_service.check_email_allowed.return_value = False

        mock_verify.return_value = {
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://example.com/pic.jpg",
            "hd": "example.com",
        }

        user = await get_current_user(
            request=mock_request,
            token="valid_token",
            user_service=mock_user_service,
            allowlist_service=mock_allowlist_service,
        )

        assert user.email == "test@example.com"
        mock_allowlist_service.has_active_entries.assert_not_called()

    @pytest.mark.anyio
    @patch("src.auth.auth_guard.auth.verify_id_token")
    async def test_get_current_user_env_fallback_is_case_insensitive(
        self,
        mock_verify,
        mock_user_service,
        mock_request,
        mock_allowlist_service,
    ):
        config_service.ENVIRONMENT = "local"
        config_service.ALLOWED_ORGS_STR = ""
        config_service.ALLOWED_EMAILS_STR = "Test@Example.com"
        mock_allowlist_service.check_email_allowed.return_value = False

        mock_verify.return_value = {
            "email": "TEST@EXAMPLE.COM",
            "name": "Test User",
            "picture": "http://example.com/pic.jpg",
            "hd": "EXAMPLE.COM",
        }

        user = await get_current_user(
            request=mock_request,
            token="valid_token",
            user_service=mock_user_service,
            allowlist_service=mock_allowlist_service,
        )

        assert user.email == "test@example.com"

    @pytest.mark.anyio
    @patch("src.auth.auth_guard.auth.verify_id_token")
    async def test_get_current_user_db_check_failure_without_env_fails_closed(
        self,
        mock_verify,
        mock_user_service,
        mock_request,
        mock_allowlist_service,
    ):
        config_service.ENVIRONMENT = "local"
        config_service.ALLOWED_ORGS_STR = ""
        config_service.ALLOWED_EMAILS_STR = ""
        mock_allowlist_service.check_email_allowed.side_effect = RuntimeError(
            "db unavailable"
        )

        mock_verify.return_value = {
            "email": "test@example.com",
            "name": "Test User",
            "hd": "example.com",
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request=mock_request,
                token="valid_token",
                user_service=mock_user_service,
                allowlist_service=mock_allowlist_service,
            )

        assert exc_info.value.status_code == 503
        assert "Authorization service temporarily unavailable" in exc_info.value.detail
        mock_user_service.create_user_if_not_exists.assert_not_called()


class TestRoleChecker:
    """Tests for RoleChecker class."""

    def test_role_checker_authorized(self):
        checker = RoleChecker(allowed_roles=[UserRoleEnum.ADMIN])
        user = UserModel(
            id=1,
            email="admin@example.com",
            roles=["admin"],
            name="Admin User",
        )

        # Should not raise exception
        checker(user=user)

    def test_role_checker_forbidden(self):
        checker = RoleChecker(allowed_roles=[UserRoleEnum.ADMIN])
        user = UserModel(
            id=1,
            email="user@example.com",
            roles=["user"],
            name="Regular User",
        )

        with pytest.raises(HTTPException) as exc_info:
            checker(user=user)

        assert exc_info.value.status_code == 403
        assert "do not have sufficient permissions" in exc_info.value.detail
