import logging

from beanie import init_beanie
from pymongo import ASCENDING, TEXT, AsyncMongoClient, IndexModel
from pymongo.errors import OperationFailure

from app.core.config import settings


logger = logging.getLogger("koperasi.database")

client = AsyncMongoClient(settings.mongodb_uri, tz_aware=True)

_transactions_supported = False


def get_database():
    return client[settings.mongodb_database]


def transactions_supported() -> bool:
    return _transactions_supported


def document_models() -> list:
    from app.models.activity import Activity
    from app.models.audit_log import AuditLog
    from app.models.category import Category
    from app.models.expense import Expense
    from app.models.inventory import StockMovement, StockOpname
    from app.models.member import Member
    from app.models.procurement import (
        GoodsReceipt,
        Purchase,
        PurchaseOrder,
        SupplierInvoice,
        SupplierPayment,
    )
    from app.models.product import Product
    from app.models.returns import Return
    from app.models.sales import Sale, SalePayment
    from app.models.supplier import Supplier
    from app.models.supplier_product import SupplierProduct
    from app.models.user import RevokedToken, User

    return [
        User,
        Category,
        Product,
        Supplier,
        SupplierProduct,
        Member,
        PurchaseOrder,
        GoodsReceipt,
        Purchase,
        SupplierInvoice,
        SupplierPayment,
        Sale,
        SalePayment,
        StockMovement,
        StockOpname,
        Return,
        Expense,
        AuditLog,
        Activity,
        RevokedToken,
    ]


# Index unik dibuat terpisah dari Beanie supaya:
# 1. data lama yang duplikat tidak membuat aplikasi gagal start
#    (cukup warning di log), dan
# 2. index non-unik lama dengan key yang sama bisa diganti otomatis.
UNIQUE_INDEXES: dict[str, list[tuple[str, dict]]] = {
    "users": [("username", {}), ("email", {})],
    "categories": [("name", {})],
    "products": [
        ("sku", {}),
        ("barcode", {"partialFilterExpression": {"barcode": {"$type": "string"}}}),
    ],
    "suppliers": [("supplierCode", {})],
    "members": [("memberNumber", {})],
    "purchase_orders": [("poNumber", {})],
    "goods_receipts": [("receiptNumber", {})],
    "purchases": [("purchaseNumber", {})],
    "supplier_invoices": [("invoiceNumber", {})],
    "supplier_payments": [("paymentNumber", {})],
    "sales": [("invoiceNumber", {})],
    "returns": [("returnNumber", {})],
    "stock_opnames": [("opnameNumber", {})],
}


async def ensure_unique_indexes() -> None:
    db = get_database()

    for collection_name, fields in UNIQUE_INDEXES.items():
        collection = db[collection_name]

        try:
            existing = await collection.index_information()
        except OperationFailure:
            existing = {}

        for field, options in fields:
            for index_name, info in existing.items():
                if info.get("key") == [(field, 1)] and not info.get("unique"):
                    try:
                        await collection.drop_index(index_name)
                    except OperationFailure as exc:
                        logger.warning("Gagal drop index %s.%s: %s", collection_name, index_name, exc)

            try:
                await collection.create_indexes(
                    [IndexModel([(field, ASCENDING)], unique=True, **options)]
                )
            except OperationFailure as exc:
                if options.get("partialFilterExpression"):
                    # Server tanpa dukungan partial index: jangan pakai sparse
                    # (null tetap terindeks -> barcode kosong dianggap duplikat).
                    # Keunikan tetap dijaga validasi aplikasi.
                    logger.warning(
                        "Partial unique index %s.%s tidak didukung server: %s",
                        collection_name,
                        field,
                        exc,
                    )
                    continue
                logger.warning(
                    "Index unik %s.%s tidak dapat dibuat (cek data duplikat): %s",
                    collection_name,
                    field,
                    exc,
                )


async def ensure_optional_indexes() -> None:
    """Index yang disarankan PRD §32 tetapi tidak wajib untuk berjalan."""
    try:
        await get_database()["products"].create_indexes(
            [IndexModel([("name", TEXT)], name="products_name_text")]
        )
    except OperationFailure as exc:
        logger.warning("Text index products.name tidak dibuat: %s", exc)


