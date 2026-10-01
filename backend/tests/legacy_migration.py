"""
Uji migrasi skema lama -> skema PRD (products snake_case, sales lama,
stock movement penjualan bertanda positif, invoice tanpa paidAmount).

    MONGODB_DATABASE=koperasi_migration_test python tests/legacy_migration.py
"""

import asyncio
import sys
from datetime import datetime, timezone

from bson import ObjectId

from app.core.database import client, get_database, init_db
from app.models.product import Product
from app.models.sales import Sale


async def main() -> None:
    db = get_database()
    now = datetime.now(timezone.utc)
    pid = ObjectId()
    await db.products.insert_one({
        "_id": pid, "sku": "OLD-1", "barcode": "", "name": "Produk Lama", "category_id": "x",
        "unit": "pcs", "purchase_price": 1000, "selling_price": 1500, "stock": 7,
        "minimum_stock": 2, "is_active": True, "created_at": now, "updated_at": now,
        "updatedAt": now,  # artefak bug lama goods receipt
    })
    sale_id = ObjectId()
    await db.sales.insert_one({
        "_id": sale_id, "saleNumber": "SALE-20260101-000000-ABC123", "memberId": None,
        "items": [{"productId": str(pid), "sku": "OLD-1", "name": "Produk Lama", "unit": "pcs",
                   "quantity": 2, "unitPrice": 1500, "subtotal": 3000}],
        "subtotal": 3000, "total": 3000, "paymentMethod": "BANK_TRANSFER", "paidAmount": 3000,
        "changeAmount": 0, "status": "PAID", "createdBy": "u1", "createdAt": now, "updatedAt": now,
    })
    await db.stock_movements.insert_one({
        "productId": str(pid), "type": "SALE", "quantity": 2, "stockBefore": 9, "stockAfter": 7,
        "referenceType": "SALE", "referenceId": str(sale_id), "createdBy": "u1", "createdAt": now,
    })
    inv_id = ObjectId()
    await db.supplier_invoices.insert_one({
        "_id": inv_id, "invoiceNumber": "OLD-INV", "supplierId": "s", "purchaseOrderId": "p",
        "receiptId": "r", "invoiceDate": now, "dueDate": now, "subtotal": 100, "tax": 0,
        "shippingCost": 0, "total": 100, "paymentStatus": "PARTIALLY_PAID", "createdAt": now, "updatedAt": now,
    })
    await db.supplier_payments.insert_one({"invoiceId": str(inv_id), "amount": 40})

    await init_db()

    product = await Product.get(pid)
    sale = await Sale.get(sale_id)
    movement = await db.stock_movements.find_one({"referenceId": str(sale_id)})
    invoice = await db.supplier_invoices.find_one({"_id": inv_id})
    raw = await db.products.find_one({"_id": pid})

    checks = [
        (product.categoryId == "x" and product.sellingPrice == 1500 and product.minimumStock == 2, "field produk dimigrasi ke camelCase"),
        ("selling_price" not in raw and "category_id" not in raw, "field snake_case lama dihapus"),
        (product.barcode is None, "barcode kosong -> null"),
        (sale.invoiceNumber.startswith("SALE-") and sale.status.value == "COMPLETED", "sales lama -> skema PRD"),
        (sale.payment.method.value == "TRANSFER" and sale.items[0].price == 1500 and sale.cashierId == "u1", "pembayaran & item sales lama dipetakan"),
        (movement["quantity"] == -2, "movement penjualan lama menjadi negatif"),
        (invoice["paidAmount"] == 40, "paidAmount invoice lama dihitung dari pembayaran"),
    ]
    ok = True
    for passed, message in checks:
        print(("  ok    " if passed else "  FAIL  ") + message)
        ok = ok and passed

    await client.close()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
