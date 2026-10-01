from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class InventoryResponse(BaseModel):
    productId: str
    sku: str
    barcode: str | None
    name: str
    categoryId: str
    categoryName: str | None = None
    unit: str
    stock: float
    minimumStock: float
    stockStatus: str
    purchasePrice: float
    sellingPrice: float
    stockValue: float
    isActive: bool
    updatedAt: datetime


class StockMovementResponse(BaseModel):
    id: str
    productId: str
    sku: str
    productName: str
    type: str
    quantity: float
    stockBefore: float
    stockAfter: float
    referenceType: str | None
    referenceId: str | None
    referenceNumber: str | None = None
    reason: str | None = None
    createdBy: str
    createdByName: str | None = None
    createdAt: datetime


class StockAdjustmentRequest(BaseModel):
    productId: str
    # Bertanda: positif menambah, negatif mengurangi stok.
    quantity: float
    reason: str = Field(min_length=3, max_length=500)

    @model_validator(mode="after")
    def non_zero(self):
        if self.quantity == 0:
            raise ValueError("quantity adjustment tidak boleh 0")
        return self


class StockAdjustmentResponse(BaseModel):
    productId: str
    quantity: float
    stockBefore: float
    stockAfter: float
    reason: str
    movementId: str


class StockOpnameItemRequest(BaseModel):
    productId: str
    physicalStock: float = Field(ge=0)
    # Sistem mencatat stok yang dilihat petugas saat menghitung; jika stok
    # berubah sebelum disimpan (mis. ada penjualan), opname ditolak.
    systemStock: float | None = None
    reason: str | None = Field(default=None, max_length=500)


class StockOpnameRequest(BaseModel):
    items: list[StockOpnameItemRequest] = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=1000)


class StockOpnameItemResponse(BaseModel):
    productId: str
    sku: str
    name: str
    systemStock: float
    physicalStock: float
    difference: float
    reason: str | None
    movementId: str | None


class StockOpnameResponse(BaseModel):
    id: str
    opnameNumber: str
    items: list[StockOpnameItemResponse]
    notes: str | None
    totalItems: int
    itemsWithDifference: int
    createdBy: str
    createdByName: str | None = None
    createdAt: datetime


class StockAlertResponse(BaseModel):
    productId: str
    sku: str
    name: str
    unit: str
    stock: float
    minimumStock: float
    status: str
