<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { deleteUser, getUsers } from '../../api/users'
import { useAuth } from '../../stores/auth'
import type { User } from '../../types/user'

/**
 * Users List — DESIGN.md §5.2 (#4), §7.3 (List Screen), §10 (States),
 * §13 (Accessibility), §14 (Permission-Aware UX).
 *
 * Token mapping (arbitrary values dipakai supaya tidak bergantung pada
 * konfigurasi tailwind.config; ganti dengan token bila sudah didaftarkan):
 *   primary-700 #176B4D | primary-600 #1F805D | primary-100 #DCEFE7 | primary-50 #F0F8F5
 *   neutral-950 #17201C | neutral-700 #46514B | neutral-500 #6B756F
 *   neutral-300 #D6DDD9 | neutral-200 #E6EBE8 | neutral-100 #F1F4F2 | neutral-50 #F8FAF9
 *   success #16834B | danger #C0392B
 */

const PAGE_SIZE = 10

const router = useRouter()
const { token } = useAuth()

const users = ref<User[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

// Filter bar
const search = ref('')
const roleFilter = ref('')
const statusFilter = ref<'' | 'active' | 'inactive'>('')
const page = ref(1)

// Feedback
const successMessage = ref('')

// Deactivate confirmation dialog
const userToDeactivate = ref<User | null>(null)
const deletingUserId = ref<string | null>(null)
const deleteError = ref('')
const dialogRef = ref<HTMLElement | null>(null)
const cancelButtonRef = ref<HTMLButtonElement | null>(null)
const headingRef = ref<HTMLElement | null>(null)
const searchInputRef = ref<HTMLInputElement | null>(null)
let lastFocusedElement: HTMLElement | null = null

/* ------------------------------------------------------------------ */
/* Data                                                                */
/* ------------------------------------------------------------------ */

async function loadUsers(options: { silent?: boolean } = {}) {
  if (!options.silent) {
    isLoading.value = true
  }
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

/* ------------------------------------------------------------------ */
/* Role & status presentation                                          */
/* ------------------------------------------------------------------ */

const ROLE_LABELS: Record<string, string> = {
  admin: 'Admin',
  kasir: 'Kasir',
  pengurus: 'Pengurus',
  anggota: 'Anggota',
}

function roleLabel(role: string) {
  const key = String(role ?? '').toLowerCase()
  return ROLE_LABELS[key] ?? role
}

const roleOptions = computed(() => {
  const unique = Array.from(new Set(users.value.map((user) => user.role)))
  return unique
    .map((role) => ({ value: role, label: roleLabel(role) }))
    .sort((a, b) => a.label.localeCompare(b.label, 'id'))
})

/* ------------------------------------------------------------------ */
/* Filtering & pagination (client-side)                                */
/* ------------------------------------------------------------------ */

const hasActiveFilter = computed(
  () => search.value.trim() !== '' || roleFilter.value !== '' || statusFilter.value !== '',
)

const filteredUsers = computed(() => {
  const query = search.value.trim().toLowerCase()

  return users.value.filter((user) => {
    if (roleFilter.value && user.role !== roleFilter.value) return false
    if (statusFilter.value === 'active' && !user.is_active) return false
    if (statusFilter.value === 'inactive' && user.is_active) return false

    if (!query) return true
    return [user.name, user.username, user.email]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query))
  })
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredUsers.value.length / PAGE_SIZE)),
)

const pagedUsers = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filteredUsers.value.slice(start, start + PAGE_SIZE)
})

const rangeStart = computed(() =>
  filteredUsers.value.length === 0 ? 0 : (page.value - 1) * PAGE_SIZE + 1,
)
const rangeEnd = computed(() =>
  Math.min(page.value * PAGE_SIZE, filteredUsers.value.length),
)

watch([search, roleFilter, statusFilter], () => {
  page.value = 1
})

watch(totalPages, (value) => {
  if (page.value > value) page.value = value
})

function resetFilters() {
  search.value = ''
  roleFilter.value = ''
  statusFilter.value = ''
  searchInputRef.value?.focus()
}

