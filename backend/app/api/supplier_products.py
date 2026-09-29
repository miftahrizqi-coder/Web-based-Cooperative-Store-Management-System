from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import get_current_user
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.supplier_product import SupplierProduct
from app.models.user import User, UserRole
from app.schemas.supplier_product import (
    SupplierProductCreateRequest,
    SupplierProductResponse,
    SupplierProductStatusRequest,
    SupplierProductUpdateRequest,
)


router = APIRouter(
    prefix="/api/supplier-products",
    tags=["Supplier Products"],
)


async def require_supplier_product_manager(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in {
        UserRole.ADMIN,
        UserRole.PENGURUS,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return current_user


def to_response(item: SupplierProduct) -> SupplierProductResponse:
    return SupplierProductResponse(
        id=str(item.id),
        supplierId=item.supplierId,
        productId=item.productId,
        supplierSku=item.supplierSku,
        purchasePrice=item.purchasePrice,
        minimumOrder=item.minimumOrder,
        leadTimeDays=item.leadTimeDays,
        isPreferred=item.isPreferred,
        isActive=item.isActive,
        createdAt=item.createdAt,
        updatedAt=item.updatedAt,
    )


@router.get("", response_model=list[SupplierProductResponse])
async def list_supplier_products(
    supplier_id: str | None = None,
    product_id: str | None = None,
    is_active: bool | None = None,
    current_user: User = Depends(require_supplier_product_manager),
):
    query = {}

    if supplier_id:
        query["supplierId"] = supplier_id

    if product_id:
        query["productId"] = product_id

    if is_active is not None:
        query["isActive"] = is_active

    items = await SupplierProduct.find(query).sort(
        [
            ("isPreferred", -1),
            ("supplierSku", 1),
        ]
    ).to_list()

    return [to_response(item) for item in items]


@router.get(
    "/{supplier_product_id}",
    response_model=SupplierProductResponse,
)
async def get_supplier_product(
    supplier_product_id: str,
    current_user: User = Depends(require_supplier_product_manager),
):
    item = await SupplierProduct.get(supplier_product_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier Product not found",
        )

    return to_response(item)


@router.post(
    "",
    response_model=SupplierProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_supplier_product(
    payload: SupplierProductCreateRequest,
    current_user: User = Depends(require_supplier_product_manager),
):
    product = await Product.get(payload.productId)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    supplier = await Supplier.get(payload.supplierId)

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    existing = await SupplierProduct.find_one(
        {
            "supplierId": payload.supplierId,
            "productId": payload.productId,
        }
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is already linked to this Supplier",
        )

    now = datetime.now(timezone.utc)

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

    return to_response(item)


@router.put(
    "/{supplier_product_id}",
    response_model=SupplierProductResponse,
)
async def update_supplier_product(
    supplier_product_id: str,
    payload: SupplierProductUpdateRequest,
    current_user: User = Depends(require_supplier_product_manager),
):
    item = await SupplierProduct.get(supplier_product_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier Product not found",
        )

    item.supplierSku = payload.supplierSku.strip()
    item.purchasePrice = payload.purchasePrice
    item.minimumOrder = payload.minimumOrder
    item.leadTimeDays = payload.leadTimeDays
    item.isPreferred = payload.isPreferred
    item.updatedAt = datetime.now(timezone.utc)

    await item.save()

    return to_response(item)


@router.patch(
    "/{supplier_product_id}/status",
    response_model=SupplierProductResponse,
)
async def update_supplier_product_status(
    supplier_product_id: str,
    payload: SupplierProductStatusRequest,
    current_user: User = Depends(require_supplier_product_manager),
):
    item = await SupplierProduct.get(supplier_product_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier Product not found",
        )

    item.isActive = payload.isActive
    item.updatedAt = datetime.now(timezone.utc)

    await item.save()

    return to_response(item)