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

import logging
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status

from src.allowlist.allowlist_model import AllowlistEntry, AllowlistEntryModel
from src.allowlist.dto.allowlist_create_dto import (
    AllowlistCreateDto,
    AllowlistUpdateDto,
)
from src.allowlist.repository.allowlist_repository import (
    AllowlistRepository,
)
from src.users.user_model import UserModel

logger = logging.getLogger(__name__)


class AllowlistService:
    """Service for managing allowlist entries with caching."""

    # In-memory cache: (active_entries, cache_timestamp)
    _cache: dict | None = None
    _cache_timestamp: datetime | None = None
    _cache_ttl: timedelta = timedelta(seconds=60)  # 60-second cache

    def __init__(
        self, allowlist_repo: AllowlistRepository = Depends()
    ):
        self.allowlist_repo = allowlist_repo

    async def create_allowlist_entry(
        self,
        entry_dto: AllowlistCreateDto,
        current_user: UserModel,
    ) -> AllowlistEntryModel:
        """Create a new allowlist entry.
        
        Args:
            entry_dto: The allowlist entry data
            current_user: The user creating the entry (for audit)
            
        Returns:
            The created allowlist entry
            
        Raises:
            ValueError: If neither email nor domain is provided
            HTTPException: If entry already exists
        """
        if not entry_dto.is_valid:
            raise ValueError(
                "At least one of 'email' or 'domain' must be provided"
            )

        # Normalize email
        email = (
            entry_dto.email.lower().strip()
            if entry_dto.email
            else None
        )

        # Normalize domain
        domain = (
            entry_dto.domain.lower().strip()
            if entry_dto.domain
            else None
        )

        # Check if email already exists
        if email:
            existing = await self.allowlist_repo.get_by_email(email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Allowlist entry for email '{email}' already exists.",
                )

        # Create entry
        entry_data = {
            "email": email,
            "domain": domain,
            "notes": entry_dto.notes,
            "is_active": True,
            "created_by": current_user.id,
        }

        created_entry = await self.allowlist_repo.create(entry_data)
        
        # Invalidate cache
        self._invalidate_cache()
        
        logger.info(
            f"Created allowlist entry: email={email}, domain={domain}, created_by={current_user.id}"
        )

        return created_entry

    async def update_allowlist_entry(
        self,
        entry_id: int,
        update_dto: AllowlistUpdateDto,
        current_user: UserModel,
    ) -> AllowlistEntryModel:
        """Update an allowlist entry.
        
        Args:
            entry_id: The allowlist entry ID
            update_dto: The update data
            current_user: The user performing the update
            
        Returns:
            The updated allowlist entry
            
        Raises:
            HTTPException: If entry not found
        """
        entry = await self.allowlist_repo.get_by_id(entry_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Allowlist entry not found.",
            )

        # Build update dict with only provided fields
        update_dict = {}
        if update_dto.is_active is not None:
            update_dict["is_active"] = update_dto.is_active
        if update_dto.notes is not None:
            update_dict["notes"] = update_dto.notes

        if not update_dict:
            return entry  # Nothing to update

        updated_entry = await self.allowlist_repo.update(
            entry_id, update_dict
        )
        
        # Invalidate cache
        self._invalidate_cache()
        
        logger.info(
            f"Updated allowlist entry {entry_id}: {update_dict}, updated_by={current_user.id}"
        )

        return updated_entry

    async def delete_allowlist_entry(
        self,
        entry_id: int,
        current_user: UserModel,
    ) -> bool:
        """Soft-delete an allowlist entry by deactivating it.
        
        Args:
            entry_id: The allowlist entry ID
            current_user: The user performing the delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            HTTPException: If entry not found
        """
        entry = await self.allowlist_repo.get_by_id(entry_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Allowlist entry not found.",
            )

        await self.allowlist_repo.update(
            entry_id, {"is_active": False}
        )
        
        # Invalidate cache
        self._invalidate_cache()
        
        logger.info(f"Deleted allowlist entry {entry_id}, deleted_by={current_user.id}")

        return True

    async def check_email_allowed(
        self, email: str, domain: str | None = None
    ) -> bool:
        """Check if an email/domain is allowed (with caching).
        
        Args:
            email: The email to check
            domain: Optional domain extracted from email (e.g., domain from email@domain.com)
            
        Returns:
            True if email is in allowlist, False otherwise
        """
        # Try database check first (most accurate)
        return await self.allowlist_repo.check_allowed(email, domain)

    async def list_allowlist_entries(
        self, active_only: bool = True
    ) -> list[AllowlistEntryModel]:
        """List all allowlist entries (with optional active filter).
        
        Args:
            active_only: If True, only return active entries
            
        Returns:
            List of allowlist entries
        """
        if active_only:
            return await self.allowlist_repo.get_active_entries()
        else:
            return await self.allowlist_repo.get_all()

    def _invalidate_cache(self) -> None:
        """Invalidate the in-memory cache."""
        self.__class__._cache = None
        self.__class__._cache_timestamp = None
        logger.debug("Allowlist cache invalidated")

    async def clear_cache_force(self) -> None:
        """Force clear cache (admin only endpoint)."""
        self._invalidate_cache()
        logger.info("Allowlist cache force cleared")
