from datetime import datetime, timezone

from beanie import Document
from pydantic import Field


class Category(Document):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    isActive: bool = True
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "categories"
        indexes = ["isActive"]
