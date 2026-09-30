<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import {
  getSuppliers,
  updateSupplierStatus,
} from '../../api/suppliers'
import type {
  Supplier,
  SupplierStatus,
} from '../../types/supplier'
import { useAuth } from '../../stores/auth'

/**
 * Catatan token (DESIGN.md §3):
 * Warna ditulis sebagai arbitrary value Tailwind agar halaman ini
 * langsung bekerja tanpa perlu mengubah tailwind.config.
 * Bila token sudah didaftarkan di config, ganti mis. `bg-[#176B4D]` -> `bg-primary-700`.
 *
 *  primary-700 #176B4D | primary-600 #1F805D | primary-100 #DCEFE7 | primary-50 #F0F8F5
 *  neutral-950 #17201C | neutral-700 #46514B | neutral-500 #6B756F
 *  neutral-300 #D6DDD9 | neutral-200 #E6EBE8 | neutral-100 #F1F4F2 | neutral-50 #F8FAF9
 *  success #16834B | warning #B7791F | danger #C0392B
 */

type StatusFilter = 'ALL' | SupplierStatus
type SortDirection = 'asc' | 'desc'

const PAGE_SIZE = 10

const router = useRouter()
const { token } = useAuth()

const suppliers = ref<Supplier[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const actionError = ref('')
const successMessage = ref('')
const search = ref('')
const statusFilter = ref<StatusFilter>('ALL')
const sortDirection = ref<SortDirection>('asc')
const page = ref(1)
const updatingSupplierId = ref<string | null>(null)

/* ------------------------------------------------------------------ */
/* Data                                                                */
/* ------------------------------------------------------------------ */

async function loadSuppliers() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    suppliers.value = await getSuppliers(token.value)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data supplier.'
  } finally {
    isLoading.value = false
  }
}

const statusCounts = computed(() => {
  const counts: Record<StatusFilter, number> = {
    ALL: suppliers.value.length,
    ACTIVE: 0,
    INACTIVE: 0,
    BLACKLISTED: 0,
  }

  for (const supplier of suppliers.value) {
    counts[supplier.status] += 1
  }

  return counts
})

const filteredSuppliers = computed(() => {
  const keyword = search.value.trim().toLowerCase()

  const result = suppliers.value.filter((supplier) => {
    const matchesSearch =
      !keyword ||
      supplier.supplierCode.toLowerCase().includes(keyword) ||
      supplier.name.toLowerCase().includes(keyword) ||
      supplier.companyName.toLowerCase().includes(keyword) ||
      supplier.contactPerson.toLowerCase().includes(keyword)

    const matchesStatus =
      statusFilter.value === 'ALL' ||
      supplier.status === statusFilter.value

    return matchesSearch && matchesStatus
  })

  const direction = sortDirection.value === 'asc' ? 1 : -1

  return [...result].sort(
    (a, b) =>
      a.name.localeCompare(b.name, 'id', { sensitivity: 'base' }) *
      direction,
  )
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredSuppliers.value.length / PAGE_SIZE)),
)

const pagedSuppliers = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filteredSuppliers.value.slice(start, start + PAGE_SIZE)
})

const rangeStart = computed(() =>
  filteredSuppliers.value.length === 0
    ? 0
    : (page.value - 1) * PAGE_SIZE + 1,
)

const rangeEnd = computed(() =>
  Math.min(page.value * PAGE_SIZE, filteredSuppliers.value.length),
)

const hasActiveFilter = computed(
  () => search.value.trim() !== '' || statusFilter.value !== 'ALL',
)

watch([search, statusFilter], () => {
  page.value = 1
})

watch(totalPages, (value) => {
  if (page.value > value) {
    page.value = value
  }
})

function resetFilters() {
  search.value = ''
  statusFilter.value = 'ALL'
}

function toggleSort() {
  sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
}

/* ------------------------------------------------------------------ */
/* Status                                                              */
/* ------------------------------------------------------------------ */

const statusOptions: { value: StatusFilter; label: string }[] = [
  { value: 'ALL', label: 'Semua' },
  { value: 'ACTIVE', label: 'Aktif' },
  { value: 'INACTIVE', label: 'Nonaktif' },
  { value: 'BLACKLISTED', label: 'Blacklist' },
]

