"""
Alur pengadaan (PRD §14-19, §37.1):
PO (DRAFT -> PENDING_APPROVAL -> APPROVED -> ORDERED) -> Goods Receipt
(PARTIALLY_RECEIVED / RECEIVED) -> Purchase -> Supplier Invoice -> Hutang
-> Supplier Payment. PO dapat ditutup menjadi COMPLETED.
"""

from datetime import timedelta

from bson import ObjectId
from fastapi import HTTPException

from app.core.uow import unit_of_work
from app.core.utils import as_utc, next_document_number, parse_object_id, utc_now
from app.models.activity import ActivityEntityType, ActivityType
from app.models.inventory import StockMovementType
from app.models.procurement import (
    GoodsReceipt,
    GoodsReceiptItem,
    PaymentStatus,
    POStatus,
    Purchase,
    PurchaseItem,
    PurchaseOrder,
    PurchaseOrderItem,
    SupplierInvoice,
    SupplierPayment,
)
from app.models.product import Product
from app.models.supplier import Supplier, SupplierStatus
from app.models.supplier_product import SupplierProduct
from app.models.user import User
from app.schemas.procurement import (
    GoodsReceiptCreate,
    GoodsReceiptResponse,
    PurchaseCreate,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    PurchaseResponse,
    SupplierInvoiceCreate,
    SupplierInvoiceResponse,
    SupplierPaymentCreate,
    SupplierPaymentResponse,
)
from app.services.activity import create_activity
from app.services.stock import apply_stock_change


# ===========================================================================
# Helper
# ===========================================================================


async def supplier_name_map(ids: set[str]) -> dict[str, str]:
    object_ids = [ObjectId(i) for i in ids if i and ObjectId.is_valid(i)]
    if not object_ids:
        return {}
    suppliers = await Supplier.find({"_id": {"$in": object_ids}}).to_list()
    return {str(s.id): s.name for s in suppliers}


async def get_po_or_404(po_id: str) -> PurchaseOrder:
    po = await PurchaseOrder.get(parse_object_id(po_id, "ID Purchase Order"))
    if po is None:
        raise HTTPException(status_code=404, detail="Purchase Order tidak ditemukan.")
    return po


async def get_receipt_or_404(receipt_id: str) -> GoodsReceipt:
    receipt = await GoodsReceipt.get(parse_object_id(receipt_id, "ID Goods Receipt"))
    if receipt is None:
        raise HTTPException(status_code=404, detail="Goods Receipt tidak ditemukan.")
    return receipt


async def get_invoice_or_404(invoice_id: str) -> SupplierInvoice:
    invoice = await SupplierInvoice.get(parse_object_id(invoice_id, "ID invoice"))
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice supplier tidak ditemukan.")
    return invoice


def purchase_order_response(po: PurchaseOrder, names: dict | None = None) -> PurchaseOrderResponse:
    return PurchaseOrderResponse(
        id=str(po.id),
        poNumber=po.poNumber,
        supplierId=po.supplierId,
        supplierName=(names or {}).get(po.supplierId),
        items=[
            {
                **item.model_dump(),
                "remainingQuantity": max(item.quantity - item.receivedQuantity, 0),
            }
            for item in po.items
        ],
        subtotal=po.subtotal,
        discount=po.discount,
        tax=po.tax,
        shippingCost=po.shippingCost,
        grandTotal=po.grandTotal,
        status=po.status,
        expectedDeliveryDate=po.expectedDeliveryDate,
        notes=po.notes,
        createdBy=po.createdBy,
        submittedAt=po.submittedAt,
        approvedBy=po.approvedBy,
        approvedAt=po.approvedAt,
        orderedAt=po.orderedAt,
        completedAt=po.completedAt,
        cancelledAt=po.cancelledAt,
        createdAt=po.createdAt,
        updatedAt=po.updatedAt,
    )


def goods_receipt_response(
    receipt: GoodsReceipt,
    names: dict | None = None,
    po_numbers: dict | None = None,
) -> GoodsReceiptResponse:
    return GoodsReceiptResponse(
        id=str(receipt.id),
        receiptNumber=receipt.receiptNumber,
        purchaseOrderId=receipt.purchaseOrderId,
        poNumber=(po_numbers or {}).get(receipt.purchaseOrderId),
        supplierId=receipt.supplierId,
        supplierName=(names or {}).get(receipt.supplierId),
        items=[item.model_dump() for item in receipt.items],
        receivedBy=receipt.receivedBy,
        receivedAt=receipt.receivedAt,
        notes=receipt.notes,
    )


