from datetime import datetime, timezone
from uuid import uuid4

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.database import client
from app.models.inventory import StockMovement, StockMovementType
from app.models.product import Product
from app.models.sales import Sale, SaleItem, SaleStatus
from app.models.user import User, UserRole
from app.schemas.sales import SaleCreate, SaleResponse, SaleCancelResponse


db = client[settings.mongodb_database]

products_collection = db["products"]
stock_movements_collection = db["stock_movements"]


def validate_product_id(product_id: str) -> ObjectId:
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product ID tidak valid: {product_id}",
        )

    return ObjectId(product_id)


def sale_response(sale: Sale) -> SaleResponse:
    return SaleResponse(
        id=str(sale.id),
        saleNumber=sale.saleNumber,
        memberId=sale.memberId,
        items=[
            {
                "productId": item.productId,
                "sku": item.sku,
                "name": item.name,
                "unit": item.unit,
                "quantity": item.quantity,
                "unitPrice": item.unitPrice,
                "subtotal": item.subtotal,
            }
            for item in sale.items
        ],
        subtotal=sale.subtotal,
        total=sale.total,
        paymentMethod=sale.paymentMethod,
        paidAmount=sale.paidAmount,
        changeAmount=sale.changeAmount,
        status=sale.status,
        createdBy=sale.createdBy,
        createdAt=sale.createdAt,
        updatedAt=sale.updatedAt,
    )


def generate_sale_number() -> str:
    now = datetime.now(timezone.utc)

    return (
        f"SALE-{now.strftime('%Y%m%d-%H%M%S')}-"
        f"{uuid4().hex[:6].upper()}"
    )


async def create_sale(
    data: SaleCreate,
    current_user: User,
) -> SaleResponse:
    if current_user.role != UserRole.KASIR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya Kasir yang dapat membuat transaksi penjualan.",
        )

    if not data.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimal satu produk harus dipilih.",
        )

    if data.paidAmount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jumlah pembayaran tidak boleh negatif.",
        )

    # Aggregate duplicate product IDs in the cart.
    requested_quantities: dict[str, float] = {}

    for item in data.items:
        product_object_id = validate_product_id(item.productId)

        product_id = str(product_object_id)

        requested_quantities[product_id] = (
            requested_quantities.get(product_id, 0)
            + item.quantity
        )

    product_ids = list(requested_quantities.keys())

    object_ids = [
        ObjectId(product_id)
        for product_id in product_ids
    ]

    products = await Product.find(
        {
            "_id": {
                "$in": object_ids,
            },
        }
    ).to_list()

    product_map = {
        str(product.id): product
        for product in products
    }

    # Validate all products before starting the transaction.
    for product_id in product_ids:
        product = product_map.get(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} tidak ditemukan.",
            )

        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Product {product.name} tidak aktif."
                ),
            )

        requested_quantity = requested_quantities[product_id]

        if product.stock < requested_quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Stok {product.name} tidak mencukupi. "
                    f"Stok tersedia: {product.stock}, "
                    f"diminta: {requested_quantity}."
                ),
            )

    sale_items: list[SaleItem] = []
    subtotal = 0.0

    for product_id in product_ids:
        product = product_map[product_id]
        quantity = requested_quantities[product_id]

        unit_price = float(product.selling_price)
        item_subtotal = quantity * unit_price

        sale_items.append(
            SaleItem(
                productId=product_id,
                sku=product.sku,
                name=product.name,
                unit=product.unit,
                quantity=quantity,
                unitPrice=unit_price,
                subtotal=item_subtotal,
            )
        )

        subtotal += item_subtotal

    total = subtotal

    if data.paidAmount < total:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Pembayaran tidak mencukupi. "
                f"Total: {total}, "
                f"dibayar: {data.paidAmount}."
            ),
        )

    change_amount = data.paidAmount - total

    sale_id: str | None = None

    async with client.start_session() as session:
        async with await session.start_transaction():
            now = datetime.now(timezone.utc)

            for item in sale_items:
                object_id = ObjectId(item.productId)

                update_result = await products_collection.update_one(
                    {
                        "_id": object_id,
                        "is_active": True,
                        "stock": {
                            "$gte": item.quantity,
                        },
                    },
                    {
                        "$inc": {
                            "stock": -item.quantity,
                        },
                        "$set": {
                            "updated_at": now,
                        },
                    },
                    session=session,
                )

                if update_result.modified_count != 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            f"Stok product {item.name} berubah "
                            "sebelum transaksi diproses. "
                            "Silakan ulangi transaksi."
                        ),
                    )

        # lanjutkan kode Sale dan StockMovement

            # The first validation read is safe for normal flow,
            # but stockBefore must reflect the actual value before
            # this transaction's decrement.
            #
            # Reconstruct it from the originally validated product
            # snapshot plus the requested quantity.
            stock_before_map = {
                product_id: product_map[product_id].stock
                for product_id in product_ids
            }

            sale = Sale(
                saleNumber=generate_sale_number(),
                memberId=data.memberId,
                items=sale_items,
                subtotal=subtotal,
                total=total,
                paymentMethod=data.paymentMethod,
                paidAmount=data.paidAmount,
                changeAmount=change_amount,
                status=SaleStatus.PAID,
                createdBy=str(current_user.id),
                createdAt=now,
                updatedAt=now,
            )

            await sale.insert(
                session=session,
            )

            sale_id = str(sale.id)

            for item in sale_items:
                stock_before = stock_before_map[item.productId]
                stock_after = (
                    stock_before - item.quantity
                )

                movement = StockMovement(
                    productId=item.productId,
                    type=StockMovementType.SALE,
                    quantity=item.quantity,
                    stockBefore=stock_before,
                    stockAfter=stock_after,
                    referenceType="SALE",
                    referenceId=str(sale.id),
                    createdBy=str(current_user.id),
                    createdAt=now,
                )

                await movement.insert(
                    session=session,
                )

    if not sale_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaksi penjualan gagal dibuat.",
        )

    saved_sale = await Sale.get(
        ObjectId(sale_id)
    )

    if not saved_sale:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaksi berhasil diproses tetapi detail tidak ditemukan.",
        )

    return sale_response(saved_sale)

