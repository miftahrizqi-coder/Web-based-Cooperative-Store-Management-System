import type { CurrentUser } from '../types/auth'

interface LoginResponse {
  user: CurrentUser
  token: string
}

export async function login(
  username: string,
  password: string,
): Promise<LoginResponse> {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username,
      password,
    }),
  })

  if (!response.ok) {
    throw new Error('Username atau password tidak valid.')
  }

  return response.json()
}