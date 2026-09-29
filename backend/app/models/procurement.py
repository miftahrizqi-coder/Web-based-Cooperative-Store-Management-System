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
    unitPrice: int = Field(ge=0)
    subtotal: int = Field(ge=0)


class PurchaseOrder(Document):
    poNumber: str
    supplierId: str

    items: list[PurchaseOrderItem]

    subtotal: int = Field(ge=0)
    discount: int = Field(default=0, ge=0)
    tax: int = Field(default=0, ge=0)
    shippingCost: int = Field(default=0, ge=0)
    grandTotal: int = Field(ge=0)

    status: POStatus = POStatus.DRAFT

    expectedDeliveryDate: datetime | None = None

    createdBy: str
    approvedBy: str | None = None
    approvedAt: datetime | None = None

    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "purchase_orders"

        indexes = [
            "poNumber",
            "supplierId",
            "status",
            "createdAt",
        ]


class GoodsReceiptItem(BaseModel):
    productId: str
    name: str

    orderedQuantity: int = Field(gt=0)
    previouslyReceivedQuantity: int = Field(default=0, ge=0)

    receivedQuantity: int = Field(gt=0)
    acceptedQuantity: int = Field(ge=0)
    rejectedQuantity: int = Field(ge=0)

    rejectionReason: str | None = None


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
            "receiptNumber",
            "purchaseOrderId",
            "supplierId",
            "receivedAt",
        ]


class PurchaseItem(BaseModel):
    productId: str
    name: str

    quantity: int = Field(gt=0)
    price: int = Field(ge=0)
    subtotal: int = Field(ge=0)


class Purchase(Document):
    purchaseNumber: str

    supplierId: str
    purchaseOrderId: str
    receiptId: str

    items: list[PurchaseItem]

    subtotal: int = Field(ge=0)
    discount: int = Field(default=0, ge=0)
    total: int = Field(ge=0)

    paymentStatus: PaymentStatus = PaymentStatus.UNPAID

    createdBy: str

    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "purchases"

        indexes = [
            "purchaseNumber",
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

    subtotal: int = Field(ge=0)
    tax: int = Field(default=0, ge=0)
    shippingCost: int = Field(default=0, ge=0)

    total: int = Field(ge=0)

    paymentStatus: PaymentStatus = PaymentStatus.UNPAID

    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "supplier_invoices"

        indexes = [
            "invoiceNumber",
            "supplierId",
            "paymentStatus",
            "dueDate",
        ]


class SupplierPayment(Document):
    supplierId: str
    invoiceId: str

    paymentNumber: str

    amount: int = Field(gt=0)

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
            "paymentNumber",
            "supplierId",
            "invoiceId",
            "paymentDate",
        ]