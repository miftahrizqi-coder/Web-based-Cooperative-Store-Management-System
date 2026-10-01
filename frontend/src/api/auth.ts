import { apiRequest } from '../services/api'
import type { CurrentUser } from '../types/auth'

interface LoginResponse {
  user: CurrentUser
  token: string
}

export function login(username: string, password: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: { username, password },
    skipAuthRedirect: true,
  })
}

export async function getCurrentUser(accessToken: string): Promise<CurrentUser> {
  const response = await fetch('/api/auth/me', {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!response.ok) {
    throw new Error('Sesi login tidak valid.')
  }
  return response.json()
}

export function changePassword(currentPassword: string, newPassword: string) {
  return apiRequest<{ message: string; token: string }>('/api/auth/password', {
    method: 'PUT',
    body: { current_password: currentPassword, new_password: newPassword },
  })
}
