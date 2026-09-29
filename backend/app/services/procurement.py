from datetime import datetime, timezone

from fastapi import HTTPException
from pymongo import ReturnDocument

from app.models.supplier import Supplier, SupplierStatus
from app.models.supplier_product import SupplierProduct
from app.models.product import Product
from app.core.config import settings
from app.core.database import client
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
from app.schemas.procurement import (
    GoodsReceiptCreate,
    POItemCreate,
    PurchaseCreate,
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    SupplierInvoiceCreate,
    SupplierPaymentCreate,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def next_document_number(prefix: str) -> str:
    """
    Generate document number berdasarkan tanggal.

    Contoh:
    PO-20260929-0001
    GR-20260929-0001
    PUR-20260929-0001
    PAY-SUP-20260929-0001
    """

    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    counter_key = f"{prefix}-{today}"

    counters = client[settings.mongodb_database]["document_counters"]

    counter = await counters.find_one_and_update(
        {"_id": counter_key},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    return f"{prefix}-{today}-{counter['value']:04d}"


def calculate_po_totals(
    items: list[POItemCreate],
    discount: int,
    tax: int,
    shipping_cost: int,
) -> tuple[int, int]:
    subtotal = sum(
        item.quantity * item.unitPrice
        for item in items
    )

    grand_total = (
        subtotal
        - discount
        + tax
        + shipping_cost
    )

    if grand_total < 0:
        raise HTTPException(
            status_code=422,
            detail="Grand total cannot be negative",
        )

    return subtotal, grand_total


async def create_purchase_order(
    payload: PurchaseOrderCreate,
    user_id: str,
) -> PurchaseOrder:
    subtotal, grand_total = calculate_po_totals(
        payload.items,
        payload.discount,
        payload.tax,
        payload.shippingCost,
    )

    now = utc_now()

    items = [
        PurchaseOrderItem(
            supplierProductId=item.supplierProductId,
            productId=item.productId,
            sku=item.sku,
            name=item.name,
            quantity=item.quantity,
            unitPrice=item.unitPrice,
            subtotal=item.quantity * item.unitPrice,
        )
        for item in payload.items
    ]

    purchase_order = PurchaseOrder(
        poNumber=await next_document_number("PO"),
        supplierId=payload.supplierId,
        items=items,
        subtotal=subtotal,
        discount=payload.discount,
        tax=payload.tax,
        shippingCost=payload.shippingCost,
        grandTotal=grand_total,
        status=POStatus.DRAFT,
        expectedDeliveryDate=payload.expectedDeliveryDate,
        createdBy=user_id,
        createdAt=now,
        updatedAt=now,
    )

    supplier = await Supplier.get(purchase_order.supplierId)

    if supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier tidak ditemukan.",
        )

    if supplier.status != SupplierStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Supplier tidak aktif dan tidak dapat digunakan untuk Purchase Order baru.",
        )

    for item in payload.items:
        supplier_product = await SupplierProduct.get(
            item.supplierProductId
        )

        if supplier_product is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Product Supplier {item.supplierProductId} "
                    "tidak ditemukan."
                ),
            )

        if supplier_product.supplierId != payload.supplierId:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Product Supplier tidak sesuai dengan supplier "
                    "Purchase Order."
                ),
            )

        if not supplier_product.isActive:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Product Supplier tidak aktif dan tidak dapat "
                    "digunakan untuk Purchase Order baru."
                ),
            )
    await purchase_order.insert()

    return purchase_order


