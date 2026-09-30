from datetime import date

from pydantic import BaseModel


class SalesReportResponse(BaseModel):
    start_date: date
    end_date: date

    total_transactions: int
    total_items_sold: float
    total_sales: float
    discount: float
    revenue: float