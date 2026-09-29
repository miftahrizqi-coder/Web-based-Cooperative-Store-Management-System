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
  {
    label: 'Purchase Order',
    to: '/purchase-orders',
    roles: ['admin', 'pengurus'],
  },
  {
    label: 'Supplier',
    to: '/suppliers',
    roles: ['admin', 'pengurus'],
  },
  {
    label: 'Produk Supplier',
    to: '/supplier-products',
    roles: ['admin', 'pengurus'],
  },
  {
    label: 'Penerimaan Barang',
    to: '/goods-receipts',
    roles: ['admin', 'pengurus'],
  },
  {
    label: 'Purchase',
    to: '/purchases',
    roles: ['admin', 'pengurus'],
  },
    {
    label: 'Supplier Invoices',
    to: '/supplier-invoices',
    roles: ['admin', 'pengurus'],
  },
  {
    label: 'Hutang Supplier',
    to: '/supplier-payables',
    roles: ['admin', 'pengurus'],
  },
  {
    label: 'Pembayaran Supplier',
    to: '/supplier-payments',
    roles: ['admin', 'pengurus'],
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