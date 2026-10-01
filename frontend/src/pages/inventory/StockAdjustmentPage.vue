<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { getInventory, createStockAdjustment } from '../../api/inventory'
import type {
  InventoryItem,
  StockAdjustmentPayload,
} from '../../types/inventory'

const router = useRouter()

/* ---------- State ---------- */
const products = ref<InventoryItem[]>([])
const productSearch = ref('')
const selectedProductId = ref('')
const quantity = ref<number | null>(null)
const reason = ref('')

const loading = ref(true)
const submitting = ref(false)
const loadError = ref('')
const submitError = ref('')
const successMessage = ref('')
const fieldErrors = ref<{ product: string; quantity: string; reason: string }>({
  product: '',
  quantity: '',
  reason: '',
})

const showConfirmation = ref(false)
const submitButtonRef = ref<HTMLButtonElement | null>(null)
const dialogRef = ref<HTMLElement | null>(null)
const cancelButtonRef = ref<HTMLButtonElement | null>(null)

const token = localStorage.getItem('access_token')

const REASON_MIN = 3

/* ---------- Derived ---------- */
const nf = new Intl.NumberFormat('id-ID')
const fmt = (n: number) => nf.format(n)
const fmtSigned = (n: number) => (n > 0 ? `+${fmt(n)}` : n < 0 ? `−${fmt(Math.abs(n))}` : '0')

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
  products.value.find((p) => p.productId === selectedProductId.value),
)

const stockBefore = computed(() => selectedProduct.value?.stock ?? 0)

/* input number yang dikosongkan menghasilkan '' — anggap belum diisi */
const hasQuantity = computed(
  () => typeof quantity.value === 'number' && Number.isFinite(quantity.value),
)

const delta = computed(() => (hasQuantity.value ? (quantity.value as number) : 0))

const stockAfter = computed(() => stockBefore.value + delta.value)

const isNegativeStock = computed(
  () => !!selectedProduct.value && hasQuantity.value && stockAfter.value < 0,
)

const unit = computed(() => selectedProduct.value?.unit ?? '')

const directionBadge = computed(() => {
  if (!hasQuantity.value || delta.value === 0) return null
  return delta.value > 0
    ? { label: 'Penambahan', cls: 'bg-[#E7F4EC] text-[#0F6B3A] border-[#B9DFC9]' }
    : { label: 'Pengurangan', cls: 'bg-[#E8F1F8] text-[#1F5F87] border-[#BCD6E8]' }
})

const afterStatus = computed(() => {
  if (!selectedProduct.value || !hasQuantity.value) return null
  if (stockAfter.value < 0)
    return { label: 'Tidak valid — stok negatif', cls: 'bg-[#FBEAE8] text-[#A32F23] border-[#F0C4BF]' }
  if (stockAfter.value === 0)
    return { label: 'Stok habis', cls: 'bg-[#FBEAE8] text-[#A32F23] border-[#F0C4BF]' }
  return { label: 'Tersedia', cls: 'bg-[#E7F4EC] text-[#0F6B3A] border-[#B9DFC9]' }
})

const requirements = computed(() => [
  { label: 'Produk dipilih', ok: !!selectedProductId.value },
  {
    label: 'Jumlah adjustment terisi dan bukan 0',
    ok: hasQuantity.value && quantity.value !== 0,
  },
  { label: 'Stok akhir tidak negatif', ok: !!selectedProduct.value && hasQuantity.value && !isNegativeStock.value },
  {
    label: `Alasan minimal ${REASON_MIN} karakter`,
    ok: reason.value.trim().length >= REASON_MIN,
  },
])

const liveQuantityError = computed(() =>
  isNegativeStock.value
    ? `Stok akhir menjadi ${fmt(stockAfter.value)}. Stok tidak boleh negatif — kurangi jumlah pengurangan.`
    : '',
)

const quantityErrorText = computed(
  () => fieldErrors.value.quantity || liveQuantityError.value,
)

/* ---------- Data ---------- */
async function loadProducts(silent = false) {
  if (!silent) loading.value = true
  loadError.value = ''

  try {
    if (!token) throw new Error('Sesi login tidak ditemukan. Silakan masuk kembali.')
    products.value = await getInventory(token)
  } catch (err) {
    loadError.value =
      err instanceof Error ? err.message : 'Data produk tidak dapat dimuat.'
  } finally {
    loading.value = false
  }
}

