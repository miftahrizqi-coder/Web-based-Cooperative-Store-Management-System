from datetime import datetime

from pydantic import BaseModel, Field

from app.models.sales import PaymentMethod, SaleStatus


class SaleItem(BaseModel):
    productId: str
    sku: str
    name: str
    unit: str
    quantity: float = Field(gt=0)
    unitPrice: float = Field(ge=0)
    subtotal: float = Field(ge=0)


class SaleItemCreate(BaseModel):
    productId: str
    quantity: float = Field(gt=0)


class SaleCreate(BaseModel):
    items: list[SaleItemCreate] = Field(min_length=1)
    memberId: str | None = None
    paymentMethod: PaymentMethod
    paidAmount: float = Field(ge=0)


class SaleItemResponse(BaseModel):
    productId: str
    sku: str
    name: str
    unit: str
    quantity: float
    unitPrice: float
    subtotal: float


class SaleResponse(BaseModel):
    id: str
    saleNumber: str
    memberId: str | None
    items: list[SaleItemResponse]
    subtotal: float
    total: float
    paymentMethod: PaymentMethod
    paidAmount: float
    changeAmount: float
    status: SaleStatus
    createdBy: str
    createdAt: datetime
    updatedAt: datetime

class SaleCancelResponse(BaseModel):
    id: str
    saleNumber: str
    status: SaleStatus
    restoredStock: list[dict]
    updatedAt: datetime