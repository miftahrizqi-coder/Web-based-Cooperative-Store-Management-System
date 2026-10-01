from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.core.deps import ADMIN_PENGURUS, client_ip, require_role
from app.core.utils import Pagination, PageParams, parse_object_id, search_regex, utc_now
from app.models.audit_log import AuditAction, AuditModule
from app.models.procurement import (
    GoodsReceipt,
    Purchase,
    PurchaseOrder,
    SupplierInvoice,
    SupplierPayment,
)
from app.models.supplier import Supplier, SupplierPaymentTermType, SupplierStatus
from app.models.supplier_product import SupplierProduct
from app.models.user import User
from app.schemas.procurement import (
    GoodsReceiptResponse,
    PayableResponse,
    PurchaseOrderResponse,
    PurchaseResponse,
    SupplierInvoiceResponse,
    SupplierPaymentResponse,
)
from app.schemas.supplier import (
    SupplierCreateRequest,
    SupplierResponse,
    SupplierStatusRequest,
    SupplierUpdateRequest,
)
from app.schemas.supplier_product import SupplierProductResponse
from app.services.audit import log_audit
from app.services.procurement import (
    compute_payables,
    goods_receipt_response,
    purchase_order_response,
    purchase_response,
    supplier_invoice_response,
    supplier_payment_response,
)
from app.api.supplier_products import to_response as supplier_product_response


router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])

supplier_manager = require_role(*ADMIN_PENGURUS)


class SupplierSummaryResponse(BaseModel):
    supplierId: str
    productsSupplied: int
    purchaseOrderCount: int
    activePurchaseOrderCount: int
    receiptCount: int
    totalPurchases: float
    invoiceCount: int
    totalInvoiced: float
    totalPaid: float
    totalReturned: float
    outstanding: float
    overdueInvoiceCount: int


def supplier_response(supplier: Supplier) -> SupplierResponse:
    return SupplierResponse(
        id=str(supplier.id),
        supplierCode=supplier.supplierCode,
        name=supplier.name,
        companyName=supplier.companyName,
        contactPerson=supplier.contactPerson,
        phone=supplier.phone,
        email=supplier.email,
        address=supplier.address,
        paymentTerm=supplier.paymentTerm,
        bankAccount=supplier.bankAccount,
        status=supplier.status,
        notes=supplier.notes,
        createdAt=supplier.createdAt,
        updatedAt=supplier.updatedAt,
    )


async def get_supplier_or_404(supplier_id: str) -> Supplier:
    supplier = await Supplier.get(parse_object_id(supplier_id, "ID supplier"))
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan.")
    return supplier


def validate_payment_term(data) -> None:
    if data.paymentTerm.type == SupplierPaymentTermType.CASH and data.paymentTerm.days != 0:
        raise HTTPException(status_code=400, detail="Payment term CASH harus memiliki 0 hari.")
    if data.paymentTerm.type == SupplierPaymentTermType.CREDIT and data.paymentTerm.days <= 0:
        raise HTTPException(status_code=400, detail="Payment term CREDIT harus lebih dari 0 hari.")


