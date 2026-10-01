"""
Primitive perubahan stok. SEMUA perubahan stok (pembelian, penjualan,
retur, adjustment, opname, pembatalan) wajib lewat `apply_stock_change`
agar:

1. stok tidak pernah negatif (BR-02) — dijamin oleh update kondisional
   atomik di MongoDB, bukan cek-lalu-tulis yang rawan race condition;
2. setiap perubahan tercatat di stock_movements dengan stockBefore /
   stockAfter yang akurat (diambil dari hasil update atomik);
3. perubahan ikut transaksi / kompensasi Unit of Work.
"""

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo import ReturnDocument

from app.core.uow import UnitOfWork
from app.core.utils import utc_now
from app.models.inventory import StockMovement, StockMovementType
from app.models.product import Product


def _fmt(value: float) -> str:
    return f"{value:g}"


async def apply_stock_change(
    uow: UnitOfWork,
    *,
    product_id: str,
    delta: float,
    movement_type: StockMovementType,
    user_id: str,
    reference_type: str | None = None,
    reference_id: str | None = None,
    reference_number: str | None = None,
    reason: str | None = None,
    require_active: bool = False,
    expected_stock: float | None = None,
) -> StockMovement:
    if delta == 0:
        raise ValueError("delta stok tidak boleh 0")

    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail=f"ID produk tidak valid: {product_id}")

    object_id = ObjectId(product_id)
    collection = Product.get_pymongo_collection()

    stock_filter: dict = {"_id": object_id}
    if expected_stock is not None:
        stock_filter["stock"] = expected_stock
    elif delta < 0:
        stock_filter["stock"] = {"$gte": -delta}
    if require_active:
        stock_filter["isActive"] = True

    updated = await collection.find_one_and_update(
        stock_filter,
        {"$inc": {"stock": delta}, "$set": {"updatedAt": utc_now()}},
        return_document=ReturnDocument.AFTER,
        session=uow.session,
    )

    if updated is None:
        product = await collection.find_one(
            {"_id": object_id},
            {"name": 1, "stock": 1, "isActive": 1},
            session=uow.session,
        )
        if product is None:
            raise HTTPException(status_code=404, detail=f"Produk {product_id} tidak ditemukan.")
        name = product.get("name", product_id)
        if require_active and not product.get("isActive", True):
            raise HTTPException(status_code=400, detail=f"Produk {name} tidak aktif.")
        if expected_stock is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Stok {name} berubah saat diproses "
                    f"(sistem {_fmt(expected_stock)}, sekarang {_fmt(product.get('stock', 0))}). "
                    "Muat ulang dan ulangi."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Stok {name} tidak mencukupi. "
                f"Tersedia {_fmt(product.get('stock', 0))}, dibutuhkan {_fmt(-delta)}."
            ),
        )

    stock_after = float(updated["stock"])
    stock_before = stock_after - delta

    uow.on_rollback(
        lambda: collection.update_one({"_id": object_id}, {"$inc": {"stock": -delta}})
    )

    movement = StockMovement(
        productId=product_id,
        type=movement_type,
        quantity=delta,
        stockBefore=stock_before,
        stockAfter=stock_after,
        referenceType=reference_type,
        referenceId=reference_id,
        referenceNumber=reference_number,
        reason=reason,
        createdBy=user_id,
    )
    await uow.insert(movement)
    return movement


def stock_status(stock: float, minimum_stock: float) -> str:
    if stock <= 0:
        return "OUT_OF_STOCK"
    if stock <= minimum_stock:
        return "LOW_STOCK"
    return "AVAILABLE"
