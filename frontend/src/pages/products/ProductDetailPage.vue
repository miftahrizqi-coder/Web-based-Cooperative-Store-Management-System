<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProduct } from '../../api/products'
import { useAuth } from '../../stores/auth'
import type { Product } from '../../types/product'

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const product = ref<Product | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

async function loadProduct() {
  if (!token.value) {
    errorMessage.value = 'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  try {
    product.value = await getProduct(token.value, route.params.id as string)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil detail produk.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadProduct)
</script>

<template>
  <section class="mx-auto max-w-4xl space-y-6">
    <header>
      <button
        type="button"
        class="text-sm font-medium text-green-800 hover:underline focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
        @click="router.push('/products')"
      >
        ← Kembali ke Produk
      </button>
      <h1 class="mt-3 text-2xl font-semibold text-gray-900">Detail produk</h1>
    </header>

    <div
      v-if="isLoading"
      class="rounded-xl border border-gray-200 bg-white p-6"
    >
      <div class="space-y-4">
        <div v-for="index in 7" :key="index" class="h-8 animate-pulse rounded bg-gray-100" />
      </div>
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
      role="alert"
    >
      <h2 class="font-semibold text-red-800">Detail produk gagal dimuat</h2>
      <p class="mt-1 text-sm text-red-700">{{ errorMessage }}</p>
      <button
        type="button"
        class="mt-4 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
        @click="router.push('/products')"
      >
        Kembali
      </button>
    </div>

    <div v-else-if="product" class="space-y-6">
      <div class="flex flex-col gap-4 rounded-xl border border-gray-200 bg-white p-6 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <h2 class="text-xl font-semibold text-gray-900">{{ product.name }}</h2>
            <span
              class="rounded-full px-2.5 py-1 text-xs font-medium"
              :class="product.is_active ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600'"
            >
              {{ product.is_active ? 'Aktif' : 'Nonaktif' }}
            </span>
          </div>
          <p class="mt-1 text-sm text-gray-500">{{ product.sku }}</p>
        </div>

        <button
          type="button"
          class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
          @click="router.push(`/products/${product.id}/edit`)"
        >
          Edit
        </button>
      </div>

      <div class="grid gap-4 sm:grid-cols-2">
        <div class="rounded-xl border border-gray-200 bg-white p-5">
          <p class="text-sm text-gray-500">Barcode</p>
          <p class="mt-1 font-medium text-gray-900">{{ product.barcode || '—' }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-5">
          <p class="text-sm text-gray-500">Kategori</p>
          <p class="mt-1 font-medium text-gray-900">{{ product.category_id }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-5">
          <p class="text-sm text-gray-500">Satuan</p>
          <p class="mt-1 font-medium text-gray-900">{{ product.unit }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-5">
          <p class="text-sm text-gray-500">Harga beli</p>
          <p class="mt-1 font-medium text-gray-900">{{ formatCurrency(product.purchase_price) }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-5">
          <p class="text-sm text-gray-500">Harga jual</p>
          <p class="mt-1 font-medium text-gray-900">{{ formatCurrency(product.selling_price) }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-5">
          <p class="text-sm text-gray-500">Stok</p>
          <p class="mt-1 font-medium text-gray-900">
            {{ product.stock }} {{ product.unit }}
          </p>
          <p class="mt-1 text-xs text-gray-500">Minimum {{ product.minimum_stock }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
