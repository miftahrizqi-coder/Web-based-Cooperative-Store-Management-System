<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProducts, deactivateProduct } from '../../api/products'
import { getCategories } from '../../api/categories'
import type { Category } from '../../types/category'
import { useAuth } from '../../stores/auth'
import type { Product, ProductStockStatus } from '../../types/product'

const router = useRouter()
const route = useRoute()
const { token } = useAuth()

const products = ref<Product[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const actionError = ref('')
const search = ref('')
const categoryId = ref('')
const categories = ref<Category[]>([])
const stockStatus = ref<ProductStockStatus>('all')
const deletingProductId = ref<string | null>(null)

const currentPage = ref(1)
const pageSize = 10

const filteredProducts = computed(() => products.value)

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredProducts.value.length / pageSize)),
)

const paginatedProducts = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredProducts.value.slice(start, start + pageSize)
})

const pageStart = computed(() => {
  if (filteredProducts.value.length === 0) return 0
  return (currentPage.value - 1) * pageSize + 1
})

const pageEnd = computed(() =>
  Math.min(currentPage.value * pageSize, filteredProducts.value.length),
)

const paginationPages = computed(() => {
  const pages: number[] = []
  const start = Math.max(1, currentPage.value - 2)
  const end = Math.min(totalPages.value, start + 4)

  for (let page = start; page <= end; page += 1) {
    pages.push(page)
  }

  return pages
})

const hasActiveFilters = computed(
  () =>
    Boolean(search.value.trim()) ||
    Boolean(categoryId.value.trim()) ||
    stockStatus.value !== 'all',
)

function resetPagination() {
  currentPage.value = 1
}

async function loadProducts() {
  if (!token.value) {
    errorMessage.value = 'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  actionError.value = ''

  try {
    products.value = await getProducts(token.value, {
      search: search.value.trim(),
      categoryId: categoryId.value.trim(),
      stockStatus: stockStatus.value,
    })

    resetPagination()
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data produk.'
  } finally {
    isLoading.value = false
  }
}

function clearFilters() {
  search.value = ''
  categoryId.value = ''
  stockStatus.value = 'all'
  resetPagination()
  loadProducts()
}

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
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
  }).format(Number(value) || 0)
}

function stockLabel(product: Product) {
  if (product.stock <= 0) return 'Habis'
  if (product.stock <= product.minimumStock) return 'Menipis'
  return 'Tersedia'
}

function stockBadgeClass(product: Product) {
  if (product.stock <= 0) {
    return 'border-[#E8B9B3] bg-[#FDF0EE] text-[#C0392B]'
  }

  if (product.stock <= product.minimumStock) {
    return 'border-[#E8D2A7] bg-[#FFF7E8] text-[#9A650F]'
  }

  return 'border-[#B9DEC9] bg-[#F0F8F5] text-[#16834B]'
}

function activeBadgeClass(product: Product) {
  return product.isActive
    ? 'border-[#B9DEC9] bg-[#F0F8F5] text-[#16834B]'
    : 'border-[#D6DDD9] bg-[#F1F4F2] text-[#6B756F]'
}

onMounted(async () => {
  if (typeof route.query.categoryId === 'string') {
    categoryId.value = route.query.categoryId
  }
  try {
    categories.value = await getCategories()
  } catch {
    categories.value = []
  }
  await loadProducts()
})
</script>

