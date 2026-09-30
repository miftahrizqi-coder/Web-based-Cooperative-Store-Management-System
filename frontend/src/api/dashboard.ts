import type { DashboardAnalytics } from '../types/dashboard'

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

export async function getDashboardAnalytics(
  accessToken: string,
  days: 7 | 30 = 7,
): Promise<DashboardAnalytics> {
  const response = await fetch(
    `/api/reports/dashboard?days=${days}`,
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
        'Gagal mengambil data dashboard.',
      ),
    )
  }

  return response.json()
}