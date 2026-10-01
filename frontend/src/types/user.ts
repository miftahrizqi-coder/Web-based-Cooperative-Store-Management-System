import type { UserRole } from './auth'

export interface User {
  id: string
  username: string
  email: string
  name: string
  role: UserRole
  is_active: boolean
  memberId: string | null
  lastLoginAt: string | null
  createdAt: string | null
  updatedAt: string | null
}
