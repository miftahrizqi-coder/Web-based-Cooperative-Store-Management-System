from datetime import date

from bson import ObjectId
from fastapi import HTTPException

from app.core.uow import unit_of_work
from app.core.utils import (
    PageParams,
    local_range_bounds,
    next_document_number,
    parse_object_id,
    search_regex,
)
from app.models.audit_log import AuditAction, AuditModule
from app.models.category import Category
from app.models.inventory import (
    StockMovement,
    StockMovementType,
    StockOpname,
    StockOpnameItem,
)
from app.models.product import Product
from app.models.user import User
from app.schemas.inventory import (
    InventoryResponse,
    StockAdjustmentRequest,
    StockAdjustmentResponse,
    StockAlertResponse,
    StockMovementResponse,
    StockOpnameItemResponse,
    StockOpnameRequest,
    StockOpnameResponse,
)
from app.services.audit import log_audit
from app.services.stock import apply_stock_change, stock_status


async def _names(model, ids: set[str], attr: str = "name") -> dict[str, str]:
    object_ids = [ObjectId(i) for i in ids if i and ObjectId.is_valid(i)]
    if not object_ids:
        return {}
    docs = await model.find({"_id": {"$in": object_ids}}).to_list()
    return {str(d.id): getattr(d, attr) for d in docs}


def inventory_response(product: Product, categories: dict[str, str]) -> InventoryResponse:
    return InventoryResponse(
        productId=str(product.id),
        sku=product.sku,
        barcode=product.barcode,
        name=product.name,
        categoryId=product.categoryId,
        categoryName=categories.get(product.categoryId),
        unit=product.unit,
        stock=product.stock,
        minimumStock=product.minimumStock,
        stockStatus=stock_status(product.stock, product.minimumStock),
        purchasePrice=product.purchasePrice,
        sellingPrice=product.sellingPrice,
        stockValue=round(product.stock * product.purchasePrice, 2),
        isActive=product.isActive,
        updatedAt=product.updatedAt,
    )


async def list_inventory(
    pagination: PageParams,
    search: str | None = None,
    stock_status_filter: str | None = None,
    category_id: str | None = None,
) -> list[InventoryResponse]:
    query: dict = {"isActive": True}
    if search and search.strip():
        regex = search_regex(search)
        query["$or"] = [{"name": regex}, {"sku": regex}, {"barcode": regex}]
    if category_id:
        query["categoryId"] = category_id

    products = await Product.find(query).sort("name").to_list()
    if stock_status_filter:
        products = [
            p for p in products
            if stock_status(p.stock, p.minimumStock) == stock_status_filter
        ]

    products = pagination.slice(products)
    categories = await _names(Category, {p.categoryId for p in products})
    return [inventory_response(p, categories) for p in products]


async def get_inventory_product(product_id: str) -> InventoryResponse:
    product = await Product.get(parse_object_id(product_id, "ID produk"))
    if product is None:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan.")
    categories = await _names(Category, {product.categoryId})
    return inventory_response(product, categories)


