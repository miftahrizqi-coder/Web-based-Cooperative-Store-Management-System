<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { createStockOpname, getInventory } from '../../api/inventory'

import type { InventoryItem, StockOpnamePayload } from '../../types/inventory'

const router = useRouter()

const REASON_MIN = 3
const REASON_MAX = 500

/* ---------- State ---------- */
const accessToken = localStorage.getItem('access_token')

const products = ref<InventoryItem[]>([])
const productSearch = ref('')
const selectedProductId = ref('')
const physicalStock = ref<number | null>(null)
const reason = ref('')

const loading = ref(true)
const submitting = ref(false)
const loadError = ref('')
const submitError = ref('')
const successMessage = ref('')
const fieldErrors = ref({ product: '', physical: '', reason: '' })

const showConfirmation = ref(false)
const submitButtonRef = ref<HTMLButtonElement | null>(null)
const dialogRef = ref<HTMLElement | null>(null)
const cancelButtonRef = ref<HTMLButtonElement | null>(null)

/* ---------- Formatting ---------- */
const numberFormatter = new Intl.NumberFormat('id-ID', { maximumFractionDigits: 3 })

function formatNumber(value: number): string {
  return numberFormatter.format(value)
}

function formatSigned(value: number): string {
  if (value > 0) return `+${numberFormatter.format(value)}`
  if (value < 0) return `−${numberFormatter.format(Math.abs(value))}`
  return '0'
}

/* ---------- Derived ---------- */
const filteredProducts = computed(() => {
  const q = productSearch.value.trim().toLowerCase()
  if (!q) return products.value
  return products.value.filter(
    (p) =>
      p.name.toLowerCase().includes(q) ||
      String(p.sku ?? '').toLowerCase().includes(q),
  )
})

const selectedProduct = computed(() =>
  products.value.find((p) => p.product_id === selectedProductId.value),
)

const systemStock = computed(() => selectedProduct.value?.stock ?? 0)

const unit = computed(() => selectedProduct.value?.unit ?? '')

/* input number yang dikosongkan menghasilkan '' — anggap belum diisi */
const hasPhysical = computed(
  () => typeof physicalStock.value === 'number' && Number.isFinite(physicalStock.value),
)

const physicalValue = computed(() => (hasPhysical.value ? (physicalStock.value as number) : 0))

const difference = computed(() => {
  if (!hasPhysical.value) return 0
  return Math.round((physicalValue.value - systemStock.value) * 1000) / 1000
})

const isNegativePhysical = computed(() => hasPhysical.value && physicalValue.value < 0)

const differenceStatus = computed(() => {
  if (!selectedProduct.value || !hasPhysical.value || isNegativePhysical.value) return null
  if (difference.value === 0)
    return {
      label: 'Sesuai — tidak ada selisih',
      cls: 'bg-[#E7F4EC] text-[#0F6B3A] border-[#B9DFC9]',
    }
  if (difference.value > 0)
    return { label: 'Lebih dari sistem', cls: 'bg-[#E8F1F8] text-[#1F5F87] border-[#BCD6E8]' }
  return { label: 'Kurang dari sistem', cls: 'bg-[#FBF3E2] text-[#8A5A12] border-[#EBD5A6]' }
})

const differenceTextClass = computed(() => {
  if (difference.value > 0) return 'text-[#0F6B3A]'
  if (difference.value < 0) return 'text-[#8A5A12]'
  return 'text-[#17201C]'
})

const requirements = computed(() => [
  { label: 'Produk dipilih', ok: !!selectedProductId.value },
  { label: 'Stok fisik terisi dan tidak negatif', ok: hasPhysical.value && !isNegativePhysical.value },
  { label: `Alasan minimal ${REASON_MIN} karakter`, ok: reason.value.trim().length >= REASON_MIN },
])

const livePhysicalError = computed(() =>
  isNegativePhysical.value ? 'Stok fisik tidak boleh negatif.' : '',
)

const physicalErrorText = computed(() => fieldErrors.value.physical || livePhysicalError.value)

