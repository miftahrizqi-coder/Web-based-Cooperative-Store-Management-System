import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuth } from '../stores/auth'
import type { UserRole } from '../types/auth'
import { getLandingPage } from './navigation'

declare module 'vue-router' {
  interface RouteMeta {
    guestOnly?: boolean
    public?: boolean
    roles?: UserRole[]
    title?: string
  }
}

const ADMIN: UserRole[] = ['admin']
const ADMIN_PENGURUS: UserRole[] = ['admin', 'pengurus']
const STAFF: UserRole[] = ['admin', 'pengurus', 'kasir']
const ALL: UserRole[] = ['admin', 'pengurus', 'kasir', 'anggota']

const page = (loader: () => Promise<unknown>, roles: UserRole[], title: string) => ({
  component: loader as RouteRecordRaw['component'],
  meta: { roles, title },
})

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/login',
    component: () => import('../pages/auth/LoginPage.vue'),
    meta: { guestOnly: true, public: true, title: 'Login' },
  },

  { path: '/dashboard', ...page(() => import('../pages/dashboard/DashboardPage.vue'), STAFF, 'Dashboard') },
  { path: '/profile', ...page(() => import('../pages/profile/ProfilePage.vue'), ALL, 'Profil') },

  // Pengguna
  { path: '/users', ...page(() => import('../pages/users/UsersPage.vue'), ADMIN, 'Pengguna') },
  { path: '/users/create', ...page(() => import('../pages/users/UserCreatePage.vue'), ADMIN, 'Tambah Pengguna') },
  { path: '/users/:id/edit', ...page(() => import('../pages/users/UserEditPage.vue'), ADMIN, 'Ubah Pengguna') },

  // Produk & kategori
  { path: '/products', ...page(() => import('../pages/products/ProductsPage.vue'), ADMIN, 'Produk') },
  { path: '/products/create', ...page(() => import('../pages/products/ProductFormPage.vue'), ADMIN, 'Tambah Produk') },
  { path: '/products/:id', ...page(() => import('../pages/products/ProductDetailPage.vue'), ADMIN, 'Detail Produk') },
  { path: '/products/:id/edit', ...page(() => import('../pages/products/ProductFormPage.vue'), ADMIN, 'Ubah Produk') },
  { path: '/categories', ...page(() => import('../pages/categories/CategoriesPage.vue'), ADMIN, 'Kategori') },

  // Supplier
  { path: '/suppliers', ...page(() => import('../pages/suppliers/SuppliersPage.vue'), ADMIN_PENGURUS, 'Supplier') },
  { path: '/suppliers/create', ...page(() => import('../pages/suppliers/SupplierFormPage.vue'), ADMIN_PENGURUS, 'Tambah Supplier') },
  { path: '/suppliers/:id/edit', ...page(() => import('../pages/suppliers/SupplierFormPage.vue'), ADMIN_PENGURUS, 'Ubah Supplier') },
  {
    path: '/suppliers/:id/products',
    redirect: (to) => ({ path: '/supplier-products', query: { supplierId: String(to.params.id) } }),
  },
  { path: '/suppliers/:id', ...page(() => import('../pages/suppliers/SupplierDetailPage.vue'), ADMIN_PENGURUS, 'Detail Supplier') },
  { path: '/supplier-products', ...page(() => import('../pages/supplierProducts/SupplierProductsPage.vue'), ADMIN_PENGURUS, 'Produk Supplier') },
  { path: '/supplier-products/create', ...page(() => import('../pages/supplierProducts/SupplierProductFormPage.vue'), ADMIN_PENGURUS, 'Tambah Produk Supplier') },
  { path: '/supplier-products/:id/edit', ...page(() => import('../pages/supplierProducts/SupplierProductFormPage.vue'), ADMIN_PENGURUS, 'Ubah Produk Supplier') },

  // Anggota
  { path: '/members', ...page(() => import('../pages/members/MembersPage.vue'), ADMIN_PENGURUS, 'Anggota') },
  { path: '/members/create', ...page(() => import('../pages/members/MemberFormPage.vue'), ADMIN, 'Tambah Anggota') },
  { path: '/members/:id', ...page(() => import('../pages/members/MemberDetailPage.vue'), ADMIN_PENGURUS, 'Detail Anggota') },
  { path: '/members/:id/edit', ...page(() => import('../pages/members/MemberFormPage.vue'), ADMIN, 'Ubah Anggota') },

  // Pengadaan
  { path: '/purchase-orders', ...page(() => import('../pages/procurement/PurchaseOrdersPage.vue'), ADMIN_PENGURUS, 'Purchase Order') },
  { path: '/purchase-orders/create', ...page(() => import('../pages/procurement/PurchaseOrderFromPage.vue'), ADMIN_PENGURUS, 'Buat PO') },
  { path: '/purchase-orders/:id', ...page(() => import('../pages/procurement/PurchaseOrderDetailPage.vue'), ADMIN_PENGURUS, 'Detail PO') },
  { path: '/purchase-orders/:id/edit', ...page(() => import('../pages/procurement/PurchaseOrderFromPage.vue'), ADMIN_PENGURUS, 'Ubah PO') },
  { path: '/goods-receipts', ...page(() => import('../pages/procurement/GoodsReceiptListPage.vue'), ADMIN_PENGURUS, 'Penerimaan Barang') },
  { path: '/goods-receipts/create', ...page(() => import('../pages/procurement/GoodsReceiptFormPage.vue'), ADMIN_PENGURUS, 'Terima Barang') },
  { path: '/goods-receipts/create/:id', ...page(() => import('../pages/procurement/GoodsReceiptFormPage.vue'), ADMIN_PENGURUS, 'Terima Barang') },
  { path: '/goods-receipts/:id', ...page(() => import('../pages/procurement/GoodsReceiptDetailPage.vue'), ADMIN_PENGURUS, 'Detail Penerimaan') },
  { path: '/purchases', ...page(() => import('../pages/procurement/PurchaseListPage.vue'), ADMIN_PENGURUS, 'Pembelian') },
  { path: '/purchases/create', ...page(() => import('../pages/procurement/PurchaseCreatePage.vue'), ADMIN_PENGURUS, 'Catat Pembelian') },
  { path: '/purchases/:id', ...page(() => import('../pages/procurement/PurchaseDetailPage.vue'), ADMIN_PENGURUS, 'Detail Pembelian') },
  { path: '/supplier-invoices', ...page(() => import('../pages/procurement/SupplierInvoiceListPage.vue'), ADMIN_PENGURUS, 'Invoice Supplier') },
  { path: '/supplier-invoices/create', ...page(() => import('../pages/procurement/SupplierInvoiceCreatePage.vue'), ADMIN_PENGURUS, 'Catat Invoice') },
  { path: '/supplier-invoices/:id', ...page(() => import('../pages/procurement/SupplierInvoiceDetailPage.vue'), ADMIN_PENGURUS, 'Detail Invoice') },
  { path: '/supplier-payables', ...page(() => import('../pages/procurement/SupplierPayableListPage.vue'), ADMIN_PENGURUS, 'Hutang Supplier') },
  { path: '/supplier-payments', ...page(() => import('../pages/procurement/SupplierPaymentListPage.vue'), ADMIN_PENGURUS, 'Pembayaran Supplier') },
  { path: '/supplier-payments/create', ...page(() => import('../pages/procurement/SupplierPaymentCreatePage.vue'), ADMIN_PENGURUS, 'Catat Pembayaran') },
  { path: '/activities', ...page(() => import('../pages/activity/ActivityListPage.vue'), ADMIN_PENGURUS, 'Timeline Pengadaan') },

  // Inventory
  { path: '/inventory', ...page(() => import('../pages/inventory/InventoryListPage.vue'), ADMIN_PENGURUS, 'Stok') },
  { path: '/inventory/movements', ...page(() => import('../pages/inventory/StockMovementListPage.vue'), ADMIN_PENGURUS, 'Stock Movement') },
  { path: '/inventory/adjustment', ...page(() => import('../pages/inventory/StockAdjustmentPage.vue'), ADMIN_PENGURUS, 'Stock Adjustment') },
  { path: '/inventory/stock-opname', ...page(() => import('../pages/inventory/StockOpnamePage.vue'), ADMIN_PENGURUS, 'Stock Opname') },

  // Penjualan
  { path: '/pos', ...page(() => import('../pages/POS/POSPage.vue'), ['admin', 'kasir'], 'POS') },
  { path: '/sales', ...page(() => import('../pages/sales/SalesPage.vue'), STAFF, 'Riwayat Penjualan') },
  { path: '/sales/:id', ...page(() => import('../pages/sales/SaleDetailPage.vue'), STAFF, 'Detail Penjualan') },
  { path: '/returns', ...page(() => import('../pages/returns/ReturnsPage.vue'), STAFF, 'Retur') },
  { path: '/returns/create', ...page(() => import('../pages/returns/ReturnCreatePage.vue'), STAFF, 'Buat Retur') },

  // Keuangan
  { path: '/expenses', ...page(() => import('../pages/expenses/ExpensesPage.vue'), ADMIN_PENGURUS, 'Pengeluaran') },

  // Laporan
  { path: '/reports', redirect: '/reports/sales' },
  { path: '/reports/sales', ...page(() => import('../pages/reports/SalesReportPage.vue'), ADMIN_PENGURUS, 'Laporan Penjualan') },
  { path: '/reports/purchases', ...page(() => import('../pages/reports/PurchasesReportPage.vue'), ADMIN_PENGURUS, 'Laporan Pembelian') },
  { path: '/reports/inventory', ...page(() => import('../pages/reports/InventoryReportPage.vue'), ADMIN_PENGURUS, 'Laporan Inventory') },
  { path: '/reports/suppliers', ...page(() => import('../pages/reports/SuppliersReportPage.vue'), ADMIN_PENGURUS, 'Laporan Supplier') },
  { path: '/reports/payables', ...page(() => import('../pages/reports/PayablesReportPage.vue'), ADMIN_PENGURUS, 'Laporan Hutang') },
  { path: '/reports/profit', ...page(() => import('../pages/reports/ProfitReportPage.vue'), ADMIN_PENGURUS, 'Laporan Laba') },

  // Administrasi
  { path: '/audit-logs', ...page(() => import('../pages/audit/AuditLogsPage.vue'), ADMIN, 'Audit Log') },

  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const { isAuthenticated, currentUser, restoreSession } = useAuth()

  if (isAuthenticated.value && !currentUser.value) {
    await restoreSession()
  }

  if (to.meta.guestOnly) {
    return isAuthenticated.value && currentUser.value
      ? getLandingPage(currentUser.value.role)
      : true
  }

  // Semua halaman selain yang public wajib login.
  if (!to.meta.public && (!isAuthenticated.value || !currentUser.value)) {
    return { path: '/login', query: to.fullPath !== '/' ? { redirect: to.fullPath } : {} }
  }

  const roles = to.meta.roles
  if (roles && currentUser.value && !roles.includes(currentUser.value.role)) {
    const landing = getLandingPage(currentUser.value.role)
    return to.path === landing ? true : landing
  }

  return true
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · Koprom` : 'Koprom'
})

export default router
