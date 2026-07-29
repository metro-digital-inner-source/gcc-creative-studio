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
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.base_repository import BaseDocument
from src.database import Base


class GroupMemberRoleEnum(str, Enum):
    """Defines the roles a user can have within a group."""

    MEMBER = "member"
    ADMIN = "admin"


class Group(Base):
    """SQLAlchemy model for the 'groups' table.

    Groups provide governance and organizational boundaries.
    Each group has a 1:1 relationship with a shared workspace.
    """

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    country_code: Mapped[str | None] = mapped_column(String, nullable=True)
    shared_workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id"), nullable=False, unique=True
    )

    # Relationships
    shared_workspace: Mapped["Workspace"] = relationship(  # type: ignore
        foreign_keys=[shared_workspace_id],
        lazy="selectin",
    )
    members: Mapped[list["GroupMember"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

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


class GroupMember(Base):
    """SQLAlchemy model for the 'group_members' table.

    Association table for the many-to-many relationship between
    Users and Groups, storing the role of the user in the group.
    """

    __tablename__ = "group_members"

    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    joined_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.now(),
        server_default=func.now(),
    )

    # Relationships
    group: Mapped["Group"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(lazy="selectin")  # type: ignore


class GroupUsageDaily(Base):
    """SQLAlchemy model for the 'group_usage_daily' table.

    Stores daily aggregated usage metrics per group for analytics.
    """

    __tablename__ = "group_usage_daily"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"), nullable=False
    )
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    spend_usd: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2), server_default="0", nullable=False
    )
    tokens_consumed: Mapped[int] = mapped_column(
        BigInteger, server_default="0", nullable=False
    )
    activity_count: Mapped[int] = mapped_column(
        server_default="0", nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.now(),
        server_default=func.now(),
    )

    # Relationships
    group: Mapped["Group"] = relationship(lazy="selectin")


# Pydantic DTOs for API responses


class GroupMemberModel(BaseModel):
    """DTO for a group member."""

    user_id: int = Field(description="The User ID of the member.")
    email: str = Field(description="The member's email (denormalized).")
    name: str = Field(description="The member's display name.")
    role: GroupMemberRoleEnum = Field(default=GroupMemberRoleEnum.MEMBER)
    joined_at: datetime.datetime

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        from_attributes=True,
    )


class GroupModel(BaseDocument):
    """DTO for a group."""

    id: int
    name: str
    country_code: str | None = None
    shared_workspace_id: int
    members: list[GroupMemberModel] = Field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class GroupUsageDailyModel(BaseDocument):
    """DTO for daily group usage metrics."""

    id: int
    group_id: int
    date: datetime.date
    spend_usd: float
    tokens_consumed: int
    activity_count: int
    created_at: datetime.datetime
