from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import BaseModel, Field


class POStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    ORDERED = "ORDERED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    UNPAID = "UNPAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"


class SupplierPaymentMethod(str, Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    DEBIT = "DEBIT"
    OTHER = "OTHER"


class PurchaseOrderItem(BaseModel):
    productId: str
    sku: str
    name: str
    supplierProductId: str
    quantity: int = Field(gt=0)
    unitPrice: float = Field(ge=0)
    subtotal: float = Field(ge=0)
    # Akumulasi qty diterima (received) dari seluruh Goods Receipt.
    receivedQuantity: int = Field(default=0, ge=0)
    # Akumulasi qty yang diterima baik (accepted) -> menambah stok.
    acceptedQuantity: int = Field(default=0, ge=0)


class PurchaseOrder(Document):
    poNumber: str
    supplierId: str

    items: list[PurchaseOrderItem]

    subtotal: float = Field(ge=0)
    discount: float = Field(default=0, ge=0)
    tax: float = Field(default=0, ge=0)
    shippingCost: float = Field(default=0, ge=0)
    grandTotal: float = Field(ge=0)

    status: POStatus = POStatus.DRAFT

    # Optimistic locking: dinaikkan setiap PO berubah akibat penerimaan
    # agar dua penerimaan bersamaan tidak menyebabkan over-receive.
    revision: int = 0

    expectedDeliveryDate: datetime | None = None

    notes: str | None = None

    createdBy: str
    submittedAt: datetime | None = None
    approvedBy: str | None = None
    approvedAt: datetime | None = None
    orderedAt: datetime | None = None
    completedAt: datetime | None = None
    cancelledBy: str | None = None
    cancelledAt: datetime | None = None

    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "purchase_orders"

        # poNumber: index unik dibuat di core/database.py
        indexes = [
            "supplierId",
            "status",
            "createdAt",
        ]


class GoodsReceiptItem(BaseModel):
    productId: str
    sku: str = "-"
    name: str
    unitPrice: float = Field(default=0, ge=0)

    orderedQuantity: int = Field(gt=0)
    previouslyReceivedQuantity: int = Field(default=0, ge=0)

    receivedQuantity: int = Field(gt=0)
    acceptedQuantity: int = Field(ge=0)
    rejectedQuantity: int = Field(ge=0)

    rejectionReason: str | None = None

    # Akumulasi retur pembelian yang disetujui untuk item ini.
    returnedQuantity: int = Field(default=0, ge=0)


class GoodsReceipt(Document):
    receiptNumber: str

    purchaseOrderId: str
    supplierId: str

    items: list[GoodsReceiptItem]

    receivedBy: str

    receivedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    notes: str | None = None

    class Settings:
        name = "goods_receipts"

        indexes = [
            "purchaseOrderId",
            "supplierId",
            "receivedAt",
        ]


class PurchaseItem(BaseModel):
    productId: str
    name: str

    quantity: int = Field(gt=0)
    price: float = Field(ge=0)
    subtotal: float = Field(ge=0)


class Purchase(Document):
    purchaseNumber: str

    supplierId: str
    purchaseOrderId: str
    receiptId: str

    items: list[PurchaseItem]

    subtotal: float = Field(ge=0)
    discount: float = Field(default=0, ge=0)
    total: float = Field(ge=0)

    paymentStatus: PaymentStatus = PaymentStatus.UNPAID

    createdBy: str

    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "purchases"

        indexes = [
            "supplierId",
            "purchaseOrderId",
            "receiptId",
            "createdAt",
        ]


class SupplierInvoice(Document):
    invoiceNumber: str

    supplierId: str
    purchaseOrderId: str
    receiptId: str

    invoiceDate: datetime
    dueDate: datetime

    subtotal: float = Field(ge=0)
    tax: float = Field(default=0, ge=0)
    shippingCost: float = Field(default=0, ge=0)

    total: float = Field(ge=0)

    # Kredit dari retur pembelian yang disetujui (mengurangi hutang).
    returnedAmount: float = Field(default=0, ge=0)

    # Akumulasi pembayaran (di-maintain atomik bersama supplier_payments).
    paidAmount: float = Field(default=0, ge=0)

    paymentStatus: PaymentStatus = PaymentStatus.UNPAID

    notes: str | None = None
    createdBy: str | None = None

    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "supplier_invoices"

        indexes = [
            "supplierId",
            "purchaseOrderId",
            "receiptId",
            "paymentStatus",
            "dueDate",
        ]


class SupplierPayment(Document):
    supplierId: str
    invoiceId: str

    paymentNumber: str

    amount: float = Field(gt=0)

    method: SupplierPaymentMethod

    paymentDate: datetime

    referenceNumber: str | None = None

    createdBy: str

    notes: str | None = None

    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "supplier_payments"

        indexes = [
            "supplierId",
            "invoiceId",
            "paymentDate",
        ]