/* ---------- Validation ---------- */
function validateForm(): boolean {
  fieldErrors.value = { product: '', quantity: '', reason: '' }

  if (!selectedProductId.value) {
    fieldErrors.value.product = 'Pilih produk yang stoknya akan dikoreksi.'
  }

  if (!hasQuantity.value) {
    fieldErrors.value.quantity = 'Jumlah adjustment wajib diisi.'
  } else if (quantity.value === 0) {
    fieldErrors.value.quantity =
      'Jumlah adjustment tidak boleh 0. Gunakan angka positif atau negatif.'
  } else if (stockAfter.value < 0) {
    fieldErrors.value.quantity = `Stok akhir menjadi ${fmt(stockAfter.value)}. Stok tidak boleh negatif.`
  }

  if (reason.value.trim().length < REASON_MIN) {
    fieldErrors.value.reason = `Alasan wajib diisi, minimal ${REASON_MIN} karakter.`
  }

  return !Object.values(fieldErrors.value).some(Boolean)
}

watch(selectedProductId, () => (fieldErrors.value.product = ''))
watch(quantity, () => (fieldErrors.value.quantity = ''))
watch(reason, () => (fieldErrors.value.reason = ''))

/* ---------- Confirmation dialog ---------- */
function openConfirmation() {
  successMessage.value = ''
  submitError.value = ''

  if (!validateForm()) return

  showConfirmation.value = true
}

