<script setup lang="ts">
import { ref } from 'vue'
import { login, getCurrentUser } from '../../api/auth'
import { useAuth } from '../../stores/auth'
import { useRouter } from 'vue-router'
import { getLandingPage } from '../../router/navigation'

const router = useRouter()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')

const usernameError = ref('')
const passwordError = ref('')

const usernameInput = ref<HTMLInputElement | null>(null)
const passwordInput = ref<HTMLInputElement | null>(null)

const { setAuth } = useAuth()

async function handleSubmit() {
  usernameError.value = ''
  passwordError.value = ''
  errorMessage.value = ''

  if (!username.value.trim()) {
    usernameError.value = 'Username wajib diisi.'
  }

  if (!password.value) {
    passwordError.value = 'Password wajib diisi.'
  }

  if (usernameError.value || passwordError.value) {
    // Pindahkan fokus ke field pertama yang bermasalah
    if (usernameError.value) {
      usernameInput.value?.focus()
    } else {
      passwordInput.value?.focus()
    }
    return
  }

  isLoading.value = true

  try {
    const result = await login(username.value.trim(), password.value)

    const user = await getCurrentUser(result.token)

    setAuth(result.token, user)
    await router.push(getLandingPage(user.role))
  } catch {
    errorMessage.value = 'Username atau password tidak valid.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <main
    class="flex min-h-screen items-center justify-center bg-[#F8FAF9] px-4 py-8 font-['Inter',ui-sans-serif,system-ui,sans-serif] text-[#17201C] sm:px-6"
  >
    <section
      class="w-full max-w-md rounded-lg border border-[#D6DDD9] bg-white p-6 shadow-[0_1px_2px_rgba(18,55,42,.06)] sm:p-8"
      aria-labelledby="login-title"
    >
      <!-- Brand -->
      <header class="flex flex-col items-center text-center">
        <div
          class="flex h-12 w-12 items-center justify-center rounded-lg bg-[#164A38] text-xl font-bold text-white"
          aria-hidden="true"
        >
          K
        </div>

        <p class="mt-3 text-lg font-semibold leading-[26px] text-[#12372A]">
          Koprom
        </p>
        <p class="text-[13px] leading-[18px] text-[#46514B]">
          Koperasi Romantis
        </p>

        <h1
          id="login-title"
          class="mt-8 text-[22px] font-semibold leading-[30px] text-[#17201C]"
        >
          Selamat datang kembali
        </h1>
        <p class="mt-1 text-sm leading-5 text-[#46514B]">
          Masuk untuk melanjutkan ke sistem toko.
        </p>
      </header>

      <form class="mt-8 space-y-5" novalidate @submit.prevent="handleSubmit">
        <!-- Global error (inline, tetap di halaman) -->
        <div
          v-if="errorMessage"
          class="flex items-start gap-2 rounded-lg border border-[#C0392B]/30 bg-[#C0392B]/5 px-3 py-2.5 text-sm leading-5 text-[#C0392B]"
          role="alert"
        >
          <svg
            class="mt-0.5 h-4 w-4 shrink-0"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm-.75-11.5a.75.75 0 011.5 0v4a.75.75 0 01-1.5 0v-4zM10 14.5a1 1 0 100-2 1 1 0 000 2z"
              clip-rule="evenodd"
            />
          </svg>
          <span>{{ errorMessage }}</span>
        </div>

        <!-- Username -->
        <div>
          <label
            for="username"
            class="block text-sm font-medium leading-5 text-[#17201C]"
          >
            Username
          </label>

          <input
            id="username"
            ref="usernameInput"
            v-model="username"
            name="username"
            type="text"
            autocomplete="username"
            autofocus
            :disabled="isLoading"
            :aria-invalid="Boolean(usernameError)"
            :aria-describedby="usernameError ? 'username-error' : undefined"
            class="mt-2 block w-full rounded-lg border bg-white px-3 py-2.5 text-base leading-6 text-[#17201C] placeholder:text-[#6B756F] focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D] disabled:cursor-not-allowed disabled:bg-[#F1F4F2] disabled:text-[#6B756F]"
            :class="
              usernameError
                ? 'border-[#C0392B]'
                : 'border-[#D6DDD9] hover:border-[#6B756F]'
            "
          />

          <p
            v-if="usernameError"
            id="username-error"
            class="mt-2 text-[13px] leading-[18px] text-[#C0392B]"
            role="alert"
          >
            {{ usernameError }}
          </p>
        </div>

        <!-- Password -->
        <div>
          <label
            for="password"
            class="block text-sm font-medium leading-5 text-[#17201C]"
          >
            Password
          </label>

          <div class="relative mt-2">
            <input
              id="password"
              ref="passwordInput"
              v-model="password"
              name="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              :disabled="isLoading"
              :aria-invalid="Boolean(passwordError)"
              :aria-describedby="passwordError ? 'password-error' : undefined"
              class="block w-full rounded-lg border bg-white py-2.5 pl-3 pr-20 text-base leading-6 text-[#17201C] placeholder:text-[#6B756F] focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D] disabled:cursor-not-allowed disabled:bg-[#F1F4F2] disabled:text-[#6B756F]"
              :class="
                passwordError
                  ? 'border-[#C0392B]'
                  : 'border-[#D6DDD9] hover:border-[#6B756F]'
              "
            />

            <button
              type="button"
              :disabled="isLoading"
              :aria-pressed="showPassword"
              class="absolute inset-y-0 right-0 flex items-center rounded-r-lg px-3 text-[13px] font-medium text-[#176B4D] hover:text-[#1F805D] focus:outline-2 focus:-outline-offset-2 focus:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-60"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? 'Sembunyikan' : 'Tampilkan' }}
            </button>
          </div>

          <p
            v-if="passwordError"
            id="password-error"
            class="mt-2 text-[13px] leading-[18px] text-[#C0392B]"
            role="alert"
          >
            {{ passwordError }}
          </p>
        </div>

        <!-- Primary action -->
        <button
          type="submit"
          :disabled="isLoading"
          :aria-busy="isLoading"
          class="flex w-full items-center justify-center gap-2 rounded-lg bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#1F805D] active:bg-[#164A38] focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-70"
        >
          <svg
            v-if="isLoading"
            class="h-4 w-4 animate-spin"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            />
            <path
              class="opacity-90"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
            />
          </svg>
          <span>{{ isLoading ? 'Memproses...' : 'Masuk' }}</span>
        </button>

        <span class="sr-only" role="status">
          {{ isLoading ? 'Sedang memproses login' : '' }}
        </span>
      </form>
    </section>
  </main>
</template>