function statusLabel(status: SupplierStatus) {
  switch (status) {
    case 'ACTIVE':
      return 'Aktif'
    case 'INACTIVE':
      return 'Nonaktif'
    case 'BLACKLISTED':
      return 'Blacklist'
  }
}

/** Badge selalu punya label teks + ikon bentuk; warna bukan satu-satunya penanda. */
function statusClass(status: SupplierStatus) {
  switch (status) {
    case 'ACTIVE':
      return 'border-[#16834B]/25 bg-[#DCEFE7] text-[#12372A]'
    case 'INACTIVE':
      return 'border-[#D6DDD9] bg-[#F1F4F2] text-[#46514B]'
    case 'BLACKLISTED':
      return 'border-[#C0392B]/25 bg-[#FBEDEB] text-[#8E2A20]'
  }
}

/* ------------------------------------------------------------------ */
/* Konfirmasi perubahan status (dialog aksesibel)                      */
/* ------------------------------------------------------------------ */

const pendingChange = ref<{
  supplier: Supplier
  status: Extract<SupplierStatus, 'INACTIVE' | 'BLACKLISTED'>
} | null>(null)

const dialogRef = ref<HTMLElement | null>(null)
const cancelButtonRef = ref<HTMLButtonElement | null>(null)
let triggerElement: HTMLElement | null = null

const isBlacklistChange = computed(
  () => pendingChange.value?.status === 'BLACKLISTED',
)

async function requestStatusChange(
  supplier: Supplier,
  status: 'INACTIVE' | 'BLACKLISTED',
) {
  triggerElement = document.activeElement as HTMLElement | null
  actionError.value = ''
  successMessage.value = ''
  pendingChange.value = { supplier, status }

  await nextTick()
  cancelButtonRef.value?.focus()
}

async function closeDialog() {
  if (updatingSupplierId.value) {
    return
  }

  pendingChange.value = null
  await nextTick()

  if (triggerElement && document.contains(triggerElement)) {
    triggerElement.focus()
  }

  triggerElement = null
}

function onDialogKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.stopPropagation()
    closeDialog()
    return
  }

  // Focus trap
  if (event.key !== 'Tab' || !dialogRef.value) {
    return
  }

  const focusable = dialogRef.value.querySelectorAll<HTMLElement>(
    'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
  )

  if (focusable.length === 0) {
    return
  }

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

async function confirmStatusChange() {
  if (!pendingChange.value) {
    return
  }

  if (!token.value) {
    actionError.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    pendingChange.value = null
    return
  }

  const { supplier, status } = pendingChange.value

  updatingSupplierId.value = supplier.id
  actionError.value = ''
  successMessage.value = ''

  try {
    const updated = await updateSupplierStatus(
      token.value,
      supplier.id,
      status,
    )

    const index = suppliers.value.findIndex(
      (item) => item.id === supplier.id,
    )

    if (index !== -1) {
      suppliers.value[index] = updated
    }

    successMessage.value =
      status === 'BLACKLISTED'
        ? `Supplier "${supplier.name}" dimasukkan ke blacklist.`
        : `Supplier "${supplier.name}" berhasil dinonaktifkan.`

    updatingSupplierId.value = null
    await closeDialog()
  } catch (error) {
    actionError.value =
      (error instanceof Error
        ? error.message
        : 'Gagal memperbarui status supplier.') +
      ' Status supplier tidak berubah.'

    updatingSupplierId.value = null
    await closeDialog()
  }
}

onMounted(loadSuppliers)
</script>

