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

import datetime

from pydantic import Field, EmailStr
from sqlalchemy import DateTime, String, func, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.common.base_repository import BaseDocument
from src.database import Base


class AllowlistEntry(Base):
    """SQLAlchemy model for the 'allowlist_entries' table.
    
    Supports both email-specific and domain-based allowlisting.
    Allows for gradual migration from env-based to DB-backed allowlist.
    """

    __tablename__ = "allowlist_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Email (exact match allowlist)
    email: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    
    # Domain (e.g., company.com for Google Workspace)
    domain: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    
    # Active status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Metadata
    notes: Mapped[str] = mapped_column(String, default="")
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )


class AllowlistEntryModel(BaseDocument):
    """Represents an allowlist entry (DTO) for the API."""

    id: int
    email: str | None = None
    domain: str | None = None
    is_active: bool = True
    notes: str = ""
    created_by: int | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
