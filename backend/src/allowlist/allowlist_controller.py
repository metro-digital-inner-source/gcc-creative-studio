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

from src.allowlist.allowlist_model import AllowlistEntryModel
from src.allowlist.allowlist_service import AllowlistService
from src.allowlist.dto.allowlist_create_dto import (
    AllowlistCreateDto,
    AllowlistUpdateDto,
)
from src.auth.auth_guard import RoleChecker, get_current_user
from src.common.dto.pagination_response_dto import PaginationResponseDto
from src.users.user_model import UserModel, UserRoleEnum

# Role-based access control
admin_only = Depends(RoleChecker(allowed_roles=[UserRoleEnum.ADMIN]))

router = APIRouter(
    prefix="/api/admin/allowlist",
    tags=["Admin - Allowlist"],
)


@router.post(
    "",
    response_model=AllowlistEntryModel,
    status_code=status.HTTP_201_CREATED,
    summary="Add Email or Domain to Allowlist (Admin Only)",
    dependencies=[admin_only],
)
async def create_allowlist_entry(
    entry_dto: AllowlistCreateDto,
    current_user: UserModel = Depends(get_current_user),
    allowlist_service: AllowlistService = Depends(),
):
    """Create a new allowlist entry for an email or domain.
    
    Must provide either 'email' or 'domain' (or both).
    Admin-only access.
    """
    try:
        return await allowlist_service.create_allowlist_entry(
            entry_dto, current_user
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=list[AllowlistEntryModel],
    summary="List Allowlist Entries (Admin Only)",
    dependencies=[admin_only],
)
async def list_allowlist_entries(
    active_only: bool = True,
    allowlist_service: AllowlistService = Depends(),
):
    """List all allowlist entries.
    
    Query Parameters:
    - active_only: If true (default), only return active entries
    
    Admin-only access.
    """
    return await allowlist_service.list_allowlist_entries(
        active_only=active_only
    )


@router.get(
    "/{entry_id}",
    response_model=AllowlistEntryModel,
    summary="Get Allowlist Entry (Admin Only)",
    dependencies=[admin_only],
)
async def get_allowlist_entry(
    entry_id: int,
    allowlist_service: AllowlistService = Depends(),
):
    """Retrieve a specific allowlist entry by ID.
    
    Admin-only access.
    """
    entry = await allowlist_service.allowlist_repo.get_by_id(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allowlist entry not found.",
        )
    return entry


@router.put(
    "/{entry_id}",
    response_model=AllowlistEntryModel,
    summary="Update Allowlist Entry (Admin Only)",
    dependencies=[admin_only],
)
async def update_allowlist_entry(
    entry_id: int,
    update_dto: AllowlistUpdateDto,
    current_user: UserModel = Depends(get_current_user),
    allowlist_service: AllowlistService = Depends(),
):
    """Update an allowlist entry.
    
    Can toggle active status or update notes.
    Admin-only access.
    """
    return await allowlist_service.update_allowlist_entry(
        entry_id, update_dto, current_user
    )


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate Allowlist Entry (Admin Only)",
    dependencies=[admin_only],
)
async def delete_allowlist_entry(
    entry_id: int,
    current_user: UserModel = Depends(get_current_user),
    allowlist_service: AllowlistService = Depends(),
):
    """Deactivate an allowlist entry (soft delete).
    
    Admin-only access.
    """
    await allowlist_service.delete_allowlist_entry(
        entry_id, current_user
    )


@router.post(
    "/cache/clear",
    status_code=status.HTTP_200_OK,
    summary="Force Clear Allowlist Cache (Admin Only)",
    dependencies=[admin_only],
)
async def clear_allowlist_cache(
    allowlist_service: AllowlistService = Depends(),
):
    """Force clear the allowlist in-memory cache.
    
    Use this if you need immediate effect without waiting for cache TTL.
    Admin-only access.
    """
    await allowlist_service.clear_cache_force()
    return {"message": "Allowlist cache cleared successfully"}
