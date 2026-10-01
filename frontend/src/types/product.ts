export type StockStatus = 'AVAILABLE' | 'LOW_STOCK' | 'OUT_OF_STOCK'

export interface Product {
  id: string
  sku: string
  barcode: string | null
  name: string
  categoryId: string
  categoryName: string | null
  unit: string
  /** null untuk kasir (harga beli disembunyikan). */
  purchasePrice: number | null
  sellingPrice: number
  stock: number
  minimumStock: number
  stockStatus: StockStatus
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export type ProductStockStatus = 'all' | 'available' | 'low' | 'out'

export interface ProductPayload {
  sku: string
  barcode: string | null
  name: string
  categoryId: string
  unit: string
  purchasePrice: number
  sellingPrice: number
  minimumStock: number
}

export interface ProductCreatePayload extends ProductPayload {
  /** Stok awal, dicatat sebagai stock movement. */
  stock: number
}

export interface ProductUpdatePayload extends ProductPayload {
  isActive: boolean
}
