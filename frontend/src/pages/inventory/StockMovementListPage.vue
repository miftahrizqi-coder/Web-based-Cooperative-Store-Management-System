<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { getInventory, getStockMovements } from '../../api/inventory'

import type {
  InventoryItem,
  StockMovement,
  StockMovementType,
} from '../../types/inventory'

/* Sesuaikan dengan route halaman Stock Adjustment di router Anda */
const ADJUSTMENT_ROUTE = '/inventory/adjustment'
const PAGE_SIZE = 25

/* ---------- State ---------- */
const movements = ref<StockMovement[]>([])
const products = ref<InventoryItem[]>([])

const selectedProduct = ref('')
const selectedMovementType = ref<StockMovementType | ''>('')

const loading = ref(true)
const filterLoading = ref(false)
const error = ref('')
const productsWarning = ref('')

const page = ref(1)
const sortDesc = ref(true)

let requestSeq = 0

const movementTypeOptions: Array<{ value: StockMovementType | ''; label: string }> = [
  { value: '', label: 'Semua tipe' },
  { value: 'PURCHASE', label: 'Pembelian' },
  { value: 'SALE', label: 'Penjualan' },
  { value: 'SALE_RETURN', label: 'Retur Penjualan' },
  { value: 'PURCHASE_RETURN', label: 'Retur Pembelian' },
  { value: 'ADJUSTMENT', label: 'Penyesuaian Stok' },
  { value: 'STOCK_OPNAME', label: 'Stock Opname' },
]

/* ---------- Derived ---------- */
const hasActiveFilter = computed(
  () => !!selectedProduct.value || !!selectedMovementType.value,
)

const sortedMovements = computed(() => {
  const list = [...movements.value]
  list.sort((a, b) => {
    const diff = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    return sortDesc.value ? -diff : diff
  })
  return list
})

const totalItems = computed(() => sortedMovements.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / PAGE_SIZE)))

const pagedMovements = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return sortedMovements.value.slice(start, start + PAGE_SIZE)
})

const rangeStart = computed(() => (totalItems.value === 0 ? 0 : (page.value - 1) * PAGE_SIZE + 1))
const rangeEnd = computed(() => Math.min(page.value * PAGE_SIZE, totalItems.value))

const activeFilterSummary = computed(() => {
  const parts: string[] = []
  if (selectedProduct.value) {
    const p = products.value.find((item) => item.product_id === selectedProduct.value)
    parts.push(p ? p.name : 'produk terpilih')
  }
  if (selectedMovementType.value) {
    const t = movementTypeOptions.find((o) => o.value === selectedMovementType.value)
    if (t) parts.push(t.label)
  }
  return parts.join(' · ')
})

/* ---------- Formatting ---------- */
const numberFormatter = new Intl.NumberFormat('id-ID', { maximumFractionDigits: 2 })
const dateFormatter = new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium' })
const timeFormatter = new Intl.DateTimeFormat('id-ID', { timeStyle: 'short' })

function formatNumber(value: number): string {
  return numberFormatter.format(value)
}

function formatSigned(value: number): string {
  if (value > 0) return `+${numberFormatter.format(value)}`
  if (value < 0) return `−${numberFormatter.format(Math.abs(value))}`
  return '0'
}

function formatDate(value: string): string {
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? '-' : dateFormatter.format(d)
}

function formatTime(value: string): string {
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? '' : timeFormatter.format(d)
}

/* Perubahan aktual = selisih stok, sehingga selalu konsisten dengan riwayat */
function deltaOf(movement: StockMovement): number {
  return movement.stock_after - movement.stock_before
}

function deltaClass(movement: StockMovement): string {
  return deltaOf(movement) > 0 ? 'text-[#0F6B3A]' : 'text-[#17201C]'
}

function movementLabel(type: StockMovementType): string {
  return movementTypeOptions.find((o) => o.value === type)?.label ?? type
}

const BADGE = {
  success: 'bg-[#E7F4EC] text-[#0F6B3A] border-[#B9DFC9]',
  info: 'bg-[#E8F1F8] text-[#1F5F87] border-[#BCD6E8]',
  warning: 'bg-[#FBF3E2] text-[#8A5A12] border-[#EBD5A6]',
}

