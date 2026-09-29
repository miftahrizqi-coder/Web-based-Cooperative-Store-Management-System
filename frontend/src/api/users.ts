import type { UserRole } from '../types/auth'
import type { User } from '../types/user'

interface CreateUserRequest {
  username: string
  email: string
  password: string
  name: string
  role: UserRole
}

export interface UpdateUserRequest {
  email: string
  name: string
  role: UserRole
  is_active: boolean
}

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

export async function getUser(
  accessToken: string,
  userId: string,
): Promise<User> {
  const response = await fetch(`/api/users/${userId}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Pengguna tidak ditemukan.')
    }

    throw new Error('Gagal mengambil data pengguna.')
  }

  return response.json()
}

export async function createUser(
  accessToken: string,
  data: CreateUserRequest,
): Promise<User> {
  const response = await fetch('/api/users', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    if (response.status === 409) {
      throw new Error('Username atau email sudah digunakan.')
    }

    throw new Error('Gagal membuat pengguna.')
  }

  return response.json()
}

export async function updateUser(
  accessToken: string,
  userId: string,
  data: UpdateUserRequest,
): Promise<User> {
  const response = await fetch(`/api/users/${userId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Pengguna tidak ditemukan.')
    }

    if (response.status === 409) {
      throw new Error('Email sudah digunakan.')
    }

    throw new Error('Gagal memperbarui pengguna.')
  }

  return response.json()
}

export async function deleteUser(
  accessToken: string,
  userId: string,
): Promise<User> {
  const response = await fetch(`/api/users/${userId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Pengguna tidak ditemukan.')
    }

    throw new Error('Gagal menonaktifkan pengguna.')
  }

  return response.json()
}