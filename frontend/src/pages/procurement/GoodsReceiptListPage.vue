<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getGoodsReceipts } from '../../api/procurement'
import type { GoodsReceipt } from '../../types/procurement'
import { useAuth } from '../../stores/auth'

const router = useRouter()
const { token } = useAuth()

const goodsReceipts = ref<GoodsReceipt[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

const searchQuery = ref('')
const statusFilter = ref('ALL')
const dateFilter = ref('ALL')
const currentPage = ref(1)
const pageSize = 10

type StatusTone = 'success' | 'warning' | 'danger' | 'info'

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object'
    ? (value as Record<string, unknown>)
    : {}
}

function readString(value: unknown, key: string): string {
  const object = asRecord(value)
  return typeof object[key] === 'string' ? object[key] as string : ''
}

function readNumber(value: unknown, key: string): number {
  const object = asRecord(value)
  const raw = object[key]

  if (typeof raw === 'number' && Number.isFinite(raw)) {
    return raw
  }

  const parsed = Number(raw ?? 0)
  return Number.isFinite(parsed) ? parsed : 0
}

function receiptNumber(receipt: GoodsReceipt): string {
  return (
    readString(receipt, 'receiptNumber') ||
    readString(receipt, 'grNumber') ||
    readString(receipt, 'number') ||
    `GR-${receipt.id}`
  )
}

function receivedAt(receipt: GoodsReceipt): string {
  return (
    readString(receipt, 'receivedAt') ||
    readString(receipt, 'createdAt') ||
    readString(receipt, 'date')
  )
}

function receiptItems(receipt: GoodsReceipt): unknown[] {
  const items = asRecord(receipt).items
  return Array.isArray(items) ? items : []
}

function totalReceived(receipt: GoodsReceipt): number {
  return receiptItems(receipt).reduce<number>(
    (total, item) => total + readNumber(item, 'receivedQuantity'),
    0,
  )
}

function totalAccepted(receipt: GoodsReceipt): number {
  return receiptItems(receipt).reduce<number>(
    (total, item) =>
      total +
      readNumber(item, 'acceptedQuantity'),
    0,
  )
}

function totalRejected(receipt: GoodsReceipt): number {
  return receiptItems(receipt).reduce<number>(
    (total, item) =>
      total +
      readNumber(item, 'rejectedQuantity'),
    0,
  )
}

function getStatus(receipt: GoodsReceipt): string {
  const explicitStatus = readString(receipt, 'status').toUpperCase()

  if (explicitStatus) {
    return explicitStatus
  }

  const rejected = totalRejected(receipt)
  const received = totalReceived(receipt)

  if (rejected > 0) {
    return 'REJECTED'
  }

  if (received > 0) {
    return 'CONFIRMED'
  }

  return 'DRAFT'
}

function formatStatus(status: string): string {
  const labels: Record<string, string> = {
    DRAFT: 'Draft',
    PENDING: 'Menunggu',
    CONFIRMED: 'Dikonfirmasi',
    RECEIVED: 'Diterima',
    PARTIALLY_RECEIVED: 'Diterima Sebagian',
    COMPLETED: 'Selesai',
    REJECTED: 'Ditolak',
    CANCELLED: 'Dibatalkan',
  }

  return (
    labels[status] ||
    status
      .toLowerCase()
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (letter) => letter.toUpperCase())
  )
}

function statusTone(status: string): StatusTone {
  if (
    ['CONFIRMED', 'RECEIVED', 'COMPLETED'].includes(status)
  ) {
    return 'success'
  }

  if (
    ['DRAFT', 'PENDING', 'PARTIALLY_RECEIVED'].includes(status)
  ) {
    return 'warning'
  }

  if (
    ['REJECTED', 'CANCELLED'].includes(status)
  ) {
    return 'danger'
  }

  return 'info'
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('id-ID').format(value)
}

function formatDate(value: string): string {
  if (!value) {
    return '—'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function dateMatches(receipt: GoodsReceipt): boolean {
  if (dateFilter.value === 'ALL') {
    return true
  }

  const rawDate = receivedAt(receipt)

  if (!rawDate) {
    return false
  }

  const date = new Date(rawDate)

  if (Number.isNaN(date.getTime())) {
    return false
  }

  const now = new Date()
  const start = new Date(now)
  start.setHours(0, 0, 0, 0)

  if (dateFilter.value === 'TODAY') {
    return date >= start
  }

  if (dateFilter.value === '7_DAYS') {
    const sevenDaysAgo = new Date(start)
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 6)
    return date >= sevenDaysAgo
  }

  if (dateFilter.value === '30_DAYS') {
    const thirtyDaysAgo = new Date(start)
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 29)
    return date >= thirtyDaysAgo
  }

  return true
}

