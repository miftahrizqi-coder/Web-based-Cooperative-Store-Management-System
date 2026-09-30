<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { getInventory } from '../../api/inventory'

import type { InventoryItem, StockStatus } from '../../types/inventory'

/* Sesuaikan dengan route di router Anda */
const OPNAME_ROUTE = '/inventory/opname'
const ADJUSTMENT_ROUTE = '/inventory/adjustment'
const MOVEMENT_ROUTE = '/inventory/movements'
const PRODUCTS_ROUTE = '/products'

const PAGE_SIZE = 25
const SEARCH_DEBOUNCE_MS = 350

type SortValue = '' | 'name_asc' | 'name_desc' | 'stock_asc' | 'stock_desc'

/* ---------- State ---------- */
const inventory = ref<InventoryItem[]>([])
const summaryItems = ref<InventoryItem[] | null>(null)

const search = ref('')
const stockStatus = ref<StockStatus | ''>('')
const sortValue = ref<SortValue>('')
const page = ref(1)

const loading = ref(true)
const searchLoading = ref(false)
const error = ref('')

const searchInputRef = ref<HTMLInputElement | null>(null)

let searchTimer: ReturnType<typeof setTimeout> | null = null
let requestSeq = 0
let lastRequestKey = ''

const statusOptions: Array<{ value: StockStatus | ''; label: string }> = [
  { value: '', label: 'Semua status' },
  { value: 'AVAILABLE', label: 'Tersedia' },
  { value: 'LOW_STOCK', label: 'Stok menipis' },
  { value: 'OUT_OF_STOCK', label: 'Stok habis' },
]

const sortOptions: Array<{ value: SortValue; label: string }> = [
  { value: '', label: 'Urutan bawaan' },
  { value: 'name_asc', label: 'Nama A–Z' },
  { value: 'name_desc', label: 'Nama Z–A' },
  { value: 'stock_asc', label: 'Stok terendah' },
  { value: 'stock_desc', label: 'Stok tertinggi' },
]

/* ---------- Derived ---------- */
const hasActiveFilter = computed(() => !!search.value.trim() || !!stockStatus.value)

const summary = computed(() => {
  const items = summaryItems.value
  if (!items) return null
  return {
    total: items.length,
    low: items.filter((i) => i.stock_status === 'LOW_STOCK').length,
    out: items.filter((i) => i.stock_status === 'OUT_OF_STOCK').length,
  }
})

const sortedInventory = computed(() => {
  const list = [...inventory.value]
  switch (sortValue.value) {
    case 'name_asc':
      return list.sort((a, b) => a.name.localeCompare(b.name, 'id'))
    case 'name_desc':
      return list.sort((a, b) => b.name.localeCompare(a.name, 'id'))
    case 'stock_asc':
      return list.sort((a, b) => a.stock - b.stock)
    case 'stock_desc':
      return list.sort((a, b) => b.stock - a.stock)
    default:
      return list
  }
})

const totalItems = computed(() => sortedInventory.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / PAGE_SIZE)))

const pagedInventory = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return sortedInventory.value.slice(start, start + PAGE_SIZE)
})

const rangeStart = computed(() => (totalItems.value === 0 ? 0 : (page.value - 1) * PAGE_SIZE + 1))
const rangeEnd = computed(() => Math.min(page.value * PAGE_SIZE, totalItems.value))

const activeFilterSummary = computed(() => {
  const parts: string[] = []
  if (search.value.trim()) parts.push(`“${search.value.trim()}”`)
  if (stockStatus.value) {
    parts.push(statusOptions.find((o) => o.value === stockStatus.value)?.label ?? '')
  }
  return parts.filter(Boolean).join(' · ')
})

/* ---------- Formatting ---------- */
const numberFormatter = new Intl.NumberFormat('id-ID', { maximumFractionDigits: 2 })

function formatNumber(value: number): string {
  return numberFormatter.format(value)
}

function statusLabel(status: StockStatus): string {
  switch (status) {
    case 'AVAILABLE':
      return 'Tersedia'
    case 'LOW_STOCK':
      return 'Stok menipis'
    case 'OUT_OF_STOCK':
      return 'Stok habis'
  }
}

function statusClass(status: StockStatus): string {
  switch (status) {
    case 'AVAILABLE':
      return 'bg-[#E7F4EC] text-[#0F6B3A] border-[#B9DFC9]'
    case 'LOW_STOCK':
      return 'bg-[#FBF3E2] text-[#8A5A12] border-[#EBD5A6]'
    case 'OUT_OF_STOCK':
      return 'bg-[#FBEAE8] text-[#A32F23] border-[#F0C4BF]'
  }
}

