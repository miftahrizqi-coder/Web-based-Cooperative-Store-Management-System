<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createUser } from '../../api/users'
import { useAuth } from '../../stores/auth'
import type { UserRole } from '../../types/auth'

const { token } = useAuth()

const router = useRouter()

const name = ref('')
const username = ref('')
const email = ref('')
const password = ref('')
const role = ref<UserRole>('kasir')

const nameError = ref('')
const usernameError = ref('')
const emailError = ref('')
const passwordError = ref('')
const roleError = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

function validateForm() {
  nameError.value = ''
  usernameError.value = ''
  emailError.value = ''
  passwordError.value = ''
  roleError.value = ''

  if (!name.value.trim()) {
    nameError.value = 'Nama wajib diisi.'
  }

  if (!username.value.trim()) {
    usernameError.value = 'Username wajib diisi.'
  } else if (username.value.trim().length < 3) {
    usernameError.value = 'Username minimal 3 karakter.'
  }

  if (!email.value.trim()) {
    emailError.value = 'Email wajib diisi.'
  } else if (!email.value.includes('@')) {
    emailError.value = 'Format email tidak valid.'
  }

  if (!password.value) {
    passwordError.value = 'Password wajib diisi.'
  } else if (password.value.length < 8) {
    passwordError.value = 'Password minimal 8 karakter.'
  }

  if (!role.value) {
    roleError.value = 'Role wajib dipilih.'
  }

  return !(
    nameError.value ||
    usernameError.value ||
    emailError.value ||
    passwordError.value ||
    roleError.value
  )
}

function handleCancel() {
  router.push('/users')
}

async function handleSubmit() {
  errorMessage.value = ''

  if (!validateForm()) {
    return
  }

  if (!token.value) {
    errorMessage.value = 'Sesi login tidak ditemukan. Silakan login kembali.'
    return
  }

  isLoading.value = true

  try {
    await createUser(token.value, {
      name: name.value.trim(),
      username: username.value.trim(),
      email: email.value.trim(),
      password: password.value,
      role: role.value,
    })

    await router.push('/users')
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal membuat pengguna.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <main class="mx-auto max-w-2xl">
    <div>
      <h1 class="text-2xl font-semibold text-gray-900">
        Tambah Pengguna
      </h1>

      <p class="mt-1 text-sm text-gray-500">
        Tambahkan pengguna baru dan tentukan role aksesnya.
      </p>
    </div>

    <form
      class="mt-6 rounded-xl border bg-white p-6"
      @submit.prevent="handleSubmit"
    >
      <div
        v-if="errorMessage"
        class="mb-6 rounded-lg border border-red-200 bg-red-50 p-4"
        role="alert"
      >
        <p class="text-sm font-medium text-red-700">
          {{ errorMessage }}
        </p>

        <p class="mt-1 text-sm text-red-600">
          Periksa kembali data yang dimasukkan lalu coba lagi.
        </p>
      </div>

      <div class="space-y-5">
        <!-- Nama -->
        <div>
          <label
            for="name"
            class="block text-sm font-medium text-gray-700"
          >
            Nama
          </label>

          <input
            id="name"
            v-model="name"
            type="text"
            autocomplete="name"
            :aria-invalid="Boolean(nameError)"
            :aria-describedby="nameError ? 'name-error' : undefined"
            class="mt-1 block w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-200"
            :class="nameError ? 'border-red-400' : 'border-gray-300'"
          />

          <p
            v-if="nameError"
            id="name-error"
            class="mt-1 text-sm text-red-600"
          >
            {{ nameError }}
          </p>
        </div>

        <!-- Username -->
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
            type="text"
            autocomplete="username"
            :aria-invalid="Boolean(usernameError)"
            :aria-describedby="usernameError ? 'username-error' : undefined"
            class="mt-1 block w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-200"
            :class="usernameError ? 'border-red-400' : 'border-gray-300'"
          />

          <p
            v-if="usernameError"
            id="username-error"
            class="mt-1 text-sm text-red-600"
          >
            {{ usernameError }}
          </p>
        </div>

        <!-- Email -->
        <div>
          <label
            for="email"
            class="block text-sm font-medium text-gray-700"
          >
            Email
          </label>

          <input
            id="email"
            v-model="email"
            type="email"
            autocomplete="email"
            :aria-invalid="Boolean(emailError)"
            :aria-describedby="emailError ? 'email-error' : undefined"
            class="mt-1 block w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-200"
            :class="emailError ? 'border-red-400' : 'border-gray-300'"
          />

          <p
            v-if="emailError"
            id="email-error"
            class="mt-1 text-sm text-red-600"
          >
            {{ emailError }}
          </p>
        </div>

        <!-- Password -->
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
            type="password"
            autocomplete="new-password"
            :aria-invalid="Boolean(passwordError)"
            :aria-describedby="passwordError ? 'password-error' : undefined"
            class="mt-1 block w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-200"
            :class="passwordError ? 'border-red-400' : 'border-gray-300'"
          />

          <p
            v-if="passwordError"
            id="password-error"
            class="mt-1 text-sm text-red-600"
          >
            {{ passwordError }}
          </p>
        </div>

        <!-- Role -->
        <div>
          <label
            for="role"
            class="block text-sm font-medium text-gray-700"
          >
            Role
          </label>

          <select
            id="role"
            v-model="role"
            :aria-invalid="Boolean(roleError)"
            :aria-describedby="roleError ? 'role-error' : undefined"
            class="mt-1 block w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-200"
            :class="roleError ? 'border-red-400' : 'border-gray-300'"
          >
            <option value="admin">Admin</option>
            <option value="kasir">Kasir</option>
            <option value="pengurus">Pengurus</option>
            <option value="anggota">Anggota</option>
          </select>

          <p
            v-if="roleError"
            id="role-error"
            class="mt-1 text-sm text-red-600"
          >
            {{ roleError }}
          </p>
        </div>
      </div>

      <div class="mt-8 flex justify-end gap-3 border-t pt-6">
        <button
          type="button"
          class="rounded-lg border px-4 py-2.5 text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400"
          :disabled="isLoading"
          @click="handleCancel"
        >
          Batal
        </button>

        <button
          type="submit"
          class="rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-400 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="isLoading"
        >
          {{ isLoading ? 'Menyimpan...' : 'Simpan' }}
        </button>
      </div>
    </form>
  </main>
</template>