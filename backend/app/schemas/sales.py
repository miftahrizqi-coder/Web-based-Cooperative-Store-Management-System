from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.sales import PaymentMethod, SaleStatus


class SaleItemCreate(BaseModel):
    productId: str
    quantity: float = Field(gt=0)


class SalePaymentCreate(BaseModel):
    method: PaymentMethod
    # Tunai: uang yang diterima (>= total). Non-tunai: boleh kosong (= total).
    amount: float | None = Field(default=None, ge=0)
    referenceNumber: str | None = Field(default=None, max_length=100)


class SaleCreate(BaseModel):
    items: list[SaleItemCreate] = Field(min_length=1)
    memberId: str | None = None
    discount: float = Field(default=0, ge=0)
    payment: SalePaymentCreate

    @model_validator(mode="before")
    @classmethod
    def legacy_payment_fields(cls, data):
        # Kompatibilitas payload lama: {paymentMethod, paidAmount}.
        if isinstance(data, dict) and "payment" not in data and "paymentMethod" in data:
            method = data.get("paymentMethod")
            if method == "BANK_TRANSFER":
                method = "TRANSFER"
            data = {
                **data,
                "payment": {"method": method, "amount": data.get("paidAmount")},
            }
        return data


class SaleCancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class SaleItemResponse(BaseModel):
    productId: str
    sku: str
    name: str
    unit: str
    quantity: float
    price: float
    # None untuk role yang tidak berhak melihat harga pokok.
    costPrice: float | None = None
    subtotal: float
    returnedQuantity: float = 0


class SalePaymentResponse(BaseModel):
    method: PaymentMethod
    amount: float
    change: float
    paidAt: datetime | None = None
    referenceNumber: str | None = None


class SaleResponse(BaseModel):
    id: str
    invoiceNumber: str
    cashierId: str
    cashierName: str | None = None
    memberId: str | None
    memberName: str | None = None
    memberNumber: str | None = None
    items: list[SaleItemResponse]
    subtotal: float
    discount: float
    total: float
    payment: SalePaymentResponse
    status: SaleStatus
    cancelledBy: str | None = None
    cancelledAt: datetime | None = None
    cancelReason: str | None = None
    createdAt: datetime
    updatedAt: datetime


class SaleCancelResponse(SaleResponse):
    restoredStock: list[dict] = []
