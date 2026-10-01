<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createProduct, getProduct, updateProduct } from '../../api/products'
import { useAuth } from '../../stores/auth'
import { getCategories } from '../../api/categories'
import type { Category } from '../../types/category'
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
const categories = ref<Category[]>([])
const selectableCategories = computed(() =>
  categories.value.filter((category) => category.isActive || category.id === categoryId.value),
)

const isLoading = ref(isEdit)
const isSaving = ref(false)
const errorMessage = ref('')
const fieldError = ref('')

const formTitle = computed(() => (isEdit ? 'Edit produk' : 'Tambah produk'))
const formDescription = computed(() =>
  isEdit
    ? 'Perbarui informasi produk, harga, dan status. Stok diubah melalui Stock Adjustment / Stock Opname agar tercatat.'
    : 'Lengkapi informasi dasar, harga, stok, SKU, dan barcode sebelum menyimpan produk.',
)

const stockState = computed(() => {
  if (stock.value <= 0) {
    return {
      label: 'Stok habis',
      class: 'border-[#E7B8B2] bg-[#FEF3F2] text-[#C0392B]',
    }
  }

  if (stock.value <= minimumStock.value) {
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
  }).format(Number(value) || 0)
}

function goBack() {
  router.push('/products')
}

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
    fieldError.value = 'Kategori wajib dipilih.'
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
  categoryId.value = product.categoryId
  unit.value = product.unit
  purchasePrice.value = product.purchasePrice ?? 0
  sellingPrice.value = product.sellingPrice
  stock.value = product.stock
  minimumStock.value = product.minimumStock
  isActive.value = product.isActive
}

