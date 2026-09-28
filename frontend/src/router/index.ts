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

  return true
})

export default router