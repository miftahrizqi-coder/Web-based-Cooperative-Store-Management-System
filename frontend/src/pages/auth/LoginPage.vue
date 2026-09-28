<script setup lang="ts">
import { ref } from 'vue'
import { login } from '../../api/auth'

const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

const usernameError = ref('')
const passwordError = ref('')

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
    return
  }

  isLoading.value = true

  try {
    const result = await login(
      username.value.trim(),
      password.value,
    )

    localStorage.setItem('access_token', result.token)

    console.log('Login berhasil:', result.user)
  } catch {
    errorMessage.value = 'Username atau password tidak valid.'
  } finally {
    isLoading.value = false
  }
}

</script>

<template>
  <main class="min-h-screen bg-gray-50 px-4 py-8">
    <div class="flex min-h-[calc(100vh-4rem)] items-center justify-center">
      <section class="w-full max-w-md rounded-xl border bg-white p-6 sm:p-8">
        <div class="text-center">
          <h1 class="text-lg font-semibold text-gray-900">
            Koprom
          </h1>

          <p class="mt-1 text-sm text-gray-500">
            Koperasi Romantis
          </p>

          <h2 class="mt-8 text-2xl font-semibold text-gray-900">
            Selamat datang kembali
          </h2>
        </div>

        <form class="mt-8 space-y-5" novalidate @submit.prevent="handleSubmit">
          <div>
            <label
              for="username"
              class="block text-sm font-medium text-gray-700"
            >
              Username
            </label>

                <input
                id="username"
                v-model="username"
                name="username"
                type="text"
                autocomplete="username"
                :aria-invalid="Boolean(usernameError)"
                :aria-describedby="usernameError ? 'username-error' : undefined"
                class="mt-2 block w-full rounded-lg border px-3 py-2.5 text-base focus:outline-none focus:ring-2 focus:ring-gray-400"
                />

                <p
                v-if="usernameError"
                id="username-error"
                class="mt-2 text-sm text-red-700"
                role="alert"
                >
                {{ usernameError }}
                </p>
          </div>

          <div>
            <label
              for="password"
              class="block text-sm font-medium text-gray-700"
            >
              Password
            </label>

            <input
                id="password"
                v-model="password"
                name="password"
                type="password"
                autocomplete="current-password"
                :aria-invalid="Boolean(passwordError)"
                :aria-describedby="passwordError ? 'password-error' : undefined"
                class="mt-2 block w-full rounded-lg border px-3 py-2.5 text-base focus:outline-none focus:ring-2 focus:ring-gray-400"
                />

                <p
                v-if="passwordError"
                id="password-error"
                class="mt-2 text-sm text-red-700"
                role="alert"
                >
                {{ passwordError }}
            </p>
          </div>

            <p
            v-if="errorMessage"
            class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
            role="alert"
            >
            {{ errorMessage }}
            </p>

            <button
            type="submit"
            :disabled="isLoading"
            class="w-full rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-gray-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
            {{ isLoading ? 'Memproses...' : 'Masuk' }}
            </button>
        </form>
      </section>
    </div>
  </main>
</template>