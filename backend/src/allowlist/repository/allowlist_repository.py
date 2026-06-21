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

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.allowlist.allowlist_model import AllowlistEntry, AllowlistEntryModel
from src.common.base_repository import BaseRepository
from src.database import get_db


class AllowlistRepository(BaseRepository[AllowlistEntry, AllowlistEntryModel]):
    """Repository for allowlist entry operations."""

    def __init__(self, db: AsyncSession = Depends(get_db)):
        super().__init__(
            model=AllowlistEntry, schema=AllowlistEntryModel, db=db
        )

    async def get_by_email(self, email: str) -> AllowlistEntryModel | None:
        """Retrieve an allowlist entry by exact email."""
        query = select(AllowlistEntry).where(
            AllowlistEntry.email == email.lower()
        )
        result = await self.db.execute(query)
        entry = result.scalar_one_or_none()
        return (
            AllowlistEntryModel.model_validate(entry) if entry else None
        )

    async def get_active_entries(self) -> list[AllowlistEntryModel]:
        """Retrieve all active allowlist entries.
        
        Used for caching purposes.
        """
        query = select(AllowlistEntry).where(
            AllowlistEntry.is_active == True
        )
        result = await self.db.execute(query)
        entries = result.scalars().all()
        return [
            AllowlistEntryModel.model_validate(entry) for entry in entries
        ]

    async def check_allowed(
        self, email: str, domain: str | None = None
    ) -> bool:
        """Check if an email or domain is allowed.
        
        Returns True if:
        - Email exact match exists and is active, OR
        - Domain match exists and is active
        """
        # Check email
        query_email = select(AllowlistEntry).where(
            AllowlistEntry.email == email.lower(),
            AllowlistEntry.is_active == True,
        )
        result = await self.db.execute(query_email)
        if result.scalar_one_or_none():
            return True

        # Check domain
        if domain:
            query_domain = select(AllowlistEntry).where(
                AllowlistEntry.domain == domain.lower(),
                AllowlistEntry.is_active == True,
            )
            result = await self.db.execute(query_domain)
            if result.scalar_one_or_none():
                return True

        return False
