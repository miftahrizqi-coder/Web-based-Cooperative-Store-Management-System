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
  receivedQuantity?: number
  acceptedQuantity?: number
  remainingQuantity?: number
}

export interface PurchaseOrder {
  id: string
  poNumber: string
  supplierId: string
  supplierName?: string | null
  items: PurchaseOrderItem[]
  subtotal: number
  discount: number
  tax: number
  shippingCost: number
  grandTotal: number
  status: PurchaseOrderStatus
  expectedDeliveryDate: string | null
  notes?: string | null
  createdBy: string
  submittedAt?: string | null
  approvedBy: string | null
  approvedAt: string | null
  orderedAt?: string | null
  completedAt?: string | null
  cancelledAt?: string | null
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
  sku?: string
  name: string
  unitPrice?: number
  returnedQuantity?: number
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
  poNumber?: string | null
  supplierId: string
  supplierName?: string | null
  items: GoodsReceiptItem[]
  receivedBy: string
  receivedAt: string
  notes: string | null
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
  supplierName?: string | null
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
  supplierName?: string | null
  purchaseOrderId: string
  receiptId: string
  subtotal: number
  tax: number
  shippingCost: number
  total: number
  returnedAmount: number
  paidAmount: number
  outstanding: number
  isOverdue: boolean
  paymentStatus: SupplierInvoicePaymentStatus
  invoiceDate: string
  dueDate: string
  notes?: string | null
  createdAt: string
  updatedAt: string
}

export interface SupplierInvoicePayload {
  receiptId: string
  invoiceNumber: string
  invoiceDate: string
  /** Kosong = invoiceDate + termin pembayaran supplier. */
  dueDate: string | null
  tax: number
  shippingCost: number
  notes?: string | null
}

export interface SupplierPayable {
  invoiceId: string
  invoiceNumber: string
  supplierId: string
  supplierName?: string | null
  invoiceDate?: string | null
  total: number
  returned: number
  paid: number
  outstanding: number
  paymentStatus: PaymentStatus
  dueDate: string
  isOverdue: boolean
  daysOverdue: number
}

// PRD §19
export type SupplierPaymentMethod =
  | 'CASH'
  | 'BANK_TRANSFER'
  | 'DEBIT'
  | 'OTHER'

export interface SupplierPayment {
  id: string
  supplierId: string
  supplierName?: string | null
  invoiceId: string
  invoiceNumber?: string | null
  paymentNumber: string
  amount: number
  method: SupplierPaymentMethod
  paymentDate: string
  referenceNumber: string | null
  createdBy: string
  notes: string | null
  createdAt: string
}

export interface SupplierPaymentPayload {
  invoiceId: string
  amount: number
  method: SupplierPaymentMethod
  paymentDate: string
  referenceNumber: string | null
  notes: string | null
}

export type ActivityEntityType =
  | 'PURCHASE_ORDER'
  | 'GOODS_RECEIPT'
  | 'PURCHASE'
  | 'SUPPLIER_INVOICE'
  | 'SUPPLIER_PAYMENT'

export type ActivityType =
  | 'CREATED'
  | 'UPDATED'
  | 'SUBMITTED'
  | 'APPROVED'
  | 'ORDERED'
  | 'RECEIVED'
  | 'COMPLETED'
  | 'PAID'
  | 'CANCELLED'

export interface Activity {
  id: string
  entityType: ActivityEntityType
  entityId: string
  activityType: ActivityType
  referenceNumber: string | null
  description: string
  actorId: string
  createdAt: string
}