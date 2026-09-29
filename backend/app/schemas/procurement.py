from datetime import datetime

from pydantic import BaseModel, Field

from app.models.procurement import (
    PaymentStatus,
    POStatus,
    SupplierPaymentMethod,
)


class POItemCreate(BaseModel):
    productId: str
    sku: str
    name: str

    quantity: int = Field(gt=0)
    unitPrice: int = Field(ge=0)


class PurchaseOrderCreate(BaseModel):
    supplierId: str

    items: list[POItemCreate] = Field(
        min_length=1
    )

    discount: int = Field(
        default=0,
        ge=0,
    )

    tax: int = Field(
        default=0,
        ge=0,
    )

    shippingCost: int = Field(
        default=0,
        ge=0,
    )

    expectedDeliveryDate: datetime | None = None


class PurchaseOrderUpdate(BaseModel):
    supplierId: str

    items: list[POItemCreate] = Field(
        min_length=1
    )

    discount: int = Field(
        default=0,
        ge=0,
    )

    tax: int = Field(
        default=0,
        ge=0,
    )

    shippingCost: int = Field(
        default=0,
        ge=0,
    )

    expectedDeliveryDate: datetime | None = None


class PurchaseOrderResponse(BaseModel):
    id: str

    poNumber: str
    supplierId: str

    items: list[dict]

    subtotal: int
    discount: int
    tax: int
    shippingCost: int
    grandTotal: int

    status: POStatus

    expectedDeliveryDate: datetime | None

    createdBy: str
    approvedBy: str | None
    approvedAt: datetime | None

    createdAt: datetime
    updatedAt: datetime


class GoodsReceiptItemCreate(BaseModel):
    productId: str
    name: str

    receivedQuantity: int = Field(
        gt=0
    )

    acceptedQuantity: int = Field(
        ge=0
    )

    rejectedQuantity: int = Field(
        ge=0
    )

    rejectionReason: str | None = None


class GoodsReceiptCreate(BaseModel):
    purchaseOrderId: str

    items: list[GoodsReceiptItemCreate] = Field(
        min_length=1
    )

    notes: str | None = None


class GoodsReceiptResponse(BaseModel):
    id: str

    receiptNumber: str

    purchaseOrderId: str
    supplierId: str

    items: list[dict]

    receivedBy: str
    receivedAt: datetime

    notes: str | None


class PurchaseCreate(BaseModel):
    receiptId: str

    discount: int = Field(
        default=0,
        ge=0,
    )


class PurchaseResponse(BaseModel):
    id: str

    purchaseNumber: str

    supplierId: str
    purchaseOrderId: str
    receiptId: str

    items: list[dict]

    subtotal: int
    discount: int
    total: int

    paymentStatus: PaymentStatus

    createdBy: str
    createdAt: datetime


class SupplierInvoiceCreate(BaseModel):
    receiptId: str

    invoiceNumber: str

    invoiceDate: datetime
    dueDate: datetime

    tax: int = Field(
        default=0,
        ge=0,
    )

    shippingCost: int = Field(
        default=0,
        ge=0,
    )


class SupplierInvoiceResponse(BaseModel):
    id: str

    invoiceNumber: str

    supplierId: str
    purchaseOrderId: str
    receiptId: str

    invoiceDate: datetime
    dueDate: datetime

    subtotal: int
    tax: int
    shippingCost: int
    total: int

    paymentStatus: PaymentStatus

    createdAt: datetime
    updatedAt: datetime


class SupplierPaymentCreate(BaseModel):
    invoiceId: str

    amount: int = Field(
        gt=0
    )

    method: SupplierPaymentMethod

    paymentDate: datetime

    referenceNumber: str | None = None

    notes: str | None = None


class SupplierPaymentResponse(BaseModel):
    id: str

    supplierId: str
    invoiceId: str

    paymentNumber: str

    amount: int
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

    total: int
    paid: int
    outstanding: int

    paymentStatus: PaymentStatus

    dueDate: datetime