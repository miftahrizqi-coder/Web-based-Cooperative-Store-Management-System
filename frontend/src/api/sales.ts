import { api, type Paginated } from '../services/api'
import type { CreateSalePayload, Sale, SaleStatus } from '../types/sale'

export interface SalesQuery {
  dateFrom?: string
  dateTo?: string
  status?: SaleStatus | ''
  cashierId?: string
  memberId?: string
  search?: string
  page?: number
  pageSize?: number
}

export function getSales(params: SalesQuery = {}): Promise<Paginated<Sale>> {
  return api.paginated<Sale>('/api/sales', {
    ...params,
    status: params.status || undefined,
    page: params.page ?? 1,
    pageSize: params.pageSize ?? 20,
  })
}

export function getSale(id: string): Promise<Sale> {
  return api.get<Sale>(`/api/sales/${id}`)
}

export function getSaleByInvoice(invoiceNumber: string): Promise<Sale> {
  return api.get<Sale>(`/api/sales/invoice/${encodeURIComponent(invoiceNumber.trim())}`)
}

export function createSale(payload: CreateSalePayload): Promise<Sale> {
  return api.post<Sale>('/api/sales', payload)
}

export function cancelSale(id: string, reason: string | null): Promise<Sale> {
  return api.post<Sale>(`/api/sales/${id}/cancel`, { reason })
}
