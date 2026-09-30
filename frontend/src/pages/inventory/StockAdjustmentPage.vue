<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getInventory, createStockAdjustment } from '../../api/inventory'
import type {
  InventoryItem,
  StockAdjustmentPayload,
} from '../../types/inventory'

const router = useRouter()

const products = ref<InventoryItem[]>([])
const selectedProductId = ref('')
const quantity = ref<number | null>(null)
const reason = ref('')

const loading = ref(true)
const submitting = ref(false)
const error = ref('')
const successMessage = ref('')
const validationError = ref('')

const showConfirmation = ref(false)

const token = localStorage.getItem('access_token')

const selectedProduct = computed(() => {
  return products.value.find(
    (product) => product.product_id === selectedProductId.value,
  )
})

const stockBefore = computed(() => {
  return selectedProduct.value?.stock ?? 0
})

const stockAfter = computed(() => {
  if (quantity.value === null || Number.isNaN(quantity.value)) {
    return stockBefore.value
  }

  return stockBefore.value + quantity.value
})

const isNegativeStock = computed(() => {
  return stockAfter.value < 0
})

const canSubmit = computed(() => {
  if (!selectedProductId.value) {
    return false
  }

  if (quantity.value === null || Number.isNaN(quantity.value)) {
    return false
  }

  if (quantity.value === 0) {
    return false
  }

  if (reason.value.trim().length < 3) {
    return false
  }

  if (isNegativeStock.value) {
    return false
  }

  return !submitting.value
})

async function loadProducts() {
  loading.value = true
  error.value = ''

  try {
    if (!token) {
      throw new Error('Sesi login tidak ditemukan.')
    }

    products.value = await getInventory(token)
  } catch (err) {
    error.value =
      err instanceof Error
        ? err.message
        : 'Gagal memuat data produk.'
  } finally {
    loading.value = false
  }
}

