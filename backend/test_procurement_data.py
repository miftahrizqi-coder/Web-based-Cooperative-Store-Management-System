import asyncio

from app.core.database import init_db
from app.models.procurement import (
    PurchaseOrder,
    GoodsReceipt,
    Purchase,
    SupplierInvoice,
    SupplierPayment,
)

async def main():
    await init_db()

    print("PO:", await PurchaseOrder.count())
    print("GR:", await GoodsReceipt.count())
    print("PURCHASE:", await Purchase.count())
    print("INVOICE:", await SupplierInvoice.count())
    print("PAYMENT:", await SupplierPayment.count())

asyncio.run(main())