function movementClass(type: StockMovementType): string {
  switch (type) {
    case 'PURCHASE':
    case 'SALE_RETURN':
      return BADGE.success
    case 'SALE':
    case 'PURCHASE_RETURN':
      return BADGE.info
    case 'ADJUSTMENT':
    case 'STOCK_OPNAME':
      return BADGE.warning
  }
}

function referenceLabel(movement: StockMovement): string {
  if (movement.reference_type && movement.reference_id) {
    return `${movement.reference_type} · ${movement.reference_id}`
  }
  if (movement.reference_type) return movement.reference_type
  return '-'
}

/* ---------- Data ---------- */
function getAccessToken(): string {
  const accessToken = localStorage.getItem('access_token')
  if (!accessToken) {
    throw new Error('Sesi login tidak ditemukan. Silakan masuk kembali.')
  }
  return accessToken
}

async function loadProducts(): Promise<void> {
  productsWarning.value = ''
  try {
    products.value = await getInventory(getAccessToken())
  } catch {
    products.value = []
    productsWarning.value =
      'Daftar produk untuk filter tidak dapat dimuat. Riwayat tetap ditampilkan tanpa filter produk.'
  }
}

async function loadMovements(showFilterLoading = false): Promise<void> {
  const seq = ++requestSeq

  if (showFilterLoading) {
    filterLoading.value = true
  } else {
    loading.value = true
  }
  error.value = ''

  try {
    const result = await getStockMovements(getAccessToken(), {
      product_id: selectedProduct.value || undefined,
      movement_type: selectedMovementType.value || undefined,
    })

    if (seq !== requestSeq) return
    movements.value = result
    page.value = 1
  } catch (err) {
    if (seq !== requestSeq) return
    error.value =
      err instanceof Error ? err.message : 'Riwayat pergerakan stok tidak dapat diambil.'
  } finally {
    if (seq === requestSeq) {
      loading.value = false
      filterLoading.value = false
    }
  }
}

function resetFilters(): void {
  /* watcher akan memuat ulang data */
  selectedProduct.value = ''
  selectedMovementType.value = ''
}

function retry(): void {
  loadMovements()
}

function toggleSort(): void {
  sortDesc.value = !sortDesc.value
  page.value = 1
}

function goToPage(next: number): void {
  page.value = Math.min(Math.max(1, next), totalPages.value)
}

watch([selectedProduct, selectedMovementType], () => {
  loadMovements(true)
})

onMounted(async () => {
  await loadProducts()
  await loadMovements()
})
</script>

