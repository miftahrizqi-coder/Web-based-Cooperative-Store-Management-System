from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.returns import ReturnReason, ReturnStatus, ReturnType


class ReturnItemCreate(BaseModel):
    productId: str
    quantity: float = Field(gt=0)


class SalesReturnCreate(BaseModel):
    saleId: str | None = None
    invoiceNumber: str | None = None
    items: list[ReturnItemCreate] = Field(min_length=1)
    reason: ReturnReason
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def need_reference(self):
        if not self.saleId and not self.invoiceNumber:
            raise ValueError("saleId atau invoiceNumber wajib diisi")
        return self


class PurchaseReturnCreate(BaseModel):
    receiptId: str
    items: list[ReturnItemCreate] = Field(min_length=1)
    reason: ReturnReason
    notes: str | None = Field(default=None, max_length=1000)


class ReturnRejectRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ReturnItemResponse(BaseModel):
    productId: str
    sku: str
    name: str
    quantity: float
    price: float
    subtotal: float


class ReturnResponse(BaseModel):
    id: str
    returnNumber: str
    type: ReturnType
    status: ReturnStatus
    saleId: str | None
    saleInvoiceNumber: str | None
    memberId: str | None
    supplierId: str | None
    supplierName: str | None = None
    purchaseOrderId: str | None
    receiptId: str | None
    receiptNumber: str | None = None
    supplierInvoiceId: str | None
    items: list[ReturnItemResponse]
    totalAmount: float
    reason: ReturnReason
    notes: str | None
    createdBy: str
    createdByName: str | None = None
    approvedBy: str | None
    approvedByName: str | None = None
    approvedAt: datetime | None
    rejectionReason: str | None
    createdAt: datetime
    updatedAt: datetime