def purchase_response(purchase: Purchase, names: dict | None = None) -> PurchaseResponse:
    return PurchaseResponse(
        id=str(purchase.id),
        purchaseNumber=purchase.purchaseNumber,
        supplierId=purchase.supplierId,
        supplierName=(names or {}).get(purchase.supplierId),
        purchaseOrderId=purchase.purchaseOrderId,
        receiptId=purchase.receiptId,
        items=[item.model_dump() for item in purchase.items],
        subtotal=purchase.subtotal,
        discount=purchase.discount,
        total=purchase.total,
        paymentStatus=purchase.paymentStatus,
        createdBy=purchase.createdBy,
        createdAt=purchase.createdAt,
    )


def supplier_invoice_response(
    invoice: SupplierInvoice,
    payable: dict | None = None,
    names: dict | None = None,
) -> SupplierInvoiceResponse:
    payable = payable or invoice_payable(invoice)
    return SupplierInvoiceResponse(
        id=str(invoice.id),
        invoiceNumber=invoice.invoiceNumber,
        supplierId=invoice.supplierId,
        supplierName=(names or {}).get(invoice.supplierId) or payable.get("supplierName"),
        purchaseOrderId=invoice.purchaseOrderId,
        receiptId=invoice.receiptId,
        invoiceDate=invoice.invoiceDate,
        dueDate=invoice.dueDate,
        subtotal=invoice.subtotal,
        tax=invoice.tax,
        shippingCost=invoice.shippingCost,
        total=invoice.total,
        returnedAmount=invoice.returnedAmount,
        paidAmount=payable["paid"],
        outstanding=payable["outstanding"],
        isOverdue=payable["isOverdue"],
        paymentStatus=payable["paymentStatus"],
        notes=invoice.notes,
        createdAt=invoice.createdAt,
        updatedAt=invoice.updatedAt,
    )


def supplier_payment_response(
    payment: SupplierPayment,
    names: dict | None = None,
    invoice_numbers: dict | None = None,
) -> SupplierPaymentResponse:
    return SupplierPaymentResponse(
        id=str(payment.id),
        supplierId=payment.supplierId,
        supplierName=(names or {}).get(payment.supplierId),
        invoiceId=payment.invoiceId,
        invoiceNumber=(invoice_numbers or {}).get(payment.invoiceId),
        paymentNumber=payment.paymentNumber,
        amount=payment.amount,
        method=payment.method,
        paymentDate=payment.paymentDate,
        referenceNumber=payment.referenceNumber,
        createdBy=payment.createdBy,
        notes=payment.notes,
        createdAt=payment.createdAt,
    )


# ===========================================================================
# Hutang supplier (PRD §18, BR-08)
# ===========================================================================


def settled_status(outstanding: float, paid: float) -> PaymentStatus:
    if outstanding <= 0.005:
        return PaymentStatus.PAID
    if paid > 0:
        return PaymentStatus.PARTIALLY_PAID
    return PaymentStatus.UNPAID


def invoice_payable(invoice: SupplierInvoice, supplier_name: str | None = None) -> dict:
    """
    Sisa Hutang = Total Invoice - Kredit Retur - Total Pembayaran.
    Status OVERDUE diturunkan saat jatuh tempo lewat & masih ada sisa.
    """
    paid = round(invoice.paidAmount, 2)
    returned = round(invoice.returnedAmount, 2)
    outstanding = round(max(invoice.total - returned - paid, 0), 2)
    due_date = as_utc(invoice.dueDate)
    now = utc_now()

    status = settled_status(outstanding, paid)
    is_overdue = outstanding > 0 and due_date < now
    if is_overdue:
        status = PaymentStatus.OVERDUE

    return {
        "invoiceId": str(invoice.id),
        "invoiceNumber": invoice.invoiceNumber,
        "supplierId": invoice.supplierId,
        "supplierName": supplier_name,
        "invoiceDate": invoice.invoiceDate,
        "total": invoice.total,
        "returned": returned,
        "paid": paid,
        "outstanding": outstanding,
        "paymentStatus": status,
        "dueDate": due_date,
        "isOverdue": is_overdue,
        "daysOverdue": max((now - due_date).days, 0) if is_overdue else 0,
    }


