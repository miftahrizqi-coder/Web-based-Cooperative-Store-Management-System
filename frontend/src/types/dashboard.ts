export interface DashboardSalesAnalyticsItem {
  date: string
  sales: number
  transactions: number
}

export interface DashboardAnalytics {
  sales_today: number
  transaction_count_today: number
  total_products: number
  total_members: number
  low_stock_count: number
  active_po_count: number
  supplier_payable: number
  overdue_invoice_count: number
  expenses: number | null
  sales_analytics: DashboardSalesAnalyticsItem[]
  generated_at: string
}