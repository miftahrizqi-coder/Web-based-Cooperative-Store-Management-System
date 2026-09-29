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