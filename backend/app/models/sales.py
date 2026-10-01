from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import BaseModel, Field


class PaymentMethod(str, Enum):
    """PRD §24."""

    CASH = "CASH"
    TRANSFER = "TRANSFER"
    QRIS = "QRIS"
    DEBIT = "DEBIT"
    E_WALLET = "E_WALLET"


class SaleStatus(str, Enum):
    """PRD §23."""

    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class SaleItem(BaseModel):
    productId: str
    sku: str
    name: str
    unit: str = "pcs"
    quantity: float = Field(gt=0)
    # Harga jual & harga pokok di-snapshot saat transaksi (BR-03).
    price: float = Field(ge=0)
    costPrice: float = Field(default=0, ge=0)
    subtotal: float = Field(ge=0)
    # Akumulasi retur penjualan yang sudah disetujui untuk item ini.
    returnedQuantity: float = Field(default=0, ge=0)


class SalePaymentInfo(BaseModel):
    method: PaymentMethod
    amount: float = Field(ge=0)
    change: float = Field(ge=0)
    paidAt: datetime | None = None
    referenceNumber: str | None = None


class Sale(Document):
    invoiceNumber: str
    cashierId: str
    memberId: str | None = None

    items: list[SaleItem]

    subtotal: float = Field(ge=0)
    discount: float = Field(default=0, ge=0)
    total: float = Field(ge=0)

    payment: SalePaymentInfo

    status: SaleStatus = SaleStatus.COMPLETED

    cancelledBy: str | None = None
    cancelledAt: datetime | None = None
    cancelReason: str | None = None

    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sales"
        # invoiceNumber: index unik dibuat di core/database.py
        indexes = ["cashierId", "memberId", "createdAt", "status"]


class SalePaymentType(str, Enum):
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"


class SalePayment(Document):
    """Collection `payments` (PRD §30): jejak pembayaran & refund penjualan."""

    saleId: str
    invoiceNumber: str
    type: SalePaymentType = SalePaymentType.PAYMENT
    method: PaymentMethod
    amount: float = Field(ge=0)
    change: float = Field(default=0, ge=0)
    referenceId: str | None = None
    paidAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    createdBy: str

    class Settings:
        name = "payments"
        indexes = ["saleId", "type", "paidAt"]
