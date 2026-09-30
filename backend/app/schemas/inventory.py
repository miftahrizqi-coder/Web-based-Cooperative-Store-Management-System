from datetime import datetime

from pydantic import BaseModel, Field


class InventoryResponse(BaseModel):
    product_id: str
    sku: str
    barcode: str | None
    name: str
    unit: str
    stock: float
    minimum_stock: float
    stock_status: str
    is_active: bool


class StockMovementResponse(BaseModel):
    id: str
    product_id: str
    sku: str
    product_name: str
    type: str
    quantity: float
    stock_before: float
    stock_after: float
    reference_type: str | None
    reference_id: str | None
    created_by: str
    created_at: datetime


class StockAdjustmentRequest(BaseModel):
    product_id: str
    quantity: float
    reason: str = Field(min_length=3, max_length=500)


class StockAdjustmentResponse(BaseModel):
    product_id: str
    quantity: float
    stock_before: float
    stock_after: float
    reason: str
    movement_id: str


class StockOpnameRequest(BaseModel):
    product_id: str
    physical_stock: float = Field(ge=0)
    reason: str = Field(min_length=3, max_length=500)


class StockOpnameResponse(BaseModel):
    product_id: str
    system_stock: float
    physical_stock: float
    difference: float
    reason: str
    movement_id: str | None
    audit_event_id: str


class StockAlertResponse(BaseModel):
    product_id: str
    sku: str
    name: str
    stock: float
    minimum_stock: float
    status: str