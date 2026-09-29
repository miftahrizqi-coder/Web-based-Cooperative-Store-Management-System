from datetime import datetime

from pydantic import BaseModel, Field


class ProductCreateRequest(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    barcode: str | None = Field(default=None, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    category_id: str
    unit: str = Field(min_length=1, max_length=30)

    purchase_price: float = Field(ge=0)
    selling_price: float = Field(ge=0)
    stock: float = Field(ge=0)
    minimum_stock: float = Field(ge=0)


class ProductUpdateRequest(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    barcode: str | None = Field(default=None, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    category_id: str
    unit: str = Field(min_length=1, max_length=30)

    purchase_price: float = Field(ge=0)
    selling_price: float = Field(ge=0)
    stock: float = Field(ge=0)
    minimum_stock: float = Field(ge=0)

    is_active: bool


class ProductResponse(BaseModel):
    id: str
    sku: str
    barcode: str | None
    name: str
    category_id: str
    unit: str

    purchase_price: float
    selling_price: float
    stock: float
    minimum_stock: float

    is_active: bool
    created_at: datetime
    updated_at: datetime