function cancelConfirmation() {
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
    cancelConfirmation()
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
async function submitAdjustment() {
  if (!validateForm()) {
    showConfirmation.value = false
    return
  }

  if (!token) {
    submitError.value = 'Sesi login tidak ditemukan. Silakan masuk kembali.'
    showConfirmation.value = false
    return
  }

  submitting.value = true
  submitError.value = ''
  successMessage.value = ''

  const productName = selectedProduct.value?.name ?? 'Produk'
  const productUnit = unit.value

  const payload: StockAdjustmentPayload = {
    productId: selectedProductId.value,
    quantity: quantity.value as number,
    reason: reason.value.trim(),
  }

  try {
    const result = await createStockAdjustment(token, payload)

    successMessage.value =
      `Adjustment ${productName} berhasil dicatat. ` +
      `Stok berubah dari ${fmt(result.stockBefore)} menjadi ${fmt(result.stockAfter)}` +
      `${productUnit ? ' ' + productUnit : ''}.`

    showConfirmation.value = false

    await loadProducts(true)

    quantity.value = null
    reason.value = ''
    fieldErrors.value = { product: '', quantity: '', reason: '' }
  } catch (err) {
    const detail =
      err instanceof Error ? err.message : 'Terjadi kesalahan pada server.'
    submitError.value = `Adjustment gagal disimpan. Stok tidak berubah. ${detail} Periksa data lalu coba lagi.`
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

onMounted(() => loadProducts())
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
        <li aria-current="page" class="font-medium text-[#46514B]">Stock Adjustment</li>
      </ol>
    </nav>

    <!-- Page header -->
    <header class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h1 class="text-[28px] font-semibold leading-9 text-[#17201C]">Stock Adjustment</h1>
        <p class="mt-1 max-w-2xl text-sm leading-5 text-[#46514B]">
          Koreksi stok secara manual. Setiap adjustment dicatat sebagai event baru beserta
          alasannya, sehingga riwayat stok sebelumnya tidak berubah.
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
      <h2 class="text-lg font-semibold text-[#17201C]">Belum ada produk untuk disesuaikan</h2>
      <p class="mx-auto mt-1 max-w-md text-sm leading-5 text-[#46514B]">
        Stock adjustment hanya bisa dilakukan pada produk yang sudah terdaftar. Tambahkan produk
        terlebih dahulu, lalu kembali ke halaman ini.
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
          <!-- Section 1: Produk -->
          <fieldset class="rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6">
            <legend class="sr-only">Pilih produk</legend>
            <h2 class="text-lg font-semibold leading-[26px] text-[#17201C]">1. Pilih produk</h2>
            <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">
              Cari berdasarkan nama atau SKU, lalu pilih produk dari daftar.
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
                    :key="product.productId"
                    :value="product.productId"
                  >
                    {{ product.name }} — {{ product.sku }} (stok {{ fmt(product.stock) }})
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
                  <template v-else>
                    {{ fmt(filteredProducts.length) }} produk tersedia.
                  </template>
                </p>
              </div>
            </div>
          </fieldset>

          <!-- Section 2: Jumlah & alasan -->
          <fieldset class="rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6">
            <legend class="sr-only">Jumlah dan alasan adjustment</legend>
            <h2 class="text-lg font-semibold leading-[26px] text-[#17201C]">2. Jumlah dan alasan</h2>
            <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">
              Masukkan selisih stok, bukan jumlah stok akhir.
            </p>

            <div class="mt-4 space-y-5">
              <div>
                <label for="quantity" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Jumlah adjustment <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  <span class="sr-only">(wajib)</span>
                </label>

                <div class="flex items-center gap-3">
                  <div class="relative w-full max-w-[220px]">
                    <input
                      id="quantity"
                      v-model.number="quantity"
                      type="number"
                      step="1"
                      inputmode="numeric"
                      placeholder="Contoh: 10 atau -5"
                      :aria-invalid="!!quantityErrorText"
                      :aria-describedby="quantityErrorText ? 'quantity-error' : 'quantity-hint'"
                      class="h-10 w-full rounded-lg border bg-white px-3 text-right text-sm tabular-nums text-[#17201C] placeholder:text-[#6B756F] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
                      :class="quantityErrorText ? 'border-[#C0392B]' : 'border-[#D6DDD9] focus:border-[#176B4D]'"
                    />
                  </div>
                  <span v-if="unit" class="text-sm text-[#46514B]">{{ unit }}</span>

                  <span
                    v-if="directionBadge"
                    class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium"
                    :class="directionBadge.cls"
                  >
                    {{ directionBadge.label }} {{ fmtSigned(delta) }}
                  </span>
                </div>

                <p
                  v-if="quantityErrorText"
                  id="quantity-error"
                  role="alert"
                  class="mt-1.5 text-xs leading-4 text-[#C0392B]"
                >
                  {{ quantityErrorText }}
                </p>
                <p v-else id="quantity-hint" class="mt-1.5 text-xs leading-4 text-[#6B756F]">
                  Angka positif menambah stok, angka negatif mengurangi stok.
                </p>
              </div>

              <div>
                <label for="reason" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Alasan adjustment <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  <span class="sr-only">(wajib)</span>
                </label>
                <textarea
                  id="reason"
                  v-model="reason"
                  rows="4"
                  placeholder="Contoh: Barang rusak saat penataan rak, hasil hitung fisik berbeda dari sistem"
                  :aria-invalid="!!fieldErrors.reason"
                  :aria-describedby="fieldErrors.reason ? 'reason-error' : 'reason-hint'"
                  class="w-full resize-y rounded-lg border bg-white px-3 py-2.5 text-sm leading-5 text-[#17201C] placeholder:text-[#6B756F] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
                  :class="fieldErrors.reason ? 'border-[#C0392B]' : 'border-[#D6DDD9] focus:border-[#176B4D]'"
                />
                <div class="mt-1.5 flex items-start justify-between gap-3 text-xs leading-4">
                  <p
                    v-if="fieldErrors.reason"
                    id="reason-error"
                    role="alert"
                    class="text-[#C0392B]"
                  >
                    {{ fieldErrors.reason }}
                  </p>
                  <p v-else id="reason-hint" class="text-[#6B756F]">
                    Alasan tersimpan di riwayat dan dapat ditelusuri oleh pengurus.
                  </p>
                  <span class="shrink-0 tabular-nums text-[#6B756F]">{{ reason.trim().length }} karakter</span>
                </div>
              </div>
            </div>
          </fieldset>
        </div>

        <!-- Context / summary -->
        <aside class="space-y-6 lg:sticky lg:top-6 lg:self-start" aria-label="Ringkasan dampak adjustment">
          <div class="rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6">
            <h2 class="text-lg font-semibold leading-[26px] text-[#17201C]">Dampak terhadap stok</h2>

            <div v-if="selectedProduct" class="mt-3">
              <p class="text-sm font-medium leading-5 text-[#17201C]">{{ selectedProduct.name }}</p>
              <p class="text-[13px] leading-[18px] text-[#6B756F]">SKU {{ selectedProduct.sku }}</p>
            </div>
            <p v-else class="mt-3 text-sm leading-5 text-[#6B756F]">
              Pilih produk untuk melihat stok saat ini dan hasil adjustment.
            </p>

            <dl class="mt-4 divide-y divide-[#E6EBE8] rounded-lg border border-[#E6EBE8] bg-[#F8FAF9]">
              <div class="flex items-baseline justify-between gap-3 px-4 py-3">
                <dt class="text-[13px] leading-[18px] text-[#46514B]">Stok saat ini</dt>
                <dd class="text-base font-medium tabular-nums text-[#17201C]">
                  {{ fmt(stockBefore) }}
                  <span class="text-[13px] font-normal text-[#6B756F]">{{ unit }}</span>
                </dd>
              </div>

              <div class="flex items-baseline justify-between gap-3 px-4 py-3">
                <dt class="text-[13px] leading-[18px] text-[#46514B]">Perubahan</dt>
                <dd class="text-base font-medium tabular-nums text-[#17201C]">
                  {{ hasQuantity ? fmtSigned(delta) : '—' }}
                  <span v-if="hasQuantity" class="text-[13px] font-normal text-[#6B756F]">{{ unit }}</span>
                </dd>
              </div>

              <div class="flex items-baseline justify-between gap-3 bg-white px-4 py-3">
                <dt class="text-[13px] font-medium leading-[18px] text-[#17201C]">Stok setelah adjustment</dt>
                <dd
                  class="text-[22px] font-semibold leading-[30px] tabular-nums"
                  :class="isNegativeStock ? 'text-[#C0392B]' : 'text-[#17201C]'"
                >
                  {{ fmt(stockAfter) }}
                  <span class="text-[13px] font-normal text-[#6B756F]">{{ unit }}</span>
                </dd>
              </div>
            </dl>

            <div v-if="afterStatus" class="mt-3" role="status" aria-live="polite">
              <span
                class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium"
                :class="afterStatus.cls"
              >
                {{ afterStatus.label }}
              </span>
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
              Adjustment tidak dapat diedit atau dihapus setelah disimpan. Jika ada kesalahan,
              buat adjustment baru untuk mengoreksinya.
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
            Tinjau Adjustment
          </button>
        </div>
      </div>
    </form>

    <!-- Confirmation dialog -->
    <div
      v-if="showConfirmation"
      class="fixed inset-0 z-50 flex items-center justify-center bg-[#12372A]/50 p-4"
      @click.self="cancelConfirmation"
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
          Konfirmasi Stock Adjustment
        </h2>

        <p id="confirmation-desc" class="mt-1 text-sm leading-5 text-[#46514B]">
          Periksa dampak berikut. Adjustment yang sudah disimpan tidak dapat diubah.
        </p>

        <div class="mt-4">
          <p class="text-sm font-medium text-[#17201C]">{{ selectedProduct?.name }}</p>
          <p class="text-[13px] text-[#6B756F]">SKU {{ selectedProduct?.sku }}</p>
        </div>

        <dl class="mt-3 divide-y divide-[#E6EBE8] rounded-lg border border-[#E6EBE8] bg-[#F8FAF9] text-sm">
          <div class="flex items-baseline justify-between px-4 py-2.5">
            <dt class="text-[#46514B]">Stok saat ini</dt>
            <dd class="tabular-nums text-[#17201C]">{{ fmt(stockBefore) }} {{ unit }}</dd>
          </div>
          <div class="flex items-baseline justify-between px-4 py-2.5">
            <dt class="text-[#46514B]">Perubahan</dt>
            <dd class="font-medium tabular-nums text-[#17201C]">
              {{ fmtSigned(delta) }} {{ unit }}
              <span class="ml-1 text-xs font-normal text-[#6B756F]">
                ({{ delta > 0 ? 'penambahan' : 'pengurangan' }})
              </span>
            </dd>
          </div>
          <div class="flex items-baseline justify-between bg-white px-4 py-2.5">
            <dt class="font-medium text-[#17201C]">Stok setelah adjustment</dt>
            <dd class="text-base font-semibold tabular-nums text-[#17201C]">
              {{ fmt(stockAfter) }} {{ unit }}
            </dd>
          </div>
        </dl>

        <div class="mt-3 rounded-lg bg-[#F1F4F2] px-4 py-3 text-sm leading-5 text-[#46514B]">
          <p class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">Alasan</p>
          <p class="mt-0.5 whitespace-pre-line break-words text-[#17201C]">{{ reason.trim() }}</p>
        </div>

        <div class="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            ref="cancelButtonRef"
            type="button"
            :disabled="submitting"
            class="inline-flex h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
            @click="cancelConfirmation"
          >
            Batal
          </button>

          <button
            type="button"
            :disabled="submitting"
            :aria-busy="submitting"
            class="inline-flex h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
            @click="submitAdjustment"
          >
            {{ submitting ? 'Menyimpan…' : 'Simpan Adjustment' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>