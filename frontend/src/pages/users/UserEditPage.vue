<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getUser, updateUser } from '../../api/users'
import type { UserRole } from '../../types/auth'
import { useAuth } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const userId = route.params.id as string

const username = ref('')
const name = ref('')
const email = ref('')
const role = ref<UserRole>('kasir')
const isActive = ref(true)

const isLoading = ref(true)
const isSaving = ref(false)

const errorMessage = ref('')
const nameError = ref('')
const emailError = ref('')
const roleError = ref('')

function validateForm() {
  nameError.value = ''
  emailError.value = ''
  roleError.value = ''

  if (!name.value.trim()) {
    nameError.value = 'Nama wajib diisi.'
  }

  if (!email.value.trim()) {
    emailError.value = 'Email wajib diisi.'
  } else if (!email.value.includes('@')) {
    emailError.value = 'Format email tidak valid.'
  }

  if (!role.value) {
    roleError.value = 'Role wajib dipilih.'
  }

  return !(
    nameError.value ||
    emailError.value ||
    roleError.value
  )
}

async function loadUser() {
  errorMessage.value = ''

  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  try {
    const user = await getUser(token.value, userId)

    username.value = user.username
    name.value = user.name
    email.value = user.email
    role.value = user.role
    isActive.value = user.is_active
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data pengguna.'
  } finally {
    isLoading.value = false
  }
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
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    return
  }

  isSaving.value = true

  try {
    await updateUser(token.value, userId, {
      name: name.value.trim(),
      email: email.value.trim(),
      role: role.value,
      is_active: isActive.value,
    })

    await router.push('/users')
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal memperbarui pengguna.'
  } finally {
    isSaving.value = false
  }
}

onMounted(loadUser)
</script>

<template>
  <main class="mx-auto max-w-2xl">
    <div>
      <h1 class="text-2xl font-semibold text-gray-900">
        Edit Pengguna
      </h1>

      <p class="mt-1 text-sm text-gray-500">
        Perbarui informasi dan akses pengguna.
      </p>
    </div>

    <div
      v-if="isLoading"
      class="mt-6 rounded-xl border bg-white p-6"
    >
      <div class="animate-pulse space-y-5">
        <div class="h-4 w-24 rounded bg-gray-200" />
        <div class="h-10 rounded bg-gray-200" />

        <div class="h-4 w-24 rounded bg-gray-200" />
        <div class="h-10 rounded bg-gray-200" />

        <div class="h-4 w-24 rounded bg-gray-200" />
        <div class="h-10 rounded bg-gray-200" />
      </div>
    </div>

    <form
      v-else
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
          Periksa kembali data pengguna lalu coba lagi.
        </p>
      </div>

      <div class="space-y-5">
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
            disabled
            class="mt-1 block w-full rounded-lg border border-gray-300 bg-gray-100 px-3 py-2.5 text-sm text-gray-500"
          />

          <p class="mt-1 text-xs text-gray-500">
            Username tidak dapat diubah.
          </p>
        </div>

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
            :aria-describedby="
              nameError ? 'name-error' : undefined
            "
            class="mt-1 block w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-200"
            :class="
              nameError
                ? 'border-red-400'
                : 'border-gray-300'
            "
          />

          <p
            v-if="nameError"
            id="name-error"
            class="mt-1 text-sm text-red-600"
          >
            {{ nameError }}
          </p>
        </div>

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
            :aria-describedby="
              emailError ? 'email-error' : undefined
            "
            class="mt-1 block w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-200"
            :class="
              emailError
                ? 'border-red-400'
                : 'border-gray-300'
            "
          />

          <p
            v-if="emailError"
            id="email-error"
            class="mt-1 text-sm text-red-600"
          >
            {{ emailError }}
          </p>
        </div>

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
            :aria-describedby="
              roleError ? 'role-error' : undefined
            "
            class="mt-1 block w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-200"
            :class="
              roleError
                ? 'border-red-400'
                : 'border-gray-300'
            "
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

        <div>
          <label
            for="is-active"
            class="flex cursor-pointer items-center gap-3"
          >
            <input
              id="is-active"
              v-model="isActive"
              type="checkbox"
              class="h-4 w-4 rounded border-gray-300"
            />

            <span class="text-sm font-medium text-gray-700">
              Pengguna aktif
            </span>
          </label>

          <p class="mt-1 text-xs text-gray-500">
            Pengguna yang tidak aktif tidak dapat login.
          </p>
        </div>
      </div>

      <div class="mt-8 flex justify-end gap-3 border-t pt-6">
        <button
          type="button"
          class="rounded-lg border px-4 py-2.5 text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="isSaving"
          @click="handleCancel"
        >
          Batal
        </button>

        <button
          type="submit"
          class="rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-400 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="isSaving"
        >
          {{ isSaving ? 'Menyimpan...' : 'Simpan perubahan' }}
        </button>
      </div>
    </form>
  </main>
</template>