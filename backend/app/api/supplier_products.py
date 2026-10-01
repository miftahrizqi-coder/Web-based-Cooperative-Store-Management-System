from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.deps import ADMIN_PENGURUS, client_ip, require_role
from app.core.utils import parse_object_id, utc_now
from app.models.audit_log import AuditAction, AuditModule
from app.models.procurement import PurchaseOrder
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.supplier_product import SupplierProduct
from app.models.user import User
from app.schemas.supplier_product import (
    SupplierProductCreateRequest,
    SupplierProductResponse,
    SupplierProductStatusRequest,
    SupplierProductUpdateRequest,
)
from app.services.audit import log_audit


router = APIRouter(prefix="/api/supplier-products", tags=["Supplier Products"])

manager = require_role(*ADMIN_PENGURUS)


async def _lookup(model, ids: set[str]) -> dict:
    object_ids = [ObjectId(i) for i in ids if ObjectId.is_valid(i)]
    if not object_ids:
        return {}
    docs = await model.find({"_id": {"$in": object_ids}}).to_list()
    return {str(d.id): d for d in docs}


def _build(item: SupplierProduct, products: dict, suppliers: dict) -> SupplierProductResponse:
    product = products.get(item.productId)
    supplier = suppliers.get(item.supplierId)
    return SupplierProductResponse(
        id=str(item.id),
        supplierId=item.supplierId,
        supplierName=supplier.name if supplier else None,
        productId=item.productId,
        productName=product.name if product else None,
        productSku=product.sku if product else None,
        supplierSku=item.supplierSku,
        purchasePrice=item.purchasePrice,
        minimumOrder=item.minimumOrder,
        leadTimeDays=item.leadTimeDays,
        isPreferred=item.isPreferred,
        isActive=item.isActive,
        createdAt=item.createdAt,
        updatedAt=item.updatedAt,
    )


async def to_response(item: SupplierProduct) -> SupplierProductResponse:
    products = await _lookup(Product, {item.productId})
    suppliers = await _lookup(Supplier, {item.supplierId})
    return _build(item, products, suppliers)


async def get_item_or_404(item_id: str) -> SupplierProduct:
    item = await SupplierProduct.get(parse_object_id(item_id, "ID produk supplier"))
    if item is None:
        raise HTTPException(status_code=404, detail="Produk supplier tidak ditemukan.")
    return item


async def clear_other_preferred(item: SupplierProduct) -> None:
    """Hanya satu supplier preferred per produk."""
    if item.isPreferred:
        await SupplierProduct.get_pymongo_collection().update_many(
            {"productId": item.productId, "_id": {"$ne": item.id}},
            {"$set": {"isPreferred": False, "updatedAt": utc_now()}},
        )


@router.get("", response_model=list[SupplierProductResponse])
async def list_supplier_products(
    supplier_id: str | None = Query(default=None),
    product_id: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    current_user: User = Depends(manager),
):
    query: dict = {}
    if supplier_id:
        query["supplierId"] = supplier_id
    if product_id:
        query["productId"] = product_id
    if is_active is not None:
        query["isActive"] = is_active

    items = await SupplierProduct.find(query).sort(
        [("isPreferred", -1), ("supplierSku", 1)]
    ).to_list()

    products = await _lookup(Product, {i.productId for i in items})
    suppliers = await _lookup(Supplier, {i.supplierId for i in items})
    return [_build(i, products, suppliers) for i in items]


@router.get("/{item_id}", response_model=SupplierProductResponse)
async def get_supplier_product(item_id: str, current_user: User = Depends(manager)):
    return await to_response(await get_item_or_404(item_id))


