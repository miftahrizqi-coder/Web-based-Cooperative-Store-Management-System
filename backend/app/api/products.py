from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.permissions import require_role
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.product import (
    ProductCreateRequest,
    ProductResponse,
    ProductUpdateRequest,
)


router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
)


def to_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=str(product.id),
        sku=product.sku,
        barcode=product.barcode,
        name=product.name,
        category_id=product.category_id,
        unit=product.unit,
        purchase_price=product.purchase_price,
        selling_price=product.selling_price,
        stock=product.stock,
        minimum_stock=product.minimum_stock,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


async def ensure_unique_product_identifiers(
    sku: str,
    barcode: str | None,
    exclude_id: ObjectId | None = None,
) -> None:
    sku_query = {"sku": sku}

    if exclude_id is not None:
        sku_query["_id"] = {"$ne": exclude_id}

    if await Product.find_one(sku_query):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SKU sudah digunakan.",
        )

    if barcode:
        barcode_query = {"barcode": barcode}

        if exclude_id is not None:
            barcode_query["_id"] = {"$ne": exclude_id}

        if await Product.find_one(barcode_query):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Barcode sudah digunakan.",
            )


@router.get("", response_model=list[ProductResponse])
async def list_products(
    search: str | None = Query(default=None),
    category_id: str | None = Query(default=None),
    stock_status: str | None = Query(
        default=None,
        pattern="^(all|available|low|out)$",
    ),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    query: dict = {}

    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"barcode": {"$regex": search, "$options": "i"}},
        ]

    if category_id:
        query["category_id"] = category_id

    if stock_status == "available":
        query["stock"] = {"$gt": 0}
    elif stock_status == "low":
        query["$expr"] = {
            "$and": [
                {"$gt": ["$stock", 0]},
                {"$lte": ["$stock", "$minimum_stock"]},
            ]
        }
    elif stock_status == "out":
        query["stock"] = 0

    products = await Product.find(query).to_list()

    return [to_response(product) for product in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID produk tidak valid.",
        )

    product = await Product.get(ObjectId(product_id))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produk tidak ditemukan.",
        )

    return to_response(product)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    data: ProductCreateRequest,
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    await ensure_unique_product_identifiers(
        sku=data.sku,
        barcode=data.barcode,
    )

    now = datetime.now(timezone.utc)

    product = Product(
        sku=data.sku,
        barcode=data.barcode,
        name=data.name,
        category_id=data.category_id,
        unit=data.unit,
        purchase_price=data.purchase_price,
        selling_price=data.selling_price,
        stock=data.stock,
        minimum_stock=data.minimum_stock,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    await product.insert()

    return to_response(product)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
async def update_product(
    product_id: str,
    data: ProductUpdateRequest,
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID produk tidak valid.",
        )

    product = await Product.get(ObjectId(product_id))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produk tidak ditemukan.",
        )

    await ensure_unique_product_identifiers(
        sku=data.sku,
        barcode=data.barcode,
        exclude_id=product.id,
    )

    product.sku = data.sku
    product.barcode = data.barcode
    product.name = data.name
    product.category_id = data.category_id
    product.unit = data.unit
    product.purchase_price = data.purchase_price
    product.selling_price = data.selling_price
    product.stock = data.stock
    product.minimum_stock = data.minimum_stock
    product.is_active = data.is_active
    product.updated_at = datetime.now(timezone.utc)

    await product.save()

    return to_response(product)


@router.delete(
    "/{product_id}",
    response_model=ProductResponse,
)
async def deactivate_product(
    product_id: str,
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID produk tidak valid.",
        )

    product = await Product.get(ObjectId(product_id))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produk tidak ditemukan.",
        )

    product.is_active = False
    product.updated_at = datetime.now(timezone.utc)

    await product.save()

    return to_response(product)
