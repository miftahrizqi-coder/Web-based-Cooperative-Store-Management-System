from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.deps import ADMIN, STAFF, client_ip, require_role
from app.core.uow import unit_of_work
from app.core.utils import Pagination, PageParams, parse_object_id, search_regex, utc_now
from app.models.audit_log import AuditAction, AuditModule
from app.models.category import Category
from app.models.inventory import StockMovement, StockMovementType
from app.models.procurement import PurchaseOrder
from app.models.product import Product
from app.models.sales import Sale
from app.models.supplier_product import SupplierProduct
from app.models.user import User, UserRole
from app.schemas.product import (
    ProductCreateRequest,
    ProductResponse,
    ProductUpdateRequest,
)
from app.services.audit import log_audit
from app.services.stock import apply_stock_change, stock_status


router = APIRouter(prefix="/api/products", tags=["Products"])


async def category_names(ids: set[str]) -> dict[str, str]:
    object_ids = [ObjectId(i) for i in ids if ObjectId.is_valid(i)]
    if not object_ids:
        return {}
    categories = await Category.find({"_id": {"$in": object_ids}}).to_list()
    return {str(c.id): c.name for c in categories}


def to_response(
    product: Product,
    viewer: User,
    names: dict[str, str] | None = None,
) -> ProductResponse:
    can_see_cost = viewer.role in {UserRole.ADMIN, UserRole.PENGURUS}
    return ProductResponse(
        id=str(product.id),
        sku=product.sku,
        barcode=product.barcode,
        name=product.name,
        categoryId=product.categoryId,
        categoryName=(names or {}).get(product.categoryId),
        unit=product.unit,
        purchasePrice=product.purchasePrice if can_see_cost else None,
        sellingPrice=product.sellingPrice,
        stock=product.stock,
        minimumStock=product.minimumStock,
        stockStatus=stock_status(product.stock, product.minimumStock),
        isActive=product.isActive,
        createdAt=product.createdAt,
        updatedAt=product.updatedAt,
    )


async def get_product_or_404(product_id: str) -> Product:
    product = await Product.get(parse_object_id(product_id, "ID produk"))
    if product is None:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan.")
    return product


async def ensure_unique_identifiers(sku: str, barcode: str | None, exclude_id=None) -> None:
    sku_query: dict = {"sku": sku}
    if exclude_id is not None:
        sku_query["_id"] = {"$ne": exclude_id}
    if await Product.find_one(sku_query):
        raise HTTPException(status_code=409, detail="SKU sudah digunakan.")

    if barcode:
        barcode_query: dict = {"barcode": barcode}
        if exclude_id is not None:
            barcode_query["_id"] = {"$ne": exclude_id}
        if await Product.find_one(barcode_query):
            raise HTTPException(status_code=409, detail="Barcode sudah digunakan.")


async def ensure_category(category_id: str, current_category_id: str | None = None) -> None:
    category = await Category.get(parse_object_id(category_id, "ID kategori"))
    if category is None:
        raise HTTPException(status_code=404, detail="Kategori tidak ditemukan.")
    # Kategori nonaktif tetap boleh dipertahankan pada produk lama,
    # tetapi tidak boleh dipilih untuk produk baru / perpindahan kategori.
    if not category.isActive and category_id != current_category_id:
        raise HTTPException(status_code=400, detail="Kategori tidak aktif.")


@router.get("", response_model=list[ProductResponse])
async def list_products(
    search: str | None = Query(default=None),
    category_id: str | None = Query(default=None, alias="categoryId"),
    stock_status_filter: str | None = Query(
        default=None,
        alias="stockStatus",
        pattern="^(all|available|low|out)$",
    ),
    is_active: bool | None = Query(default=None, alias="isActive"),
    pagination: PageParams = Depends(Pagination()),
    current_user: User = Depends(require_role(*STAFF)),
):
    query: dict = {}

    # Kasir hanya melihat produk aktif (PRD §6.2).
    if current_user.role == UserRole.KASIR:
        query["isActive"] = True
    elif is_active is not None:
        query["isActive"] = is_active

    if search and search.strip():
        regex = search_regex(search)
        query["$or"] = [{"name": regex}, {"sku": regex}, {"barcode": regex}]

    if category_id:
        query["categoryId"] = category_id

    if stock_status_filter == "available":
        query["stock"] = {"$gt": 0}
    elif stock_status_filter == "out":
        query["stock"] = {"$lte": 0}

    find = Product.find(query).sort("name")

    if stock_status_filter == "low":
        # Perbandingan antar-field (stock <= minimumStock) difilter di aplikasi
        # agar portabel; jumlah produk koperasi relatif kecil.
        products = [
            p for p in await find.to_list()
            if 0 < p.stock <= p.minimumStock
        ]
        products = pagination.slice(products)
    else:
        products = await pagination.apply(find)

    names = await category_names({p.categoryId for p in products})
    return [to_response(p, current_user, names) for p in products]


