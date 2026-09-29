<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getProducts, deactivateProduct } from '../../api/products'
import { useAuth } from '../../stores/auth'
import type { Product, ProductStockStatus } from '../../types/product'

const router = useRouter()
const { token } = useAuth()

const products = ref<Product[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const actionError = ref('')
const search = ref('')
const categoryId = ref('')
const stockStatus = ref<ProductStockStatus>('all')
const deletingProductId = ref<string | null>(null)

async function loadProducts() {
  if (!token.value) {
    errorMessage.value = 'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    products.value = await getProducts(token.value, {
      search: search.value,
      categoryId: categoryId.value,
      stockStatus: stockStatus.value,
    })
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data produk.'
  } finally {
    isLoading.value = false
  }
}

async function handleDeactivate(product: Product) {
  if (!token.value || deletingProductId.value) {
    return
  }

  const confirmed = window.confirm(
    `Nonaktifkan produk "${product.name}"? Produk tidak akan dihapus permanen.`,
  )

  if (!confirmed) {
    return
  }

  deletingProductId.value = product.id
  actionError.value = ''

  try {
    await deactivateProduct(token.value, product.id)
    await loadProducts()
  } catch (error) {
    actionError.value =
      error instanceof Error
        ? error.message
        : 'Gagal menonaktifkan produk.'
  } finally {
    deletingProductId.value = null
  }
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

function stockLabel(product: Product) {
  if (product.stock === 0) return 'Habis'
  if (product.stock <= product.minimum_stock) return 'Menipis'
  return 'Tersedia'
}

function stockClass(product: Product) {
  if (product.stock === 0) return 'bg-red-50 text-red-700'
  if (product.stock <= product.minimum_stock) return 'bg-amber-50 text-amber-700'
  return 'bg-green-50 text-green-700'
}

onMounted(loadProducts)
</script>

<template>
  <section class="space-y-6">
    <header class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">Produk</h1>
        <p class="mt-1 text-sm text-gray-600">
          Kelola data produk, harga, stok, SKU, dan barcode.
        </p>
      </div>

      <button
        type="button"
        class="rounded-lg bg-green-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-900 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
        @click="router.push('/products/create')"
      >
        Tambah produk
      </button>
    </header>

    <form
      class="grid gap-3 rounded-xl border border-gray-200 bg-white p-4 md:grid-cols-[1fr_180px_180px_auto]"
      @submit.prevent="loadProducts"
    >
      <label class="block">
        <span class="mb-1 block text-sm font-medium text-gray-700">Cari</span>
        <input
          v-model="search"
          type="search"
          placeholder="Nama, SKU, atau barcode"
          class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
        >
      </label>

      <label class="block">
        <span class="mb-1 block text-sm font-medium text-gray-700">Kategori</span>
        <input
          v-model="categoryId"
          type="text"
          placeholder="ID kategori"
          class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
        >
      </label>

      <label class="block">
        <span class="mb-1 block text-sm font-medium text-gray-700">Stok</span>
        <select
          v-model="stockStatus"
          class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
        >
          <option value="all">Semua</option>
          <option value="available">Tersedia</option>
          <option value="low">Menipis</option>
          <option value="out">Habis</option>
        </select>
      </label>

      <button
        type="submit"
        class="self-end rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
      >
        Terapkan
      </button>
    </form>

    <p
      v-if="actionError"
      role="alert"
      class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
    >
      {{ actionError }}
    </p>

    <div v-if="isLoading" class="overflow-hidden rounded-xl border border-gray-200 bg-white">
      <div class="space-y-3 p-4">
        <div v-for="index in 5" :key="index" class="h-12 animate-pulse rounded bg-gray-100" />
      </div>
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
      role="alert"
    >
      <h2 class="font-semibold text-red-800">Data produk gagal dimuat</h2>
      <p class="mt-1 text-sm text-red-700">{{ errorMessage }}</p>
      <button
        type="button"
        class="mt-4 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
        @click="loadProducts"
      >
        Coba lagi
      </button>
    </div>

    <div
      v-else-if="products.length === 0"
      class="rounded-xl border border-gray-200 bg-white p-8 text-center"
    >
      <h2 class="font-semibold text-gray-900">Tidak ada produk</h2>
      <p class="mt-1 text-sm text-gray-600">
        Tidak ada produk yang cocok dengan pencarian atau filter saat ini.
      </p>
      <button
        type="button"
        class="mt-4 rounded-lg bg-green-800 px-4 py-2 text-sm font-medium text-white hover:bg-green-900 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
        @click="router.push('/products/create')"
      >
        Tambah produk
      </button>
    </div>

    <div v-else class="overflow-x-auto rounded-xl border border-gray-200 bg-white">
      <table class="min-w-full text-left text-sm">
        <thead class="border-b border-gray-200 bg-gray-50 text-gray-600">
          <tr>
            <th class="px-4 py-3 font-medium">Produk</th>
            <th class="px-4 py-3 font-medium">SKU</th>
            <th class="px-4 py-3 font-medium">Harga jual</th>
            <th class="px-4 py-3 font-medium">Stok</th>
            <th class="px-4 py-3 font-medium">Status</th>
            <th class="px-4 py-3 font-medium">Aksi</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="product in products" :key="product.id">
            <td class="px-4 py-3">
              <div class="font-medium text-gray-900">{{ product.name }}</div>
              <div class="text-xs text-gray-500">{{ product.unit }}</div>
            </td>
            <td class="px-4 py-3 text-gray-700">{{ product.sku }}</td>
            <td class="px-4 py-3 text-gray-700">{{ formatCurrency(product.selling_price) }}</td>
            <td class="px-4 py-3 text-gray-700">
              {{ product.stock }} {{ product.unit }}
              <div class="text-xs text-gray-500">Min. {{ product.minimum_stock }}</div>
            </td>
            <td class="px-4 py-3">
              <span
                class="rounded-full px-2.5 py-1 text-xs font-medium"
                :class="product.is_active ? stockClass(product) : 'bg-gray-100 text-gray-600'"
              >
                {{ product.is_active ? stockLabel(product) : 'Nonaktif' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-2">
                <button
                  type="button"
                  class="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
                  @click="router.push(`/products/${product.id}`)"
                >
                  Detail
                </button>
                <button
                  type="button"
                  class="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
                  @click="router.push(`/products/${product.id}/edit`)"
                >
                  Edit
                </button>
                <button
                  v-if="product.is_active"
                  type="button"
                  :disabled="deletingProductId === product.id"
                  class="rounded-md border border-red-300 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
                  @click="handleDeactivate(product)"
                >
                  {{ deletingProductId === product.id ? 'Memproses...' : 'Nonaktifkan' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
