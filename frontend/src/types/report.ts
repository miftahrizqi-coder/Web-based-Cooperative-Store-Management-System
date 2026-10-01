export type GroupBy = 'day' | 'week' | 'month'

export interface ReportPeriod {
  dateFrom: string
  dateTo: string
  groupBy?: GroupBy
}

export interface DashboardStockRow {
  productId: string
  sku: string
  name: string
  unit: string
  stock: number
  minimumStock: number
}

export interface DashboardData {
  date: string
  todaySales: number
  todayTransactions: number
  salesChart: { date: string; total: number; transactions: number }[]
  // Hanya untuk admin/pengurus:
  totalProducts?: number
  totalMembers?: number
  lowStockCount?: number
  outOfStockCount?: number
  lowStockProducts?: DashboardStockRow[]
  outOfStockProducts?: DashboardStockRow[]
  activePurchaseOrders?: number
  pendingApprovalPurchaseOrders?: number
  supplierPayables?: number
  dueInvoiceCount?: number
  overdueInvoiceCount?: number
  dueInvoices?: {
    invoiceId: string
    invoiceNumber: string
    supplierName: string | null
    outstanding: number
    dueDate: string
    isOverdue: boolean
  }[]
  monthExpenses?: number
  monthSales?: number
  topProducts?: { productId: string; sku: string; name: string; quantity: number; total: number }[]
  pendingReturns?: number
  pendingReceipts?: number
}

export interface SalesReport {
  period: ReportPeriod
  summary: {
    transactionCount: number
    itemsSold: number
    grossSales: number
    discount: number
    totalSales: number
    returns: number
    returnedItems: number
    revenue: number
    cancelledCount: number
    averageTransaction: number
  }
  series: { period: string; transactionCount: number; itemsSold: number; grossSales: number; discount: number; netSales: number }[]
  byProduct: { productId: string; sku: string; name: string; quantity: number; netSales: number }[]
  byCashier: { cashierId: string; cashierName: string; transactionCount: number; netSales: number }[]
  byPaymentMethod: { method: string; transactionCount: number; netSales: number }[]
}

export interface PurchasesReport {
  period: ReportPeriod
  summary: {
    poCount: number
    cancelledPoCount: number
    purchaseCount: number
    itemsQuantity: number
    totalPurchases: number
    purchaseReturns: number
  }
  series: { period: string; purchaseCount: number; itemsQuantity: number; totalPurchases: number }[]
  bySupplier: {
    supplierId: string
    supplierName: string
    poCount: number
    poValue: number
    purchaseCount: number
    itemsQuantity: number
    totalPurchases: number
  }[]
}

export interface InventoryReportRow {
  productId: string
  sku: string
  name: string
  categoryName: string
  unit: string
  stock: number
  minimumStock: number
  stockStatus: string
  stockValue: number
  stockIn: number
  stockOut: number
  adjustment: number
}

export interface InventoryReport {
  period: ReportPeriod
  summary: {
    totalProducts: number
    totalStock: number
    totalStockValue: number
    lowStockCount: number
    outOfStockCount: number
    stockIn: number
    stockOut: number
    adjustment: number
  }
  movementsByType: { type: string; count: number; quantity: number }[]
  lowStock: InventoryReportRow[]
  outOfStock: InventoryReportRow[]
  products: InventoryReportRow[]
}

export interface SuppliersReport {
  summary: {
    supplierCount: number
    activeSupplierCount: number
    totalPurchases: number
    totalInvoiced: number
    totalPaid: number
    outstanding: number
  }
  suppliers: {
    supplierId: string
    supplierCode: string
    supplierName: string
    status: string
    productsSupplied: number
    poCount: number
    totalPurchases: number
    invoiceCount: number
    totalInvoiced: number
    totalPaid: number
    totalReturned: number
    outstanding: number
    overdueCount: number
  }[]
}

export interface PayablesReport {
  summary: {
    invoiceCount: number
    total: number
    paid: number
    returned: number
    outstanding: number
    overdueCount: number
    overdueAmount: number
  }
  aging: Record<string, number>
  invoices: {
    invoiceId: string
    invoiceNumber: string
    supplierId: string
    supplierName: string | null
    invoiceDate: string | null
    total: number
    returned: number
    paid: number
    outstanding: number
    paymentStatus: string
    dueDate: string
    isOverdue: boolean
    daysOverdue: number
  }[]
}

export interface ProfitReport {
  period: ReportPeriod
  cogsMethod: string
  cogsMethodDescription: string
  summary: {
    totalSales: number
    salesReturns: number
    netSales: number
    cogs: number
    grossProfit: number
    expenses: number
    netProfit: number
    grossMargin: number
  }
  expensesByCategory: { category: string; amount: number }[]
  series: { period: string; sales: number; cogs: number; grossProfit: number; expenses: number; netProfit: number }[]
}