function statusDot(status: StockStatus): string {
  switch (status) {
    case 'AVAILABLE':
      return 'bg-[#16834B]'
    case 'LOW_STOCK':
      return 'bg-[#B7791F]'
    case 'OUT_OF_STOCK':
      return 'bg-[#C0392B]'
  }
}

function shortfallText(item: InventoryItem): string {
  if (item.stock_status === 'AVAILABLE') return ''
  const gap = item.minimum_stock - item.stock
  if (gap <= 0) return ''
  return `Kurang ${formatNumber(gap)} ${item.unit} dari minimum`
}

/* ---------- Data ---------- */
function getAccessToken(): string {
  const accessToken = localStorage.getItem('access_token')
  if (!accessToken) {
    throw new Error('Sesi login tidak ditemukan. Silakan masuk kembali.')
  }
  return accessToken
}

function requestKey(): string {
  return `${search.value.trim()}|${stockStatus.value}`
}

async function loadInventory(showSearchLoading = false, force = false): Promise<void> {
  const key = requestKey()
  if (!force && key === lastRequestKey && !error.value) return
  lastRequestKey = key

  const seq = ++requestSeq

  if (showSearchLoading) {
    searchLoading.value = true
  } else {
    loading.value = true
  }
  error.value = ''

  try {
    const result = await getInventory(getAccessToken(), {
      search: search.value.trim() || undefined,
      stock_status: stockStatus.value || undefined,
    })

    if (seq !== requestSeq) return
    inventory.value = result
    page.value = 1
  } catch (err) {
    if (seq !== requestSeq) return
    error.value = err instanceof Error ? err.message : 'Data stok tidak dapat diambil.'
  } finally {
    if (seq === requestSeq) {
      loading.value = false
      searchLoading.value = false
    }
  }
}

/* Ringkasan tidak boleh menggagalkan halaman — gagal = disembunyikan */
async function loadSummary(): Promise<void> {
  try {
    summaryItems.value = await getInventory(getAccessToken())
  } catch {
    summaryItems.value = null
  }
}

function clearSearchTimer(): void {
  if (searchTimer) {
    clearTimeout(searchTimer)
    searchTimer = null
  }
}

function resetFilters(): void {
  clearSearchTimer()
  search.value = ''
  stockStatus.value = ''
  loadInventory(true)
}

function applyStatus(status: StockStatus): void {
  stockStatus.value = stockStatus.value === status ? '' : status
}

function retry(): void {
  loadInventory(false, true)
  loadSummary()
}

function toggleSort(key: 'name' | 'stock'): void {
  const asc = `${key}_asc` as SortValue
  const desc = `${key}_desc` as SortValue
  sortValue.value = sortValue.value === asc ? desc : sortValue.value === desc ? '' : asc
  page.value = 1
}

function ariaSort(key: 'name' | 'stock'): 'ascending' | 'descending' | 'none' {
  if (sortValue.value === `${key}_asc`) return 'ascending'
  if (sortValue.value === `${key}_desc`) return 'descending'
  return 'none'
}

function sortArrow(key: 'name' | 'stock'): string {
  if (sortValue.value === `${key}_asc`) return '↑'
  if (sortValue.value === `${key}_desc`) return '↓'
  return '↕'
}

function goToPage(next: number): void {
  page.value = Math.min(Math.max(1, next), totalPages.value)
}

watch(search, () => {
  clearSearchTimer()
  searchTimer = setTimeout(() => {
    loadInventory(true)
  }, SEARCH_DEBOUNCE_MS)
})

watch(stockStatus, () => {
  clearSearchTimer()
  loadInventory(true)
})

watch(sortValue, () => {
  page.value = 1
})

/* Shortcut "/" memfokuskan pencarian (§13.3) */
function onGlobalKeydown(e: KeyboardEvent): void {
  if (e.key !== '/' || e.ctrlKey || e.metaKey || e.altKey) return
  const target = e.target as HTMLElement | null
  const tag = target?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target?.isContentEditable) return
  e.preventDefault()
  searchInputRef.value?.focus()
}

onMounted(() => {
  window.addEventListener('keydown', onGlobalKeydown)
  loadInventory()
  loadSummary()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKeydown)
  clearSearchTimer()
})
</script>

