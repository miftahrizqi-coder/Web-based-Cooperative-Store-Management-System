// Fungsi khusus layar POS (kasir).
import { api } from '../services/api'
import type { Member } from '../types/member'
import type { Product } from '../types/product'

export { createSale } from './sales'

export function searchPOSProducts(search: string): Promise<Product[]> {
  return api.get<Product[]>('/api/products', { search: search.trim(), stockStatus: undefined })
}

export function getPOSProductByBarcode(barcode: string): Promise<Product> {
  return api.get<Product>(`/api/products/barcode/${encodeURIComponent(barcode.trim())}`)
}

export function searchPOSMembers(search: string): Promise<Member[]> {
  return api.get<Member[]>('/api/members', { search: search.trim() })
}
