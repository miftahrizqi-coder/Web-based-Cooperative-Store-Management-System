import type { UserRole } from '../types/auth'

export interface NavigationItem {
  label: string
  to: string
  roles: UserRole[]
}

const ADMIN: UserRole[] = ['admin']
const ADMIN_PENGURUS: UserRole[] = ['admin', 'pengurus']
const STAFF: UserRole[] = ['admin', 'pengurus', 'kasir']
const ALL: UserRole[] = ['admin', 'pengurus', 'kasir', 'anggota']

/**
 * Urutan & pengelompokan mengikuti modul PRD §7. Pengelompokan visual
 * dilakukan di AppLayout berdasarkan prefix path.
 */
export const navigationItems: NavigationItem[] = [
  { label: 'Dashboard', to: '/dashboard', roles: STAFF },

  // Master data
  { label: 'Produk', to: '/products', roles: ADMIN },
  { label: 'Kategori', to: '/categories', roles: ADMIN },
  { label: 'Supplier', to: '/suppliers', roles: ADMIN_PENGURUS },
  { label: 'Produk Supplier', to: '/supplier-products', roles: ADMIN_PENGURUS },
  { label: 'Anggota', to: '/members', roles: ADMIN_PENGURUS },

  // Pengadaan
  { label: 'Purchase Order', to: '/purchase-orders', roles: ADMIN_PENGURUS },
  { label: 'Penerimaan Barang', to: '/goods-receipts', roles: ADMIN_PENGURUS },
  { label: 'Pembelian', to: '/purchases', roles: ADMIN_PENGURUS },
  { label: 'Invoice Supplier', to: '/supplier-invoices', roles: ADMIN_PENGURUS },
  { label: 'Hutang Supplier', to: '/supplier-payables', roles: ADMIN_PENGURUS },
  { label: 'Pembayaran Supplier', to: '/supplier-payments', roles: ADMIN_PENGURUS },
  { label: 'Timeline Pengadaan', to: '/activities', roles: ADMIN_PENGURUS },

  // Inventory
  { label: 'Stok', to: '/inventory', roles: ADMIN_PENGURUS },
  { label: 'Stock Movement', to: '/inventory/movements', roles: ADMIN_PENGURUS },
  { label: 'Stock Adjustment', to: '/inventory/adjustment', roles: ADMIN_PENGURUS },
  { label: 'Stock Opname', to: '/inventory/stock-opname', roles: ADMIN_PENGURUS },

  // Penjualan
  { label: 'POS / Kasir', to: '/pos', roles: ['admin', 'kasir'] },
  { label: 'Riwayat Penjualan', to: '/sales', roles: STAFF },
  { label: 'Retur', to: '/returns', roles: STAFF },

  // Keuangan
  { label: 'Pengeluaran', to: '/expenses', roles: ADMIN_PENGURUS },

  // Laporan
  { label: 'Laporan Penjualan', to: '/reports/sales', roles: ADMIN_PENGURUS },
  { label: 'Laporan Pembelian', to: '/reports/purchases', roles: ADMIN_PENGURUS },
  { label: 'Laporan Inventory', to: '/reports/inventory', roles: ADMIN_PENGURUS },
  { label: 'Laporan Supplier', to: '/reports/suppliers', roles: ADMIN_PENGURUS },
  { label: 'Laporan Hutang', to: '/reports/payables', roles: ADMIN_PENGURUS },
  { label: 'Laporan Laba', to: '/reports/profit', roles: ADMIN_PENGURUS },

  // Administrasi
  { label: 'Pengguna', to: '/users', roles: ADMIN },
  { label: 'Audit Log', to: '/audit-logs', roles: ADMIN },

  // Akun
  { label: 'Profil Saya', to: '/profile', roles: ALL },
]

export function getLandingPage(role: UserRole): string {
  switch (role) {
    case 'admin':
    case 'pengurus':
    case 'kasir':
      return '/dashboard'
    case 'anggota':
      return '/profile'
    default:
      return '/login'
  }
}

export function getNavigationItems(role: UserRole) {
  return navigationItems.filter((item) => item.roles.includes(role))
}