async def compute_payables(invoices: list[SupplierInvoice]) -> list[dict]:
    names = await supplier_name_map({i.supplierId for i in invoices})
    return [invoice_payable(i, names.get(i.supplierId)) for i in invoices]


# ===========================================================================
# Purchase Order
# ===========================================================================


async def _build_po_items(payload: PurchaseOrderCreate) -> list[PurchaseOrderItem]:
    supplier = await Supplier.get(parse_object_id(payload.supplierId, "ID supplier"))
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan.")
    if supplier.status != SupplierStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Supplier tidak aktif dan tidak dapat digunakan untuk Purchase Order.",
        )

    items: list[PurchaseOrderItem] = []
    seen_products: set[str] = set()

    for line in payload.items:
        sp = await SupplierProduct.get(parse_object_id(line.supplierProductId, "ID produk supplier"))
        if sp is None:
            raise HTTPException(status_code=404, detail="Produk supplier tidak ditemukan.")
        if sp.supplierId != payload.supplierId:
            raise HTTPException(
                status_code=422,
                detail="Produk supplier tidak sesuai dengan supplier Purchase Order.",
            )
        if line.productId and line.productId != sp.productId:
            raise HTTPException(
                status_code=422,
                detail="productId tidak sesuai dengan produk supplier yang dipilih.",
            )
        if not sp.isActive:
            raise HTTPException(
                status_code=400,
                detail=f"Produk supplier {sp.supplierSku} tidak aktif.",
            )
        if sp.productId in seen_products:
            raise HTTPException(
                status_code=422,
                detail="Produk yang sama tidak boleh muncul dua kali dalam satu PO.",
            )
        seen_products.add(sp.productId)

        product = await Product.get(parse_object_id(sp.productId, "ID produk"))
        if product is None:
            raise HTTPException(status_code=404, detail="Produk tidak ditemukan.")
        if not product.isActive:
            raise HTTPException(status_code=400, detail=f"Produk {product.name} tidak aktif.")

        if line.quantity < sp.minimumOrder:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Jumlah {product.name} minimal {sp.minimumOrder} "
                    "sesuai minimum order supplier."
                ),
            )

        unit_price = sp.purchasePrice if line.unitPrice is None else line.unitPrice
        items.append(
            PurchaseOrderItem(
                productId=sp.productId,
                sku=product.sku,
                name=product.name,
                supplierProductId=str(sp.id),
                quantity=line.quantity,
                unitPrice=unit_price,
                subtotal=round(line.quantity * unit_price, 2),
            )
        )

    return items


def _po_totals(items: list[PurchaseOrderItem], discount: float, tax: float, shipping: float):
    subtotal = round(sum(item.subtotal for item in items), 2)
    if discount > subtotal:
        raise HTTPException(status_code=422, detail="Diskon tidak boleh melebihi subtotal.")
    grand_total = round(subtotal - discount + tax + shipping, 2)
    return subtotal, grand_total


async def create_purchase_order(payload: PurchaseOrderCreate, user_id: str) -> PurchaseOrder:
    items = await _build_po_items(payload)
    subtotal, grand_total = _po_totals(items, payload.discount, payload.tax, payload.shippingCost)
    now = utc_now()

    po = PurchaseOrder(
        poNumber=await next_document_number("PO"),
        supplierId=payload.supplierId,
        items=items,
        subtotal=subtotal,
        discount=payload.discount,
        tax=payload.tax,
        shippingCost=payload.shippingCost,
        grandTotal=grand_total,
        status=POStatus.PENDING_APPROVAL if payload.submit else POStatus.DRAFT,
        expectedDeliveryDate=payload.expectedDeliveryDate,
        notes=payload.notes,
        createdBy=user_id,
        submittedAt=now if payload.submit else None,
        createdAt=now,
        updatedAt=now,
    )
    await po.insert()

    await create_activity(
        entity_type=ActivityEntityType.PURCHASE_ORDER,
        entity_id=str(po.id),
        activity_type=ActivityType.CREATED,
        actor_id=user_id,
        reference_number=po.poNumber,
        description=f"Purchase Order {po.poNumber} dibuat"
        + (" dan diajukan untuk approval" if payload.submit else ""),
    )
    return po


