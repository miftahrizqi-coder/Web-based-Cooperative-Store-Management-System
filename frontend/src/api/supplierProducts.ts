import type {
  CreateSupplierProductRequest,
  SupplierProduct,
  UpdateSupplierProductRequest,
} from '../types/supplierProduct'

const API_BASE = '/api/supplier-products'

function getToken() {
  return localStorage.getItem('access_token')
}

async function request<T>(
  url: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken()

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {}),
      ...(options.headers || {}),
    },
  })

  if (!response.ok) {
    let message = 'Terjadi kesalahan.'

    try {
      const data = await response.json()
      message =
        typeof data.detail === 'string'
          ? data.detail
          : message
    } catch {
      // Keep default message.
    }

    throw new Error(message)
  }

  return response.json()
}

export function getSupplierProducts(params?: {
  supplierId?: string
  productId?: string
  isActive?: boolean
}) {
  const searchParams = new URLSearchParams()

  if (params?.supplierId) {
    searchParams.set('supplier_id', params.supplierId)
  }

  if (params?.productId) {
    searchParams.set('product_id', params.productId)
  }

  if (params?.isActive !== undefined) {
    searchParams.set('is_active', String(params.isActive))
  }

  const query = searchParams.toString()

  return request<SupplierProduct[]>(
    `${API_BASE}${query ? `?${query}` : ''}`,
  )
}

export function getSupplierProduct(id: string) {
  return request<SupplierProduct>(`${API_BASE}/${id}`)
}

export function createSupplierProduct(
  payload: CreateSupplierProductRequest,
) {
  return request<SupplierProduct>(API_BASE, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateSupplierProduct(
  id: string,
  payload: UpdateSupplierProductRequest,
) {
  return request<SupplierProduct>(`${API_BASE}/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function updateSupplierProductStatus(
  id: string,
  isActive: boolean,
) {
  return request<SupplierProduct>(`${API_BASE}/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({
      isActive,
    }),
  })
}