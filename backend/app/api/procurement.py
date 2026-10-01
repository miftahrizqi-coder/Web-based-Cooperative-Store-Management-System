from datetime import date

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import ADMIN_PENGURUS, require_role
from app.core.utils import (
    Pagination,
    PageParams,
    local_range_bounds,
    parse_object_id,
    search_regex,
)
from app.models.procurement import (
    GoodsReceipt,
    PaymentStatus,
    POStatus,
    Purchase,
    PurchaseOrder,
    SupplierInvoice,
    SupplierPayment,
)
from app.models.user import User
from app.schemas.procurement import (
    GoodsReceiptCreate,
    GoodsReceiptResponse,
    PayableResponse,
    PurchaseCreate,
    PurchaseOrderCompleteRequest,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    PurchaseResponse,
    SupplierInvoiceCreate,
    SupplierInvoiceResponse,
    SupplierPaymentCreate,
    SupplierPaymentResponse,
)
from app.services.procurement import (
    approve_purchase_order,
    cancel_purchase_order,
    complete_purchase_order,
    compute_payables,
    create_goods_receipt,
    create_purchase,
    create_purchase_order,
    create_supplier_invoice,
    create_supplier_payment,
    get_invoice_or_404,
    get_po_or_404,
    get_receipt_or_404,
    goods_receipt_response,
    invoice_payable,
    order_purchase_order,
    purchase_order_response,
    purchase_response,
    reject_purchase_order,
    submit_purchase_order,
    supplier_invoice_response,
    supplier_name_map,
    supplier_payment_response,
    update_purchase_order,
)


router = APIRouter(prefix="/api", tags=["Procurement"])

# PRD §6.3: pengadaan dikelola Pengurus (dan Admin dengan akses penuh).
require_procurement_user = require_role(*ADMIN_PENGURUS)


def date_filter(field: str, date_from: date | None, date_to: date | None) -> dict:
    start, end = local_range_bounds(date_from, date_to)
    if not start and not end:
        return {}
    condition: dict = {}
    if start:
        condition["$gte"] = start
    if end:
        condition["$lt"] = end
    return {field: condition}


async def po_number_map(ids: set[str]) -> dict[str, str]:
    object_ids = [ObjectId(i) for i in ids if ObjectId.is_valid(i)]
    if not object_ids:
        return {}
    orders = await PurchaseOrder.find({"_id": {"$in": object_ids}}).to_list()
    return {str(o.id): o.poNumber for o in orders}


# =========================================================
# PURCHASE ORDER
# =========================================================


@router.get("/purchase-orders", response_model=list[PurchaseOrderResponse])
async def list_purchase_orders(
    status: POStatus | None = Query(default=None),
    supplier_id: str | None = Query(default=None, alias="supplierId"),
    search: str | None = Query(default=None),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    pagination: PageParams = Depends(Pagination()),
    user: User = Depends(require_procurement_user),
):
    query: dict = {**date_filter("createdAt", date_from, date_to)}
    if status:
        query["status"] = status.value
    if supplier_id:
        query["supplierId"] = supplier_id
    if search and search.strip():
        query["poNumber"] = search_regex(search)

    orders = await pagination.apply(PurchaseOrder.find(query).sort("-createdAt"))
    names = await supplier_name_map({o.supplierId for o in orders})
    return [purchase_order_response(o, names) for o in orders]


@router.post("/purchase-orders", response_model=PurchaseOrderResponse, status_code=201)
async def create_purchase_order_endpoint(
    payload: PurchaseOrderCreate,
    user: User = Depends(require_procurement_user),
):
    po = await create_purchase_order(payload=payload, user_id=str(user.id))
    return purchase_order_response(po, await supplier_name_map({po.supplierId}))


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(po_id: str, user: User = Depends(require_procurement_user)):
    po = await get_po_or_404(po_id)
    return purchase_order_response(po, await supplier_name_map({po.supplierId}))


@router.get("/purchase-orders/{po_id}/goods-receipts", response_model=list[GoodsReceiptResponse])
async def get_purchase_order_receipts(po_id: str, user: User = Depends(require_procurement_user)):
    po = await get_po_or_404(po_id)
    receipts = await GoodsReceipt.find({"purchaseOrderId": str(po.id)}).sort("-receivedAt").to_list()
    names = await supplier_name_map({po.supplierId})
    return [goods_receipt_response(r, names, {str(po.id): po.poNumber}) for r in receipts]


@router.put("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order_endpoint(
    po_id: str,
    payload: PurchaseOrderUpdate,
    user: User = Depends(require_procurement_user),
):
    po = await update_purchase_order(po_id=po_id, payload=payload, user_id=str(user.id))
    return purchase_order_response(po, await supplier_name_map({po.supplierId}))


async def _po_action(action, po_id: str, user: User) -> PurchaseOrderResponse:
    po = await action(po_id=po_id, user_id=str(user.id))
    return purchase_order_response(po, await supplier_name_map({po.supplierId}))


