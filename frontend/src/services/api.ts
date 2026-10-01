/**
 * Klien REST terpusat (PRD §40: services/api.ts).
 *
 * - Menyisipkan token Bearer dari store auth.
 * - Mengubah error FastAPI (detail string / array validasi) menjadi pesan
 *   yang dapat ditampilkan.
 * - 401 -> sesi dibersihkan dan pengguna diarahkan ke /login.
 * - Mendukung pagination server via header X-Total-Count.
 */
import { useAuth } from '../stores/auth'

export type QueryValue = string | number | boolean | null | undefined

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  params?: Record<string, QueryValue>
  /** Tidak redirect ke /login saat 401 (dipakai halaman login). */
  skipAuthRedirect?: boolean
}

export interface Paginated<T> {
  items: T[]
  total: number
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function buildUrl(path: string, params?: Record<string, QueryValue>): string {
  const query = new URLSearchParams()
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null || value === '') continue
      query.set(key, String(value))
    }
  }
  const suffix = query.toString()
  return suffix ? `${path}?${suffix}` : path
}

export async function extractErrorMessage(
  response: Response,
  fallback = 'Terjadi kesalahan.',
): Promise<string> {
  try {
    const data = await response.json()
    if (typeof data?.detail === 'string') return data.detail
    if (Array.isArray(data?.detail)) {
      const messages = data.detail
        .map((item: { msg?: string; loc?: unknown[] }) => {
          const field = Array.isArray(item.loc) ? item.loc.slice(1).join('.') : ''
          const msg = (item.msg ?? '').replace(/^Value error, /, '')
          return field ? `${field}: ${msg}` : msg
        })
        .filter(Boolean)
      if (messages.length) return messages.join('; ')
    }
  } catch {
    // body bukan JSON
  }
  if (response.status === 403) return 'Anda tidak memiliki akses untuk aksi ini.'
  if (response.status >= 500) return 'Server mengalami gangguan. Coba lagi beberapa saat.'
  return fallback
}

async function send(path: string, options: RequestOptions = {}): Promise<Response> {
  const { token, clearAuth } = useAuth()
  const headers: Record<string, string> = {}
  if (token.value) headers.Authorization = `Bearer ${token.value}`
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'

  let response: Response
  try {
    response = await fetch(buildUrl(path, options.params), {
      method: options.method ?? 'GET',
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    })
  } catch {
    throw new ApiError('Tidak dapat terhubung ke server. Periksa koneksi Anda.', 0)
  }

  if (response.status === 401 && !options.skipAuthRedirect) {
    clearAuth()
    if (window.location.pathname !== '/login') {
      const redirect = encodeURIComponent(window.location.pathname + window.location.search)
      window.location.assign(`/login?redirect=${redirect}`)
    }
  }

  if (!response.ok) {
    throw new ApiError(await extractErrorMessage(response), response.status)
  }

  return response
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await send(path, options)
  if (response.status === 204) return undefined as T
  const text = await response.text()
  return (text ? JSON.parse(text) : undefined) as T
}

export async function apiPaginated<T>(
  path: string,
  params: Record<string, QueryValue> = {},
): Promise<Paginated<T>> {
  const response = await send(path, { params })
  const items = (await response.json()) as T[]
  const total = Number(response.headers.get('X-Total-Count') ?? items.length)
  return { items, total: Number.isFinite(total) ? total : items.length }
}

export const api = {
  get: <T>(path: string, params?: Record<string, QueryValue>) =>
    apiRequest<T>(path, { params }),
  post: <T>(path: string, body?: unknown) =>
    apiRequest<T>(path, { method: 'POST', body: body ?? {} }),
  put: <T>(path: string, body: unknown) => apiRequest<T>(path, { method: 'PUT', body }),
  patch: <T>(path: string, body: unknown) => apiRequest<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string, params?: Record<string, QueryValue>) =>
    apiRequest<T>(path, { method: 'DELETE', params }),
  paginated: apiPaginated,
}

export function errorMessage(error: unknown, fallback = 'Terjadi kesalahan.'): string {
  return error instanceof Error && error.message ? error.message : fallback
}
