from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import BaseModel, Field


class StockMovementType(str, Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    SALE_RETURN = "SALE_RETURN"
    PURCHASE_RETURN = "PURCHASE_RETURN"
    ADJUSTMENT = "ADJUSTMENT"
    STOCK_OPNAME = "STOCK_OPNAME"


class StockMovement(Document):
    """
    Kartu stok. `quantity` bertanda (PRD §20):
    positif = stok masuk, negatif = stok keluar.
    stockAfter = stockBefore + quantity.
    """

    productId: str
    type: StockMovementType
    quantity: float
    stockBefore: float
    stockAfter: float
    referenceType: str | None = None
    referenceId: str | None = None
    referenceNumber: str | None = None
    reason: str | None = None
    createdBy: str
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "stock_movements"
        indexes = ["productId", "type", "referenceType", "referenceId", "createdAt"]


class StockOpnameItem(BaseModel):
    productId: str
    sku: str
    name: str
    systemStock: float
    physicalStock: float = Field(ge=0)
    difference: float
    reason: str | None = None
    movementId: str | None = None


class StockOpname(Document):
    """Collection `stock_opnames` (PRD §21)."""

    opnameNumber: str
    items: list[StockOpnameItem]
    notes: str | None = None
    totalItems: int
    itemsWithDifference: int
    createdBy: str
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "stock_opnames"
        indexes = ["createdAt", "createdBy"]
