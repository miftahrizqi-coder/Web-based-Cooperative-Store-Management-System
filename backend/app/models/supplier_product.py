from datetime import datetime, timezone

from beanie import Document
from pydantic import Field


class SupplierProduct(Document):
    supplierId: str
    productId: str
    supplierSku: str = Field(min_length=1, max_length=100)
    purchasePrice: float = Field(ge=0)
    minimumOrder: int = Field(ge=1)
    leadTimeDays: int = Field(ge=0)
    isPreferred: bool = False
    isActive: bool = True
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "supplier_products"
        indexes = [
            [("supplierId", 1), ("productId", 1)],
            "supplierId",
            "productId",
            "supplierSku",
            "isActive",
            "isPreferred",
        ]