async def update_purchase_order(
    po_id: str,
    payload: PurchaseOrderUpdate,
) -> PurchaseOrder:
    purchase_order = await PurchaseOrder.get(po_id)

    if not purchase_order:
        raise HTTPException(
            status_code=404,
            detail="Purchase Order not found",
        )

    if purchase_order.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=409,
            detail="Only DRAFT Purchase Order can be updated",
        )

    subtotal, grand_total = calculate_po_totals(
        payload.items,
        payload.discount,
        payload.tax,
        payload.shippingCost,
    )

    purchase_order.supplierId = payload.supplierId

    purchase_order.items = [
        PurchaseOrderItem(
            supplierProductId=item.supplierProductId,
            productId=item.productId,
            sku=item.sku,
            name=item.name,
            quantity=item.quantity,
            unitPrice=item.unitPrice,
            subtotal=item.quantity * item.unitPrice,
        )
        for item in payload.items
    ]

    purchase_order.subtotal = subtotal
    purchase_order.discount = payload.discount
    purchase_order.tax = payload.tax
    purchase_order.shippingCost = payload.shippingCost
    purchase_order.grandTotal = grand_total
    purchase_order.expectedDeliveryDate = (
        payload.expectedDeliveryDate
    )
    purchase_order.updatedAt = utc_now()

    supplier = await Supplier.get(payload.supplierId)

    if supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier tidak ditemukan.",
        )

    if supplier.status != SupplierStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=(
                "Supplier tidak aktif dan tidak dapat digunakan "
                "untuk Purchase Order."
            ),
        )

    for item in payload.items:
        supplier_product = await SupplierProduct.get(
            item.supplierProductId
        )

        if supplier_product is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Product Supplier {item.supplierProductId} "
                    "tidak ditemukan."
                ),
            )

        if supplier_product.supplierId != payload.supplierId:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Product Supplier tidak sesuai dengan supplier "
                    "Purchase Order."
                ),
            )

        if not supplier_product.isActive:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Product Supplier tidak aktif dan tidak dapat "
                    "digunakan untuk Purchase Order."
                ),
            )
    await purchase_order.save()

    return purchase_order


async def submit_purchase_order(
    po_id: str,
) -> PurchaseOrder:
    purchase_order = await PurchaseOrder.get(po_id)

    if not purchase_order:
        raise HTTPException(
            status_code=404,
            detail="Purchase Order not found",
        )

    if purchase_order.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=409,
            detail="Only DRAFT Purchase Order can be submitted",
        )

    purchase_order.status = POStatus.PENDING_APPROVAL
    purchase_order.updatedAt = utc_now()

    await purchase_order.save()

    return purchase_order


async def approve_purchase_order(
    po_id: str,
    user_id: str,
) -> PurchaseOrder:
    purchase_order = await PurchaseOrder.get(po_id)

    if not purchase_order:
        raise HTTPException(
            status_code=404,
            detail="Purchase Order not found",
        )

    if purchase_order.status != POStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=409,
            detail=(
                "Only PENDING_APPROVAL Purchase Order "
                "can be approved"
            ),
        )
    
    if purchase_order.createdBy == user_id:
        raise HTTPException(
            status_code=403,
            detail="Purchase Order creator cannot approve their own Purchase Order",
        )
    purchase_order.status = POStatus.APPROVED
    purchase_order.approvedBy = user_id
    purchase_order.approvedAt = utc_now()
    purchase_order.updatedAt = utc_now()

    await purchase_order.save()

    return purchase_order


async def order_purchase_order(
    po_id: str,
) -> PurchaseOrder:
    purchase_order = await PurchaseOrder.get(po_id)

    if not purchase_order:
        raise HTTPException(
            status_code=404,
            detail="Purchase Order not found",
        )

    if purchase_order.status != POStatus.APPROVED:
        raise HTTPException(
            status_code=409,
            detail=(
                "Only APPROVED Purchase Order "
                "can be ordered"
            ),
        )

    purchase_order.status = POStatus.ORDERED
    purchase_order.updatedAt = utc_now()

    await purchase_order.save()

    return purchase_order


async def cancel_purchase_order(
    po_id: str,
) -> PurchaseOrder:
    purchase_order = await PurchaseOrder.get(po_id)

    if not purchase_order:
        raise HTTPException(
            status_code=404,
            detail="Purchase Order not found",
        )

    allowed_statuses = {
        POStatus.DRAFT,
        POStatus.PENDING_APPROVAL,
        POStatus.APPROVED,
        POStatus.ORDERED,
    }

    if purchase_order.status not in allowed_statuses:
        raise HTTPException(
            status_code=409,
            detail=(
                "Purchase Order cannot be cancelled "
                "from its current status"
            ),
        )

    purchase_order.status = POStatus.CANCELLED
    purchase_order.updatedAt = utc_now()

    await purchase_order.save()

    return purchase_order


