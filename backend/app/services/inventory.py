from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.database import client
from app.models.inventory import (
    InventoryAuditEvent,
    StockMovement,
    StockMovementType,
)
from app.models.product import Product
from app.models.user import User
from app.schemas.inventory import (
    InventoryResponse,
    StockAdjustmentRequest,
    StockAdjustmentResponse,
    StockAlertResponse,
    StockMovementResponse,
    StockOpnameRequest,
    StockOpnameResponse,
)


db = client[settings.mongodb_database]
products_collection = db["products"]


def validate_product_id(product_id: str) -> ObjectId:
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product ID tidak valid.",
        )

    return ObjectId(product_id)


def get_stock_status(stock: float, minimum_stock: float) -> str:
    if stock <= 0:
        return "OUT_OF_STOCK"

    if stock <= minimum_stock:
        return "LOW_STOCK"

    return "AVAILABLE"


def inventory_response(product: Product) -> InventoryResponse:
    return InventoryResponse(
        product_id=str(product.id),
        sku=product.sku,
        barcode=product.barcode,
        name=product.name,
        unit=product.unit,
        stock=product.stock,
        minimum_stock=product.minimum_stock,
        stock_status=get_stock_status(
            product.stock,
            product.minimum_stock,
        ),
        is_active=product.is_active,
    )


async def list_inventory(
    search: str | None = None,
    stock_status: str | None = None,
) -> list[InventoryResponse]:
    query: dict = {
        "is_active": True,
    }

    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"barcode": {"$regex": search, "$options": "i"}},
        ]

    products = await Product.find(query).to_list()

    result = [
        inventory_response(product)
        for product in products
    ]

    if stock_status:
        result = [
            item
            for item in result
            if item.stock_status == stock_status
        ]

    return result


async def get_inventory_product(
    product_id: str,
) -> InventoryResponse:
    object_id = validate_product_id(product_id)

    product = await Product.get(object_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product tidak ditemukan.",
        )

    return inventory_response(product)


async def list_stock_movements(
    product_id: str | None = None,
    movement_type: StockMovementType | None = None,
) -> list[StockMovementResponse]:
    query: dict = {}

    if product_id:
        query["productId"] = product_id

    if movement_type:
        query["type"] = movement_type.value

    movements = (
        await StockMovement
        .find(query)
        .sort("-createdAt")
        .to_list()
    )

    return [
        StockMovementResponse(
            id=str(movement.id),
            product_id=movement.productId,
            type=movement.type.value,
            quantity=movement.quantity,
            stock_before=movement.stockBefore,
            stock_after=movement.stockAfter,
            reference_type=movement.referenceType,
            reference_id=movement.referenceId,
            created_by=movement.createdBy,
            created_at=movement.createdAt,
        )
        for movement in movements
    ]


async def create_stock_adjustment(
    data: StockAdjustmentRequest,
    current_user: User,
) -> StockAdjustmentResponse:
    object_id = validate_product_id(data.product_id)

    if data.quantity == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity adjustment tidak boleh 0.",
        )

    product = await Product.get(object_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product tidak ditemukan.",
        )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product tidak aktif.",
        )

    stock_before = product.stock
    stock_after = stock_before + data.quantity

    if stock_after < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adjustment menyebabkan stok negatif.",
        )

    stock_filter = {
        "_id": object_id,
    }

    if data.quantity < 0:
        stock_filter["stock"] = {
            "$gte": -data.quantity,
        }

    update_result = await products_collection.update_one(
        stock_filter,
        {
            "$inc": {
                "stock": data.quantity,
            },
            "$set": {
                "updated_at": datetime.now(timezone.utc),
            },
        },
    )

    if update_result.modified_count != 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Stok berubah sebelum adjustment diproses. "
                "Silakan ulangi."
            ),
        )

    movement = StockMovement(
        productId=str(object_id),
        type=StockMovementType.ADJUSTMENT,
        quantity=data.quantity,
        stockBefore=stock_before,
        stockAfter=stock_after,
        referenceType="STOCK_ADJUSTMENT",
        createdBy=str(current_user.id),
    )

    await movement.insert()

    audit_event = InventoryAuditEvent(
        action="STOCK_ADJUSTMENT",
        productId=str(object_id),
        referenceType="STOCK_ADJUSTMENT",
        referenceId=str(movement.id),
        stockBefore=stock_before,
        stockAfter=stock_after,
        quantity=data.quantity,
        reason=data.reason,
        createdBy=str(current_user.id),
    )

    await audit_event.insert()

    return StockAdjustmentResponse(
        product_id=str(object_id),
        quantity=data.quantity,
        stock_before=stock_before,
        stock_after=stock_after,
        reason=data.reason,
        movement_id=str(movement.id),
    )


async def create_stock_opname(
    data: StockOpnameRequest,
    current_user: User,
) -> StockOpnameResponse:
    object_id = validate_product_id(data.product_id)

    product = await Product.get(object_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product tidak ditemukan.",
        )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product tidak aktif.",
        )

    system_stock = product.stock
    difference = data.physical_stock - system_stock

    movement_id: str | None = None

    if difference != 0:
        stock_filter = {
            "_id": object_id,
        }

        if difference < 0:
            stock_filter["stock"] = {
                "$gte": -difference,
            }

        update_result = await products_collection.update_one(
            stock_filter,
            {
                "$inc": {
                    "stock": difference,
                },
                "$set": {
                    "updated_at": datetime.now(timezone.utc),
                },
            },
        )

        if update_result.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Stok berubah sebelum opname diproses. "
                    "Silakan ulangi."
                ),
            )

        movement = StockMovement(
            productId=str(object_id),
            type=StockMovementType.STOCK_OPNAME,
            quantity=difference,
            stockBefore=system_stock,
            stockAfter=data.physical_stock,
            referenceType="STOCK_OPNAME",
            createdBy=str(current_user.id),
        )

        await movement.insert()

        movement_id = str(movement.id)

    audit_event = InventoryAuditEvent(
        action="STOCK_OPNAME",
        productId=str(object_id),
        referenceType="STOCK_OPNAME",
        referenceId=movement_id,
        stockBefore=system_stock,
        stockAfter=data.physical_stock,
        quantity=difference,
        reason=data.reason,
        createdBy=str(current_user.id),
    )

    await audit_event.insert()

    return StockOpnameResponse(
        product_id=str(object_id),
        system_stock=system_stock,
        physical_stock=data.physical_stock,
        difference=difference,
        reason=data.reason,
        movement_id=movement_id,
        audit_event_id=str(audit_event.id),
    )


async def list_stock_alerts() -> list[StockAlertResponse]:
    products = await Product.find(
        {
            "is_active": True,
            "$expr": {
                "$lte": [
                    "$stock",
                    "$minimum_stock",
                ]
            },
        }
    ).to_list()

    return [
        StockAlertResponse(
            product_id=str(product.id),
            sku=product.sku,
            name=product.name,
            stock=product.stock,
            minimum_stock=product.minimum_stock,
            status=(
                "OUT_OF_STOCK"
                if product.stock <= 0
                else "LOW_STOCK"
            ),
        )
        for product in products
    ]