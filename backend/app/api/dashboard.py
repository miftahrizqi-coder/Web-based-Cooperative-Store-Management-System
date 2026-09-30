from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.permissions import require_role
from app.models.user import User, UserRole
from app.schemas.dashboard import DashboardAnalyticsResponse
from app.services.dashboard import get_dashboard_analytics


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