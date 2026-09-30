from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.permissions import require_role
from app.models.category import Category
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryStatusUpdate,
    CategoryUpdate,
)

router = APIRouter(prefix="/api/categories", tags=["Categories"])

admin_required = require_role(UserRole.ADMIN)
admin_pengurus = require_role(UserRole.ADMIN, UserRole.PENGURUS)


def to_response(category: Category) -> CategoryResponse:
    return CategoryResponse(
        id=str(category.id),
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.get("", response_model=list[CategoryResponse])
async def get_categories(
    is_active: bool | None = Query(default=None),
    current_user: User = Depends(admin_pengurus),
):
    filters = {}

    if is_active is not None:
        filters["is_active"] = is_active

    categories = await Category.find(filters).sort("+name").to_list()

    return [to_response(category) for category in categories]


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str,
    current_user: User = Depends(admin_pengurus),
):
    category = await Category.get(category_id)

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category tidak ditemukan.",
        )

    return to_response(category)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=201,
)
async def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(admin_required),
):
    existing = await Category.find_one(
        {"name": payload.name.strip()}
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Category dengan nama tersebut sudah ada.",
        )

    now = datetime.now(timezone.utc)

    category = Category(
        name=payload.name.strip(),
        description=payload.description,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    await category.insert()

    return to_response(category)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
)
async def update_category(
    category_id: str,
    payload: CategoryUpdate,
    current_user: User = Depends(admin_required),
):
    category = await Category.get(category_id)

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category tidak ditemukan.",
        )

    existing = await Category.find_one(
        {
            "name": payload.name.strip(),
            "_id": {"$ne": category.id},
        }
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Category dengan nama tersebut sudah ada.",
        )

    category.name = payload.name.strip()
    category.description = payload.description
    category.updated_at = datetime.now(timezone.utc)

    await category.save()

    return to_response(category)


@router.patch(
    "/{category_id}/status",
    response_model=CategoryResponse,
)
async def update_category_status(
    category_id: str,
    payload: CategoryStatusUpdate,
    current_user: User = Depends(admin_required),
):
    category = await Category.get(category_id)

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category tidak ditemukan.",
        )

    category.is_active = payload.is_active
    category.updated_at = datetime.now(timezone.utc)

    await category.save()

    return to_response(category)


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    current_user: User = Depends(admin_required),
):
    category = await Category.get(category_id)

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category tidak ditemukan.",
        )

    product_exists = await Product.find_one(
        {"category_id": str(category.id)}
    )

    if product_exists:
        raise HTTPException(
            status_code=409,
            detail=(
                "Category sudah digunakan oleh Product "
                "dan tidak dapat dihapus. "
                "Nonaktifkan Category sebagai gantinya."
            ),
        )

    await category.delete()

    return {"message": "Category berhasil dihapus."}