async def update_purchase_order(po_id: str, payload: PurchaseOrderUpdate, user_id: str) -> PurchaseOrder:
    po = await get_po_or_404(po_id)

    if po.status != POStatus.DRAFT:
        raise HTTPException(status_code=409, detail="Hanya PO berstatus DRAFT yang dapat diubah.")

    items = await _build_po_items(payload)
    subtotal, grand_total = _po_totals(items, payload.discount, payload.tax, payload.shippingCost)
    now = utc_now()

    po.supplierId = payload.supplierId
    po.items = items
    po.subtotal = subtotal
    po.discount = payload.discount
    po.tax = payload.tax
    po.shippingCost = payload.shippingCost
    po.grandTotal = grand_total
    po.expectedDeliveryDate = payload.expectedDeliveryDate
    po.notes = payload.notes
    if payload.submit:
        po.status = POStatus.PENDING_APPROVAL
        po.submittedAt = now
    po.updatedAt = now
    await po.save()

    await create_activity(
        entity_type=ActivityEntityType.PURCHASE_ORDER,
        entity_id=str(po.id),
        activity_type=ActivityType.UPDATED,
        actor_id=user_id,
        reference_number=po.poNumber,
        description=f"Purchase Order {po.poNumber} diperbarui",
    )
    return po


async def _transition(
    po_id: str,
    *,
    allowed: set[POStatus],
    new_status: POStatus,
    user_id: str,
    activity: ActivityType,
    description: str,
    error: str,
    extra: dict | None = None,
) -> PurchaseOrder:
    po = await get_po_or_404(po_id)
    if po.status not in allowed:
        raise HTTPException(status_code=409, detail=error)

    now = utc_now()
    update = {"status": new_status.value, "updatedAt": now, **(extra or {})}

    # Update kondisional: status tidak berubah oleh request lain di tengah jalan.
    result = await PurchaseOrder.get_pymongo_collection().update_one(
        {"_id": po.id, "status": po.status.value},
        {"$set": update, "$inc": {"revision": 1}},
    )
    if result.modified_count != 1:
        raise HTTPException(status_code=409, detail="Status PO berubah. Muat ulang halaman.")

    po = await get_po_or_404(po_id)
    await create_activity(
        entity_type=ActivityEntityType.PURCHASE_ORDER,
        entity_id=str(po.id),
        activity_type=activity,
        actor_id=user_id,
        reference_number=po.poNumber,
        description=description.format(po=po.poNumber),
    )
    return po


async def submit_purchase_order(po_id: str, user_id: str) -> PurchaseOrder:
    return await _transition(
        po_id,
        allowed={POStatus.DRAFT},
        new_status=POStatus.PENDING_APPROVAL,
        user_id=user_id,
        activity=ActivityType.SUBMITTED,
        description="Purchase Order {po} diajukan untuk approval",
        error="Hanya PO berstatus DRAFT yang dapat diajukan.",
        extra={"submittedAt": utc_now()},
    )


async def approve_purchase_order(po_id: str, user_id: str) -> PurchaseOrder:
    po = await get_po_or_404(po_id)
    if po.status != POStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=409,
            detail="Hanya PO berstatus PENDING_APPROVAL yang dapat disetujui.",
        )
    if po.createdBy == user_id:
        # Segregation of duties: pembuat PO tidak boleh menyetujui PO-nya sendiri.
        raise HTTPException(
            status_code=403,
            detail="Pembuat PO tidak dapat menyetujui PO miliknya sendiri.",
        )
    now = utc_now()
    return await _transition(
        po_id,
        allowed={POStatus.PENDING_APPROVAL},
        new_status=POStatus.APPROVED,
        user_id=user_id,
        activity=ActivityType.APPROVED,
        description="Purchase Order {po} disetujui",
        error="Hanya PO berstatus PENDING_APPROVAL yang dapat disetujui.",
        extra={"approvedBy": user_id, "approvedAt": now},
    )


