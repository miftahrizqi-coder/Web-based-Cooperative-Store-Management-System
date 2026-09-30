<script setup lang="ts">
import {
  computed,
  onMounted,
  ref,
  watch,
} from 'vue'

import {
  createStockOpname,
  getInventory,
} from '../../api/inventory'

import type {
  InventoryItem,
  StockOpnamePayload,
} from '../../types/inventory'

const accessToken = localStorage.getItem(
  'access_token',
)

const products = ref<InventoryItem[]>([])
const selectedProductId = ref('')
const physicalStock = ref<number | null>(null)
const reason = ref('')

const loading = ref(true)
const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const validationMessage = ref('')

const showConfirmation = ref(false)

const selectedProduct = computed(() =>
  products.value.find(
    (product) =>
      product.product_id === selectedProductId.value,
  ),
)

const systemStock = computed(() => {
  return selectedProduct.value?.stock ?? 0
})

const difference = computed(() => {
  if (physicalStock.value === null) {
    return 0
  }

  return physicalStock.value - systemStock.value
})

const differenceLabel = computed(() => {
  if (difference.value > 0) {
    return 'Lebih'
  }

  if (difference.value < 0) {
    return 'Kurang'
  }

  return 'Sama'
})

const canSubmit = computed(() => {
  return (
    !loading.value &&
    !submitting.value &&
    !!selectedProduct.value &&
    physicalStock.value !== null &&
    physicalStock.value >= 0 &&
    reason.value.trim().length >= 3
  )
})

async function loadProducts() {
  loading.value = true
  errorMessage.value = ''

  try {
    if (!accessToken) {
      throw new Error(
        'Sesi login tidak ditemukan.',
      )
    }

    products.value = await getInventory(
      accessToken,
    )
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data produk.'
  } finally {
    loading.value = false
  }
}

function validateForm(): boolean {
  validationMessage.value = ''

  if (!selectedProductId.value) {
    validationMessage.value =
      'Produk wajib dipilih.'

    return false
  }

  if (physicalStock.value === null) {
    validationMessage.value =
      'Stok fisik wajib diisi.'

    return false
  }

  if (
    !Number.isFinite(
      physicalStock.value,
    )
  ) {
    validationMessage.value =
      'Stok fisik harus berupa angka yang valid.'

    return false
  }

  if (physicalStock.value < 0) {
    validationMessage.value =
      'Stok fisik tidak boleh negatif.'

    return false
  }

  if (reason.value.trim().length < 3) {
    validationMessage.value =
      'Alasan minimal 3 karakter.'

    return false
  }

  return true
}

function openConfirmation() {
  successMessage.value = ''

  if (!validateForm()) {
    return
  }

  showConfirmation.value = true
}

function closeConfirmation() {
  if (submitting.value) {
    return
  }

  showConfirmation.value = false
}

async function submitStockOpname() {
  if (!validateForm()) {
    showConfirmation.value = false
    return
  }

  if (!accessToken) {
    errorMessage.value =
      'Sesi login tidak ditemukan.'
    showConfirmation.value = false
    return
  }

  const payload: StockOpnamePayload = {
    product_id: selectedProductId.value,
    physical_stock:
      physicalStock.value as number,
    reason: reason.value.trim(),
  }

  submitting.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const response =
      await createStockOpname(
        accessToken,
        payload,
      )

    successMessage.value =
      `Stock opname berhasil disimpan. ` +
      `Stok sistem ${response.system_stock} ` +
      `→ stok fisik ${response.physical_stock}. ` +
      `Selisih ${response.difference}.`

    showConfirmation.value = false

    await loadProducts()

    physicalStock.value = null
    reason.value = ''
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal menyimpan stock opname.'
  } finally {
    submitting.value = false
  }
}

function formatNumber(value: number) {
  return new Intl.NumberFormat(
    'id-ID',
  ).format(value)
}

watch(
  selectedProductId,
  () => {
    physicalStock.value = null
    validationMessage.value = ''
    successMessage.value = ''
  },
)

onMounted(() => {
  loadProducts()
})
</script>

