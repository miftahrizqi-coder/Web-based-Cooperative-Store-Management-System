import { api, type Paginated } from '../services/api'
import type {
  InventoryItem,
  StockAdjustmentPayload,
  StockAdjustmentResponse,
  StockAlert,
  StockMovement,
  StockMovementType,
  StockOpname,
  StockOpnamePayload,
  StockStatus,
} from '../types/inventory'

export interface InventoryParams {
  search?: string
  stockStatus?: StockStatus
  categoryId?: string
}

export function getInventory(_accessToken: string | null, params: InventoryParams = {}): Promise<InventoryItem[]> {
  return api.get<InventoryItem[]>('/api/inventory', {
    search: params.search,
    stockStatus: params.stockStatus,
    categoryId: params.categoryId,
  })
}

export function getStockMovements(params: {
  productId?: string
  type?: StockMovementType | ''
  referenceId?: string
  dateFrom?: string
  dateTo?: string
  page?: number
  pageSize?: number
} = {}): Promise<Paginated<StockMovement>> {
  return api.paginated<StockMovement>('/api/inventory/movements', {
    productId: params.productId,
    type: params.type || undefined,
    referenceId: params.referenceId,
    dateFrom: params.dateFrom,
    dateTo: params.dateTo,
    page: params.page ?? 1,
    pageSize: params.pageSize ?? 50,
  })
}

export function createStockAdjustment(
  _accessToken: string | null,
  payload: StockAdjustmentPayload,
): Promise<StockAdjustmentResponse> {
  return api.post<StockAdjustmentResponse>('/api/inventory/adjustment', payload)
}

export function createStockOpname(payload: StockOpnamePayload): Promise<StockOpname> {
  return api.post<StockOpname>('/api/inventory/stock-opname', payload)
}

export function getStockOpnames(page = 1, pageSize = 20): Promise<Paginated<StockOpname>> {
  return api.paginated<StockOpname>('/api/inventory/stock-opname', { page, pageSize })
}

export function getStockOpname(id: string): Promise<StockOpname> {
  return api.get<StockOpname>(`/api/inventory/stock-opname/${id}`)
}

export function getInventoryAlerts(_accessToken?: string | null): Promise<StockAlert[]> {
  return api.get<StockAlert[]>('/api/inventory/alerts')
}
