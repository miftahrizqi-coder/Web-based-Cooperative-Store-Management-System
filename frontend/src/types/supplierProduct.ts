export interface SupplierProduct {
  id: string
  supplierId: string
  supplierName?: string | null
  productId: string
  productName?: string | null
  productSku?: string | null
  supplierSku: string
  purchasePrice: number
  minimumOrder: number
  leadTimeDays: number
  isPreferred: boolean
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface CreateSupplierProductRequest {
  supplierId: string
  productId: string
  supplierSku: string
  purchasePrice: number
  minimumOrder: number
  leadTimeDays: number
  isPreferred: boolean
  isActive: boolean
}

export interface UpdateSupplierProductRequest {
  supplierSku: string
  purchasePrice: number
  minimumOrder: number
  leadTimeDays: number
  isPreferred: boolean
}