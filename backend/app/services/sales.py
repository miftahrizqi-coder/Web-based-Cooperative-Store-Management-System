"""
Penjualan / POS (PRD §23-24, §37.2, BR-02, BR-03, BR-04, BR-07).

Transaksi penjualan dijalankan dalam Unit of Work:
validasi stok -> simpan sales -> kurangi stok (atomik) -> stock movement
-> payment -> audit log -> COMMIT (atau ROLLBACK/kompensasi jika gagal).
"""

from datetime import date

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.uow import unit_of_work
from app.core.utils import (
    PageParams,
    local_range_bounds,
    next_document_number,
    parse_object_id,
    search_regex,
    utc_now,
)
from app.models.audit_log import AuditAction, AuditModule
from app.models.inventory import StockMovementType
from app.models.member import Member, MemberStatus
from app.models.product import Product
from app.models.returns import Return, ReturnStatus
from app.models.sales import (
    PaymentMethod,
    Sale,
    SaleItem,
    SalePayment,
    SalePaymentInfo,
    SalePaymentType,
    SaleStatus,
)
from app.models.user import User, UserRole
from app.schemas.sales import (
    SaleCancelResponse,
    SaleCreate,
    SaleItemResponse,
    SalePaymentResponse,
    SaleResponse,
)
from app.services.audit import log_audit
from app.services.stock import apply_stock_change


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------


async def _lookup(model, ids: set[str]) -> dict:
    object_ids = [ObjectId(i) for i in ids if i and ObjectId.is_valid(i)]
    if not object_ids:
        return {}
    return {str(d.id): d for d in await model.find({"_id": {"$in": object_ids}}).to_list()}


def _sale_response(sale: Sale, viewer: User, users: dict, members: dict) -> SaleResponse:
    can_see_cost = viewer.role in {UserRole.ADMIN, UserRole.PENGURUS}
    member = members.get(sale.memberId or "")
    cashier = users.get(sale.cashierId)
    return SaleResponse(
        id=str(sale.id),
        invoiceNumber=sale.invoiceNumber,
        cashierId=sale.cashierId,
        cashierName=cashier.name if cashier else None,
        memberId=sale.memberId,
        memberName=member.name if member else None,
        memberNumber=member.memberNumber if member else None,
        items=[
            SaleItemResponse(
                productId=item.productId,
                sku=item.sku,
                name=item.name,
                unit=item.unit,
                quantity=item.quantity,
                price=item.price,
                costPrice=item.costPrice if can_see_cost else None,
                subtotal=item.subtotal,
                returnedQuantity=item.returnedQuantity,
            )
            for item in sale.items
        ],
        subtotal=sale.subtotal,
        discount=sale.discount,
        total=sale.total,
        payment=SalePaymentResponse(**sale.payment.model_dump()),
        status=sale.status,
        cancelledBy=sale.cancelledBy,
        cancelledAt=sale.cancelledAt,
        cancelReason=sale.cancelReason,
        createdAt=sale.createdAt,
        updatedAt=sale.updatedAt,
    )


async def build_sale_responses(sales: list[Sale], viewer: User) -> list[SaleResponse]:
    users = await _lookup(User, {s.cashierId for s in sales})
    members = await _lookup(Member, {s.memberId for s in sales if s.memberId})
    return [_sale_response(s, viewer, users, members) for s in sales]


async def get_sale_or_404(sale_id: str) -> Sale:
    sale = await Sale.get(parse_object_id(sale_id, "ID transaksi"))
    if sale is None:
        raise HTTPException(status_code=404, detail="Transaksi penjualan tidak ditemukan.")
    return sale


# ---------------------------------------------------------------------------
# Create sale
# ---------------------------------------------------------------------------