async def reject_purchase_order(po_id: str, user_id: str) -> PurchaseOrder:
    """Approval ditolak -> kembali ke DRAFT untuk direvisi."""
    return await _transition(
        po_id,
        allowed={POStatus.PENDING_APPROVAL},
        new_status=POStatus.DRAFT,
        user_id=user_id,
        activity=ActivityType.UPDATED,
        description="Approval Purchase Order {po} ditolak, dikembalikan ke DRAFT",
        error="Hanya PO berstatus PENDING_APPROVAL yang dapat ditolak.",
        extra={"submittedAt": None},
    )


async def order_purchase_order(po_id: str, user_id: str) -> PurchaseOrder:
    return await _transition(
        po_id,
        allowed={POStatus.APPROVED},
        new_status=POStatus.ORDERED,
        user_id=user_id,
        activity=ActivityType.ORDERED,
        description="Purchase Order {po} dikirim ke supplier (ORDERED)",
        error="Hanya PO berstatus APPROVED yang dapat dikirim ke supplier.",
        extra={"orderedAt": utc_now()},
    )


async def cancel_purchase_order(po_id: str, user_id: str) -> PurchaseOrder:
    po = await get_po_or_404(po_id)
    if await GoodsReceipt.find_one({"purchaseOrderId": str(po.id)}):
        raise HTTPException(
            status_code=409,
            detail="PO yang sudah memiliki penerimaan barang tidak dapat dibatalkan. Gunakan 'Selesaikan PO'.",
        )
    return await _transition(
        po_id,
        allowed={POStatus.DRAFT, POStatus.PENDING_APPROVAL, POStatus.APPROVED, POStatus.ORDERED},
        new_status=POStatus.CANCELLED,
        user_id=user_id,
        activity=ActivityType.CANCELLED,
        description="Purchase Order {po} dibatalkan",
        error="PO tidak dapat dibatalkan dari status saat ini.",
        extra={"cancelledBy": user_id, "cancelledAt": utc_now()},
    )


async def complete_purchase_order(po_id: str, user_id: str, notes: str | None) -> PurchaseOrder:
    """
    Menutup PO: RECEIVED -> COMPLETED, atau PARTIALLY_RECEIVED -> COMPLETED
    bila sisa barang dipastikan tidak akan dikirim supplier.
    """
    extra: dict = {"completedAt": utc_now()}
    if notes:
        extra["notes"] = notes
    return await _transition(
        po_id,
        allowed={POStatus.RECEIVED, POStatus.PARTIALLY_RECEIVED},
        new_status=POStatus.COMPLETED,
        user_id=user_id,
        activity=ActivityType.COMPLETED,
        description="Purchase Order {po} diselesaikan (COMPLETED)",
        error="Hanya PO yang sudah diterima (sebagian/penuh) yang dapat diselesaikan.",
        extra=extra,
    )


# ===========================================================================
# Goods Receipt (PRD §15, BR-05, BR-06)
# ===========================================================================


