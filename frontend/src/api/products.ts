import { api } from '../services/api'
import type {
  Product,
  ProductCreatePayload,
  ProductStockStatus,
  ProductUpdatePayload,
} from '../types/product'

export type { ProductCreatePayload as ProductPayload, ProductUpdatePayload } from '../types/product'

export interface ProductQuery {
  search?: string
  categoryId?: string
  stockStatus?: ProductStockStatus
  isActive?: boolean
}

// Parameter accessToken dipertahankan demi kompatibilitas pemanggil lama;
// token diambil dari store oleh services/api.

export function getProducts(_accessToken: string | null, params: ProductQuery = {}): Promise<Product[]> {
  return api.get<Product[]>('/api/products', {
    search: params.search?.trim(),
    categoryId: params.categoryId,
    stockStatus: params.stockStatus && params.stockStatus !== 'all' ? params.stockStatus : undefined,
    isActive: params.isActive,
  })
}

export function getProduct(_accessToken: string | null, productId: string): Promise<Product> {
  return api.get<Product>(`/api/products/${productId}`)
}

export function getProductByBarcode(barcode: string): Promise<Product> {
  return api.get<Product>(`/api/products/barcode/${encodeURIComponent(barcode.trim())}`)
}

export function createProduct(_accessToken: string | null, data: ProductCreatePayload): Promise<Product> {
  return api.post<Product>('/api/products', data)
}

export function updateProduct(
  _accessToken: string | null,
  productId: string,
  data: ProductUpdatePayload,
): Promise<Product> {
  return api.put<Product>(`/api/products/${productId}`, data)
}

export function deactivateProduct(_accessToken: string | null, productId: string): Promise<Product> {
  return api.delete<Product>(`/api/products/${productId}`)
}