async def create_sale(data: SaleCreate, current_user: User, ip_address: str | None = None) -> SaleResponse:
    # Gabungkan produk duplikat di keranjang.
    quantities: dict[str, float] = {}
    for item in data.items:
        product_id = str(parse_object_id(item.productId, "ID produk"))
        quantities[product_id] = quantities.get(product_id, 0) + item.quantity

    products = {
        str(p.id): p
        for p in await Product.find(
            {"_id": {"$in": [ObjectId(pid) for pid in quantities]}}
        ).to_list()
    }

    sale_items: list[SaleItem] = []
    for product_id, quantity in quantities.items():
        product = products.get(product_id)
        if product is None:
            raise HTTPException(status_code=404, detail=f"Produk {product_id} tidak ditemukan.")
        if not product.isActive:
            raise HTTPException(status_code=400, detail=f"Produk {product.name} tidak aktif.")
        # Validasi awal (pesan ramah). Jaminan sebenarnya ada di update
        # kondisional atomik saat pengurangan stok (BR-02).
        if product.stock < quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Stok {product.name} tidak mencukupi. "
                    f"Tersedia {product.stock:g}, diminta {quantity:g}."
                ),
            )
        sale_items.append(
            SaleItem(
                productId=product_id,
                sku=product.sku,
                name=product.name,
                unit=product.unit,
                quantity=quantity,
                price=product.sellingPrice,
                costPrice=product.purchasePrice,
                subtotal=round(quantity * product.sellingPrice, 2),
            )
        )

    subtotal = round(sum(i.subtotal for i in sale_items), 2)
    if data.discount > subtotal:
        raise HTTPException(status_code=422, detail="Diskon tidak boleh melebihi subtotal.")
    total = round(subtotal - data.discount, 2)

    member_id = None
    if data.memberId:
        member = await Member.get(parse_object_id(data.memberId, "ID anggota"))
        if member is None:
            raise HTTPException(status_code=404, detail="Anggota tidak ditemukan.")
        if member.status != MemberStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Anggota tidak aktif.")
        member_id = str(member.id)

    method = data.payment.method
    if method == PaymentMethod.CASH:
        paid = data.payment.amount if data.payment.amount is not None else 0
        if paid < total:
            raise HTTPException(
                status_code=400,
                detail=f"Pembayaran tidak mencukupi. Total Rp{total:,.0f}, dibayar Rp{paid:,.0f}.",
            )
        change = round(paid - total, 2)
    else:
        paid = total if data.payment.amount is None else data.payment.amount
        if abs(paid - total) > 0.005:
            raise HTTPException(
                status_code=400,
                detail="Pembayaran non-tunai harus sama dengan total transaksi.",
            )
        change = 0.0

    now = utc_now()
    user_id = str(current_user.id)

    async with unit_of_work() as uow:
        sale = Sale(
            invoiceNumber=await next_document_number("TRX"),
            cashierId=user_id,
            memberId=member_id,
            items=sale_items,
            subtotal=subtotal,
            discount=data.discount,
            total=total,
            payment=SalePaymentInfo(
                method=method,
                amount=paid,
                change=change,
                paidAt=now,
                referenceNumber=data.payment.referenceNumber,
            ),
            status=SaleStatus.COMPLETED,
            createdAt=now,
            updatedAt=now,
        )
        await uow.insert(sale)

        for item in sale_items:
            await apply_stock_change(
                uow,
                product_id=item.productId,
                delta=-item.quantity,
                movement_type=StockMovementType.SALE,
                user_id=user_id,
                reference_type="SALE",
                reference_id=str(sale.id),
                reference_number=sale.invoiceNumber,
                require_active=True,
            )

        await uow.insert(
            SalePayment(
                saleId=str(sale.id),
                invoiceNumber=sale.invoiceNumber,
                type=SalePaymentType.PAYMENT,
                method=method,
                amount=paid,
                change=change,
                referenceId=data.payment.referenceNumber,
                paidAt=now,
                createdBy=user_id,
            )
        )

        await log_audit(
            action=AuditAction.SALE,
            module=AuditModule.SALE,
            description=f"Penjualan {sale.invoiceNumber} sebesar Rp{total:,.0f} ({method.value})",
            user=current_user,
            reference_id=str(sale.id),
            ip_address=ip_address,
            session=uow.session,
        )

    return (await build_sale_responses([sale], current_user))[0]


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


async def list_sales(
    current_user: User,
    pagination: PageParams,
    date_from: date | None = None,
    date_to: date | None = None,
    status_filter: SaleStatus | None = None,
    cashier_id: str | None = None,
    member_id: str | None = None,
    search: str | None = None,
) -> list[SaleResponse]:
    query: dict = {}

    # Kasir hanya melihat transaksi yang dibuat sendiri (PRD §6.2).
    if current_user.role == UserRole.KASIR:
        query["cashierId"] = str(current_user.id)
    elif cashier_id:
        query["cashierId"] = cashier_id

    if member_id:
        query["memberId"] = member_id
    if status_filter:
        query["status"] = status_filter.value
    if search and search.strip():
        query["invoiceNumber"] = search_regex(search)

    start, end = local_range_bounds(date_from, date_to)
    if start or end:
        query["createdAt"] = {}
        if start:
            query["createdAt"]["$gte"] = start
        if end:
            query["createdAt"]["$lt"] = end

    sales = await pagination.apply(Sale.find(query).sort("-createdAt"))
    return await build_sale_responses(sales, current_user)


