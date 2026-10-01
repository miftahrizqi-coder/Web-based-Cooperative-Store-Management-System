from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.core.deps import ADMIN, STAFF, client_ip, require_role
from app.core.utils import parse_object_id, search_regex, utc_now
from app.models.audit_log import AuditAction, AuditModule
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.services.audit import log_audit


router = APIRouter(prefix="/api/categories", tags=["Categories"])


class CategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    isActive: bool = True


class CategoryResponse(BaseModel):
    id: str
    name: str
    description: str | None
    isActive: bool
    productCount: int = 0
    createdAt: datetime
    updatedAt: datetime


def to_response(category: Category, product_count: int = 0) -> CategoryResponse:
    return CategoryResponse(
        id=str(category.id),
        name=category.name,
        description=category.description,
        isActive=category.isActive,
        productCount=product_count,
        createdAt=category.createdAt,
        updatedAt=category.updatedAt,
    )


async def get_category_or_404(category_id: str) -> Category:
    category = await Category.get(parse_object_id(category_id, "ID kategori"))
    if category is None:
        raise HTTPException(status_code=404, detail="Kategori tidak ditemukan.")
    return category


async def ensure_unique_name(name: str, exclude_id=None) -> None:
    query: dict = {"name": {"$regex": f"^{search_regex(name)['$regex']}$", "$options": "i"}}
    if exclude_id is not None:
        query["_id"] = {"$ne": exclude_id}
    if await Category.find_one(query):
        raise HTTPException(status_code=409, detail="Nama kategori sudah digunakan.")


async def product_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    async for doc in Product.get_pymongo_collection().find(
        {"isActive": True}, {"categoryId": 1}
    ):
        key = doc.get("categoryId")
        if key:
            counts[key] = counts.get(key, 0) + 1
    return counts


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None, alias="isActive"),
    current_user: User = Depends(require_role(*STAFF)),
):
    query: dict = {}
    if search and search.strip():
        query["name"] = search_regex(search)
    if is_active is not None:
        query["isActive"] = is_active

    categories = await Category.find(query).sort("name").to_list()
    counts = await product_counts()
    return [to_response(c, counts.get(str(c.id), 0)) for c in categories]


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str,
    current_user: User = Depends(require_role(*STAFF)),
):
    category = await get_category_or_404(category_id)
    count = await Product.find({"categoryId": category_id, "isActive": True}).count()
    return to_response(category, count)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryRequest,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN)),
):
    name = payload.name.strip()
    await ensure_unique_name(name)

    category = Category(
        name=name,
        description=payload.description,
        isActive=payload.isActive,
    )
    await category.insert()

    await log_audit(
        action=AuditAction.CREATE,
        module=AuditModule.CATEGORY,
        description=f"Membuat kategori {category.name}",
        user=current_user,
        reference_id=str(category.id),
        ip_address=client_ip(request),
    )
    return to_response(category)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    payload: CategoryRequest,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN)),
):
    category = await get_category_or_404(category_id)
    name = payload.name.strip()
    await ensure_unique_name(name, category.id)

    category.name = name
    category.description = payload.description
    category.isActive = payload.isActive
    category.updatedAt = utc_now()
    await category.save()

    await log_audit(
        action=AuditAction.UPDATE,
        module=AuditModule.CATEGORY,
        description=f"Mengubah kategori {category.name}",
        user=current_user,
        reference_id=str(category.id),
        ip_address=client_ip(request),
    )
    return to_response(category)


@router.delete("/{category_id}", response_model=CategoryResponse)
async def deactivate_category(
    category_id: str,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN)),
):
    """Kategori dinonaktifkan (bukan dihapus) karena direferensikan produk."""
    category = await get_category_or_404(category_id)
    category.isActive = False
    category.updatedAt = utc_now()
    await category.save()

    await log_audit(
        action=AuditAction.DELETE,
        module=AuditModule.CATEGORY,
        description=f"Menonaktifkan kategori {category.name}",
        user=current_user,
        reference_id=str(category.id),
        ip_address=client_ip(request),
    )
    return to_response(category)
