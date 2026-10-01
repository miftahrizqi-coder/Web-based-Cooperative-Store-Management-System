export interface AuditLog {
  id: string
  userId: string | null
  userName: string | null
  action: string
  module: string
  referenceId: string | null
  description: string
  metadata: Record<string, unknown> | null
  ipAddress: string | null
  createdAt: string
}

export const AUDIT_ACTIONS = [
  'LOGIN', 'LOGIN_FAILED', 'LOGOUT', 'CREATE', 'UPDATE', 'DELETE', 'SALE', 'CANCEL',
  'PURCHASE', 'STOCK_ADJUSTMENT', 'STOCK_OPNAME', 'RETURN', 'APPROVE', 'REJECT',
  'PAYMENT', 'PASSWORD_CHANGE', 'PASSWORD_RESET',
] as const

export const AUDIT_MODULES = [
  'AUTH', 'USER', 'CATEGORY', 'PRODUCT', 'SUPPLIER', 'SUPPLIER_PRODUCT', 'MEMBER',
  'PURCHASE_ORDER', 'GOODS_RECEIPT', 'PURCHASE', 'SUPPLIER_INVOICE', 'SUPPLIER_PAYMENT',
  'INVENTORY', 'SALE', 'RETURN', 'EXPENSE',
] as const
