import type {
  InventoryItem,
  StockStatus,
} from '../types/inventory'

interface InventoryParams {
  search?: string
  stock_status?: StockStatus
}

async function getErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const data = await response.json()

    if (typeof data?.detail === 'string') {
      return data.detail
    }

    if (Array.isArray(data?.detail)) {
      return data.detail
        .map((item: { msg?: string }) => item.msg)
        .filter(Boolean)
        .join(', ')
    }
  } catch {
    // Ignore invalid error response body.
  }

  return fallback
}

export async function getInventory(
  accessToken: string,
  params?: InventoryParams,
): Promise<InventoryItem[]> {
  const searchParams = new URLSearchParams()

  if (params?.search) {
    searchParams.set('search', params.search)
  }

  if (params?.stock_status) {
    searchParams.set(
      'stock_status',
      params.stock_status,
    )
  }

  const query = searchParams.toString()

  const response = await fetch(
    `/api/inventory${query ? `?${query}` : ''}`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal mengambil data stok.',
      ),
    )
  }

  return response.json()
}