async def get_sale_detail(sale_id: str, current_user: User) -> SaleResponse:
    sale = await get_sale_or_404(sale_id)
    if current_user.role == UserRole.KASIR and sale.cashierId != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Kasir hanya dapat melihat transaksi yang dibuat sendiri.",
        )
    return (await build_sale_responses([sale], current_user))[0]


async def get_sale_by_invoice(invoice_number: str, current_user: User) -> SaleResponse:
    sale = await Sale.find_one({"invoiceNumber": invoice_number.strip()})
    if sale is None:
        raise HTTPException(status_code=404, detail="Transaksi penjualan tidak ditemukan.")
    return await get_sale_detail(str(sale.id), current_user)


# ---------------------------------------------------------------------------
# Cancel (BR-07)
# ---------------------------------------------------------------------------


async def cancel_sale(
    sale_id: str,
    current_user: User,
    reason: str | None = None,
    ip_address: str | None = None,
) -> SaleCancelResponse:
    sale = await get_sale_or_404(sale_id)

    if sale.status == SaleStatus.CANCELLED:
        raise HTTPException(status_code=409, detail="Transaksi sudah dibatalkan.")

    if await Return.find_one(
        {"saleId": str(sale.id), "status": ReturnStatus.PENDING_APPROVAL.value}
    ):
        raise HTTPException(
            status_code=409,
            detail="Masih ada retur yang menunggu approval untuk transaksi ini.",
        )

    user_id = str(current_user.id)
    now = utc_now()
    restored: list[dict] = []

    async with unit_of_work() as uow:
        collection = Sale.get_pymongo_collection()
        result = await collection.update_one(
            {"_id": sale.id, "status": SaleStatus.COMPLETED.value},
            {
                "$set": {
                    "status": SaleStatus.CANCELLED.value,
                    "cancelledBy": user_id,
                    "cancelledAt": now,
                    "cancelReason": reason,
                    "updatedAt": now,
                }
            },
            session=uow.session,
        )
        if result.modified_count != 1:
            raise HTTPException(status_code=409, detail="Transaksi sudah dibatalkan.")
        uow.on_rollback(
            lambda: collection.update_one(
                {"_id": sale.id},
                {
                    "$set": {"status": SaleStatus.COMPLETED.value, "updatedAt": sale.updatedAt},
                    "$unset": {"cancelledBy": "", "cancelledAt": "", "cancelReason": ""},
                },
            )
        )

        # Stock movement pembalik hanya untuk qty yang belum diretur.
        refund_total = 0.0
        ratio = (sale.total / sale.subtotal) if sale.subtotal else 1
        for item in sale.items:
            quantity = item.quantity - item.returnedQuantity
            if quantity <= 0:
                continue
            movement = await apply_stock_change(
                uow,
                product_id=item.productId,
                delta=quantity,
                movement_type=StockMovementType.SALE,
                user_id=user_id,
                reference_type="SALE_CANCEL",
                reference_id=str(sale.id),
                reference_number=sale.invoiceNumber,
                reason=reason or "Pembatalan transaksi",
            )
            refund_total += quantity * item.price * ratio
            restored.append(
                {
                    "productId": item.productId,
                    "sku": item.sku,
                    "name": item.name,
                    "quantity": quantity,
                    "stockBefore": movement.stockBefore,
                    "stockAfter": movement.stockAfter,
                }
            )

        if refund_total > 0:
            await uow.insert(
                SalePayment(
                    saleId=str(sale.id),
                    invoiceNumber=sale.invoiceNumber,
                    type=SalePaymentType.REFUND,
                    method=sale.payment.method,
                    amount=round(refund_total, 2),
                    paidAt=now,
                    createdBy=user_id,
                )
            )

        await log_audit(
            action=AuditAction.CANCEL,
            module=AuditModule.SALE,
            description=(
                f"Membatalkan transaksi {sale.invoiceNumber}"
                + (f": {reason}" if reason else "")
            ),
            user=current_user,
            reference_id=str(sale.id),
            ip_address=ip_address,
            session=uow.session,
        )

    sale = await get_sale_or_404(sale_id)
    response = (await build_sale_responses([sale], current_user))[0]
    return SaleCancelResponse(**response.model_dump(), restoredStock=restored)
