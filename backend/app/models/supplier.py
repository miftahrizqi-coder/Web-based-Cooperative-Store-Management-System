from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import BaseModel, EmailStr, Field


class SupplierStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLACKLISTED = "BLACKLISTED"


class SupplierAddress(BaseModel):
    street: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    province: str = Field(min_length=1, max_length=100)
    postalCode: str = Field(min_length=1, max_length=20)


class SupplierPaymentTermType(str, Enum):
    CASH = "CASH"
    CREDIT = "CREDIT"


class SupplierPaymentTerm(BaseModel):
    type: SupplierPaymentTermType
    days: int = Field(default=0, ge=0)


class SupplierBankAccount(BaseModel):
    bankName: str = Field(min_length=1, max_length=100)
    accountNumber: str = Field(min_length=1, max_length=50)
    accountName: str = Field(min_length=1, max_length=150)


class Supplier(Document):
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

    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "suppliers"

        indexes = [
            "supplierCode",
            "name",
            "status",
            "email",
        ]