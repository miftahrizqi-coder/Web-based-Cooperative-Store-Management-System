from datetime import datetime, timezone

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
from app.schemas.dashboard import DashboardAnalyticsResponse


db = client[settings.mongodb_database]

supplier_invoices_collection = db["supplier_invoices"]
supplier_payments_collection = db["supplier_payments"]


ACTIVE_PO_STATUSES = [
    POStatus.PENDING_APPROVAL.value,
    POStatus.APPROVED.value,
    POStatus.ORDERED.value,
    POStatus.PARTIALLY_RECEIVED.value,
]


async def get_dashboard_analytics() -> DashboardAnalyticsResponse:
    now = datetime.now(timezone.utc)

    start_of_today = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

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
                    "invoice_id": {"$toString": "$_id"},
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
                            "paid": {"$sum": "$amount"},
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
                                {"$arrayElemAt": ["$payments.paid", 0]},
                                0,
                            ]
                        },
                    ]
                }
            }
        },
        {
            "$match": {
                "outstanding": {"$gt": 0},
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$outstanding"},
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
        generated_at=now,
    )