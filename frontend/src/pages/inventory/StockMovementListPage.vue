<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import {
  getInventory,
  getStockMovements,
} from '../../api/inventory'

import type {
  InventoryItem,
  StockMovement,
  StockMovementType,
} from '../../types/inventory'

const movements = ref<StockMovement[]>([])
const products = ref<InventoryItem[]>([])

const selectedProduct = ref('')
const selectedMovementType =
  ref<StockMovementType | ''>('')

const loading = ref(true)
const error = ref('')
const filterLoading = ref(false)

const movementTypeOptions: Array<{
  value: StockMovementType | ''
  label: string
}> = [
  {
    value: '',
    label: 'Semua tipe',
  },
  {
    value: 'PURCHASE',
    label: 'Pembelian',
  },
  {
    value: 'SALE',
    label: 'Penjualan',
  },
  {
    value: 'SALE_RETURN',
    label: 'Retur Penjualan',
  },
  {
    value: 'PURCHASE_RETURN',
    label: 'Retur Pembelian',
  },
  {
    value: 'ADJUSTMENT',
    label: 'Penyesuaian Stok',
  },
  {
    value: 'STOCK_OPNAME',
    label: 'Stock Opname',
  },
]

const isEmpty = computed(
  () =>
    !loading.value &&
    !error.value &&
    movements.value.length === 0,
)

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

