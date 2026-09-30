import type {
  POSMember,
  POSProduct,
  CreateSalePayload,
  SaleResponse,
} from '../types/pos'

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

export async function searchPOSProducts(
  accessToken: string,
  search: string,
): Promise<POSProduct[]> {
  const searchParams = new URLSearchParams()

  if (search.trim()) {
    searchParams.set('search', search.trim())
  }

  const query = searchParams.toString()

  const response = await fetch(
    `/api/products${query ? `?${query}` : ''}`,
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
        'Gagal mencari produk.',
      ),
    )
  }

  return response.json()
}

export async function getPOSProductByBarcode(
  accessToken: string,
  barcode: string,
): Promise<POSProduct> {
  const response = await fetch(
    `/api/products/barcode/${encodeURIComponent(barcode)}`,
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
        'Produk dengan barcode tersebut tidak ditemukan.',
      ),
    )
  }

  return response.json()
}

export async function searchPOSMembers(
  accessToken: string,
  search: string,
): Promise<POSMember[]> {
  const searchParams = new URLSearchParams()

  if (search.trim()) {
    searchParams.set('search', search.trim())
  }

  const query = searchParams.toString()

  const response = await fetch(
    `/api/members${query ? `?${query}` : ''}`,
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
        'Gagal mencari anggota.',
      ),
    )
  }

  return response.json()
}

export async function createSale(
  accessToken: string,
  payload: CreateSalePayload,
): Promise<SaleResponse> {
  const response = await fetch('/api/sales', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let message = 'Gagal membuat transaksi penjualan.'

    try {
      const data = await response.json()

      if (typeof data?.detail === 'string') {
        message = data.detail
      }
    } catch {
      // Gunakan pesan default jika response bukan JSON.
    }

    throw new Error(message)
  }

  return response.json()
}