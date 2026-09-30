<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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

const productStatus = computed(() => {
  if (!product.value) return null

  return product.value.is_active
    ? {
        label: 'Aktif',
        class: 'border-[#B9DEC9] bg-[#F0F8F5] text-[#16834B]',
      }
    : {
        label: 'Nonaktif',
        class: 'border-[#D6DDD9] bg-[#F1F4F2] text-[#46514B]',
      }
})

const stockStatus = computed(() => {
  if (!product.value) return null

  const stock = Number(product.value.stock)
  const minimum = Number(product.value.minimum_stock)

  if (stock <= 0) {
    return {
      label: 'Stok habis',
      class: 'border-[#E7B8B2] bg-[#FEF3F2] text-[#C0392B]',
    }
  }

  if (stock <= minimum) {
    return {
      label: 'Stok rendah',
      class: 'border-[#E6C98F] bg-[#FFF8E8] text-[#B7791F]',
    }
  }

  return {
    label: 'Stok tersedia',
    class: 'border-[#B9DEC9] bg-[#F0F8F5] text-[#16834B]',
  }
})

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

function goBack() {
  router.push('/products')
}

function goToEdit() {
  if (!product.value) return
  router.push(`/products/${product.value.id}/edit`)
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
  <main class="min-w-0 bg-[#F8FAF9] font-[Inter,ui-sans-serif,system-ui,sans-serif] text-[#17201C]">
    <div class="mx-auto w-full max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8">
      <!-- Loading -->
      <section v-if="isLoading" aria-label="Memuat detail produk">
        <div class="mb-6 space-y-2">
          <div class="h-4 w-32 animate-pulse rounded bg-[#E6EBE8]" />
          <div class="h-9 w-64 animate-pulse rounded bg-[#E6EBE8]" />
        </div>

        <div class="space-y-6">
          <div class="rounded-lg border border-[#D6DDD9] bg-white p-6">
            <div class="space-y-4">
              <div class="h-5 w-48 animate-pulse rounded bg-[#E6EBE8]" />
              <div class="h-4 w-72 animate-pulse rounded bg-[#E6EBE8]" />
              <div class="grid gap-4 sm:grid-cols-3">
                <div
                  v-for="index in 3"
                  :key="index"
                  class="h-20 animate-pulse rounded-md bg-[#F1F4F2]"
                />
              </div>
            </div>
          </div>

          <div class="rounded-lg border border-[#D6DDD9] bg-white p-6">
            <div class="space-y-4">
              <div class="h-5 w-36 animate-pulse rounded bg-[#E6EBE8]" />
              <div
                v-for="index in 4"
                :key="index"
                class="h-10 animate-pulse rounded bg-[#F1F4F2]"
              />
            </div>
          </div>
        </div>
      </section>

      <!-- Error -->
      <section
        v-else-if="errorMessage"
        class="rounded-lg border border-[#E7B8B2] bg-white p-6"
        role="alert"
        aria-labelledby="product-detail-error-title"
      >
        <div class="flex items-start gap-3">
          <div class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#FEF3F2] text-[#C0392B]">
            !
          </div>

          <div class="min-w-0">
            <h1
              id="product-detail-error-title"
              class="text-[18px] font-semibold leading-[26px] text-[#17201C]"
            >
              Detail produk gagal dimuat
            </h1>
            <p class="mt-1 text-[14px] leading-5 text-[#46514B]">
              {{ errorMessage }}
            </p>

            <button
              type="button"
              class="mt-5 inline-flex min-h-10 items-center justify-center rounded-md border border-[#D6DDD9] bg-white px-4 text-[14px] font-medium text-[#46514B] transition hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
              @click="goBack"
            >
              Kembali ke Produk
            </button>
          </div>
        </div>
      </section>

      <!-- Detail -->
      <section v-else-if="product" aria-labelledby="product-detail-title">
        <!-- Breadcrumb -->
        <nav
          class="mb-4"
          aria-label="Breadcrumb"
        >
          <ol class="flex flex-wrap items-center gap-2 text-[13px] leading-[18px] text-[#6B756F]">
            <li>
              <button
                type="button"
                class="rounded-sm font-medium text-[#176B4D] hover:text-[#1F805D] hover:underline focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                @click="goBack"
              >
                Produk
              </button>
            </li>
            <li aria-hidden="true">/</li>
            <li class="truncate" aria-current="page">
              {{ product.name }}
            </li>
          </ol>
        </nav>

        <!-- Page header -->
        <header class="border-b border-[#E6EBE8] pb-6">
          <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <h1
                  id="product-detail-title"
                  class="text-[28px] font-semibold leading-9 tracking-[-0.01em] text-[#17201C]"
                >
                  {{ product.name }}
                </h1>

                <span
                  v-if="productStatus"
                  class="inline-flex items-center rounded-full border px-2.5 py-1 text-[12px] font-medium leading-4"
                  :class="productStatus.class"
                >
                  {{ productStatus.label }}
                </span>
              </div>

              <p class="mt-2 text-[14px] leading-5 text-[#6B756F]">
                SKU {{ product.sku }}
              </p>
            </div>

            <div class="flex shrink-0 flex-wrap gap-2">
              <button
                type="button"
                class="inline-flex min-h-10 items-center justify-center rounded-md border border-[#D6DDD9] bg-white px-4 text-[14px] font-medium text-[#46514B] transition hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                @click="goBack"
              >
                Kembali
              </button>

              <button
                type="button"
                class="inline-flex min-h-10 items-center justify-center rounded-md bg-[#176B4D] px-4 text-[14px] font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                @click="goToEdit"
              >
                Edit Produk
              </button>
            </div>
          </div>
        </header>

        <!-- Summary / Key Metrics -->
        <section
          class="mt-6"
          aria-labelledby="product-summary-title"
        >
          <div class="mb-3">
            <h2
              id="product-summary-title"
              class="text-[18px] font-semibold leading-[26px] text-[#17201C]"
            >
              Ringkasan
            </h2>
            <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
              Informasi utama produk dan kondisi stok saat ini.
            </p>
          </div>

          <div class="grid gap-4 md:grid-cols-3">
            <article class="rounded-lg border border-[#D6DDD9] bg-white p-5">
              <p class="text-[13px] leading-[18px] text-[#6B756F]">Harga jual</p>
              <p class="mt-2 text-[24px] font-semibold leading-8 text-[#17201C]">
                {{ formatCurrency(product.selling_price) }}
              </p>
              <p class="mt-1 text-[12px] leading-4 text-[#6B756F]">
                Harga yang digunakan pada penjualan.
              </p>
            </article>

            <article class="rounded-lg border border-[#D6DDD9] bg-white p-5">
              <p class="text-[13px] leading-[18px] text-[#6B756F]">Stok saat ini</p>
              <div class="mt-2 flex flex-wrap items-baseline gap-2">
                <p class="text-[24px] font-semibold leading-8 text-[#17201C]">
                  {{ product.stock }}
                </p>
                <span class="text-[14px] leading-5 text-[#46514B]">
                  {{ product.unit }}
                </span>
              </div>
              <span
                v-if="stockStatus"
                class="mt-2 inline-flex items-center rounded-full border px-2.5 py-1 text-[12px] font-medium leading-4"
                :class="stockStatus.class"
              >
                {{ stockStatus.label }}
              </span>
            </article>

            <article class="rounded-lg border border-[#D6DDD9] bg-white p-5">
              <p class="text-[13px] leading-[18px] text-[#6B756F]">Minimum stok</p>
              <p class="mt-2 text-[24px] font-semibold leading-8 text-[#17201C]">
                {{ product.minimum_stock }}
              </p>
              <p class="mt-1 text-[12px] leading-4 text-[#6B756F]">
                Batas minimum sebelum stok perlu diperhatikan.
              </p>
            </article>
          </div>
        </section>

        <!-- Overview -->
        <section
          class="mt-8 rounded-lg border border-[#D6DDD9] bg-white"
          aria-labelledby="overview-title"
        >
          <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
            <h2
              id="overview-title"
              class="text-[18px] font-semibold leading-[26px] text-[#17201C]"
            >
              Overview
            </h2>
          </div>

          <dl class="divide-y divide-[#E6EBE8]">
            <div class="grid gap-1 px-5 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6 sm:px-6">
              <dt class="text-[13px] leading-[18px] text-[#6B756F]">Nama produk</dt>
              <dd class="text-[14px] font-medium leading-5 text-[#17201C]">
                {{ product.name }}
              </dd>
            </div>

            <div class="grid gap-1 px-5 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6 sm:px-6">
              <dt class="text-[13px] leading-[18px] text-[#6B756F]">SKU</dt>
              <dd class="break-all font-mono text-[14px] font-medium leading-5 text-[#17201C]">
                {{ product.sku }}
              </dd>
            </div>

            <div class="grid gap-1 px-5 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6 sm:px-6">
              <dt class="text-[13px] leading-[18px] text-[#6B756F]">Barcode</dt>
              <dd class="break-all font-mono text-[14px] font-medium leading-5 text-[#17201C]">
                {{ product.barcode || '—' }}
              </dd>
            </div>

            <div class="grid gap-1 px-5 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6 sm:px-6">
              <dt class="text-[13px] leading-[18px] text-[#6B756F]">Kategori</dt>
              <dd class="text-[14px] font-medium leading-5 text-[#17201C]">
                {{ product.category_id }}
              </dd>
            </div>

            <div class="grid gap-1 px-5 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6 sm:px-6">
              <dt class="text-[13px] leading-[18px] text-[#6B756F]">Satuan</dt>
              <dd class="text-[14px] font-medium leading-5 text-[#17201C]">
                {{ product.unit }}
              </dd>
            </div>
          </dl>
        </section>

        <!-- Financial -->
        <section
          class="mt-6 rounded-lg border border-[#D6DDD9] bg-white"
          aria-labelledby="financial-title"
        >
          <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
            <h2
              id="financial-title"
              class="text-[18px] font-semibold leading-[26px] text-[#17201C]"
            >
              Financial
            </h2>
            <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
              Informasi harga produk yang tersimpan pada sistem.
            </p>
          </div>

          <dl class="divide-y divide-[#E6EBE8]">
            <div class="grid gap-1 px-5 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6 sm:px-6">
              <dt class="text-[13px] leading-[18px] text-[#6B756F]">Harga beli</dt>
              <dd class="text-right text-[14px] font-semibold leading-5 text-[#17201C] sm:text-left">
                {{ formatCurrency(product.purchase_price) }}
              </dd>
            </div>

            <div class="grid gap-1 px-5 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6 sm:px-6">
              <dt class="text-[13px] leading-[18px] text-[#6B756F]">Harga jual</dt>
              <dd class="text-right text-[14px] font-semibold leading-5 text-[#17201C] sm:text-left">
                {{ formatCurrency(product.selling_price) }}
              </dd>
            </div>
          </dl>
        </section>

        <!-- Inventory -->
        <section
          class="mt-6 rounded-lg border border-[#D6DDD9] bg-white"
          aria-labelledby="inventory-title"
        >
          <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
            <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2
                  id="inventory-title"
                  class="text-[18px] font-semibold leading-[26px] text-[#17201C]"
                >
                  Inventory
                </h2>
                <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                  Kondisi stok dan batas minimum produk.
                </p>
              </div>

              <span
                v-if="stockStatus"
                class="inline-flex w-fit items-center rounded-full border px-2.5 py-1 text-[12px] font-medium leading-4"
                :class="stockStatus.class"
              >
                {{ stockStatus.label }}
              </span>
            </div>
          </div>

          <dl class="grid divide-y divide-[#E6EBE8] sm:grid-cols-3 sm:divide-x sm:divide-y-0">
            <div class="px-5 py-4 sm:px-6">
              <dt class="text-[13px] leading-[18px] text-[#6B756F]">Stok tersedia</dt>
              <dd class="mt-1 text-[16px] font-semibold leading-6 text-[#17201C]">
                {{ product.stock }} {{ product.unit }}
              </dd>
            </div>

            <div class="px-5 py-4 sm:px-6">
              <dt class="text-[13px] leading-[18px] text-[#6B756F]">Minimum stok</dt>
              <dd class="mt-1 text-[16px] font-semibold leading-6 text-[#17201C]">
                {{ product.minimum_stock }} {{ product.unit }}
              </dd>
            </div>

            <div class="px-5 py-4 sm:px-6">
              <dt class="text-[13px] leading-[18px] text-[#6B756F]">Status produk</dt>
              <dd class="mt-1 text-[16px] font-semibold leading-6 text-[#17201C]">
                {{ product.is_active ? 'Dapat digunakan' : 'Tidak digunakan' }}
              </dd>
            </div>
          </dl>
        </section>

        <!-- History / Audit placeholder: no API data is currently available in the original file -->
        <section
          class="mt-6 rounded-lg border border-[#D6DDD9] bg-white"
          aria-labelledby="history-title"
        >
          <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
            <h2
              id="history-title"
              class="text-[18px] font-semibold leading-[26px] text-[#17201C]"
            >
              History
            </h2>
            <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
              Riwayat perubahan dan aktivitas produk.
            </p>
          </div>

          <div class="px-5 py-6 sm:px-6">
            <div class="rounded-md border border-dashed border-[#D6DDD9] bg-[#F8FAF9] px-4 py-5">
              <p class="text-[14px] font-medium leading-5 text-[#46514B]">
                Belum ada data riwayat yang tersedia pada halaman ini.
              </p>
              <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                Data history/audit belum tersedia dari API yang digunakan oleh halaman produk saat ini.
              </p>
            </div>
          </div>
        </section>

        <!-- Bottom action -->
        <footer class="mt-8 flex flex-col-reverse gap-3 border-t border-[#E6EBE8] pt-5 sm:flex-row sm:items-center sm:justify-end">
          <button
            type="button"
            class="inline-flex min-h-10 items-center justify-center rounded-md border border-[#D6DDD9] bg-white px-4 text-[14px] font-medium text-[#46514B] transition hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="goBack"
          >
            Kembali ke Produk
          </button>

          <button
            type="button"
            class="inline-flex min-h-10 items-center justify-center rounded-md bg-[#176B4D] px-4 text-[14px] font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="goToEdit"
          >
            Edit Produk
          </button>
        </footer>
      </section>
    </div>
  </main>
</template>
