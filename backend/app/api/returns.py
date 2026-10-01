from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.deps import ADMIN_PENGURUS, POS_OPERATORS, STAFF, client_ip, require_role
from app.core.utils import Pagination, PageParams
from app.models.returns import ReturnStatus, ReturnType
from app.models.user import User, UserRole
from app.schemas.returns import (
    PurchaseReturnCreate,
    ReturnRejectRequest,
    ReturnResponse,
    SalesReturnCreate,
)
from app.services.returns import (
    approve_return,
    build_return_responses,
    create_purchase_return,
    create_sales_return,
    get_return_or_404,
    list_returns,
    reject_return,
)


router = APIRouter(prefix="/api/returns", tags=["Returns"])


@router.get("", response_model=list[ReturnResponse])
async def get_returns(
    type: ReturnType | None = Query(default=None),
    status: ReturnStatus | None = Query(default=None),
    sale_id: str | None = Query(default=None, alias="saleId"),
    receipt_id: str | None = Query(default=None, alias="receiptId"),
    supplier_id: str | None = Query(default=None, alias="supplierId"),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    pagination: PageParams = Depends(Pagination(default_page_size=20)),
    current_user: User = Depends(require_role(*STAFF)),
):
    return await list_returns(
        current_user,
        pagination,
        return_type=type,
        status=status,
        sale_id=sale_id,
        receipt_id=receipt_id,
        supplier_id=supplier_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("/sales", response_model=ReturnResponse, status_code=201)
async def create_sales_return_endpoint(
    payload: SalesReturnCreate,
    request: Request,
    current_user: User = Depends(require_role(*POS_OPERATORS, UserRole.PENGURUS)),
):
    ret = await create_sales_return(payload, current_user, client_ip(request))
    return (await build_return_responses([ret]))[0]


@router.post("/purchases", response_model=ReturnResponse, status_code=201)
async def create_purchase_return_endpoint(
    payload: PurchaseReturnCreate,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN_PENGURUS)),
):
    ret = await create_purchase_return(payload, current_user, client_ip(request))
    return (await build_return_responses([ret]))[0]


@router.get("/{return_id}", response_model=ReturnResponse)
async def get_return(
    return_id: str,
    current_user: User = Depends(require_role(*STAFF)),
):
    ret = await get_return_or_404(return_id)
    if current_user.role == UserRole.KASIR and (
        ret.type != ReturnType.SALE or ret.createdBy != str(current_user.id)
    ):
        raise HTTPException(status_code=404, detail="Retur tidak ditemukan.")
    return (await build_return_responses([ret]))[0]


@router.post("/{return_id}/approve", response_model=ReturnResponse)
async def approve_return_endpoint(
    return_id: str,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN_PENGURUS)),
):
    ret = await approve_return(return_id, current_user, client_ip(request))
    return (await build_return_responses([ret]))[0]


@router.post("/{return_id}/reject", response_model=ReturnResponse)
async def reject_return_endpoint(
    return_id: str,
    payload: ReturnRejectRequest,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN_PENGURUS)),
):
    ret = await reject_return(return_id, payload.reason, current_user, client_ip(request))
    return (await build_return_responses([ret]))[0]