async def migrate_legacy_data() -> None:
    """
    Migrasi skema versi lama:
    - products: field snake_case -> camelCase sesuai PRD.
    - products: barcode string kosong -> null (agar index unik parsial aman).
    - sales: skema lama (saleNumber/paidAmount/status PAID) -> skema PRD.
    """
    db = get_database()
    products = db["products"]

    rename_map = {
        "category_id": "categoryId",
        "purchase_price": "purchasePrice",
        "selling_price": "sellingPrice",
        "minimum_stock": "minimumStock",
        "is_active": "isActive",
        "created_at": "createdAt",
        "updated_at": "updatedAt",
    }

    for old, new in rename_map.items():
        result = await products.update_many(
            {old: {"$exists": True}, new: {"$exists": False}},
            {"$rename": {old: new}},
        )
        if result.modified_count:
            logger.info("Migrasi products.%s -> %s: %s dokumen", old, new, result.modified_count)
        # Sisa field lama (jika dua-duanya ada) dihapus.
        await products.update_many({old: {"$exists": True}}, {"$unset": {old: ""}})

    await products.update_many({"barcode": ""}, {"$set": {"barcode": None}})

    # supplier_invoices.paidAmount (cache) untuk data lama.
    invoices = db["supplier_invoices"]
    async for invoice in invoices.find({"paidAmount": {"$exists": False}}, {"_id": 1}):
        paid = 0.0
        async for payment in db["supplier_payments"].find(
            {"invoiceId": str(invoice["_id"])}, {"amount": 1}
        ):
            paid += float(payment.get("amount", 0))
        await invoices.update_one({"_id": invoice["_id"]}, {"$set": {"paidAmount": paid}})

    # stock_movements lama mencatat penjualan dengan quantity positif.
    # PRD §20: quantity bertanda (keluar = negatif).
    movements = db["stock_movements"]
    async for movement in movements.find(
        {"type": "SALE", "quantity": {"$gt": 0}, "referenceType": "SALE"},
        {"quantity": 1, "stockBefore": 1, "stockAfter": 1},
    ):
        if movement.get("stockAfter", 0) < movement.get("stockBefore", 0):
            await movements.update_one(
                {"_id": movement["_id"]},
                {"$set": {"quantity": -abs(movement["quantity"])}},
            )

    sales = db["sales"]
    async for legacy in sales.find({"saleNumber": {"$exists": True}}):
        payment_method = legacy.get("paymentMethod", "CASH")
        if payment_method == "BANK_TRANSFER":
            payment_method = "TRANSFER"
        elif payment_method not in {"CASH", "TRANSFER", "QRIS", "DEBIT", "E_WALLET"}:
            payment_method = "CASH"

        items = []
        for item in legacy.get("items", []):
            price = item.get("unitPrice", item.get("price", 0))
            items.append(
                {
                    "productId": item.get("productId"),
                    "sku": item.get("sku", "-"),
                    "name": item.get("name", "-"),
                    "unit": item.get("unit", "pcs"),
                    "quantity": item.get("quantity", 0),
                    "price": price,
                    "costPrice": item.get("costPrice", 0),
                    "subtotal": item.get("subtotal", 0),
                }
            )

        await sales.update_one(
            {"_id": legacy["_id"]},
            {
                "$set": {
                    "invoiceNumber": legacy["saleNumber"],
                    "cashierId": legacy.get("createdBy"),
                    "items": items,
                    "discount": legacy.get("discount", 0),
                    "payment": {
                        "method": payment_method,
                        "amount": legacy.get("paidAmount", legacy.get("total", 0)),
                        "change": legacy.get("changeAmount", 0),
                        "paidAt": legacy.get("createdAt"),
                    },
                    "status": "CANCELLED" if legacy.get("status") == "CANCELLED" else "COMPLETED",
                },
                "$unset": {
                    "saleNumber": "",
                    "paymentMethod": "",
                    "paidAmount": "",
                    "changeAmount": "",
                    "createdBy": "",
                },
            },
        )


async def detect_transaction_support() -> bool:
    mode = settings.mongodb_transactions.lower()
    if mode == "on":
        return True
    if mode == "off":
        return False

    try:
        hello = await client.admin.command("hello")
    except OperationFailure:
        return False

    return bool(hello.get("setName")) or hello.get("msg") == "isdbgrid"


async def init_db() -> None:
    global _transactions_supported

    await migrate_legacy_data()

    await init_beanie(
        database=get_database(),
        document_models=document_models(),
    )

    await ensure_unique_indexes()
    await ensure_optional_indexes()

    _transactions_supported = await detect_transaction_support()
    logger.info(
        "MongoDB transaksi multi-dokumen: %s",
        "aktif" if _transactions_supported else "tidak tersedia (mode kompensasi)",
    )