function formatNumber(value: number): string {
  return new Intl.NumberFormat('id-ID', {
    maximumFractionDigits: 2,
  }).format(value)
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function movementLabel(
  type: StockMovementType,
): string {
  switch (type) {
    case 'PURCHASE':
      return 'Pembelian'

    case 'SALE':
      return 'Penjualan'

    case 'SALE_RETURN':
      return 'Retur Penjualan'

    case 'PURCHASE_RETURN':
      return 'Retur Pembelian'

    case 'ADJUSTMENT':
      return 'Penyesuaian Stok'

    case 'STOCK_OPNAME':
      return 'Stock Opname'
  }
}

function movementClass(
  type: StockMovementType,
): string {
  switch (type) {
    case 'PURCHASE':
    case 'SALE_RETURN':
      return 'bg-green-50 text-green-700 ring-green-600/20'

    case 'SALE':
    case 'PURCHASE_RETURN':
      return 'bg-red-50 text-red-700 ring-red-600/20'

    case 'ADJUSTMENT':
    case 'STOCK_OPNAME':
      return 'bg-amber-50 text-amber-700 ring-amber-600/20'
  }
}

function quantityPrefix(
  type: StockMovementType,
): string {
  switch (type) {
    case 'PURCHASE':
    case 'SALE_RETURN':
      return '+'

    case 'SALE':
    case 'PURCHASE_RETURN':
      return '-'

    case 'ADJUSTMENT':
    case 'STOCK_OPNAME':
      return ''
  }
}

function referenceLabel(
  movement: StockMovement,
): string {
  if (
    movement.reference_type &&
    movement.reference_id
  ) {
    return `${movement.reference_type} · ${movement.reference_id}`
  }

  if (movement.reference_type) {
    return movement.reference_type
  }

  return '-'
}

async function loadProducts(): Promise<void> {
  const accessToken = getAccessToken()

  products.value = await getInventory(
    accessToken,
  )
}

async function loadMovements(
  showFilterLoading = false,
): Promise<void> {
  const accessToken = getAccessToken()

  if (showFilterLoading) {
    filterLoading.value = true
  } else {
    loading.value = true
  }

  error.value = ''

  try {
    movements.value =
      await getStockMovements(
        accessToken,
        {
          product_id:
            selectedProduct.value || undefined,

          movement_type:
            selectedMovementType.value ||
            undefined,
        },
      )
  } catch (err) {
    error.value =
      err instanceof Error
        ? err.message
        : 'Gagal mengambil riwayat pergerakan stok.'
  } finally {
    loading.value = false
    filterLoading.value = false
  }
}

function resetFilters(): void {
  selectedProduct.value = ''
  selectedMovementType.value = ''

  loadMovements()
}

function retry(): void {
  loadMovements()
}

watch(selectedProduct, () => {
  loadMovements(true)
})

watch(selectedMovementType, () => {
  loadMovements(true)
})

onMounted(async () => {
  loading.value = true

  try {
    await loadProducts()
    await loadMovements()
  } catch (err) {
    error.value =
      err instanceof Error
        ? err.message
        : 'Gagal memuat data inventory.'

    loading.value = false
  }
})
</script>

<template>
  <section class="space-y-6">
    <div>
      <p
        class="text-sm font-medium text-gray-500"
      >
        Inventory
      </p>

      <h1
        class="mt-1 text-2xl font-semibold text-gray-900"
      >
        Stock Movement
      </h1>

      <p
        class="mt-1 text-sm text-gray-500"
      >
        Riwayat seluruh perubahan stok produk.
      </p>
    </div>

    <div
      class="rounded-lg border border-gray-200 bg-white p-4"
    >
      <div
        class="grid gap-4 md:grid-cols-[minmax(0,1fr)_240px_auto]"
      >
        <div>
          <label
            for="movement-product"
            class="mb-1.5 block text-sm font-medium text-gray-700"
          >
            Produk
          </label>

          <select
            id="movement-product"
            v-model="selectedProduct"
            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700/20"
          >
            <option value="">
              Semua produk
            </option>

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
          <label
            for="movement-type"
            class="mb-1.5 block text-sm font-medium text-gray-700"
          >
            Tipe movement
          </label>

          <select
            id="movement-type"
            v-model="selectedMovementType"
            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700/20"
          >
            <option
              v-for="option in movementTypeOptions"
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
            class="w-full rounded-md border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-700/20 md:w-auto"
            @click="resetFilters"
          >
            Reset
          </button>
        </div>
      </div>

      <div
        v-if="filterLoading"
        class="mt-3 flex items-center gap-2 text-xs text-gray-500"
      >
        <span
          class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-gray-300 border-t-green-700"
          aria-hidden="true"
        />

        Memuat movement...
      </div>
    </div>

    <div
      v-if="loading"
      class="overflow-hidden rounded-lg border border-gray-200 bg-white"
      aria-live="polite"
      aria-label="Memuat stock movement"
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
        Gagal memuat stock movement
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
        Belum ada stock movement
      </h2>

      <p
        class="mx-auto mt-1 max-w-md text-sm text-gray-500"
      >
        Tidak ditemukan riwayat perubahan stok
        dengan filter yang dipilih.
      </p>

      <button
        v-if="
          selectedProduct ||
          selectedMovementType
        "
        type="button"
        class="mt-4 rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        @click="resetFilters"
      >
        Tampilkan semua movement
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
            Riwayat movement
          </p>

          <p
            class="mt-0.5 text-xs text-gray-500"
          >
            {{ movements.length }} movement
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
                Waktu
              </th>

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
                Tipe
              </th>

              <th
                scope="col"
                class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Quantity
              </th>

              <th
                scope="col"
                class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Sebelum
              </th>

              <th
                scope="col"
                class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Sesudah
              </th>

              <th
                scope="col"
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Reference
              </th>
            </tr>
          </thead>

          <tbody
            class="divide-y divide-gray-100 bg-white"
          >
            <tr
              v-for="movement in movements"
              :key="movement.id"
              class="hover:bg-gray-50"
            >
              <td
                class="whitespace-nowrap px-4 py-4 text-sm text-gray-600"
              >
                {{ formatDate(movement.created_at) }}
              </td>

              <td class="px-4 py-4">
                <div
                  class="font-medium text-gray-900"
                >
                  {{ movement.product_name }}
                </div>

                <div
                  class="mt-1 text-xs text-gray-500"
                >
                  {{ movement.sku }}
                </div>
              </td>

              <td class="px-4 py-4">
                <span
                  class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset"
                  :class="movementClass(movement.type)"
                >
                  {{ movementLabel(movement.type) }}
                </span>
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-right text-sm font-semibold text-gray-900"
              >
                {{ quantityPrefix(movement.type) }}{{ formatNumber(movement.quantity) }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-right text-sm text-gray-600"
              >
                {{ formatNumber(movement.stock_before) }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-right text-sm font-semibold text-gray-900"
              >
                {{ formatNumber(movement.stock_after) }}
              </td>

              <td
                class="max-w-xs px-4 py-4 text-sm text-gray-600"
              >
                <span class="break-all">
                  {{ referenceLabel(movement) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div
        class="divide-y divide-gray-100 md:hidden"
      >
        <article
          v-for="movement in movements"
          :key="movement.id"
          class="p-4"
        >
          <div
            class="flex items-start justify-between gap-3"
          >
            <div class="min-w-0">
              <h2
                class="font-medium text-gray-900"
              >
                {{ movement.product_name }}
              </h2>

              <p
                class="mt-1 text-xs text-gray-500"
              >
                {{ movement.sku }}
              </p>

              <p
                class="mt-1 text-xs text-gray-500"
              >
                {{ formatDate(movement.created_at) }}
              </p>
            </div>

            <span
              class="shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset"
              :class="movementClass(movement.type)"
            >
              {{ movementLabel(movement.type) }}
            </span>
          </div>

          <dl
            class="mt-4 grid grid-cols-3 gap-3"
          >
            <div>
              <dt
                class="text-xs text-gray-500"
              >
                Quantity
              </dt>

              <dd
                class="mt-1 font-semibold text-gray-900"
              >
                {{ quantityPrefix(movement.type) }}{{ formatNumber(movement.quantity) }}
              </dd>
            </div>

            <div>
              <dt
                class="text-xs text-gray-500"
              >
                Sebelum
              </dt>

              <dd
                class="mt-1 font-medium text-gray-700"
              >
                {{ formatNumber(movement.stock_before) }}
              </dd>
            </div>

            <div>
              <dt
                class="text-xs text-gray-500"
              >
                Sesudah
              </dt>

              <dd
                class="mt-1 font-semibold text-gray-900"
              >
                {{ formatNumber(movement.stock_after) }}
              </dd>
            </div>
          </dl>

          <div class="mt-4">
            <p
              class="text-xs text-gray-500"
            >
              Reference
            </p>

            <p
              class="mt-1 break-all text-sm text-gray-700"
            >
              {{ referenceLabel(movement) }}
            </p>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>