@router.post("", response_model=SupplierProductResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier_product(
    payload: SupplierProductCreateRequest,
    request: Request,
    current_user: User = Depends(manager),
):
    product = await Product.get(parse_object_id(payload.productId, "ID produk"))
    if product is None:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan.")

    supplier = await Supplier.get(parse_object_id(payload.supplierId, "ID supplier"))
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan.")

    if await SupplierProduct.find_one(
        {"supplierId": payload.supplierId, "productId": payload.productId}
    ):
        raise HTTPException(status_code=409, detail="Produk sudah terhubung dengan supplier ini.")

    now = utc_now()
    item = SupplierProduct(
        supplierId=payload.supplierId,
        productId=payload.productId,
        supplierSku=payload.supplierSku.strip(),
        purchasePrice=payload.purchasePrice,
        minimumOrder=payload.minimumOrder,
        leadTimeDays=payload.leadTimeDays,
        isPreferred=payload.isPreferred,
        isActive=payload.isActive,
        createdAt=now,
        updatedAt=now,
    )
    await item.insert()
    await clear_other_preferred(item)

    await log_audit(
        action=AuditAction.CREATE,
        module=AuditModule.SUPPLIER_PRODUCT,
        description=f"Menghubungkan produk {product.sku} ke supplier {supplier.name}",
        user=current_user,
        reference_id=str(item.id),
        ip_address=client_ip(request),
    )
    return await to_response(item)


@router.put("/{item_id}", response_model=SupplierProductResponse)
async def update_supplier_product(
    item_id: str,
    payload: SupplierProductUpdateRequest,
    request: Request,
    current_user: User = Depends(manager),
):
    item = await get_item_or_404(item_id)

    old_price = item.purchasePrice
    item.supplierSku = payload.supplierSku.strip()
    item.purchasePrice = payload.purchasePrice
    item.minimumOrder = payload.minimumOrder
    item.leadTimeDays = payload.leadTimeDays
    item.isPreferred = payload.isPreferred
    if payload.isActive is not None:
        item.isActive = payload.isActive
    item.updatedAt = utc_now()
    await item.save()
    await clear_other_preferred(item)

    await log_audit(
        action=AuditAction.UPDATE,
        module=AuditModule.SUPPLIER_PRODUCT,
        description=f"Mengubah produk supplier {item.supplierSku}",
        user=current_user,
        reference_id=str(item.id),
        metadata=(
            {"purchasePrice": {"from": old_price, "to": item.purchasePrice}}
            if old_price != item.purchasePrice
            else None
        ),
        ip_address=client_ip(request),
    )
    return await to_response(item)


@router.patch("/{item_id}/status", response_model=SupplierProductResponse)
async def update_supplier_product_status(
    item_id: str,
    payload: SupplierProductStatusRequest,
    request: Request,
    current_user: User = Depends(manager),
):
    item = await get_item_or_404(item_id)
    item.isActive = payload.isActive
    item.updatedAt = utc_now()
    await item.save()

    await log_audit(
        action=AuditAction.UPDATE,
        module=AuditModule.SUPPLIER_PRODUCT,
        description=(
            f"{'Mengaktifkan' if item.isActive else 'Menonaktifkan'} "
            f"produk supplier {item.supplierSku}"
        ),
        user=current_user,
        reference_id=str(item.id),
        ip_address=client_ip(request),
    )
    return await to_response(item)


@router.delete("/{item_id}", response_model=SupplierProductResponse | None)
async def delete_supplier_product(
    item_id: str,
    request: Request,
    current_user: User = Depends(manager),
):
    """Hapus relasi jika belum dipakai PO; jika sudah, relasi dinonaktifkan."""
    item = await get_item_or_404(item_id)

    used = await PurchaseOrder.find_one({"items.supplierProductId": item_id})

    if used:
        item.isActive = False
        item.isPreferred = False
        item.updatedAt = utc_now()
        await item.save()
        description = f"Menonaktifkan produk supplier {item.supplierSku} (sudah dipakai PO)"
    else:
        await item.delete()
        description = f"Menghapus produk supplier {item.supplierSku}"

    await log_audit(
        action=AuditAction.DELETE,
        module=AuditModule.SUPPLIER_PRODUCT,
        description=description,
        user=current_user,
        reference_id=item_id,
        ip_address=client_ip(request),
    )

    return await to_response(item) if used else None
