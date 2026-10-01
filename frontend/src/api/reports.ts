import { api } from '../services/api'
import type {
  DashboardData,
  GroupBy,
  InventoryReport,
  PayablesReport,
  ProfitReport,
  PurchasesReport,
  SalesReport,
  SuppliersReport,
} from '../types/report'

export interface PeriodParams {
  dateFrom?: string
  dateTo?: string
  groupBy?: GroupBy
}

export const getDashboard = () => api.get<DashboardData>('/api/reports/dashboard')

export const getSalesReport = (
  params: PeriodParams & { cashierId?: string; productId?: string; categoryId?: string; memberId?: string },
) => api.get<SalesReport>('/api/reports/sales', { ...params })

export const getPurchasesReport = (params: PeriodParams & { supplierId?: string }) =>
  api.get<PurchasesReport>('/api/reports/purchases', { ...params })

export const getInventoryReport = (params: PeriodParams & { categoryId?: string }) =>
  api.get<InventoryReport>('/api/reports/inventory', { ...params })

export const getSuppliersReport = () => api.get<SuppliersReport>('/api/reports/suppliers')

export const getPayablesReport = (params: { supplierId?: string; outstandingOnly?: boolean } = {}) =>
  api.get<PayablesReport>('/api/reports/payables', { ...params })

export const getProfitReport = (params: PeriodParams) =>
  api.get<ProfitReport>('/api/reports/profit', { ...params })
