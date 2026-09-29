export type PurchaseOrderStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'ORDERED'
  | 'PARTIALLY_RECEIVED'
  | 'RECEIVED'
  | 'COMPLETED'
  | 'CANCELLED'

export interface PurchaseOrderItem {
  supplierProductId: string
  productId: string
  sku: string
  name: string
  quantity: number
  unitPrice: number
  subtotal: number
}

export interface PurchaseOrder {
  id: string
  poNumber: string
  supplierId: string
  items: PurchaseOrderItem[]
  subtotal: number
  discount: number
  tax: number
  shippingCost: number
  grandTotal: number
  status: PurchaseOrderStatus
  expectedDeliveryDate: string | null
  createdBy: string
  approvedBy: string | null
  approvedAt: string | null
  createdAt: string
  updatedAt: string
}

export interface PurchaseOrderItemPayload {
  supplierProductId: string
  productId: string
  sku: string
  name: string
  quantity: number
  unitPrice: number
}

export interface PurchaseOrderPayload {
  supplierId: string
  items: PurchaseOrderItemPayload[]
  discount: number
  tax: number
  shippingCost: number
  expectedDeliveryDate: string | null
}