/* ---------- Data ---------- */
async function loadProducts(silent = false) {
  if (!silent) loading.value = true
  loadError.value = ''

  try {
    if (!accessToken) {
      throw new Error('Sesi login tidak ditemukan. Silakan masuk kembali.')
    }
    products.value = await getInventory(accessToken)
  } catch (error) {
    loadError.value =
      error instanceof Error ? error.message : 'Data produk tidak dapat dimuat.'
  } finally {
    loading.value = false
  }
}

/* ---------- Validation ---------- */
function validateForm(): boolean {
  fieldErrors.value = { product: '', physical: '', reason: '' }

  if (!selectedProductId.value) {
    fieldErrors.value.product = 'Pilih produk yang akan dilakukan stock opname.'
  }

  if (!hasPhysical.value) {
    fieldErrors.value.physical = 'Stok fisik wajib diisi dengan angka yang valid.'
  } else if (physicalValue.value < 0) {
    fieldErrors.value.physical = 'Stok fisik tidak boleh negatif.'
  }

  if (reason.value.trim().length < REASON_MIN) {
    fieldErrors.value.reason = `Alasan wajib diisi, minimal ${REASON_MIN} karakter.`
  }

  return !Object.values(fieldErrors.value).some(Boolean)
}

watch(selectedProductId, () => {
  physicalStock.value = null
  fieldErrors.value = { product: '', physical: '', reason: fieldErrors.value.reason }
  successMessage.value = ''
  submitError.value = ''
})
watch(physicalStock, () => (fieldErrors.value.physical = ''))
watch(reason, () => (fieldErrors.value.reason = ''))

/* ---------- Confirmation dialog ---------- */
function openConfirmation() {
  successMessage.value = ''
  submitError.value = ''

  if (!validateForm()) return

  showConfirmation.value = true
}

function closeConfirmation() {
  if (submitting.value) return
  showConfirmation.value = false
}

watch(showConfirmation, async (open) => {
  await nextTick()
  if (open) {
    cancelButtonRef.value?.focus()
  } else {
    submitButtonRef.value?.focus()
  }
})

function onDialogKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    e.preventDefault()
    closeConfirmation()
    return
  }

  if (e.key !== 'Tab' || !dialogRef.value) return

  const focusable = dialogRef.value.querySelectorAll<HTMLElement>(
    'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
  )
  if (focusable.length === 0) return

  const first = focusable[0]
  const last = focusable[focusable.length - 1]

  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault()
    first.focus()
  }
}

/* ---------- Submit ---------- */
async function submitStockOpname() {
  if (!validateForm()) {
    showConfirmation.value = false
    return
  }

  if (!accessToken) {
    submitError.value = 'Sesi login tidak ditemukan. Silakan masuk kembali.'
    showConfirmation.value = false
    return
  }

  const productName = selectedProduct.value?.name ?? 'Produk'
  const productUnit = unit.value

  const payload: StockOpnamePayload = {
    product_id: selectedProductId.value,
    physical_stock: physicalValue.value,
    reason: reason.value.trim(),
  }

  submitting.value = true
  submitError.value = ''
  successMessage.value = ''

  try {
    const response = await createStockOpname(accessToken, payload)

    successMessage.value =
      `Stock opname ${productName} berhasil disimpan. ` +
      `Stok sistem ${formatNumber(response.system_stock)} → stok fisik ${formatNumber(response.physical_stock)}, ` +
      `selisih ${formatSigned(response.difference)}${productUnit ? ' ' + productUnit : ''}.`

    showConfirmation.value = false

    await loadProducts(true)

    physicalStock.value = null
    reason.value = ''
    fieldErrors.value = { product: '', physical: '', reason: '' }
  } catch (error) {
    const detail = error instanceof Error ? error.message : 'Terjadi kesalahan pada server.'
    submitError.value = `Stock opname gagal disimpan. Stok tidak berubah. ${detail} Periksa data lalu coba lagi.`
    showConfirmation.value = false
  } finally {
    submitting.value = false
  }
}

