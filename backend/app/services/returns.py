"""
Retur penjualan (PRD §25) & retur pembelian (PRD §26, §37.3).

Keduanya melalui approval. Stok baru berubah saat retur disetujui:
- Retur penjualan: stok += quantity (BR-01), movement SALE_RETURN,
  refund dicatat di collection payments.
- Retur pembelian: stok -= quantity (BR-01, tidak boleh minus), movement
  PURCHASE_RETURN, dan hutang/invoice supplier dikoreksi (kredit retur).
"""

from datetime import date

from bson import ObjectId
from fastapi import HTTPException

from app.core.uow import unit_of_work
from app.core.utils import (
    PageParams,
    inc_embedded_item,
    local_range_bounds,
    next_document_number,
    parse_object_id,
    utc_now,
)
from app.models.audit_log import AuditAction, AuditModule
from app.models.inventory import StockMovementType
from app.models.procurement import GoodsReceipt, SupplierInvoice
from app.models.returns import Return, ReturnItem, ReturnStatus, ReturnType
from app.models.sales import Sale, SalePayment, SalePaymentType, SaleStatus
from app.models.supplier import Supplier
from app.models.user import User, UserRole
from app.schemas.returns import (
    PurchaseReturnCreate,
    ReturnItemResponse,
    ReturnResponse,
    SalesReturnCreate,
)
from app.services.audit import log_audit
from app.services.procurement import refresh_invoice_status
from app.services.stock import apply_stock_change


async def _lookup(model, ids: set[str]) -> dict:
    object_ids = [ObjectId(i) for i in ids if i and ObjectId.is_valid(i)]
    if not object_ids:
        return {}
    return {str(d.id): d for d in await model.find({"_id": {"$in": object_ids}}).to_list()}


async def build_return_responses(returns: list[Return]) -> list[ReturnResponse]:
    users = await _lookup(User, {r.createdBy for r in returns} | {r.approvedBy for r in returns if r.approvedBy})
    suppliers = await _lookup(Supplier, {r.supplierId for r in returns if r.supplierId})
    receipts = await _lookup(GoodsReceipt, {r.receiptId for r in returns if r.receiptId})

    def name(mapping, key):
        doc = mapping.get(key or "")
        return getattr(doc, "name", None) if doc else None

    return [
        ReturnResponse(
            id=str(r.id),
            returnNumber=r.returnNumber,
            type=r.type,
            status=r.status,
            saleId=r.saleId,
            saleInvoiceNumber=r.saleInvoiceNumber,
            memberId=r.memberId,
            supplierId=r.supplierId,
            supplierName=name(suppliers, r.supplierId),
            purchaseOrderId=r.purchaseOrderId,
            receiptId=r.receiptId,
            receiptNumber=(
                receipts[r.receiptId].receiptNumber if r.receiptId in receipts else None
            ),
            supplierInvoiceId=r.supplierInvoiceId,
            items=[ReturnItemResponse(**i.model_dump()) for i in r.items],
            totalAmount=r.totalAmount,
            reason=r.reason,
            notes=r.notes,
            createdBy=r.createdBy,
            createdByName=name(users, r.createdBy),
            approvedBy=r.approvedBy,
            approvedByName=name(users, r.approvedBy),
            approvedAt=r.approvedAt,
            rejectionReason=r.rejectionReason,
            createdAt=r.createdAt,
            updatedAt=r.updatedAt,
        )
        for r in returns
    ]


async def get_return_or_404(return_id: str) -> Return:
    ret = await Return.get(parse_object_id(return_id, "ID retur"))
    if ret is None:
        raise HTTPException(status_code=404, detail="Retur tidak ditemukan.")
    return ret


async def _pending_quantities(query: dict) -> dict[str, float]:
    pending: dict[str, float] = {}
    for ret in await Return.find(
        {**query, "status": ReturnStatus.PENDING_APPROVAL.value}
    ).to_list():
        for item in ret.items:
            pending[item.productId] = pending.get(item.productId, 0) + item.quantity
    return pending


