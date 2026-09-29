from fastapi import APIRouter, Depends

from app.core.permissions import require_role
from app.models.user import User, UserRole
from app.schemas.sales import SaleCreate, SaleResponse, SaleCancelResponse
from app.services.sales import (
    create_sale,
    get_sale_detail,
    list_sales,
    cancel_sale,
)


router = APIRouter(
    prefix="/api/sales",
    tags=["Sales"],
)


sales_user = require_role(
    UserRole.ADMIN,
    UserRole.PENGURUS,
    UserRole.KASIR,
)


@router.post(
    "",
    response_model=SaleResponse,
    status_code=201,
)
async def create_sale_endpoint(
    payload: SaleCreate,
    current_user: User = Depends(
        require_role(UserRole.KASIR)
    ),
):
    return await create_sale(
        payload,
        current_user,
    )


@router.get(
    "",
    response_model=list[SaleResponse],
)
async def get_sales_endpoint(
    current_user: User = Depends(sales_user),
):
    return await list_sales(current_user)


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
)
async def get_sale_detail_endpoint(
    sale_id: str,
    current_user: User = Depends(sales_user),
):
    return await get_sale_detail(
        sale_id,
        current_user,
    )

@router.post(
    "/{sale_id}/cancel",
    response_model=SaleCancelResponse,
)
async def cancel_sale_endpoint(
    sale_id: str,
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.PENGURUS,
        )
    ),
):
    return await cancel_sale(
        sale_id,
        current_user,
    )