@router.post("/purchase-orders/{po_id}/submit", response_model=PurchaseOrderResponse)
async def submit_purchase_order_endpoint(po_id: str, user: User = Depends(require_procurement_user)):
    return await _po_action(submit_purchase_order, po_id, user)


@router.post("/purchase-orders/{po_id}/approve", response_model=PurchaseOrderResponse)
async def approve_purchase_order_endpoint(po_id: str, user: User = Depends(require_procurement_user)):
    return await _po_action(approve_purchase_order, po_id, user)


@router.post("/purchase-orders/{po_id}/reject", response_model=PurchaseOrderResponse)
async def reject_purchase_order_endpoint(po_id: str, user: User = Depends(require_procurement_user)):
    return await _po_action(reject_purchase_order, po_id, user)


@router.post("/purchase-orders/{po_id}/order", response_model=PurchaseOrderResponse)
async def order_purchase_order_endpoint(po_id: str, user: User = Depends(require_procurement_user)):
    return await _po_action(order_purchase_order, po_id, user)


@router.post("/purchase-orders/{po_id}/cancel", response_model=PurchaseOrderResponse)
async def cancel_purchase_order_endpoint(po_id: str, user: User = Depends(require_procurement_user)):
    return await _po_action(cancel_purchase_order, po_id, user)


@router.post("/purchase-orders/{po_id}/complete", response_model=PurchaseOrderResponse)
async def complete_purchase_order_endpoint(
    po_id: str,
    payload: PurchaseOrderCompleteRequest | None = None,
    user: User = Depends(require_procurement_user),
):
    po = await complete_purchase_order(po_id, str(user.id), payload.notes if payload else None)
    return purchase_order_response(po, await supplier_name_map({po.supplierId}))


# =========================================================
# GOODS RECEIPT
# =========================================================


@router.get("/goods-receipts", response_model=list[GoodsReceiptResponse])
async def list_goods_receipts(
    purchase_order_id: str | None = Query(default=None, alias="purchaseOrderId"),
    supplier_id: str | None = Query(default=None, alias="supplierId"),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    pagination: PageParams = Depends(Pagination()),
    user: User = Depends(require_procurement_user),
):
    query: dict = {**date_filter("receivedAt", date_from, date_to)}
    if purchase_order_id:
        query["purchaseOrderId"] = purchase_order_id
    if supplier_id:
        query["supplierId"] = supplier_id

    receipts = await pagination.apply(GoodsReceipt.find(query).sort("-receivedAt"))
    names = await supplier_name_map({r.supplierId for r in receipts})
    po_numbers = await po_number_map({r.purchaseOrderId for r in receipts})
    return [goods_receipt_response(r, names, po_numbers) for r in receipts]


@router.post("/goods-receipts", response_model=GoodsReceiptResponse, status_code=201)
async def create_goods_receipt_endpoint(
    payload: GoodsReceiptCreate,
    user: User = Depends(require_procurement_user),
):
    receipt = await create_goods_receipt(payload=payload, user=user)
    names = await supplier_name_map({receipt.supplierId})
    po_numbers = await po_number_map({receipt.purchaseOrderId})
    return goods_receipt_response(receipt, names, po_numbers)


@router.get("/goods-receipts/{receipt_id}", response_model=GoodsReceiptResponse)
async def get_goods_receipt(receipt_id: str, user: User = Depends(require_procurement_user)):
    receipt = await get_receipt_or_404(receipt_id)
    names = await supplier_name_map({receipt.supplierId})
    po_numbers = await po_number_map({receipt.purchaseOrderId})
    return goods_receipt_response(receipt, names, po_numbers)


# =========================================================
# PURCHASE
# =========================================================


@router.get("/purchases", response_model=list[PurchaseResponse])
async def list_purchases(
    supplier_id: str | None = Query(default=None, alias="supplierId"),
    payment_status: PaymentStatus | None = Query(default=None, alias="paymentStatus"),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    pagination: PageParams = Depends(Pagination()),
    user: User = Depends(require_procurement_user),
):
    query: dict = {**date_filter("createdAt", date_from, date_to)}
    if supplier_id:
        query["supplierId"] = supplier_id
    if payment_status:
        query["paymentStatus"] = payment_status.value

    purchases = await pagination.apply(Purchase.find(query).sort("-createdAt"))
    names = await supplier_name_map({p.supplierId for p in purchases})
    return [purchase_response(p, names) for p in purchases]


@router.post("/purchases", response_model=PurchaseResponse, status_code=201)
async def create_purchase_endpoint(
    payload: PurchaseCreate,
    user: User = Depends(require_procurement_user),
):
    purchase = await create_purchase(payload=payload, user_id=str(user.id))
    return purchase_response(purchase, await supplier_name_map({purchase.supplierId}))


@router.get("/purchases/{purchase_id}", response_model=PurchaseResponse)
async def get_purchase(purchase_id: str, user: User = Depends(require_procurement_user)):
    purchase = await Purchase.get(parse_object_id(purchase_id, "ID pembelian"))
    if purchase is None:
        raise HTTPException(status_code=404, detail="Pembelian tidak ditemukan.")
    return purchase_response(purchase, await supplier_name_map({purchase.supplierId}))


