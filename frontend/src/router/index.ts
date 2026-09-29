import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth'
import SupplierProductsPage from '../pages/supplierProducts/SupplierProductsPage.vue'
import SupplierProductFormPage from '../pages/supplierProducts/SupplierProductFormPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/login',
      component: () => import('../pages/auth/LoginPage.vue'),
      meta: {
        guestOnly: true,
      },
    },
    {
      path: '/dashboard',
      component: () => import('../pages/dashboard/DashboardPage.vue'),
      meta: {
        requiresAuth: true,
      },
    },
    {
      path: '/users',
      component: () => import('../pages/users/UsersPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin'],
      },
    },
    {
      path: '/users/create',
      component: () => import('../pages/users/UserCreatePage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin'],
      },
    },
    {
      path: '/users/:id/edit',
      component: () => import('../pages/users/UserEditPage.vue'),
      meta: { 
        requiresAuth: true,
        roles: ['admin'],
      },
    },
    {
      path: '/products',
      component: () => import('../pages/products/ProductsPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin'],
      },
    },
    {
      path: '/products/create',
      component: () => import('../pages/products/ProductFormPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin'],
      },
    },
    {
      path: '/products/:id',
      component: () => import('../pages/products/ProductDetailPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin'],
      },
    },
    {
      path: '/products/:id/edit',
      component: () => import('../pages/products/ProductFormPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin'],
      },
    },
    {
      path: '/purchase-orders',
      component: () => import('../pages/procurement/PurchaseOrdersPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/purchase-orders/create',
      component: () => import('../pages/procurement/PurchaseOrderFromPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/purchase-orders/:id',
      component: () => import('../pages/procurement/PurchaseOrderDetailPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/purchase-orders/:id/edit',
      component: () => import('../pages/procurement/PurchaseOrderFromPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/suppliers',
      component: () => import('../pages/suppliers/SuppliersPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/suppliers/create',
      component: () => import('../pages/suppliers/SupplierFormPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/suppliers/:id/edit',
      component: () => import('../pages/suppliers/SupplierFormPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/suppliers/:id',
      component: () => import('../pages/suppliers/SupplierDetailPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/supplier-products',
      component: SupplierProductsPage,
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/supplier-products/create',
      component: SupplierProductFormPage,
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/supplier-products/:id/edit',
      component: SupplierProductFormPage,
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/goods-receipts',
      name: 'goods-receipts',
      component: () => import('../pages/procurement/GoodsReceiptListPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },

    {
      path: '/goods-receipts/create/:id',
      name: 'goods-receipt-create',
      component: () =>
        import('../pages/procurement/GoodsReceiptFormPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },

    {
      path: '/goods-receipts/:id',
      name: 'goods-receipt-detail',
      component: () =>
        import('../pages/procurement/GoodsReceiptDetailPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/purchases',
      name: 'purchases',
      component: () =>
        import('../pages/procurement/PurchaseListPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/purchases/create',
      name: 'purchase-create',
      component: () =>
        import('../pages/procurement/PurchaseCreatePage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/purchases/:id',
      name: 'purchase-detail',
      component: () =>
        import('../pages/procurement/PurchaseDetailPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/supplier-invoices',
      name: 'supplier-invoice',
      component: () =>
        import(
          '../pages/procurement/SupplierInvoiceListPage.vue'
        ),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/supplier-invoices/create',
      name: 'supplier-invoice-create',
      component: () =>
        import(
          '../pages/procurement/SupplierInvoiceCreatePage.vue'
        ),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/supplier-invoices/:id',
      name: 'supplier-invoice-detail',
      component: () =>
        import(
          '../pages/procurement/SupplierInvoiceDetailPage.vue'
        ),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/supplier-payables',
      name: 'supplier-payables',
      component: () =>
        import('../pages/procurement/SupplierPayableListPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/supplier-payments',
      name: 'supplier-payments',
      component: () =>
        import('../pages/procurement/SupplierPaymentListPage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/supplier-payments/create',
      name: 'supplier-payment-create',
      component: () =>
        import('../pages/procurement/SupplierPaymentCreatePage.vue'),
      meta: {
        requiresAuth: true,
        roles: ['admin', 'pengurus'],
      },
    },
    {
      path: '/activities',
      component: () =>
        import('../pages/activity/ActivityListPage.vue'),
      meta: {
        roles: ['admin', 'pengurus'],
      },
    },
  ],
})

router.beforeEach(async (to) => {
  const {
    isAuthenticated,
    currentUser,
    restoreSession,
  } = useAuth()

  if (isAuthenticated.value && !currentUser.value) {
    await restoreSession()
  }

  if (to.meta.requiresAuth && !isAuthenticated.value) {
    return '/login'
  }

  if (to.meta.guestOnly && isAuthenticated.value) {
    return '/dashboard'
  }

  const allowedRoles = to.meta.roles as string[] | undefined

  if (
    allowedRoles &&
    (!currentUser.value || !allowedRoles.includes(currentUser.value.role))
  ) {
    return '/dashboard'
  }

  return true
})

export default router