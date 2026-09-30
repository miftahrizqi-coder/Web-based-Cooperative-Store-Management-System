<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
} from 'vue'

import { useAuth } from '../../stores/auth'

import {
  createSale,
  getPOSProductByBarcode,
  searchPOSMembers,
  searchPOSProducts,
} from '../../api/pos'

import type {
  CartItem,
  POSMember,
  POSProduct,
  PaymentMethod,
  SaleResponse,
} from '../../types/pos'

/**
 * Catatan token (DESIGN.md §3):
 * Warna ditulis sebagai arbitrary value Tailwind agar langsung bekerja
 * tanpa mengubah tailwind.config.
 *
 *  primary-900 #12372A | primary-700 #176B4D | primary-600 #1F805D
 *  primary-100 #DCEFE7 | primary-50 #F0F8F5
 *  neutral-950 #17201C | neutral-700 #46514B | neutral-500 #6B756F
 *  neutral-300 #D6DDD9 | neutral-200 #E6EBE8 | neutral-100 #F1F4F2 | neutral-50 #F8FAF9
 *  success #16834B | warning #B7791F (teks: #7A4F0F) | danger #C0392B (teks: #8E2A20)
 */

const { currentUser } = useAuth()

/** Batas stok "menipis" untuk StockIndicator. Sesuaikan dengan aturan minimum stok toko. */
const LOW_STOCK_THRESHOLD = 5

const paymentOptions: { value: PaymentMethod; label: string }[] = [
  { value: 'CASH' as PaymentMethod, label: 'Tunai' },
  { value: 'BANK_TRANSFER' as PaymentMethod, label: 'Transfer bank' },
  { value: 'DEBIT' as PaymentMethod, label: 'Debit' },
  { value: 'OTHER' as PaymentMethod, label: 'Lainnya' },
]

function paymentLabel(method: string): string {
  return (
    paymentOptions.find((option) => option.value === method)?.label ??
    method
  )
}

/* ------------------------------------------------------------------ */
/* State                                                               */
/* ------------------------------------------------------------------ */

const searchInput = ref('')
const barcodeInput = ref('')

const products = ref<POSProduct[]>([])
const members = ref<POSMember[]>([])
const cart = ref<CartItem[]>([])

const selectedMember = ref<POSMember | null>(null)
const memberSearch = ref('')

const loadingProducts = ref(false)
const loadingBarcode = ref(false)
const loadingMembers = ref(false)
const submittingSale = ref(false)

const productError = ref('')
const addError = ref('')
const barcodeError = ref('')
const memberError = ref('')
const checkoutError = ref('')

const showMemberPicker = ref(false)
const confirmingClear = ref(false)

const paymentMethod = ref<PaymentMethod>('CASH' as PaymentMethod)
const paidAmount = ref<number>(0)
const paymentOpen = ref(false)
const saleSuccess = ref<SaleResponse | null>(null)

const isOnline = ref(
  typeof navigator === 'undefined' ? true : navigator.onLine,
)

const announcement = ref('')
const highlightedProductId = ref<string | null>(null)

const searchRef = ref<HTMLInputElement | null>(null)
const barcodeRef = ref<HTMLInputElement | null>(null)
const dialogRef = ref<HTMLElement | null>(null)
const amountRef = ref<HTMLInputElement | null>(null)
const newSaleButtonRef = ref<HTMLButtonElement | null>(null)

let payTrigger: HTMLElement | null = null
let searchTimer: ReturnType<typeof setTimeout> | null = null
let memberSearchTimer: ReturnType<typeof setTimeout> | null = null
let announceTimer: ReturnType<typeof setTimeout> | null = null
let productRequestId = 0

const accessToken = computed(() =>
  localStorage.getItem('access_token'),
)

/* ------------------------------------------------------------------ */
/* Turunan                                                             */
/* ------------------------------------------------------------------ */

const cartTotal = computed(() =>
  cart.value.reduce(
    (total, item) =>
      total + item.product.selling_price * item.quantity,
    0,
  ),
)

const cartItemCount = computed(() =>
  cart.value.reduce((total, item) => total + item.quantity, 0),
)

const paymentShortfall = computed(() =>
  Math.max(cartTotal.value - paidAmount.value, 0),
)

const changeAmount = computed(() =>
  Math.max(paidAmount.value - cartTotal.value, 0),
)

const paymentValid = computed(
  () => cart.value.length > 0 && paidAmount.value >= cartTotal.value,
)

const paidAmountText = computed(() =>
  paidAmount.value > 0
    ? new Intl.NumberFormat('id-ID').format(paidAmount.value)
    : '',
)

const quickAmounts = computed(() => {
  const total = cartTotal.value
  const values = new Set<number>([total])

  for (const step of [10000, 50000, 100000]) {
    values.add(Math.ceil(total / step) * step)
  }

  return [...values]
    .filter((value) => value >= total && value > 0)
    .sort((a, b) => a - b)
    .slice(0, 4)
})

const soldUnits = computed(() =>
  saleSuccess.value
    ? saleSuccess.value.items.reduce(
        (total, item) => total + item.quantity,
        0,
      )
    : 0,
)

const canSubmit = computed(
  () => paymentValid.value && !submittingSale.value && isOnline.value,
)

/* ------------------------------------------------------------------ */
/* Helper                                                              */
/* ------------------------------------------------------------------ */

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatStock(product: POSProduct): string {
  return `${product.stock} ${product.unit}`
}

type StockState = 'in' | 'low' | 'out'

function stockState(product: POSProduct): StockState {
  if (product.stock <= 0) return 'out'
  if (product.stock <= LOW_STOCK_THRESHOLD) return 'low'
  return 'in'
}

function stockLabel(product: POSProduct): string {
  switch (stockState(product)) {
    case 'out':
      return 'Stok habis'
    case 'low':
      return `Stok menipis: ${formatStock(product)}`
    default:
      return `Stok: ${formatStock(product)}`
  }
}

function stockClass(product: POSProduct): string {
  switch (stockState(product)) {
    case 'out':
      return 'border-[#C0392B]/30 bg-[#FBEDEB] text-[#8E2A20]'
    case 'low':
      return 'border-[#B7791F]/30 bg-[#FBF3E2] text-[#7A4F0F]'
    default:
      return 'border-[#16834B]/25 bg-[#DCEFE7] text-[#12372A]'
  }
}

function quantityInCart(productId: string): number {
  return (
    cart.value.find((item) => item.product.id === productId)
      ?.quantity ?? 0
  )
}