def _merge(items) -> dict[str, float]:
    merged: dict[str, float] = {}
    for item in items:
        merged[item.productId] = merged.get(item.productId, 0) + item.quantity
    return merged


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def create_sales_return(payload: SalesReturnCreate, user: User, ip: str | None) -> Return:
    if payload.saleId:
        sale = await Sale.get(parse_object_id(payload.saleId, "ID transaksi"))
    else:
        sale = await Sale.find_one({"invoiceNumber": (payload.invoiceNumber or "").strip()})
    if sale is None:
        raise HTTPException(status_code=404, detail="Transaksi penjualan tidak ditemukan.")
    if sale.status != SaleStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Retur hanya untuk transaksi berstatus COMPLETED.")
    if user.role == UserRole.KASIR and sale.cashierId != str(user.id):
        raise HTTPException(status_code=403, detail="Kasir hanya dapat meretur transaksi miliknya.")

    sold = {i.productId: i for i in sale.items}
    pending = await _pending_quantities({"saleId": str(sale.id)})
    ratio = (sale.total / sale.subtotal) if sale.subtotal else 1

    items: list[ReturnItem] = []
    for product_id, quantity in _merge(payload.items).items():
        sale_item = sold.get(product_id)
        if sale_item is None:
            raise HTTPException(status_code=422, detail="Produk tidak ada dalam transaksi ini.")
        available = sale_item.quantity - sale_item.returnedQuantity - pending.get(product_id, 0)
        if quantity > available + 1e-9:
            raise HTTPException(
                status_code=422,
                detail=f"Jumlah retur {sale_item.name} melebihi yang dapat diretur ({available:g}).",
            )
        # Nilai refund memperhitungkan diskon transaksi secara proporsional.
        price = round(sale_item.price * ratio, 2)
        items.append(
            ReturnItem(
                productId=product_id,
                sku=sale_item.sku,
                name=sale_item.name,
                quantity=quantity,
                price=price,
                costPrice=sale_item.costPrice,
                subtotal=round(price * quantity, 2),
            )
        )

    ret = Return(
        returnNumber=await next_document_number("RTS"),
        type=ReturnType.SALE,
        saleId=str(sale.id),
        saleInvoiceNumber=sale.invoiceNumber,
        memberId=sale.memberId,
        items=items,
        totalAmount=round(sum(i.subtotal for i in items), 2),
        reason=payload.reason,
        notes=payload.notes,
        createdBy=str(user.id),
    )
    await ret.insert()

    await log_audit(
        action=AuditAction.RETURN,
        module=AuditModule.RETURN,
        description=f"Pengajuan retur penjualan {ret.returnNumber} untuk {sale.invoiceNumber}",
        user=user,
        reference_id=str(ret.id),
        ip_address=ip,
    )
    return ret


async def create_purchase_return(payload: PurchaseReturnCreate, user: User, ip: str | None) -> Return:
    receipt = await GoodsReceipt.get(parse_object_id(payload.receiptId, "ID Goods Receipt"))
    if receipt is None:
        raise HTTPException(status_code=404, detail="Goods Receipt tidak ditemukan.")

    received = {i.productId: i for i in receipt.items}
    pending = await _pending_quantities({"receiptId": str(receipt.id)})

    items: list[ReturnItem] = []
    for product_id, quantity in _merge(payload.items).items():
        receipt_item = received.get(product_id)
        if receipt_item is None:
            raise HTTPException(status_code=422, detail="Produk tidak ada dalam penerimaan ini.")
        if quantity != int(quantity):
            raise HTTPException(status_code=422, detail="Jumlah retur pembelian harus bilangan bulat.")
        available = (
            receipt_item.acceptedQuantity
            - receipt_item.returnedQuantity
            - pending.get(product_id, 0)
        )
        if quantity > available:
            raise HTTPException(
                status_code=422,
                detail=f"Jumlah retur {receipt_item.name} melebihi yang dapat diretur ({available:g}).",
            )
        items.append(
            ReturnItem(
                productId=product_id,
                sku=receipt_item.sku,
                name=receipt_item.name,
                quantity=quantity,
                price=receipt_item.unitPrice,
                costPrice=receipt_item.unitPrice,
                subtotal=round(receipt_item.unitPrice * quantity, 2),
            )
        )

    invoice = await SupplierInvoice.find_one({"receiptId": str(receipt.id)})

    ret = Return(
        returnNumber=await next_document_number("RTP"),
        type=ReturnType.PURCHASE,
        supplierId=receipt.supplierId,
        purchaseOrderId=receipt.purchaseOrderId,
        receiptId=str(receipt.id),
        supplierInvoiceId=None,
        items=items,
        totalAmount=round(sum(i.subtotal for i in items), 2),
        reason=payload.reason,
        notes=payload.notes,
        createdBy=str(user.id),
    )
    await ret.insert()

    await log_audit(
        action=AuditAction.RETURN,
        module=AuditModule.RETURN,
        description=(
            f"Pengajuan retur pembelian {ret.returnNumber} untuk {receipt.receiptNumber}"
            + (f" (invoice {invoice.invoiceNumber})" if invoice else "")
        ),
        user=user,
        reference_id=str(ret.id),
        ip_address=ip,
    )
    return ret


