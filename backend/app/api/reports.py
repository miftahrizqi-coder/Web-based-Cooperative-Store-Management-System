from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.deps import ADMIN_PENGURUS, STAFF, require_role
from app.models.user import User
from app.services import reports


router = APIRouter(prefix="/api/reports", tags=["Reports"])

# PRD §6.3: Pengurus melihat laporan; Admin akses penuh.
report_viewer = require_role(*ADMIN_PENGURUS)

GROUP_BY = Query(default="day", pattern="^(day|week|month)$", alias="groupBy")


@router.get("/dashboard")
async def dashboard_report(current_user: User = Depends(require_role(*STAFF))):
    """Admin/Pengurus: dashboard lengkap. Kasir: ringkasan penjualan miliknya."""
    return await reports.dashboard(current_user)


@router.get("/sales")
async def sales_report(
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    group_by: str = GROUP_BY,
    cashier_id: str | None = Query(default=None, alias="cashierId"),
    product_id: str | None = Query(default=None, alias="productId"),
    category_id: str | None = Query(default=None, alias="categoryId"),
    member_id: str | None = Query(default=None, alias="memberId"),
    current_user: User = Depends(report_viewer),
):
    return await reports.sales_report(
        date_from, date_to, group_by, cashier_id, product_id, category_id, member_id
    )


@router.get("/purchases")
async def purchases_report(
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    group_by: str = Query(default="month", pattern="^(day|week|month)$", alias="groupBy"),
    supplier_id: str | None = Query(default=None, alias="supplierId"),
    current_user: User = Depends(report_viewer),
):
    return await reports.purchases_report(date_from, date_to, group_by, supplier_id)


@router.get("/inventory")
async def inventory_report(
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    category_id: str | None = Query(default=None, alias="categoryId"),
    current_user: User = Depends(report_viewer),
):
    return await reports.inventory_report(date_from, date_to, category_id)


@router.get("/suppliers")
async def suppliers_report(current_user: User = Depends(report_viewer)):
    return await reports.suppliers_report()


@router.get("/payables")
async def payables_report(
    supplier_id: str | None = Query(default=None, alias="supplierId"),
    outstanding_only: bool = Query(default=False, alias="outstandingOnly"),
    current_user: User = Depends(report_viewer),
):
    return await reports.payables_report(supplier_id, outstanding_only)


@router.get("/profit")
async def profit_report(
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    group_by: str = Query(default="month", pattern="^(day|week|month)$", alias="groupBy"),
    current_user: User = Depends(report_viewer),
):
    return await reports.profit_report(date_from, date_to, group_by)
