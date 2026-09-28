import type { User } from '../types/user'

export async function getUsers(
  accessToken: string,
): Promise<User[]> {
  const response = await fetch('/api/users', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error('Gagal mengambil data pengguna.')
  }

  return response.json()
}