async def list_sales(
    current_user: User,
) -> list[SaleResponse]:
    if current_user.role == UserRole.KASIR:
        sales = await Sale.find(
            {
                "createdBy": str(current_user.id),
            }
        ).sort(
            "-createdAt"
        ).to_list()

    elif current_user.role in {
        UserRole.ADMIN,
        UserRole.PENGURUS,
    }:
        sales = await Sale.find().sort(
            "-createdAt"
        ).to_list()

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses ke riwayat penjualan.",
        )

    return [
        sale_response(sale)
        for sale in sales
    ]


async def get_sale_detail(
    sale_id: str,
    current_user: User,
) -> SaleResponse:
    if not ObjectId.is_valid(sale_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sale ID tidak valid.",
        )

    sale = await Sale.get(
        ObjectId(sale_id)
    )

    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi penjualan tidak ditemukan.",
        )

    if (
        current_user.role == UserRole.KASIR
        and sale.createdBy != str(current_user.id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kasir hanya dapat melihat transaksi yang dibuat sendiri.",
        )

    if current_user.role not in {
        UserRole.ADMIN,
        UserRole.PENGURUS,
        UserRole.KASIR,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses ke detail penjualan.",
        )

    return sale_response(sale)

async def cancel_sale(
    sale_id: str,
    current_user: User,
) -> SaleCancelResponse:
    if current_user.role not in {
        UserRole.ADMIN,
        UserRole.PENGURUS,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses untuk membatalkan transaksi.",
        )

    if not ObjectId.is_valid(sale_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sale ID tidak valid.",
        )

    sale = await Sale.get(
        ObjectId(sale_id)
    )

    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi penjualan tidak ditemukan.",
        )

    if sale.status == SaleStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaksi sudah dibatalkan.",
        )

    now = datetime.now(timezone.utc)

    restored_stock: list[dict] = []

    async with client.start_session() as session:
        async with await session.start_transaction():
            for item in sale.items:
                product = await Product.get(
                    ObjectId(item.productId),
                    session=session,
                )

                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=(
                            f"Product {item.productId} "
                            "tidak ditemukan."
                        ),
                    )

                stock_before = product.stock
                stock_after = (
                    stock_before + item.quantity
                )

                update_result = await products_collection.update_one(
                    {
                        "_id": ObjectId(item.productId),
                    },
                    {
                        "$inc": {
                            "stock": item.quantity,
                        },
                        "$set": {
                            "updated_at": now,
                        },
                    },
                    session=session,
                )

                if update_result.modified_count != 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            f"Gagal mengembalikan stok "
                            f"product {item.name}."
                        ),
                    )

                movement = StockMovement(
                    productId=item.productId,
                    type=StockMovementType.SALE_RETURN,
                    quantity=item.quantity,
                    stockBefore=stock_before,
                    stockAfter=stock_after,
                    referenceType="SALE",
                    referenceId=str(sale.id),
                    createdBy=str(current_user.id),
                    createdAt=now,
                )

                await movement.insert(
                    session=session,
                )

                restored_stock.append(
                    {
                        "productId": item.productId,
                        "sku": item.sku,
                        "name": item.name,
                        "quantity": item.quantity,
                        "stockBefore": stock_before,
                        "stockAfter": stock_after,
                    }
                )

            sale.status = SaleStatus.CANCELLED
            sale.updatedAt = now

            await sale.save(
                session=session,
            )

    return SaleCancelResponse(
        id=str(sale.id),
        saleNumber=sale.saleNumber,
        status=sale.status,
        restoredStock=restored_stock,
        updatedAt=sale.updatedAt,
    )