const filteredReceipts = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return goodsReceipts.value.filter((receipt) => {
    const matchesSearch =
      !query ||
      [
        receiptNumber(receipt),
        String(receipt.purchaseOrderId ?? ''),
        String(receipt.supplierId ?? ''),
      ]
        .join(' ')
        .toLowerCase()
        .includes(query)

    const matchesStatus =
      statusFilter.value === 'ALL' ||
      getStatus(receipt) === statusFilter.value

    return matchesSearch && matchesStatus && dateMatches(receipt)
  })
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredReceipts.value.length / pageSize)),
)

const paginatedReceipts = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredReceipts.value.slice(start, start + pageSize)
})

const pageStart = computed(() => {
  if (filteredReceipts.value.length === 0) {
    return 0
  }

  return (currentPage.value - 1) * pageSize + 1
})

const pageEnd = computed(() =>
  Math.min(
    currentPage.value * pageSize,
    filteredReceipts.value.length,
  ),
)

const availableStatuses = computed(() => {
  const statuses = new Set(
    goodsReceipts.value.map((receipt) => getStatus(receipt)),
  )

  return Array.from(statuses)
})

function resetPage() {
  currentPage.value = 1
}

function clearFilters() {
  searchQuery.value = ''
  statusFilter.value = 'ALL'
  dateFilter.value = 'ALL'
  currentPage.value = 1
}

function goToPage(page: number) {
  currentPage.value = Math.min(
    Math.max(page, 1),
    totalPages.value,
  )
}

function goToDetail(id: string | number) {
  router.push(`/goods-receipts/${id}`)
}

function goToCreate() {
  router.push('/goods-receipts/create')
}

async function loadGoodsReceipts() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Tidak ada perubahan pada data. Silakan login kembali.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    goodsReceipts.value = await getGoodsReceipts(token.value)
    currentPage.value = 1
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil daftar penerimaan barang. Tidak ada perubahan pada data.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadGoodsReceipts)
</script>

