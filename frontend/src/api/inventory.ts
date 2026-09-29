import type {
  InventoryItem,
  StockMovement,
  StockMovementType,
  StockStatus,
  StockAdjustmentPayload,
  StockAdjustmentResponse,
  StockOpnamePayload,
  StockOpnameResponse,
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

export async function getStockMovements(
  accessToken: string,
  params?: {
    product_id?: string
    movement_type?: StockMovementType
  },
): Promise<StockMovement[]> {
  const searchParams = new URLSearchParams()

  if (params?.product_id) {
    searchParams.set(
      'product_id',
      params.product_id,
    )
  }

  if (params?.movement_type) {
    searchParams.set(
      'movement_type',
      params.movement_type,
    )
  }

  const query = searchParams.toString()

  const response = await fetch(
    `/api/inventory/movements${query ? `?${query}` : ''}`,
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
        'Gagal mengambil riwayat pergerakan stok.',
      ),
    )
  }

  return response.json()
}

export async function createStockAdjustment(
  accessToken: string,
  payload: StockAdjustmentPayload,
): Promise<StockAdjustmentResponse> {
  const response = await fetch(
    '/api/inventory/adjustment',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(payload),
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal membuat stock adjustment.',
      ),
    )
  }

  return response.json()
}

export async function createStockOpname(
  accessToken: string,
  payload: StockOpnamePayload,
): Promise<StockOpnameResponse> {
  const response = await fetch(
    '/api/inventory/stock-opname',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(payload),
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal membuat stock opname.',
      ),
    )
  }

  return response.json()
}