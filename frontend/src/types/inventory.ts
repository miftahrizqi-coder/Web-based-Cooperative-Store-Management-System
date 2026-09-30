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

export interface StockAdjustmentPayload {
  product_id: string
  quantity: number
  reason: string
}

export interface StockAdjustmentResponse {
  product_id: string
  quantity: number
  stock_before: number
  stock_after: number
  reason: string
  movement_id: string
}

export interface StockOpnamePayload {
  product_id: string
  physical_stock: number
  reason: string
}

export interface StockOpnameResponse {
  product_id: string
  system_stock: number
  physical_stock: number
  difference: number
  reason: string
  movement_id: string | null
  audit_event_id: string
}

export interface StockAlert {
  product_id: string
  sku: string
  name: string
  stock: number
  minimum_stock: number
  status: 'LOW_STOCK' | 'OUT_OF_STOCK'
}

export interface InventoryItem {
  product_id: string
  sku: string
  barcode: string | null
  name: string
  unit: string
  stock: number
  minimum_stock: number
  stock_status:
    | 'AVAILABLE'
    | 'LOW_STOCK'
    | 'OUT_OF_STOCK'
  is_active: boolean
}

export interface StockMovement {
  id: string
  product_id: string
  sku: string
  product_name: string
  type:
    | 'PURCHASE'
    | 'SALE'
    | 'SALE_RETURN'
    | 'PURCHASE_RETURN'
    | 'ADJUSTMENT'
    | 'STOCK_OPNAME'
  quantity: number
  stock_before: number
  stock_after: number
  reference_type: string | null
  reference_id: string | null
  created_by: string
  created_at: string
}

export interface StockAdjustmentPayload {
  product_id: string
  quantity: number
  reason: string
}

export interface StockAdjustmentResponse {
  product_id: string
  quantity: number
  stock_before: number
  stock_after: number
  reason: string
  movement_id: string
}

export interface StockOpnamePayload {
  product_id: string
  physical_stock: number
  reason: string
}

export interface StockOpnameResponse {
  product_id: string
  system_stock: number
  physical_stock: number
  difference: number
  reason: string
  movement_id: string | null
  audit_event_id: string
}

export interface StockAlert {
  product_id: string
  sku: string
  name: string
  stock: number
  minimum_stock: number
  status: 'LOW_STOCK' | 'OUT_OF_STOCK'
}