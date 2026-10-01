import { api, type Paginated } from '../services/api'
import type {
  PurchaseReturnPayload,
  ReturnRecord,
  ReturnStatus,
  ReturnType,
  SalesReturnPayload,
} from '../types/returns'

export function getReturns(params: {
  type?: ReturnType | ''
  status?: ReturnStatus | ''
  saleId?: string
  receiptId?: string
  page?: number
  pageSize?: number
} = {}): Promise<Paginated<ReturnRecord>> {
  return api.paginated<ReturnRecord>('/api/returns', {
    type: params.type || undefined,
    status: params.status || undefined,
    saleId: params.saleId,
    receiptId: params.receiptId,
    page: params.page ?? 1,
    pageSize: params.pageSize ?? 20,
  })
}

export function getReturn(id: string): Promise<ReturnRecord> {
  return api.get<ReturnRecord>(`/api/returns/${id}`)
}

export function createSalesReturn(payload: SalesReturnPayload): Promise<ReturnRecord> {
  return api.post<ReturnRecord>('/api/returns/sales', payload)
}

export function createPurchaseReturn(payload: PurchaseReturnPayload): Promise<ReturnRecord> {
  return api.post<ReturnRecord>('/api/returns/purchases', payload)
}

export function approveReturn(id: string): Promise<ReturnRecord> {
  return api.post<ReturnRecord>(`/api/returns/${id}/approve`)
}

export function rejectReturn(id: string, reason: string): Promise<ReturnRecord> {
  return api.post<ReturnRecord>(`/api/returns/${id}/reject`, { reason })
}
