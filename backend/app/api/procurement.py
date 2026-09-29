from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.models.procurement import (
    GoodsReceipt,
    Purchase,
    PurchaseOrder,
    SupplierInvoice,
    SupplierPayment,
)
from app.models.user import User, UserRole
from app.schemas.procurement import (
    GoodsReceiptCreate,
    GoodsReceiptResponse,
    PayableResponse,
    PurchaseCreate,
    PurchaseResponse,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    SupplierInvoiceCreate,
    SupplierInvoiceResponse,
    SupplierPaymentCreate,
    SupplierPaymentResponse,
)
from app.services.procurement import (
    approve_purchase_order,
    cancel_purchase_order,
    create_goods_receipt,
    create_purchase,
    create_purchase_order,
    create_supplier_invoice,
    create_supplier_payment,
    get_supplier_payables,
    order_purchase_order,
    submit_purchase_order,
    update_purchase_order,
)


router = APIRouter(
    prefix="/api",
    tags=["Procurement"],
)


def require_procurement_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    Phase 3 procurement sementara hanya dapat
    diakses Admin dan Pengurus.

    Role Pengurus memang bertanggung jawab terhadap
    procurement berdasarkan PRD.
    """

    if user.role not in {
        UserRole.ADMIN,
        UserRole.PENGURUS,
    }:
        raise HTTPException(
            status_code=403,
            detail="Procurement access denied",
        )

    return user


def purchase_order_response(
    purchase_order: PurchaseOrder,
) -> PurchaseOrderResponse:
    return PurchaseOrderResponse(
        id=str(purchase_order.id),
        poNumber=purchase_order.poNumber,
        supplierId=purchase_order.supplierId,
        items=[
            item.model_dump()
            for item in purchase_order.items
        ],
        subtotal=purchase_order.subtotal,
        discount=purchase_order.discount,
        tax=purchase_order.tax,
        shippingCost=purchase_order.shippingCost,
        grandTotal=purchase_order.grandTotal,
        status=purchase_order.status,
        expectedDeliveryDate=(
            purchase_order.expectedDeliveryDate
        ),
        createdBy=purchase_order.createdBy,
        approvedBy=purchase_order.approvedBy,
        approvedAt=purchase_order.approvedAt,
        createdAt=purchase_order.createdAt,
        updatedAt=purchase_order.updatedAt,
    )


def goods_receipt_response(
    receipt: GoodsReceipt,
) -> GoodsReceiptResponse:
    return GoodsReceiptResponse(
        id=str(receipt.id),
        receiptNumber=receipt.receiptNumber,
        purchaseOrderId=receipt.purchaseOrderId,
        supplierId=receipt.supplierId,
        items=[
            item.model_dump()
            for item in receipt.items
        ],
        receivedBy=receipt.receivedBy,
        receivedAt=receipt.receivedAt,
        notes=receipt.notes,
    )


def purchase_response(
    purchase: Purchase,
) -> PurchaseResponse:
    return PurchaseResponse(
        id=str(purchase.id),
        purchaseNumber=purchase.purchaseNumber,
        supplierId=purchase.supplierId,
        purchaseOrderId=purchase.purchaseOrderId,
        receiptId=purchase.receiptId,
        items=[
            item.model_dump()
            for item in purchase.items
        ],
        subtotal=purchase.subtotal,
        discount=purchase.discount,
        total=purchase.total,
        paymentStatus=purchase.paymentStatus,
        createdBy=purchase.createdBy,
        createdAt=purchase.createdAt,
    )


def supplier_invoice_response(
    invoice: SupplierInvoice,
) -> SupplierInvoiceResponse:
    return SupplierInvoiceResponse(
        id=str(invoice.id),
        invoiceNumber=invoice.invoiceNumber,
        supplierId=invoice.supplierId,
        purchaseOrderId=invoice.purchaseOrderId,
        receiptId=invoice.receiptId,
        invoiceDate=invoice.invoiceDate,
        dueDate=invoice.dueDate,
        subtotal=invoice.subtotal,
        tax=invoice.tax,
        shippingCost=invoice.shippingCost,
        total=invoice.total,
        paymentStatus=invoice.paymentStatus,
        createdAt=invoice.createdAt,
        updatedAt=invoice.updatedAt,
    )


def supplier_payment_response(
    payment: SupplierPayment,
) -> SupplierPaymentResponse:
    return SupplierPaymentResponse(
        id=str(payment.id),
        supplierId=payment.supplierId,
        invoiceId=payment.invoiceId,
        paymentNumber=payment.paymentNumber,
        amount=payment.amount,
        method=payment.method,
        paymentDate=payment.paymentDate,
        referenceNumber=payment.referenceNumber,
        createdBy=payment.createdBy,
        notes=payment.notes,
        createdAt=payment.createdAt,
    )


# =========================================================
# PURCHASE ORDER
# =========================================================


@router.get(
    "/purchase-orders",
    response_model=list[PurchaseOrderResponse],
)
async def list_purchase_orders(
    user: User = Depends(require_procurement_user),
):
    purchase_orders = (
        await PurchaseOrder.find_all()
        .sort("-createdAt")
        .to_list()
    )

    return [
        purchase_order_response(item)
        for item in purchase_orders
    ]


@router.post(
    "/purchase-orders",
    response_model=PurchaseOrderResponse,
    status_code=201,
)
async def create_purchase_order_endpoint(
    payload: PurchaseOrderCreate,
    user: User = Depends(require_procurement_user),
):
    purchase_order = await create_purchase_order(
        payload=payload,
        user_id=str(user.id),
    )

    return purchase_order_response(
        purchase_order
    )


@router.get(
    "/purchase-orders/{po_id}",
    response_model=PurchaseOrderResponse,
)
async def get_purchase_order(
    po_id: str,
    user: User = Depends(require_procurement_user),
):
    purchase_order = await PurchaseOrder.get(
        po_id
    )

    if not purchase_order:
        raise HTTPException(
            status_code=404,
            detail="Purchase Order not found",
        )

    return purchase_order_response(
        purchase_order
    )


@router.put(
    "/purchase-orders/{po_id}",
    response_model=PurchaseOrderResponse,
)
async def update_purchase_order_endpoint(
    po_id: str,
    payload: PurchaseOrderUpdate,
    user: User = Depends(require_procurement_user),
):
    purchase_order = await update_purchase_order(
        po_id=po_id,
        payload=payload,
    )

    return purchase_order_response(
        purchase_order
    )


@router.post(
    "/purchase-orders/{po_id}/submit",
    response_model=PurchaseOrderResponse,
)
async def submit_purchase_order_endpoint(
    po_id: str,
    user: User = Depends(require_procurement_user),
):
    purchase_order = await submit_purchase_order(
        po_id=po_id
    )

    return purchase_order_response(
        purchase_order
    )


@router.post(
    "/purchase-orders/{po_id}/approve",
    response_model=PurchaseOrderResponse,
)
async def approve_purchase_order_endpoint(
    po_id: str,
    user: User = Depends(require_procurement_user),
):
    purchase_order = await approve_purchase_order(
        po_id=po_id,
        user_id=str(user.id),
    )

    return purchase_order_response(
        purchase_order
    )


@router.post(
    "/purchase-orders/{po_id}/order",
    response_model=PurchaseOrderResponse,
)
async def order_purchase_order_endpoint(
    po_id: str,
    user: User = Depends(require_procurement_user),
):
    purchase_order = await order_purchase_order(
        po_id=po_id
    )

    return purchase_order_response(
        purchase_order
    )


@router.post(
    "/purchase-orders/{po_id}/cancel",
    response_model=PurchaseOrderResponse,
)
async def cancel_purchase_order_endpoint(
    po_id: str,
    user: User = Depends(require_procurement_user),
):
    purchase_order = await cancel_purchase_order(
        po_id=po_id
    )

    return purchase_order_response(
        purchase_order
    )


# =========================================================
# GOODS RECEIPT
# =========================================================


@router.get(
    "/goods-receipts",
    response_model=list[GoodsReceiptResponse],
)
async def list_goods_receipts(
    user: User = Depends(require_procurement_user),
):
    receipts = (
        await GoodsReceipt.find_all()
        .sort("-receivedAt")
        .to_list()
    )

    return [
        goods_receipt_response(item)
        for item in receipts
    ]


@router.post(
    "/goods-receipts",
    response_model=GoodsReceiptResponse,
    status_code=201,
)
async def create_goods_receipt_endpoint(
    payload: GoodsReceiptCreate,
    user: User = Depends(require_procurement_user),
):
    receipt = await create_goods_receipt(
        payload=payload,
        user_id=str(user.id),
    )

    return goods_receipt_response(receipt)


@router.get(
    "/goods-receipts/{receipt_id}",
    response_model=GoodsReceiptResponse,
)
async def get_goods_receipt(
    receipt_id: str,
    user: User = Depends(require_procurement_user),
):
    receipt = await GoodsReceipt.get(
        receipt_id
    )

    if not receipt:
        raise HTTPException(
            status_code=404,
            detail="Goods Receipt not found",
        )

    return goods_receipt_response(receipt)


# =========================================================
# PURCHASE
# =========================================================


@router.get(
    "/purchases",
    response_model=list[PurchaseResponse],
)
async def list_purchases(
    user: User = Depends(require_procurement_user),
):
    purchases = (
        await Purchase.find_all()
        .sort("-createdAt")
        .to_list()
    )

    return [
        purchase_response(item)
        for item in purchases
    ]


@router.post(
    "/purchases",
    response_model=PurchaseResponse,
    status_code=201,
)
async def create_purchase_endpoint(
    payload: PurchaseCreate,
    user: User = Depends(require_procurement_user),
):
    purchase = await create_purchase(
        payload=payload,
        user_id=str(user.id),
    )

    return purchase_response(purchase)


@router.get(
    "/purchases/{purchase_id}",
    response_model=PurchaseResponse,
)
async def get_purchase(
    purchase_id: str,
    user: User = Depends(require_procurement_user),
):
    purchase = await Purchase.get(
        purchase_id
    )

    if not purchase:
        raise HTTPException(
            status_code=404,
            detail="Purchase not found",
        )

    return purchase_response(purchase)


# =========================================================
# SUPPLIER INVOICE
# =========================================================


@router.get(
    "/supplier-invoices",
    response_model=list[SupplierInvoiceResponse],
)
async def list_supplier_invoices(
    user: User = Depends(require_procurement_user),
):
    invoices = (
        await SupplierInvoice.find_all()
        .sort("-createdAt")
        .to_list()
    )

    return [
        supplier_invoice_response(item)
        for item in invoices
    ]


@router.post(
    "/supplier-invoices",
    response_model=SupplierInvoiceResponse,
    status_code=201,
)
async def create_supplier_invoice_endpoint(
    payload: SupplierInvoiceCreate,
    user: User = Depends(require_procurement_user),
):
    invoice = await create_supplier_invoice(
        payload=payload,
    )

    return supplier_invoice_response(invoice)


@router.get(
    "/supplier-invoices/{invoice_id}",
    response_model=SupplierInvoiceResponse,
)
async def get_supplier_invoice(
    invoice_id: str,
    user: User = Depends(require_procurement_user),
):
    invoice = await SupplierInvoice.get(
        invoice_id
    )

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Supplier Invoice not found",
        )

    return supplier_invoice_response(invoice)


# =========================================================
# SUPPLIER PAYABLES / HUTANG
# =========================================================


@router.get(
    "/supplier-payables",
    response_model=list[PayableResponse],
)
async def list_supplier_payables(
    user: User = Depends(require_procurement_user),
):
    return await get_supplier_payables()


# =========================================================
# SUPPLIER PAYMENT
# =========================================================


@router.get(
    "/supplier-payments",
    response_model=list[SupplierPaymentResponse],
)
async def list_supplier_payments(
    user: User = Depends(require_procurement_user),
):
    payments = (
        await SupplierPayment.find_all()
        .sort("-paymentDate")
        .to_list()
    )

    return [
        supplier_payment_response(item)
        for item in payments
    ]


@router.post(
    "/supplier-payments",
    response_model=SupplierPaymentResponse,
    status_code=201,
)
async def create_supplier_payment_endpoint(
    payload: SupplierPaymentCreate,
    user: User = Depends(require_procurement_user),
):
    payment = await create_supplier_payment(
        payload=payload,
        user_id=str(user.id),
    )

    return supplier_payment_response(payment)