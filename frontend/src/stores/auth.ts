import { computed, ref } from 'vue'
import type { CurrentUser, UserRole } from '../types/auth'

const TOKEN_KEY = 'access_token'

const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
const currentUser = ref<CurrentUser | null>(null)
let restorePromise: Promise<boolean> | null = null

export function useAuth() {
  const isAuthenticated = computed(() => Boolean(token.value))

  function setAuth(newToken: string, user: CurrentUser) {
    token.value = newToken
    currentUser.value = user
    localStorage.setItem(TOKEN_KEY, newToken)
  }

  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem(TOKEN_KEY, newToken)
  }

  function clearAuth() {
    token.value = null
    currentUser.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  /** Memuat ulang user dari token tersimpan (sekali jalan, di-cache). */
  async function restoreSession(): Promise<boolean> {
    if (!token.value) return false
    if (currentUser.value) return true
    if (restorePromise) return restorePromise

    restorePromise = (async () => {
      try {
        const response = await fetch('/api/auth/me', {
          headers: { Authorization: `Bearer ${token.value}` },
        })
        if (!response.ok) {
          clearAuth()
          return false
        }
        currentUser.value = await response.json()
        return true
      } catch {
        // Server tidak terjangkau: jangan hapus token agar bisa dicoba lagi.
        return false
      } finally {
        restorePromise = null
      }
    })()

    return restorePromise
  }

  async function logout() {
    const currentToken = token.value
    clearAuth()
    if (!currentToken) return
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${currentToken}` },
      })
    } catch {
      // Token tetap dihapus di klien walau server tidak terjangkau.
    }
  }

  function hasRole(...roles: UserRole[]) {
    return Boolean(currentUser.value && roles.includes(currentUser.value.role))
  }

  return {
    token,
    currentUser,
    isAuthenticated,
    setAuth,
    setToken,
    clearAuth,
    restoreSession,
    logout,
    hasRole,
  }
}
