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
  {
    label: 'Pengguna',
    to: '/users',
    roles: ['admin'],
  },
  {
    label: 'Produk',
    to: '/products',
    roles: ['admin'],
  },
]

export function getLandingPage(role: UserRole): string {
  switch (role) {
    case 'admin':
      return '/dashboard'
    case 'kasir':
      return '/dashboard'
    case 'pengurus':
      return '/dashboard'
    case 'anggota':
      return '/dashboard'
    default:
      return '/login'
  }
}

export function getNavigationItems(role: UserRole) {
  return navigationItems.filter((item) =>
    item.roles.includes(role),
  )
}