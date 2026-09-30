from datetime import date, datetime, time, timedelta, timezone

from app.core.database import client
from app.core.config import settings
from app.models.product import Product
from app.models.sales import Sale, SaleStatus
from app.schemas.sales_report import SalesReportResponse


db = client[settings.mongodb_database]


async def get_sales_report(
    start_date: date | None = None,
    end_date: date | None = None,
    cashier_id: str | None = None,
    product_id: str | None = None,
    category_id: str | None = None,
    member_id: str | None = None,
) -> SalesReportResponse:
    """
    Generate Sales Report.

    Default period:
    - today

    Business rules:
    - only PAID sales are counted
    - CANCELLED sales are excluded
    - total_sales uses Sale.total
    - discount is currently 0 because Sale has no discount field
    - revenue equals total_sales
    """

    now = datetime.now(timezone.utc)
    today = now.date()

    if start_date is None:
        start_date = today

    if end_date is None:
        end_date = today

    if start_date > end_date:
        raise ValueError(
            "start_date tidak boleh lebih besar dari end_date."
        )

    start_datetime = datetime.combine(
        start_date,
        time.min,
        tzinfo=timezone.utc,
    )

    end_datetime = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
        tzinfo=timezone.utc,
    )

    sale_filter: dict = {
        "status": SaleStatus.PAID.value,
        "createdAt": {
            "$gte": start_datetime,
            "$lt": end_datetime,
        },
    }

    if cashier_id:
        sale_filter["createdBy"] = cashier_id

    if member_id:
        sale_filter["memberId"] = member_id

    # ---------------------------------------------------------
    # Product / Category filter
    #
    # Jika product_id atau category_id digunakan,
    # cari product yang memenuhi filter terlebih dahulu.
    # ---------------------------------------------------------
    product_ids: list[str] | None = None

    if product_id:
        product_ids = [product_id]

    if category_id:
        category_products = await Product.find(
            {
                "category_id": category_id,
                "is_active": True,
            }
        ).to_list()

        category_product_ids = [
            str(product.id)
            for product in category_products
        ]

        if product_ids is None:
            product_ids = category_product_ids
        else:
            product_ids = [
                value
                for value in product_ids
                if value in category_product_ids
            ]

    sales = await Sale.find(sale_filter).to_list()

    total_transactions = len(sales)
    total_items_sold = 0.0
    total_sales = 0.0

    for sale in sales:
        # Tanpa product/category filter,
        # seluruh item transaksi dihitung.
        if product_ids is None:
            total_items_sold += sum(
                float(item.quantity)
                for item in sale.items
            )

            total_sales += float(sale.total)
            continue

        # Dengan product/category filter,
        # hanya item yang cocok yang dihitung.
        matching_items = [
            item
            for item in sale.items
            if item.productId in product_ids
        ]

        if not matching_items:
            continue

        total_items_sold += sum(
            float(item.quantity)
            for item in matching_items
        )

        total_sales += sum(
            float(item.subtotal)
            for item in matching_items
        )

    # ---------------------------------------------------------
    # Jika filter product/category aktif, transaksi yang tidak
    # memiliki item cocok tidak termasuk dalam jumlah transaksi.
    # ---------------------------------------------------------
    if product_ids is not None:
        total_transactions = sum(
            1
            for sale in sales
            if any(
                item.productId in product_ids
                for item in sale.items
            )
        )

    discount = 0.0
    revenue = total_sales

    return SalesReportResponse(
        start_date=start_date,
        end_date=end_date,
        total_transactions=total_transactions,
        total_items_sold=total_items_sold,
        total_sales=total_sales,
        discount=discount,
        revenue=revenue,
    )