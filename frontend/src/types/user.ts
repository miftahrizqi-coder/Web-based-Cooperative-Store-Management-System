import type { UserRole } from './auth'

export interface User {
  id: string
  username: string
  email: string
  name: string
  role: UserRole
  is_active: boolean
}