function announce(message: string, productId?: string): void {
  announcement.value = message
  highlightedProductId.value = productId ?? null

  if (announceTimer) {
    clearTimeout(announceTimer)
  }

  announceTimer = setTimeout(() => {
    announcement.value = ''
    highlightedProductId.value = null
  }, 2500)
}

async function focusSearch(): Promise<void> {
  await nextTick()
  searchRef.value?.focus()
}

function printReceipt(): void {
  if (!saleSuccess.value) {
    return
  }

  window.print()
}

/* ------------------------------------------------------------------ */
/* Produk & barcode                                                    */
/* ------------------------------------------------------------------ */

async function loadProducts(): Promise<void> {
  const token = accessToken.value

  if (!token) {
    productError.value = 'Sesi login tidak ditemukan.'
    return
  }

  const requestId = ++productRequestId

  loadingProducts.value = true
  productError.value = ''

  try {
    const result = await searchPOSProducts(token, searchInput.value)

    // Abaikan respons lama yang tiba setelah pencarian yang lebih baru.
    if (requestId === productRequestId) {
      products.value = result
    }
  } catch (error) {
    if (requestId === productRequestId) {
      productError.value =
        error instanceof Error
          ? error.message
          : 'Gagal mengambil produk.'
    }
  } finally {
    if (requestId === productRequestId) {
      loadingProducts.value = false
    }
  }
}

function handleProductSearch(): void {
  addError.value = ''

  if (searchTimer) {
    clearTimeout(searchTimer)
  }

  searchTimer = setTimeout(() => {
    void loadProducts()
  }, 250)
}

async function lookupBarcode(rawCode?: string): Promise<void> {
  const fromSearch = typeof rawCode === 'string'
  const barcode = (fromSearch ? rawCode : barcodeInput.value).trim()

  if (!barcode) {
    barcodeError.value = 'Masukkan atau scan barcode terlebih dahulu.'
    return
  }

  const token = accessToken.value

  if (!token) {
    barcodeError.value = 'Sesi login tidak ditemukan.'
    return
  }

  loadingBarcode.value = true
  barcodeError.value = ''
  addError.value = ''

  try {
    const product = await getPOSProductByBarcode(token, barcode)

    addToCart(product)

    barcodeInput.value = ''

    if (fromSearch) {
      if (searchTimer) {
        clearTimeout(searchTimer)
      }

      searchInput.value = ''
      void loadProducts()
    }

    await focusSearch()
  } catch (error) {
    barcodeError.value =
      error instanceof Error
        ? error.message
        : 'Produk dengan barcode ini tidak ditemukan.'
  } finally {
    loadingBarcode.value = false
  }
}

function handleSearchKeydown(event: KeyboardEvent): void {
  if (event.key !== 'Enter') {
    return
  }

  event.preventDefault()

  const value = searchInput.value.trim()

  // Scanner barcode berperilaku seperti keyboard: angka panjang + Enter.
  if (/^\d{8,}$/.test(value)) {
    void lookupBarcode(value)
    return
  }

  if (products.value.length === 1) {
    addToCart(products.value[0])
  }
}

function handleBarcodeKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter') {
    event.preventDefault()
    void lookupBarcode()
  }
}

/* ------------------------------------------------------------------ */
/* Keranjang                                                           */
/* ------------------------------------------------------------------ */

function addToCart(product: POSProduct): void {
  addError.value = ''

  if (!product.is_active) {
    addError.value = `${product.name} tidak aktif dan tidak dapat dijual.`
    return
  }

  if (product.stock <= 0) {
    addError.value = `Stok ${product.name} habis.`
    return
  }

  const existing = cart.value.find(
    (item) => item.product.id === product.id,
  )

  if (existing) {
    if (existing.quantity >= product.stock) {
      addError.value = `Jumlah ${product.name} tidak boleh melebihi stok (${formatStock(product)}).`
      return
    }

    existing.quantity += 1
    announce(
      `${product.name} ditambahkan. Jumlah di keranjang: ${existing.quantity}.`,
      product.id,
    )
    return
  }

  cart.value.push({ product, quantity: 1 })
  announce(
    `${product.name} ditambahkan ke keranjang. Jumlah: 1.`,
    product.id,
  )
}

function increaseQuantity(item: CartItem): void {
  if (item.quantity >= item.product.stock) {
    return
  }

  item.quantity += 1
}

function decreaseQuantity(item: CartItem): void {
  if (item.quantity <= 1) {
    removeFromCart(item.product.id)
    return
  }

  item.quantity -= 1
}

function removeFromCart(productId: string): void {
  const removed = cart.value.find(
    (item) => item.product.id === productId,
  )

  cart.value = cart.value.filter(
    (item) => item.product.id !== productId,
  )

  if (removed) {
    announce(`${removed.product.name} dihapus dari keranjang.`)
  }
}

function clearCart(): void {
  cart.value = []
  selectedMember.value = null
  showMemberPicker.value = false
  confirmingClear.value = false
  addError.value = ''
  announce('Keranjang dikosongkan.')
  resetPayment()
  void focusSearch()
}

/* ------------------------------------------------------------------ */
/* Anggota                                                             */
/* ------------------------------------------------------------------ */

async function loadMembers(): Promise<void> {
  const token = accessToken.value

  if (!token) {
    memberError.value = 'Sesi login tidak ditemukan.'
    return
  }

  loadingMembers.value = true
  memberError.value = ''

  try {
    members.value = await searchPOSMembers(token, memberSearch.value)
  } catch (error) {
    memberError.value =
      error instanceof Error
        ? error.message
        : 'Gagal mencari anggota.'
  } finally {
    loadingMembers.value = false
  }
}

function handleMemberSearch(): void {
  if (memberSearchTimer) {
    clearTimeout(memberSearchTimer)
  }

  memberSearchTimer = setTimeout(() => {
    void loadMembers()
  }, 250)
}

function selectMember(member: POSMember): void {
  if (member.status !== 'ACTIVE') {
    return
  }

  selectedMember.value = member
  showMemberPicker.value = false
  memberSearch.value = ''
  members.value = []
  announce(`Anggota ${member.name} dipilih.`)
}

function removeMember(): void {
  selectedMember.value = null
}

/* ------------------------------------------------------------------ */
/* Pembayaran                                                          */
/* ------------------------------------------------------------------ */

function resetPayment(): void {
  paymentMethod.value = 'CASH' as PaymentMethod
  paidAmount.value = 0
  checkoutError.value = ''
  saleSuccess.value = null
  paymentOpen.value = false
}