async def create_goods_receipt(
    payload: GoodsReceiptCreate,
    user_id: str,
) -> GoodsReceipt:
    purchase_order = await PurchaseOrder.get(
        payload.purchaseOrderId
    )

    if not purchase_order:
        raise HTTPException(
            status_code=404,
            detail="Purchase Order not found",
        )

    allowed_statuses = {
        POStatus.ORDERED,
        POStatus.PARTIALLY_RECEIVED,
    }

    if purchase_order.status not in allowed_statuses:
        raise HTTPException(
            status_code=409,
            detail=(
                "Purchase Order is not available "
                "for goods receipt"
            ),
        )

    existing_receipts = await GoodsReceipt.find(
        GoodsReceipt.purchaseOrderId
        == str(purchase_order.id)
    ).to_list()

    previously_received: dict[str, int] = {}

    for receipt in existing_receipts:
        for item in receipt.items:
            previously_received[item.productId] = (
                previously_received.get(item.productId, 0)
                + item.receivedQuantity
            )

    po_items = {
        item.productId: item
        for item in purchase_order.items
    }

    receipt_items: list[GoodsReceiptItem] = []

    for payload_item in payload.items:
        po_item = po_items.get(payload_item.productId)

        if not po_item:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Product {payload_item.productId} "
                    "is not part of this Purchase Order"
                ),
            )

        already_received = previously_received.get(
            payload_item.productId,
            0,
        )

        remaining_quantity = (
            po_item.quantity
            - already_received
        )

        if payload_item.receivedQuantity > remaining_quantity:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Received quantity for product "
                    f"{payload_item.productId} exceeds "
                    f"remaining quantity"
                ),
            )

        if (
            payload_item.acceptedQuantity
            + payload_item.rejectedQuantity
            != payload_item.receivedQuantity
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "acceptedQuantity + rejectedQuantity "
                    "must equal receivedQuantity"
                ),
            )

        if (
            payload_item.rejectedQuantity > 0
            and not payload_item.rejectionReason
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "rejectionReason is required when "
                    "rejectedQuantity is greater than 0"
                ),
            )

        receipt_items.append(
            GoodsReceiptItem(
                productId=payload_item.productId,
                name=payload_item.name,
                orderedQuantity=po_item.quantity,
                previouslyReceivedQuantity=already_received,
                receivedQuantity=payload_item.receivedQuantity,
                acceptedQuantity=payload_item.acceptedQuantity,
                rejectedQuantity=payload_item.rejectedQuantity,
                rejectionReason=payload_item.rejectionReason,
            )
        )

    # Validasi semua product terlebih dahulu sebelum
    # menyimpan Goods Receipt.
    products_collection = client[
        settings.mongodb_database
    ]["products"]

    from bson import ObjectId

    product_documents = {}

    for item in receipt_items:
        try:
            product_object_id = ObjectId(item.productId)
        except Exception:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Invalid product id: "
                    f"{item.productId}"
                ),
            )

        product = await products_collection.find_one(
            {"_id": product_object_id}
        )

        if not product:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Product {item.productId} not found"
                ),
            )

        product_documents[item.productId] = (
            product_object_id,
            product,
        )

    receipt = GoodsReceipt(
        receiptNumber=await next_document_number("GR"),
        purchaseOrderId=str(purchase_order.id),
        supplierId=purchase_order.supplierId,
        items=receipt_items,
        receivedBy=user_id,
        receivedAt=utc_now(),
        notes=payload.notes,
    )

    await receipt.insert()

    stock_movements_collection = client[
        settings.mongodb_database
    ]["stock_movements"]

    total_received_for_po: dict[str, int] = {}

    for item in receipt_items:
        total_received_for_po[item.productId] = (
            previously_received.get(item.productId, 0)
            + item.receivedQuantity
        )

        if item.acceptedQuantity <= 0:
            continue

        product_object_id, product = (
            product_documents[item.productId]
        )

        stock_before = int(
            product.get("stock", 0)
        )

        stock_after = (
            stock_before
            + item.acceptedQuantity
        )

        await products_collection.update_one(
            {"_id": product_object_id},
            {
                "$set": {
                    "stock": stock_after,
                    "updatedAt": utc_now(),
                }
            },
        )

        await stock_movements_collection.insert_one(
            {
                "productId": item.productId,
                "type": "PURCHASE",
                "quantity": item.acceptedQuantity,
                "stockBefore": stock_before,
                "stockAfter": stock_after,
                "referenceType": "GOODS_RECEIPT",
                "referenceId": str(receipt.id),
                "createdBy": user_id,
                "createdAt": utc_now(),
            }
        )

    all_items_completed = True

    for po_item in purchase_order.items:
        received_quantity = total_received_for_po.get(
            po_item.productId,
            previously_received.get(
                po_item.productId,
                0,
            ),
        )

        if received_quantity < po_item.quantity:
            all_items_completed = False
            break

    if all_items_completed:
        purchase_order.status = POStatus.RECEIVED
    else:
        purchase_order.status = (
            POStatus.PARTIALLY_RECEIVED
        )

    purchase_order.updatedAt = utc_now()

    await purchase_order.save()

    return receipt