@router.get("/barcode/{barcode}", response_model=ProductResponse)
async def get_product_by_barcode(
    barcode: str,
    current_user: User = Depends(require_role(*STAFF)),
):
    product = await Product.find_one({"barcode": barcode.strip(), "isActive": True})
    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Produk dengan barcode tersebut tidak ditemukan.",
        )
    names = await category_names({product.categoryId})
    return to_response(product, current_user, names)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user: User = Depends(require_role(*STAFF)),
):
    product = await get_product_or_404(product_id)
    if current_user.role == UserRole.KASIR and not product.isActive:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan.")
    names = await category_names({product.categoryId})
    return to_response(product, current_user, names)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreateRequest,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN)),
):
    await ensure_unique_identifiers(data.sku, data.barcode)
    await ensure_category(data.categoryId)

    now = utc_now()
    product = Product(
        sku=data.sku,
        barcode=data.barcode,
        name=data.name,
        categoryId=data.categoryId,
        unit=data.unit,
        purchasePrice=data.purchasePrice,
        sellingPrice=data.sellingPrice,
        stock=0,
        minimumStock=data.minimumStock,
        isActive=True,
        createdAt=now,
        updatedAt=now,
    )

    async with unit_of_work() as uow:
        await uow.insert(product)

        if data.stock > 0:
            await apply_stock_change(
                uow,
                product_id=str(product.id),
                delta=data.stock,
                movement_type=StockMovementType.ADJUSTMENT,
                user_id=str(current_user.id),
                reference_type="INITIAL_STOCK",
                reference_id=str(product.id),
                reason="Stok awal produk",
            )

        await log_audit(
            action=AuditAction.CREATE,
            module=AuditModule.PRODUCT,
            description=f"Membuat produk {product.sku} - {product.name}",
            user=current_user,
            reference_id=str(product.id),
            metadata={"initialStock": data.stock},
            ip_address=client_ip(request),
            session=uow.session,
        )

    product = await get_product_or_404(str(product.id))
    names = await category_names({product.categoryId})
    return to_response(product, current_user, names)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    data: ProductUpdateRequest,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN)),
):
    product = await get_product_or_404(product_id)

    await ensure_unique_identifiers(data.sku, data.barcode, exclude_id=product.id)
    await ensure_category(data.categoryId, current_category_id=product.categoryId)

    changes: dict[str, dict] = {}
    for field in (
        "sku", "barcode", "name", "categoryId", "unit",
        "purchasePrice", "sellingPrice", "minimumStock", "isActive",
    ):
        old = getattr(product, field)
        new = getattr(data, field)
        if old != new:
            changes[field] = {"from": old, "to": new}
            setattr(product, field, new)

    if changes:
        product.updatedAt = utc_now()
        # Hanya field yang diubah yang ditulis agar tidak menimpa `stock`
        # yang mungkin berubah bersamaan oleh transaksi lain.
        await Product.get_pymongo_collection().update_one(
            {"_id": product.id},
            {"$set": {**{k: v["to"] for k, v in changes.items()}, "updatedAt": product.updatedAt}},
        )

        price_changed = "purchasePrice" in changes or "sellingPrice" in changes
        await log_audit(
            action=AuditAction.UPDATE,
            module=AuditModule.PRODUCT,
            description=(
                f"Mengubah {'harga ' if price_changed else ''}produk {product.sku} - {product.name}"
            ),
            user=current_user,
            reference_id=str(product.id),
            metadata={"changes": changes},
            ip_address=client_ip(request),
        )

    product = await get_product_or_404(product_id)
    names = await category_names({product.categoryId})
    return to_response(product, current_user, names)


async def product_has_history(product_id: str) -> bool:
    if await StockMovement.find_one({"productId": product_id}):
        return True
    if await Sale.find_one({"items.productId": product_id}):
        return True
    if await PurchaseOrder.find_one({"items.productId": product_id}):
        return True
    return False


@router.delete("/{product_id}", response_model=ProductResponse | None)
async def delete_product(
    product_id: str,
    request: Request,
    permanent: bool = Query(default=False),
    current_user: User = Depends(require_role(*ADMIN)),
):
    """
    Default: nonaktifkan (BR-09). `?permanent=true` hanya diizinkan untuk
    produk yang belum pernah dipakai transaksi / stock movement.
    """
    product = await get_product_or_404(product_id)

    if permanent:
        if await product_has_history(product_id):
            raise HTTPException(
                status_code=409,
                detail="Produk sudah memiliki riwayat transaksi. Nonaktifkan saja produk ini.",
            )
        await SupplierProduct.find({"productId": product_id}).delete()
        await product.delete()
        await log_audit(
            action=AuditAction.DELETE,
            module=AuditModule.PRODUCT,
            description=f"Menghapus permanen produk {product.sku} - {product.name}",
            user=current_user,
            reference_id=product_id,
            ip_address=client_ip(request),
        )
        return None

    product.isActive = False
    product.updatedAt = utc_now()
    await Product.get_pymongo_collection().update_one(
        {"_id": product.id},
        {"$set": {"isActive": False, "updatedAt": product.updatedAt}},
    )

    await log_audit(
        action=AuditAction.DELETE,
        module=AuditModule.PRODUCT,
        description=f"Menonaktifkan produk {product.sku} - {product.name}",
        user=current_user,
        reference_id=product_id,
        ip_address=client_ip(request),
    )

    names = await category_names({product.categoryId})
    return to_response(product, current_user, names)