/* ------------------------------------------------------------------ */
/* Deactivate flow (confirmation dialog, DESIGN §11 "Deactivate        */
/* confirmation", §13.5 modal behaviour)                               */
/* ------------------------------------------------------------------ */

async function openDeactivateDialog(user: User, event: Event) {
  lastFocusedElement = event.currentTarget as HTMLElement
  deleteError.value = ''
  successMessage.value = ''
  userToDeactivate.value = user

  await nextTick()
  cancelButtonRef.value?.focus()
}

async function closeDeactivateDialog() {
  if (deletingUserId.value) return

  userToDeactivate.value = null
  deleteError.value = ''

  await nextTick()
  restoreFocus()
}

function restoreFocus() {
  // Tombol pemicu bisa hilang dari DOM setelah data dimuat ulang
  // (pengguna sudah nonaktif) — fallback ke judul halaman.
  if (lastFocusedElement && lastFocusedElement.isConnected) {
    lastFocusedElement.focus()
  } else {
    headingRef.value?.focus()
  }
  lastFocusedElement = null
}

async function confirmDeactivate() {
  const user = userToDeactivate.value
  if (!user) return

  deleteError.value = ''

  if (!token.value) {
    deleteError.value =
      'Sesi login tidak ditemukan. Tidak ada perubahan pada pengguna. Silakan login kembali.'
    return
  }

  deletingUserId.value = user.id

  try {
    await deleteUser(token.value, user.id)
    await loadUsers({ silent: true })

    successMessage.value = `Pengguna "${user.name}" berhasil dinonaktifkan. Pengguna ini tidak dapat login lagi.`
    userToDeactivate.value = null
    await nextTick()
    restoreFocus()
  } catch (error) {
    const reason =
      error instanceof Error ? error.message : 'Gagal menonaktifkan pengguna.'
    deleteError.value = `${reason} Tidak ada perubahan pada pengguna. Coba lagi.`
  } finally {
    deletingUserId.value = null
  }
}

// Focus trap + Esc
function handleDialogKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.stopPropagation()
    closeDeactivateDialog()
    return
  }

  if (event.key !== 'Tab' || !dialogRef.value) return

  const focusable = Array.from(
    dialogRef.value.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  )
  if (focusable.length === 0) return

  const first = focusable[0]
  const last = focusable[focusable.length - 1]

  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

/* ------------------------------------------------------------------ */
/* Shortcuts                                                           */
/* ------------------------------------------------------------------ */

// "/" memfokuskan pencarian (DESIGN §13.3). Bukan satu-satunya cara.
function handleGlobalKeydown(event: KeyboardEvent) {
  if (event.key !== '/' || userToDeactivate.value) return

  const target = event.target as HTMLElement | null
  const tag = target?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target?.isContentEditable) {
    return
  }

  event.preventDefault()
  searchInputRef.value?.focus()
}