@router.get("", response_model=list[SupplierResponse])
async def list_suppliers(
    search: str | None = Query(default=None),
    status_filter: SupplierStatus | None = Query(default=None, alias="status"),
    pagination: PageParams = Depends(Pagination()),
    user: User = Depends(supplier_manager),
):
    query: dict = {}
    if search and search.strip():
        regex = search_regex(search)
        query["$or"] = [
            {"name": regex},
            {"companyName": regex},
            {"supplierCode": regex},
            {"contactPerson": regex},
        ]
    if status_filter:
        query["status"] = status_filter.value

    suppliers = await pagination.apply(Supplier.find(query).sort("name"))
    return [supplier_response(s) for s in suppliers]


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: str, user: User = Depends(supplier_manager)):
    return supplier_response(await get_supplier_or_404(supplier_id))


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    data: SupplierCreateRequest,
    request: Request,
    user: User = Depends(supplier_manager),
):
    if await Supplier.find_one(Supplier.supplierCode == data.supplierCode.strip()):
        raise HTTPException(status_code=409, detail="Kode supplier sudah digunakan.")

    if await Supplier.find_one(Supplier.email == data.email):
        raise HTTPException(status_code=409, detail="Email supplier sudah digunakan.")

    validate_payment_term(data)

    payload = data.model_dump()
    payload["supplierCode"] = payload["supplierCode"].strip()
    supplier = Supplier(**payload)
    await supplier.insert()

    await log_audit(
        action=AuditAction.CREATE,
        module=AuditModule.SUPPLIER,
        description=f"Membuat supplier {supplier.supplierCode} - {supplier.name}",
        user=user,
        reference_id=str(supplier.id),
        ip_address=client_ip(request),
    )
    return supplier_response(supplier)


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: str,
    data: SupplierUpdateRequest,
    request: Request,
    user: User = Depends(supplier_manager),
):
    supplier = await get_supplier_or_404(supplier_id)

    if await Supplier.find_one({"email": data.email, "_id": {"$ne": supplier.id}}):
        raise HTTPException(status_code=409, detail="Email supplier sudah digunakan.")

    validate_payment_term(data)

    supplier.name = data.name
    supplier.companyName = data.companyName
    supplier.contactPerson = data.contactPerson
    supplier.phone = data.phone
    supplier.email = data.email
    supplier.address = data.address
    supplier.paymentTerm = data.paymentTerm
    supplier.bankAccount = data.bankAccount
    supplier.notes = data.notes
    supplier.updatedAt = utc_now()
    await supplier.save()

    await log_audit(
        action=AuditAction.UPDATE,
        module=AuditModule.SUPPLIER,
        description=f"Mengubah supplier {supplier.supplierCode} - {supplier.name}",
        user=user,
        reference_id=str(supplier.id),
        ip_address=client_ip(request),
    )
    return supplier_response(supplier)


async def _set_status(supplier: Supplier, new_status: SupplierStatus, user: User, request: Request):
    old_status = supplier.status
    supplier.status = new_status
    supplier.updatedAt = utc_now()
    await supplier.save()

    await log_audit(
        action=AuditAction.UPDATE if new_status != SupplierStatus.INACTIVE else AuditAction.DELETE,
        module=AuditModule.SUPPLIER,
        description=(
            f"Status supplier {supplier.supplierCode} diubah "
            f"{old_status.value} -> {new_status.value}"
        ),
        user=user,
        reference_id=str(supplier.id),
        ip_address=client_ip(request),
    )


@router.patch("/{supplier_id}/status", response_model=SupplierResponse)
async def update_supplier_status(
    supplier_id: str,
    data: SupplierStatusRequest,
    request: Request,
    user: User = Depends(supplier_manager),
):
    supplier = await get_supplier_or_404(supplier_id)
    await _set_status(supplier, data.status, user, request)
    return supplier_response(supplier)


@router.delete("/{supplier_id}", response_model=SupplierResponse)
async def deactivate_supplier(
    supplier_id: str,
    request: Request,
    user: User = Depends(supplier_manager),
):
    """Supplier tidak dihapus permanen (dipakai riwayat PO/invoice)."""
    supplier = await get_supplier_or_404(supplier_id)
    await _set_status(supplier, SupplierStatus.INACTIVE, user, request)
    return supplier_response(supplier)


# ---------------------------------------------------------------------------
# Sub-resource riwayat supplier (PRD §12 & §33)
# ---------------------------------------------------------------------------


@router.get("/{supplier_id}/products", response_model=list[SupplierProductResponse])
async def supplier_products(supplier_id: str, user: User = Depends(supplier_manager)):
    await get_supplier_or_404(supplier_id)
    items = await SupplierProduct.find({"supplierId": supplier_id}).sort(
        [("isPreferred", -1), ("supplierSku", 1)]
    ).to_list()
    return [await supplier_product_response(item) for item in items]


@router.get("/{supplier_id}/purchase-orders", response_model=list[PurchaseOrderResponse])
async def supplier_purchase_orders(
    supplier_id: str,
    pagination: PageParams = Depends(Pagination()),
    user: User = Depends(supplier_manager),
):
    await get_supplier_or_404(supplier_id)
    orders = await pagination.apply(
        PurchaseOrder.find({"supplierId": supplier_id}).sort("-createdAt")
    )
    return [purchase_order_response(o) for o in orders]


