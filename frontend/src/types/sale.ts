export type PaymentMethod = 'CASH' | 'TRANSFER' | 'QRIS' | 'DEBIT' | 'E_WALLET'
export type SaleStatus = 'COMPLETED' | 'CANCELLED'

export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  CASH: 'Tunai',
  TRANSFER: 'Transfer',
  QRIS: 'QRIS',
  DEBIT: 'Debit',
  E_WALLET: 'E-Wallet',
}

export interface SaleItem {
  productId: string
  sku: string
  name: string
  unit: string
  quantity: number
  price: number
  costPrice: number | null
  subtotal: number
  returnedQuantity: number
}

export interface SalePayment {
  method: PaymentMethod
  amount: number
  change: number
  paidAt: string | null
  referenceNumber: string | null
}

export interface Sale {
  id: string
  invoiceNumber: string
  cashierId: string
  cashierName: string | null
  memberId: string | null
  memberName: string | null
  memberNumber: string | null
  items: SaleItem[]
  subtotal: number
  discount: number
  total: number
  payment: SalePayment
  status: SaleStatus
  cancelledBy: string | null
  cancelledAt: string | null
  cancelReason: string | null
  createdAt: string
  updatedAt: string
}

export interface CreateSalePayload {
  items: { productId: string; quantity: number }[]
  memberId: string | null
  discount: number
  payment: {
    method: PaymentMethod
    amount: number | null
    referenceNumber: string | null
  }
}
