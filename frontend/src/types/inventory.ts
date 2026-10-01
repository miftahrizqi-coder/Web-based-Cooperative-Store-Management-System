import type { StockStatus } from './product'

export type { StockStatus }

export interface InventoryItem {
  productId: string
  sku: string
  barcode: string | null
  name: string
  categoryId: string
  categoryName: string | null
  unit: string
  stock: number
  minimumStock: number
  stockStatus: StockStatus
  purchasePrice: number
  sellingPrice: number
  stockValue: number
  isActive: boolean
  updatedAt: string
}

export type StockMovementType =
  | 'PURCHASE'
  | 'SALE'
  | 'SALE_RETURN'
  | 'PURCHASE_RETURN'
  | 'ADJUSTMENT'
  | 'STOCK_OPNAME'

export const MOVEMENT_TYPE_LABELS: Record<StockMovementType, string> = {
  PURCHASE: 'Pembelian',
  SALE: 'Penjualan',
  SALE_RETURN: 'Retur penjualan',
  PURCHASE_RETURN: 'Retur pembelian',
  ADJUSTMENT: 'Adjustment',
  STOCK_OPNAME: 'Stock opname',
}

export interface StockMovement {
  id: string
  productId: string
  sku: string
  productName: string
  type: StockMovementType
  /** Bertanda: positif = masuk, negatif = keluar. */
  quantity: number
  stockBefore: number
  stockAfter: number
  referenceType: string | null
  referenceId: string | null
  referenceNumber: string | null
  reason: string | null
  createdBy: string
  createdByName: string | null
  createdAt: string
}

export interface StockAdjustmentPayload {
  productId: string
  quantity: number
  reason: string
}

export interface StockAdjustmentResponse {
  productId: string
  quantity: number
  stockBefore: number
  stockAfter: number
  reason: string
  movementId: string
}

export interface StockOpnameItemPayload {
  productId: string
  physicalStock: number
  systemStock: number | null
  reason: string | null
}

export interface StockOpnamePayload {
  items: StockOpnameItemPayload[]
  notes: string | null
}

export interface StockOpnameItem {
  productId: string
  sku: string
  name: string
  systemStock: number
  physicalStock: number
  difference: number
  reason: string | null
  movementId: string | null
}

export interface StockOpname {
  id: string
  opnameNumber: string
  items: StockOpnameItem[]
  notes: string | null
  totalItems: number
  itemsWithDifference: number
  createdBy: string
  createdByName: string | null
  createdAt: string
}

export interface StockAlert {
  productId: string
  sku: string
  name: string
  unit: string
  stock: number
  minimumStock: number
  status: 'LOW_STOCK' | 'OUT_OF_STOCK'
}
