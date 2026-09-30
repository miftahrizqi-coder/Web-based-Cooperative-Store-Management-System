<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getInventory } from '../../api/inventory'
import type { InventoryItem, StockStatus } from '../../types/inventory'

const PAGE_SIZE = 25

const inventory = ref<InventoryItem[]>([])
const search = ref('')
const stockStatus = ref<StockStatus | ''>('')
const page = ref(1)

const loading = ref(true)
const error = ref('')
const searchLoading = ref(false)

let searchTimer: ReturnType<typeof setTimeout> | null = null

const hasData = computed(() => inventory.value.length > 0)
const hasActiveFilter = computed(
  () => Boolean(search.value.trim()) || Boolean(stockStatus.value),
)
const isEmpty = computed(
  () => !loading.value && !error.value && !hasData.value,
)

const totalPages = computed(() =>
  Math.max(1, Math.ceil(inventory.value.length / PAGE_SIZE)),
)
const pagedInventory = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return inventory.value.slice(start, start + PAGE_SIZE)
})
const rangeStart = computed(() =>
  hasData.value ? (page.value - 1) * PAGE_SIZE + 1 : 0,
)
const rangeEnd = computed(() =>
  Math.min(page.value * PAGE_SIZE, inventory.value.length),
)

const statusOptions: Array<{ value: StockStatus | ''; label: string }> = [
  { value: '', label: 'Semua status' },
  { value: 'AVAILABLE', label: 'Tersedia' },
  { value: 'LOW_STOCK', label: 'Stok menipis' },
  { value: 'OUT_OF_STOCK', label: 'Stok habis' },
]

function getAccessToken(): string {
  const accessToken = localStorage.getItem('access_token')

  if (!accessToken) {
    throw new Error('Sesi login tidak ditemukan.')
  }

  return accessToken
}

function formatStock(value: number): string {
  return new Intl.NumberFormat('id-ID', {
    maximumFractionDigits: 2,
  }).format(value)
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

// Semantic mapping §3.1: low stock → warning, out of stock → danger, available → success
function statusClass(status: StockStatus): string {
  switch (status) {
    case 'AVAILABLE':
      return 'bg-[#16834B]/10 text-[#16834B]'
    case 'LOW_STOCK':
      return 'bg-[#B7791F]/10 text-[#8A5A14]'
    case 'OUT_OF_STOCK':
      return 'bg-[#C0392B]/10 text-[#C0392B]'
  }
}

function statusDotClass(status: StockStatus): string {
  switch (status) {
    case 'AVAILABLE':
      return 'bg-[#16834B]'
    case 'LOW_STOCK':
      return 'bg-[#B7791F]'
    case 'OUT_OF_STOCK':
      return 'bg-[#C0392B]'
  }
}

async function loadInventory(showSearchLoading = false): Promise<void> {
  if (showSearchLoading) {
    searchLoading.value = true
  } else {
    loading.value = true
  }

  error.value = ''

  try {
    const accessToken = getAccessToken()

    inventory.value = await getInventory(accessToken, {
      search: search.value.trim() || undefined,
      stock_status: stockStatus.value || undefined,
    })
    page.value = 1
  } catch (err) {
    error.value =
      err instanceof Error ? err.message : 'Gagal mengambil data stok.'
  } finally {
    loading.value = false
    searchLoading.value = false
  }
}

function resetFilters(): void {
  search.value = ''
  stockStatus.value = ''
  loadInventory()
}

function retry(): void {
  loadInventory()
}

function goToPage(next: number): void {
  page.value = Math.min(Math.max(1, next), totalPages.value)
}

watch(search, () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }

  searchTimer = setTimeout(() => {
    loadInventory(true)
  }, 350)
})

watch(stockStatus, () => {
  loadInventory(true)
})

onMounted(() => {
  loadInventory()
})

onBeforeUnmount(() => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
})
</script>

