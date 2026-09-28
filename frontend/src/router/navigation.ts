import type { UserRole } from '../types/auth'

export interface NavigationItem {
  label: string
  to: string
  roles: UserRole[]
}

export const navigationItems: NavigationItem[] = [
  {
    label: 'Dashboard',
    to: '/dashboard',
    roles: ['admin', 'kasir', 'pengurus'],
  },
]