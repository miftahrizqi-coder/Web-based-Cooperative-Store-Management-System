import { api } from '../services/api'
import type { UserRole } from '../types/auth'
import type { User } from '../types/user'

export interface CreateUserRequest {
  username: string
  email: string
  password: string
  name: string
  role: UserRole
  memberId?: string | null
}

export interface UpdateUserRequest {
  email: string
  name: string
  role: UserRole
  is_active: boolean
  memberId?: string | null
}

// accessToken dipertahankan demi kompatibilitas pemanggil lama.

export function getUsers(_accessToken?: string | null): Promise<User[]> {
  return api.get<User[]>('/api/users')
}

export function getUser(_accessToken: string | null, userId: string): Promise<User> {
  return api.get<User>(`/api/users/${userId}`)
}

export function createUser(_accessToken: string | null, data: CreateUserRequest): Promise<User> {
  return api.post<User>('/api/users', data)
}

export function updateUser(_accessToken: string | null, userId: string, data: UpdateUserRequest): Promise<User> {
  return api.put<User>(`/api/users/${userId}`, data)
}

export function deleteUser(_accessToken: string | null, userId: string): Promise<User> {
  return api.delete<User>(`/api/users/${userId}`)
}

export function resetUserPassword(userId: string, newPassword: string): Promise<User> {
  return api.post<User>(`/api/users/${userId}/reset-password`, { new_password: newPassword })
}
