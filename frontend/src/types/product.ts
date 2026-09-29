export interface Product {
  id: string
  sku: string
  barcode: string | null
  name: string
  category_id: string
  unit: string
  purchase_price: number
  selling_price: number
  stock: number
  minimum_stock: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export type ProductStockStatus = 'all' | 'available' | 'low' | 'out'
