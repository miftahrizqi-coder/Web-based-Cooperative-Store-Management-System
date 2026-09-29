export interface POSProduct {
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

export type MemberStatus = 'ACTIVE' | 'INACTIVE'

export interface POSMember {
  id: string
  memberNumber: string
  name: string
  phone: string
  email: string | null
  address: string | null
  joinedAt: string
  status: MemberStatus
  createdAt: string
  updatedAt: string
}

export interface CartItem {
  product: POSProduct
  quantity: number
}

export interface SaleItemPayload {
  productId: string
  quantity: number
}

export type PaymentMethod =
  | 'CASH'
  | 'BANK_TRANSFER'
  | 'DEBIT'
  | 'OTHER'