async def list_stock_movements(
    pagination: PageParams,
    product_id: str | None = None,
    movement_type: StockMovementType | None = None,
    reference_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[StockMovementResponse]:
    query: dict = {}
    if product_id:
        query["productId"] = product_id
    if movement_type:
        query["type"] = movement_type.value
    if reference_id:
        query["referenceId"] = reference_id

    start, end = local_range_bounds(date_from, date_to)
    if start or end:
        query["createdAt"] = {}
        if start:
            query["createdAt"]["$gte"] = start
        if end:
            query["createdAt"]["$lt"] = end

    movements = await pagination.apply(StockMovement.find(query).sort("-createdAt"))
    if not movements:
        return []

    object_ids = [ObjectId(m.productId) for m in movements if ObjectId.is_valid(m.productId)]
    products = {
        str(p.id): p for p in await Product.find({"_id": {"$in": object_ids}}).to_list()
    }
    users = await _names(User, {m.createdBy for m in movements})

    return [
        StockMovementResponse(
            id=str(m.id),
            productId=m.productId,
            sku=products[m.productId].sku if m.productId in products else "-",
            productName=(
                products[m.productId].name if m.productId in products else "Produk tidak ditemukan"
            ),
            type=m.type.value,
            quantity=m.quantity,
            stockBefore=m.stockBefore,
            stockAfter=m.stockAfter,
            referenceType=m.referenceType,
            referenceId=m.referenceId,
            referenceNumber=m.referenceNumber,
            reason=m.reason,
            createdBy=m.createdBy,
            createdByName=users.get(m.createdBy),
            createdAt=m.createdAt,
        )
        for m in movements
    ]


async def create_stock_adjustment(
    data: StockAdjustmentRequest,
    current_user: User,
    ip_address: str | None = None,
) -> StockAdjustmentResponse:
    product = await Product.get(parse_object_id(data.productId, "ID produk"))
    if product is None:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan.")

    async with unit_of_work() as uow:
        movement = await apply_stock_change(
            uow,
            product_id=data.productId,
            delta=data.quantity,
            movement_type=StockMovementType.ADJUSTMENT,
            user_id=str(current_user.id),
            reference_type="STOCK_ADJUSTMENT",
            reason=data.reason,
            require_active=True,
        )
        await log_audit(
            action=AuditAction.STOCK_ADJUSTMENT,
            module=AuditModule.INVENTORY,
            description=(
                f"Adjustment stok {product.sku} {data.quantity:+g} "
                f"({movement.stockBefore:g} -> {movement.stockAfter:g}): {data.reason}"
            ),
            user=current_user,
            reference_id=str(movement.id),
            metadata={"productId": data.productId, "quantity": data.quantity},
            ip_address=ip_address,
            session=uow.session,
        )

    return StockAdjustmentResponse(
        productId=data.productId,
        quantity=data.quantity,
        stockBefore=movement.stockBefore,
        stockAfter=movement.stockAfter,
        reason=data.reason,
        movementId=str(movement.id),
    )


def opname_response(opname: StockOpname, user_names: dict[str, str] | None = None) -> StockOpnameResponse:
    return StockOpnameResponse(
        id=str(opname.id),
        opnameNumber=opname.opnameNumber,
        items=[StockOpnameItemResponse(**item.model_dump()) for item in opname.items],
        notes=opname.notes,
        totalItems=opname.totalItems,
        itemsWithDifference=opname.itemsWithDifference,
        createdBy=opname.createdBy,
        createdByName=(user_names or {}).get(opname.createdBy),
        createdAt=opname.createdAt,
    )


async def create_stock_opname(
    data: StockOpnameRequest,
    current_user: User,
    ip_address: str | None = None,
) -> StockOpnameResponse:
    """
    PRD §21: ambil stok sistem -> hitung fisik -> bandingkan -> jika selisih,
    buat adjustment (movement STOCK_OPNAME). Selisih wajib diberi alasan.
    """
    user_id = str(current_user.id)
    seen: set[str] = set()
    prepared: list[tuple[Product, float, float, str | None]] = []

    for line in data.items:
        if line.productId in seen:
            raise HTTPException(status_code=422, detail="Produk duplikat dalam stock opname.")
        seen.add(line.productId)

        product = await Product.get(parse_object_id(line.productId, "ID produk"))
        if product is None:
            raise HTTPException(status_code=404, detail=f"Produk {line.productId} tidak ditemukan.")
        if not product.isActive:
            raise HTTPException(status_code=400, detail=f"Produk {product.name} tidak aktif.")

        system_stock = product.stock if line.systemStock is None else line.systemStock
        if line.systemStock is not None and line.systemStock != product.stock:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Stok sistem {product.name} berubah dari {line.systemStock:g} "
                    f"menjadi {product.stock:g} sejak dihitung. Muat ulang lalu ulangi."
                ),
            )

        difference = line.physicalStock - system_stock
        reason = (line.reason or "").strip() or None
        if difference != 0 and not reason:
            raise HTTPException(
                status_code=422,
                detail=f"Alasan selisih wajib diisi untuk {product.name}.",
            )
        prepared.append((product, system_stock, difference, reason))

    async with unit_of_work() as uow:
        opname = StockOpname(
            opnameNumber=await next_document_number("SO"),
            items=[],
            notes=data.notes,
            totalItems=len(prepared),
            itemsWithDifference=sum(1 for _, _, diff, _ in prepared if diff != 0),
            createdBy=user_id,
        )
        await uow.insert(opname)

        items: list[StockOpnameItem] = []
        for product, system_stock, difference, reason in prepared:
            movement_id = None
            if difference != 0:
                movement = await apply_stock_change(
                    uow,
                    product_id=str(product.id),
                    delta=difference,
                    movement_type=StockMovementType.STOCK_OPNAME,
                    user_id=user_id,
                    reference_type="STOCK_OPNAME",
                    reference_id=str(opname.id),
                    reference_number=opname.opnameNumber,
                    reason=reason,
                    expected_stock=system_stock,
                )
                movement_id = str(movement.id)

            items.append(
                StockOpnameItem(
                    productId=str(product.id),
                    sku=product.sku,
                    name=product.name,
                    systemStock=system_stock,
                    physicalStock=system_stock + difference,
                    difference=difference,
                    reason=reason,
                    movementId=movement_id,
                )
            )

        opname.items = items
        await opname.save(session=uow.session)

        await log_audit(
            action=AuditAction.STOCK_OPNAME,
            module=AuditModule.INVENTORY,
            description=(
                f"Stock opname {opname.opnameNumber}: {opname.totalItems} produk, "
                f"{opname.itemsWithDifference} selisih"
            ),
            user=current_user,
            reference_id=str(opname.id),
            ip_address=ip_address,
            session=uow.session,
        )

    return opname_response(opname, {user_id: current_user.name})


async def list_stock_opnames(pagination: PageParams) -> list[StockOpnameResponse]:
    opnames = await pagination.apply(StockOpname.find({}).sort("-createdAt"))
    users = await _names(User, {o.createdBy for o in opnames})
    return [opname_response(o, users) for o in opnames]


async def get_stock_opname(opname_id: str) -> StockOpnameResponse:
    opname = await StockOpname.get(parse_object_id(opname_id, "ID stock opname"))
    if opname is None:
        raise HTTPException(status_code=404, detail="Stock opname tidak ditemukan.")
    users = await _names(User, {opname.createdBy})
    return opname_response(opname, users)


async def list_stock_alerts() -> list[StockAlertResponse]:
    products = await Product.find({"isActive": True}).sort("stock").to_list()
    return [
        StockAlertResponse(
            productId=str(p.id),
            sku=p.sku,
            name=p.name,
            unit=p.unit,
            stock=p.stock,
            minimumStock=p.minimumStock,
            status=stock_status(p.stock, p.minimumStock),
        )
        for p in products
        if stock_status(p.stock, p.minimumStock) != "AVAILABLE"
    ]
