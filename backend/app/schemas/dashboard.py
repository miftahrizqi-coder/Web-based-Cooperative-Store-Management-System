from datetime import datetime

from pydantic import BaseModel


class DashboardSalesAnalyticsItem(BaseModel):
    date: str
    sales: float
    transactions: int


class DashboardAnalyticsResponse(BaseModel):
    sales_today: float
    transaction_count_today: int
    total_products: int
    total_members: int
    low_stock_count: int
    active_po_count: int
    supplier_payable: float
    overdue_invoice_count: int

    # Phase 6 (Expenses) belum dikerjakan.
    # Jangan mengarang nilai expense.
    expenses: float | None

    sales_analytics: list[DashboardSalesAnalyticsItem]

    generated_at: datetime