async def create_goods_receipt(payload: GoodsReceiptCreate, user: User) -> GoodsReceipt:
    user_id = str(user.id)
    po = await get_po_or_404(payload.purchaseOrderId)

    if po.status not in {POStatus.ORDERED, POStatus.PARTIALLY_RECEIVED}:
        raise HTTPException(
            status_code=409,
            detail="Barang hanya dapat diterima untuk PO berstatus ORDERED / PARTIALLY_RECEIVED.",
        )

    po_items = {item.productId: item for item in po.items}
    seen: set[str] = set()
    receipt_items: list[GoodsReceiptItem] = []

    for line in payload.items:
        po_item = po_items.get(line.productId)
        if po_item is None:
            raise HTTPException(
                status_code=422,
                detail=f"Produk {line.productId} bukan bagian dari PO ini.",
            )
        if line.productId in seen:
            raise HTTPException(status_code=422, detail="Produk duplikat dalam penerimaan.")
        seen.add(line.productId)

        remaining = po_item.quantity - po_item.receivedQuantity
        if line.receivedQuantity > remaining:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Jumlah diterima {po_item.name} ({line.receivedQuantity}) "
                    f"melebihi sisa PO ({remaining})."
                ),
            )

        receipt_items.append(
            GoodsReceiptItem(
                productId=po_item.productId,
                sku=po_item.sku,
                name=po_item.name,
                unitPrice=po_item.unitPrice,
                orderedQuantity=po_item.quantity,
                previouslyReceivedQuantity=po_item.receivedQuantity,
                receivedQuantity=line.receivedQuantity,
                acceptedQuantity=line.acceptedQuantity,
                rejectedQuantity=line.rejectedQuantity,
                rejectionReason=(line.rejectionReason or None),
            )
        )

    # Hitung status PO baru.
    received_now = {i.productId: i for i in receipt_items}
    new_items = []
    all_received = True
    for item in po.items:
        line = received_now.get(item.productId)
        updated = item.model_copy()
        if line:
            updated.receivedQuantity += line.receivedQuantity
            updated.acceptedQuantity += line.acceptedQuantity
        if updated.receivedQuantity < updated.quantity:
            all_received = False
        new_items.append(updated)

    new_status = POStatus.RECEIVED if all_received else POStatus.PARTIALLY_RECEIVED
    now = utc_now()

    async with unit_of_work() as uow:
        # Optimistic lock pada PO: mencegah dua penerimaan bersamaan
        # melebihi qty PO.
        po_collection = PurchaseOrder.get_pymongo_collection()
        result = await po_collection.update_one(
            {"_id": po.id, "revision": po.revision, "status": po.status.value},
            {
                "$set": {
                    "items": [i.model_dump() for i in new_items],
                    "status": new_status.value,
                    "updatedAt": now,
                },
                "$inc": {"revision": 1},
            },
            session=uow.session,
        )
        if result.modified_count != 1:
            raise HTTPException(
                status_code=409,
                detail="PO sedang diproses oleh pengguna lain. Muat ulang lalu ulangi.",
            )
        previous = {
            "items": [i.model_dump() for i in po.items],
            "status": po.status.value,
            "updatedAt": po.updatedAt,
        }
        uow.on_rollback(
            lambda: po_collection.update_one(
                {"_id": po.id}, {"$set": previous, "$inc": {"revision": 1}}
            )
        )

        receipt = GoodsReceipt(
            receiptNumber=await next_document_number("GR"),
            purchaseOrderId=str(po.id),
            supplierId=po.supplierId,
            items=receipt_items,
            receivedBy=user_id,
            receivedAt=payload.receivedAt or now,
            notes=payload.notes,
        )
        await uow.insert(receipt)

        product_collection = Product.get_pymongo_collection()
        for item in receipt_items:
            # Hanya acceptedQuantity yang menambah stok (PRD §15).
            if item.acceptedQuantity <= 0:
                continue
            await apply_stock_change(
                uow,
                product_id=item.productId,
                delta=item.acceptedQuantity,
                movement_type=StockMovementType.PURCHASE,
                user_id=user_id,
                reference_type="GOODS_RECEIPT",
                reference_id=str(receipt.id),
                reference_number=receipt.receiptNumber,
                reason=f"Penerimaan {po.poNumber}",
            )
            # Harga beli produk mengikuti harga pembelian terakhir; dipakai
            # sebagai dasar HPP (snapshot) pada transaksi penjualan berikutnya.
            previous_product = await product_collection.find_one_and_update(
                {"_id": ObjectId(item.productId)},
                {"$set": {"purchasePrice": item.unitPrice}},
                session=uow.session,
            )
            if previous_product is not None:
                uow.on_rollback(
                    lambda pid=item.productId, old=previous_product.get("purchasePrice", 0): (
                        product_collection.update_one(
                            {"_id": ObjectId(pid)}, {"$set": {"purchasePrice": old}}
                        )
                    )
                )

        await create_activity(
            entity_type=ActivityEntityType.GOODS_RECEIPT,
            entity_id=str(receipt.id),
            activity_type=ActivityType.RECEIVED,
            actor_id=user_id,
            reference_number=receipt.receiptNumber,
            description=(
                f"Goods Receipt {receipt.receiptNumber} untuk PO {po.poNumber} "
                f"({new_status.value})"
            ),
            session=uow.session,
        )

    return receipt


# ===========================================================================
# Purchase (PRD §16)
# ===========================================================================


