from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.procurement import (
    PaymentStatus,
    POStatus,
    SupplierPaymentMethod,
)


# ---------------------------------------------------------------------------
# Purchase Order
# ---------------------------------------------------------------------------


class POItemCreate(BaseModel):
    supplierProductId: str
    # productId/sku/name dari client diabaikan untuk integritas data:
    # server mengambil dari master produk supplier (tetap diterima demi
    # kompatibilitas payload frontend lama).
    productId: str | None = None
    sku: str | None = None
    name: str | None = None

    quantity: int = Field(gt=0)
    # Kosong = memakai harga beli di produk supplier.
    unitPrice: float | None = Field(default=None, ge=0)


class PurchaseOrderCreate(BaseModel):
    supplierId: str
    items: list[POItemCreate] = Field(min_length=1)
    discount: float = Field(default=0, ge=0)
    tax: float = Field(default=0, ge=0)
    shippingCost: float = Field(default=0, ge=0)
    expectedDeliveryDate: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)
    # True = langsung diajukan untuk approval.
    submit: bool = False


class PurchaseOrderUpdate(PurchaseOrderCreate):
    pass


class PurchaseOrderCompleteRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)


class PurchaseOrderResponse(BaseModel):
    id: str
    poNumber: str
    supplierId: str
    supplierName: str | None = None
    items: list[dict]
    subtotal: float
    discount: float
    tax: float
    shippingCost: float
    grandTotal: float
    status: POStatus
    expectedDeliveryDate: datetime | None
    notes: str | None = None
    createdBy: str
    submittedAt: datetime | None = None
    approvedBy: str | None
    approvedAt: datetime | None
    orderedAt: datetime | None = None
    completedAt: datetime | None = None
    cancelledAt: datetime | None = None
    createdAt: datetime
    updatedAt: datetime


# ---------------------------------------------------------------------------
# Goods Receipt
# ---------------------------------------------------------------------------


class GoodsReceiptItemCreate(BaseModel):
    productId: str
    name: str | None = None
    receivedQuantity: int = Field(gt=0)
    acceptedQuantity: int = Field(ge=0)
    rejectedQuantity: int = Field(ge=0)
    rejectionReason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def check_quantities(self):
        if self.acceptedQuantity + self.rejectedQuantity != self.receivedQuantity:
            raise ValueError("acceptedQuantity + rejectedQuantity harus sama dengan receivedQuantity")
        if self.rejectedQuantity > 0 and not (self.rejectionReason or "").strip():
            raise ValueError("rejectionReason wajib diisi jika ada barang ditolak")
        return self


class GoodsReceiptCreate(BaseModel):
    purchaseOrderId: str
    items: list[GoodsReceiptItemCreate] = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=1000)
    receivedAt: datetime | None = None


class GoodsReceiptResponse(BaseModel):
    id: str
    receiptNumber: str
    purchaseOrderId: str
    poNumber: str | None = None
    supplierId: str
    supplierName: str | None = None
    items: list[dict]
    receivedBy: str
    receivedAt: datetime
    notes: str | None


# ---------------------------------------------------------------------------
# Purchase
# ---------------------------------------------------------------------------


class PurchaseCreate(BaseModel):
    receiptId: str
    discount: float = Field(default=0, ge=0)


class PurchaseResponse(BaseModel):
    id: str
    purchaseNumber: str
    supplierId: str
    supplierName: str | None = None
    purchaseOrderId: str
    receiptId: str
    items: list[dict]
    subtotal: float
    discount: float
    total: float
    paymentStatus: PaymentStatus
    createdBy: str
    createdAt: datetime


# ---------------------------------------------------------------------------
# Supplier Invoice / Hutang / Pembayaran
# ---------------------------------------------------------------------------


class SupplierInvoiceCreate(BaseModel):
    receiptId: str
    invoiceNumber: str = Field(min_length=1, max_length=100)
    invoiceDate: datetime
    # Kosong = invoiceDate + termin pembayaran supplier.
    dueDate: datetime | None = None
    tax: float = Field(default=0, ge=0)
    shippingCost: float = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=1000)


class SupplierInvoiceResponse(BaseModel):
    id: str
    invoiceNumber: str
    supplierId: str
    supplierName: str | None = None
    purchaseOrderId: str
    receiptId: str
    invoiceDate: datetime
    dueDate: datetime
    subtotal: float
    tax: float
    shippingCost: float
    total: float
    returnedAmount: float = 0
    paidAmount: float = 0
    outstanding: float = 0
    isOverdue: bool = False
    paymentStatus: PaymentStatus
    notes: str | None = None
    createdAt: datetime
    updatedAt: datetime


class SupplierPaymentCreate(BaseModel):
    invoiceId: str
    amount: float = Field(gt=0)
    method: SupplierPaymentMethod
    paymentDate: datetime
    referenceNumber: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)


class SupplierPaymentResponse(BaseModel):
    id: str
    supplierId: str
    supplierName: str | None = None
    invoiceId: str
    invoiceNumber: str | None = None
    paymentNumber: str
    amount: float
    method: SupplierPaymentMethod
    paymentDate: datetime
    referenceNumber: str | None
    createdBy: str
    notes: str | None
    createdAt: datetime


class PayableResponse(BaseModel):
    invoiceId: str
    invoiceNumber: str
    supplierId: str
    supplierName: str | None = None
    invoiceDate: datetime | None = None
    total: float
    returned: float = 0
    paid: float
    outstanding: float
    paymentStatus: PaymentStatus
    dueDate: datetime
    isOverdue: bool = False
    daysOverdue: int = 0
