export type StockStatus =
  | 'AVAILABLE'
  | 'LOW_STOCK'
  | 'OUT_OF_STOCK'

export interface InventoryItem {
  product_id: string
  sku: string
  barcode: string | null
  name: string
  unit: string
  stock: number
  minimum_stock: number
  stock_status: StockStatus
  is_active: boolean
}

export type StockMovementType =
  | 'PURCHASE'
  | 'SALE'
  | 'SALE_RETURN'
  | 'PURCHASE_RETURN'
  | 'ADJUSTMENT'
  | 'STOCK_OPNAME'

export interface StockMovement {
  id: string
  product_id: string
  sku: string
  product_name: string
  type: StockMovementType
  quantity: number
  stock_before: number
  stock_after: number
  reference_type: string | null
  reference_id: string | null
  created_by: string
  created_at: string
}