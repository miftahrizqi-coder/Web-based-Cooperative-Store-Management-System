"""
Laporan (PRD §28) & dashboard (PRD §9).

Agregasi dihitung di aplikasi (Python) di atas query yang sudah difilter
per periode. Pertimbangannya: portabel (tidak bergantung operator agregasi
tertentu), mudah diuji, dan cukup cepat untuk skala toko koperasi. Bila data
tumbuh sangat besar, fungsi di sini adalah titik tunggal untuk dipindah ke
aggregation pipeline MongoDB.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta

from bson import ObjectId

from app.core.config import settings
from app.core.utils import (
    as_utc,
    local_day_bounds,
    local_range_bounds,
    local_today,
    to_local_date,
    utc_now,
)
from app.models.category import Category
from app.models.expense import Expense
from app.models.inventory import StockMovement
from app.models.member import Member, MemberStatus
from app.models.procurement import (
    POStatus,
    Purchase,
    PurchaseOrder,
    SupplierInvoice,
)
from app.models.product import Product
from app.models.returns import Return, ReturnStatus, ReturnType
from app.models.sales import Sale, SaleStatus
from app.models.supplier import Supplier
from app.models.supplier_product import SupplierProduct
from app.models.user import User
from app.services.procurement import compute_payables
from app.services.stock import stock_status


ACTIVE_PO_STATUSES = [
    POStatus.PENDING_APPROVAL.value,
    POStatus.APPROVED.value,
    POStatus.ORDERED.value,
    POStatus.PARTIALLY_RECEIVED.value,
]


# ---------------------------------------------------------------------------
# Helper periode
# ---------------------------------------------------------------------------


def resolve_period(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    """Default: awal bulan berjalan s/d hari ini (zona waktu lokal)."""
    today = local_today()
    end = date_to or today
    start = date_from or end.replace(day=1)
    if start > end:
        start, end = end, start
    return start, end


def range_query(field: str, start: date, end: date) -> dict:
    lower, upper = local_range_bounds(start, end)
    return {field: {"$gte": lower, "$lt": upper}}


def period_key(value: datetime, group_by: str) -> str:
    day = to_local_date(value)
    if group_by == "month":
        return day.strftime("%Y-%m")
    if group_by == "week":
        iso = day.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    return day.isoformat()


def period_keys(start: date, end: date, group_by: str) -> list[str]:
    keys: list[str] = []
    cursor = start
    while cursor <= end:
        key = period_key(datetime(cursor.year, cursor.month, cursor.day, 12), group_by)
        if key not in keys:
            keys.append(key)
        cursor += timedelta(days=1)
    return keys


async def _lookup(model, ids: set[str]) -> dict:
    object_ids = [ObjectId(i) for i in ids if i and ObjectId.is_valid(i)]
    if not object_ids:
        return {}
    return {str(d.id): d for d in await model.find({"_id": {"$in": object_ids}}).to_list()}


def _r(value: float) -> float:
    return round(value, 2)


# ---------------------------------------------------------------------------
# Penjualan (PRD §28.1)
# ---------------------------------------------------------------------------


async def sales_report(
    date_from: date | None,
    date_to: date | None,
    group_by: str = "day",
    cashier_id: str | None = None,
    product_id: str | None = None,
    category_id: str | None = None,
    member_id: str | None = None,
) -> dict:
    start, end = resolve_period(date_from, date_to)
    query: dict = {**range_query("createdAt", start, end)}
    if cashier_id:
        query["cashierId"] = cashier_id
    if member_id:
        query["memberId"] = member_id

    sales = await Sale.find(query).to_list()
    completed = [s for s in sales if s.status == SaleStatus.COMPLETED]
    cancelled_count = len(sales) - len(completed)

    category_products: set[str] | None = None
    if category_id:
        category_products = {
            str(p.id) for p in await Product.find({"categoryId": category_id}).to_list()
        }

    def item_included(pid: str) -> bool:
        if product_id and pid != product_id:
            return False
        if category_products is not None and pid not in category_products:
            return False
        return True

    series: dict[str, dict] = {
        key: {"period": key, "transactionCount": 0, "itemsSold": 0.0,
              "grossSales": 0.0, "discount": 0.0, "netSales": 0.0}
        for key in period_keys(start, end, group_by)
    }
    by_product: dict[str, dict] = {}
    by_cashier: dict[str, dict] = defaultdict(lambda: {"transactionCount": 0, "netSales": 0.0})
    by_payment: dict[str, dict] = defaultdict(lambda: {"transactionCount": 0, "netSales": 0.0})

    summary = {"transactionCount": 0, "itemsSold": 0.0, "grossSales": 0.0, "discount": 0.0, "netSales": 0.0}

    for sale in completed:
        lines = [i for i in sale.items if item_included(i.productId)]
        if not lines:
            continue
        gross = sum(i.subtotal for i in lines)
        # Diskon transaksi dialokasikan proporsional ke item yang difilter.
        discount = sale.discount * (gross / sale.subtotal) if sale.subtotal else 0
        net = gross - discount
        qty = sum(i.quantity for i in lines)

        key = period_key(sale.createdAt, group_by)
        bucket = series.setdefault(key, {"period": key, "transactionCount": 0, "itemsSold": 0.0,
                                         "grossSales": 0.0, "discount": 0.0, "netSales": 0.0})
        for target in (bucket, summary):
            target["transactionCount"] += 1
            target["itemsSold"] += qty
            target["grossSales"] += gross
            target["discount"] += discount
            target["netSales"] += net

        by_cashier[sale.cashierId]["transactionCount"] += 1
        by_cashier[sale.cashierId]["netSales"] += net
        by_payment[sale.payment.method.value]["transactionCount"] += 1
        by_payment[sale.payment.method.value]["netSales"] += net

        ratio = (sale.total / sale.subtotal) if sale.subtotal else 1
        for item in lines:
            row = by_product.setdefault(
                item.productId,
                {"productId": item.productId, "sku": item.sku, "name": item.name,
                 "quantity": 0.0, "netSales": 0.0},
            )
            row["quantity"] += item.quantity
            row["netSales"] += item.subtotal * ratio

    # Retur penjualan yang disetujui dalam periode mengurangi pendapatan.
    return_query: dict = {
        "type": ReturnType.SALE.value,
        "status": ReturnStatus.APPROVED.value,
        **range_query("approvedAt", start, end),
    }
    returns_amount = 0.0
    returned_items = 0.0
    for ret in await Return.find(return_query).to_list():
        if member_id and ret.memberId != member_id:
            continue
        for item in ret.items:
            if item_included(item.productId):
                returns_amount += item.subtotal
                returned_items += item.quantity

    users = await _lookup(User, set(by_cashier))

    return {
        "period": {"dateFrom": start.isoformat(), "dateTo": end.isoformat(), "groupBy": group_by},
        "summary": {
            "transactionCount": summary["transactionCount"],
            "itemsSold": _r(summary["itemsSold"]),
            "grossSales": _r(summary["grossSales"]),
            "discount": _r(summary["discount"]),
            "totalSales": _r(summary["netSales"]),
            "returns": _r(returns_amount),
            "returnedItems": _r(returned_items),
            "revenue": _r(summary["netSales"] - returns_amount),
            "cancelledCount": cancelled_count,
            "averageTransaction": _r(summary["netSales"] / summary["transactionCount"])
            if summary["transactionCount"] else 0,
        },
        "series": [
            {**row, "itemsSold": _r(row["itemsSold"]), "grossSales": _r(row["grossSales"]),
             "discount": _r(row["discount"]), "netSales": _r(row["netSales"])}
            for row in sorted(series.values(), key=lambda r: r["period"])
        ],
        "byProduct": sorted(
            [{**r, "quantity": _r(r["quantity"]), "netSales": _r(r["netSales"])} for r in by_product.values()],
            key=lambda r: r["netSales"],
            reverse=True,
        ),
        "byCashier": sorted(
            [
                {"cashierId": cid, "cashierName": users[cid].name if cid in users else "-",
                 "transactionCount": v["transactionCount"], "netSales": _r(v["netSales"])}
                for cid, v in by_cashier.items()
            ],
            key=lambda r: r["netSales"],
            reverse=True,
        ),
        "byPaymentMethod": [
            {"method": m, "transactionCount": v["transactionCount"], "netSales": _r(v["netSales"])}
            for m, v in sorted(by_payment.items())
        ],
    }


# ---------------------------------------------------------------------------
# Pembelian (PRD §28.2)
# ---------------------------------------------------------------------------


async def purchases_report(
    date_from: date | None,
    date_to: date | None,
    group_by: str = "month",
    supplier_id: str | None = None,
) -> dict:
    start, end = resolve_period(date_from, date_to)

    purchase_query: dict = {**range_query("createdAt", start, end)}
    po_query: dict = {**range_query("createdAt", start, end)}
    if supplier_id:
        purchase_query["supplierId"] = supplier_id
        po_query["supplierId"] = supplier_id

    purchases = await Purchase.find(purchase_query).to_list()
    orders = await PurchaseOrder.find(po_query).to_list()

    by_supplier: dict[str, dict] = defaultdict(
        lambda: {"poCount": 0, "purchaseCount": 0, "itemsQuantity": 0.0, "totalPurchases": 0.0, "poValue": 0.0}
    )
    series: dict[str, dict] = {
        key: {"period": key, "purchaseCount": 0, "itemsQuantity": 0.0, "totalPurchases": 0.0}
        for key in period_keys(start, end, group_by)
    }

    for po in orders:
        if po.status == POStatus.CANCELLED:
            continue
        by_supplier[po.supplierId]["poCount"] += 1
        by_supplier[po.supplierId]["poValue"] += po.grandTotal

    for purchase in purchases:
        qty = sum(i.quantity for i in purchase.items)
        row = by_supplier[purchase.supplierId]
        row["purchaseCount"] += 1
        row["itemsQuantity"] += qty
        row["totalPurchases"] += purchase.total

        key = period_key(purchase.createdAt, group_by)
        bucket = series.setdefault(key, {"period": key, "purchaseCount": 0, "itemsQuantity": 0.0, "totalPurchases": 0.0})
        bucket["purchaseCount"] += 1
        bucket["itemsQuantity"] += qty
        bucket["totalPurchases"] += purchase.total

    suppliers = await _lookup(Supplier, set(by_supplier))
    returns = await Return.find(
        {
            "type": ReturnType.PURCHASE.value,
            "status": ReturnStatus.APPROVED.value,
            **range_query("approvedAt", start, end),
            **({"supplierId": supplier_id} if supplier_id else {}),
        }
    ).to_list()

    return {
        "period": {"dateFrom": start.isoformat(), "dateTo": end.isoformat(), "groupBy": group_by},
        "summary": {
            "poCount": sum(1 for po in orders if po.status != POStatus.CANCELLED),
            "cancelledPoCount": sum(1 for po in orders if po.status == POStatus.CANCELLED),
            "purchaseCount": len(purchases),
            "itemsQuantity": _r(sum(r["itemsQuantity"] for r in by_supplier.values())),
            "totalPurchases": _r(sum(p.total for p in purchases)),
            "purchaseReturns": _r(sum(r.totalAmount for r in returns)),
        },
        "series": [
            {**row, "itemsQuantity": _r(row["itemsQuantity"]), "totalPurchases": _r(row["totalPurchases"])}
            for row in sorted(series.values(), key=lambda r: r["period"])
        ],
        "bySupplier": sorted(
            [
                {
                    "supplierId": sid,
                    "supplierName": suppliers[sid].name if sid in suppliers else "-",
                    "poCount": v["poCount"],
                    "poValue": _r(v["poValue"]),
                    "purchaseCount": v["purchaseCount"],
                    "itemsQuantity": _r(v["itemsQuantity"]),
                    "totalPurchases": _r(v["totalPurchases"]),
                }
                for sid, v in by_supplier.items()
            ],
            key=lambda r: r["totalPurchases"],
            reverse=True,
        ),
    }


# ---------------------------------------------------------------------------
# Inventory (PRD §28.3)
# ---------------------------------------------------------------------------


async def inventory_report(
    date_from: date | None,
    date_to: date | None,
    category_id: str | None = None,
) -> dict:
    start, end = resolve_period(date_from, date_to)

    product_query: dict = {"isActive": True}
    if category_id:
        product_query["categoryId"] = category_id
    products = await Product.find(product_query).sort("name").to_list()
    product_ids = {str(p.id) for p in products}

    movements = await StockMovement.find(range_query("createdAt", start, end)).to_list()

    per_product: dict[str, dict] = defaultdict(
        lambda: {"stockIn": 0.0, "stockOut": 0.0, "adjustment": 0.0}
    )
    by_type: dict[str, dict] = defaultdict(lambda: {"count": 0, "quantity": 0.0})

    for m in movements:
        if m.productId not in product_ids:
            continue
        by_type[m.type.value]["count"] += 1
        by_type[m.type.value]["quantity"] += m.quantity
        row = per_product[m.productId]
        if m.type.value in {"ADJUSTMENT", "STOCK_OPNAME"}:
            row["adjustment"] += m.quantity
        elif m.quantity > 0:
            row["stockIn"] += m.quantity
        else:
            row["stockOut"] += -m.quantity

    categories = await _lookup(Category, {p.categoryId for p in products})

    rows = []
    for p in products:
        pid = str(p.id)
        status = stock_status(p.stock, p.minimumStock)
        rows.append(
            {
                "productId": pid,
                "sku": p.sku,
                "name": p.name,
                "categoryName": categories[p.categoryId].name if p.categoryId in categories else "-",
                "unit": p.unit,
                "stock": p.stock,
                "minimumStock": p.minimumStock,
                "stockStatus": status,
                "stockValue": _r(p.stock * p.purchasePrice),
                "stockIn": _r(per_product[pid]["stockIn"]),
                "stockOut": _r(per_product[pid]["stockOut"]),
                "adjustment": _r(per_product[pid]["adjustment"]),
            }
        )

    return {
        "period": {"dateFrom": start.isoformat(), "dateTo": end.isoformat()},
        "summary": {
            "totalProducts": len(rows),
            "totalStock": _r(sum(r["stock"] for r in rows)),
            "totalStockValue": _r(sum(r["stockValue"] for r in rows)),
            "lowStockCount": sum(1 for r in rows if r["stockStatus"] == "LOW_STOCK"),
            "outOfStockCount": sum(1 for r in rows if r["stockStatus"] == "OUT_OF_STOCK"),
            "stockIn": _r(sum(r["stockIn"] for r in rows)),
            "stockOut": _r(sum(r["stockOut"] for r in rows)),
            "adjustment": _r(sum(r["adjustment"] for r in rows)),
        },
        "movementsByType": [
            {"type": t, "count": v["count"], "quantity": _r(v["quantity"])}
            for t, v in sorted(by_type.items())
        ],
        "lowStock": [r for r in rows if r["stockStatus"] == "LOW_STOCK"],
        "outOfStock": [r for r in rows if r["stockStatus"] == "OUT_OF_STOCK"],
        "products": rows,
    }


# ---------------------------------------------------------------------------
# Supplier (PRD §28.4) & Hutang (PRD §28.5)
# ---------------------------------------------------------------------------


async def suppliers_report() -> dict:
    suppliers = await Supplier.find({}).sort("name").to_list()
    purchases = await Purchase.find({}).to_list()
    orders = await PurchaseOrder.find({"status": {"$ne": POStatus.CANCELLED.value}}).to_list()
    invoices = await SupplierInvoice.find({}).to_list()
    payables = await compute_payables(invoices)
    supplier_products = await SupplierProduct.find({"isActive": True}).to_list()

    rows = []
    for s in suppliers:
        sid = str(s.id)
        inv = [p for p in payables if p["supplierId"] == sid]
        rows.append(
            {
                "supplierId": sid,
                "supplierCode": s.supplierCode,
                "supplierName": s.name,
                "status": s.status.value,
                "productsSupplied": sum(1 for sp in supplier_products if sp.supplierId == sid),
                "poCount": sum(1 for o in orders if o.supplierId == sid),
                "totalPurchases": _r(sum(p.total for p in purchases if p.supplierId == sid)),
                "invoiceCount": len(inv),
                "totalInvoiced": _r(sum(p["total"] for p in inv)),
                "totalPaid": _r(sum(p["paid"] for p in inv)),
                "totalReturned": _r(sum(p["returned"] for p in inv)),
                "outstanding": _r(sum(p["outstanding"] for p in inv)),
                "overdueCount": sum(1 for p in inv if p["isOverdue"]),
            }
        )

    return {
        "summary": {
            "supplierCount": len(rows),
            "activeSupplierCount": sum(1 for r in rows if r["status"] == "ACTIVE"),
            "totalPurchases": _r(sum(r["totalPurchases"] for r in rows)),
            "totalInvoiced": _r(sum(r["totalInvoiced"] for r in rows)),
            "totalPaid": _r(sum(r["totalPaid"] for r in rows)),
            "outstanding": _r(sum(r["outstanding"] for r in rows)),
        },
        "suppliers": rows,
    }


async def payables_report(supplier_id: str | None = None, outstanding_only: bool = False) -> dict:
    query: dict = {}
    if supplier_id:
        query["supplierId"] = supplier_id
    invoices = await SupplierInvoice.find(query).sort("dueDate").to_list()
    rows = await compute_payables(invoices)
    if outstanding_only:
        rows = [r for r in rows if r["outstanding"] > 0]

    aging = {"current": 0.0, "1-30": 0.0, "31-60": 0.0, "61-90": 0.0, ">90": 0.0}
    for r in rows:
        if r["outstanding"] <= 0:
            continue
        days = r["daysOverdue"]
        bucket = (
            "current" if not r["isOverdue"] else
            "1-30" if days <= 30 else
            "31-60" if days <= 60 else
            "61-90" if days <= 90 else ">90"
        )
        aging[bucket] += r["outstanding"]

    return {
        "summary": {
            "invoiceCount": len(rows),
            "total": _r(sum(r["total"] for r in rows)),
            "paid": _r(sum(r["paid"] for r in rows)),
            "returned": _r(sum(r["returned"] for r in rows)),
            "outstanding": _r(sum(r["outstanding"] for r in rows)),
            "overdueCount": sum(1 for r in rows if r["isOverdue"]),
            "overdueAmount": _r(sum(r["outstanding"] for r in rows if r["isOverdue"])),
        },
        "aging": {k: _r(v) for k, v in aging.items()},
        "invoices": [
            {**r, "paymentStatus": r["paymentStatus"].value if hasattr(r["paymentStatus"], "value") else r["paymentStatus"]}
            for r in rows
        ],
    }


# ---------------------------------------------------------------------------
# Laba dasar (PRD §28.6)
# ---------------------------------------------------------------------------


async def profit_report(date_from: date | None, date_to: date | None, group_by: str = "month") -> dict:
    start, end = resolve_period(date_from, date_to)

    sales = await Sale.find(
        {**range_query("createdAt", start, end), "status": SaleStatus.COMPLETED.value}
    ).to_list()
    returns = await Return.find(
        {
            "type": ReturnType.SALE.value,
            "status": ReturnStatus.APPROVED.value,
            **range_query("approvedAt", start, end),
        }
    ).to_list()
    expenses = await Expense.find(range_query("date", start, end)).to_list()

    series: dict[str, dict] = {
        key: {"period": key, "sales": 0.0, "cogs": 0.0, "expenses": 0.0}
        for key in period_keys(start, end, group_by)
    }

    def bucket(value: datetime) -> dict:
        key = period_key(value, group_by)
        return series.setdefault(key, {"period": key, "sales": 0.0, "cogs": 0.0, "expenses": 0.0})

    total_sales = cogs = returned_sales = returned_cogs = total_expenses = 0.0

    for sale in sales:
        sale_cogs = sum(i.quantity * i.costPrice for i in sale.items)
        total_sales += sale.total
        cogs += sale_cogs
        b = bucket(sale.createdAt)
        b["sales"] += sale.total
        b["cogs"] += sale_cogs

    for ret in returns:
        ret_cogs = sum(i.quantity * i.costPrice for i in ret.items)
        returned_sales += ret.totalAmount
        returned_cogs += ret_cogs
        b = bucket(ret.approvedAt or ret.createdAt)
        b["sales"] -= ret.totalAmount
        b["cogs"] -= ret_cogs

    expenses_by_category: dict[str, float] = defaultdict(float)
    for exp in expenses:
        total_expenses += exp.amount
        expenses_by_category[exp.category.value] += exp.amount
        bucket(exp.date)["expenses"] += exp.amount

    net_sales = total_sales - returned_sales
    net_cogs = cogs - returned_cogs
    gross_profit = net_sales - net_cogs

    return {
        "period": {"dateFrom": start.isoformat(), "dateTo": end.isoformat(), "groupBy": group_by},
        "cogsMethod": settings.cogs_method,
        "cogsMethodDescription": (
            "HPP dihitung dari harga beli produk yang di-snapshot pada saat transaksi "
            "penjualan (harga beli terakhir dari penerimaan barang). Tetapkan metode HPP "
            "resmi koperasi sebelum laporan ini dipakai sebagai laporan keuangan resmi."
        ),
        "summary": {
            "totalSales": _r(total_sales),
            "salesReturns": _r(returned_sales),
            "netSales": _r(net_sales),
            "cogs": _r(net_cogs),
            "grossProfit": _r(gross_profit),
            "expenses": _r(total_expenses),
            "netProfit": _r(gross_profit - total_expenses),
            "grossMargin": _r(gross_profit / net_sales * 100) if net_sales else 0,
        },
        "expensesByCategory": [
            {"category": k, "amount": _r(v)} for k, v in sorted(expenses_by_category.items())
        ],
        "series": [
            {
                "period": row["period"],
                "sales": _r(row["sales"]),
                "cogs": _r(row["cogs"]),
                "grossProfit": _r(row["sales"] - row["cogs"]),
                "expenses": _r(row["expenses"]),
                "netProfit": _r(row["sales"] - row["cogs"] - row["expenses"]),
            }
            for row in sorted(series.values(), key=lambda r: r["period"])
        ],
    }


# ---------------------------------------------------------------------------
# Dashboard (PRD §9)
# ---------------------------------------------------------------------------


async def dashboard(user: User) -> dict:
    today = local_today()
    today_start, today_end = local_day_bounds(today)
    is_cashier = user.role.value == "kasir"

    today_query: dict = {"createdAt": {"$gte": today_start, "$lt": today_end}, "status": SaleStatus.COMPLETED.value}
    if is_cashier:
        today_query["cashierId"] = str(user.id)
    today_sales = await Sale.find(today_query).to_list()

    # Grafik 14 hari terakhir.
    chart_start = today - timedelta(days=13)
    chart_query: dict = {
        **range_query("createdAt", chart_start, today),
        "status": SaleStatus.COMPLETED.value,
    }
    if is_cashier:
        chart_query["cashierId"] = str(user.id)
    chart_sales = await Sale.find(chart_query).to_list()
    chart = {key: {"date": key, "total": 0.0, "transactions": 0} for key in period_keys(chart_start, today, "day")}
    for sale in chart_sales:
        key = period_key(sale.createdAt, "day")
        if key in chart:
            chart[key]["total"] += sale.total
            chart[key]["transactions"] += 1

    result: dict = {
        "date": today.isoformat(),
        "todaySales": _r(sum(s.total for s in today_sales)),
        "todayTransactions": len(today_sales),
        "salesChart": [{**v, "total": _r(v["total"])} for v in chart.values()],
    }

    if is_cashier:
        return result

    # Produk terlaris bulan berjalan.
    month_start = today.replace(day=1)
    month_sales = [
        s for s in await Sale.find(
            {**range_query("createdAt", month_start, today), "status": SaleStatus.COMPLETED.value}
        ).to_list()
    ]
    top: dict[str, dict] = {}
    for sale in month_sales:
        for item in sale.items:
            row = top.setdefault(item.productId, {"productId": item.productId, "sku": item.sku,
                                                  "name": item.name, "quantity": 0.0, "total": 0.0})
            row["quantity"] += item.quantity - item.returnedQuantity
            row["total"] += item.subtotal

    products = await Product.find({"isActive": True}).to_list()
    low = [p for p in products if stock_status(p.stock, p.minimumStock) == "LOW_STOCK"]
    out = [p for p in products if stock_status(p.stock, p.minimumStock) == "OUT_OF_STOCK"]

    invoices = await SupplierInvoice.find({}).to_list()
    payables = [p for p in await compute_payables(invoices) if p["outstanding"] > 0]
    soon = utc_now() + timedelta(days=7)
    due = [p for p in payables if p["isOverdue"] or as_utc(p["dueDate"]) <= soon]

    expenses = await Expense.find(range_query("date", month_start, today)).to_list()

    def stock_row(p: Product) -> dict:
        return {"productId": str(p.id), "sku": p.sku, "name": p.name, "unit": p.unit,
                "stock": p.stock, "minimumStock": p.minimumStock}

    result.update(
        {
            "totalProducts": len(products),
            "totalMembers": await Member.find({"status": MemberStatus.ACTIVE.value}).count(),
            "lowStockCount": len(low),
            "outOfStockCount": len(out),
            "lowStockProducts": [stock_row(p) for p in sorted(low, key=lambda p: p.stock)[:10]],
            "outOfStockProducts": [stock_row(p) for p in out[:10]],
            "activePurchaseOrders": await PurchaseOrder.find(
                {"status": {"$in": ACTIVE_PO_STATUSES}}
            ).count(),
            "pendingApprovalPurchaseOrders": await PurchaseOrder.find(
                {"status": POStatus.PENDING_APPROVAL.value}
            ).count(),
            "supplierPayables": _r(sum(p["outstanding"] for p in payables)),
            "dueInvoiceCount": len(due),
            "overdueInvoiceCount": sum(1 for p in due if p["isOverdue"]),
            "dueInvoices": [
                {
                    "invoiceId": p["invoiceId"],
                    "invoiceNumber": p["invoiceNumber"],
                    "supplierName": p["supplierName"],
                    "outstanding": p["outstanding"],
                    "dueDate": as_utc(p["dueDate"]).isoformat(),
                    "isOverdue": p["isOverdue"],
                }
                for p in sorted(due, key=lambda p: as_utc(p["dueDate"]))[:5]
            ],
            "monthExpenses": _r(sum(e.amount for e in expenses)),
            "monthSales": _r(sum(s.total for s in month_sales)),
            "topProducts": sorted(
                [{**r, "quantity": _r(r["quantity"]), "total": _r(r["total"])} for r in top.values()],
                key=lambda r: r["quantity"],
                reverse=True,
            )[:5],
            "pendingReturns": await Return.find(
                {"status": ReturnStatus.PENDING_APPROVAL.value}
            ).count(),
            "pendingReceipts": await PurchaseOrder.find(
                {"status": {"$in": [POStatus.ORDERED.value, POStatus.PARTIALLY_RECEIVED.value]}}
            ).count(),
        }
    )
    return result