# ---------------------------------------------------------------------------
# Approval
# ---------------------------------------------------------------------------


async def _claim_pending(ret: Return, uow, new_status: ReturnStatus, extra: dict) -> None:
    collection = Return.get_pymongo_collection()
    result = await collection.update_one(
        {"_id": ret.id, "status": ReturnStatus.PENDING_APPROVAL.value},
        {"$set": {"status": new_status.value, "updatedAt": utc_now(), **extra}},
        session=uow.session,
    )
    if result.modified_count != 1:
        raise HTTPException(status_code=409, detail="Retur sudah diproses.")
    uow.on_rollback(
        lambda: collection.update_one(
            {"_id": ret.id},
            {"$set": {"status": ReturnStatus.PENDING_APPROVAL.value, "approvedBy": None, "approvedAt": None}},
        )
    )


async def approve_return(return_id: str, user: User, ip: str | None) -> Return:
    ret = await get_return_or_404(return_id)
    if ret.status != ReturnStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=409, detail="Retur sudah diproses.")
    if ret.createdBy == str(user.id):
        raise HTTPException(
            status_code=403,
            detail="Pengaju retur tidak dapat menyetujui returnya sendiri.",
        )

    user_id = str(user.id)
    now = utc_now()

    async with unit_of_work() as uow:
        await _claim_pending(ret, uow, ReturnStatus.APPROVED, {"approvedBy": user_id, "approvedAt": now})

        if ret.type == ReturnType.SALE:
            sale = await Sale.get(parse_object_id(ret.saleId or "", "ID transaksi"))
            if sale is None or sale.status != SaleStatus.COMPLETED:
                raise HTTPException(status_code=409, detail="Transaksi asal tidak lagi berstatus COMPLETED.")

            sale_collection = Sale.get_pymongo_collection()
            for item in ret.items:
                await apply_stock_change(
                    uow,
                    product_id=item.productId,
                    delta=item.quantity,
                    movement_type=StockMovementType.SALE_RETURN,
                    user_id=user_id,
                    reference_type="SALE_RETURN",
                    reference_id=str(ret.id),
                    reference_number=ret.returnNumber,
                    reason=ret.reason.value,
                )
                await inc_embedded_item(
                    sale_collection, sale.id, item.productId, "returnedQuantity",
                    item.quantity, session=uow.session,
                )
                uow.on_rollback(
                    lambda pid=item.productId, qty=item.quantity: inc_embedded_item(
                        sale_collection, sale.id, pid, "returnedQuantity", -qty
                    )
                )

            await uow.insert(
                SalePayment(
                    saleId=str(sale.id),
                    invoiceNumber=sale.invoiceNumber,
                    type=SalePaymentType.REFUND,
                    method=sale.payment.method,
                    amount=ret.totalAmount,
                    referenceId=str(ret.id),
                    paidAt=now,
                    createdBy=user_id,
                )
            )
        else:
            receipt_collection = GoodsReceipt.get_pymongo_collection()
            receipt_oid = parse_object_id(ret.receiptId or "", "ID Goods Receipt")
            for item in ret.items:
                # Stok berkurang; ditolak bila stok saat ini tidak cukup (BR-02).
                await apply_stock_change(
                    uow,
                    product_id=item.productId,
                    delta=-item.quantity,
                    movement_type=StockMovementType.PURCHASE_RETURN,
                    user_id=user_id,
                    reference_type="PURCHASE_RETURN",
                    reference_id=str(ret.id),
                    reference_number=ret.returnNumber,
                    reason=ret.reason.value,
                )
                await inc_embedded_item(
                    receipt_collection, receipt_oid, item.productId, "returnedQuantity",
                    int(item.quantity), session=uow.session,
                )
                uow.on_rollback(
                    lambda pid=item.productId, qty=int(item.quantity): inc_embedded_item(
                        receipt_collection, receipt_oid, pid, "returnedQuantity", -qty
                    )
                )

            # Koreksi hutang: kredit retur pada invoice (jika sudah ada).
            invoice = await SupplierInvoice.find_one({"receiptId": ret.receiptId})
            if invoice is not None:
                invoice_collection = SupplierInvoice.get_pymongo_collection()
                uow.on_rollback(lambda: refresh_invoice_status(str(invoice.id)))
                await invoice_collection.update_one(
                    {"_id": invoice.id},
                    {"$inc": {"returnedAmount": ret.totalAmount}, "$set": {"updatedAt": now}},
                    session=uow.session,
                )
                uow.on_rollback(
                    lambda: invoice_collection.update_one(
                        {"_id": invoice.id}, {"$inc": {"returnedAmount": -ret.totalAmount}}
                    )
                )
                await Return.get_pymongo_collection().update_one(
                    {"_id": ret.id},
                    {"$set": {"supplierInvoiceId": str(invoice.id)}},
                    session=uow.session,
                )
                await refresh_invoice_status(str(invoice.id), session=uow.session)

        await log_audit(
            action=AuditAction.APPROVE,
            module=AuditModule.RETURN,
            description=(
                f"Menyetujui retur {'penjualan' if ret.type == ReturnType.SALE else 'pembelian'} "
                f"{ret.returnNumber} senilai Rp{ret.totalAmount:,.0f}"
            ),
            user=user,
            reference_id=str(ret.id),
            ip_address=ip,
            session=uow.session,
        )

    return await get_return_or_404(return_id)


