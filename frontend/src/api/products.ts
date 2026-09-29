import type { Product, ProductStockStatus } from '../types/product'

export interface ProductPayload {
  sku: string
  barcode: string | null
  name: string
  category_id: string
  unit: string
  purchase_price: number
  selling_price: number
  stock: number
  minimum_stock: number
}

export interface ProductUpdatePayload extends ProductPayload {
  is_active: boolean
}

function authHeaders(accessToken: string) {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${accessToken}`,
  }
}

async function getErrorMessage(response: Response, fallback: string) {
  try {
    const body = await response.json()
    if (typeof body?.detail === 'string') {
      return body.detail
    }
  } catch {
    // Ignore malformed error bodies.
  }

  return fallback
}

export async function getProducts(
  accessToken: string,
  params: {
    search?: string
    categoryId?: string
    stockStatus?: ProductStockStatus
  } = {},
): Promise<Product[]> {
  const query = new URLSearchParams()

  if (params.search?.trim()) {
    query.set('search', params.search.trim())
  }

  if (params.categoryId?.trim()) {
    query.set('category_id', params.categoryId.trim())
  }

  if (params.stockStatus && params.stockStatus !== 'all') {
    query.set('stock_status', params.stockStatus)
  }

  const suffix = query.toString() ? `?${query.toString()}` : ''
  const response = await fetch(`/api/products${suffix}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'Gagal mengambil data produk.'),
    )
  }

  return response.json()
}

export async function getProduct(
  accessToken: string,
  productId: string,
): Promise<Product> {
  const response = await fetch(`/api/products/${productId}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'Gagal mengambil detail produk.'),
    )
  }

  return response.json()
}

export async function createProduct(
  accessToken: string,
  data: ProductPayload,
): Promise<Product> {
  const response = await fetch('/api/products', {
    method: 'POST',
    headers: authHeaders(accessToken),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'Gagal membuat produk.'),
    )
  }

  return response.json()
}

export async function updateProduct(
  accessToken: string,
  productId: string,
  data: ProductUpdatePayload,
): Promise<Product> {
  const response = await fetch(`/api/products/${productId}`, {
    method: 'PUT',
    headers: authHeaders(accessToken),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'Gagal memperbarui produk.'),
    )
  }

  return response.json()
}

export async function deactivateProduct(
  accessToken: string,
  productId: string,
): Promise<Product> {
  const response = await fetch(`/api/products/${productId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'Gagal menonaktifkan produk.'),
    )
  }

  return response.json()
}
