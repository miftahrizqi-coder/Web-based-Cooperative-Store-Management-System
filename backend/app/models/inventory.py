from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import Field


class StockMovementType(str, Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    SALE_RETURN = "SALE_RETURN"
    PURCHASE_RETURN = "PURCHASE_RETURN"
    ADJUSTMENT = "ADJUSTMENT"
    STOCK_OPNAME = "STOCK_OPNAME"


class StockMovement(Document):
    productId: str
    type: StockMovementType
    quantity: float
    stockBefore: float
    stockAfter: float
    referenceType: str | None = None
    referenceId: str | None = None
    createdBy: str
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "stock_movements"
        indexes = [
            "productId",
            "type",
            "referenceType",
            "createdAt",
        ]


class InventoryAuditEvent(Document):
    action: str
    productId: str
    referenceType: str | None = None
    referenceId: str | None = None
    stockBefore: float
    stockAfter: float
    quantity: float
    reason: str | None = None
    createdBy: str
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "inventory_audit_events"
        indexes = [
            "productId",
            "action",
            "referenceType",
            "createdAt",
        ]