from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import BaseModel, Field


class ReturnType(str, Enum):
    SALE = "SALE"
    PURCHASE = "PURCHASE"


class ReturnStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReturnReason(str, Enum):
    BARANG_RUSAK = "BARANG_RUSAK"
    SALAH_BARANG = "SALAH_BARANG"
    SALAH_JUMLAH = "SALAH_JUMLAH"
    LAINNYA = "LAINNYA"


class ReturnItem(BaseModel):
    productId: str
    sku: str
    name: str
    quantity: float = Field(gt=0)
    price: float = Field(ge=0)
    costPrice: float = Field(default=0, ge=0)
    subtotal: float = Field(ge=0)


class Return(Document):
    returnNumber: str
    type: ReturnType
    status: ReturnStatus = ReturnStatus.PENDING_APPROVAL

    # Retur penjualan
    saleId: str | None = None
    saleInvoiceNumber: str | None = None
    memberId: str | None = None

    # Retur pembelian
    supplierId: str | None = None
    purchaseOrderId: str | None = None
    receiptId: str | None = None
    supplierInvoiceId: str | None = None

    items: list[ReturnItem]
    totalAmount: float = Field(ge=0)

    reason: ReturnReason
    notes: str | None = Field(default=None, max_length=1000)

    createdBy: str
    approvedBy: str | None = None
    approvedAt: datetime | None = None
    rejectionReason: str | None = None

    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "returns"
        indexes = ["type", "status", "saleId", "receiptId", "supplierId", "createdAt"]