onMounted(() => {
  loadUsers()
  window.addEventListener('keydown', handleGlobalKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<template>
  <main class="mx-auto w-full max-w-[1440px] font-sans text-[#17201C]">
    <!-- Breadcrumb -->
    <nav aria-label="Breadcrumb" class="text-[13px] leading-[18px] text-[#6B756F]">
      <ol class="flex items-center gap-2">
        <li>Administrasi</li>
        <li aria-hidden="true">/</li>
        <li aria-current="page" class="font-medium text-[#46514B]">Pengguna</li>
      </ol>
    </nav>

    <!-- Page header: title + primary CTA -->
    <header class="mt-3 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1
          ref="headingRef"
          tabindex="-1"
          class="text-[28px] font-semibold leading-9 text-[#17201C] focus:outline-none"
        >
          Pengguna
        </h1>
        <p class="mt-1 max-w-prose text-sm leading-5 text-[#46514B]">
          Kelola akun pengguna dan hak akses berdasarkan role: Admin, Kasir,
          Pengurus, dan Anggota.
        </p>
      </div>

      <button
        type="button"
        class="inline-flex h-10 items-center gap-2 rounded-lg bg-[#176B4D] px-4 text-sm font-medium text-white transition-colors hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
        @click="router.push('/users/create')"
      >
        <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path d="M10 4a1 1 0 0 1 1 1v4h4a1 1 0 1 1 0 2h-4v4a1 1 0 1 1-2 0v-4H5a1 1 0 1 1 0-2h4V5a1 1 0 0 1 1-1Z" />
        </svg>
        Tambah pengguna
      </button>
    </header>

    <!-- Success feedback (contextual, singkat) -->
    <div
      v-if="successMessage"
      role="status"
      class="mt-6 flex items-start justify-between gap-4 rounded-lg border border-[#16834B]/30 bg-[#F0F8F5] px-4 py-3"
    >
      <p class="flex items-start gap-2 text-sm leading-5 text-[#164A38]">
        <svg class="mt-0.5 h-4 w-4 shrink-0 text-[#16834B]" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fill-rule="evenodd" d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm3.7-9.3a1 1 0 0 0-1.4-1.4L9 10.58 7.7 9.3a1 1 0 0 0-1.4 1.4l2 2a1 1 0 0 0 1.4 0l4-4Z" clip-rule="evenodd" />
        </svg>
        {{ successMessage }}
      </p>
      <button
        type="button"
        class="shrink-0 rounded text-sm font-medium text-[#176B4D] hover:text-[#12372A] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
        @click="successMessage = ''"
      >
        Tutup
      </button>
    </div>

    <!-- Loading: skeleton rows -->
    <section
      v-if="isLoading"
      class="mt-6 overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
      aria-label="Memuat daftar pengguna"
      aria-busy="true"
    >
      <div class="border-b border-[#E6EBE8] bg-[#F8FAF9] px-4 py-3 sm:px-6">
        <div class="h-4 w-40 animate-pulse rounded bg-[#E6EBE8]"></div>
      </div>
      <div class="divide-y divide-[#E6EBE8]">
        <div v-for="index in 6" :key="index" class="flex items-center gap-4 px-4 py-4 sm:px-6">
          <div class="h-9 w-9 shrink-0 animate-pulse rounded-full bg-[#F1F4F2]"></div>
          <div class="flex-1 space-y-2">
            <div class="h-4 w-1/3 animate-pulse rounded bg-[#F1F4F2]"></div>
            <div class="h-3 w-1/4 animate-pulse rounded bg-[#F1F4F2]"></div>
          </div>
          <div class="hidden h-6 w-20 animate-pulse rounded-full bg-[#F1F4F2] sm:block"></div>
          <div class="h-6 w-20 animate-pulse rounded-full bg-[#F1F4F2]"></div>
        </div>
      </div>
    </section>

    <!-- Error: apa yang gagal, apakah data berubah, apa yang bisa dilakukan -->
    <section
      v-else-if="errorMessage"
      class="mt-6 rounded-lg border border-[#C0392B]/30 bg-white p-6"
      role="alert"
    >
      <div class="flex items-start gap-3">
        <svg class="mt-0.5 h-5 w-5 shrink-0 text-[#C0392B]" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fill-rule="evenodd" d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-8-4a1 1 0 0 0-1 1v3a1 1 0 0 0 2 0V7a1 1 0 0 0-1-1Zm0 8a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" clip-rule="evenodd" />
        </svg>
        <div>
          <h2 class="text-base font-semibold text-[#17201C]">{{ errorMessage }}</h2>
          <p class="mt-1 text-sm leading-5 text-[#46514B]">
            Tidak ada data pengguna yang berubah. Periksa koneksi Anda, lalu coba
            muat ulang daftar.
          </p>
          <button
            type="button"
            class="mt-4 inline-flex h-9 items-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition-colors hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
            @click="loadUsers()"
          >
            Coba lagi
          </button>
        </div>
      </div>
    </section>

    <!-- Empty: belum ada pengguna sama sekali -->
    <section
      v-else-if="users.length === 0"
      class="mt-6 rounded-lg border border-dashed border-[#D6DDD9] bg-white px-6 py-12 text-center"
    >
      <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#F0F8F5] text-[#176B4D]">
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      </div>
      <h2 class="mt-4 text-lg font-semibold leading-[26px] text-[#17201C]">
        Belum ada pengguna
      </h2>
      <p class="mx-auto mt-1 max-w-md text-sm leading-5 text-[#46514B]">
        Akun pengguna menentukan siapa yang dapat masuk dan apa yang boleh
        dilakukan di sistem. Tambahkan pengguna pertama untuk mulai mengelola
        akses.
      </p>
      <button
        type="button"
        class="mt-5 inline-flex h-10 items-center rounded-lg bg-[#176B4D] px-4 text-sm font-medium text-white transition-colors hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
        @click="router.push('/users/create')"
      >
        Tambah pengguna
      </button>
    </section>

    <!-- Loaded -->
    <section v-else class="mt-6" aria-label="Daftar pengguna">
      <!-- Filter bar -->
      <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <div class="min-w-0 flex-1 sm:min-w-[260px] sm:max-w-sm">
          <label for="user-search" class="mb-1 block text-xs font-medium leading-4 text-[#46514B]">
            Cari pengguna
          </label>
          <div class="relative">
            <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6B756F]" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fill-rule="evenodd" d="M8 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM2 8a6 6 0 1 1 10.89 3.48l4.31 4.3a1 1 0 0 1-1.42 1.42l-4.3-4.31A6 6 0 0 1 2 8Z" clip-rule="evenodd" />
            </svg>
            <input
              id="user-search"
              ref="searchInputRef"
              v-model="search"
              type="search"
              autocomplete="off"
              placeholder="Nama, username, atau email  ( / )"
              class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white pl-9 pr-3 text-sm text-[#17201C] placeholder:text-[#6B756F] focus:border-[#176B4D] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
            />
          </div>
        </div>

        <div>
          <label for="user-role" class="mb-1 block text-xs font-medium leading-4 text-[#46514B]">
            Role
          </label>
          <select
            id="user-role"
            v-model="roleFilter"
            class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm text-[#17201C] focus:border-[#176B4D] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D] sm:w-44"
          >
            <option value="">Semua role</option>
            <option v-for="option in roleOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div>
          <label for="user-status" class="mb-1 block text-xs font-medium leading-4 text-[#46514B]">
            Status
          </label>
          <select
            id="user-status"
            v-model="statusFilter"
            class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm text-[#17201C] focus:border-[#176B4D] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D] sm:w-44"
          >
            <option value="">Semua status</option>
            <option value="active">Aktif</option>
            <option value="inactive">Nonaktif</option>
          </select>
        </div>

        <button
          v-if="hasActiveFilter"
          type="button"
          class="h-10 rounded-lg px-3 text-sm font-medium text-[#176B4D] hover:bg-[#F0F8F5] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          @click="resetFilters"
        >
          Reset filter
        </button>
      </div>

      <!-- Search / filter no result -->
      <div
        v-if="filteredUsers.length === 0"
        class="rounded-lg border border-dashed border-[#D6DDD9] bg-white px-6 py-12 text-center"
      >
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#F1F4F2] text-[#6B756F]">
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="m21 21-4.3-4.3" />
          </svg>
        </div>
        <h2 class="mt-4 text-lg font-semibold leading-[26px] text-[#17201C]">
          Tidak ada pengguna yang cocok
        </h2>
        <p class="mx-auto mt-1 max-w-md text-sm leading-5 text-[#46514B]">
          Tidak ditemukan pengguna dengan kata kunci atau filter yang dipilih.
          Periksa ejaan, atau hapus filter untuk melihat semua pengguna.
        </p>
        <button
          type="button"
          class="mt-5 inline-flex h-9 items-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition-colors hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          @click="resetFilters"
        >
          Reset filter
        </button>
      </div>

      <!-- Data table -->
      <div v-else class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white">
        <div class="max-h-[70vh] overflow-auto">
          <table class="min-w-full text-left text-sm">
            <caption class="sr-only">
              Daftar pengguna sistem beserta role dan status akun
            </caption>

            <thead class="sticky top-0 z-10 bg-[#F8FAF9] shadow-[0_1px_0_#D6DDD9]">
              <tr>
                <th scope="col" class="px-4 py-3 text-[13px] font-semibold leading-[18px] text-[#46514B] sm:px-6">
                  Pengguna
                </th>
                <th scope="col" class="hidden px-4 py-3 text-[13px] font-semibold leading-[18px] text-[#46514B] md:table-cell sm:px-6">
                  Email
                </th>
                <th scope="col" class="px-4 py-3 text-[13px] font-semibold leading-[18px] text-[#46514B] sm:px-6">
                  Role
                </th>
                <th scope="col" class="px-4 py-3 text-[13px] font-semibold leading-[18px] text-[#46514B] sm:px-6">
                  Status
                </th>
                <th scope="col" class="w-px whitespace-nowrap px-4 py-3 text-right text-[13px] font-semibold leading-[18px] text-[#46514B] sm:px-6">
                  Aksi
                </th>
              </tr>
            </thead>

            <tbody class="divide-y divide-[#E6EBE8]">
              <tr
                v-for="user in pagedUsers"
                :key="user.id"
                class="transition-colors hover:bg-[#F8FAF9]"
              >
                <!-- Identifier: nama kuat + username sebagai metadata -->
                <td class="px-4 py-3 sm:px-6">
                  <div class="font-semibold text-[#17201C]">{{ user.name }}</div>
                  <div class="text-[13px] leading-[18px] text-[#6B756F]">
                    @{{ user.username }}
                  </div>
                  <!-- Email dipindah ke bawah nama di layar kecil -->
                  <div class="mt-0.5 break-all text-[13px] leading-[18px] text-[#46514B] md:hidden">
                    {{ user.email }}
                  </div>
                </td>

                <td class="hidden px-4 py-3 text-[#46514B] md:table-cell sm:px-6">
                  {{ user.email }}
                </td>

                <td class="px-4 py-3 text-[#17201C] sm:px-6">
                  {{ roleLabel(user.role) }}
                </td>

                <!-- Status: label teks + ikon + semantic color -->
                <td class="px-4 py-3 sm:px-6">
                  <span
                    v-if="user.is_active"
                    class="inline-flex items-center gap-1.5 rounded-full bg-[#DCEFE7] px-2.5 py-1 text-xs font-medium leading-4 text-[#0F5C3A]"
                  >
                    <svg class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fill-rule="evenodd" d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0L3.3 9.7a1 1 0 1 1 1.4-1.4l3.8 3.79 6.8-6.8a1 1 0 0 1 1.4 0Z" clip-rule="evenodd" />
                    </svg>
                    Aktif
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center gap-1.5 rounded-full bg-[#F1F4F2] px-2.5 py-1 text-xs font-medium leading-4 text-[#46514B] ring-1 ring-inset ring-[#D6DDD9]"
                  >
                    <svg class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path d="M4 10a1 1 0 0 1 1-1h10a1 1 0 1 1 0 2H5a1 1 0 0 1-1-1Z" />
                    </svg>
                    Nonaktif
                  </span>
                </td>

                <!-- Aksi: kolom stabil, posisi tetap -->
                <td class="whitespace-nowrap px-4 py-3 sm:px-6">
                  <div class="flex items-center justify-end gap-1">
                    <button
                      type="button"
                      class="rounded-md px-2.5 py-1.5 text-sm font-medium text-[#176B4D] hover:bg-[#F0F8F5] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
                      :aria-label="`Edit pengguna ${user.name}`"
                      @click="router.push(`/users/${user.id}/edit`)"
                    >
                      Edit
                    </button>

                    <button
                      v-if="user.is_active"
                      type="button"
                      class="rounded-md px-2.5 py-1.5 text-sm font-medium text-[#C0392B] hover:bg-[#C0392B]/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
                      :aria-label="`Nonaktifkan pengguna ${user.name}`"
                      :disabled="deletingUserId === user.id"
                      @click="openDeactivateDialog(user, $event)"
                    >
                      Nonaktifkan
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="flex flex-col gap-3 border-t border-[#E6EBE8] bg-white px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p role="status" class="text-[13px] leading-[18px] text-[#46514B]">
            Menampilkan
            <span class="font-medium text-[#17201C]">{{ rangeStart }}–{{ rangeEnd }}</span>
            dari
            <span class="font-medium text-[#17201C]">{{ filteredUsers.length }}</span>
            pengguna
            <template v-if="hasActiveFilter">(hasil filter, total {{ users.length }})</template>
          </p>

          <nav aria-label="Navigasi halaman" class="flex items-center gap-2">
            <button
              type="button"
              class="h-9 rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm font-medium text-[#17201C] hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:text-[#6B756F] disabled:opacity-60 disabled:hover:bg-white"
              :disabled="page <= 1"
              @click="page -= 1"
            >
              Sebelumnya
            </button>
            <span class="px-1 text-[13px] text-[#46514B]">
              Halaman {{ page }} dari {{ totalPages }}
            </span>
            <button
              type="button"
              class="h-9 rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm font-medium text-[#17201C] hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:text-[#6B756F] disabled:opacity-60 disabled:hover:bg-white"
              :disabled="page >= totalPages"
              @click="page += 1"
            >
              Berikutnya
            </button>
          </nav>
        </div>
      </div>
    </section>

    <!-- Deactivate confirmation dialog -->
    <div
      v-if="userToDeactivate"
      class="fixed inset-0 z-50 flex items-end justify-center bg-[#17201C]/50 p-4 sm:items-center"
      @mousedown.self="closeDeactivateDialog"
    >
      <div
        ref="dialogRef"
        role="dialog"
        aria-modal="true"
        aria-labelledby="deactivate-title"
        aria-describedby="deactivate-desc"
        class="w-full max-w-md rounded-xl bg-white p-6 shadow-[0_12px_32px_rgba(18,55,42,.12)]"
        @keydown="handleDialogKeydown"
      >
        <h2 id="deactivate-title" class="text-lg font-semibold leading-[26px] text-[#17201C]">
          Nonaktifkan pengguna ini?
        </h2>

        <div id="deactivate-desc" class="mt-3 text-sm leading-5 text-[#46514B]">
          <div class="rounded-lg border border-[#E6EBE8] bg-[#F8FAF9] px-4 py-3">
            <div class="font-semibold text-[#17201C]">{{ userToDeactivate.name }}</div>
            <div class="text-[13px] leading-[18px] text-[#6B756F]">
              @{{ userToDeactivate.username }} · {{ roleLabel(userToDeactivate.role) }}
            </div>
          </div>

          <p class="mt-3">Yang akan berubah:</p>
          <ul class="mt-1 list-disc space-y-1 pl-5">
            <li>Status akun menjadi <strong class="font-semibold text-[#17201C]">Nonaktif</strong>.</li>
            <li>Pengguna tidak dapat login lagi.</li>
            <li>Data pengguna tidak dihapus dan riwayat transaksinya tetap tersimpan.</li>
          </ul>
        </div>

        <p
          v-if="deleteError"
          role="alert"
          class="mt-4 rounded-lg border border-[#C0392B]/30 bg-[#C0392B]/5 px-3 py-2 text-sm leading-5 text-[#9B2C20]"
        >
          {{ deleteError }}
        </p>

        <div class="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            ref="cancelButtonRef"
            type="button"
            class="h-10 rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="deletingUserId !== null"
            @click="closeDeactivateDialog"
          >
            Batal
          </button>
          <button
            type="button"
            class="h-10 rounded-lg bg-[#C0392B] px-4 text-sm font-medium text-white hover:bg-[#A93226] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="deletingUserId !== null"
            @click="confirmDeactivate"
          >
            {{ deletingUserId ? 'Menonaktifkan...' : 'Nonaktifkan pengguna' }}
          </button>
        </div>
      </div>
    </div>
  </main>
</template>
