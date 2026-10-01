from datetime import datetime

from pydantic import BaseModel, Field


class SupplierProductCreateRequest(BaseModel):
    supplierId: str
    productId: str
    supplierSku: str = Field(min_length=1, max_length=100)
    purchasePrice: float = Field(ge=0)
    minimumOrder: int = Field(ge=1)
    leadTimeDays: int = Field(ge=0)
    isPreferred: bool = False
    isActive: bool = True


class SupplierProductUpdateRequest(BaseModel):
    supplierSku: str = Field(min_length=1, max_length=100)
    purchasePrice: float = Field(ge=0)
    minimumOrder: int = Field(ge=1)
    leadTimeDays: int = Field(ge=0)
    isPreferred: bool = False
    isActive: bool | None = None


class SupplierProductStatusRequest(BaseModel):
    isActive: bool


class SupplierProductResponse(BaseModel):
    id: str
    supplierId: str
    supplierName: str | None = None
    productId: str
    productName: str | None = None
    productSku: str | None = None
    supplierSku: str
    purchasePrice: float
    minimumOrder: int
    leadTimeDays: int
    isPreferred: bool
    isActive: bool
    createdAt: datetime
    updatedAt: datetime
