from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import BaseModel, Field


class PaymentMethod(str, Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    DEBIT = "DEBIT"
    OTHER = "OTHER"


class SaleStatus(str, Enum):
    PAID = "PAID"


class SaleItem(BaseModel):
    productId: str
    sku: str
    name: str
    unit: str
    quantity: float = Field(gt=0)
    unitPrice: float = Field(ge=0)
    subtotal: float = Field(ge=0)


class Sale(Document):
    saleNumber: str
    memberId: str | None = None

    items: list[SaleItem]

    subtotal: float = Field(ge=0)
    total: float = Field(ge=0)

    paymentMethod: PaymentMethod
    paidAmount: float = Field(ge=0)
    changeAmount: float = Field(ge=0)

    status: SaleStatus = SaleStatus.PAID

    createdBy: str
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "sales"
        indexes = [
            "saleNumber",
            "memberId",
            "createdBy",
            "createdAt",
            "status",
        ]