# =========================================================
# SUPPLIER INVOICE
# =========================================================


@router.get("/supplier-invoices", response_model=list[SupplierInvoiceResponse])
async def list_supplier_invoices(
    supplier_id: str | None = Query(default=None, alias="supplierId"),
    payment_status: PaymentStatus | None = Query(default=None, alias="paymentStatus"),
    pagination: PageParams = Depends(Pagination()),
    user: User = Depends(require_procurement_user),
):
    query: dict = {}
    if supplier_id:
        query["supplierId"] = supplier_id

    invoices = await SupplierInvoice.find(query).sort("-invoiceDate").to_list()
    payables = {p["invoiceId"]: p for p in await compute_payables(invoices)}

    if payment_status:
        invoices = [
            i for i in invoices
            if payables[str(i.id)]["paymentStatus"] == payment_status
        ]

    invoices = pagination.slice(invoices)
    return [supplier_invoice_response(i, payables[str(i.id)]) for i in invoices]


@router.post("/supplier-invoices", response_model=SupplierInvoiceResponse, status_code=201)
async def create_supplier_invoice_endpoint(
    payload: SupplierInvoiceCreate,
    user: User = Depends(require_procurement_user),
):
    invoice = await create_supplier_invoice(payload=payload, user_id=str(user.id))
    names = await supplier_name_map({invoice.supplierId})
    return supplier_invoice_response(invoice, invoice_payable(invoice, names.get(invoice.supplierId)))


@router.get("/supplier-invoices/{invoice_id}", response_model=SupplierInvoiceResponse)
async def get_supplier_invoice(invoice_id: str, user: User = Depends(require_procurement_user)):
    invoice = await get_invoice_or_404(invoice_id)
    names = await supplier_name_map({invoice.supplierId})
    return supplier_invoice_response(invoice, invoice_payable(invoice, names.get(invoice.supplierId)))


@router.get("/supplier-invoices/{invoice_id}/payments", response_model=list[SupplierPaymentResponse])
async def get_supplier_invoice_payments(invoice_id: str, user: User = Depends(require_procurement_user)):
    invoice = await get_invoice_or_404(invoice_id)
    payments = await SupplierPayment.find({"invoiceId": str(invoice.id)}).sort("-paymentDate").to_list()
    names = await supplier_name_map({invoice.supplierId})
    return [
        supplier_payment_response(p, names, {str(invoice.id): invoice.invoiceNumber})
        for p in payments
    ]


# =========================================================
# SUPPLIER PAYABLES / HUTANG
# =========================================================


@router.get("/supplier-payables", response_model=list[PayableResponse])
async def list_supplier_payables(
    supplier_id: str | None = Query(default=None, alias="supplierId"),
    outstanding_only: bool = Query(default=False, alias="outstandingOnly"),
    user: User = Depends(require_procurement_user),
):
    query: dict = {}
    if supplier_id:
        query["supplierId"] = supplier_id
    invoices = await SupplierInvoice.find(query).sort("dueDate").to_list()
    payables = await compute_payables(invoices)
    if outstanding_only:
        payables = [p for p in payables if p["outstanding"] > 0]
    return payables


# =========================================================
# SUPPLIER PAYMENT
# =========================================================


@router.get("/supplier-payments", response_model=list[SupplierPaymentResponse])
async def list_supplier_payments(
    supplier_id: str | None = Query(default=None, alias="supplierId"),
    invoice_id: str | None = Query(default=None, alias="invoiceId"),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    pagination: PageParams = Depends(Pagination()),
    user: User = Depends(require_procurement_user),
):
    query: dict = {**date_filter("paymentDate", date_from, date_to)}
    if supplier_id:
        query["supplierId"] = supplier_id
    if invoice_id:
        query["invoiceId"] = invoice_id

    payments = await pagination.apply(SupplierPayment.find(query).sort("-paymentDate"))
    names = await supplier_name_map({p.supplierId for p in payments})

    invoice_ids = [ObjectId(p.invoiceId) for p in payments if ObjectId.is_valid(p.invoiceId)]
    invoice_numbers = {
        str(i.id): i.invoiceNumber
        for i in await SupplierInvoice.find({"_id": {"$in": invoice_ids}}).to_list()
    } if invoice_ids else {}

    return [supplier_payment_response(p, names, invoice_numbers) for p in payments]


@router.post("/supplier-payments", response_model=SupplierPaymentResponse, status_code=201)
async def create_supplier_payment_endpoint(
    payload: SupplierPaymentCreate,
    user: User = Depends(require_procurement_user),
):
    payment = await create_supplier_payment(payload=payload, user=user)
    names = await supplier_name_map({payment.supplierId})
    invoice = await get_invoice_or_404(payment.invoiceId)
    return supplier_payment_response(payment, names, {str(invoice.id): invoice.invoiceNumber})
