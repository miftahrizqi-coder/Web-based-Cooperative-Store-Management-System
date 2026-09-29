from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.models.supplier_product import SupplierProduct
from app.core.config import settings
from app.models.product import Product
from app.models.user import User
from app.models.supplier import Supplier
from app.models.procurement import (
    GoodsReceipt,
    Purchase,
    PurchaseOrder,
    SupplierInvoice,
    SupplierPayment,
)
from app.models.inventory import (
    InventoryAuditEvent,
    StockMovement,
)



client = AsyncMongoClient(settings.mongodb_uri)


async def init_db():
    await init_beanie(
        database=client[settings.mongodb_database],
        document_models=[
            User,
            Supplier,
            Product,
            PurchaseOrder,
            GoodsReceipt,
            Purchase,
            SupplierProduct,
            SupplierInvoice,
            SupplierPayment,
            StockMovement,
            InventoryAuditEvent,
        ],
    )