<template>
  <section
    class="space-y-6 font-['Inter',ui-sans-serif,system-ui,sans-serif] text-[#17201C]"
  >
    <!-- Page header: breadcrumb, title, context -->
    <header>
      <nav aria-label="Breadcrumb" class="text-[13px] leading-[18px] text-[#6B756F]">
        <ol class="flex items-center gap-1.5">
          <li>Inventory</li>
          <li aria-hidden="true">/</li>
          <li aria-current="page" class="font-medium text-[#46514B]">Stok</li>
        </ol>
      </nav>

      <h1 class="mt-2 text-[28px] font-semibold leading-9 text-[#17201C]">
        Stok
      </h1>

      <p class="mt-1 text-sm leading-5 text-[#46514B]">
        Pantau ketersediaan stok produk aktif. Stok berubah lewat penerimaan
        barang, penjualan, retur, atau penyesuaian, bukan diedit dari halaman
        ini.
      </p>
    </header>

    <!-- Filter bar: dekat dengan data -->
    <div class="rounded-lg border border-[#D6DDD9] bg-white p-4">
      <div class="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px_auto]">
        <div>
          <label
            for="inventory-search"
            class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#17201C]"
          >
            Cari produk
          </label>

          <div class="relative">
            <input
              id="inventory-search"
              v-model="search"
              type="search"
              placeholder="Cari nama, SKU, atau barcode..."
              class="w-full rounded-lg border border-[#D6DDD9] bg-white px-3 py-2.5 pr-10 text-sm text-[#17201C] placeholder:text-[#6B756F] hover:border-[#6B756F] focus:border-[#176B4D] focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
            />

            <div
              v-if="searchLoading"
              class="absolute right-3 top-1/2 -translate-y-1/2"
              role="status"
              aria-label="Memuat hasil pencarian"
            >
              <div
                class="h-4 w-4 animate-spin rounded-full border-2 border-[#D6DDD9] border-t-[#176B4D]"
              />
            </div>
          </div>
        </div>

        <div>
          <label
            for="stock-status"
            class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#17201C]"
          >
            Status stok
          </label>

          <select
            id="stock-status"
            v-model="stockStatus"
            class="w-full rounded-lg border border-[#D6DDD9] bg-white px-3 py-2.5 text-sm text-[#17201C] hover:border-[#6B756F] focus:border-[#176B4D] focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
          >
            <option
              v-for="option in statusOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>

        <div class="flex items-end">
          <button
            type="button"
            :disabled="!hasActiveFilter"
            class="w-full rounded-lg border border-[#D6DDD9] bg-white px-4 py-2.5 text-sm font-medium text-[#17201C] transition-colors hover:bg-[#F1F4F2] focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D] disabled:cursor-not-allowed disabled:text-[#6B756F] disabled:opacity-60 disabled:hover:bg-white md:w-auto"
            @click="resetFilters"
          >
            Reset
          </button>
        </div>
      </div>
    </div>

    <!-- Loading: skeleton -->
    <div
      v-if="loading"
      class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
      aria-busy="true"
    >
      <span class="sr-only" role="status">Memuat data stok</span>

      <div class="hidden md:block" aria-hidden="true">
        <div
          class="grid grid-cols-7 gap-4 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3"
        >
          <div
            v-for="index in 7"
            :key="index"
            class="h-4 animate-pulse rounded bg-[#E6EBE8]"
          />
        </div>

        <div class="divide-y divide-[#E6EBE8]">
          <div
            v-for="row in 6"
            :key="row"
            class="grid grid-cols-7 gap-4 px-4 py-4"
          >
            <div
              v-for="column in 7"
              :key="column"
              class="h-4 animate-pulse rounded bg-[#F1F4F2]"
            />
          </div>
        </div>
      </div>

      <div class="space-y-3 p-4 md:hidden" aria-hidden="true">
        <div
          v-for="row in 5"
          :key="row"
          class="space-y-3 rounded-lg border border-[#E6EBE8] p-4"
        >
          <div class="h-5 w-2/3 animate-pulse rounded bg-[#F1F4F2]" />
          <div class="h-4 w-1/2 animate-pulse rounded bg-[#F1F4F2]" />
          <div class="h-4 w-1/3 animate-pulse rounded bg-[#F1F4F2]" />
        </div>
      </div>
    </div>

    <!-- Error: apa yang gagal, apakah data berubah, apa yang bisa dilakukan -->
    <div
      v-else-if="error"
      class="rounded-lg border border-[#C0392B]/30 bg-[#C0392B]/5 p-5"
      role="alert"
    >
      <h2 class="font-semibold text-[#C0392B]">Gagal memuat data stok</h2>

      <p class="mt-1 text-sm text-[#46514B]">
        {{ error }} Tidak ada perubahan pada stok. Periksa koneksi Anda, lalu
        coba lagi.
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg bg-[#176B4D] px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#1F805D] active:bg-[#164A38] focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
        @click="retry"
      >
        Coba lagi
      </button>
    </div>

    <!-- Empty: apa yang kosong, kenapa, apa yang bisa dilakukan -->
    <div
      v-else-if="isEmpty"
      class="rounded-lg border border-[#D6DDD9] bg-white p-8 text-center"
    >
      <div
        class="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-[#F0F8F5] text-[#176B4D]"
        aria-hidden="true"
      >
        <svg
          class="h-5 w-5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M21 8l-9-5-9 5 9 5 9-5z" />
          <path d="M3 8v8l9 5 9-5V8" />
          <path d="M12 13v8" />
        </svg>
      </div>

      <template v-if="hasActiveFilter">
        <h2 class="mt-4 font-semibold text-[#17201C]">
          Tidak ada produk yang cocok
        </h2>

        <p class="mx-auto mt-1 max-w-md text-sm text-[#46514B]">
          Tidak ada stok yang sesuai dengan pencarian atau filter yang dipilih.
          Coba kata kunci lain atau tampilkan semua stok.
        </p>

        <button
          type="button"
          class="mt-4 rounded-lg border border-[#D6DDD9] bg-white px-4 py-2 text-sm font-medium text-[#17201C] transition-colors hover:bg-[#F1F4F2] focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
          @click="resetFilters"
        >
          Tampilkan semua stok
        </button>
      </template>

      <template v-else>
        <h2 class="mt-4 font-semibold text-[#17201C]">
          Belum ada data stok
        </h2>

        <p class="mx-auto mt-1 max-w-md text-sm text-[#46514B]">
          Stok muncul setelah ada produk aktif dan penerimaan barang
          dikonfirmasi. Tambahkan produk atau buat penerimaan barang untuk
          memulai.
        </p>
      </template>
    </div>

    <!-- Data -->
    <div
      v-else
      class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
    >
      <div
        class="flex items-center justify-between border-b border-[#D6DDD9] px-4 py-3"
      >
        <div>
          <h2 class="text-sm font-semibold text-[#17201C]">Daftar stok</h2>
          <p class="mt-0.5 text-xs text-[#6B756F]" role="status">
            {{ inventory.length }} produk
          </p>
        </div>
      </div>

      <!-- Tabel (tablet & desktop) -->
      <div class="hidden max-h-[70vh] overflow-auto md:block">
        <table class="min-w-full border-separate border-spacing-0">
          <caption class="sr-only">
            Daftar stok produk
          </caption>

          <thead>
            <tr>
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
                SKU
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                Barcode
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                Stok
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                Minimum
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                Status
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
              >
                Unit
              </th>
            </tr>
          </thead>

          <tbody class="bg-white">
            <tr
              v-for="item in pagedInventory"
              :key="item.product_id"
              class="hover:bg-[#F8FAF9]"
            >
              <th
                scope="row"
                class="border-b border-[#E6EBE8] px-4 py-3.5 text-left text-sm font-semibold text-[#17201C]"
              >
                {{ item.name }}
              </th>

              <td
                class="whitespace-nowrap border-b border-[#E6EBE8] px-4 py-3.5 text-sm tabular-nums text-[#46514B]"
              >
                {{ item.sku }}
              </td>

              <td
                class="whitespace-nowrap border-b border-[#E6EBE8] px-4 py-3.5 text-sm tabular-nums text-[#46514B]"
              >
                {{ item.barcode || '-' }}
              </td>

              <td
                class="whitespace-nowrap border-b border-[#E6EBE8] px-4 py-3.5 text-right text-sm font-semibold tabular-nums text-[#17201C]"
              >
                {{ formatStock(item.stock) }}
              </td>

              <td
                class="whitespace-nowrap border-b border-[#E6EBE8] px-4 py-3.5 text-right text-sm tabular-nums text-[#46514B]"
              >
                {{ formatStock(item.minimum_stock) }}
              </td>

              <td class="border-b border-[#E6EBE8] px-4 py-3.5">
                <span
                  class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-medium leading-4"
                  :class="statusClass(item.stock_status)"
                >
                  <span
                    class="h-1.5 w-1.5 rounded-full"
                    :class="statusDotClass(item.stock_status)"
                    aria-hidden="true"
                  />
                  {{ statusLabel(item.stock_status) }}
                </span>
              </td>

              <td
                class="whitespace-nowrap border-b border-[#E6EBE8] px-4 py-3.5 text-sm text-[#46514B]"
              >
                {{ item.unit }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Kartu ringkas (mobile) -->
      <div class="divide-y divide-[#E6EBE8] md:hidden">
        <article
          v-for="item in pagedInventory"
          :key="item.product_id"
          class="p-4"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <h3 class="truncate text-sm font-semibold text-[#17201C]">
                {{ item.name }}
              </h3>

              <p class="mt-1 text-[13px] leading-[18px] text-[#46514B]">
                {{ item.sku }}
                <span aria-hidden="true">·</span>
                {{ item.unit }}
              </p>
            </div>

            <span
              class="inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium leading-4"
              :class="statusClass(item.stock_status)"
            >
              <span
                class="h-1.5 w-1.5 rounded-full"
                :class="statusDotClass(item.stock_status)"
                aria-hidden="true"
              />
              {{ statusLabel(item.stock_status) }}
            </span>
          </div>

          <dl class="mt-4 grid grid-cols-2 gap-3">
            <div>
              <dt class="text-xs text-[#6B756F]">Stok</dt>
              <dd class="mt-1 font-semibold tabular-nums text-[#17201C]">
                {{ formatStock(item.stock) }}
              </dd>
            </div>

            <div>
              <dt class="text-xs text-[#6B756F]">Minimum</dt>
              <dd class="mt-1 font-medium tabular-nums text-[#46514B]">
                {{ formatStock(item.minimum_stock) }}
              </dd>
            </div>

            <div class="col-span-2">
              <dt class="text-xs text-[#6B756F]">Barcode</dt>
              <dd class="mt-1 break-all text-sm tabular-nums text-[#46514B]">
                {{ item.barcode || '-' }}
              </dd>
            </div>
          </dl>
        </article>
      </div>

      <!-- Pagination -->
      <nav
        v-if="totalPages > 1"
        class="flex flex-col gap-3 border-t border-[#D6DDD9] px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
        aria-label="Paginasi daftar stok"
      >
        <p class="text-[13px] leading-[18px] text-[#46514B]">
          Menampilkan
          <span class="font-medium tabular-nums">{{ rangeStart }}–{{ rangeEnd }}</span>
          dari
          <span class="font-medium tabular-nums">{{ inventory.length }}</span>
          produk
        </p>

        <div class="flex items-center gap-2">
          <button
            type="button"
            :disabled="page <= 1"
            class="rounded-lg border border-[#D6DDD9] bg-white px-3 py-1.5 text-sm font-medium text-[#17201C] transition-colors hover:bg-[#F1F4F2] focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-white"
            @click="goToPage(page - 1)"
          >
            Sebelumnya
          </button>

          <span class="px-1 text-[13px] tabular-nums text-[#46514B]" aria-current="page">
            Halaman {{ page }} dari {{ totalPages }}
          </span>

          <button
            type="button"
            :disabled="page >= totalPages"
            class="rounded-lg border border-[#D6DDD9] bg-white px-3 py-1.5 text-sm font-medium text-[#17201C] transition-colors hover:bg-[#F1F4F2] focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-white"
            @click="goToPage(page + 1)"
          >
            Berikutnya
          </button>
        </div>
      </nav>
    </div>
  </section>
</template>