async function openPayment(): Promise<void> {
  if (cart.value.length === 0) {
    return
  }

  payTrigger = document.activeElement as HTMLElement | null

  checkoutError.value = ''
  paymentMethod.value = 'CASH' as PaymentMethod
  paidAmount.value = 0
  paymentOpen.value = true

  await nextTick()
  amountRef.value?.focus()
}

async function closePayment(): Promise<void> {
  // Selama diproses atau setelah sukses, dialog tidak boleh ditutup sembarangan.
  if (submittingSale.value || saleSuccess.value) {
    return
  }

  paymentOpen.value = false
  await nextTick()

  if (payTrigger && document.contains(payTrigger)) {
    payTrigger.focus()
  } else {
    void focusSearch()
  }

  payTrigger = null
}

function selectPaymentMethod(method: PaymentMethod): void {
  paymentMethod.value = method
  checkoutError.value = ''

  // Non-tunai dibayar pas; tunai diisi kasir.
  paidAmount.value = method === ('CASH' as PaymentMethod) ? 0 : cartTotal.value
}

function handlePaidAmountInput(event: Event): void {
  const target = event.target as HTMLInputElement
  const digits = target.value.replace(/\D/g, '')

  paidAmount.value = digits ? Number(digits) : 0
  target.value = paidAmountText.value
}

async function submitSale(): Promise<void> {
  if (submittingSale.value || saleSuccess.value) {
    return
  }

  checkoutError.value = ''

  if (cart.value.length === 0) {
    checkoutError.value = 'Keranjang masih kosong.'
    return
  }

  if (paidAmount.value < cartTotal.value) {
    checkoutError.value = 'Nominal pembayaran masih kurang.'
    return
  }

  if (!isOnline.value) {
    checkoutError.value =
      'Koneksi terputus. Jangan tutup halaman. Periksa koneksi sebelum mengulangi transaksi.'
    return
  }

  const token = accessToken.value

  if (!token) {
    checkoutError.value = 'Sesi login tidak ditemukan.'
    return
  }

  submittingSale.value = true

  try {
    const sale = await createSale(token, {
      items: cart.value.map((item) => ({
        productId: item.product.id,
        quantity: item.quantity,
      })),
      memberId: selectedMember.value?.id ?? null,
      paymentMethod: paymentMethod.value,
      paidAmount: paidAmount.value,
    })

    saleSuccess.value = sale

    for (const item of cart.value) {
      item.product.stock = Math.max(
        item.product.stock - item.quantity,
        0,
      )
    }

    await nextTick()
    newSaleButtonRef.value?.focus()
  } catch (error) {
    const reason =
      error instanceof Error
        ? error.message
        : 'Transaksi gagal diproses.'

    checkoutError.value = `${reason} Keranjang Anda tidak dihapus. Bila ragu, periksa Riwayat Penjualan sebelum mengulangi agar transaksi tidak tercatat ganda.`
  } finally {
    submittingSale.value = false
  }
}

function startNewSale(): void {
  cart.value = []
  selectedMember.value = null
  memberSearch.value = ''
  members.value = []
  showMemberPicker.value = false
  confirmingClear.value = false

  searchInput.value = ''
  barcodeInput.value = ''

  productError.value = ''
  addError.value = ''
  barcodeError.value = ''
  memberError.value = ''

  resetPayment()

  void loadProducts()
  void focusSearch()
}

/* ------------------------------------------------------------------ */
/* Keyboard, fokus, koneksi                                            */
/* ------------------------------------------------------------------ */

function onDialogKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.stopPropagation()
    void closePayment()
    return
  }

  if (event.key !== 'Tab' || !dialogRef.value) {
    return
  }

  const focusable = dialogRef.value.querySelectorAll<HTMLElement>(
    'button:not([disabled]), [href], input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])',
  )

  if (focusable.length === 0) {
    return
  }

  const first = focusable[0]
  const last = focusable[focusable.length - 1]

  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

function onGlobalKeydown(event: KeyboardEvent): void {
  if (event.key !== '/' || paymentOpen.value) {
    return
  }

  const target = event.target as HTMLElement | null
  const tag = target?.tagName

  if (
    tag === 'INPUT' ||
    tag === 'TEXTAREA' ||
    tag === 'SELECT' ||
    target?.isContentEditable
  ) {
    return
  }

  event.preventDefault()
  searchRef.value?.focus()
}

function setOnline(): void {
  isOnline.value = true
}

function setOffline(): void {
  isOnline.value = false
}

function scrollToCart(): void {
  document
    .getElementById('cart-panel')
    ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(async () => {
  window.addEventListener('keydown', onGlobalKeydown)
  window.addEventListener('online', setOnline)
  window.addEventListener('offline', setOffline)

  await loadProducts()
  await focusSearch()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKeydown)
  window.removeEventListener('online', setOnline)
  window.removeEventListener('offline', setOffline)

  if (searchTimer) clearTimeout(searchTimer)
  if (memberSearchTimer) clearTimeout(memberSearchTimer)
  if (announceTimer) clearTimeout(announceTimer)
})
</script>

