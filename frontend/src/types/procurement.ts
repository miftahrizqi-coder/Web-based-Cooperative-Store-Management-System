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

export interface GoodsReceiptItem {
  productId: string
  name: string
  orderedQuantity: number
  previouslyReceivedQuantity: number
  receivedQuantity: number
  acceptedQuantity: number
  rejectedQuantity: number
  rejectionReason: string | null
}

export interface GoodsReceipt {
  id: string
  receiptNumber: string
  purchaseOrderId: string
  supplierId: string
  items: GoodsReceiptItem[]
  receivedBy: string
  receivedAt: string
  notes: string | null
  createdAt: string
  updatedAt: string
}

export interface GoodsReceiptItemPayload {
  productId: string
  name: string
  receivedQuantity: number
  acceptedQuantity: number
  rejectedQuantity: number
  rejectionReason: string | null
}

export interface GoodsReceiptPayload {
  purchaseOrderId: string
  items: GoodsReceiptItemPayload[]
  notes: string | null
}

export type PaymentStatus =
  | 'UNPAID'
  | 'PARTIALLY_PAID'
  | 'PAID'
  | 'OVERDUE'

export interface PurchaseItem {
  productId: string
  name: string
  quantity: number
  price: number
  subtotal: number
}

export interface Purchase {
  id: string
  purchaseNumber: string
  supplierId: string
  purchaseOrderId: string
  receiptId: string
  items: PurchaseItem[]
  subtotal: number
  discount: number
  total: number
  paymentStatus: PaymentStatus
  createdBy: string
  createdAt: string
}

export interface PurchasePayload {
  receiptId: string
  discount: number
}

export type SupplierInvoicePaymentStatus =
  | 'UNPAID'
  | 'PARTIALLY_PAID'
  | 'PAID'
  | 'OVERDUE'

export interface SupplierInvoice {
  id: string
  invoiceNumber: string
  supplierId: string
  purchaseId: string
  purchaseOrderId: string
  receiptId: string
  subtotal: number
  tax: number
  shipping: number
  total: number
  paymentStatus: SupplierInvoicePaymentStatus
  invoiceDate: string
  dueDate: string | null
  createdBy: string
  createdAt: string
}

export interface SupplierInvoicePayload {
  receiptId: string
  invoiceNumber: string
  invoiceDate: string
  dueDate: string
  tax: number
  shippingCost: number
}

export interface SupplierPayable {
  invoiceId: string
  invoiceNumber: string
  supplierId: string
  total: number
  paid: number
  outstanding: number
  paymentStatus: PaymentStatus
  dueDate: string
}