async def create_purchase(
    payload: PurchaseCreate,
    user_id: str,
) -> Purchase:
    receipt = await GoodsReceipt.get(
        payload.receiptId
    )

    if not receipt:
        raise HTTPException(
            status_code=404,
            detail="Goods Receipt not found",
        )

    purchase_order = await PurchaseOrder.get(
        receipt.purchaseOrderId
    )

    if not purchase_order:
        raise HTTPException(
            status_code=404,
            detail="Purchase Order not found",
        )

    existing_purchase = await Purchase.find(
        Purchase.receiptId == str(receipt.id)
    ).first_or_none()

    if existing_purchase:
        raise HTTPException(
            status_code=409,
            detail=(
                "Purchase already exists "
                "for this Goods Receipt"
            ),
        )

    prices = {
        item.productId: item.unitPrice
        for item in purchase_order.items
    }

    purchase_items: list[PurchaseItem] = []

    for receipt_item in receipt.items:
        if receipt_item.acceptedQuantity <= 0:
            continue

        price = prices.get(
            receipt_item.productId,
            0,
        )

        quantity = receipt_item.acceptedQuantity

        purchase_items.append(
            PurchaseItem(
                productId=receipt_item.productId,
                name=receipt_item.name,
                quantity=quantity,
                price=price,
                subtotal=quantity * price,
            )
        )

    if not purchase_items:
        raise HTTPException(
            status_code=422,
            detail=(
                "Goods Receipt does not contain "
                "any accepted quantity"
            ),
        )

    subtotal = sum(
        item.subtotal
        for item in purchase_items
    )

    total = subtotal - payload.discount

    if total < 0:
        raise HTTPException(
            status_code=422,
            detail="Purchase total cannot be negative",
        )

    purchase = Purchase(
        purchaseNumber=await next_document_number(
            "PUR"
        ),
        supplierId=receipt.supplierId,
        purchaseOrderId=receipt.purchaseOrderId,
        receiptId=str(receipt.id),
        items=purchase_items,
        subtotal=subtotal,
        discount=payload.discount,
        total=total,
        paymentStatus=PaymentStatus.UNPAID,
        createdBy=user_id,
        createdAt=utc_now(),
    )

    await purchase.insert()

    return purchase


