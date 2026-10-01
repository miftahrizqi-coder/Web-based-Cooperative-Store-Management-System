from datetime import date

from fastapi import APIRouter, Depends, Query, Request

from app.core.deps import ADMIN_PENGURUS, client_ip, require_role
from app.core.utils import Pagination, PageParams
from app.models.inventory import StockMovementType
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
from app.services.inventory import (
    create_stock_adjustment,
    create_stock_opname,
    get_inventory_product,
    get_stock_opname,
    list_inventory,
    list_stock_alerts,
    list_stock_movements,
    list_stock_opnames,
)


router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

# PRD §6: Kasir tidak boleh mengubah stok manual. Pengurus melihat stok &
# melakukan stock opname; Admin akses penuh.
inventory_user = require_role(*ADMIN_PENGURUS)


@router.get("", response_model=list[InventoryResponse])
async def get_inventory(
    search: str | None = Query(default=None),
    stock_status: str | None = Query(
        default=None,
        alias="stockStatus",
        pattern="^(AVAILABLE|LOW_STOCK|OUT_OF_STOCK)$",
    ),
    category_id: str | None = Query(default=None, alias="categoryId"),
    pagination: PageParams = Depends(Pagination()),
    current_user: User = Depends(inventory_user),
):
    return await list_inventory(pagination, search, stock_status, category_id)


@router.get("/alerts", response_model=list[StockAlertResponse])
async def get_inventory_alerts(current_user: User = Depends(inventory_user)):
    return await list_stock_alerts()


@router.get("/movements", response_model=list[StockMovementResponse])
async def get_stock_movements(
    product_id: str | None = Query(default=None, alias="productId"),
    movement_type: StockMovementType | None = Query(default=None, alias="type"),
    reference_id: str | None = Query(default=None, alias="referenceId"),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    pagination: PageParams = Depends(Pagination(default_page_size=50)),
    current_user: User = Depends(inventory_user),
):
    return await list_stock_movements(
        pagination, product_id, movement_type, reference_id, date_from, date_to
    )


@router.post("/adjustment", response_model=StockAdjustmentResponse, status_code=201)
async def create_adjustment(
    payload: StockAdjustmentRequest,
    request: Request,
    current_user: User = Depends(inventory_user),
):
    return await create_stock_adjustment(payload, current_user, client_ip(request))


@router.post("/stock-opname", response_model=StockOpnameResponse, status_code=201)
async def create_opname(
    payload: StockOpnameRequest,
    request: Request,
    current_user: User = Depends(inventory_user),
):
    return await create_stock_opname(payload, current_user, client_ip(request))


@router.get("/stock-opname", response_model=list[StockOpnameResponse])
async def get_opnames(
    pagination: PageParams = Depends(Pagination(default_page_size=20)),
    current_user: User = Depends(inventory_user),
):
    return await list_stock_opnames(pagination)


@router.get("/stock-opname/{opname_id}", response_model=StockOpnameResponse)
async def get_opname(opname_id: str, current_user: User = Depends(inventory_user)):
    return await get_stock_opname(opname_id)


# Didefinisikan terakhir agar tidak menangkap path statis di atas.
@router.get("/{product_id}", response_model=InventoryResponse)
async def get_inventory_detail(product_id: str, current_user: User = Depends(inventory_user)):
    return await get_inventory_product(product_id)
