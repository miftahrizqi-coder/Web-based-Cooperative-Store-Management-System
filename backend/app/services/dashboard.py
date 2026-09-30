from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.database import client
from app.models.member import Member
from app.models.product import Product
from app.models.procurement import (
    POStatus,
    PaymentStatus,
    SupplierInvoice,
)
from app.models.sales import Sale, SaleStatus
from app.schemas.dashboard import (
    DashboardAnalyticsResponse,
    DashboardSalesAnalyticsItem,
    DashboardBestSellingProduct,
)


db = client[settings.mongodb_database]

supplier_invoices_collection = db["supplier_invoices"]
supplier_payments_collection = db["supplier_payments"]


ACTIVE_PO_STATUSES = [
    POStatus.PENDING_APPROVAL.value,
    POStatus.APPROVED.value,
    POStatus.ORDERED.value,
    POStatus.PARTIALLY_RECEIVED.value,
]


async def get_dashboard_analytics(
    days: int = 7,
) -> DashboardAnalyticsResponse:
    now = datetime.now(timezone.utc)

    start_of_today = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    if days not in (7, 30):
        raise ValueError("days harus 7 atau 30.")

    # ---------------------------------------------------------
    # Sales hari ini
    # ---------------------------------------------------------
    sales_today_result = await Sale.find(
        {
            "status": SaleStatus.PAID,
            "createdAt": {
                "$gte": start_of_today,
                "$lt": now,
            },
        }
    ).to_list()

    sales_today = sum(
        sale.total
        for sale in sales_today_result
    )

    transaction_count_today = len(
        sales_today_result
    )

    # ---------------------------------------------------------
    # Sales Analytics
    #
    # Menampilkan total penjualan dan jumlah transaksi
    # per hari untuk periode 7 atau 30 hari.
    # Hanya transaksi PAID yang dihitung.
    # ---------------------------------------------------------
    analytics_start = (
        start_of_today
        - timedelta(days=days - 1)
    )

    sales_analytics_result = await Sale.find(
        {
            "status": SaleStatus.PAID,
            "createdAt": {
                "$gte": analytics_start,
                "$lt": now,
            },
        }
    ).to_list()

    analytics_by_date: dict[
        str,
        dict[str, float | int],
    ] = {}

    for sale in sales_analytics_result:
        sale_date = sale.createdAt.astimezone(
            timezone.utc
        ).date().isoformat()

        if sale_date not in analytics_by_date:
            analytics_by_date[sale_date] = {
                "sales": 0.0,
                "transactions": 0,
            }

        analytics_by_date[sale_date]["sales"] += float(
            sale.total
        )

        analytics_by_date[sale_date]["transactions"] += 1

    sales_analytics = []

    for index in range(days):
        current_date = (
            analytics_start
            + timedelta(days=index)
        ).date().isoformat()

        daily_data = analytics_by_date.get(
            current_date,
            {
                "sales": 0.0,
                "transactions": 0,
            },
        )

        sales_analytics.append(
            DashboardSalesAnalyticsItem(
                date=current_date,
                sales=float(daily_data["sales"]),
                transactions=int(
                    daily_data["transactions"]
                ),
            )
        )

    # ---------------------------------------------------------
    # Product aktif
    # ---------------------------------------------------------
    total_products = await Product.find(
        {
            "is_active": True,
        }
    ).count()

    # ---------------------------------------------------------
    # Member terdaftar
    # ---------------------------------------------------------
    total_members = await Member.find_all().count()

    # ---------------------------------------------------------
    # Low / Out of Stock
    # ---------------------------------------------------------
    low_stock_count = await Product.find(
        {
            "is_active": True,
            "$expr": {
                "$lte": [
                    "$stock",
                    "$minimum_stock",
                ]
            },
        }
    ).count()

    # ---------------------------------------------------------
    # Active Purchase Order
    # ---------------------------------------------------------
    active_po_count = await db["purchase_orders"].count_documents(
        {
            "status": {
                "$in": ACTIVE_PO_STATUSES,
            }
        }
    )

    # ---------------------------------------------------------
    # Supplier Payable
    #
    # Outstanding =
    # total invoice - seluruh pembayaran invoice
    # ---------------------------------------------------------
    payable_pipeline = [
        {
            "$match": {
                "paymentStatus": {
                    "$in": [
                        PaymentStatus.UNPAID.value,
                        PaymentStatus.PARTIALLY_PAID.value,
                        PaymentStatus.OVERDUE.value,
                    ]
                }
            }
        },
        {
            "$lookup": {
                "from": "supplier_payments",
                "let": {
                    "invoice_id": {
                        "$toString": "$_id",
                    },
                },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$eq": [
                                    "$invoiceId",
                                    "$$invoice_id",
                                ]
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "paid": {
                                "$sum": "$amount",
                            },
                        }
                    },
                ],
                "as": "payments",
            }
        },
        {
            "$project": {
                "outstanding": {
                    "$subtract": [
                        "$total",
                        {
                            "$ifNull": [
                                {
                                    "$arrayElemAt": [
                                        "$payments.paid",
                                        0,
                                    ]
                                },
                                0,
                            ]
                        },
                    ]
                }
            }
        },
        {
            "$match": {
                "outstanding": {
                    "$gt": 0,
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {
                    "$sum": "$outstanding",
                },
            }
        },
    ]

    payable_cursor = await supplier_invoices_collection.aggregate(
        payable_pipeline
    )

    payable_result = await payable_cursor.to_list()

    supplier_payable = (
        float(payable_result[0]["total"])
        if payable_result
        else 0.0
    )

    # ---------------------------------------------------------
    # Invoice jatuh tempo
    # ---------------------------------------------------------
    overdue_invoice_count = await SupplierInvoice.find(
        {
            "paymentStatus": {
                "$in": [
                    PaymentStatus.UNPAID,
                    PaymentStatus.PARTIALLY_PAID,
                    PaymentStatus.OVERDUE,
                ]
            },
            "dueDate": {
                "$lt": now,
            },
        }
    ).count()

    # Produk terlaris berdasarkan quantity terjual
    best_selling_pipeline = [
        {
            "$match": {
                "status": SaleStatus.PAID.value,
            }
        },
        {
            "$unwind": "$items",
        },
        {
            "$group": {
                "_id": {
                    "product_id": "$items.productId",
                    "sku": "$items.sku",
                    "name": "$items.name",
                },
                "quantity_sold": {
                    "$sum": "$items.quantity",
                },
            },
        },
        {
            "$sort": {
                "quantity_sold": -1,
                "_id.name": 1,
            },
        },
        {
            "$limit": 10,
        },
    ]

    best_selling_cursor = await db["sales"].aggregate(
        best_selling_pipeline
    )
    best_selling_result = await best_selling_cursor.to_list()

    best_selling_products = [
        DashboardBestSellingProduct(
            product_id=item["_id"]["product_id"],
            sku=item["_id"]["sku"],
            name=item["_id"]["name"],
            quantity_sold=float(item["quantity_sold"]),
        )
        for item in best_selling_result
    ]

    # ---------------------------------------------------------
    # Response
    # ---------------------------------------------------------
    return DashboardAnalyticsResponse(
        sales_today=float(sales_today),
        transaction_count_today=transaction_count_today,
        total_products=total_products,
        total_members=total_members,
        low_stock_count=low_stock_count,
        active_po_count=active_po_count,
        supplier_payable=supplier_payable,
        overdue_invoice_count=overdue_invoice_count,
        expenses=None,
        sales_analytics=sales_analytics,
        best_selling_products=best_selling_products,
        generated_at=now,
    )