<template>
  <section class="space-y-6 text-[#17201C]">
    <!-- Header: Breadcrumb -> Title + Primary CTA -> Context -->
    <header class="space-y-3">
      <nav aria-label="Breadcrumb" class="text-[13px] leading-[18px] text-[#6B756F]">
        <ol class="flex items-center gap-1.5">
          <li>Master Data</li>
          <li aria-hidden="true">/</li>
          <li aria-current="page" class="font-medium text-[#46514B]">
            Supplier
          </li>
        </ol>
      </nav>

      <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 class="text-[28px] font-semibold leading-9 text-[#17201C]">
            Supplier
          </h1>

          <p class="mt-1 max-w-2xl text-sm leading-5 text-[#46514B]">
            Kelola data supplier, syarat pembayaran, dan status kerja sama.
            Perubahan status tidak menghapus riwayat transaksi.
          </p>
        </div>

        <button
          type="button"
          class="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          @click="router.push('/suppliers/create')"
        >
          <svg
            class="h-4 w-4"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <path d="M10 4v12M4 10h12" />
          </svg>
          Tambah supplier
        </button>
      </div>
    </header>

    <!-- Feedback global (async update -> role=status, error -> role=alert) -->
    <div role="status" aria-live="polite">
      <div
        v-if="successMessage"
        class="flex items-start justify-between gap-3 rounded-lg border border-[#16834B]/30 bg-[#F0F8F5] px-4 py-3 text-sm text-[#12372A]"
      >
        <span class="flex items-start gap-2">
          <svg
            class="mt-0.5 h-4 w-4 shrink-0 text-[#16834B]"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm3.7-9.3a1 1 0 0 0-1.4-1.4L9 10.6 7.7 9.3a1 1 0 0 0-1.4 1.4l2 2a1 1 0 0 0 1.4 0l4-4Z"
              clip-rule="evenodd"
            />
          </svg>
          {{ successMessage }}
        </span>

        <button
          type="button"
          class="rounded px-1 text-[13px] font-medium text-[#176B4D] underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          @click="successMessage = ''"
        >
          Tutup
        </button>
      </div>
    </div>

    <div
      v-if="actionError"
      role="alert"
      class="rounded-lg border border-[#C0392B]/30 bg-[#FBEDEB] px-4 py-3 text-sm text-[#8E2A20]"
    >
      {{ actionError }}
    </div>

    <!-- Loading: skeleton tabel -->
    <div
      v-if="isLoading"
      class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <span class="sr-only">Memuat data supplier...</span>

      <div class="border-b border-[#E6EBE8] bg-[#F8FAF9] px-4 py-3">
        <div class="h-4 w-40 animate-pulse rounded bg-[#E6EBE8]" />
      </div>

      <div class="divide-y divide-[#E6EBE8]">
        <div
          v-for="row in 6"
          :key="row"
          class="flex items-center gap-4 px-4 py-4"
        >
          <div class="w-1/3 space-y-2">
            <div class="h-4 w-3/4 animate-pulse rounded bg-[#E6EBE8]" />
            <div class="h-3 w-1/2 animate-pulse rounded bg-[#F1F4F2]" />
          </div>
          <div class="hidden w-1/4 space-y-2 md:block">
            <div class="h-4 w-2/3 animate-pulse rounded bg-[#E6EBE8]" />
            <div class="h-3 w-1/2 animate-pulse rounded bg-[#F1F4F2]" />
          </div>
          <div class="hidden h-4 w-24 animate-pulse rounded bg-[#E6EBE8] lg:block" />
          <div class="h-6 w-20 animate-pulse rounded-full bg-[#E6EBE8]" />
        </div>
      </div>
    </div>

    <!-- Error: apa yang gagal, apakah data berubah, apa yang bisa dilakukan -->
    <div
      v-else-if="errorMessage"
      role="alert"
      class="rounded-lg border border-[#C0392B]/30 bg-[#FBEDEB] p-6"
    >
      <h2 class="text-base font-semibold text-[#8E2A20]">
        Data supplier tidak dapat dimuat
      </h2>

      <p class="mt-1 text-sm text-[#8E2A20]">
        {{ errorMessage }}
      </p>

      <p class="mt-1 text-sm text-[#46514B]">
        Tidak ada data yang diubah. Periksa koneksi Anda, lalu coba lagi.
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg border border-[#C0392B]/40 bg-white px-4 py-2 text-sm font-semibold text-[#8E2A20] hover:bg-[#FBEDEB] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
        @click="loadSuppliers"
      >
        Coba lagi
      </button>
    </div>

    <template v-else>
      <!-- Filter bar: dekat dengan data -->
      <div class="rounded-lg border border-[#D6DDD9] bg-white p-4">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div class="w-full lg:max-w-md">
            <label
              for="supplier-search"
              class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]"
            >
              Cari supplier
            </label>

            <div class="relative">
              <svg
                class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6B756F]"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                aria-hidden="true"
              >
                <circle cx="9" cy="9" r="5.5" />
                <path d="m13 13 4 4" />
              </svg>

              <input
                id="supplier-search"
                v-model="search"
                type="search"
                autocomplete="off"
                placeholder="Kode, nama, perusahaan, atau kontak"
                class="w-full rounded-lg border border-[#D6DDD9] bg-white py-2.5 pl-9 pr-3 text-sm text-[#17201C] placeholder:text-[#6B756F] outline-none focus:border-[#176B4D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
              />
            </div>
          </div>

          <div
            role="group"
            aria-label="Filter status supplier"
            class="flex flex-wrap gap-2"
          >
            <button
              v-for="option in statusOptions"
              :key="option.value"
              type="button"
              :aria-pressed="statusFilter === option.value"
              class="inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-[13px] font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
              :class="
                statusFilter === option.value
                  ? 'border-[#176B4D] bg-[#DCEFE7] text-[#12372A]'
                  : 'border-[#D6DDD9] bg-white text-[#46514B] hover:bg-[#F1F4F2]'
              "
              @click="statusFilter = option.value"
            >
              {{ option.label }}
              <span
                class="rounded-full px-1.5 text-xs tabular-nums"
                :class="
                  statusFilter === option.value
                    ? 'bg-white/70 text-[#12372A]'
                    : 'bg-[#F1F4F2] text-[#46514B]'
                "
              >
                {{ statusCounts[option.value] }}
              </span>
            </button>
          </div>
        </div>
      </div>

      <!-- Empty: belum ada data sama sekali -->
      <div
        v-if="suppliers.length === 0"
        class="rounded-lg border border-dashed border-[#D6DDD9] bg-white px-6 py-12 text-center"
      >
        <div
          class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#F0F8F5] text-[#176B4D]"
          aria-hidden="true"
        >
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 9.5 12 4l9 5.5M5 10v9h14v-9M9 19v-5h6v5" />
          </svg>
        </div>

        <h2 class="mt-4 text-base font-semibold text-[#17201C]">
          Belum ada supplier
        </h2>

        <p class="mx-auto mt-1 max-w-md text-sm text-[#46514B]">
          Supplier dibutuhkan untuk membuat purchase order dan mencatat
          hutang. Tambahkan supplier pertama untuk memulai proses pengadaan.
        </p>

        <button
          type="button"
          class="mt-5 rounded-lg bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          @click="router.push('/suppliers/create')"
        >
          Tambah supplier
        </button>
      </div>

      <!-- Empty: pencarian / filter tanpa hasil -->
      <div
        v-else-if="filteredSuppliers.length === 0"
        class="rounded-lg border border-[#D6DDD9] bg-white px-6 py-12 text-center"
      >
        <h2 class="text-base font-semibold text-[#17201C]">
          Tidak ada supplier yang cocok
        </h2>

        <p class="mx-auto mt-1 max-w-md text-sm text-[#46514B]">
          Tidak ada hasil untuk
          <template v-if="search.trim()">
            pencarian
            <span class="font-medium text-[#17201C]">"{{ search.trim() }}"</span>
          </template>
          <template v-if="search.trim() && statusFilter !== 'ALL'"> dengan </template>
          <template v-if="statusFilter !== 'ALL'">
            status
            <span class="font-medium text-[#17201C]">{{
              statusLabel(statusFilter as SupplierStatus)
            }}</span>
          </template>.
          Periksa ejaan atau ubah filter.
        </p>

        <button
          v-if="hasActiveFilter"
          type="button"
          class="mt-5 rounded-lg border border-[#D6DDD9] bg-white px-4 py-2 text-sm font-semibold text-[#17201C] hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          @click="resetFilters"
        >
          Reset filter
        </button>
      </div>

      <!-- Data -->
      <div
        v-else
        class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
      >
        <!-- Tabel (tablet/desktop) -->
        <div class="hidden max-h-[70vh] overflow-auto md:block">
          <table class="min-w-full border-separate border-spacing-0">
            <caption class="sr-only">
              Daftar supplier
            </caption>

            <thead>
              <tr>
                <th
                  scope="col"
                  :aria-sort="sortDirection === 'asc' ? 'ascending' : 'descending'"
                  class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F8FAF9] px-4 py-3 text-left text-xs font-semibold text-[#46514B]"
                >
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 rounded font-semibold hover:text-[#17201C] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
                    @click="toggleSort"
                  >
                    Supplier
                    <svg
                      class="h-3.5 w-3.5"
                      :class="sortDirection === 'desc' ? 'rotate-180' : ''"
                      viewBox="0 0 20 20"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M10 4v12m0 0-4-4m4 4 4-4" />
                    </svg>
                    <span class="sr-only">
                      , urut nama
                      {{ sortDirection === 'asc' ? 'A ke Z' : 'Z ke A' }}. Klik untuk membalik.
                    </span>
                  </button>
                </th>

                <th
                  scope="col"
                  class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F8FAF9] px-4 py-3 text-left text-xs font-semibold text-[#46514B]"
                >
                  Kontak
                </th>

                <th
                  scope="col"
                  class="sticky top-0 z-10 hidden border-b border-[#D6DDD9] bg-[#F8FAF9] px-4 py-3 text-left text-xs font-semibold text-[#46514B] lg:table-cell"
                >
                  Syarat pembayaran
                </th>

                <th
                  scope="col"
                  class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F8FAF9] px-4 py-3 text-left text-xs font-semibold text-[#46514B]"
                >
                  Status
                </th>

                <th
                  scope="col"
                  class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F8FAF9] px-4 py-3 text-right text-xs font-semibold text-[#46514B]"
                >
                  Aksi
                </th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="supplier in pagedSuppliers"
                :key="supplier.id"
                class="hover:bg-[#F8FAF9]"
              >
                <!-- Identifier kuat: kode -> nama -> perusahaan -->
                <td class="border-b border-[#E6EBE8] px-4 py-3.5 align-top">
                  <RouterLink
                    :to="`/suppliers/${supplier.id}`"
                    class="rounded text-sm font-semibold text-[#17201C] hover:text-[#176B4D] hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
                  >
                    {{ supplier.name }}
                  </RouterLink>

                  <div class="mt-0.5 text-[13px] leading-[18px] tabular-nums text-[#46514B]">
                    {{ supplier.supplierCode }}
                  </div>

                  <div class="text-[13px] leading-[18px] text-[#6B756F]">
                    {{ supplier.companyName }}
                  </div>
                </td>

                <td class="border-b border-[#E6EBE8] px-4 py-3.5 align-top">
                  <div class="text-sm text-[#17201C]">
                    {{ supplier.contactPerson }}
                  </div>

                  <div class="mt-0.5 text-[13px] leading-[18px] tabular-nums text-[#46514B]">
                    {{ supplier.phone }}
                  </div>

                  <div class="text-[13px] leading-[18px] text-[#6B756F]">
                    {{ supplier.email }}
                  </div>
                </td>

                <td class="hidden border-b border-[#E6EBE8] px-4 py-3.5 align-top text-sm text-[#17201C] lg:table-cell">
                  <template v-if="supplier.paymentTerm.type === 'CASH'">
                    Tunai
                  </template>
                  <template v-else>
                    Kredit
                    <span class="tabular-nums">{{ supplier.paymentTerm.days }}</span>
                    hari
                  </template>
                </td>

                <td class="border-b border-[#E6EBE8] px-4 py-3.5 align-top">
                  <span
                    class="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium"
                    :class="statusClass(supplier.status)"
                  >
                    <svg class="h-3 w-3" viewBox="0 0 12 12" aria-hidden="true">
                      <circle
                        v-if="supplier.status === 'ACTIVE'"
                        cx="6" cy="6" r="4" fill="currentColor"
                      />
                      <circle
                        v-else-if="supplier.status === 'INACTIVE'"
                        cx="6" cy="6" r="3.25" fill="none" stroke="currentColor" stroke-width="1.5"
                      />
                      <path
                        v-else
                        d="M3 3l6 6M9 3l-6 6"
                        stroke="currentColor"
                        stroke-width="1.75"
                        stroke-linecap="round"
                      />
                    </svg>
                    {{ statusLabel(supplier.status) }}
                  </span>
                </td>

                <td class="border-b border-[#E6EBE8] px-4 py-3.5 align-top">
                  <div class="flex flex-wrap justify-end gap-1.5">
                    <RouterLink
                      :to="`/suppliers/${supplier.id}`"
                      class="rounded-lg border border-[#D6DDD9] bg-white px-3 py-1.5 text-[13px] font-medium text-[#17201C] hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
                    >
                      Detail
                    </RouterLink>

                    <RouterLink
                      :to="`/suppliers/${supplier.id}/edit`"
                      class="rounded-lg border border-[#D6DDD9] bg-white px-3 py-1.5 text-[13px] font-medium text-[#17201C] hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
                    >
                      Edit
                    </RouterLink>

                    <button
                      v-if="supplier.status === 'ACTIVE'"
                      type="button"
                      :disabled="updatingSupplierId === supplier.id"
                      class="rounded-lg px-3 py-1.5 text-[13px] font-medium text-[#46514B] hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
                      @click="requestStatusChange(supplier, 'INACTIVE')"
                    >
                      Nonaktifkan
                    </button>

                    <button
                      v-if="supplier.status !== 'BLACKLISTED'"
                      type="button"
                      :disabled="updatingSupplierId === supplier.id"
                      class="rounded-lg px-3 py-1.5 text-[13px] font-medium text-[#C0392B] hover:bg-[#FBEDEB] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
                      @click="requestStatusChange(supplier, 'BLACKLISTED')"
                    >
                      Blacklist
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Representasi kartu ringkas (mobile) -->
        <ul class="divide-y divide-[#E6EBE8] md:hidden">
          <li
            v-for="supplier in pagedSuppliers"
            :key="supplier.id"
            class="space-y-3 p-4"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <RouterLink
                  :to="`/suppliers/${supplier.id}`"
                  class="block truncate rounded text-sm font-semibold text-[#17201C] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
                >
                  {{ supplier.name }}
                </RouterLink>
                <div class="text-[13px] tabular-nums text-[#46514B]">
                  {{ supplier.supplierCode }}
                </div>
                <div class="truncate text-[13px] text-[#6B756F]">
                  {{ supplier.companyName }}
                </div>
              </div>

              <span
                class="inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium"
                :class="statusClass(supplier.status)"
              >
                <svg class="h-3 w-3" viewBox="0 0 12 12" aria-hidden="true">
                  <circle
                    v-if="supplier.status === 'ACTIVE'"
                    cx="6" cy="6" r="4" fill="currentColor"
                  />
                  <circle
                    v-else-if="supplier.status === 'INACTIVE'"
                    cx="6" cy="6" r="3.25" fill="none" stroke="currentColor" stroke-width="1.5"
                  />
                  <path
                    v-else
                    d="M3 3l6 6M9 3l-6 6"
                    stroke="currentColor"
                    stroke-width="1.75"
                    stroke-linecap="round"
                  />
                </svg>
                {{ statusLabel(supplier.status) }}
              </span>
            </div>

            <dl class="grid grid-cols-2 gap-x-4 gap-y-1 text-[13px]">
              <div>
                <dt class="text-[#6B756F]">Kontak</dt>
                <dd class="text-[#17201C]">{{ supplier.contactPerson }}</dd>
                <dd class="tabular-nums text-[#46514B]">{{ supplier.phone }}</dd>
              </div>
              <div>
                <dt class="text-[#6B756F]">Syarat pembayaran</dt>
                <dd class="text-[#17201C]">
                  <template v-if="supplier.paymentTerm.type === 'CASH'">Tunai</template>
                  <template v-else>Kredit {{ supplier.paymentTerm.days }} hari</template>
                </dd>
              </div>
            </dl>

            <div class="flex flex-wrap gap-2">
              <RouterLink
                :to="`/suppliers/${supplier.id}`"
                class="rounded-lg border border-[#D6DDD9] bg-white px-3 py-2 text-[13px] font-medium text-[#17201C] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
              >
                Detail
              </RouterLink>

              <RouterLink
                :to="`/suppliers/${supplier.id}/edit`"
                class="rounded-lg border border-[#D6DDD9] bg-white px-3 py-2 text-[13px] font-medium text-[#17201C] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
              >
                Edit
              </RouterLink>

              <button
                v-if="supplier.status === 'ACTIVE'"
                type="button"
                :disabled="updatingSupplierId === supplier.id"
                class="rounded-lg px-3 py-2 text-[13px] font-medium text-[#46514B] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:opacity-50"
                @click="requestStatusChange(supplier, 'INACTIVE')"
              >
                Nonaktifkan
              </button>

              <button
                v-if="supplier.status !== 'BLACKLISTED'"
                type="button"
                :disabled="updatingSupplierId === supplier.id"
                class="rounded-lg px-3 py-2 text-[13px] font-medium text-[#C0392B] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:opacity-50"
                @click="requestStatusChange(supplier, 'BLACKLISTED')"
              >
                Blacklist
              </button>
            </div>
          </li>
        </ul>

        <!-- Pagination -->
        <nav
          aria-label="Paginasi supplier"
          class="flex flex-col gap-3 border-t border-[#D6DDD9] bg-[#F8FAF9] px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
        >
          <p class="text-[13px] text-[#46514B]">
            Menampilkan
            <span class="font-medium tabular-nums text-[#17201C]">{{ rangeStart }}–{{ rangeEnd }}</span>
            dari
            <span class="font-medium tabular-nums text-[#17201C]">{{ filteredSuppliers.length }}</span>
            supplier
          </p>

          <div class="flex items-center gap-2">
            <button
              type="button"
              :disabled="page <= 1"
              class="rounded-lg border border-[#D6DDD9] bg-white px-3 py-1.5 text-[13px] font-medium text-[#17201C] hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
              @click="page -= 1"
            >
              Sebelumnya
            </button>

            <span class="px-1 text-[13px] tabular-nums text-[#46514B]" aria-current="page">
              Halaman {{ page }} / {{ totalPages }}
            </span>

            <button
              type="button"
              :disabled="page >= totalPages"
              class="rounded-lg border border-[#D6DDD9] bg-white px-3 py-1.5 text-[13px] font-medium text-[#17201C] hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
              @click="page += 1"
            >
              Berikutnya
            </button>
          </div>
        </nav>
      </div>
    </template>

    <!-- Dialog konfirmasi: menjelaskan konsekuensi, trap focus, Esc menutup -->
    <div
      v-if="pendingChange"
      class="fixed inset-0 z-50 flex items-end justify-center bg-[#17201C]/50 p-4 sm:items-center"
      @click.self="closeDialog"
    >
      <div
        ref="dialogRef"
        role="dialog"
        aria-modal="true"
        aria-labelledby="status-dialog-title"
        aria-describedby="status-dialog-desc"
        class="w-full max-w-md rounded-xl bg-white p-6 shadow-[0_12px_32px_rgba(18,55,42,.12)]"
        @keydown="onDialogKeydown"
      >
        <h2
          id="status-dialog-title"
          class="text-lg font-semibold leading-[26px] text-[#17201C]"
        >
          {{
            isBlacklistChange
              ? 'Masukkan supplier ke blacklist?'
              : 'Nonaktifkan supplier?'
          }}
        </h2>

        <div id="status-dialog-desc" class="mt-3 space-y-3 text-sm text-[#46514B]">
          <dl class="rounded-lg border border-[#E6EBE8] bg-[#F8FAF9] p-3">
            <div class="flex justify-between gap-4">
              <dt>Supplier</dt>
              <dd class="text-right font-medium text-[#17201C]">
                {{ pendingChange.supplier.name }}
              </dd>
            </div>
            <div class="mt-1 flex justify-between gap-4">
              <dt>Kode</dt>
              <dd class="tabular-nums text-[#17201C]">
                {{ pendingChange.supplier.supplierCode }}
              </dd>
            </div>
            <div class="mt-1 flex items-center justify-between gap-4">
              <dt>Status</dt>
              <dd class="text-[#17201C]">
                {{ statusLabel(pendingChange.supplier.status) }}
                →
                <span class="font-semibold">{{ statusLabel(pendingChange.status) }}</span>
              </dd>
            </div>
          </dl>

          <p>
            {{
              isBlacklistChange
                ? 'Supplier ditandai sebagai Blacklist. Data dan riwayat transaksinya tidak dihapus.'
                : 'Supplier ditandai Nonaktif. Data dan riwayat transaksinya tidak dihapus.'
            }}
          </p>
        </div>

        <div class="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            ref="cancelButtonRef"
            type="button"
            :disabled="!!updatingSupplierId"
            class="rounded-lg border border-[#D6DDD9] bg-white px-4 py-2.5 text-sm font-semibold text-[#17201C] hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:opacity-50"
            @click="closeDialog"
          >
            Batal
          </button>

          <button
            type="button"
            :disabled="!!updatingSupplierId"
            class="rounded-lg px-4 py-2.5 text-sm font-semibold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-60"
            :class="
              isBlacklistChange
                ? 'bg-[#C0392B] hover:bg-[#A93226]'
                : 'bg-[#176B4D] hover:bg-[#1F805D]'
            "
            @click="confirmStatusChange"
          >
            {{
              updatingSupplierId
                ? 'Menyimpan...'
                : isBlacklistChange
                  ? 'Ya, blacklist supplier'
                  : 'Ya, nonaktifkan'
            }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
