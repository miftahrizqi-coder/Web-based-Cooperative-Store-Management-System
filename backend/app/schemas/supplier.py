from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.supplier import (
    SupplierAddress,
    SupplierBankAccount,
    SupplierPaymentTerm,
    SupplierStatus,
)


class SupplierCreateRequest(BaseModel):
    supplierCode: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    companyName: str = Field(min_length=1, max_length=200)

    contactPerson: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=30)
    email: EmailStr

    address: SupplierAddress
    paymentTerm: SupplierPaymentTerm
    bankAccount: SupplierBankAccount | None = None

    status: SupplierStatus = SupplierStatus.ACTIVE
    notes: str | None = Field(default=None, max_length=1000)


class SupplierUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    companyName: str = Field(min_length=1, max_length=200)

    contactPerson: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=30)
    email: EmailStr

    address: SupplierAddress
    paymentTerm: SupplierPaymentTerm
    bankAccount: SupplierBankAccount | None = None

    notes: str | None = Field(default=None, max_length=1000)


class SupplierStatusRequest(BaseModel):
    status: SupplierStatus


class SupplierResponse(BaseModel):
    id: str

    supplierCode: str
    name: str
    companyName: str

    contactPerson: str
    phone: str
    email: EmailStr

    address: SupplierAddress
    paymentTerm: SupplierPaymentTerm
    bankAccount: SupplierBankAccount | None

    status: SupplierStatus
    notes: str | None

    createdAt: datetime
    updatedAt: datetime