from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    barcode: str | None = Field(default=None, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    categoryId: str = Field(min_length=1)
    unit: str = Field(min_length=1, max_length=30)

    purchasePrice: float = Field(ge=0)
    sellingPrice: float = Field(ge=0)
    minimumStock: float = Field(default=0, ge=0)

    @field_validator("sku", "name", "unit")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("tidak boleh kosong")
        return value

    @field_validator("barcode")
    @classmethod
    def normalize_barcode(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ProductCreateRequest(ProductBase):
    # Stok awal dicatat sebagai stock movement ADJUSTMENT "Stok awal".
    stock: float = Field(default=0, ge=0)


class ProductUpdateRequest(ProductBase):
    """Stok TIDAK dapat diubah lewat edit produk; gunakan stock adjustment
    atau stock opname agar setiap perubahan tercatat (PRD §20)."""

    isActive: bool = True


class ProductResponse(BaseModel):
    id: str
    sku: str
    barcode: str | None
    name: str
    categoryId: str
    categoryName: str | None = None
    unit: str

    # None untuk role yang tidak berhak melihat harga beli (kasir).
    purchasePrice: float | None
    sellingPrice: float
    stock: float
    minimumStock: float
    stockStatus: str

    isActive: bool
    createdAt: datetime
    updatedAt: datetime
