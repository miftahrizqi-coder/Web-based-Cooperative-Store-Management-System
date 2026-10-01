from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import Field


class MemberStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Member(Document):
    memberNumber: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=1, max_length=30)
    email: str | None = Field(default=None, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    joinedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: MemberStatus = MemberStatus.ACTIVE
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "members"
        # memberNumber: index unik dibuat di core/database.py
        indexes = [
            "name",
            "status",
        ]