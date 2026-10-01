export type ReturnType = 'SALE' | 'PURCHASE'
export type ReturnStatus = 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED'
export type ReturnReason = 'BARANG_RUSAK' | 'SALAH_BARANG' | 'SALAH_JUMLAH' | 'LAINNYA'

export const RETURN_REASON_LABELS: Record<ReturnReason, string> = {
  BARANG_RUSAK: 'Barang rusak',
  SALAH_BARANG: 'Salah barang',
  SALAH_JUMLAH: 'Salah jumlah',
  LAINNYA: 'Lainnya',
}

export const RETURN_STATUS_LABELS: Record<ReturnStatus, string> = {
  PENDING_APPROVAL: 'Menunggu approval',
  APPROVED: 'Disetujui',
  REJECTED: 'Ditolak',
}

export interface ReturnItem {
  productId: string
  sku: string
  name: string
  quantity: number
  price: number
  subtotal: number
}

export interface ReturnRecord {
  id: string
  returnNumber: string
  type: ReturnType
  status: ReturnStatus
  saleId: string | null
  saleInvoiceNumber: string | null
  memberId: string | null
  supplierId: string | null
  supplierName: string | null
  purchaseOrderId: string | null
  receiptId: string | null
  receiptNumber: string | null
  supplierInvoiceId: string | null
  items: ReturnItem[]
  totalAmount: number
  reason: ReturnReason
  notes: string | null
  createdBy: string
  createdByName: string | null
  approvedBy: string | null
  approvedByName: string | null
  approvedAt: string | null
  rejectionReason: string | null
  createdAt: string
  updatedAt: string
}

export interface ReturnItemPayload {
  productId: string
  quantity: number
}

export interface SalesReturnPayload {
  saleId: string | null
  invoiceNumber: string | null
  items: ReturnItemPayload[]
  reason: ReturnReason
  notes: string | null
}

export interface PurchaseReturnPayload {
  receiptId: string
  items: ReturnItemPayload[]
  reason: ReturnReason
  notes: string | null
}
