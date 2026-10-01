from datetime import datetime, timezone

from beanie import Document
from pydantic import Field


class Product(Document):
    """Skema sesuai PRD §10 (camelCase). Data lama snake_case dimigrasi
    otomatis saat startup (lihat core/database.py:migrate_legacy_data)."""

    sku: str = Field(min_length=1, max_length=50)
    barcode: str | None = Field(default=None, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    categoryId: str
    unit: str = Field(min_length=1, max_length=30)

    purchasePrice: float = Field(ge=0)
    sellingPrice: float = Field(ge=0)
    stock: float = Field(default=0, ge=0)
    minimumStock: float = Field(default=0, ge=0)

    isActive: bool = True

    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "products"
        # sku & barcode (unik) serta name (text) dibuat di core/database.py
        indexes = [
            "categoryId",
            "isActive",
            "name",
        ]