<template>
  <main
    class="min-h-full min-w-0 bg-[#F8FAF9] px-4 py-6 font-[Inter,ui-sans-serif,system-ui,sans-serif] text-[#17201C] md:px-6 md:py-7 lg:px-8 lg:py-8"
  >
    <div class="mx-auto w-full max-w-[1440px]">
      <!-- Page header -->
      <header class="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div class="min-w-0">
          <nav aria-label="Breadcrumb" class="mb-3">
            <ol class="flex flex-wrap items-center gap-2 text-[13px] leading-[18px] text-[#6B756F]">
              <li>
                <a
                  href="/dashboard"
                  class="rounded-sm hover:text-[#176B4D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                  @click.prevent="router.push('/dashboard')"
                >
                  Master Data
                </a>
              </li>
              <li aria-hidden="true">/</li>
              <li class="font-medium text-[#46514B]" aria-current="page">Produk</li>
            </ol>
          </nav>

          <h1 class="text-[28px] font-semibold leading-9 tracking-[-0.02em] text-[#17201C]">
            Produk
          </h1>
          <p class="mt-1.5 max-w-2xl text-[14px] leading-5 text-[#6B756F]">
            Kelola data produk, harga, stok, SKU, dan barcode.
          </p>
        </div>

        <button
          type="button"
          class="inline-flex min-h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 py-2 text-[14px] font-semibold leading-5 text-white shadow-sm transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
          @click="router.push('/products/create')"
        >
          <span aria-hidden="true" class="mr-2 text-base leading-none">+</span>
          Tambah produk
        </button>
      </header>

      <!-- Filter bar -->
      <form
        class="mb-5 rounded-lg border border-[#D6DDD9] bg-white p-4 shadow-[0_1px_2px_rgba(18,55,42,.06)]"
        @submit.prevent="loadProducts"
      >
        <div class="mb-3 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-[14px] font-semibold leading-5 text-[#17201C]">Filter produk</h2>
            <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">
              Gunakan filter yang paling relevan untuk menemukan produk.
            </p>
          </div>

          <button
            v-if="hasActiveFilters"
            type="button"
            class="shrink-0 rounded-md px-2 py-1 text-[13px] font-medium text-[#176B4D] hover:bg-[#F0F8F5] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="clearFilters"
          >
            Reset
          </button>
        </div>

        <div class="grid gap-3 lg:grid-cols-[minmax(0,1fr)_200px_200px_auto] lg:items-end">
          <label class="block min-w-0">
            <span class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#46514B]">
              Cari produk
            </span>
            <input
              v-model="search"
              type="search"
              placeholder="Nama, SKU, atau barcode"
              autocomplete="off"
              class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-[14px] leading-5 text-[#17201C] outline-none transition placeholder:text-[#8A948E] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            >
          </label>

          <label class="block">
            <span class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#46514B]">
              Kategori
            </span>
            <select
              v-model="categoryId"
              class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-[14px] leading-5 text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            >
              <option value="">Semua kategori</option>
              <option v-for="category in categories" :key="category.id" :value="category.id">
                {{ category.name }}{{ category.isActive ? '' : ' (nonaktif)' }}
              </option>
            </select>
          </label>

          <label class="block">
            <span class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#46514B]">
              Status stok
            </span>
            <select
              v-model="stockStatus"
              class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-[14px] leading-5 text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            >
              <option value="all">Semua</option>
              <option value="available">Tersedia</option>
              <option value="low">Menipis</option>
              <option value="out">Habis</option>
            </select>
          </label>

          <button
            type="submit"
            class="h-10 rounded-lg border border-[#D6DDD9] bg-white px-4 text-[14px] font-semibold leading-5 text-[#46514B] transition hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
          >
            Terapkan
          </button>
        </div>
      </form>

      <!-- Action error -->
      <div
        v-if="actionError"
        class="mb-5 flex items-start gap-3 rounded-lg border border-[#E8B9B3] bg-[#FDF0EE] p-4"
        role="alert"
      >
        <div class="min-w-0">
          <p class="text-[14px] font-semibold leading-5 text-[#C0392B]">
            Aksi tidak berhasil
          </p>
          <p class="mt-0.5 text-[13px] leading-[18px] text-[#9D3328]">
            {{ actionError }}
          </p>
        </div>
      </div>

      <!-- Loading -->
      <section
        v-if="isLoading"
        aria-label="Memuat produk"
        class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white shadow-[0_1px_2px_rgba(18,55,42,.06)]"
      >
        <div class="hidden md:block">
          <div class="border-b border-[#E6EBE8] bg-[#F1F4F2] px-5 py-3">
            <div class="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1.7fr] gap-4">
              <div v-for="index in 6" :key="index" class="h-3 animate-pulse rounded bg-[#D6DDD9]" />
            </div>
          </div>
          <div class="divide-y divide-[#E6EBE8]">
            <div v-for="row in 6" :key="row" class="px-5 py-4">
              <div class="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1.7fr] items-center gap-4">
                <div class="space-y-2">
                  <div class="h-4 w-40 animate-pulse rounded bg-[#F1F4F2]" />
                  <div class="h-3 w-20 animate-pulse rounded bg-[#F1F4F2]" />
                </div>
                <div class="h-4 w-20 animate-pulse rounded bg-[#F1F4F2]" />
                <div class="h-4 w-28 animate-pulse rounded bg-[#F1F4F2]" />
                <div class="h-4 w-24 animate-pulse rounded bg-[#F1F4F2]" />
                <div class="h-6 w-20 animate-pulse rounded-full bg-[#F1F4F2]" />
                <div class="h-8 w-36 animate-pulse rounded bg-[#F1F4F2]" />
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-3 p-4 md:hidden">
          <div v-for="row in 5" :key="row" class="rounded-lg border border-[#E6EBE8] p-4">
            <div class="h-4 w-40 animate-pulse rounded bg-[#F1F4F2]" />
            <div class="mt-2 h-3 w-24 animate-pulse rounded bg-[#F1F4F2]" />
            <div class="mt-4 grid grid-cols-2 gap-3">
              <div class="h-4 animate-pulse rounded bg-[#F1F4F2]" />
              <div class="h-4 animate-pulse rounded bg-[#F1F4F2]" />
            </div>
          </div>
        </div>
      </section>

      <!-- Error -->
      <section
        v-else-if="errorMessage"
        class="rounded-lg border border-[#E8B9B3] bg-white p-6 shadow-[0_1px_2px_rgba(18,55,42,.06)]"
        role="alert"
      >
        <div class="max-w-xl">
          <p class="text-[14px] font-semibold leading-5 text-[#C0392B]">
            Data produk gagal dimuat
          </p>
          <p class="mt-1 text-[14px] leading-5 text-[#46514B]">
            {{ errorMessage }}
          </p>
          <button
            type="button"
            class="mt-4 rounded-lg bg-[#176B4D] px-4 py-2 text-[14px] font-semibold leading-5 text-white hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="loadProducts"
          >
            Coba lagi
          </button>
        </div>
      </section>

      <!-- Empty -->
      <section
        v-else-if="products.length === 0"
        class="rounded-lg border border-[#D6DDD9] bg-white p-8 text-center shadow-[0_1px_2px_rgba(18,55,42,.06)]"
      >
        <div class="mx-auto max-w-md">
          <div
            class="mx-auto flex h-11 w-11 items-center justify-center rounded-lg bg-[#F0F8F5] text-[#176B4D]"
            aria-hidden="true"
          >
            —
          </div>
          <h2 class="mt-4 text-[18px] font-semibold leading-[26px] text-[#17201C]">
            Belum ada produk yang ditampilkan
          </h2>
          <p class="mt-1.5 text-[14px] leading-5 text-[#6B756F]">
            {{
              hasActiveFilters
                ? 'Tidak ada produk yang cocok dengan pencarian atau filter saat ini.'
                : 'Belum ada data produk. Tambahkan produk pertama untuk mulai mengelola katalog.'
            }}
          </p>

          <div class="mt-5 flex flex-col justify-center gap-2 sm:flex-row">
            <button
              v-if="hasActiveFilters"
              type="button"
              class="rounded-lg border border-[#D6DDD9] bg-white px-4 py-2 text-[14px] font-semibold leading-5 text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
              @click="clearFilters"
            >
              Reset filter
            </button>
            <button
              type="button"
              class="rounded-lg bg-[#176B4D] px-4 py-2 text-[14px] font-semibold leading-5 text-white hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
              @click="router.push('/products/create')"
            >
              Tambah produk
            </button>
          </div>
        </div>
      </section>

      <!-- Data table -->
      <section
        v-else
        class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white shadow-[0_1px_2px_rgba(18,55,42,.06)]"
        aria-label="Daftar produk"
      >
        <!-- Table toolbar -->
        <div class="flex flex-col gap-2 border-b border-[#E6EBE8] px-4 py-3 sm:flex-row sm:items-center sm:justify-between md:px-5">
          <div>
            <p class="text-[14px] font-semibold leading-5 text-[#17201C]">
              Daftar produk
            </p>
            <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">
              {{ filteredProducts.length }} produk ditemukan
            </p>
          </div>

          <div class="text-[13px] leading-[18px] text-[#6B756F]">
            Menampilkan
            <span class="font-medium text-[#46514B]">{{ pageStart }}–{{ pageEnd }}</span>
            dari
            <span class="font-medium text-[#46514B]">{{ filteredProducts.length }}</span>
          </div>
        </div>

        <!-- Desktop / tablet table -->
        <div class="hidden overflow-x-auto md:block">
          <table class="min-w-[900px] w-full border-collapse text-left">
            <caption class="sr-only">Daftar produk dan status stok</caption>
            <thead class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2]">
              <tr class="text-[12px] font-semibold uppercase tracking-[0.04em] text-[#6B756F]">
                <th scope="col" class="px-5 py-3">Produk</th>
                <th scope="col" class="px-5 py-3">SKU</th>
                <th scope="col" class="px-5 py-3 text-right">Harga jual</th>
                <th scope="col" class="px-5 py-3 text-right">Stok</th>
                <th scope="col" class="px-5 py-3">Status</th>
                <th scope="col" class="px-5 py-3 text-right">Aksi</th>
              </tr>
            </thead>

            <tbody class="divide-y divide-[#E6EBE8]">
              <tr
                v-for="product in paginatedProducts"
                :key="product.id"
                class="transition hover:bg-[#FAFCFB]"
              >
                <td class="px-5 py-4 align-middle">
                  <div class="min-w-[180px]">
                    <button
                      type="button"
                      class="text-left text-[14px] font-semibold leading-5 text-[#17201C] hover:text-[#176B4D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                      @click="router.push(`/products/${product.id}`)"
                    >
                      {{ product.name }}
                    </button>
                    <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">
                      {{ product.categoryName || 'Tanpa kategori' }} · Satuan: {{ product.unit }}
                    </p>
                  </div>
                </td>

                <td class="px-5 py-4 align-middle">
                  <span class="font-mono text-[13px] leading-[18px] text-[#46514B]">
                    {{ product.sku }}
                  </span>
                </td>

                <td class="px-5 py-4 text-right align-middle">
                  <span class="whitespace-nowrap text-[14px] font-medium leading-5 text-[#17201C]">
                    {{ formatCurrency(product.sellingPrice) }}
                  </span>
                </td>

                <td class="px-5 py-4 text-right align-middle">
                  <span class="block whitespace-nowrap text-[14px] font-medium leading-5 text-[#17201C]">
                    {{ product.stock }} {{ product.unit }}
                  </span>
                  <span class="mt-0.5 block text-[12px] leading-4 text-[#6B756F]">
                    Min. {{ product.minimumStock }}
                  </span>
                </td>

                <td class="px-5 py-4 align-middle">
                  <div class="flex flex-wrap gap-1.5">
                    <span
                      class="inline-flex rounded-full border px-2.5 py-1 text-[12px] font-medium leading-4"
                      :class="activeBadgeClass(product)"
                    >
                      {{ product.isActive ? 'Aktif' : 'Nonaktif' }}
                    </span>
                    <span
                      v-if="product.isActive"
                      class="inline-flex rounded-full border px-2.5 py-1 text-[12px] font-medium leading-4"
                      :class="stockBadgeClass(product)"
                    >
                      {{ stockLabel(product) }}
                    </span>
                  </div>
                </td>

                <td class="px-5 py-4 align-middle">
                  <div class="flex justify-end gap-2">
                    <button
                      type="button"
                      class="rounded-md border border-[#D6DDD9] bg-white px-3 py-1.5 text-[13px] font-medium leading-[18px] text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                      @click="router.push(`/products/${product.id}`)"
                    >
                      Detail
                    </button>
                    <button
                      type="button"
                      class="rounded-md border border-[#D6DDD9] bg-white px-3 py-1.5 text-[13px] font-medium leading-[18px] text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                      @click="router.push(`/products/${product.id}/edit`)"
                    >
                      Edit
                    </button>
                    <button
                      v-if="product.isActive"
                      type="button"
                      :disabled="deletingProductId === product.id"
                      class="rounded-md border border-[#E8B9B3] bg-white px-3 py-1.5 text-[13px] font-medium leading-[18px] text-[#C0392B] hover:bg-[#FDF0EE] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-2"
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

        <!-- Mobile responsive rows -->
        <div class="divide-y divide-[#E6EBE8] md:hidden">
          <article
            v-for="product in paginatedProducts"
            :key="product.id"
            class="p-4"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <button
                  type="button"
                  class="text-left text-[14px] font-semibold leading-5 text-[#17201C] hover:text-[#176B4D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                  @click="router.push(`/products/${product.id}`)"
                >
                  {{ product.name }}
                </button>
                <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">
                  {{ product.unit }} · SKU {{ product.sku }}
                </p>
              </div>

              <div class="flex shrink-0 flex-wrap justify-end gap-1">
                <span
                  class="inline-flex rounded-full border px-2 py-1 text-[11px] font-medium leading-4"
                  :class="activeBadgeClass(product)"
                >
                  {{ product.isActive ? 'Aktif' : 'Nonaktif' }}
                </span>
                <span
                  v-if="product.isActive"
                  class="inline-flex rounded-full border px-2 py-1 text-[11px] font-medium leading-4"
                  :class="stockBadgeClass(product)"
                >
                  {{ stockLabel(product) }}
                </span>
              </div>
            </div>

            <dl class="mt-4 grid grid-cols-2 gap-x-4 gap-y-3">
              <div>
                <dt class="text-[12px] leading-4 text-[#6B756F]">Harga jual</dt>
                <dd class="mt-0.5 text-[14px] font-medium leading-5 text-[#17201C]">
                  {{ formatCurrency(product.sellingPrice) }}
                </dd>
              </div>
              <div class="text-right">
                <dt class="text-[12px] leading-4 text-[#6B756F]">Stok</dt>
                <dd class="mt-0.5 text-[14px] font-medium leading-5 text-[#17201C]">
                  {{ product.stock }} {{ product.unit }}
                </dd>
              </div>
              <div>
                <dt class="text-[12px] leading-4 text-[#6B756F]">Minimum stok</dt>
                <dd class="mt-0.5 text-[13px] leading-[18px] text-[#46514B]">
                  {{ product.minimumStock }} {{ product.unit }}
                </dd>
              </div>
            </dl>

            <div class="mt-4 flex flex-wrap gap-2 border-t border-[#E6EBE8] pt-3">
              <button
                type="button"
                class="rounded-md border border-[#D6DDD9] bg-white px-3 py-1.5 text-[13px] font-medium leading-[18px] text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                @click="router.push(`/products/${product.id}`)"
              >
                Detail
              </button>
              <button
                type="button"
                class="rounded-md border border-[#D6DDD9] bg-white px-3 py-1.5 text-[13px] font-medium leading-[18px] text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                @click="router.push(`/products/${product.id}/edit`)"
              >
                Edit
              </button>
              <button
                v-if="product.isActive"
                type="button"
                :disabled="deletingProductId === product.id"
                class="rounded-md border border-[#E8B9B3] bg-white px-3 py-1.5 text-[13px] font-medium leading-[18px] text-[#C0392B] hover:bg-[#FDF0EE] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-2"
                @click="handleDeactivate(product)"
              >
                {{ deletingProductId === product.id ? 'Memproses...' : 'Nonaktifkan' }}
              </button>
            </div>
          </article>
        </div>

        <!-- Pagination -->
        <footer
          v-if="totalPages > 1"
          class="flex flex-col gap-3 border-t border-[#E6EBE8] px-4 py-3 sm:flex-row sm:items-center sm:justify-between md:px-5"
        >
          <p class="text-[13px] leading-[18px] text-[#6B756F]">
            Halaman {{ currentPage }} dari {{ totalPages }}
          </p>

          <nav aria-label="Pagination produk" class="flex items-center gap-1">
            <button
              type="button"
              :disabled="currentPage === 1"
              class="rounded-md border border-[#D6DDD9] bg-white px-3 py-1.5 text-[13px] font-medium leading-[18px] text-[#46514B] hover:bg-[#F1F4F2] disabled:cursor-not-allowed disabled:opacity-40 focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
              @click="goToPage(currentPage - 1)"
            >
              Sebelumnya
            </button>

            <button
              v-for="page in paginationPages"
              :key="page"
              type="button"
              :aria-current="page === currentPage ? 'page' : undefined"
              :class="
                page === currentPage
                  ? 'border-[#176B4D] bg-[#176B4D] text-white'
                  : 'border-[#D6DDD9] bg-white text-[#46514B] hover:bg-[#F1F4F2]'
              "
              class="min-w-9 rounded-md border px-2.5 py-1.5 text-[13px] font-medium leading-[18px] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
              @click="goToPage(page)"
            >
              {{ page }}
            </button>

            <button
              type="button"
              :disabled="currentPage === totalPages"
              class="rounded-md border border-[#D6DDD9] bg-white px-3 py-1.5 text-[13px] font-medium leading-[18px] text-[#46514B] hover:bg-[#F1F4F2] disabled:cursor-not-allowed disabled:opacity-40 focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
              @click="goToPage(currentPage + 1)"
            >
              Berikutnya
            </button>
          </nav>
        </footer>
      </section>
    </div>
  </main>
</template>
