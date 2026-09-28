import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      component: () => import('../pages/dashboard/DashboardPage.vue'),
    },
    {
        path: '/login',
        component: () => import('../pages/auth/LoginPage.vue'),
    },
  ],
})

export default router