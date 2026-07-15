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
"""Tests for BrandGuidelineService workspace scope and permissions."""


from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.brand_guidelines.brand_guideline_service import BrandGuidelineService
from src.brand_guidelines.schema.brand_guideline_model import (
    BrandGuidelineModel,
)
from src.common.schema.media_item_model import JobStatusEnum
from src.workspaces.schema.workspace_model import WorkspaceModel, WorkspaceScopeEnum


@pytest.fixture(name="mock_brand_guideline_repo")
def fixture_mock_brand_guideline_repo():
    repo = AsyncMock()
    repo.query = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture(name="mock_workspace_repo")
def fixture_mock_workspace_repo():
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.is_member = AsyncMock(return_value=False)
    return repo


@pytest.fixture(name="mock_signer")
def fixture_mock_signer():
    signer = MagicMock()
    signer.generate_presigned_url.return_value = "https://signed-url"
    return signer


@pytest.fixture(name="brand_guideline_service")
def fixture_brand_guideline_service(
    mock_brand_guideline_repo,
    mock_workspace_repo,
    mock_signer,
):
    return BrandGuidelineService(
        repo=mock_brand_guideline_repo,
        gcs_service=MagicMock(),
        gemini_service=MagicMock(),
        workspace_repo=mock_workspace_repo,
        iam_signer_credentials=mock_signer,
    )


class TestWorkspaceScopedGuidelines:
    """Workspace isolation tests for brand guidelines."""

    @pytest.mark.anyio
    async def test_get_guideline_by_workspace_keeps_workspaces_independent(
        self,
        brand_guideline_service,
        mock_brand_guideline_repo,
        mock_workspace_repo,
        mock_admin,
    ):
        workspace_one = WorkspaceModel(
            id=10,
            name="Workspace One",
            owner_id=1,
            scope=WorkspaceScopeEnum.PRIVATE,
        )
        workspace_two = WorkspaceModel(
            id=11,
            name="Workspace Two",
            owner_id=2,
            scope=WorkspaceScopeEnum.PRIVATE,
        )
        guideline_one = BrandGuidelineModel(
            id=100,
            name="Guideline One",
            workspace_id=10,
            status=JobStatusEnum.COMPLETED,
            source_pdf_gcs_uris=["gs://bucket/one.pdf"],
        )
        guideline_two = BrandGuidelineModel(
            id=101,
            name="Guideline Two",
            workspace_id=11,
            status=JobStatusEnum.COMPLETED,
            source_pdf_gcs_uris=["gs://bucket/two.pdf"],
        )

        mock_workspace_repo.get_by_id.side_effect = [workspace_one, workspace_two]
        mock_brand_guideline_repo.query.side_effect = [
            SimpleNamespace(data=[guideline_one]),
            SimpleNamespace(data=[guideline_two]),
        ]

        result_one = await brand_guideline_service.get_guideline_by_workspace_id(
            10,
            mock_admin,
        )
        result_two = await brand_guideline_service.get_guideline_by_workspace_id(
            11,
            mock_admin,
        )

        assert result_one.workspace_id == 10
        assert result_one.name == "Guideline One"
        assert result_two.workspace_id == 11
        assert result_two.name == "Guideline Two"


class TestWorkspacePermissions:
    """Owner/admin permission checks for workspace-scoped guidelines."""

    @pytest.mark.anyio
    async def test_start_processing_denies_non_owner_non_admin(
        self,
        brand_guideline_service,
        mock_workspace_repo,
        mock_user,
    ):
        workspace = WorkspaceModel(
            id=20,
            name="Private Workspace",
            owner_id=999,
            scope=WorkspaceScopeEnum.PRIVATE,
        )
        mock_workspace_repo.get_by_id.return_value = workspace

        with pytest.raises(HTTPException) as exc_info:
            await brand_guideline_service.start_brand_guideline_processing_job(
                name="Retail Guide",
                workspace_id=20,
                gcs_uri="gs://bucket/file.pdf",
                original_filename="file.pdf",
                current_user=mock_user,
                executor=MagicMock(),
            )

        assert exc_info.value.status_code == 403
        assert "workspace owner or a system admin" in exc_info.value.detail

    @pytest.mark.anyio
    async def test_delete_guideline_denies_non_owner_non_admin(
        self,
        brand_guideline_service,
        mock_brand_guideline_repo,
        mock_workspace_repo,
        mock_user,
    ):
        guideline = BrandGuidelineModel(
            id=200,
            name="Workspace Guideline",
            workspace_id=30,
            status=JobStatusEnum.COMPLETED,
            source_pdf_gcs_uris=["gs://bucket/w.pdf"],
        )
        workspace = WorkspaceModel(
            id=30,
            name="Workspace",
            owner_id=500,
            scope=WorkspaceScopeEnum.PRIVATE,
        )
        mock_brand_guideline_repo.get_by_id.return_value = guideline
        mock_workspace_repo.get_by_id.return_value = workspace

        with pytest.raises(HTTPException) as exc_info:
            await brand_guideline_service.delete_guideline(200, mock_user)

        assert exc_info.value.status_code == 403
        assert "workspace owner or a system admin" in exc_info.value.detail

    @pytest.mark.anyio
    async def test_delete_guideline_allows_admin(
        self,
        brand_guideline_service,
        mock_brand_guideline_repo,
        mock_workspace_repo,
        mock_admin,
    ):
        guideline = BrandGuidelineModel(
            id=201,
            name="Workspace Guideline",
            workspace_id=31,
            status=JobStatusEnum.COMPLETED,
            source_pdf_gcs_uris=["gs://bucket/x.pdf"],
        )
        workspace = WorkspaceModel(
            id=31,
            name="Workspace",
            owner_id=500,
            scope=WorkspaceScopeEnum.PRIVATE,
        )
        mock_brand_guideline_repo.get_by_id.return_value = guideline
        mock_workspace_repo.get_by_id.return_value = workspace
        brand_guideline_service._delete_guideline_and_assets = AsyncMock()

        await brand_guideline_service.delete_guideline(201, mock_admin)

        brand_guideline_service._delete_guideline_and_assets.assert_called_once_with(
            guideline
        )