async def create_supplier_invoice(
    payload: SupplierInvoiceCreate,
) -> SupplierInvoice:
    receipt = await GoodsReceipt.get(
        payload.receiptId
    )

    if not receipt:
        raise HTTPException(
            status_code=404,
            detail="Goods Receipt not found",
        )

    purchase_order = await PurchaseOrder.get(
        receipt.purchaseOrderId
    )

    if not purchase_order:
        raise HTTPException(
            status_code=404,
            detail="Purchase Order not found",
        )

    purchase = await Purchase.find(
        Purchase.receiptId == str(receipt.id)
    ).first_or_none()

    if not purchase:
        raise HTTPException(
            status_code=409,
            detail=(
                "Create Purchase before creating "
                "Supplier Invoice"
            ),
        )

    existing_invoice = await SupplierInvoice.find(
        SupplierInvoice.invoiceNumber
        == payload.invoiceNumber
    ).first_or_none()

    if existing_invoice:
        raise HTTPException(
            status_code=409,
            detail="Invoice number already exists",
        )

    total = (
        purchase.total
        + payload.tax
        + payload.shippingCost
    )

    invoice = SupplierInvoice(
        invoiceNumber=payload.invoiceNumber,
        supplierId=receipt.supplierId,
        purchaseOrderId=receipt.purchaseOrderId,
        receiptId=str(receipt.id),
        invoiceDate=payload.invoiceDate,
        dueDate=payload.dueDate,
        subtotal=purchase.total,
        tax=payload.tax,
        shippingCost=payload.shippingCost,
        total=total,
        paymentStatus=PaymentStatus.UNPAID,
        createdAt=utc_now(),
        updatedAt=utc_now(),
    )

    await invoice.insert()

    return invoice


async def get_supplier_payables() -> list[dict]:
    invoices = await SupplierInvoice.find_all().to_list()

    result = []

    for invoice in invoices:
        payments = await SupplierPayment.find(
            SupplierPayment.invoiceId
            == str(invoice.id)
        ).to_list()

        paid = sum(
            payment.amount
            for payment in payments
        )

        outstanding = max(
            invoice.total - paid,
            0,
        )

        due_date = invoice.dueDate

        if due_date.tzinfo is None:
            due_date = due_date.replace(
                tzinfo=timezone.utc,
            )

        if outstanding == 0:
            payment_status = PaymentStatus.PAID
        elif paid > 0:
            payment_status = (
                PaymentStatus.PARTIALLY_PAID
            )
        elif due_date < utc_now():
            payment_status = PaymentStatus.OVERDUE
        else:
            payment_status = PaymentStatus.UNPAID

        result.append(
            {
                "invoiceId": str(invoice.id),
                "invoiceNumber": invoice.invoiceNumber,
                "supplierId": invoice.supplierId,
                "total": invoice.total,
                "paid": paid,
                "outstanding": outstanding,
                "paymentStatus": payment_status,
                "dueDate": due_date,
            }
        )

    return result

async def create_supplier_payment(
    payload: SupplierPaymentCreate,
    user_id: str,
) -> SupplierPayment:
    invoice = await SupplierInvoice.get(
        payload.invoiceId
    )

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Supplier Invoice not found",
        )

    payments = await SupplierPayment.find(
        SupplierPayment.invoiceId
        == str(invoice.id)
    ).to_list()

    total_paid = sum(
        payment.amount
        for payment in payments
    )

    outstanding = (
        invoice.total
        - total_paid
    )

    if outstanding <= 0:
        raise HTTPException(
            status_code=409,
            detail="Supplier invoice is already fully paid",
        )

    if payload.amount > outstanding:
        raise HTTPException(
            status_code=422,
            detail=(
                "Payment amount exceeds "
                "outstanding debt"
            ),
        )

    payment = SupplierPayment(
        supplierId=invoice.supplierId,
        invoiceId=str(invoice.id),
        paymentNumber=await next_document_number(
            "PAY-SUP"
        ),
        amount=payload.amount,
        method=payload.method,
        paymentDate=payload.paymentDate,
        referenceNumber=payload.referenceNumber,
        createdBy=user_id,
        notes=payload.notes,
        createdAt=utc_now(),
    )

    await payment.insert()

    new_total_paid = (
        total_paid + payload.amount
    )

    if new_total_paid >= invoice.total:
        invoice.paymentStatus = PaymentStatus.PAID
    else:
        invoice.paymentStatus = (
            PaymentStatus.PARTIALLY_PAID
        )

    invoice.updatedAt = utc_now()

    await invoice.save()

    return payment