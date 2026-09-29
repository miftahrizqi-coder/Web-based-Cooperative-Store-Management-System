<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createProduct, getProduct, updateProduct } from '../../api/products'
import { useAuth } from '../../stores/auth'
import type { Product } from '../../types/product'

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const productId = route.params.id as string | undefined
const isEdit = Boolean(productId)

const sku = ref('')
const barcode = ref('')
const name = ref('')
const categoryId = ref('')
const unit = ref('pcs')
const purchasePrice = ref(0)
const sellingPrice = ref(0)
const stock = ref(0)
const minimumStock = ref(0)
const isActive = ref(true)

const isLoading = ref(isEdit)
const isSaving = ref(false)
const errorMessage = ref('')
const fieldError = ref('')

function validate() {
  fieldError.value = ''

  if (!sku.value.trim()) {
    fieldError.value = 'SKU wajib diisi.'
    return false
  }

  if (!name.value.trim()) {
    fieldError.value = 'Nama produk wajib diisi.'
    return false
  }

  if (!categoryId.value.trim()) {
    fieldError.value = 'ID kategori wajib diisi.'
    return false
  }

  if (!unit.value.trim()) {
    fieldError.value = 'Satuan wajib diisi.'
    return false
  }

  if (
    purchasePrice.value < 0 ||
    sellingPrice.value < 0 ||
    stock.value < 0 ||
    minimumStock.value < 0
  ) {
    fieldError.value = 'Harga dan stok tidak boleh negatif.'
    return false
  }

  return true
}

function fillForm(product: Product) {
  sku.value = product.sku
  barcode.value = product.barcode ?? ''
  name.value = product.name
  categoryId.value = product.category_id
  unit.value = product.unit
  purchasePrice.value = product.purchase_price
  sellingPrice.value = product.selling_price
  stock.value = product.stock
  minimumStock.value = product.minimum_stock
  isActive.value = product.is_active
}

async function loadProduct() {
  if (!isEdit || !token.value || !productId) {
    isLoading.value = false
    return
  }

  try {
    fillForm(await getProduct(token.value, productId))
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data produk.'
  } finally {
    isLoading.value = false
  }
}

async function handleSubmit() {
  errorMessage.value = ''

  if (!validate()) {
    return
  }

  if (!token.value) {
    errorMessage.value = 'Sesi login tidak ditemukan. Silakan login kembali.'
    return
  }

  isSaving.value = true

  try {
    const payload = {
      sku: sku.value.trim(),
      barcode: barcode.value.trim() || null,
      name: name.value.trim(),
      category_id: categoryId.value.trim(),
      unit: unit.value.trim(),
      purchase_price: purchasePrice.value,
      selling_price: sellingPrice.value,
      stock: stock.value,
      minimum_stock: minimumStock.value,
    }

    if (isEdit && productId) {
      await updateProduct(token.value, productId, {
        ...payload,
        is_active: isActive.value,
      })
    } else {
      await createProduct(token.value, payload)
    }

    await router.push('/products')
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal menyimpan produk.'
  } finally {
    isSaving.value = false
  }
}

onMounted(loadProduct)
</script>

<template>
  <section class="mx-auto max-w-3xl space-y-6">
    <header>
      <button
        type="button"
        class="text-sm font-medium text-green-800 hover:underline focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
        @click="router.push('/products')"
      >
        ← Kembali ke Produk
      </button>

      <h1 class="mt-3 text-2xl font-semibold text-gray-900">
        {{ isEdit ? 'Edit produk' : 'Tambah produk' }}
      </h1>
      <p class="mt-1 text-sm text-gray-600">
        Lengkapi informasi dasar, harga, stok, SKU, dan barcode.
      </p>
    </header>

    <div
      v-if="isLoading"
      class="space-y-4 rounded-xl border border-gray-200 bg-white p-6"
    >
      <div v-for="index in 8" :key="index" class="h-10 animate-pulse rounded bg-gray-100" />
    </div>

    <div
      v-else-if="errorMessage && isEdit && !sku"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
      role="alert"
    >
      <h2 class="font-semibold text-red-800">Produk gagal dimuat</h2>
      <p class="mt-1 text-sm text-red-700">{{ errorMessage }}</p>
      <button
        type="button"
        class="mt-4 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
        @click="router.push('/products')"
      >
        Kembali
      </button>
    </div>

    <form
      v-else
      class="space-y-6 rounded-xl border border-gray-200 bg-white p-6"
      @submit.prevent="handleSubmit"
    >
      <div
        v-if="errorMessage"
        role="alert"
        class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
      >
        {{ errorMessage }}
      </div>

      <div
        v-if="fieldError"
        role="alert"
        class="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800"
      >
        {{ fieldError }}
      </div>

      <div class="grid gap-5 md:grid-cols-2">
        <label class="block">
          <span class="mb-1 block text-sm font-medium text-gray-700">Nama produk</span>
          <input
            v-model="name"
            required
            type="text"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
          >
        </label>

        <label class="block">
          <span class="mb-1 block text-sm font-medium text-gray-700">SKU</span>
          <input
            v-model="sku"
            required
            type="text"
            :disabled="isEdit"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none disabled:bg-gray-100 focus:border-green-700 focus:ring-2 focus:ring-green-700"
          >
        </label>

        <label class="block">
          <span class="mb-1 block text-sm font-medium text-gray-700">Barcode</span>
          <input
            v-model="barcode"
            type="text"
            inputmode="numeric"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
          >
        </label>

        <label class="block">
          <span class="mb-1 block text-sm font-medium text-gray-700">ID kategori</span>
          <input
            v-model="categoryId"
            required
            type="text"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
          >
        </label>

        <label class="block">
          <span class="mb-1 block text-sm font-medium text-gray-700">Satuan</span>
          <input
            v-model="unit"
            required
            type="text"
            placeholder="pcs"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
          >
        </label>

        <label class="block">
          <span class="mb-1 block text-sm font-medium text-gray-700">Harga beli</span>
          <input
            v-model.number="purchasePrice"
            required
            min="0"
            type="number"
            step="1"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
          >
        </label>

        <label class="block">
          <span class="mb-1 block text-sm font-medium text-gray-700">Harga jual</span>
          <input
            v-model.number="sellingPrice"
            required
            min="0"
            type="number"
            step="1"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
          >
        </label>

        <label class="block">
          <span class="mb-1 block text-sm font-medium text-gray-700">Stok</span>
          <input
            v-model.number="stock"
            required
            min="0"
            type="number"
            step="1"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
          >
        </label>

        <label class="block">
          <span class="mb-1 block text-sm font-medium text-gray-700">Stok minimum</span>
          <input
            v-model.number="minimumStock"
            required
            min="0"
            type="number"
            step="1"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
          >
        </label>
      </div>

      <label v-if="isEdit" class="flex items-center gap-3 text-sm text-gray-700">
        <input
          v-model="isActive"
          type="checkbox"
          class="h-4 w-4 rounded border-gray-300 text-green-800 focus:ring-green-700"
        >
        Produk aktif
      </label>

      <div class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <button
          type="button"
          class="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
          @click="router.push('/products')"
        >
          Batal
        </button>

        <button
          type="submit"
          :disabled="isSaving"
          class="rounded-lg bg-green-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-900 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
        >
          {{ isSaving ? 'Menyimpan...' : 'Simpan produk' }}
        </button>
      </div>
    </form>
  </section>
</template>
