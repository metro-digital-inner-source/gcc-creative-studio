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

from email.utils import parseaddr

from pydantic import BaseModel, field_validator


class AllowlistCreateDto(BaseModel):
    """DTO for creating a new allowlist entry.
    
    Must provide either email or domain (or both).
    """

    email: str | None = None
    domain: str | None = None
    notes: str = ""

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v:
            normalized = v.strip()
            _, parsed_email = parseaddr(normalized)
            if (
                parsed_email != normalized
                or "@" not in normalized
                or normalized.startswith("@")
                or normalized.endswith("@")
                or " " in normalized
            ):
                raise ValueError(f"Invalid email format: {v}")
        return v

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v):
        if v:
            # Basic domain validation (lowercase, no spaces)
            if " " in v or not v.strip():
                raise ValueError("Domain cannot contain spaces")
            v = v.lower().strip()
        return v

    @property
    def is_valid(self) -> bool:
        """At least one of email or domain must be provided."""
        return bool(self.email or self.domain)


class AllowlistUpdateDto(BaseModel):
    """DTO for updating an allowlist entry."""

    is_active: bool | None = None
    notes: str | None = None
