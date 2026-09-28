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
  
    async function restoreSession() {
    if (!token.value) {
        return false
    }

    try {
        const response = await fetch('/api/auth/me', {
        headers: {
            Authorization: `Bearer ${token.value}`,
        },
        })

        if (!response.ok) {
        clearAuth()
        return false
        }

        currentUser.value = await response.json()
        return true
    } catch {
        clearAuth()
        return false
    }
    }
    return {
    token,
    currentUser,
    isAuthenticated,
    setAuth,
    clearAuth,
    restoreSession,
    }
}