@router.get("/{supplier_id}/goods-receipts", response_model=list[GoodsReceiptResponse])
async def supplier_goods_receipts(
    supplier_id: str,
    pagination: PageParams = Depends(Pagination()),
    user: User = Depends(supplier_manager),
):
    await get_supplier_or_404(supplier_id)
    receipts = await pagination.apply(
        GoodsReceipt.find({"supplierId": supplier_id}).sort("-receivedAt")
    )
    return [goods_receipt_response(r) for r in receipts]


@router.get("/{supplier_id}/purchases", response_model=list[PurchaseResponse])
async def supplier_purchases(
    supplier_id: str,
    pagination: PageParams = Depends(Pagination()),
    user: User = Depends(supplier_manager),
):
    await get_supplier_or_404(supplier_id)
    purchases = await pagination.apply(
        Purchase.find({"supplierId": supplier_id}).sort("-createdAt")
    )
    return [purchase_response(p) for p in purchases]


@router.get("/{supplier_id}/invoices", response_model=list[SupplierInvoiceResponse])
async def supplier_invoices(
    supplier_id: str,
    pagination: PageParams = Depends(Pagination()),
    user: User = Depends(supplier_manager),
):
    await get_supplier_or_404(supplier_id)
    invoices = await pagination.apply(
        SupplierInvoice.find({"supplierId": supplier_id}).sort("-invoiceDate")
    )
    payables = {p["invoiceId"]: p for p in await compute_payables(invoices)}
    return [supplier_invoice_response(i, payables.get(str(i.id))) for i in invoices]


@router.get("/{supplier_id}/payments", response_model=list[SupplierPaymentResponse])
async def supplier_payments(
    supplier_id: str,
    pagination: PageParams = Depends(Pagination()),
    user: User = Depends(supplier_manager),
):
    await get_supplier_or_404(supplier_id)
    payments = await pagination.apply(
        SupplierPayment.find({"supplierId": supplier_id}).sort("-paymentDate")
    )
    return [supplier_payment_response(p) for p in payments]


@router.get("/{supplier_id}/payables", response_model=list[PayableResponse])
async def supplier_payables(supplier_id: str, user: User = Depends(supplier_manager)):
    await get_supplier_or_404(supplier_id)
    invoices = await SupplierInvoice.find({"supplierId": supplier_id}).to_list()
    return await compute_payables(invoices)


@router.get("/{supplier_id}/summary", response_model=SupplierSummaryResponse)
async def supplier_summary(supplier_id: str, user: User = Depends(supplier_manager)):
    """Informasi hutang & ringkasan riwayat supplier (PRD §12)."""
    await get_supplier_or_404(supplier_id)

    orders = await PurchaseOrder.find({"supplierId": supplier_id}).to_list()
    invoices = await SupplierInvoice.find({"supplierId": supplier_id}).to_list()
    payables = await compute_payables(invoices)
    purchases = await Purchase.find({"supplierId": supplier_id}).to_list()

    active_statuses = {"PENDING_APPROVAL", "APPROVED", "ORDERED", "PARTIALLY_RECEIVED"}

    return SupplierSummaryResponse(
        supplierId=supplier_id,
        productsSupplied=await SupplierProduct.find(
            {"supplierId": supplier_id, "isActive": True}
        ).count(),
        purchaseOrderCount=len(orders),
        activePurchaseOrderCount=sum(1 for o in orders if o.status.value in active_statuses),
        receiptCount=await GoodsReceipt.find({"supplierId": supplier_id}).count(),
        totalPurchases=sum(p.total for p in purchases),
        invoiceCount=len(invoices),
        totalInvoiced=sum(p["total"] for p in payables),
        totalPaid=sum(p["paid"] for p in payables),
        totalReturned=sum(p["returned"] for p in payables),
        outstanding=sum(p["outstanding"] for p in payables),
        overdueInvoiceCount=sum(1 for p in payables if p["isOverdue"]),
    )
