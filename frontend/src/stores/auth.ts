import { computed, ref } from 'vue'
import type { CurrentUser } from '../types/auth'

const token = ref<string | null>(
  localStorage.getItem('access_token'),
)

const currentUser = ref<CurrentUser | null>(null)

export function useAuth() {
  const isAuthenticated = computed(() => Boolean(token.value))

  function setAuth(newToken: string, user: CurrentUser) {
    token.value = newToken
    currentUser.value = user

    localStorage.setItem('access_token', newToken)
  }

  function clearAuth() {
    token.value = null
    currentUser.value = null

    localStorage.removeItem('access_token')
  }

  return {
    token,
    currentUser,
    isAuthenticated,
    setAuth,
    clearAuth,
  }
}