async def create_purchase(payload: PurchaseCreate, user_id: str) -> Purchase:
    receipt = await get_receipt_or_404(payload.receiptId)

    if await Purchase.find_one({"receiptId": str(receipt.id)}):
        raise HTTPException(status_code=409, detail="Pembelian untuk Goods Receipt ini sudah dibuat.")

    purchase_items = [
        PurchaseItem(
            productId=item.productId,
            name=item.name,
            quantity=item.acceptedQuantity,
            price=item.unitPrice,
            subtotal=round(item.acceptedQuantity * item.unitPrice, 2),
        )
        for item in receipt.items
        if item.acceptedQuantity > 0
    ]

    if not purchase_items:
        raise HTTPException(
            status_code=422,
            detail="Goods Receipt tidak memiliki barang yang diterima baik.",
        )

    # Data lama: unitPrice belum ada di receipt -> ambil dari PO.
    if any(item.price == 0 for item in purchase_items):
        po = await get_po_or_404(receipt.purchaseOrderId)
        prices = {i.productId: i.unitPrice for i in po.items}
        for item in purchase_items:
            if item.price == 0:
                item.price = prices.get(item.productId, 0)
                item.subtotal = round(item.quantity * item.price, 2)

    subtotal = round(sum(i.subtotal for i in purchase_items), 2)
    if payload.discount > subtotal:
        raise HTTPException(status_code=422, detail="Diskon tidak boleh melebihi subtotal.")

    purchase = Purchase(
        purchaseNumber=await next_document_number("PUR"),
        supplierId=receipt.supplierId,
        purchaseOrderId=receipt.purchaseOrderId,
        receiptId=str(receipt.id),
        items=purchase_items,
        subtotal=subtotal,
        discount=payload.discount,
        total=round(subtotal - payload.discount, 2),
        paymentStatus=PaymentStatus.UNPAID,
        createdBy=user_id,
        createdAt=utc_now(),
    )
    await purchase.insert()

    await create_activity(
        entity_type=ActivityEntityType.PURCHASE,
        entity_id=str(purchase.id),
        activity_type=ActivityType.CREATED,
        actor_id=user_id,
        reference_number=purchase.purchaseNumber,
        description=f"Pembelian {purchase.purchaseNumber} dicatat dari {receipt.receiptNumber}",
    )
    return purchase


# ===========================================================================
# Supplier Invoice (PRD §17)
# ===========================================================================


async def create_supplier_invoice(payload: SupplierInvoiceCreate, user_id: str) -> SupplierInvoice:
    receipt = await get_receipt_or_404(payload.receiptId)

    purchase = await Purchase.find_one({"receiptId": str(receipt.id)})
    if purchase is None:
        raise HTTPException(
            status_code=409,
            detail="Catat pembelian (Purchase) terlebih dahulu sebelum membuat invoice.",
        )

    if await SupplierInvoice.find_one({"receiptId": str(receipt.id)}):
        raise HTTPException(status_code=409, detail="Invoice untuk Goods Receipt ini sudah ada.")

    invoice_number = payload.invoiceNumber.strip()
    if await SupplierInvoice.find_one({"invoiceNumber": invoice_number}):
        raise HTTPException(status_code=409, detail="Nomor invoice sudah digunakan.")

    due_date = payload.dueDate
    if due_date is None:
        supplier = await Supplier.get(parse_object_id(receipt.supplierId, "ID supplier"))
        term_days = supplier.paymentTerm.days if supplier else 0
        due_date = payload.invoiceDate + timedelta(days=term_days)

    if as_utc(due_date) < as_utc(payload.invoiceDate):
        raise HTTPException(status_code=422, detail="Tanggal jatuh tempo tidak boleh sebelum tanggal invoice.")

    # Retur pembelian yang sudah disetujui sebelum invoice dibuat langsung
    # menjadi kredit invoice.
    from app.models.returns import Return, ReturnStatus, ReturnType

    prior_returns = await Return.find(
        {
            "type": ReturnType.PURCHASE.value,
            "receiptId": str(receipt.id),
            "status": ReturnStatus.APPROVED.value,
            "supplierInvoiceId": None,
        }
    ).to_list()
    returned_amount = round(sum(r.totalAmount for r in prior_returns), 2)

    now = utc_now()
    invoice = SupplierInvoice(
        invoiceNumber=invoice_number,
        supplierId=receipt.supplierId,
        purchaseOrderId=receipt.purchaseOrderId,
        receiptId=str(receipt.id),
        invoiceDate=payload.invoiceDate,
        dueDate=due_date,
        subtotal=purchase.total,
        tax=payload.tax,
        shippingCost=payload.shippingCost,
        total=round(purchase.total + payload.tax + payload.shippingCost, 2),
        returnedAmount=returned_amount,
        paidAmount=0,
        paymentStatus=PaymentStatus.UNPAID,
        notes=payload.notes,
        createdBy=user_id,
        createdAt=now,
        updatedAt=now,
    )
    await invoice.insert()

    for ret in prior_returns:
        ret.supplierInvoiceId = str(invoice.id)
        await ret.save()

    await create_activity(
        entity_type=ActivityEntityType.SUPPLIER_INVOICE,
        entity_id=str(invoice.id),
        activity_type=ActivityType.CREATED,
        actor_id=user_id,
        reference_number=invoice.invoiceNumber,
        description=f"Invoice supplier {invoice.invoiceNumber} dicatat",
    )
    return invoice