async function loadProduct() {
  try {
    categories.value = await getCategories()
  } catch {
    categories.value = []
  }

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
      categoryId: categoryId.value,
      unit: unit.value.trim(),
      purchasePrice: purchasePrice.value,
      sellingPrice: sellingPrice.value,
      minimumStock: minimumStock.value,
    }

    if (isEdit && productId) {
      await updateProduct(token.value, productId, {
        ...payload,
        isActive: isActive.value,
      })
    } else {
      // Stok awal dicatat backend sebagai stock movement.
      await createProduct(token.value, { ...payload, stock: stock.value })
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
  <main class="min-w-0 bg-[#F8FAF9] font-[Inter,ui-sans-serif,system-ui,sans-serif] text-[#17201C]">
    <div class="mx-auto w-full max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8">
      <!-- Breadcrumb -->
      <nav class="mb-4" aria-label="Breadcrumb">
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
          <li aria-current="page">{{ formTitle }}</li>
        </ol>
      </nav>

      <!-- Page header -->
      <header class="border-b border-[#E6EBE8] pb-6">
        <div class="flex flex-col gap-2">
          <h1 class="text-[28px] font-semibold leading-9 tracking-[-0.01em] text-[#17201C]">
            {{ formTitle }}
          </h1>
          <p class="max-w-3xl text-[14px] leading-5 text-[#6B756F]">
            {{ formDescription }}
          </p>
        </div>
      </header>

      <!-- Loading -->
      <section v-if="isLoading" class="mt-6" aria-label="Memuat data produk">
        <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div class="rounded-lg border border-[#D6DDD9] bg-white p-6">
            <div class="space-y-6">
              <div v-for="index in 8" :key="index" class="space-y-2">
                <div class="h-4 w-28 animate-pulse rounded bg-[#E6EBE8]" />
                <div class="h-10 animate-pulse rounded-md bg-[#F1F4F2]" />
              </div>
            </div>
          </div>

          <aside class="rounded-lg border border-[#D6DDD9] bg-white p-5">
            <div class="space-y-4">
              <div class="h-5 w-36 animate-pulse rounded bg-[#E6EBE8]" />
              <div class="h-24 animate-pulse rounded-md bg-[#F1F4F2]" />
              <div class="h-16 animate-pulse rounded-md bg-[#F1F4F2]" />
            </div>
          </aside>
        </div>
      </section>

      <!-- Load error -->
      <section
        v-else-if="errorMessage && isEdit && !sku"
        class="mt-6 rounded-lg border border-[#E7B8B2] bg-white p-6"
        role="alert"
      >
        <div class="flex items-start gap-3">
          <div class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#FEF3F2] text-[#C0392B]">
            !
          </div>

          <div>
            <h2 class="text-[18px] font-semibold leading-[26px] text-[#17201C]">
              Produk gagal dimuat
            </h2>
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

      <!-- Form -->
      <form
        v-else
        class="mt-6 pb-24"
        novalidate
        @submit.prevent="handleSubmit"
      >
        <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
          <!-- Main form -->
          <div class="min-w-0 space-y-6">
            <!-- Errors -->
            <section
              v-if="errorMessage || fieldError"
              class="space-y-3"
              aria-label="Pesan validasi"
            >
              <div
                v-if="errorMessage"
                role="alert"
                class="rounded-md border border-[#E7B8B2] bg-[#FEF3F2] px-4 py-3"
              >
                <p class="text-[14px] font-medium leading-5 text-[#C0392B]">
                  {{ errorMessage }}
                </p>
              </div>

              <div
                v-if="fieldError"
                role="alert"
                class="rounded-md border border-[#E6C98F] bg-[#FFF8E8] px-4 py-3"
              >
                <p class="text-[14px] font-medium leading-5 text-[#B7791F]">
                  {{ fieldError }}
                </p>
              </div>
            </section>

            <!-- Basic information -->
            <section
              class="rounded-lg border border-[#D6DDD9] bg-white"
              aria-labelledby="basic-information-title"
            >
              <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
                <h2
                  id="basic-information-title"
                  class="text-[18px] font-semibold leading-[26px] text-[#17201C]"
                >
                  Informasi dasar
                </h2>
                <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                  Identitas utama produk yang digunakan pada katalog dan transaksi.
                </p>
              </div>

              <div class="grid gap-5 p-5 sm:grid-cols-2 sm:p-6">
                <label class="block">
                  <span class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#46514B]">
                    Nama produk
                    <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  </span>
                  <input
                    v-model="name"
                    required
                    type="text"
                    autocomplete="off"
                    class="min-h-10 w-full rounded-md border border-[#D6DDD9] bg-white px-3 text-[14px] leading-5 text-[#17201C] outline-none transition placeholder:text-[#6B756F] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                  >
                </label>

                <label class="block">
                  <span class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#46514B]">
                    SKU
                    <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  </span>
                  <input
                    v-model="sku"
                    required
                    type="text"
                    autocomplete="off"
                    :disabled="isEdit"
                    class="min-h-10 w-full rounded-md border border-[#D6DDD9] bg-white px-3 text-[14px] leading-5 text-[#17201C] outline-none transition placeholder:text-[#6B756F] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-[#F1F4F2] disabled:text-[#6B756F]"
                  >
                  <span v-if="isEdit" class="mt-1 block text-[12px] leading-4 text-[#6B756F]">
                    SKU tidak diubah setelah produk dibuat.
                  </span>
                </label>

                <label class="block">
                  <span class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#46514B]">
                    Barcode
                  </span>
                  <input
                    v-model="barcode"
                    type="text"
                    inputmode="numeric"
                    autocomplete="off"
                    class="min-h-10 w-full rounded-md border border-[#D6DDD9] bg-white px-3 text-[14px] leading-5 text-[#17201C] outline-none transition placeholder:text-[#6B756F] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                  >
                  <span class="mt-1 block text-[12px] leading-4 text-[#6B756F]">
                    Opsional.
                  </span>
                </label>

                <label class="block">
                  <span class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#46514B]">
                    Kategori
                    <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  </span>
                  <select
                    v-model="categoryId"
                    required
                    class="min-h-10 w-full rounded-md border border-[#D6DDD9] bg-white px-3 text-[14px] leading-5 text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                  >
                    <option value="" disabled>Pilih kategori</option>
                    <option v-for="category in selectableCategories" :key="category.id" :value="category.id">
                      {{ category.name }}{{ category.isActive ? '' : ' (nonaktif)' }}
                    </option>
                  </select>
                  <span v-if="categories.length === 0" class="mt-1 block text-[12px] leading-4 text-[#9A650F]">
                    Belum ada kategori. Tambahkan di menu Kategori.
                  </span>
                </label>

                <label class="block sm:col-span-2">
                  <span class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#46514B]">
                    Satuan
                    <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  </span>
                  <input
                    v-model="unit"
                    required
                    type="text"
                    placeholder="pcs"
                    autocomplete="off"
                    class="min-h-10 w-full rounded-md border border-[#D6DDD9] bg-white px-3 text-[14px] leading-5 text-[#17201C] outline-none transition placeholder:text-[#6B756F] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 sm:max-w-md"
                  >
                </label>
              </div>
            </section>

            <!-- Pricing -->
            <section
              class="rounded-lg border border-[#D6DDD9] bg-white"
              aria-labelledby="pricing-title"
            >
              <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
                <h2
                  id="pricing-title"
                  class="text-[18px] font-semibold leading-[26px] text-[#17201C]"
                >
                  Pricing
                </h2>
                <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                  Tentukan harga beli dan harga jual dalam Rupiah.
                </p>
              </div>

              <div class="grid gap-5 p-5 sm:grid-cols-2 sm:p-6">
                <label class="block">
                  <span class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#46514B]">
                    Harga beli
                    <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  </span>
                  <div class="relative">
                    <span class="pointer-events-none absolute inset-y-0 left-3 flex items-center text-[14px] text-[#6B756F]">
                      Rp
                    </span>
                    <input
                      v-model.number="purchasePrice"
                      required
                      min="0"
                      type="number"
                      step="1"
                      inputmode="numeric"
                      class="min-h-10 w-full rounded-md border border-[#D6DDD9] bg-white py-2 pl-10 pr-3 text-right text-[14px] leading-5 text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                    >
                  </div>
                  <span class="mt-1 block text-[12px] leading-4 text-[#6B756F]">
                    {{ formatCurrency(purchasePrice) }}
                  </span>
                </label>

                <label class="block">
                  <span class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#46514B]">
                    Harga jual
                    <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  </span>
                  <div class="relative">
                    <span class="pointer-events-none absolute inset-y-0 left-3 flex items-center text-[14px] text-[#6B756F]">
                      Rp
                    </span>
                    <input
                      v-model.number="sellingPrice"
                      required
                      min="0"
                      type="number"
                      step="1"
                      inputmode="numeric"
                      class="min-h-10 w-full rounded-md border border-[#D6DDD9] bg-white py-2 pl-10 pr-3 text-right text-[14px] leading-5 text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                    >
                  </div>
                  <span class="mt-1 block text-[12px] leading-4 text-[#6B756F]">
                    {{ formatCurrency(sellingPrice) }}
                  </span>
                </label>
              </div>
            </section>

            <!-- Inventory -->
            <section
              class="rounded-lg border border-[#D6DDD9] bg-white"
              aria-labelledby="inventory-title"
            >
              <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
                <h2
                  id="inventory-title"
                  class="text-[18px] font-semibold leading-[26px] text-[#17201C]"
                >
                  Inventory
                </h2>
                <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                  {{ isEdit ? 'Stok hanya berubah lewat transaksi, Stock Adjustment, atau Stock Opname (tercatat di kartu stok).' : 'Atur stok awal dan batas minimum stok produk. Stok awal tercatat sebagai stock movement.' }}
                </p>
              </div>

              <div class="grid gap-5 p-5 sm:grid-cols-2 sm:p-6">
                <label class="block">
                  <span class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#46514B]">
                    {{ isEdit ? 'Stok saat ini' : 'Stok awal' }}
                    <span v-if="!isEdit" class="text-[#C0392B]" aria-hidden="true">*</span>
                  </span>
                  <input
                    v-model.number="stock"
                    :required="!isEdit"
                    :disabled="isEdit"
                    :title="isEdit ? 'Ubah stok melalui Stock Adjustment atau Stock Opname' : undefined"
                    min="0"
                    type="number"
                    step="1"
                    inputmode="numeric"
                    class="disabled:bg-[#F1F4F2] disabled:text-[#6B756F] "min-h-10 w-full rounded-md border border-[#D6DDD9] bg-white px-3 text-right text-[14px] leading-5 text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                  >
                </label>

                <label class="block">
                  <span class="mb-1.5 block text-[13px] font-medium leading-[18px] text-[#46514B]">
                    Stok minimum
                    <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  </span>
                  <input
                    v-model.number="minimumStock"
                    required
                    min="0"
                    type="number"
                    step="1"
                    inputmode="numeric"
                    class="min-h-10 w-full rounded-md border border-[#D6DDD9] bg-white px-3 text-right text-[14px] leading-5 text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                  >
                </label>
              </div>
            </section>

            <!-- Status -->
            <section
              v-if="isEdit"
              class="rounded-lg border border-[#D6DDD9] bg-white"
              aria-labelledby="status-title"
            >
              <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
                <h2
                  id="status-title"
                  class="text-[18px] font-semibold leading-[26px] text-[#17201C]"
                >
                  Status produk
                </h2>
                <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                  Nonaktifkan produk tanpa menghapus histori transaksi yang sudah ada.
                </p>
              </div>

              <div class="p-5 sm:p-6">
                <label class="flex cursor-pointer items-start gap-3">
                  <input
                    v-model="isActive"
                    type="checkbox"
                    class="mt-0.5 h-4 w-4 rounded border-[#D6DDD9] text-[#176B4D] focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                  >
                  <span>
                    <span class="block text-[14px] font-medium leading-5 text-[#17201C]">
                      Produk aktif
                    </span>
                    <span class="mt-1 block text-[13px] leading-[18px] text-[#6B756F]">
                      Produk tetap tersimpan dan dapat digunakan sesuai permission ketika status ini aktif.
                    </span>
                  </span>
                </label>
              </div>
            </section>
          </div>

          <!-- Context / Summary -->
          <aside class="min-w-0 lg:sticky lg:top-6 lg:self-start">
            <div class="space-y-6">
              <section
                class="rounded-lg border border-[#D6DDD9] bg-white"
                aria-labelledby="summary-title"
              >
                <div class="border-b border-[#E6EBE8] px-5 py-4">
                  <h2
                    id="summary-title"
                    class="text-[18px] font-semibold leading-[26px] text-[#17201C]"
                  >
                    Ringkasan
                  </h2>
                  <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                    Konteks data sebelum disimpan.
                  </p>
                </div>

                <dl class="divide-y divide-[#E6EBE8]">
                  <div class="px-5 py-4">
                    <dt class="text-[12px] leading-4 text-[#6B756F]">Nama</dt>
                    <dd class="mt-1 break-words text-[14px] font-medium leading-5 text-[#17201C]">
                      {{ name || 'Belum diisi' }}
                    </dd>
                  </div>

                  <div class="px-5 py-4">
                    <dt class="text-[12px] leading-4 text-[#6B756F]">SKU</dt>
                    <dd class="mt-1 break-all font-mono text-[14px] font-medium leading-5 text-[#17201C]">
                      {{ sku || 'Belum diisi' }}
                    </dd>
                  </div>

                  <div class="px-5 py-4">
                    <dt class="text-[12px] leading-4 text-[#6B756F]">Harga jual</dt>
                    <dd class="mt-1 text-[16px] font-semibold leading-6 text-[#17201C]">
                      {{ formatCurrency(sellingPrice) }}
                    </dd>
                  </div>

                  <div class="px-5 py-4">
                    <dt class="text-[12px] leading-4 text-[#6B756F]">Stok</dt>
                    <dd class="mt-1 flex flex-wrap items-center gap-2">
                      <span class="text-[16px] font-semibold leading-6 text-[#17201C]">
                        {{ stock }} {{ unit || 'unit' }}
                      </span>
                      <span
                        class="inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium leading-4"
                        :class="stockState.class"
                      >
                        {{ stockState.label }}
                      </span>
                    </dd>
                  </div>

                  <div class="px-5 py-4">
                    <dt class="text-[12px] leading-4 text-[#6B756F]">Status</dt>
                    <dd class="mt-1 text-[14px] font-medium leading-5 text-[#17201C]">
                      {{ isEdit ? (isActive ? 'Aktif' : 'Nonaktif') : 'Produk baru' }}
                    </dd>
                  </div>
                </dl>
              </section>

              <section
                class="rounded-lg border border-[#D6DDD9] bg-[#F0F8F5]"
                aria-labelledby="validation-title"
              >
                <div class="p-5">
                  <h2
                    id="validation-title"
                    class="text-[16px] font-semibold leading-6 text-[#12372A]"
                  >
                    Sebelum menyimpan
                  </h2>

                  <ul class="mt-3 space-y-2 text-[13px] leading-[18px] text-[#46514B]">
                    <li class="flex gap-2">
                      <span aria-hidden="true">•</span>
                      <span>SKU, nama, kategori, dan satuan wajib diisi.</span>
                    </li>
                    <li class="flex gap-2">
                      <span aria-hidden="true">•</span>
                      <span>Harga dan stok tidak boleh bernilai negatif.</span>
                    </li>
                    <li class="flex gap-2">
                      <span aria-hidden="true">•</span>
                      <span>Periksa kembali data sebelum menyimpan.</span>
                    </li>
                  </ul>
                </div>
              </section>

              <p class="text-[12px] leading-4 text-[#6B756F]">
                Field bertanda <span class="font-medium text-[#C0392B]">*</span> wajib diisi.
              </p>
            </div>
          </aside>
        </div>

        <!-- Sticky footer -->
        <div class="fixed inset-x-0 bottom-0 z-20 border-t border-[#D6DDD9] bg-white/95 px-4 py-3 backdrop-blur-sm sm:px-6 lg:left-auto lg:right-0 lg:w-[calc(100%-240px)] lg:px-8">
          <div class="mx-auto flex max-w-[1440px] flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-end">
            <button
              type="button"
              :disabled="isSaving"
              class="inline-flex min-h-10 items-center justify-center rounded-md border border-[#D6DDD9] bg-white px-4 text-[14px] font-medium text-[#46514B] transition hover:bg-[#F1F4F2] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
              @click="goBack"
            >
              Batal
            </button>

            <button
              type="submit"
              :disabled="isSaving"
              class="inline-flex min-h-10 items-center justify-center rounded-md bg-[#176B4D] px-4 text-[14px] font-semibold text-white transition hover:bg-[#1F805D] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            >
              {{ isSaving ? 'Menyimpan...' : isEdit ? 'Simpan perubahan' : 'Simpan produk' }}
            </button>
          </div>
        </div>
      </form>
    </div>
  </main>
</template>
