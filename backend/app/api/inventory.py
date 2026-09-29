from fastapi import APIRouter, Depends, Query

from app.api.auth import get_current_user
from app.core.permissions import require_role
from app.models.inventory import StockMovementType
from app.models.user import User, UserRole
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
    list_inventory,
    list_stock_alerts,
    list_stock_movements,
)


router = APIRouter(
    prefix="/api/inventory",
    tags=["Inventory"],
)


inventory_user = require_role(
    UserRole.ADMIN,
    UserRole.PENGURUS,
)


@router.get(
    "",
    response_model=list[InventoryResponse],
)
async def get_inventory(
    search: str | None = Query(default=None),
    stock_status: str | None = Query(
        default=None,
        pattern="^(AVAILABLE|LOW_STOCK|OUT_OF_STOCK)$",
    ),
    current_user: User = Depends(inventory_user),
):
    return await list_inventory(
        search=search,
        stock_status=stock_status,
    )


@router.get(
    "/alerts",
    response_model=list[StockAlertResponse],
)
async def get_inventory_alerts(
    current_user: User = Depends(inventory_user),
):
    return await list_stock_alerts()


@router.get(
    "/movements",
    response_model=list[StockMovementResponse],
)
async def get_stock_movements(
    product_id: str | None = Query(default=None),
    movement_type: StockMovementType | None = Query(default=None),
    current_user: User = Depends(inventory_user),
):
    return await list_stock_movements(
        product_id=product_id,
        movement_type=movement_type,
    )


@router.get(
    "/{product_id}",
    response_model=InventoryResponse,
)
async def get_inventory_detail(
    product_id: str,
    current_user: User = Depends(inventory_user),
):
    return await get_inventory_product(product_id)


@router.post(
    "/adjustment",
    response_model=StockAdjustmentResponse,
    status_code=201,
)
async def create_adjustment(
    payload: StockAdjustmentRequest,
    current_user: User = Depends(inventory_user),
):
    return await create_stock_adjustment(
        payload,
        current_user,
    )


@router.post(
    "/stock-opname",
    response_model=StockOpnameResponse,
    status_code=201,
)
async def create_opname(
    payload: StockOpnameRequest,
    current_user: User = Depends(inventory_user),
):
    return await create_stock_opname(
        payload,
        current_user,
    )