<template>
  <section class="space-y-6">
    <div>
      <h1
        class="text-2xl font-semibold text-gray-900"
      >
        Stock Opname
      </h1>

      <p class="mt-1 text-sm text-gray-600">
        Sesuaikan stok sistem berdasarkan hasil
        pengecekan stok fisik.
      </p>
    </div>

    <!-- Loading -->
    <div
      v-if="loading"
      class="space-y-4"
    >
      <div
        class="h-10 animate-pulse rounded-lg bg-gray-200"
      />

      <div
        class="h-24 animate-pulse rounded-lg bg-gray-200"
      />

      <div
        class="h-10 animate-pulse rounded-lg bg-gray-200"
      />

      <div
        class="h-32 animate-pulse rounded-lg bg-gray-200"
      />
    </div>

    <!-- Error -->
    <div
      v-else-if="errorMessage"
      class="rounded-lg border border-red-200 bg-red-50 p-4"
    >
      <div
        class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <p
            class="font-medium text-red-800"
          >
            Gagal memuat data
          </p>

          <p
            class="mt-1 text-sm text-red-700"
          >
            {{ errorMessage }}
          </p>
        </div>

        <button
          type="button"
          class="rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          @click="loadProducts"
        >
          Coba Lagi
        </button>
      </div>
    </div>

    <!-- Empty -->
    <div
      v-else-if="products.length === 0"
      class="rounded-lg border border-gray-200 bg-white p-8 text-center"
    >
      <h2
        class="text-lg font-medium text-gray-900"
      >
        Tidak ada produk
      </h2>

      <p
        class="mt-2 text-sm text-gray-600"
      >
        Belum ada produk aktif yang dapat
        dilakukan stock opname.
      </p>
    </div>

    <!-- Form -->
    <div
      v-else
      class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6"
    >
      <form
        class="space-y-6"
        @submit.prevent="openConfirmation"
      >
        <!-- Product -->
        <div>
          <label
            for="product"
            class="mb-2 block text-sm font-medium text-gray-700"
          >
            Produk
          </label>

          <select
            id="product"
            v-model="selectedProductId"
            class="w-full rounded-lg border border-gray-300 bg-white px-3 py-3 text-base text-gray-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">
              Pilih produk
            </option>

            <option
              v-for="product in products"
              :key="product.product_id"
              :value="product.product_id"
            >
              {{ product.sku }} —
              {{ product.name }}
            </option>
          </select>
        </div>

        <!-- Product information -->
        <div
          v-if="selectedProduct"
          class="grid gap-4 sm:grid-cols-3"
        >
          <div
            class="rounded-lg bg-gray-50 p-4"
          >
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Produk
            </p>

            <p
              class="mt-1 font-medium text-gray-900"
            >
              {{ selectedProduct.name }}
            </p>

            <p
              class="mt-1 text-sm text-gray-500"
            >
              SKU: {{ selectedProduct.sku }}
            </p>
          </div>

          <div
            class="rounded-lg bg-gray-50 p-4"
          >
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Stok Sistem
            </p>

            <p
              class="mt-1 text-2xl font-semibold text-gray-900"
            >
              {{ formatNumber(systemStock) }}
              <span
                class="text-sm font-normal text-gray-500"
              >
                {{ selectedProduct.unit }}
              </span>
            </p>
          </div>

          <div
            class="rounded-lg bg-gray-50 p-4"
          >
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Selisih
            </p>

            <p
              class="mt-1 text-2xl font-semibold"
              :class="{
                'text-green-700':
                  difference > 0,
                'text-red-700':
                  difference < 0,
                'text-gray-900':
                  difference === 0,
              }"
            >
              {{ difference > 0 ? '+' : '' }}{{
                formatNumber(difference)
              }}
            </p>

            <p
              class="mt-1 text-sm text-gray-500"
            >
              {{ differenceLabel }}
            </p>
          </div>
        </div>

        <!-- Physical stock -->
        <div>
          <label
            for="physical-stock"
            class="mb-2 block text-sm font-medium text-gray-700"
          >
            Stok Fisik
          </label>

          <input
            id="physical-stock"
            v-model.number="physicalStock"
            type="number"
            min="0"
            step="any"
            inputmode="decimal"
            placeholder="Masukkan jumlah stok fisik"
            class="w-full rounded-lg border border-gray-300 px-3 py-3 text-base text-gray-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500"
          />

          <p
            class="mt-1 text-xs text-gray-500"
          >
            Masukkan jumlah barang yang benar-benar
            ditemukan saat pengecekan fisik.
          </p>
        </div>

        <!-- Difference preview -->
        <div
          v-if="selectedProduct && physicalStock !== null"
          class="rounded-lg border border-gray-200 bg-gray-50 p-4"
        >
          <div
            class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p
                class="text-sm font-medium text-gray-700"
              >
                Preview penyesuaian
              </p>

              <p
                class="mt-1 text-sm text-gray-500"
              >
                Stok sistem akan disesuaikan dengan
                hasil stok fisik.
              </p>
            </div>

            <div
              class="text-left sm:text-right"
            >
              <p
                class="text-sm text-gray-500"
              >
                {{ formatNumber(systemStock) }}
                →
                {{ formatNumber(physicalStock) }}
              </p>

              <p
                class="mt-1 font-semibold"
                :class="{
                  'text-green-700':
                    difference > 0,
                  'text-red-700':
                    difference < 0,
                  'text-gray-700':
                    difference === 0,
                }"
              >
                Selisih:
                {{ difference > 0 ? '+' : '' }}{{
                  formatNumber(difference)
                }}
              </p>
            </div>
          </div>
        </div>

        <!-- Reason -->
        <div>
          <label
            for="reason"
            class="mb-2 block text-sm font-medium text-gray-700"
          >
            Alasan Stock Opname
          </label>

          <textarea
            id="reason"
            v-model="reason"
            rows="4"
            maxlength="500"
            placeholder="Contoh: Hasil pengecekan stok fisik gudang."
            class="w-full resize-y rounded-lg border border-gray-300 px-3 py-3 text-base text-gray-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500"
          />

          <p
            class="mt-1 text-xs text-gray-500"
          >
            Minimal 3 karakter. Maksimal 500
            karakter.
          </p>
        </div>

        <!-- Validation -->
        <div
          v-if="validationMessage"
          class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {{ validationMessage }}
        </div>

        <!-- Success -->
        <div
          v-if="successMessage"
          class="rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700"
        >
          {{ successMessage }}
        </div>

        <!-- Submit -->
        <div
          class="flex flex-col-reverse gap-3 border-t border-gray-200 pt-5 sm:flex-row sm:justify-end"
        >
          <button
            type="submit"
            :disabled="!canSubmit"
            class="rounded-lg bg-indigo-600 px-5 py-3 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Simpan Stock Opname
          </button>
        </div>
      </form>
    </div>

    <!-- Confirmation Modal -->
    <div
      v-if="showConfirmation"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      @click.self="closeConfirmation"
    >
      <div
        class="w-full max-w-md rounded-xl bg-white p-5 shadow-xl sm:p-6"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirmation-title"
      >
        <h2
          id="confirmation-title"
          class="text-lg font-semibold text-gray-900"
        >
          Konfirmasi Stock Opname
        </h2>

        <div
          v-if="selectedProduct"
          class="mt-4 space-y-3 text-sm"
        >
          <div
            class="rounded-lg bg-gray-50 p-3"
          >
            <p class="text-gray-500">
              Produk
            </p>

            <p
              class="mt-1 font-medium text-gray-900"
            >
              {{ selectedProduct.name }}
            </p>
          </div>

          <div
            class="grid grid-cols-2 gap-3"
          >
            <div
              class="rounded-lg bg-gray-50 p-3"
            >
              <p class="text-gray-500">
                Stok sistem
              </p>

              <p
                class="mt-1 font-semibold text-gray-900"
              >
                {{ formatNumber(systemStock) }}
              </p>
            </div>

            <div
              class="rounded-lg bg-gray-50 p-3"
            >
              <p class="text-gray-500">
                Stok fisik
              </p>

              <p
                class="mt-1 font-semibold text-gray-900"
              >
                {{ formatNumber(physicalStock ?? 0) }}
              </p>
            </div>
          </div>

          <div
            class="rounded-lg border border-gray-200 p-3"
          >
            <p class="text-gray-500">
              Selisih
            </p>

            <p
              class="mt-1 font-semibold"
              :class="{
                'text-green-700':
                  difference > 0,
                'text-red-700':
                  difference < 0,
                'text-gray-900':
                  difference === 0,
              }"
            >
              {{ difference > 0 ? '+' : '' }}{{
                formatNumber(difference)
              }}
            </p>
          </div>

          <div
            class="rounded-lg bg-yellow-50 p-3 text-yellow-800"
          >
            Stok sistem akan disesuaikan dengan
            stok fisik setelah proses ini dikonfirmasi.
          </div>
        </div>

        <div
          class="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end"
        >
          <button
            type="button"
            :disabled="submitting"
            class="rounded-lg border border-gray-300 px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            @click="closeConfirmation"
          >
            Batal
          </button>

          <button
            type="button"
            :disabled="submitting"
            class="rounded-lg bg-indigo-600 px-4 py-3 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            @click="submitStockOpname"
          >
            {{
              submitting
                ? 'Menyimpan...'
                : 'Konfirmasi'
            }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>