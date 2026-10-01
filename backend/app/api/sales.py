from datetime import date

from fastapi import APIRouter, Depends, Query, Request

from app.core.deps import ADMIN_PENGURUS, POS_OPERATORS, STAFF, client_ip, require_role
from app.core.utils import Pagination, PageParams
from app.models.sales import SaleStatus
from app.models.user import User
from app.schemas.sales import SaleCancelRequest, SaleCancelResponse, SaleCreate, SaleResponse
from app.services.sales import (
    cancel_sale,
    create_sale,
    get_sale_by_invoice,
    get_sale_detail,
    list_sales,
)


router = APIRouter(prefix="/api/sales", tags=["Sales"])


@router.post("", response_model=SaleResponse, status_code=201)
async def create_sale_endpoint(
    payload: SaleCreate,
    request: Request,
    current_user: User = Depends(require_role(*POS_OPERATORS)),
):
    return await create_sale(payload, current_user, client_ip(request))


@router.get("", response_model=list[SaleResponse])
async def get_sales_endpoint(
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    status: SaleStatus | None = Query(default=None),
    cashier_id: str | None = Query(default=None, alias="cashierId"),
    member_id: str | None = Query(default=None, alias="memberId"),
    search: str | None = Query(default=None),
    pagination: PageParams = Depends(Pagination(default_page_size=20)),
    current_user: User = Depends(require_role(*STAFF)),
):
    return await list_sales(
        current_user,
        pagination,
        date_from=date_from,
        date_to=date_to,
        status_filter=status,
        cashier_id=cashier_id,
        member_id=member_id,
        search=search,
    )


@router.get("/invoice/{invoice_number}", response_model=SaleResponse)
async def get_sale_by_invoice_endpoint(
    invoice_number: str,
    current_user: User = Depends(require_role(*STAFF)),
):
    return await get_sale_by_invoice(invoice_number, current_user)


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale_detail_endpoint(
    sale_id: str,
    current_user: User = Depends(require_role(*STAFF)),
):
    return await get_sale_detail(sale_id, current_user)


@router.post("/{sale_id}/cancel", response_model=SaleCancelResponse)
async def cancel_sale_endpoint(
    sale_id: str,
    request: Request,
    payload: SaleCancelRequest | None = None,
    current_user: User = Depends(require_role(*ADMIN_PENGURUS)),
):
    """Transaksi tidak pernah dihapus; hanya dibatalkan (BR-07)."""
    return await cancel_sale(
        sale_id,
        current_user,
        reason=payload.reason if payload else None,
        ip_address=client_ip(request),
    )