<template>
  <section class="mx-auto w-full max-w-[1440px] font-sans text-[#17201C]">
    <!-- Breadcrumb -->
    <nav aria-label="Breadcrumb" class="mb-3 text-[13px] leading-[18px] text-[#6B756F]">
      <ol class="flex items-center gap-2">
        <li>
          <router-link
            to="/inventory"
            class="rounded-sm hover:text-[#176B4D] hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          >
            Inventory
          </router-link>
        </li>
        <li aria-hidden="true">/</li>
        <li aria-current="page" class="font-medium text-[#46514B]">Stock Movement</li>
      </ol>
    </nav>

    <!-- Page header -->
    <header class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h1 class="text-[28px] font-semibold leading-9 text-[#17201C]">Stock Movement</h1>
        <p class="mt-1 max-w-2xl text-sm leading-5 text-[#46514B]">
          Riwayat seluruh perubahan stok produk. Setiap baris adalah catatan permanen dan tidak
          dapat diubah; koreksi dicatat sebagai movement baru.
        </p>
      </div>

      <router-link
        :to="ADJUSTMENT_ROUTE"
        class="inline-flex h-10 shrink-0 items-center justify-center rounded-lg bg-[#176B4D] px-4 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
      >
        Buat Stock Adjustment
      </router-link>
    </header>

    <!-- Filter bar -->
    <div class="mb-4 rounded-lg border border-[#D6DDD9] bg-white p-4">
      <div class="grid gap-4 md:grid-cols-[minmax(0,1fr)_240px_auto]">
        <div>
          <label for="movement-product" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
            Produk
          </label>
          <select
            id="movement-product"
            v-model="selectedProduct"
            class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm text-[#17201C] focus:border-[#176B4D] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
          >
            <option value="">Semua produk</option>
            <option
              v-for="product in products"
              :key="product.product_id"
              :value="product.product_id"
            >
              {{ product.name }} — {{ product.sku }}
            </option>
          </select>
        </div>

        <div>
          <label for="movement-type" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
            Tipe movement
          </label>
          <select
            id="movement-type"
            v-model="selectedMovementType"
            class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm text-[#17201C] focus:border-[#176B4D] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
          >
            <option v-for="option in movementTypeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div class="flex items-end">
          <button
            type="button"
            :disabled="!hasActiveFilter"
            class="inline-flex h-10 w-full items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50 md:w-auto"
            @click="resetFilters"
          >
            Reset filter
          </button>
        </div>
      </div>

      <p v-if="productsWarning" class="mt-3 text-xs leading-4 text-[#8A5A12]" role="status">
        {{ productsWarning }}
      </p>
    </div>

    <!-- Loading (initial) -->
    <div
      v-if="loading"
      class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
      role="status"
      aria-label="Memuat stock movement"
    >
      <div class="hidden md:block">
        <div class="grid grid-cols-6 gap-4 border-b border-[#E6EBE8] bg-[#F1F4F2] px-4 py-3">
          <div v-for="index in 6" :key="index" class="h-4 animate-pulse rounded bg-[#E6EBE8]" />
        </div>
        <div class="divide-y divide-[#E6EBE8]">
          <div v-for="row in 6" :key="row" class="grid grid-cols-6 gap-4 px-4 py-4">
            <div v-for="column in 6" :key="column" class="h-4 animate-pulse rounded bg-[#F1F4F2]" />
          </div>
        </div>
      </div>

      <div class="space-y-3 p-4 md:hidden">
        <div v-for="row in 5" :key="row" class="space-y-3 rounded-lg border border-[#E6EBE8] p-4">
          <div class="h-5 w-2/3 animate-pulse rounded bg-[#F1F4F2]" />
          <div class="h-4 w-1/2 animate-pulse rounded bg-[#F1F4F2]" />
          <div class="h-4 w-1/3 animate-pulse rounded bg-[#F1F4F2]" />
        </div>
      </div>
    </div>

    <!-- Error -->
    <div
      v-else-if="error"
      class="rounded-lg border border-[#F0C4BF] bg-white p-8 text-center"
      role="alert"
    >
      <h2 class="text-lg font-semibold text-[#17201C]">Riwayat stock movement gagal dimuat</h2>
      <p class="mx-auto mt-1 max-w-md text-sm leading-5 text-[#46514B]">
        {{ error }} Halaman ini hanya membaca data, jadi stok tidak berubah. Periksa koneksi lalu
        coba lagi.
      </p>
      <button
        type="button"
        class="mt-5 inline-flex h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
        @click="retry"
      >
        Coba lagi
      </button>
    </div>

    <!-- Empty: filter no result -->
    <div
      v-else-if="movements.length === 0 && hasActiveFilter"
      class="rounded-lg border border-[#D6DDD9] bg-white p-10 text-center"
    >
      <div
        aria-hidden="true"
        class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#F0F8F5] text-xl text-[#176B4D]"
      >⌕</div>
      <h2 class="text-lg font-semibold text-[#17201C]">Tidak ada movement yang cocok</h2>
      <p class="mx-auto mt-1 max-w-md text-sm leading-5 text-[#46514B]">
        Belum ada perubahan stok untuk {{ activeFilterSummary }}. Coba ubah filter atau tampilkan
        semua movement.
      </p>
      <button
        type="button"
        class="mt-5 inline-flex h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
        @click="resetFilters"
      >
        Tampilkan semua movement
      </button>
    </div>

    <!-- Empty: no data at all -->
    <div
      v-else-if="movements.length === 0"
      class="rounded-lg border border-[#D6DDD9] bg-white p-10 text-center"
    >
      <div
        aria-hidden="true"
        class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#F0F8F5] text-xl text-[#176B4D]"
      >⇄</div>
      <h2 class="text-lg font-semibold text-[#17201C]">Belum ada pergerakan stok</h2>
      <p class="mx-auto mt-1 max-w-md text-sm leading-5 text-[#46514B]">
        Riwayat akan muncul otomatis saat ada penerimaan barang, penjualan, retur, atau penyesuaian
        stok. Untuk mengoreksi stok secara manual, buat stock adjustment.
      </p>
      <router-link
        :to="ADJUSTMENT_ROUTE"
        class="mt-5 inline-flex h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
      >
        Buat Stock Adjustment
      </router-link>
    </div>

    <!-- Data -->
    <div
      v-else
      class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
      :aria-busy="filterLoading"
    >
      <div class="flex items-center justify-between gap-3 border-b border-[#E6EBE8] px-4 py-3">
        <div>
          <h2 class="text-sm font-semibold leading-5 text-[#17201C]">Riwayat movement</h2>
          <p class="mt-0.5 text-xs leading-4 text-[#6B756F]">
            {{ formatNumber(totalItems) }} movement
            <template v-if="hasActiveFilter"> · Filter: {{ activeFilterSummary }}</template>
          </p>
        </div>

        <p
          v-if="filterLoading"
          class="flex items-center gap-2 text-xs text-[#46514B]"
          role="status"
        >
          <span
            class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[#D6DDD9] border-t-[#176B4D]"
            aria-hidden="true"
          />
          Memperbarui daftar…
        </p>
      </div>

      <!-- Table (tablet & desktop) -->
      <div
        class="hidden max-h-[70vh] overflow-auto md:block"
        :class="filterLoading ? 'opacity-60' : ''"
      >
        <table class="min-w-full border-separate border-spacing-0">
          <caption class="sr-only">
            Riwayat perubahan stok, diurutkan berdasarkan waktu
            {{ sortDesc ? 'terbaru lebih dulu' : 'terlama lebih dulu' }}
          </caption>
          <thead>
            <tr>
              <th
                scope="col"
                :aria-sort="sortDesc ? 'descending' : 'ascending'"
                class="sticky top-0 z-10 whitespace-nowrap border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                <button
                  type="button"
                  class="inline-flex items-center gap-1 rounded-sm uppercase tracking-wide hover:text-[#176B4D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
                  @click="toggleSort"
                >
                  Waktu
                  <span aria-hidden="true">{{ sortDesc ? '↓' : '↑' }}</span>
                  <span class="sr-only">
                    , urutkan {{ sortDesc ? 'terlama lebih dulu' : 'terbaru lebih dulu' }}
                  </span>
                </button>
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                Produk
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                Tipe
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                Perubahan
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 hidden border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B] lg:table-cell"
              >
                Sebelum
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                Sesudah
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                Referensi
              </th>
            </tr>
          </thead>

          <tbody class="bg-white">
            <tr
              v-for="movement in pagedMovements"
              :key="movement.id"
              class="hover:bg-[#F8FAF9]"
            >
              <td class="whitespace-nowrap border-b border-[#E6EBE8] px-4 py-3 align-top">
                <div class="text-sm leading-5 text-[#17201C]">{{ formatDate(movement.created_at) }}</div>
                <div class="text-[13px] leading-[18px] tabular-nums text-[#6B756F]">
                  {{ formatTime(movement.created_at) }}
                </div>
              </td>

              <td class="border-b border-[#E6EBE8] px-4 py-3 align-top">
                <div class="text-sm font-semibold leading-5 text-[#17201C]">{{ movement.product_name }}</div>
                <div class="text-[13px] leading-[18px] text-[#6B756F]">SKU {{ movement.sku }}</div>
              </td>

              <td class="border-b border-[#E6EBE8] px-4 py-3 align-top">
                <span
                  class="inline-flex whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-medium"
                  :class="movementClass(movement.type)"
                >
                  {{ movementLabel(movement.type) }}
                </span>
              </td>

              <td
                class="whitespace-nowrap border-b border-[#E6EBE8] px-4 py-3 text-right align-top text-sm font-semibold tabular-nums"
                :class="deltaClass(movement)"
              >
                {{ formatSigned(deltaOf(movement)) }}
              </td>

              <td
                class="hidden whitespace-nowrap border-b border-[#E6EBE8] px-4 py-3 text-right align-top text-sm tabular-nums text-[#46514B] lg:table-cell"
              >
                {{ formatNumber(movement.stock_before) }}
              </td>

              <td
                class="whitespace-nowrap border-b border-[#E6EBE8] px-4 py-3 text-right align-top text-sm font-semibold tabular-nums text-[#17201C]"
              >
                {{ formatNumber(movement.stock_after) }}
              </td>

              <td class="max-w-[260px] border-b border-[#E6EBE8] px-4 py-3 align-top text-sm text-[#46514B]">
                <span class="break-all">{{ referenceLabel(movement) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Cards (mobile) -->
      <div
        class="divide-y divide-[#E6EBE8] md:hidden"
        :class="filterLoading ? 'opacity-60' : ''"
      >
        <div class="flex justify-end px-4 py-2">
          <button
            type="button"
            class="rounded-sm text-[13px] font-medium text-[#176B4D] hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
            @click="toggleSort"
          >
            Urutan: {{ sortDesc ? 'terbaru dulu' : 'terlama dulu' }}
          </button>
        </div>

        <article v-for="movement in pagedMovements" :key="movement.id" class="p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <h3 class="text-sm font-semibold leading-5 text-[#17201C]">{{ movement.product_name }}</h3>
              <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">SKU {{ movement.sku }}</p>
              <p class="text-[13px] leading-[18px] tabular-nums text-[#6B756F]">
                {{ formatDate(movement.created_at) }}, {{ formatTime(movement.created_at) }}
              </p>
            </div>

            <span
              class="shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-medium"
              :class="movementClass(movement.type)"
            >
              {{ movementLabel(movement.type) }}
            </span>
          </div>

          <dl class="mt-3 grid grid-cols-3 gap-3 rounded-lg bg-[#F8FAF9] px-3 py-2.5">
            <div>
              <dt class="text-xs text-[#6B756F]">Perubahan</dt>
              <dd class="mt-0.5 text-sm font-semibold tabular-nums" :class="deltaClass(movement)">
                {{ formatSigned(deltaOf(movement)) }}
              </dd>
            </div>
            <div>
              <dt class="text-xs text-[#6B756F]">Sebelum</dt>
              <dd class="mt-0.5 text-sm tabular-nums text-[#46514B]">{{ formatNumber(movement.stock_before) }}</dd>
            </div>
            <div>
              <dt class="text-xs text-[#6B756F]">Sesudah</dt>
              <dd class="mt-0.5 text-sm font-semibold tabular-nums text-[#17201C]">
                {{ formatNumber(movement.stock_after) }}
              </dd>
            </div>
          </dl>

          <p class="mt-3 text-[13px] leading-[18px] text-[#6B756F]">
            Referensi: <span class="break-all text-[#46514B]">{{ referenceLabel(movement) }}</span>
          </p>
        </article>
      </div>

      <!-- Pagination -->
      <nav
        aria-label="Paginasi stock movement"
        class="flex flex-col gap-3 border-t border-[#E6EBE8] px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
      >
        <p class="text-[13px] leading-[18px] tabular-nums text-[#46514B]" role="status" aria-live="polite">
          Menampilkan {{ formatNumber(rangeStart) }}–{{ formatNumber(rangeEnd) }} dari
          {{ formatNumber(totalItems) }} movement
        </p>

        <div class="flex items-center gap-2">
          <button
            type="button"
            :disabled="page <= 1"
            class="inline-flex h-9 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
            @click="goToPage(page - 1)"
          >
            Sebelumnya
          </button>

          <span class="px-2 text-[13px] tabular-nums text-[#46514B]">
            Halaman {{ page }} dari {{ totalPages }}
          </span>

          <button
            type="button"
            :disabled="page >= totalPages"
            class="inline-flex h-9 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
            @click="goToPage(page + 1)"
          >
            Berikutnya
          </button>
        </div>
      </nav>
    </div>
  </section>
</template>