<template>
  <main
    class="min-h-full bg-[#F8FAF9] px-4 py-6 text-[#17201C] sm:px-6 lg:px-8 lg:py-8"
  >
    <div class="mx-auto max-w-[1440px] space-y-6">
      <!-- Breadcrumb -->
      <nav
        aria-label="Breadcrumb"
        class="text-sm text-[#6B756F]"
      >
        <a
          href="/dashboard"
          class="rounded-md font-medium text-[#176B4D] hover:text-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
        >
          Procurement
        </a>

        <span class="mx-2" aria-hidden="true">/</span>

        <span
          class="font-medium text-[#46514B]"
          aria-current="page"
        >
          Goods Receipts
        </span>
      </nav>

      <!-- Page Header -->
      <header
        class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"
      >
        <div>
          <h1
            class="text-[28px] font-semibold leading-9 tracking-[-0.02em] text-[#17201C]"
          >
            Penerimaan Barang
          </h1>

          <p
            class="mt-2 max-w-2xl text-sm leading-5 text-[#46514B]"
          >
            Daftar penerimaan barang dari Purchase Order.
            Gunakan pencarian dan filter untuk menemukan
            penerimaan dengan cepat.
          </p>
        </div>

        <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
          <button
            type="button"
            class="inline-flex min-h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white shadow-[0_1px_2px_rgba(18,55,42,.06)] transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="isLoading"
            @click="goToCreate"
          >
            + Buat Penerimaan
          </button>

          <button
            type="button"
            class="inline-flex min-h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 py-2.5 text-sm font-semibold text-[#46514B] shadow-[0_1px_2px_rgba(18,55,42,.06)] transition hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="isLoading"
            @click="loadGoodsReceipts"
          >
            <span
              v-if="isLoading"
              class="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-[#D6DDD9] border-t-[#176B4D]"
              aria-hidden="true"
            />
            {{ isLoading ? 'Memuat...' : 'Refresh' }}
          </button>
        </div>
      </header>

      <!-- Loading -->
      <section
        v-if="isLoading"
        aria-label="Memuat daftar penerimaan barang"
        aria-live="polite"
        class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
      >
        <div
          class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6"
        >
          <div class="h-5 w-32 animate-pulse rounded bg-[#E6EBE8]" />
          <div
            class="mt-2 h-4 w-64 animate-pulse rounded bg-[#F1F4F2]"
          />
        </div>

        <div class="hidden md:block">
          <div
            class="grid grid-cols-[1.3fr_1fr_1fr_1fr_.8fr_.8fr_.8fr] gap-4 border-b border-[#E6EBE8] bg-[#F8FAF9] px-5 py-3"
          >
            <div
              v-for="index in 7"
              :key="index"
              class="h-3 animate-pulse rounded bg-[#E6EBE8]"
            />
          </div>

          <div class="divide-y divide-[#E6EBE8]">
            <div
              v-for="row in 6"
              :key="row"
              class="grid grid-cols-[1.3fr_1fr_1fr_1fr_.8fr_.8fr_.8fr] gap-4 px-5 py-5"
            >
              <div
                v-for="cell in 7"
                :key="cell"
                class="h-4 animate-pulse rounded bg-[#F1F4F2]"
              />
            </div>
          </div>
        </div>

        <div class="space-y-3 p-4 md:hidden">
          <div
            v-for="row in 4"
            :key="row"
            class="rounded-lg border border-[#E6EBE8] p-4"
          >
            <div class="h-4 w-32 animate-pulse rounded bg-[#E6EBE8]" />
            <div
              class="mt-3 h-4 w-full animate-pulse rounded bg-[#F1F4F2]"
            />
            <div
              class="mt-2 h-4 w-2/3 animate-pulse rounded bg-[#F1F4F2]"
            />
          </div>
        </div>
      </section>

      <!-- Error -->
      <section
        v-else-if="errorMessage"
        class="rounded-lg border border-[#C0392B]/30 bg-white p-6"
        role="alert"
      >
        <div
          class="flex h-11 w-11 items-center justify-center rounded-full bg-[#FDECEA] text-lg font-bold text-[#C0392B]"
          aria-hidden="true"
        >
          !
        </div>

        <h2
          class="mt-4 text-[22px] font-semibold leading-[30px] text-[#17201C]"
        >
          Daftar penerimaan tidak dapat dimuat
        </h2>

        <p
          class="mt-2 max-w-2xl text-sm leading-5 text-[#46514B]"
        >
          {{ errorMessage }}
        </p>

        <div class="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            class="rounded-lg bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="loadGoodsReceipts"
          >
            Coba Lagi
          </button>

          <button
            type="button"
            class="rounded-lg border border-[#D6DDD9] bg-white px-4 py-2.5 text-sm font-semibold text-[#46514B] transition hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="router.push('/dashboard')"
          >
            Kembali ke Dashboard
          </button>
        </div>
      </section>

      <template v-else>
        <!-- Filter Bar -->
        <section
          aria-labelledby="filter-title"
          class="rounded-lg border border-[#D6DDD9] bg-white"
        >
          <div
            class="border-b border-[#E6EBE8] px-4 py-4 sm:px-5"
          >
            <div
              class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <h2
                  id="filter-title"
                  class="text-[16px] font-semibold leading-6 text-[#17201C]"
                >
                  Filter penerimaan
                </h2>

                <p class="text-[13px] leading-5 text-[#6B756F]">
                  Cari berdasarkan nomor receipt, PO, atau supplier.
                </p>
              </div>

              <button
                v-if="
                  searchQuery ||
                  statusFilter !== 'ALL' ||
                  dateFilter !== 'ALL'
                "
                type="button"
                class="self-start rounded-md text-[13px] font-semibold text-[#176B4D] hover:underline focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 sm:self-auto"
                @click="clearFilters"
              >
                Reset filter
              </button>
            </div>
          </div>

          <div
            class="grid gap-4 p-4 sm:grid-cols-2 sm:p-5 lg:grid-cols-[minmax(280px,1.5fr)_minmax(180px,1fr)_minmax(180px,1fr)_auto]"
          >
            <div>
              <label
                for="receipt-search"
                class="mb-1.5 block text-[13px] font-medium text-[#46514B]"
              >
                Search
              </label>

              <div class="relative">
                <span
                  class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#6B756F]"
                  aria-hidden="true"
                >
                  ⌕
                </span>

                <input
                  id="receipt-search"
                  v-model="searchQuery"
                  type="search"
                  autocomplete="off"
                  placeholder="Cari receipt, PO, supplier..."
                  class="min-h-10 w-full rounded-lg border border-[#C9D2CD] bg-white pl-9 pr-3 text-sm text-[#17201C] outline-none transition placeholder:text-[#8A948E] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
                  @input="resetPage"
                />
              </div>
            </div>

            <div>
              <label
                for="receipt-status"
                class="mb-1.5 block text-[13px] font-medium text-[#46514B]"
              >
                Status
              </label>

              <select
                id="receipt-status"
                v-model="statusFilter"
                class="min-h-10 w-full rounded-lg border border-[#C9D2CD] bg-white px-3 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
                @change="resetPage"
              >
                <option value="ALL">
                  Semua status
                </option>

                <option
                  v-for="status in availableStatuses"
                  :key="status"
                  :value="status"
                >
                  {{ formatStatus(status) }}
                </option>
              </select>
            </div>

            <div>
              <label
                for="receipt-date"
                class="mb-1.5 block text-[13px] font-medium text-[#46514B]"
              >
                Tanggal
              </label>

              <select
                id="receipt-date"
                v-model="dateFilter"
                class="min-h-10 w-full rounded-lg border border-[#C9D2CD] bg-white px-3 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
                @change="resetPage"
              >
                <option value="ALL">
                  Semua tanggal
                </option>
                <option value="TODAY">
                  Hari ini
                </option>
                <option value="7_DAYS">
                  7 hari terakhir
                </option>
                <option value="30_DAYS">
                  30 hari terakhir
                </option>
              </select>
            </div>

            <div class="flex items-end">
              <div
                class="rounded-lg bg-[#F8FAF9] px-3 py-2.5 text-[13px] text-[#46514B]"
              >
                <span class="font-semibold text-[#17201C]">
                  {{ filteredReceipts.length }}
                </span>
                receipt
              </div>
            </div>
          </div>
        </section>

        <!-- Empty: no records -->
        <section
          v-if="goodsReceipts.length === 0"
          class="rounded-lg border border-dashed border-[#C9D2CD] bg-white p-8 text-center sm:p-12"
        >
          <div
            class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#EAF3EE] text-xl text-[#176B4D]"
            aria-hidden="true"
          >
            ✓
          </div>

          <h2
            class="mt-4 text-[18px] font-semibold leading-[26px] text-[#17201C]"
          >
            Belum ada penerimaan barang
          </h2>

          <p
            class="mx-auto mt-2 max-w-lg text-sm leading-5 text-[#6B756F]"
          >
            Belum ada Goods Receipt yang tersimpan. Buat penerimaan
            dari Purchase Order ketika barang sudah diterima.
          </p>
        </section>

        <!-- Empty: filter result -->
        <section
          v-else-if="filteredReceipts.length === 0"
          class="rounded-lg border border-dashed border-[#C9D2CD] bg-white p-8 text-center sm:p-12"
        >
          <div
            class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#F1F4F2] text-xl text-[#6B756F]"
            aria-hidden="true"
          >
            ⌕
          </div>

          <h2
            class="mt-4 text-[18px] font-semibold leading-[26px] text-[#17201C]"
          >
            Tidak ada hasil
          </h2>

          <p
            class="mx-auto mt-2 max-w-lg text-sm leading-5 text-[#6B756F]"
          >
            Tidak ada penerimaan yang sesuai dengan pencarian atau
            filter saat ini. Coba ubah kata kunci atau reset filter.
          </p>

          <button
            type="button"
            class="mt-5 rounded-lg border border-[#D6DDD9] bg-white px-4 py-2.5 text-sm font-semibold text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="clearFilters"
          >
            Reset filter
          </button>
        </section>

        <!-- Data Table -->
        <section
          v-else
          aria-labelledby="receipts-table-title"
          class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
        >
          <div
            class="flex flex-col gap-3 border-b border-[#E6EBE8] px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-5"
          >
            <div>
              <h2
                id="receipts-table-title"
                class="text-[18px] font-semibold leading-[26px] text-[#17201C]"
              >
                Daftar Goods Receipt
              </h2>

              <p class="mt-1 text-[13px] text-[#6B756F]">
                {{ pageStart }}–{{ pageEnd }} dari
                {{ filteredReceipts.length }} penerimaan
              </p>
            </div>

            <p
              class="text-[13px] text-[#6B756F]"
              aria-live="polite"
            >
              Total diterima:
              <span class="font-semibold text-[#17201C]">
                {{
                  formatNumber(
                    paginatedReceipts.reduce(
                      (total, receipt) =>
                        total + totalReceived(receipt),
                      0,
                    ),
                  )
                }}
              </span>
            </p>
          </div>

          <!-- Desktop / Tablet Table -->
          <div class="hidden overflow-x-auto md:block">
            <table class="min-w-full text-sm">
              <caption class="sr-only">
                Daftar penerimaan barang
              </caption>

              <thead class="border-b border-[#D6DDD9] bg-[#F8FAF9]">
                <tr>
                  <th
                    scope="col"
                    class="whitespace-nowrap px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                  >
                    Receipt
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                  >
                    Purchase Order
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                  >
                    Supplier
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                  >
                    Tanggal
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-5 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                  >
                    Diterima
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-5 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                  >
                    Accepted
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-5 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                  >
                    Rejected
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                  >
                    Status
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-5 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                  >
                    Aksi
                  </th>
                </tr>
              </thead>

              <tbody class="divide-y divide-[#E6EBE8]">
                <tr
                  v-for="receipt in paginatedReceipts"
                  :key="receipt.id"
                  class="transition hover:bg-[#FAFCFB]"
                >
                  <td class="px-5 py-4 align-top">
                    <button
                      type="button"
                      class="font-semibold text-[#176B4D] hover:underline focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                      @click="goToDetail(receipt.id)"
                    >
                      {{ receiptNumber(receipt) }}
                    </button>

                    <p
                      class="mt-1 font-mono text-xs text-[#8A948E]"
                    >
                      ID {{ receipt.id }}
                    </p>
                  </td>

                  <td class="px-5 py-4 align-top">
                    <span class="font-medium text-[#17201C]">
                      {{ receipt.purchaseOrderId || '—' }}
                    </span>
                  </td>

                  <td class="px-5 py-4 align-top">
                    <span class="text-[#46514B]">
                      {{ receipt.supplierId || '—' }}
                    </span>
                  </td>

                  <td class="px-5 py-4 align-top">
                    <span class="text-[#46514B]">
                      {{ formatDate(receivedAt(receipt)) }}
                    </span>
                  </td>

                  <td
                    class="tabular-nums px-5 py-4 text-right align-top font-medium text-[#17201C]"
                  >
                    {{ formatNumber(totalReceived(receipt)) }}
                  </td>

                  <td
                    class="tabular-nums px-5 py-4 text-right align-top text-[#46514B]"
                  >
                    {{ formatNumber(totalAccepted(receipt)) }}
                  </td>

                  <td
                    class="tabular-nums px-5 py-4 text-right align-top"
                    :class="
                      totalRejected(receipt) > 0
                        ? 'font-semibold text-[#C0392B]'
                        : 'text-[#46514B]'
                    "
                  >
                    {{ formatNumber(totalRejected(receipt)) }}
                  </td>

                  <td class="px-5 py-4 align-top">
                    <span
                      class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold"
                      :class="{
                        'bg-[#DCEFE7] text-[#16834B]':
                          statusTone(getStatus(receipt)) === 'success',
                        'bg-[#FFF4DC] text-[#8A5A13]':
                          statusTone(getStatus(receipt)) === 'warning',
                        'bg-[#FDECEA] text-[#C0392B]':
                          statusTone(getStatus(receipt)) === 'danger',
                        'bg-[#EAF3F8] text-[#2874A6]':
                          statusTone(getStatus(receipt)) === 'info',
                      }"
                    >
                      {{ formatStatus(getStatus(receipt)) }}
                    </span>
                  </td>

                  <td class="px-5 py-4 text-right align-top">
                    <button
                      type="button"
                      class="rounded-md px-2 py-1 font-semibold text-[#176B4D] hover:bg-[#EAF3EE] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                      :aria-label="`Lihat detail ${receiptNumber(receipt)}`"
                      @click="goToDetail(receipt.id)"
                    >
                      Detail
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mobile Row / Card -->
          <div class="space-y-3 p-4 md:hidden">
            <article
              v-for="receipt in paginatedReceipts"
              :key="receipt.id"
              class="rounded-lg border border-[#E6EBE8] bg-white p-4"
            >
              <div
                class="flex items-start justify-between gap-3"
              >
                <div class="min-w-0">
                  <button
                    type="button"
                    class="truncate text-left font-semibold text-[#176B4D] hover:underline focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                    @click="goToDetail(receipt.id)"
                  >
                    {{ receiptNumber(receipt) }}
                  </button>

                  <p
                    class="mt-1 font-mono text-xs text-[#8A948E]"
                  >
                    ID {{ receipt.id }}
                  </p>
                </div>

                <span
                  class="shrink-0 inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold"
                  :class="{
                    'bg-[#DCEFE7] text-[#16834B]':
                      statusTone(getStatus(receipt)) === 'success',
                    'bg-[#FFF4DC] text-[#8A5A13]':
                      statusTone(getStatus(receipt)) === 'warning',
                    'bg-[#FDECEA] text-[#C0392B]':
                      statusTone(getStatus(receipt)) === 'danger',
                    'bg-[#EAF3F8] text-[#2874A6]':
                      statusTone(getStatus(receipt)) === 'info',
                  }"
                >
                  {{ formatStatus(getStatus(receipt)) }}
                </span>
              </div>

              <dl
                class="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-[#E6EBE8] pt-4"
              >
                <div>
                  <dt class="text-xs text-[#6B756F]">
                    Purchase Order
                  </dt>
                  <dd
                    class="mt-1 truncate text-sm font-medium text-[#17201C]"
                  >
                    {{ receipt.purchaseOrderId || '—' }}
                  </dd>
                </div>

                <div>
                  <dt class="text-xs text-[#6B756F]">
                    Supplier
                  </dt>
                  <dd
                    class="mt-1 truncate text-sm text-[#46514B]"
                  >
                    {{ receipt.supplierId || '—' }}
                  </dd>
                </div>

                <div>
                  <dt class="text-xs text-[#6B756F]">
                    Diterima
                  </dt>
                  <dd
                    class="tabular-nums mt-1 text-sm font-semibold text-[#17201C]"
                  >
                    {{ formatNumber(totalReceived(receipt)) }}
                  </dd>
                </div>

                <div>
                  <dt class="text-xs text-[#6B756F]">
                    Accepted
                  </dt>
                  <dd
                    class="tabular-nums mt-1 text-sm text-[#46514B]"
                  >
                    {{ formatNumber(totalAccepted(receipt)) }}
                  </dd>
                </div>

                <div>
                  <dt class="text-xs text-[#6B756F]">
                    Rejected
                  </dt>
                  <dd
                    class="tabular-nums mt-1 text-sm"
                    :class="
                      totalRejected(receipt) > 0
                        ? 'font-semibold text-[#C0392B]'
                        : 'text-[#46514B]'
                    "
                  >
                    {{ formatNumber(totalRejected(receipt)) }}
                  </dd>
                </div>

                <div>
                  <dt class="text-xs text-[#6B756F]">
                    Diterima pada
                  </dt>
                  <dd
                    class="mt-1 text-sm text-[#46514B]"
                  >
                    {{ formatDate(receivedAt(receipt)) }}
                  </dd>
                </div>
              </dl>

              <button
                type="button"
                class="mt-4 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 py-2.5 text-sm font-semibold text-[#176B4D] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                @click="goToDetail(receipt.id)"
              >
                Lihat Detail
              </button>
            </article>
          </div>

          <!-- Pagination -->
          <footer
            class="flex flex-col gap-3 border-t border-[#E6EBE8] px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-5"
          >
            <p class="text-[13px] text-[#6B756F]">
              Menampilkan
              <span class="font-medium text-[#46514B]">
                {{ pageStart }}–{{ pageEnd }}
              </span>
              dari
              <span class="font-medium text-[#46514B]">
                {{ filteredReceipts.length }}
              </span>
              penerimaan
            </p>

            <nav
              aria-label="Pagination penerimaan barang"
              class="flex items-center gap-1"
            >
              <button
                type="button"
                class="min-h-9 rounded-md border border-[#D6DDD9] bg-white px-3 text-sm font-medium text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-40"
                :disabled="currentPage === 1"
                @click="goToPage(currentPage - 1)"
              >
                Sebelumnya
              </button>

              <span
                class="hidden px-2 text-sm text-[#6B756F] sm:inline"
              >
                Halaman {{ currentPage }} / {{ totalPages }}
              </span>

              <button
                type="button"
                class="min-h-9 rounded-md border border-[#D6DDD9] bg-white px-3 text-sm font-medium text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-40"
                :disabled="currentPage === totalPages"
                @click="goToPage(currentPage + 1)"
              >
                Berikutnya
              </button>
            </nav>
          </footer>
        </section>
      </template>
    </div>
  </main>
</template>

<style scoped>
:global(html) {
  font-family:
    Inter,
    ui-sans-serif,
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}
</style>
