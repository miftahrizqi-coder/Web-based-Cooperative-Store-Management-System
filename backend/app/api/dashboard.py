from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from app.core.permissions import require_role
from app.models.user import User, UserRole
from app.schemas.dashboard import DashboardAnalyticsResponse
from app.services.dashboard import get_dashboard_analytics
from app.schemas.sales_report import SalesReportResponse
from app.services.sales_report import get_sales_report


router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
)


reports_user = require_role(
    UserRole.ADMIN,
    UserRole.PENGURUS,
)


@router.get(
    "/dashboard",
    response_model=DashboardAnalyticsResponse,
)
async def get_dashboard_report(
    days: int = Query(
        default=7,
        description="Rentang analytics penjualan: 7 atau 30 hari.",
    ),
    current_user: User = Depends(reports_user),
):
    if days not in (7, 30):
        raise HTTPException(
            status_code=400,
            detail="Parameter days harus 7 atau 30.",
        )

    return await get_dashboard_analytics(days=days)

@router.get(
    "/sales",
    response_model=SalesReportResponse,
)
async def get_sales_report_endpoint(
    start_date: date | None = Query(
        default=None,
        description="Tanggal awal laporan. Default hari ini.",
    ),
    end_date: date | None = Query(
        default=None,
        description="Tanggal akhir laporan. Default hari ini.",
    ),
    cashier_id: str | None = Query(
        default=None,
        description="Filter berdasarkan ID kasir.",
    ),
    product_id: str | None = Query(
        default=None,
        description="Filter berdasarkan ID produk.",
    ),
    category_id: str | None = Query(
        default=None,
        description="Filter berdasarkan ID kategori.",
    ),
    member_id: str | None = Query(
        default=None,
        description="Filter berdasarkan ID anggota.",
    ),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.PENGURUS,
        )
    ),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date tidak boleh lebih besar dari end_date.",
        )

    try:
        return await get_sales_report(
            start_date=start_date,
            end_date=end_date,
            cashier_id=cashier_id,
            product_id=product_id,
            category_id=category_id,
            member_id=member_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc