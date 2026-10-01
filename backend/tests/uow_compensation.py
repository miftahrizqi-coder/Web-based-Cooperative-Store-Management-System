"""
Uji mekanisme kompensasi Unit of Work (mode MongoDB tanpa transaksi).

Mensimulasikan kegagalan di tengah transaksi penjualan multi-item (item ke-2
gagal setelah stok item ke-1 sudah dikurangi) lalu memastikan semua efek
samping dibatalkan: stok kembali, dokumen sales & stock movement terhapus.

    MONGODB_DATABASE=koperasi_uow_test MONGODB_TRANSACTIONS=off python tests/uow_compensation.py
"""

import asyncio
import sys

from fastapi import HTTPException

import app.services.sales as sales_service
from app.core.database import client, init_db, transactions_supported
from app.models.category import Category
from app.models.inventory import StockMovement
from app.models.product import Product
from app.models.sales import Sale
from app.models.user import User, UserRole
from app.schemas.sales import SaleCreate


async def main() -> None:
    await init_db()
    assert not transactions_supported(), "Jalankan dengan MONGODB_TRANSACTIONS=off"

    category = Category(name="UOW-TEST")
    await category.insert()
    a = Product(sku="UOW-A", name="A", categoryId=str(category.id), unit="pcs", purchasePrice=1, sellingPrice=2, stock=10)
    b = Product(sku="UOW-B", name="B", categoryId=str(category.id), unit="pcs", purchasePrice=1, sellingPrice=2, stock=10)
    await a.insert()
    await b.insert()
    cashier = User(username="uow-kasir", email="uow@example.com", password_hash="x", name="UOW", role=UserRole.KASIR)
    await cashier.insert()

    original = sales_service.apply_stock_change
    calls = {"n": 0}

    async def failing_apply(uow, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise HTTPException(status_code=409, detail="simulasi kegagalan item ke-2")
        return await original(uow, **kwargs)

    sales_service.apply_stock_change = failing_apply
    try:
        await sales_service.create_sale(
            SaleCreate(
                items=[{"productId": str(a.id), "quantity": 3}, {"productId": str(b.id), "quantity": 4}],
                payment={"method": "QRIS"},
            ),
            cashier,
        )
        print("FAIL: exception tidak terjadi")
        sys.exit(1)
    except HTTPException as exc:
        assert exc.status_code == 409
    finally:
        sales_service.apply_stock_change = original

    a_after = await Product.get(a.id)
    b_after = await Product.get(b.id)
    checks = [
        (a_after.stock == 10, f"stok A dikembalikan (={a_after.stock})"),
        (b_after.stock == 10, f"stok B tidak berubah (={b_after.stock})"),
        (await Sale.find({"cashierId": str(cashier.id)}).count() == 0, "dokumen sales dihapus"),
        (await StockMovement.find({"productId": {"$in": [str(a.id), str(b.id)]}}).count() == 0, "stock movement dihapus"),
    ]
    ok = True
    for passed, message in checks:
        print(("  ok    " if passed else "  FAIL  ") + message)
        ok = ok and passed

    await client.close()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
