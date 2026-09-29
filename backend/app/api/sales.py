from fastapi import APIRouter, Depends

from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.schemas.sales import SaleCreate, SaleResponse
from app.services.sales import create_sale
from app.core.permissions import require_role


router = APIRouter(
    prefix="/api/sales",
    tags=["Sales"],
)


sales_user = require_role(
    UserRole.KASIR,
)


@router.post(
    "",
    response_model=SaleResponse,
    status_code=201,
)
async def create_sale_endpoint(
    payload: SaleCreate,
    current_user: User = Depends(sales_user),
):
    return await create_sale(
        payload,
        current_user,
    )