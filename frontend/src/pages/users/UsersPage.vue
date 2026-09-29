<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getUsers } from '../../api/users'
import type { User } from '../../types/user'
import { useAuth } from '../../stores/auth'
import { useRouter } from 'vue-router'

const router = useRouter()
const { token } = useAuth()

const users = ref<User[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

async function loadUsers() {
  isLoading.value = true
  errorMessage.value = ''

  if (!token.value) {
    errorMessage.value = 'Sesi login tidak ditemukan.'
    isLoading.value = false
    return
  }

  try {
    users.value = await getUsers(token.value)
  } catch {
    errorMessage.value = 'Gagal memuat data pengguna.'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <main>
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">
          Pengguna
        </h1>

        <p class="mt-1 text-sm text-gray-500">
          Kelola pengguna dan hak akses sistem.
        </p>
      </div>

      <button
        type="button"
        class="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-400"
        @click="router.push('/users/create')"      
        >
        Tambah pengguna
      </button>
    </div>

    <!-- Loading -->
    <section
      v-if="isLoading"
      class="mt-6 overflow-hidden rounded-xl border bg-white"
      aria-label="Memuat daftar pengguna"
    >
      <div class="space-y-4 p-6">
        <div
          v-for="index in 5"
          :key="index"
          class="h-12 animate-pulse rounded bg-gray-100"
        />
      </div>
    </section>

    <!-- Error -->
    <section
      v-else-if="errorMessage"
      class="mt-6 rounded-xl border bg-white p-6"
    >
      <p
        class="text-sm text-red-600"
        role="alert"
      >
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg border px-4 py-2 text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400"
        @click="loadUsers"
      >
        Coba lagi
      </button>
    </section>

    <!-- Empty -->
    <section
      v-else-if="users.length === 0"
      class="mt-6 rounded-xl border bg-white p-8 text-center"
    >
      <h2 class="font-medium text-gray-900">
        Belum ada pengguna
      </h2>

      <p class="mt-1 text-sm text-gray-500">
        Tambahkan pengguna untuk mulai mengelola akses sistem.
      </p>
    </section>

    <!-- Table -->
    <section
      v-else
      class="mt-6 overflow-hidden rounded-xl border bg-white"
    >
      <div class="overflow-x-auto">
        <table class="min-w-full text-left text-sm">
          <thead class="border-b bg-gray-50">
            <tr>
              <th class="px-6 py-3 font-medium text-gray-600">
                Nama
              </th>

              <th class="px-6 py-3 font-medium text-gray-600">
                Username
              </th>

              <th class="px-6 py-3 font-medium text-gray-600">
                Email
              </th>

              <th class="px-6 py-3 font-medium text-gray-600">
                Role
              </th>

              <th class="px-6 py-3 font-medium text-gray-600">
                Status
              </th>

              <th class="px-6 py-3 font-medium text-gray-600">
                Aksi
              </th>
            </tr>
          </thead>

          <tbody class="divide-y">
            <tr
              v-for="user in users"
              :key="user.id"
              class="hover:bg-gray-50"
            >
              <td class="px-6 py-4 font-medium text-gray-900">
                {{ user.name }}
              </td>

              <td class="px-6 py-4 text-gray-600">
                {{ user.username }}
              </td>

              <td class="px-6 py-4 text-gray-600">
                {{ user.email }}
              </td>

              <td class="px-6 py-4 capitalize text-gray-600">
                {{ user.role }}
              </td>

              <td class="px-6 py-4">
                <span
                  class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium"
                  :class="
                    user.is_active
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-600'
                  "
                >
                  {{ user.is_active ? 'Aktif' : 'Nonaktif' }}
                </span>
              </td>

              <td class="px-6 py-4">
                <button
                  type="button"
                  class="text-sm font-medium text-gray-700 hover:text-gray-900"
                  @click="router.push(`/users/${user.id}/edit`)"
                >
                  Edit
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</template>