<template>
  <section class="mx-auto w-full max-w-[1440px] font-sans text-[#17201C]">
    <!-- Breadcrumb -->
    <nav aria-label="Breadcrumb" class="mb-3 text-[13px] leading-[18px] text-[#6B756F]">
      <ol class="flex items-center gap-2">
        <li>Inventory</li>
        <li aria-hidden="true">/</li>
        <li aria-current="page" class="font-medium text-[#46514B]">Stok</li>
      </ol>
    </nav>

    <!-- Page header -->
    <header class="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div>
        <h1 class="text-[28px] font-semibold leading-9 text-[#17201C]">Stok</h1>
        <p class="mt-1 max-w-2xl text-sm leading-5 text-[#46514B]">
          Pantau ketersediaan stok produk aktif. Perubahan stok dilakukan lewat stock opname atau
          stock adjustment dan selalu tercatat di riwayat.
        </p>
      </div>

      <div class="flex flex-wrap gap-3">
        <router-link
          :to="MOVEMENT_ROUTE"
          class="inline-flex h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
        >
          Riwayat Movement
        </router-link>
        <router-link
          :to="ADJUSTMENT_ROUTE"
          class="inline-flex h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
        >
          Stock Adjustment
        </router-link>
        <router-link
          :to="OPNAME_ROUTE"
          class="inline-flex h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
        >
          Stock Opname
        </router-link>
      </div>
    </header>

    <!-- Operational attention -->
    <div
      v-if="summary && (summary.low > 0 || summary.out > 0)"
      class="mb-4 flex flex-col gap-3 rounded-lg border border-[#EBD5A6] bg-[#FBF3E2] px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
      role="status"
    >
      <p class="text-sm leading-5 text-[#6B4A0F]">
        <span class="font-semibold">Perlu perhatian.</span>
        Dari {{ formatNumber(summary.total) }} produk,
        <span class="font-semibold tabular-nums">{{ formatNumber(summary.out) }}</span> stok habis dan
        <span class="font-semibold tabular-nums">{{ formatNumber(summary.low) }}</span> stok menipis.
      </p>

      <div class="flex flex-wrap gap-2">
        <button
          v-if="summary.out > 0"
          type="button"
          :aria-pressed="stockStatus === 'OUT_OF_STOCK'"
          class="inline-flex h-9 items-center justify-center rounded-lg border px-3 text-[13px] font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          :class="
            stockStatus === 'OUT_OF_STOCK'
              ? 'border-[#176B4D] bg-[#DCEFE7] text-[#164A38]'
              : 'border-[#D6DDD9] bg-white text-[#17201C] hover:bg-[#F1F4F2]'
          "
          @click="applyStatus('OUT_OF_STOCK')"
        >
          Lihat stok habis
        </button>
        <button
          v-if="summary.low > 0"
          type="button"
          :aria-pressed="stockStatus === 'LOW_STOCK'"
          class="inline-flex h-9 items-center justify-center rounded-lg border px-3 text-[13px] font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          :class="
            stockStatus === 'LOW_STOCK'
              ? 'border-[#176B4D] bg-[#DCEFE7] text-[#164A38]'
              : 'border-[#D6DDD9] bg-white text-[#17201C] hover:bg-[#F1F4F2]'
          "
          @click="applyStatus('LOW_STOCK')"
        >
          Lihat stok menipis
        </button>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="mb-4 rounded-lg border border-[#D6DDD9] bg-white p-4">
      <div class="grid gap-4 md:grid-cols-[minmax(0,1fr)_200px_200px_auto]">
        <div>
          <label for="inventory-search" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
            Cari produk
          </label>
          <div class="relative">
            <input
              id="inventory-search"
              ref="searchInputRef"
              v-model="search"
              type="search"
              autocomplete="off"
              placeholder="Nama, SKU, atau barcode (tekan / untuk fokus)"
              class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 pr-10 text-sm text-[#17201C] placeholder:text-[#6B756F] focus:border-[#176B4D] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
            />
            <span
              v-if="searchLoading"
              class="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin rounded-full border-2 border-[#D6DDD9] border-t-[#176B4D]"
              aria-hidden="true"
            />
          </div>
        </div>

        <div>
          <label for="stock-status" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
            Status stok
          </label>
          <select
            id="stock-status"
            v-model="stockStatus"
            class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm text-[#17201C] focus:border-[#176B4D] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
          >
            <option v-for="option in statusOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div class="md:hidden">
          <label for="inventory-sort" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
            Urutkan
          </label>
          <select
            id="inventory-sort"
            v-model="sortValue"
            class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm text-[#17201C] focus:border-[#176B4D] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
          >
            <option v-for="option in sortOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div class="flex items-end md:col-start-4">
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
    </div>

    <!-- Loading (initial) -->
    <div
      v-if="loading"
      class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
      role="status"
      aria-label="Memuat data stok"
    >
      <div class="hidden md:block">
        <div class="grid grid-cols-4 gap-4 border-b border-[#E6EBE8] bg-[#F1F4F2] px-4 py-3">
          <div v-for="index in 4" :key="index" class="h-4 animate-pulse rounded bg-[#E6EBE8]" />
        </div>
        <div class="divide-y divide-[#E6EBE8]">
          <div v-for="row in 6" :key="row" class="grid grid-cols-4 gap-4 px-4 py-4">
            <div v-for="column in 4" :key="column" class="h-4 animate-pulse rounded bg-[#F1F4F2]" />
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
      <h2 class="text-lg font-semibold text-[#17201C]">Data stok gagal dimuat</h2>
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
      v-else-if="inventory.length === 0 && hasActiveFilter"
      class="rounded-lg border border-[#D6DDD9] bg-white p-10 text-center"
    >
      <div
        aria-hidden="true"
        class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#F0F8F5] text-xl text-[#176B4D]"
      >⌕</div>
      <h2 class="text-lg font-semibold text-[#17201C]">Tidak ada produk yang cocok</h2>
      <p class="mx-auto mt-1 max-w-md text-sm leading-5 text-[#46514B]">
        Tidak ditemukan produk untuk {{ activeFilterSummary }}. Periksa ejaan nama, SKU, atau
        barcode, atau tampilkan semua stok.
      </p>
      <button
        type="button"
        class="mt-5 inline-flex h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
        @click="resetFilters"
      >
        Tampilkan semua stok
      </button>
    </div>

    <!-- Empty: no products at all -->
    <div
      v-else-if="inventory.length === 0"
      class="rounded-lg border border-[#D6DDD9] bg-white p-10 text-center"
    >
      <div
        aria-hidden="true"
        class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#F0F8F5] text-xl text-[#176B4D]"
      >▦</div>
      <h2 class="text-lg font-semibold text-[#17201C]">Belum ada data stok</h2>
      <p class="mx-auto mt-1 max-w-md text-sm leading-5 text-[#46514B]">
        Stok muncul setelah ada produk aktif. Tambahkan produk, lalu catat penerimaan barang agar
        stok mulai terisi.
      </p>
      <router-link
        :to="PRODUCTS_ROUTE"
        class="mt-5 inline-flex h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
      >
        Lihat Produk
      </router-link>
    </div>

    <!-- Data -->
    <div
      v-else
      class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
      :aria-busy="searchLoading"
    >
      <div class="flex items-center justify-between gap-3 border-b border-[#E6EBE8] px-4 py-3">
        <div>
          <h2 class="text-sm font-semibold leading-5 text-[#17201C]">Daftar stok</h2>
          <p class="mt-0.5 text-xs leading-4 text-[#6B756F]">
            {{ formatNumber(totalItems) }} produk
            <template v-if="hasActiveFilter"> · Filter: {{ activeFilterSummary }}</template>
          </p>
        </div>

        <p v-if="searchLoading" class="flex items-center gap-2 text-xs text-[#46514B]" role="status">
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
        :class="searchLoading ? 'opacity-60' : ''"
      >
        <table class="min-w-full border-separate border-spacing-0">
          <caption class="sr-only">
            Daftar stok produk aktif beserta status ketersediaannya
          </caption>
          <thead>
            <tr>
              <th
                scope="col"
                :aria-sort="ariaSort('name')"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                <button
                  type="button"
                  class="inline-flex items-center gap-1 rounded-sm uppercase tracking-wide hover:text-[#176B4D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
                  @click="toggleSort('name')"
                >
                  Produk
                  <span aria-hidden="true">{{ sortArrow('name') }}</span>
                  <span class="sr-only">, ubah urutan nama</span>
                </button>
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                Status
              </th>
              <th
                scope="col"
                :aria-sort="ariaSort('stock')"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                <button
                  type="button"
                  class="inline-flex items-center gap-1 rounded-sm uppercase tracking-wide hover:text-[#176B4D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
                  @click="toggleSort('stock')"
                >
                  Stok
                  <span aria-hidden="true">{{ sortArrow('stock') }}</span>
                  <span class="sr-only">, ubah urutan stok</span>
                </button>
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 hidden border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B] lg:table-cell"
              >
                Minimum
              </th>
            </tr>
          </thead>

          <tbody class="bg-white">
            <tr v-for="item in pagedInventory" :key="item.product_id" class="hover:bg-[#F8FAF9]">
              <td class="border-b border-[#E6EBE8] px-4 py-3 align-top">
                <div class="text-sm font-semibold leading-5 text-[#17201C]">{{ item.name }}</div>
                <div class="text-[13px] leading-[18px] text-[#6B756F]">
                  SKU {{ item.sku }}
                  <template v-if="item.barcode">
                    <span aria-hidden="true"> · </span>Barcode {{ item.barcode }}
                  </template>
                </div>
              </td>

              <td class="border-b border-[#E6EBE8] px-4 py-3 align-top">
                <span
                  class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-medium"
                  :class="statusClass(item.stock_status)"
                >
                  <span class="h-1.5 w-1.5 rounded-full" :class="statusDot(item.stock_status)" aria-hidden="true" />
                  {{ statusLabel(item.stock_status) }}
                </span>
                <p v-if="shortfallText(item)" class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                  {{ shortfallText(item) }}
                </p>
              </td>

              <td class="whitespace-nowrap border-b border-[#E6EBE8] px-4 py-3 text-right align-top">
                <span class="text-sm font-semibold tabular-nums text-[#17201C]">{{ formatNumber(item.stock) }}</span>
                <span class="ml-1 text-[13px] text-[#6B756F]">{{ item.unit }}</span>
              </td>

              <td
                class="hidden whitespace-nowrap border-b border-[#E6EBE8] px-4 py-3 text-right align-top text-sm tabular-nums text-[#46514B] lg:table-cell"
              >
                {{ formatNumber(item.minimum_stock) }}
                <span class="ml-1 text-[13px] text-[#6B756F]">{{ item.unit }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Cards (mobile) -->
      <div class="divide-y divide-[#E6EBE8] md:hidden" :class="searchLoading ? 'opacity-60' : ''">
        <article v-for="item in pagedInventory" :key="item.product_id" class="p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <h3 class="text-sm font-semibold leading-5 text-[#17201C]">{{ item.name }}</h3>
              <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">SKU {{ item.sku }}</p>
              <p v-if="item.barcode" class="break-all text-[13px] leading-[18px] text-[#6B756F]">
                Barcode {{ item.barcode }}
              </p>
            </div>

            <span
              class="inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium"
              :class="statusClass(item.stock_status)"
            >
              <span class="h-1.5 w-1.5 rounded-full" :class="statusDot(item.stock_status)" aria-hidden="true" />
              {{ statusLabel(item.stock_status) }}
            </span>
          </div>

          <dl class="mt-3 grid grid-cols-2 gap-3 rounded-lg bg-[#F8FAF9] px-3 py-2.5">
            <div>
              <dt class="text-xs text-[#6B756F]">Stok</dt>
              <dd class="mt-0.5 text-sm font-semibold tabular-nums text-[#17201C]">
                {{ formatNumber(item.stock) }}
                <span class="text-[13px] font-normal text-[#6B756F]">{{ item.unit }}</span>
              </dd>
            </div>
            <div>
              <dt class="text-xs text-[#6B756F]">Minimum</dt>
              <dd class="mt-0.5 text-sm tabular-nums text-[#46514B]">
                {{ formatNumber(item.minimum_stock) }}
                <span class="text-[13px] text-[#6B756F]">{{ item.unit }}</span>
              </dd>
            </div>
          </dl>

          <p v-if="shortfallText(item)" class="mt-2 text-[13px] leading-[18px] text-[#6B756F]">
            {{ shortfallText(item) }}
          </p>
        </article>
      </div>

      <!-- Pagination -->
      <nav
        aria-label="Paginasi daftar stok"
        class="flex flex-col gap-3 border-t border-[#E6EBE8] px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
      >
        <p class="text-[13px] leading-[18px] tabular-nums text-[#46514B]" role="status" aria-live="polite">
          Menampilkan {{ formatNumber(rangeStart) }}–{{ formatNumber(rangeEnd) }} dari
          {{ formatNumber(totalItems) }} produk
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