function goBack() {
  router.push('/inventory')
}

function goProducts() {
  router.push('/products')
}

onMounted(() => {
  loadProducts()
})
</script>

<template>
  <section class="mx-auto w-full max-w-[1440px] font-sans text-[#17201C]">
    <!-- Breadcrumb -->
    <nav aria-label="Breadcrumb" class="mb-3 text-[13px] leading-[18px] text-[#6B756F]">
      <ol class="flex items-center gap-2">
        <li>
          <router-link
            to="/inventory"
            class="rounded-sm hover:text-[#176B4D] hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          >
            Inventory
          </router-link>
        </li>
        <li aria-hidden="true">/</li>
        <li aria-current="page" class="font-medium text-[#46514B]">Stock Opname</li>
      </ol>
    </nav>

    <!-- Page header -->
    <header class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h1 class="text-[28px] font-semibold leading-9 text-[#17201C]">Stock Opname</h1>
        <p class="mt-1 max-w-2xl text-sm leading-5 text-[#46514B]">
          Cocokkan stok sistem dengan hasil penghitungan fisik. Selisih yang ditemukan akan
          menyesuaikan stok sistem dan dicatat sebagai riwayat baru.
        </p>
      </div>

      <button
        type="button"
        class="inline-flex h-10 shrink-0 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
        @click="goBack"
      >
        Kembali ke Stok
      </button>
    </header>

    <!-- Success -->
    <div
      v-if="successMessage"
      class="mb-6 flex items-start gap-3 rounded-lg border border-[#B9DFC9] bg-[#E7F4EC] px-4 py-3"
      role="status"
      aria-live="polite"
    >
      <span
        aria-hidden="true"
        class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#16834B] text-xs font-bold text-white"
      >✓</span>
      <p class="text-sm leading-5 text-[#0F5C33]">
        <span class="font-semibold">Berhasil.</span> {{ successMessage }}
      </p>
    </div>

    <!-- Submit error -->
    <div
      v-if="submitError"
      class="mb-6 flex items-start gap-3 rounded-lg border border-[#F0C4BF] bg-[#FBEAE8] px-4 py-3"
      role="alert"
    >
      <span
        aria-hidden="true"
        class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#C0392B] text-xs font-bold text-white"
      >!</span>
      <p class="text-sm leading-5 text-[#8E271C]">{{ submitError }}</p>
    </div>

    <!-- Loading -->
    <div
      v-if="loading"
      class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]"
      role="status"
      aria-label="Memuat data produk"
    >
      <div class="animate-pulse space-y-6 rounded-lg border border-[#D6DDD9] bg-white p-6">
        <div class="h-4 w-32 rounded bg-[#E6EBE8]" />
        <div class="h-10 rounded-lg bg-[#E6EBE8]" />
        <div class="h-4 w-40 rounded bg-[#E6EBE8]" />
        <div class="h-10 rounded-lg bg-[#E6EBE8]" />
        <div class="h-24 rounded-lg bg-[#E6EBE8]" />
      </div>
      <div class="animate-pulse space-y-4 rounded-lg border border-[#D6DDD9] bg-white p-6">
        <div class="h-4 w-28 rounded bg-[#E6EBE8]" />
        <div class="h-16 rounded-lg bg-[#E6EBE8]" />
        <div class="h-16 rounded-lg bg-[#E6EBE8]" />
        <div class="h-16 rounded-lg bg-[#E6EBE8]" />
      </div>
    </div>

    <!-- Load error -->
    <div
      v-else-if="loadError"
      class="rounded-lg border border-[#F0C4BF] bg-white p-8 text-center"
      role="alert"
    >
      <h2 class="text-lg font-semibold text-[#17201C]">Data produk gagal dimuat</h2>
      <p class="mx-auto mt-1 max-w-md text-sm leading-5 text-[#46514B]">
        {{ loadError }} Tidak ada perubahan pada stok. Periksa koneksi lalu coba lagi.
      </p>
      <button
        type="button"
        class="mt-5 inline-flex h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
        @click="loadProducts()"
      >
        Muat ulang
      </button>
    </div>

    <!-- Empty -->
    <div
      v-else-if="products.length === 0"
      class="rounded-lg border border-[#D6DDD9] bg-white p-10 text-center"
    >
      <div
        aria-hidden="true"
        class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#F0F8F5] text-xl text-[#176B4D]"
      >▦</div>
      <h2 class="text-lg font-semibold text-[#17201C]">Belum ada produk untuk di-opname</h2>
      <p class="mx-auto mt-1 max-w-md text-sm leading-5 text-[#46514B]">
        Stock opname membandingkan stok sistem dengan stok fisik produk yang sudah terdaftar.
        Tambahkan produk terlebih dahulu, lalu kembali ke halaman ini.
      </p>
      <div class="mt-5 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <button
          type="button"
          class="inline-flex h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          @click="goProducts"
        >
          Lihat Produk
        </button>
        <button
          type="button"
          class="inline-flex h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          @click="goBack"
        >
          Kembali ke Stok
        </button>
      </div>
    </div>

    <!-- Form -->
    <form v-else novalidate @submit.prevent="openConfirmation">
      <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <!-- Main form -->
        <div class="space-y-6">
          <!-- Section 1 -->
          <fieldset class="rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6">
            <legend class="sr-only">Pilih produk</legend>
            <h2 class="text-lg font-semibold leading-[26px] text-[#17201C]">1. Pilih produk</h2>
            <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">
              Cari berdasarkan nama atau SKU. Stok sistem produk akan tampil di panel kanan.
            </p>

            <div class="mt-4 space-y-4">
              <div>
                <label for="product-search" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Cari produk
                </label>
                <input
                  id="product-search"
                  v-model="productSearch"
                  type="search"
                  autocomplete="off"
                  placeholder="Ketik nama atau SKU"
                  class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm text-[#17201C] placeholder:text-[#6B756F] focus:border-[#176B4D] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
                />
              </div>

              <div>
                <label for="product" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Produk <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  <span class="sr-only">(wajib)</span>
                </label>
                <select
                  id="product"
                  v-model="selectedProductId"
                  :aria-invalid="!!fieldErrors.product"
                  :aria-describedby="fieldErrors.product ? 'product-error' : 'product-hint'"
                  class="h-10 w-full rounded-lg border bg-white px-3 text-sm text-[#17201C] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
                  :class="fieldErrors.product ? 'border-[#C0392B]' : 'border-[#D6DDD9] focus:border-[#176B4D]'"
                >
                  <option value="">Pilih produk</option>
                  <option
                    v-for="product in filteredProducts"
                    :key="product.product_id"
                    :value="product.product_id"
                  >
                    {{ product.sku }} — {{ product.name }} (sistem {{ formatNumber(product.stock) }})
                  </option>
                </select>

                <p
                  v-if="fieldErrors.product"
                  id="product-error"
                  role="alert"
                  class="mt-1.5 text-xs leading-4 text-[#C0392B]"
                >
                  {{ fieldErrors.product }}
                </p>
                <p v-else id="product-hint" class="mt-1.5 text-xs leading-4 text-[#6B756F]">
                  <template v-if="productSearch && filteredProducts.length === 0">
                    Tidak ada produk yang cocok dengan “{{ productSearch }}”. Coba kata kunci lain.
                  </template>
                  <template v-else>{{ formatNumber(filteredProducts.length) }} produk tersedia.</template>
                </p>
              </div>
            </div>
          </fieldset>

          <!-- Section 2 -->
          <fieldset class="rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6">
            <legend class="sr-only">Hasil penghitungan fisik dan alasan</legend>
            <h2 class="text-lg font-semibold leading-[26px] text-[#17201C]">2. Hasil penghitungan fisik</h2>
            <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">
              Masukkan jumlah total yang benar-benar ditemukan, bukan selisihnya.
            </p>

            <div class="mt-4 space-y-5">
              <div>
                <label for="physical-stock" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Stok fisik <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  <span class="sr-only">(wajib)</span>
                </label>

                <div class="flex flex-wrap items-center gap-3">
                  <input
                    id="physical-stock"
                    v-model.number="physicalStock"
                    type="number"
                    min="0"
                    step="any"
                    inputmode="decimal"
                    placeholder="Contoh: 48"
                    :aria-invalid="!!physicalErrorText"
                    :aria-describedby="physicalErrorText ? 'physical-error' : 'physical-hint'"
                    class="h-10 w-full max-w-[220px] rounded-lg border bg-white px-3 text-right text-sm tabular-nums text-[#17201C] placeholder:text-[#6B756F] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
                    :class="physicalErrorText ? 'border-[#C0392B]' : 'border-[#D6DDD9] focus:border-[#176B4D]'"
                  />
                  <span v-if="unit" class="text-sm text-[#46514B]">{{ unit }}</span>

                  <span
                    v-if="differenceStatus"
                    class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium"
                    :class="differenceStatus.cls"
                  >
                    {{ differenceStatus.label }}<template v-if="difference !== 0"> {{ formatSigned(difference) }}</template>
                  </span>
                </div>

                <p
                  v-if="physicalErrorText"
                  id="physical-error"
                  role="alert"
                  class="mt-1.5 text-xs leading-4 text-[#C0392B]"
                >
                  {{ physicalErrorText }}
                </p>
                <p v-else id="physical-hint" class="mt-1.5 text-xs leading-4 text-[#6B756F]">
                  Boleh berisi 0 jika barang tidak ditemukan sama sekali. Desimal diperbolehkan.
                </p>
              </div>

              <div>
                <label for="reason" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Alasan stock opname <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  <span class="sr-only">(wajib)</span>
                </label>
                <textarea
                  id="reason"
                  v-model="reason"
                  rows="4"
                  :maxlength="REASON_MAX"
                  placeholder="Contoh: Hasil pengecekan stok fisik gudang akhir bulan"
                  :aria-invalid="!!fieldErrors.reason"
                  :aria-describedby="fieldErrors.reason ? 'reason-error' : 'reason-hint'"
                  class="w-full resize-y rounded-lg border bg-white px-3 py-2.5 text-sm leading-5 text-[#17201C] placeholder:text-[#6B756F] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
                  :class="fieldErrors.reason ? 'border-[#C0392B]' : 'border-[#D6DDD9] focus:border-[#176B4D]'"
                />
                <div class="mt-1.5 flex items-start justify-between gap-3 text-xs leading-4">
                  <p v-if="fieldErrors.reason" id="reason-error" role="alert" class="text-[#C0392B]">
                    {{ fieldErrors.reason }}
                  </p>
                  <p v-else id="reason-hint" class="text-[#6B756F]">
                    Minimal {{ REASON_MIN }} karakter, maksimal {{ REASON_MAX }} karakter.
                  </p>
                  <span class="shrink-0 tabular-nums text-[#6B756F]">
                    {{ reason.length }} / {{ REASON_MAX }}
                  </span>
                </div>
              </div>
            </div>
          </fieldset>
        </div>

        <!-- Context / summary -->
        <aside class="space-y-6 lg:sticky lg:top-6 lg:self-start" aria-label="Ringkasan perbandingan stok">
          <div class="rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6">
            <h2 class="text-lg font-semibold leading-[26px] text-[#17201C]">Perbandingan stok</h2>

            <div v-if="selectedProduct" class="mt-3">
              <p class="text-sm font-medium leading-5 text-[#17201C]">{{ selectedProduct.name }}</p>
              <p class="text-[13px] leading-[18px] text-[#6B756F]">SKU {{ selectedProduct.sku }}</p>
            </div>
            <p v-else class="mt-3 text-sm leading-5 text-[#6B756F]">
              Pilih produk untuk melihat stok sistem dan membandingkannya dengan stok fisik.
            </p>

            <dl class="mt-4 divide-y divide-[#E6EBE8] rounded-lg border border-[#E6EBE8] bg-[#F8FAF9]">
              <div class="flex items-baseline justify-between gap-3 px-4 py-3">
                <dt class="text-[13px] leading-[18px] text-[#46514B]">Stok sistem</dt>
                <dd class="text-base font-medium tabular-nums text-[#17201C]">
                  {{ selectedProduct ? formatNumber(systemStock) : '—' }}
                  <span v-if="selectedProduct" class="text-[13px] font-normal text-[#6B756F]">{{ unit }}</span>
                </dd>
              </div>

              <div class="flex items-baseline justify-between gap-3 px-4 py-3">
                <dt class="text-[13px] leading-[18px] text-[#46514B]">Stok fisik</dt>
                <dd class="text-base font-medium tabular-nums text-[#17201C]">
                  {{ hasPhysical ? formatNumber(physicalValue) : '—' }}
                  <span v-if="hasPhysical" class="text-[13px] font-normal text-[#6B756F]">{{ unit }}</span>
                </dd>
              </div>

              <div class="flex items-baseline justify-between gap-3 bg-white px-4 py-3">
                <dt class="text-[13px] font-medium leading-[18px] text-[#17201C]">Selisih</dt>
                <dd class="text-[22px] font-semibold leading-[30px] tabular-nums" :class="differenceTextClass">
                  {{ selectedProduct && hasPhysical ? formatSigned(difference) : '—' }}
                  <span
                    v-if="selectedProduct && hasPhysical"
                    class="text-[13px] font-normal text-[#6B756F]"
                  >{{ unit }}</span>
                </dd>
              </div>
            </dl>

            <div v-if="differenceStatus" class="mt-3" role="status" aria-live="polite">
              <span
                class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium"
                :class="differenceStatus.cls"
              >
                {{ differenceStatus.label }}
              </span>
              <p class="mt-2 text-[13px] leading-[18px] text-[#46514B]">
                <template v-if="difference === 0">Stok sistem sudah sama dengan stok fisik.</template>
                <template v-else>
                  Stok sistem akan menjadi
                  <span class="font-semibold tabular-nums text-[#17201C]">{{ formatNumber(physicalValue) }} {{ unit }}</span>.
                </template>
              </p>
            </div>
          </div>

          <div class="rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6">
            <h2 class="text-base font-semibold leading-6 text-[#17201C]">Status validasi</h2>
            <ul class="mt-3 space-y-2">
              <li
                v-for="req in requirements"
                :key="req.label"
                class="flex items-start gap-2.5 text-[13px] leading-[18px]"
                :class="req.ok ? 'text-[#17201C]' : 'text-[#6B756F]'"
              >
                <span
                  aria-hidden="true"
                  class="mt-px flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
                  :class="req.ok ? 'bg-[#16834B] text-white' : 'border border-[#D6DDD9] bg-white text-transparent'"
                >✓</span>
                <span>
                  {{ req.label }}
                  <span class="sr-only">— {{ req.ok ? 'terpenuhi' : 'belum terpenuhi' }}</span>
                </span>
              </li>
            </ul>
          </div>

          <div class="rounded-lg border border-[#DCEFE7] bg-[#F0F8F5] p-4 text-[13px] leading-[18px] text-[#164A38]">
            <p class="font-semibold">Tentang riwayat</p>
            <p class="mt-1">
              Hasil opname dicatat sebagai event baru pada riwayat stok dan audit log. Catatan lama
              tidak diubah, dan opname yang sudah disimpan tidak dapat dihapus.
            </p>
          </div>
        </aside>
      </div>

      <!-- Sticky footer -->
      <div
        class="sticky bottom-0 z-10 -mx-4 mt-6 border-t border-[#D6DDD9] bg-white px-4 py-3 sm:mx-0 sm:rounded-lg sm:border sm:px-6 sm:py-4 sm:shadow-[0_1px_2px_rgba(18,55,42,.06)]"
      >
        <div class="flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
          <button
            type="button"
            class="inline-flex h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
            @click="goBack"
          >
            Batal
          </button>

          <button
            ref="submitButtonRef"
            type="submit"
            :disabled="submitting"
            class="inline-flex h-10 items-center justify-center rounded-lg bg-[#176B4D] px-5 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
          >
            Tinjau Stock Opname
          </button>
        </div>
      </div>
    </form>

    <!-- Confirmation dialog -->
    <div
      v-if="showConfirmation"
      class="fixed inset-0 z-50 flex items-center justify-center bg-[#12372A]/50 p-4"
      @click.self="closeConfirmation"
    >
      <div
        ref="dialogRef"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirmation-title"
        aria-describedby="confirmation-desc"
        class="w-full max-w-md rounded-xl bg-white p-6 shadow-[0_12px_32px_rgba(18,55,42,.12)]"
        @keydown="onDialogKeydown"
      >
        <h2 id="confirmation-title" class="text-lg font-semibold leading-[26px] text-[#17201C]">
          Konfirmasi Stock Opname
        </h2>

        <p id="confirmation-desc" class="mt-1 text-sm leading-5 text-[#46514B]">
          Periksa hasilnya. Stok sistem akan disesuaikan dengan stok fisik dan tidak dapat
          dibatalkan setelah disimpan.
        </p>

        <div v-if="selectedProduct" class="mt-4">
          <p class="text-sm font-medium text-[#17201C]">{{ selectedProduct.name }}</p>
          <p class="text-[13px] text-[#6B756F]">SKU {{ selectedProduct.sku }}</p>
        </div>

        <dl class="mt-3 divide-y divide-[#E6EBE8] rounded-lg border border-[#E6EBE8] bg-[#F8FAF9] text-sm">
          <div class="flex items-baseline justify-between px-4 py-2.5">
            <dt class="text-[#46514B]">Stok sistem</dt>
            <dd class="tabular-nums text-[#17201C]">{{ formatNumber(systemStock) }} {{ unit }}</dd>
          </div>
          <div class="flex items-baseline justify-between px-4 py-2.5">
            <dt class="text-[#46514B]">Stok fisik</dt>
            <dd class="tabular-nums text-[#17201C]">{{ formatNumber(physicalValue) }} {{ unit }}</dd>
          </div>
          <div class="flex items-baseline justify-between bg-white px-4 py-2.5">
            <dt class="font-medium text-[#17201C]">Selisih</dt>
            <dd class="text-base font-semibold tabular-nums" :class="differenceTextClass">
              {{ formatSigned(difference) }} {{ unit }}
              <span class="ml-1 text-xs font-normal text-[#6B756F]">
                ({{ difference > 0 ? 'lebih' : difference < 0 ? 'kurang' : 'sesuai' }})
              </span>
            </dd>
          </div>
        </dl>

        <p
          v-if="difference !== 0"
          class="mt-3 rounded-lg bg-[#FBF3E2] px-4 py-3 text-[13px] leading-[18px] text-[#6B4A0F]"
        >
          Stok sistem berubah dari
          <span class="font-semibold tabular-nums">{{ formatNumber(systemStock) }}</span>
          menjadi
          <span class="font-semibold tabular-nums">{{ formatNumber(physicalValue) }}</span>
          {{ unit }}.
        </p>
        <p v-else class="mt-3 rounded-lg bg-[#F0F8F5] px-4 py-3 text-[13px] leading-[18px] text-[#164A38]">
          Tidak ada selisih, sehingga stok sistem tidak berubah.
        </p>

        <div class="mt-3 rounded-lg bg-[#F1F4F2] px-4 py-3 text-sm leading-5">
          <p class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">Alasan</p>
          <p class="mt-0.5 whitespace-pre-line break-words text-[#17201C]">{{ reason.trim() }}</p>
        </div>

        <div class="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            ref="cancelButtonRef"
            type="button"
            :disabled="submitting"
            class="inline-flex h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
            @click="closeConfirmation"
          >
            Batal
          </button>

          <button
            type="button"
            :disabled="submitting"
            :aria-busy="submitting"
            class="inline-flex h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
            @click="submitStockOpname"
          >
            {{ submitting ? 'Menyimpan…' : 'Simpan Stock Opname' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>