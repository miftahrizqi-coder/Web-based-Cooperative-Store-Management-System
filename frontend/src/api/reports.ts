import type { SalesReport } from '../types/salesReport'

export interface SalesReportParams {
  start_date?: string
  end_date?: string
  cashier_id?: string
  product_id?: string
  category_id?: string
  member_id?: string
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
      const message = data.detail
        .map((item: { msg?: string }) => item.msg)
        .filter(Boolean)
        .join(', ')

      if (message) {
        return message
      }
    }
  } catch {
    // Ignore invalid response body.
  }

  return fallback
}

export async function getSalesReport(
  accessToken: string,
  params: SalesReportParams = {},
): Promise<SalesReport> {
  const query = new URLSearchParams()

  if (params.start_date) {
    query.set('start_date', params.start_date)
  }

  if (params.end_date) {
    query.set('end_date', params.end_date)
  }

  if (params.cashier_id) {
    query.set('cashier_id', params.cashier_id)
  }

  if (params.product_id) {
    query.set('product_id', params.product_id)
  }

  if (params.category_id) {
    query.set('category_id', params.category_id)
  }

  if (params.member_id) {
    query.set('member_id', params.member_id)
  }

  const queryString = query.toString()

  const response = await fetch(
    `/api/reports/sales${queryString ? `?${queryString}` : ''}`,
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
        'Laporan penjualan gagal dimuat.',
      ),
    )
  }

  return response.json() as Promise<SalesReport>
}