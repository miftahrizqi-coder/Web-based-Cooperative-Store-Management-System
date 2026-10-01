import { api } from '../services/api'
import type {
  GoodsReceipt,
  Purchase,
  PurchaseOrder,
  SupplierInvoice,
  SupplierPayment,
} from '../types/procurement'
import type { SupplierProduct } from '../types/supplierProduct'
import type {
  CreateSupplierRequest,
  Supplier,
  SupplierStatus,
  UpdateSupplierRequest,
} from '../types/supplier'

async function parseError(
  response: Response,
  fallback: string,
): Promise<never> {
  try {
    const body = await response.json()

    if (typeof body.detail === 'string') {
      throw new Error(body.detail)
    }
  } catch (error) {
    if (error instanceof Error) {
      throw error
    }
  }

  throw new Error(fallback)
}

export async function getSuppliers(
  accessToken: string,
): Promise<Supplier[]> {
  const response = await fetch('/api/suppliers', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    return parseError(
      response,
      'Gagal mengambil data supplier.',
    )
  }

  return response.json()
}


export async function getSupplier(
  accessToken: string,
  supplierId: string,
): Promise<Supplier> {
  const response = await fetch(
    `/api/suppliers/${supplierId}`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  )

  if (!response.ok) {
    return parseError(
      response,
      'Gagal mengambil detail supplier.',
    )
  }

  return response.json()
}


export async function createSupplier(
  accessToken: string,
  data: CreateSupplierRequest,
): Promise<Supplier> {
  const response = await fetch('/api/suppliers', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    return parseError(
      response,
      'Gagal membuat supplier.',
    )
  }

  return response.json()
}


export async function updateSupplier(
  accessToken: string,
  supplierId: string,
  data: UpdateSupplierRequest,
): Promise<Supplier> {
  const response = await fetch(
    `/api/suppliers/${supplierId}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(data),
    },
  )

  if (!response.ok) {
    return parseError(
      response,
      'Gagal memperbarui supplier.',
    )
  }

  return response.json()
}


export async function updateSupplierStatus(
  accessToken: string,
  supplierId: string,
  status: SupplierStatus,
): Promise<Supplier> {
  const response = await fetch(
    `/api/suppliers/${supplierId}/status`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        status,
      }),
    },
  )

  if (!response.ok) {
    return parseError(
      response,
      'Gagal memperbarui status supplier.',
    )
  }

  return response.json()
}
// ---------------------------------------------------------------------------
// Riwayat & hutang supplier (PRD §12, §33)
// ---------------------------------------------------------------------------

export interface SupplierSummary {
  supplierId: string
  productsSupplied: number
  purchaseOrderCount: number
  activePurchaseOrderCount: number
  receiptCount: number
  totalPurchases: number
  invoiceCount: number
  totalInvoiced: number
  totalPaid: number
  totalReturned: number
  outstanding: number
  overdueInvoiceCount: number
}

export const getSupplierSummary = (id: string) => api.get<SupplierSummary>(`/api/suppliers/${id}/summary`)
export const getSupplierProductsOf = (id: string) => api.get<SupplierProduct[]>(`/api/suppliers/${id}/products`)
export const getSupplierPurchaseOrders = (id: string) => api.get<PurchaseOrder[]>(`/api/suppliers/${id}/purchase-orders`)
export const getSupplierReceipts = (id: string) => api.get<GoodsReceipt[]>(`/api/suppliers/${id}/goods-receipts`)
export const getSupplierPurchases = (id: string) => api.get<Purchase[]>(`/api/suppliers/${id}/purchases`)
export const getSupplierInvoicesOf = (id: string) => api.get<SupplierInvoice[]>(`/api/suppliers/${id}/invoices`)
export const getSupplierPaymentsOf = (id: string) => api.get<SupplierPayment[]>(`/api/suppliers/${id}/payments`)