function validateForm(): boolean {
  validationError.value = ''

  if (!selectedProductId.value) {
    validationError.value = 'Produk wajib dipilih.'
    return false
  }

  if (quantity.value === null || Number.isNaN(quantity.value)) {
    validationError.value = 'Adjustment quantity wajib diisi.'
    return false
  }

  if (quantity.value === 0) {
    validationError.value = 'Adjustment tidak boleh bernilai 0.'
    return false
  }

  if (reason.value.trim().length < 3) {
    validationError.value =
      'Alasan adjustment minimal 3 karakter.'
    return false
  }

  if (stockAfter.value < 0) {
    validationError.value =
      'Stok setelah adjustment tidak boleh negatif.'
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

function cancelConfirmation() {
  if (submitting.value) {
    return
  }

  showConfirmation.value = false
}

async function submitAdjustment() {
  if (!validateForm()) {
    showConfirmation.value = false
    return
  }

  if (!token) {
    error.value = 'Sesi login tidak ditemukan.'
    showConfirmation.value = false
    return
  }

  submitting.value = true
  error.value = ''
  successMessage.value = ''

  const payload: StockAdjustmentPayload = {
    product_id: selectedProductId.value,
    quantity: quantity.value as number,
    reason: reason.value.trim(),
  }

  try {
    const result = await createStockAdjustment(
      token,
      payload,
    )

    successMessage.value =
      `Adjustment berhasil. Stok berubah dari ` +
      `${result.stock_before} menjadi ${result.stock_after}.`

    showConfirmation.value = false

    await loadProducts()

    quantity.value = null
    reason.value = ''
  } catch (err) {
    error.value =
      err instanceof Error
        ? err.message
        : 'Gagal membuat stock adjustment.'

    showConfirmation.value = false
  } finally {
    submitting.value = false
  }
}

function goBack() {
  router.push('/inventory')
}

onMounted(loadProducts)
</script>

<template>
  <section class="space-y-6">
    <div
      class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <p class="text-sm font-medium text-slate-500">
          Inventory
        </p>

        <h1 class="text-2xl font-semibold text-slate-900">
          Stock Adjustment
        </h1>

        <p class="mt-1 text-sm text-slate-500">
          Koreksi stok secara manual dengan alasan yang
          dapat ditelusuri.
        </p>
      </div>

      <button
        type="button"
        class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
        @click="goBack"
      >
        Kembali ke Stok
      </button>
    </div>

    <div
      v-if="successMessage"
      class="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"
      role="status"
      aria-live="polite"
    >
      {{ successMessage }}
    </div>

    <div
      v-if="error"
      class="rounded-lg border border-red-200 bg-red-50 px-4 py-3"
      role="alert"
    >
      <p class="text-sm font-medium text-red-800">
        {{ error }}
      </p>

      <button
        type="button"
        class="mt-2 text-sm font-medium text-red-700 underline"
        @click="loadProducts"
      >
        Coba lagi
      </button>
    </div>

    <div
      v-if="loading"
      class="rounded-xl border border-slate-200 bg-white p-6"
      aria-label="Memuat data produk"
    >
      <div class="animate-pulse space-y-5">
        <div class="h-4 w-32 rounded bg-slate-200" />
        <div class="h-10 rounded bg-slate-200" />
        <div class="h-4 w-40 rounded bg-slate-200" />
        <div class="h-10 rounded bg-slate-200" />
        <div class="h-24 rounded bg-slate-200" />
      </div>
    </div>

    <div
      v-else-if="products.length === 0"
      class="rounded-xl border border-slate-200 bg-white p-8 text-center"
    >
      <h2 class="text-base font-semibold text-slate-900">
        Tidak ada produk
      </h2>

      <p class="mt-1 text-sm text-slate-500">
        Belum ada produk yang dapat digunakan untuk
        stock adjustment.
      </p>
    </div>

    <form
      v-else
      class="max-w-3xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      @submit.prevent="openConfirmation"
    >
      <div class="space-y-5">
        <div>
          <label
            for="product"
            class="mb-2 block text-sm font-medium text-slate-700"
          >
            Produk
          </label>

          <select
            id="product"
            v-model="selectedProductId"
            class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
          >
            <option value="">
              Pilih produk
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

        <div
          class="grid gap-4 sm:grid-cols-2"
        >
          <div
            class="rounded-lg border border-slate-200 bg-slate-50 p-4"
          >
            <p class="text-xs font-medium uppercase tracking-wide text-slate-500">
              Stok saat ini
            </p>

            <p class="mt-1 text-2xl font-semibold text-slate-900">
              {{ stockBefore }}
              <span class="text-sm font-normal text-slate-500">
                {{ selectedProduct?.unit ?? '' }}
              </span>
            </p>
          </div>

          <div
            class="rounded-lg border border-slate-200 bg-slate-50 p-4"
          >
            <p class="text-xs font-medium uppercase tracking-wide text-slate-500">
              Stok setelah adjustment
            </p>

            <p
              class="mt-1 text-2xl font-semibold"
              :class="
                isNegativeStock
                  ? 'text-red-600'
                  : 'text-slate-900'
              "
            >
              {{ stockAfter }}
              <span class="text-sm font-normal text-slate-500">
                {{ selectedProduct?.unit ?? '' }}
              </span>
            </p>
          </div>
        </div>

        <div>
          <label
            for="quantity"
            class="mb-2 block text-sm font-medium text-slate-700"
          >
            Adjustment Quantity
          </label>

          <input
            id="quantity"
            v-model.number="quantity"
            type="number"
            step="1"
            inputmode="numeric"
            placeholder="Contoh: 10 atau -5"
            class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
          />

          <p class="mt-1 text-xs text-slate-500">
            Gunakan angka positif untuk menambah stok dan
            angka negatif untuk mengurangi stok.
          </p>
        </div>

        <div>
          <label
            for="reason"
            class="mb-2 block text-sm font-medium text-slate-700"
          >
            Alasan
          </label>

          <textarea
            id="reason"
            v-model="reason"
            rows="4"
            placeholder="Jelaskan alasan adjustment..."
            class="w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
          />
        </div>

        <div
          v-if="validationError"
          class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          role="alert"
        >
          {{ validationError }}
        </div>

        <div
          v-if="isNegativeStock"
          class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          role="alert"
        >
          Stok setelah adjustment tidak boleh negatif.
        </div>

        <div
          class="flex flex-col-reverse gap-3 border-t border-slate-200 pt-5 sm:flex-row sm:justify-end"
        >
          <button
            type="button"
            class="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            @click="goBack"
          >
            Batal
          </button>

          <button
            type="submit"
            :disabled="!canSubmit"
            class="rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Simpan Adjustment
          </button>
        </div>
      </div>
    </form>

    <div
      v-if="showConfirmation"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirmation-title"
    >
      <div
        class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl"
      >
        <h2
          id="confirmation-title"
          class="text-lg font-semibold text-slate-900"
        >
          Konfirmasi Stock Adjustment
        </h2>

        <p class="mt-2 text-sm leading-6 text-slate-600">
          Stok
          <strong>{{ selectedProduct?.name }}</strong>
          akan berubah dari
          <strong>{{ stockBefore }}</strong>
          menjadi
          <strong>{{ stockAfter }}</strong>.
        </p>

        <div
          class="mt-4 rounded-lg bg-slate-50 p-3 text-sm text-slate-600"
        >
          <p>
            <span class="font-medium">Adjustment:</span>
            {{ quantity }}
          </p>

          <p class="mt-1">
            <span class="font-medium">Alasan:</span>
            {{ reason }}
          </p>
        </div>

        <div class="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            type="button"
            :disabled="submitting"
            class="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
            @click="cancelConfirmation"
          >
            Batal
          </button>

          <button
            type="button"
            :disabled="submitting"
            class="rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            @click="submitAdjustment"
          >
            {{ submitting ? 'Menyimpan...' : 'Ya, Simpan' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>