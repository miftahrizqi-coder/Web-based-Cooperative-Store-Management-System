import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth'

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