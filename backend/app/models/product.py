from datetime import datetime, timezone

from beanie import Document
from pydantic import Field


class Product(Document):
    sku: str = Field(min_length=1, max_length=50)
    barcode: str | None = Field(default=None, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    category_id: str
    unit: str = Field(min_length=1, max_length=30)

    purchase_price: float = Field(ge=0)
    selling_price: float = Field(ge=0)
    stock: float = Field(ge=0)
    minimum_stock: float = Field(ge=0)

    is_active: bool = True

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "products"
        indexes = [
            "sku",
            "barcode",
            "category_id",
            "is_active",
        ]