async def reject_return(return_id: str, reason: str, user: User, ip: str | None) -> Return:
    ret = await get_return_or_404(return_id)
    async with unit_of_work() as uow:
        await _claim_pending(
            ret,
            uow,
            ReturnStatus.REJECTED,
            {"approvedBy": str(user.id), "approvedAt": utc_now(), "rejectionReason": reason},
        )
        await log_audit(
            action=AuditAction.REJECT,
            module=AuditModule.RETURN,
            description=f"Menolak retur {ret.returnNumber}: {reason}",
            user=user,
            reference_id=str(ret.id),
            ip_address=ip,
            session=uow.session,
        )
    return await get_return_or_404(return_id)


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


async def list_returns(
    user: User,
    pagination: PageParams,
    return_type: ReturnType | None = None,
    status: ReturnStatus | None = None,
    sale_id: str | None = None,
    receipt_id: str | None = None,
    supplier_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[ReturnResponse]:
    query: dict = {}
    if user.role == UserRole.KASIR:
        query["type"] = ReturnType.SALE.value
        query["createdBy"] = str(user.id)
    elif return_type:
        query["type"] = return_type.value
    if status:
        query["status"] = status.value
    if sale_id:
        query["saleId"] = sale_id
    if receipt_id:
        query["receiptId"] = receipt_id
    if supplier_id:
        query["supplierId"] = supplier_id

    start, end = local_range_bounds(date_from, date_to)
    if start or end:
        query["createdAt"] = {}
        if start:
            query["createdAt"]["$gte"] = start
        if end:
            query["createdAt"]["$lt"] = end

    returns = await pagination.apply(Return.find(query).sort("-createdAt"))
    return await build_return_responses(returns)