<template>
  <div class="mx-auto max-w-[1440px] space-y-4 pb-24 text-[#17201C] lg:pb-0">
    <!-- Header -->
    <header class="flex flex-wrap items-end justify-between gap-2">
      <div>
        <h1 class="text-[28px] font-semibold leading-9">
          Point of Sale
        </h1>

        <p class="text-sm text-[#46514B]">
          Kasir:
          <span class="font-medium text-[#17201C]">
            {{ currentUser?.name || currentUser?.username || '-' }}
          </span>
        </p>
      </div>

      <p class="hidden text-[13px] text-[#6B756F] sm:block">
        Tekan
        <kbd class="rounded border border-[#D6DDD9] bg-[#F1F4F2] px-1.5 py-0.5 text-xs font-medium text-[#46514B]">/</kbd>
        untuk mencari produk
      </p>
    </header>

    <!-- Koneksi terputus -->
    <div
      v-if="!isOnline"
      role="alert"
      class="rounded-lg border border-[#C0392B]/30 bg-[#FBEDEB] px-4 py-3 text-sm text-[#8E2A20]"
    >
      <strong class="font-semibold">Koneksi terputus.</strong>
      Jangan tutup halaman. Periksa koneksi sebelum mengulangi transaksi.
      Tombol bayar dinonaktifkan sampai koneksi kembali.
    </div>

    <!-- Search / Scan -->
    <section
      class="rounded-lg border border-[#D6DDD9] bg-white p-4"
      aria-label="Cari atau scan produk"
    >
      <div class="grid gap-3 md:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div>
          <label
            for="product-search"
            class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]"
          >
            Cari produk (nama atau SKU)
          </label>

          <input
            id="product-search"
            ref="searchRef"
            v-model="searchInput"
            type="search"
            autocomplete="off"
            placeholder="Ketik nama atau SKU, atau scan barcode di sini"
            class="focus-ring min-h-11 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-base text-[#17201C] placeholder:text-[#6B756F] outline-none focus:border-[#176B4D]"
            @input="handleProductSearch"
            @keydown="handleSearchKeydown"
          />
        </div>

        <div>
          <label
            for="barcode-search"
            class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]"
          >
            Scan barcode
          </label>

          <div class="flex gap-2">
            <input
              id="barcode-search"
              ref="barcodeRef"
              v-model="barcodeInput"
              type="text"
              inputmode="numeric"
              autocomplete="off"
              placeholder="Scan atau ketik barcode"
              class="focus-ring min-h-11 min-w-0 flex-1 rounded-lg border border-[#D6DDD9] bg-white px-3 text-base tabular-nums text-[#17201C] placeholder:text-[#6B756F] outline-none focus:border-[#176B4D]"
              @keydown="handleBarcodeKeydown"
            />

            <button
              type="button"
              class="focus-ring min-h-11 rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-semibold text-[#17201C] hover:bg-[#F1F4F2] disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="loadingBarcode"
              @click="lookupBarcode()"
            >
              {{ loadingBarcode ? 'Mencari...' : 'Cari' }}
            </button>
          </div>
        </div>
      </div>

      <p
        v-if="barcodeError"
        role="alert"
        class="mt-3 rounded-lg border border-[#C0392B]/30 bg-[#FBEDEB] px-3 py-2 text-sm text-[#8E2A20]"
      >
        {{ barcodeError }}
      </p>

      <p
        v-if="addError"
        role="alert"
        class="mt-3 rounded-lg border border-[#B7791F]/30 bg-[#FBF3E2] px-3 py-2 text-sm text-[#7A4F0F]"
      >
        {{ addError }}
      </p>

      <!-- Umpan balik penambahan produk (visual + screen reader) -->
      <p
        role="status"
        aria-live="polite"
        class="mt-3 min-h-5 text-[13px] font-medium text-[#176B4D]"
      >
        {{ announcement }}
      </p>
    </section>

    <div class="grid gap-4 lg:grid-cols-[55fr_45fr] lg:items-start">
      <!-- Product workspace (±55%) -->
      <section
        aria-labelledby="product-section-title"
        class="rounded-lg border border-[#D6DDD9] bg-white p-4"
      >
        <div class="mb-4 flex items-baseline justify-between gap-3">
          <h2
            id="product-section-title"
            class="text-lg font-semibold leading-[26px]"
          >
            Produk
          </h2>

          <p
            v-if="!loadingProducts && !productError && products.length"
            class="text-[13px] tabular-nums text-[#6B756F]"
          >
            {{ products.length }} hasil
          </p>
        </div>

        <!-- Loading -->
        <div
          v-if="loadingProducts"
          class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3"
          role="status"
          aria-busy="true"
        >
          <span class="sr-only">Memuat produk...</span>
          <div
            v-for="index in 6"
            :key="index"
            class="h-28 animate-pulse rounded-lg bg-[#F1F4F2]"
          />
        </div>

        <!-- Error -->
        <div
          v-else-if="productError"
          role="alert"
          class="rounded-lg border border-[#C0392B]/30 bg-[#FBEDEB] p-5"
        >
          <p class="font-semibold text-[#8E2A20]">
            Produk tidak dapat dimuat
          </p>
          <p class="mt-1 text-sm text-[#8E2A20]">
            {{ productError }}
          </p>
          <p class="mt-1 text-sm text-[#46514B]">
            Keranjang tidak terpengaruh. Coba muat ulang daftar produk.
          </p>
          <button
            type="button"
            class="focus-ring mt-3 min-h-11 rounded-lg border border-[#C0392B]/40 bg-white px-4 text-sm font-semibold text-[#8E2A20] hover:bg-[#FBEDEB]"
            @click="loadProducts"
          >
            Coba lagi
          </button>
        </div>

        <!-- Empty -->
        <div
          v-else-if="products.length === 0"
          class="rounded-lg border border-dashed border-[#D6DDD9] px-6 py-10 text-center"
        >
          <template v-if="searchInput.trim()">
            <p class="font-semibold">
              Tidak ada produk untuk "{{ searchInput.trim() }}"
            </p>
            <p class="mx-auto mt-1 max-w-sm text-sm text-[#46514B]">
              Periksa ejaan, coba nama atau SKU lain, atau scan barcode
              produk.
            </p>
          </template>

          <template v-else>
            <p class="font-semibold">
              Belum ada produk yang bisa dijual
            </p>
            <p class="mx-auto mt-1 max-w-sm text-sm text-[#46514B]">
              Daftar produk kosong. Hubungi Admin untuk menambahkan
              produk ke katalog.
            </p>
          </template>
        </div>

        <!-- Hasil -->
        <ul
          v-else
          class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3"
        >
          <li
            v-for="product in products"
            :key="product.id"
          >
            <button
              type="button"
              class="focus-ring flex h-full w-full flex-col justify-between rounded-lg border p-3 text-left transition-colors disabled:cursor-not-allowed"
              :class="
                !product.is_active || product.stock <= 0
                  ? 'border-[#E6EBE8] bg-[#F8FAF9] opacity-75'
                  : highlightedProductId === product.id
                    ? 'border-[#176B4D] bg-[#F0F8F5]'
                    : 'border-[#D6DDD9] bg-white hover:border-[#176B4D] hover:bg-[#F0F8F5]'
              "
              :disabled="!product.is_active || product.stock <= 0"
              :aria-label="`Tambah ${product.name} ke keranjang, ${formatCurrency(product.selling_price)}, ${stockLabel(product)}`"
              @click="addToCart(product)"
            >
              <div>
                <p class="text-sm font-semibold leading-5 text-[#17201C]">
                  {{ product.name }}
                </p>

                <p class="mt-0.5 text-[13px] leading-[18px] tabular-nums text-[#6B756F]">
                  {{ product.sku }}
                </p>

                <p
                  v-if="product.barcode"
                  class="text-[13px] leading-[18px] tabular-nums text-[#6B756F]"
                >
                  {{ product.barcode }}
                </p>
              </div>

              <div class="mt-3">
                <p class="text-base font-semibold tabular-nums">
                  {{ formatCurrency(product.selling_price) }}
                </p>

                <div class="mt-2 flex flex-wrap items-center gap-1.5">
                  <span
                    class="inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium tabular-nums"
                    :class="stockClass(product)"
                  >
                    <svg class="h-2.5 w-2.5" viewBox="0 0 10 10" aria-hidden="true">
                      <circle
                        v-if="stockState(product) === 'in'"
                        cx="5" cy="5" r="4" fill="currentColor"
                      />
                      <path
                        v-else-if="stockState(product) === 'low'"
                        d="M5 1 9.5 9h-9z"
                        fill="currentColor"
                      />
                      <path
                        v-else
                        d="M2 2l6 6M8 2 2 8"
                        stroke="currentColor"
                        stroke-width="1.75"
                        stroke-linecap="round"
                      />
                    </svg>
                    {{ stockLabel(product) }}
                  </span>

                  <span
                    v-if="!product.is_active"
                    class="rounded-full border border-[#D6DDD9] bg-[#F1F4F2] px-2 py-0.5 text-xs font-medium text-[#46514B]"
                  >
                    Produk nonaktif
                  </span>

                  <span
                    v-if="quantityInCart(product.id) > 0"
                    class="rounded-full border border-[#176B4D]/30 bg-[#DCEFE7] px-2 py-0.5 text-xs font-medium tabular-nums text-[#12372A]"
                  >
                    Di keranjang: {{ quantityInCart(product.id) }}
                  </span>
                </div>
              </div>
            </button>
          </li>
        </ul>
      </section>

      <!-- Cart (±45%, dominan & persisten) -->
      <section
        id="cart-panel"
        aria-labelledby="cart-section-title"
        class="flex flex-col overflow-hidden rounded-lg border-2 border-[#176B4D]/40 bg-white lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)]"
      >
        <div class="flex items-center justify-between gap-3 border-b border-[#E6EBE8] bg-[#F0F8F5] px-4 py-3">
          <div>
            <h2
              id="cart-section-title"
              class="text-lg font-semibold leading-[26px] text-[#12372A]"
            >
              Keranjang
            </h2>

            <p class="text-[13px] tabular-nums text-[#46514B]">
              {{ cartItemCount }} item
            </p>
          </div>

          <div v-if="cart.length">
            <button
              v-if="!confirmingClear"
              type="button"
              class="focus-ring min-h-11 rounded-lg px-3 text-sm font-medium text-[#C0392B] hover:bg-[#FBEDEB]"
              @click="confirmingClear = true"
            >
              Kosongkan
            </button>

            <div
              v-else
              class="flex items-center gap-1"
              role="group"
              aria-label="Konfirmasi kosongkan keranjang"
            >
              <span class="hidden text-[13px] text-[#46514B] sm:inline">
                Hapus semua item?
              </span>

              <button
                type="button"
                class="focus-ring min-h-11 rounded-lg bg-[#C0392B] px-3 text-sm font-semibold text-white hover:bg-[#A93226]"
                @click="clearCart"
              >
                Ya, kosongkan
              </button>

              <button
                type="button"
                class="focus-ring min-h-11 rounded-lg px-3 text-sm font-medium text-[#46514B] hover:bg-[#F1F4F2]"
                @click="confirmingClear = false"
              >
                Batal
              </button>
            </div>
          </div>
        </div>

        <!-- Isi keranjang + anggota (area scroll) -->
        <div class="min-h-0 flex-1 overflow-y-auto">
          <div
            v-if="cart.length === 0"
            class="px-6 py-10 text-center"
          >
            <p class="font-semibold">
              Keranjang masih kosong
            </p>
            <p class="mx-auto mt-1 max-w-xs text-sm text-[#46514B]">
              Cari atau scan produk untuk memulai transaksi. Produk yang
              ditambahkan akan muncul di sini.
            </p>
          </div>

          <ul
            v-else
            class="divide-y divide-[#E6EBE8]"
          >
            <li
              v-for="item in cart"
              :key="item.product.id"
              class="px-4 py-3 transition-colors"
              :class="
                highlightedProductId === item.product.id
                  ? 'bg-[#F0F8F5]'
                  : ''
              "
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="text-sm font-semibold leading-5">
                    {{ item.product.name }}
                  </p>

                  <p class="text-[13px] tabular-nums text-[#6B756F]">
                    {{ formatCurrency(item.product.selling_price) }}
                    / {{ item.product.unit }}
                  </p>
                </div>

                <button
                  type="button"
                  class="focus-ring min-h-11 rounded-lg px-2 text-[13px] font-medium text-[#C0392B] hover:bg-[#FBEDEB]"
                  :aria-label="`Hapus ${item.product.name} dari keranjang`"
                  @click="removeFromCart(item.product.id)"
                >
                  Hapus
                </button>
              </div>

              <div class="mt-1 flex items-center justify-between gap-3">
                <div
                  class="flex items-center rounded-lg border border-[#D6DDD9]"
                  role="group"
                  :aria-label="`Jumlah ${item.product.name}`"
                >
                  <button
                    type="button"
                    class="focus-ring min-h-11 min-w-11 rounded-l-lg text-lg text-[#17201C] hover:bg-[#F1F4F2]"
                    :aria-label="`Kurangi ${item.product.name}`"
                    @click="decreaseQuantity(item)"
                  >
                    −
                  </button>

                  <span
                    class="min-w-10 text-center text-sm font-semibold tabular-nums"
                    aria-live="polite"
                  >
                    {{ item.quantity }}
                  </span>

                  <button
                    type="button"
                    class="focus-ring min-h-11 min-w-11 rounded-r-lg text-lg text-[#17201C] hover:bg-[#F1F4F2] disabled:cursor-not-allowed disabled:opacity-40"
                    :aria-label="`Tambah ${item.product.name}`"
                    :disabled="item.quantity >= item.product.stock"
                    @click="increaseQuantity(item)"
                  >
                    +
                  </button>
                </div>

                <p class="text-right text-base font-semibold tabular-nums">
                  {{ formatCurrency(item.product.selling_price * item.quantity) }}
                </p>
              </div>

              <p
                class="mt-1.5 text-xs tabular-nums"
                :class="
                  item.quantity >= item.product.stock
                    ? 'font-medium text-[#7A4F0F]'
                    : 'text-[#6B756F]'
                "
              >
                <template v-if="item.quantity >= item.product.stock">
                  Stok maksimal tercapai ({{ formatStock(item.product) }})
                </template>
                <template v-else>
                  Stok tersedia: {{ formatStock(item.product) }}
                </template>
              </p>
            </li>
          </ul>

          <!-- Anggota -->
          <div class="border-t border-[#E6EBE8] px-4 py-4">
            <div class="flex items-center justify-between gap-3">
              <div class="min-w-0">
                <h3 class="text-sm font-semibold">
                  Anggota
                  <span class="font-normal text-[#6B756F]">(opsional)</span>
                </h3>

                <p
                  v-if="selectedMember"
                  class="mt-0.5 truncate text-[13px] text-[#46514B]"
                >
                  <span class="font-medium text-[#17201C]">{{ selectedMember.name }}</span>
                  <span class="tabular-nums"> — {{ selectedMember.memberNumber }}</span>
                </p>

                <p
                  v-else
                  class="mt-0.5 text-[13px] text-[#6B756F]"
                >
                  Belum dipilih
                </p>
              </div>

              <div class="flex shrink-0 items-center gap-1">
                <button
                  v-if="selectedMember"
                  type="button"
                  class="focus-ring min-h-11 rounded-lg px-3 text-[13px] font-medium text-[#C0392B] hover:bg-[#FBEDEB]"
                  @click="removeMember"
                >
                  Hapus
                </button>

                <button
                  type="button"
                  class="focus-ring min-h-11 rounded-lg border border-[#D6DDD9] bg-white px-3 text-[13px] font-medium hover:bg-[#F1F4F2]"
                  :aria-expanded="showMemberPicker"
                  aria-controls="member-picker"
                  @click="showMemberPicker = !showMemberPicker"
                >
                  {{ selectedMember ? 'Ganti' : 'Pilih anggota' }}
                </button>
              </div>
            </div>

            <div
              v-if="showMemberPicker"
              id="member-picker"
              class="mt-3 rounded-lg border border-[#E6EBE8] bg-[#F8FAF9] p-3"
            >
              <label
                for="member-search"
                class="mb-1.5 block text-xs font-medium text-[#46514B]"
              >
                Cari anggota
              </label>

              <input
                id="member-search"
                v-model="memberSearch"
                type="search"
                autocomplete="off"
                placeholder="Nomor anggota, nama, atau telepon"
                class="focus-ring min-h-11 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-base placeholder:text-[#6B756F] outline-none focus:border-[#176B4D]"
                @input="handleMemberSearch"
              />

              <p
                v-if="memberError"
                role="alert"
                class="mt-2 text-sm text-[#8E2A20]"
              >
                {{ memberError }}
              </p>

              <p
                v-if="loadingMembers"
                class="mt-3 text-sm text-[#46514B]"
                role="status"
              >
                Mencari anggota...
              </p>

              <ul
                v-else-if="members.length"
                class="mt-3 space-y-2"
              >
                <li
                  v-for="member in members"
                  :key="member.id"
                >
                  <button
                    type="button"
                    class="focus-ring flex min-h-11 w-full items-center justify-between gap-3 rounded-lg border border-[#D6DDD9] bg-white p-3 text-left hover:bg-[#F0F8F5] disabled:cursor-not-allowed disabled:bg-[#F1F4F2] disabled:opacity-70"
                    :disabled="member.status !== 'ACTIVE'"
                    @click="selectMember(member)"
                  >
                    <span class="min-w-0">
                      <span class="block truncate text-sm font-medium">
                        {{ member.name }}
                      </span>
                      <span class="block text-xs tabular-nums text-[#6B756F]">
                        {{ member.memberNumber }} — {{ member.phone }}
                      </span>
                    </span>

                    <span
                      v-if="member.status !== 'ACTIVE'"
                      class="shrink-0 rounded-full border border-[#D6DDD9] bg-[#F1F4F2] px-2 py-0.5 text-xs font-medium text-[#46514B]"
                    >
                      Nonaktif
                    </span>
                  </button>
                </li>
              </ul>

              <p
                v-else-if="memberSearch.trim()"
                class="mt-3 text-sm text-[#46514B]"
              >
                Anggota tidak ditemukan. Periksa nomor atau ejaan nama.
              </p>
            </div>
          </div>
        </div>

        <!-- Total + aksi utama -->
        <div class="border-t-2 border-[#176B4D]/30 bg-[#F0F8F5] px-4 py-4">
          <div class="flex items-end justify-between gap-3">
            <span class="text-sm font-medium text-[#46514B]">
              Total
            </span>

            <span class="text-[28px] font-bold leading-[34px] tabular-nums text-[#12372A]">
              {{ formatCurrency(cartTotal) }}
            </span>
          </div>

          <button
            type="button"
            class="focus-ring mt-3 min-h-14 w-full rounded-lg bg-[#176B4D] px-4 py-3 text-base font-semibold text-white transition-colors hover:bg-[#1F805D] disabled:cursor-not-allowed disabled:bg-[#9AA8A1]"
            :disabled="cart.length === 0"
            @click="openPayment"
          >
            Bayar
          </button>

          <p
            v-if="cart.length === 0"
            class="mt-2 text-center text-xs text-[#6B756F]"
          >
            Tambahkan produk untuk melanjutkan ke pembayaran.
          </p>
        </div>
      </section>
    </div>

    <!-- Bar bawah (mobile): Total & Payment paling utama -->
    <div
      class="fixed inset-x-0 bottom-0 z-30 flex items-center gap-3 border-t border-[#D6DDD9] bg-white px-4 py-3 shadow-[0_-4px_12px_rgba(18,55,42,.08)] lg:hidden"
    >
      <button
        type="button"
        class="focus-ring min-h-11 min-w-0 flex-1 rounded-lg text-left"
        :aria-label="`Lihat keranjang, ${cartItemCount} item, total ${formatCurrency(cartTotal)}`"
        @click="scrollToCart"
      >
        <span class="block text-xs text-[#46514B] tabular-nums">
          {{ cartItemCount }} item
        </span>
        <span class="block truncate text-lg font-bold leading-6 tabular-nums text-[#12372A]">
          {{ formatCurrency(cartTotal) }}
        </span>
      </button>

      <button
        type="button"
        class="focus-ring min-h-12 rounded-lg bg-[#176B4D] px-6 text-base font-semibold text-white hover:bg-[#1F805D] disabled:cursor-not-allowed disabled:bg-[#9AA8A1]"
        :disabled="cart.length === 0"
        @click="openPayment"
      >
        Bayar
      </button>
    </div>

    <!-- Payment modal -->
    <div
      v-if="paymentOpen"
      class="fixed inset-0 z-50 flex items-end justify-center bg-[#17201C]/50 sm:items-center sm:p-4"
      @click.self="closePayment"
    >
      <div
        ref="dialogRef"
        role="dialog"
        aria-modal="true"
        aria-labelledby="payment-dialog-title"
        class="max-h-[95vh] w-full max-w-md overflow-y-auto rounded-t-xl bg-white p-6 shadow-[0_12px_32px_rgba(18,55,42,.12)] sm:rounded-xl"
        @keydown="onDialogKeydown"
      >
        <!-- Sukses -->
        <template v-if="saleSuccess">
          <div
            role="status"
            aria-live="polite"
          >
            <div class="flex items-start gap-3">
              <div
                class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#DCEFE7] text-[#16834B]"
                aria-hidden="true"
              >
                <svg class="h-5 w-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m4.5 10.5 3.5 3.5 7.5-8" />
                </svg>
              </div>

              <div>
                <h2
                  id="payment-dialog-title"
                  class="text-lg font-semibold leading-[26px]"
                >
                  Transaksi berhasil
                </h2>

                <p class="text-sm text-[#46514B]">
                  Transaksi
                  <strong class="tabular-nums text-[#17201C]">{{ saleSuccess.saleNumber }}</strong>
                  tersimpan. Stok berkurang
                  <strong class="tabular-nums text-[#17201C]">{{ soldUnits }}</strong>
                  unit dari
                  <strong class="tabular-nums text-[#17201C]">{{ saleSuccess.items.length }}</strong>
                  produk.
                </p>
              </div>
            </div>

            <dl class="mt-5 space-y-2 rounded-lg border border-[#E6EBE8] bg-[#F8FAF9] p-4 text-sm">
              <div class="flex justify-between gap-4">
                <dt class="text-[#46514B]">Total</dt>
                <dd class="font-semibold tabular-nums">{{ formatCurrency(saleSuccess.total) }}</dd>
              </div>
              <div class="flex justify-between gap-4">
                <dt class="text-[#46514B]">Metode</dt>
                <dd>{{ paymentLabel(saleSuccess.paymentMethod) }}</dd>
              </div>
              <div class="flex justify-between gap-4">
                <dt class="text-[#46514B]">Dibayar</dt>
                <dd class="tabular-nums">{{ formatCurrency(saleSuccess.paidAmount) }}</dd>
              </div>
              <div class="flex justify-between gap-4 border-t border-[#E6EBE8] pt-2 text-base">
                <dt class="font-medium">Kembalian</dt>
                <dd class="font-bold tabular-nums text-[#12372A]">{{ formatCurrency(saleSuccess.changeAmount) }}</dd>
              </div>
            </dl>
          </div>

          <div class="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <button
              type="button"
              class="focus-ring min-h-12 rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-semibold hover:bg-[#F1F4F2]"
              @click="printReceipt"
            >
              Cetak struk
            </button>

            <button
              ref="newSaleButtonRef"
              type="button"
              class="focus-ring min-h-12 rounded-lg bg-[#176B4D] px-5 text-sm font-semibold text-white hover:bg-[#1F805D]"
              @click="startNewSale"
            >
              Transaksi baru
            </button>
          </div>
        </template>

        <!-- Pembayaran -->
        <template v-else>
          <h2
            id="payment-dialog-title"
            class="text-lg font-semibold leading-[26px]"
          >
            Pembayaran
          </h2>

          <p class="mt-1 text-sm text-[#46514B]">
            {{ cartItemCount }} item
            <template v-if="selectedMember">
              untuk anggota
              <span class="font-medium text-[#17201C]">{{ selectedMember.name }}</span>
            </template>
          </p>

          <div class="mt-4 rounded-lg bg-[#F0F8F5] p-4">
            <p class="text-xs font-medium text-[#46514B]">
              Total transaksi
            </p>
            <p class="text-[28px] font-bold leading-[34px] tabular-nums text-[#12372A]">
              {{ formatCurrency(cartTotal) }}
            </p>
          </div>

          <!-- PaymentMethodSelector -->
          <fieldset class="mt-5">
            <legend class="mb-2 text-xs font-medium text-[#46514B]">
              Metode pembayaran
            </legend>

            <div class="grid grid-cols-2 gap-2">
              <div
                v-for="option in paymentOptions"
                :key="option.value"
                class="relative"
              >
                <input
                  :id="`pay-${option.value}`"
                  class="peer sr-only"
                  type="radio"
                  name="payment-method"
                  :value="option.value"
                  :checked="paymentMethod === option.value"
                  @change="selectPaymentMethod(option.value)"
                />

                <label
                  :for="`pay-${option.value}`"
                  class="flex min-h-11 cursor-pointer items-center justify-center rounded-lg border px-3 text-sm font-medium transition-colors peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-[#176B4D]"
                  :class="
                    paymentMethod === option.value
                      ? 'border-[#176B4D] bg-[#DCEFE7] text-[#12372A]'
                      : 'border-[#D6DDD9] bg-white text-[#46514B] hover:bg-[#F1F4F2]'
                  "
                >
                  {{ option.label }}
                </label>
              </div>
            </div>
          </fieldset>

          <!-- MoneyInput -->
          <div class="mt-5">
            <label
              for="paid-amount"
              class="mb-1.5 block text-xs font-medium text-[#46514B]"
            >
              Nominal dibayar
            </label>

            <div class="relative">
              <span
                class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-base text-[#6B756F]"
                aria-hidden="true"
              >
                Rp
              </span>

              <input
                id="paid-amount"
                ref="amountRef"
                type="text"
                inputmode="numeric"
                autocomplete="off"
                :value="paidAmountText"
                placeholder="0"
                class="focus-ring min-h-12 w-full rounded-lg border border-[#D6DDD9] bg-white pl-10 pr-3 text-right text-lg font-semibold tabular-nums outline-none focus:border-[#176B4D]"
                :aria-invalid="paymentShortfall > 0 && paidAmount > 0"
                aria-describedby="payment-summary"
                @input="handlePaidAmountInput"
                @keydown.enter.prevent="submitSale"
              />
            </div>

            <div
              v-if="paymentMethod === 'CASH'"
              class="mt-2 flex flex-wrap gap-2"
            >
              <button
                v-for="amount in quickAmounts"
                :key="amount"
                type="button"
                class="focus-ring min-h-11 rounded-lg border border-[#D6DDD9] bg-white px-3 text-[13px] font-medium tabular-nums hover:bg-[#F1F4F2]"
                @click="paidAmount = amount"
              >
                {{ amount === cartTotal ? 'Uang pas' : formatCurrency(amount) }}
              </button>
            </div>
          </div>

          <!-- Ringkasan: Total / Bayar / Kembalian -->
          <dl
            id="payment-summary"
            class="mt-5 space-y-2 rounded-lg border border-[#E6EBE8] bg-[#F8FAF9] p-4 text-sm"
            aria-live="polite"
          >
            <div class="flex justify-between gap-4">
              <dt class="text-[#46514B]">Total</dt>
              <dd class="font-semibold tabular-nums">{{ formatCurrency(cartTotal) }}</dd>
            </div>

            <div class="flex justify-between gap-4">
              <dt class="text-[#46514B]">Bayar</dt>
              <dd class="font-semibold tabular-nums">{{ formatCurrency(paidAmount) }}</dd>
            </div>

            <div
              v-if="paymentShortfall > 0"
              class="flex justify-between gap-4 border-t border-[#E6EBE8] pt-2 text-base font-semibold text-[#8E2A20]"
            >
              <dt>Kurang</dt>
              <dd class="tabular-nums">{{ formatCurrency(paymentShortfall) }}</dd>
            </div>

            <div
              v-else
              class="flex justify-between gap-4 border-t border-[#E6EBE8] pt-2 text-base font-semibold text-[#12372A]"
            >
              <dt>Kembalian</dt>
              <dd class="tabular-nums">{{ formatCurrency(changeAmount) }}</dd>
            </div>
          </dl>

          <p
            v-if="checkoutError"
            role="alert"
            class="mt-4 rounded-lg border border-[#C0392B]/30 bg-[#FBEDEB] px-3 py-2 text-sm text-[#8E2A20]"
          >
            {{ checkoutError }}
          </p>

          <p
            v-if="!isOnline"
            role="alert"
            class="mt-4 rounded-lg border border-[#C0392B]/30 bg-[#FBEDEB] px-3 py-2 text-sm text-[#8E2A20]"
          >
            Koneksi terputus. Jangan tutup halaman. Periksa koneksi
            sebelum mengulangi transaksi.
          </p>

          <p class="mt-4 text-[13px] text-[#46514B]">
            Setelah diselesaikan, stok berkurang
            <span class="font-medium tabular-nums text-[#17201C]">{{ cartItemCount }}</span>
            unit dan transaksi tidak dapat diubah.
          </p>

          <div class="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <button
              type="button"
              class="focus-ring min-h-12 rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-semibold hover:bg-[#F1F4F2] disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="submittingSale"
              @click="closePayment"
            >
              Kembali ke keranjang
            </button>

            <button
              type="button"
              class="focus-ring min-h-12 rounded-lg bg-[#176B4D] px-5 text-sm font-semibold text-white hover:bg-[#1F805D] disabled:cursor-not-allowed disabled:bg-[#9AA8A1]"
              :disabled="!canSubmit"
              @click="submitSale"
            >
              {{ submittingSale ? 'Memproses transaksi...' : 'Selesaikan Transaksi' }}
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- Struk: hanya tampil saat dicetak -->
    <div
      v-if="saleSuccess"
      id="print-receipt"
      class="receipt-print hidden w-full max-w-sm bg-white p-5 text-sm text-slate-900"
    >
      <div class="text-center">
        <h2 class="text-lg font-bold">
          Koperasi Romantis
        </h2>

        <p class="mt-1 text-xs text-slate-500">
          Struk Penjualan
        </p>
      </div>

      <div class="my-4 border-t border-dashed border-slate-300"></div>

      <div class="space-y-1 text-xs">
        <div class="flex justify-between gap-4">
          <span>Transaksi</span>
          <span class="font-medium">{{ saleSuccess.saleNumber }}</span>
        </div>

        <div class="flex justify-between gap-4">
          <span>Tanggal</span>
          <span class="text-right">
            {{ new Date(saleSuccess.createdAt).toLocaleString('id-ID') }}
          </span>
        </div>
      </div>

      <div class="my-4 border-t border-dashed border-slate-300"></div>

      <div class="space-y-3">
        <div
          v-for="item in saleSuccess.items"
          :key="`${item.productId}-${item.sku}`"
        >
          <div class="font-medium">
            {{ item.name }}
          </div>

          <div class="mt-1 flex justify-between gap-4 text-xs text-slate-600">
            <span>
              {{ item.quantity }} {{ item.unit }} ×
              {{ formatCurrency(item.unitPrice) }}
            </span>

            <span class="font-medium text-slate-900">
              {{ formatCurrency(item.subtotal) }}
            </span>
          </div>
        </div>
      </div>

      <div class="my-4 border-t border-dashed border-slate-300"></div>

      <div class="space-y-2">
        <div class="flex justify-between">
          <span>Subtotal</span>
          <span>{{ formatCurrency(saleSuccess.subtotal) }}</span>
        </div>

        <div class="flex justify-between font-bold">
          <span>Total</span>
          <span>{{ formatCurrency(saleSuccess.total) }}</span>
        </div>

        <div class="flex justify-between">
          <span>Pembayaran</span>
          <span>{{ paymentLabel(saleSuccess.paymentMethod) }}</span>
        </div>

        <div class="flex justify-between">
          <span>Dibayar</span>
          <span>{{ formatCurrency(saleSuccess.paidAmount) }}</span>
        </div>

        <div class="flex justify-between font-semibold">
          <span>Kembalian</span>
          <span>{{ formatCurrency(saleSuccess.changeAmount) }}</span>
        </div>
      </div>

      <div
        v-if="saleSuccess.memberId"
        class="mt-4 border-t border-dashed border-slate-300 pt-3 text-xs"
      >
        <span class="text-slate-500">Member:</span>
        {{ saleSuccess.memberId }}
      </div>

      <div class="mt-6 text-center text-xs text-slate-500">
        Terima kasih telah berbelanja.
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Focus ring standar (DESIGN.md §13.2): 2px solid #176B4D, offset 2px */
.focus-ring:focus-visible {
  outline: 2px solid #176b4d;
  outline-offset: 2px;
}

@media print {
  :global(body) {
    margin: 0 !important;
    padding: 0 !important;
  }

  /* Sembunyikan seluruh isi halaman secara visual */
  :global(body *) {
    visibility: hidden !important;
  }

  /* Tampilkan struk dan seluruh isinya */
  #print-receipt,
  #print-receipt * {
    visibility: visible !important;
  }

  /* Lepaskan struk dari layout POS */
  #print-receipt {
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;

    display: block !important;

    width: 80mm !important;
    max-width: 80mm !important;

    margin: 0 !important;
    padding: 5mm !important;

    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;

    background: white !important;
    color: black !important;

    overflow: visible !important;
  }

  /* Pertahankan layout horizontal pada baris struk */
  #print-receipt .flex {
    display: flex !important;
  }
}
</style>