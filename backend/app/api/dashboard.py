from fastapi import APIRouter, Depends

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
    current_user: User = Depends(reports_user),
):
    return await get_dashboard_analytics()