<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  getInventory,
} from '../../api/inventory'
import type {
  InventoryItem,
  StockStatus,
} from '../../types/inventory'

const inventory = ref<InventoryItem[]>([])
const search = ref('')
const stockStatus = ref<StockStatus | ''>('')

const loading = ref(true)
const error = ref('')
const searchLoading = ref(false)

let searchTimer: ReturnType<typeof setTimeout> | null = null

const hasData = computed(
  () => inventory.value.length > 0,
)

const isEmpty = computed(
  () => !loading.value && !error.value && !hasData.value,
)

const statusOptions: Array<{
  value: StockStatus | ''
  label: string
}> = [
  {
    value: '',
    label: 'Semua status',
  },
  {
    value: 'AVAILABLE',
    label: 'Tersedia',
  },
  {
    value: 'LOW_STOCK',
    label: 'Stok menipis',
  },
  {
    value: 'OUT_OF_STOCK',
    label: 'Stok habis',
  },
]

function getAccessToken(): string {
  const accessToken = localStorage.getItem(
    'access_token',
  )

  if (!accessToken) {
    throw new Error(
      'Sesi login tidak ditemukan.',
    )
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

function statusClass(status: StockStatus): string {
  switch (status) {
    case 'AVAILABLE':
      return 'bg-green-50 text-green-700 ring-green-600/20'
    case 'LOW_STOCK':
      return 'bg-amber-50 text-amber-700 ring-amber-600/20'
    case 'OUT_OF_STOCK':
      return 'bg-red-50 text-red-700 ring-red-600/20'
  }
}

async function loadInventory(
  showSearchLoading = false,
): Promise<void> {
  const accessToken = getAccessToken()

  if (showSearchLoading) {
    searchLoading.value = true
  } else {
    loading.value = true
  }

  error.value = ''

  try {
    inventory.value = await getInventory(
      accessToken,
      {
        search: search.value.trim() || undefined,
        stock_status:
          stockStatus.value || undefined,
      },
    )
  } catch (err) {
    error.value =
      err instanceof Error
        ? err.message
        : 'Gagal mengambil data stok.'
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

watch(
  search,
  () => {
    if (searchTimer) {
      clearTimeout(searchTimer)
    }

    searchTimer = setTimeout(() => {
      loadInventory(true)
    }, 350)
  },
)

watch(stockStatus, () => {
  loadInventory(true)
})

onMounted(() => {
  loadInventory()
})
</script>

<template>
  <section class="space-y-6">
    <div
      class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"
    >
      <div>
        <p
          class="text-sm font-medium text-gray-500"
        >
          Inventory
        </p>

        <h1
          class="mt-1 text-2xl font-semibold text-gray-900"
        >
          Stok
        </h1>

        <p
          class="mt-1 text-sm text-gray-500"
        >
          Pantau ketersediaan stok produk aktif.
        </p>
      </div>
    </div>

    <div
      class="rounded-lg border border-gray-200 bg-white p-4"
    >
      <div
        class="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px_auto]"
      >
        <div>
          <label
            for="inventory-search"
            class="mb-1.5 block text-sm font-medium text-gray-700"
          >
            Cari produk
          </label>

          <div class="relative">
            <input
              id="inventory-search"
              v-model="search"
              type="search"
              placeholder="Cari nama, SKU, atau barcode..."
              class="w-full rounded-md border border-gray-300 px-3 py-2.5 pr-10 text-sm text-gray-900 outline-none transition focus:border-green-700 focus:ring-2 focus:ring-green-700/20"
            />

            <div
              v-if="searchLoading"
              class="absolute right-3 top-1/2 -translate-y-1/2"
              aria-label="Memuat"
            >
              <div
                class="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-green-700"
              />
            </div>
          </div>
        </div>

        <div>
          <label
            for="stock-status"
            class="mb-1.5 block text-sm font-medium text-gray-700"
          >
            Status stok
          </label>

          <select
            id="stock-status"
            v-model="stockStatus"
            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 outline-none transition focus:border-green-700 focus:ring-2 focus:ring-green-700/20"
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
            class="w-full rounded-md border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-700/20 md:w-auto"
            @click="resetFilters"
          >
            Reset
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="loading"
      class="overflow-hidden rounded-lg border border-gray-200 bg-white"
      aria-live="polite"
      aria-label="Memuat data stok"
    >
      <div class="hidden md:block">
        <div
          class="grid grid-cols-7 gap-4 border-b border-gray-200 bg-gray-50 px-4 py-3"
        >
          <div
            v-for="index in 7"
            :key="index"
            class="h-4 animate-pulse rounded bg-gray-200"
          />
        </div>

        <div class="divide-y divide-gray-100">
          <div
            v-for="row in 6"
            :key="row"
            class="grid grid-cols-7 gap-4 px-4 py-4"
          >
            <div
              v-for="column in 7"
              :key="column"
              class="h-4 animate-pulse rounded bg-gray-100"
            />
          </div>
        </div>
      </div>

      <div class="space-y-3 p-4 md:hidden">
        <div
          v-for="row in 5"
          :key="row"
          class="space-y-3 rounded-md border border-gray-100 p-4"
        >
          <div
            class="h-5 w-2/3 animate-pulse rounded bg-gray-100"
          />
          <div
            class="h-4 w-1/2 animate-pulse rounded bg-gray-100"
          />
          <div
            class="h-4 w-1/3 animate-pulse rounded bg-gray-100"
          />
        </div>
      </div>
    </div>

    <div
      v-else-if="error"
      class="rounded-lg border border-red-200 bg-red-50 p-5"
      role="alert"
    >
      <h2
        class="font-semibold text-red-800"
      >
        Gagal memuat stok
      </h2>

      <p
        class="mt-1 text-sm text-red-700"
      >
        {{ error }}
      </p>

      <button
        type="button"
        class="mt-4 rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-700/30"
        @click="retry"
      >
        Coba lagi
      </button>
    </div>

    <div
      v-else-if="isEmpty"
      class="rounded-lg border border-gray-200 bg-white p-8 text-center"
    >
      <h2
        class="font-semibold text-gray-900"
      >
        Tidak ada data stok
      </h2>

      <p
        class="mx-auto mt-1 max-w-md text-sm text-gray-500"
      >
        Tidak ada produk yang sesuai dengan pencarian
        atau filter yang dipilih.
      </p>

      <button
        v-if="search || stockStatus"
        type="button"
        class="mt-4 rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-700/20"
        @click="resetFilters"
      >
        Tampilkan semua stok
      </button>
    </div>

    <div
      v-else
      class="overflow-hidden rounded-lg border border-gray-200 bg-white"
    >
      <div
        class="flex items-center justify-between border-b border-gray-200 px-4 py-3"
      >
        <div>
          <p
            class="text-sm font-medium text-gray-900"
          >
            Daftar stok
          </p>

          <p
            class="mt-0.5 text-xs text-gray-500"
          >
            {{ inventory.length }} produk
          </p>
        </div>
      </div>

      <div class="hidden overflow-x-auto md:block">
        <table
          class="min-w-full divide-y divide-gray-200"
        >
          <thead class="bg-gray-50">
            <tr>
              <th
                scope="col"
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Produk
              </th>

              <th
                scope="col"
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                SKU
              </th>

              <th
                scope="col"
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Barcode
              </th>

              <th
                scope="col"
                class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Stok
              </th>

              <th
                scope="col"
                class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Minimum
              </th>

              <th
                scope="col"
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Status
              </th>

              <th
                scope="col"
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Unit
              </th>
            </tr>
          </thead>

          <tbody
            class="divide-y divide-gray-100 bg-white"
          >
            <tr
              v-for="item in inventory"
              :key="item.product_id"
              class="hover:bg-gray-50"
            >
              <td class="px-4 py-4">
                <div
                  class="font-medium text-gray-900"
                >
                  {{ item.name }}
                </div>
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-sm text-gray-600"
              >
                {{ item.sku }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-sm text-gray-600"
              >
                {{ item.barcode || '-' }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-right text-sm font-semibold text-gray-900"
              >
                {{ formatStock(item.stock) }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-right text-sm text-gray-600"
              >
                {{ formatStock(item.minimum_stock) }}
              </td>

              <td class="px-4 py-4">
                <span
                  class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset"
                  :class="statusClass(item.stock_status)"
                >
                  {{ statusLabel(item.stock_status) }}
                </span>
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-sm text-gray-600"
              >
                {{ item.unit }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="divide-y divide-gray-100 md:hidden">
        <article
          v-for="item in inventory"
          :key="item.product_id"
          class="p-4"
        >
          <div
            class="flex items-start justify-between gap-3"
          >
            <div class="min-w-0">
              <h2
                class="truncate font-medium text-gray-900"
              >
                {{ item.name }}
              </h2>

              <p
                class="mt-1 text-sm text-gray-500"
              >
                {{ item.sku }}
                <span aria-hidden="true">·</span>
                {{ item.unit }}
              </p>
            </div>

            <span
              class="shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset"
              :class="statusClass(item.stock_status)"
            >
              {{ statusLabel(item.stock_status) }}
            </span>
          </div>

          <dl
            class="mt-4 grid grid-cols-2 gap-3"
          >
            <div>
              <dt
                class="text-xs text-gray-500"
              >
                Stok
              </dt>

              <dd
                class="mt-1 font-semibold text-gray-900"
              >
                {{ formatStock(item.stock) }}
              </dd>
            </div>

            <div>
              <dt
                class="text-xs text-gray-500"
              >
                Minimum
              </dt>

              <dd
                class="mt-1 font-medium text-gray-700"
              >
                {{ formatStock(item.minimum_stock) }}
              </dd>
            </div>

            <div class="col-span-2">
              <dt
                class="text-xs text-gray-500"
              >
                Barcode
              </dt>

              <dd
                class="mt-1 break-all text-sm text-gray-700"
              >
                {{ item.barcode || '-' }}
              </dd>
            </div>
          </dl>
        </article>
      </div>
    </div>
  </section>
</template>