async def refresh_invoice_status(invoice_id: str, session=None) -> None:
    """Sinkronkan paymentStatus invoice & purchase dari angka terbaru."""
    collection = SupplierInvoice.get_pymongo_collection()
    doc = await collection.find_one({"_id": ObjectId(invoice_id)}, session=session)
    if not doc:
        return
    outstanding = max(doc["total"] - doc.get("returnedAmount", 0) - doc.get("paidAmount", 0), 0)
    status = settled_status(outstanding, doc.get("paidAmount", 0))
    await collection.update_one(
        {"_id": doc["_id"]},
        {"$set": {"paymentStatus": status.value, "updatedAt": utc_now()}},
        session=session,
    )
    await Purchase.get_pymongo_collection().update_one(
        {"receiptId": doc["receiptId"]},
        {"$set": {"paymentStatus": status.value}},
        session=session,
    )


# ===========================================================================
# Supplier Payment (PRD §19, BR-08)
# ===========================================================================


async def create_supplier_payment(payload: SupplierPaymentCreate, user: User) -> SupplierPayment:
    user_id = str(user.id)
    invoice = await get_invoice_or_404(payload.invoiceId)

    payable = invoice_payable(invoice)
    if payable["outstanding"] <= 0:
        raise HTTPException(status_code=409, detail="Invoice supplier sudah lunas.")
    if payload.amount - payable["outstanding"] > 0.005:
        raise HTTPException(
            status_code=422,
            detail=f"Jumlah pembayaran melebihi sisa hutang ({payable['outstanding']:,.0f}).",
        )

    async with unit_of_work() as uow:
        collection = SupplierInvoice.get_pymongo_collection()
        # Dijalankan paling akhir saat kompensasi: status kembali sinkron.
        uow.on_rollback(lambda: refresh_invoice_status(str(invoice.id)))
        # Guard atomik: paidAmount + amount <= total - returnedAmount.
        limit = invoice.total - invoice.returnedAmount - payload.amount + 0.005
        result = await collection.update_one(
            {"_id": invoice.id, "paidAmount": {"$lte": limit}, "returnedAmount": invoice.returnedAmount},
            {"$inc": {"paidAmount": payload.amount}, "$set": {"updatedAt": utc_now()}},
            session=uow.session,
        )
        if result.modified_count != 1:
            raise HTTPException(
                status_code=409,
                detail="Sisa hutang berubah saat diproses. Muat ulang lalu ulangi.",
            )
        uow.on_rollback(
            lambda: collection.update_one(
                {"_id": invoice.id}, {"$inc": {"paidAmount": -payload.amount}}
            )
        )

        payment = SupplierPayment(
            supplierId=invoice.supplierId,
            invoiceId=str(invoice.id),
            paymentNumber=await next_document_number("PAY-SUP"),
            amount=payload.amount,
            method=payload.method,
            paymentDate=payload.paymentDate,
            referenceNumber=payload.referenceNumber,
            createdBy=user_id,
            notes=payload.notes,
            createdAt=utc_now(),
        )
        await uow.insert(payment)

        await refresh_invoice_status(str(invoice.id), session=uow.session)

        await create_activity(
            entity_type=ActivityEntityType.SUPPLIER_PAYMENT,
            entity_id=str(payment.id),
            activity_type=ActivityType.PAID,
            actor_id=user_id,
            reference_number=payment.paymentNumber,
            description=(
                f"Pembayaran {payment.paymentNumber} sebesar Rp{payment.amount:,.0f} "
                f"untuk invoice {invoice.invoiceNumber}"
            ),
            session=uow.session,
        )

    return payment

