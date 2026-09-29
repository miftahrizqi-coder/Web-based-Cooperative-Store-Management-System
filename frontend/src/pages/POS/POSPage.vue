<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'

import { useAuth } from '../../stores/auth'
import {
  getPOSProductByBarcode,
  searchPOSMembers,
  searchPOSProducts,
} from '../../api/pos'
import type {
  CartItem,
  POSMember,
  POSProduct,
} from '../../types/pos'

const { currentUser } = useAuth()

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

const productError = ref('')
const barcodeError = ref('')
const memberError = ref('')

const showMemberPicker = ref(false)

const searchRef = ref<HTMLInputElement | null>(null)
const barcodeRef = ref<HTMLInputElement | null>(null)

const accessToken = computed(() =>
  localStorage.getItem('access_token'),
)

const cartTotal = computed(() =>
  cart.value.reduce(
    (total, item) =>
      total +
      item.product.selling_price * item.quantity,
    0,
  ),
)

const cartItemCount = computed(() =>
  cart.value.reduce(
    (total, item) => total + item.quantity,
    0,
  ),
)

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

async function focusSearch(): Promise<void> {
  await nextTick()
  searchRef.value?.focus()
}

async function loadProducts(): Promise<void> {
  const token = accessToken.value

  if (!token) {
    productError.value = 'Sesi login tidak ditemukan.'
    return
  }

  loadingProducts.value = true
  productError.value = ''

  try {
    products.value = await searchPOSProducts(
      token,
      searchInput.value,
    )
  } catch (error) {
    productError.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil produk.'
  } finally {
    loadingProducts.value = false
  }
}

let searchTimer: ReturnType<typeof setTimeout> | null =
  null

function handleProductSearch(): void {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }

  searchTimer = setTimeout(() => {
    void loadProducts()
  }, 250)
}

async function lookupBarcode(): Promise<void> {
  const barcode = barcodeInput.value.trim()

  if (!barcode) {
    barcodeError.value = 'Masukkan barcode terlebih dahulu.'
    return
  }

  const token = accessToken.value

  if (!token) {
    barcodeError.value = 'Sesi login tidak ditemukan.'
    return
  }

  loadingBarcode.value = true
  barcodeError.value = ''

  try {
    const product = await getPOSProductByBarcode(
      token,
      barcode,
    )

    addToCart(product)

    barcodeInput.value = ''

    await focusSearch()
  } catch (error) {
    barcodeError.value =
      error instanceof Error
        ? error.message
        : 'Produk tidak ditemukan.'
  } finally {
    loadingBarcode.value = false
  }
}

function getCartItem(
  productId: string,
): CartItem | undefined {
  return cart.value.find(
    (item) => item.product.id === productId,
  )
}

function addToCart(product: POSProduct): void {
  if (!product.is_active) {
    return
  }

  if (product.stock <= 0) {
    productError.value =
      `Stok ${product.name} habis.`
    return
  }

  const existing = getCartItem(product.id)

  if (existing) {
    if (existing.quantity >= product.stock) {
      productError.value =
        `Jumlah ${product.name} tidak boleh melebihi stok.`
      return
    }

    existing.quantity += 1
    return
  }

  cart.value.push({
    product,
    quantity: 1,
  })
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
  cart.value = cart.value.filter(
    (item) => item.product.id !== productId,
  )
}

function clearCart(): void {
  cart.value = []
  selectedMember.value = null
}

async function loadMembers(): Promise<void> {
  const token = accessToken.value

  if (!token) {
    memberError.value = 'Sesi login tidak ditemukan.'
    return
  }

  loadingMembers.value = true
  memberError.value = ''

  try {
    members.value = await searchPOSMembers(
      token,
      memberSearch.value,
    )
  } catch (error) {
    memberError.value =
      error instanceof Error
        ? error.message
        : 'Gagal mencari anggota.'
  } finally {
    loadingMembers.value = false
  }
}

let memberSearchTimer: ReturnType<typeof setTimeout> | null =
  null

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
}

function removeMember(): void {
  selectedMember.value = null
}

function handleSearchKeydown(
  event: KeyboardEvent,
): void {
  if (event.key === 'Enter') {
    event.preventDefault()

    if (products.value.length === 1) {
      addToCart(products.value[0])
    }
  }
}

function handleBarcodeKeydown(
  event: KeyboardEvent,
): void {
  if (event.key === 'Enter') {
    event.preventDefault()
    void lookupBarcode()
  }
}

onMounted(async () => {
  await loadProducts()
  await focusSearch()
})
</script>

<template>
  <div class="mx-auto max-w-7xl space-y-4">
    <div>
      <h1 class="text-2xl font-semibold text-gray-900">
        POS
      </h1>
      <p class="mt-1 text-sm text-gray-500">
        Kasir:
        {{ currentUser?.name || currentUser?.username || '-' }}
      </p>
    </div>

    <div
      class="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]"
    >
      <!-- Product workspace -->
      <section
        class="rounded-xl border bg-white p-4"
        aria-labelledby="product-section-title"
      >
        <div class="mb-4">
          <h2
            id="product-section-title"
            class="text-lg font-semibold"
          >
            Produk
          </h2>
          <p class="text-sm text-gray-500">
            Cari berdasarkan nama, SKU, atau gunakan barcode.
          </p>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label
              for="product-search"
              class="mb-1 block text-sm font-medium text-gray-700"
            >
              Cari produk
            </label>

            <input
              id="product-search"
              ref="searchRef"
              v-model="searchInput"
              type="search"
              autocomplete="off"
              placeholder="Nama, SKU, barcode..."
              class="min-h-11 w-full rounded-lg border px-3 text-base outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-200"
              @input="handleProductSearch"
              @keydown="handleSearchKeydown"
            />
          </div>

          <div>
            <label
              for="barcode-search"
              class="mb-1 block text-sm font-medium text-gray-700"
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
                placeholder="Scan / ketik barcode"
                class="min-h-11 min-w-0 flex-1 rounded-lg border px-3 text-base outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-200"
                @keydown="handleBarcodeKeydown"
              />

              <button
                type="button"
                class="min-h-11 rounded-lg bg-gray-900 px-4 text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="loadingBarcode"
                @click="lookupBarcode"
              >
                {{ loadingBarcode ? '...' : 'Cari' }}
              </button>
            </div>
          </div>
        </div>

        <p
          v-if="barcodeError"
          class="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {{ barcodeError }}
        </p>

        <p
          v-if="productError"
          class="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {{ productError }}
        </p>

        <div class="mt-4">
          <div
            v-if="loadingProducts"
            class="space-y-3"
            aria-label="Memuat produk"
          >
            <div
              v-for="index in 4"
              :key="index"
              class="h-20 animate-pulse rounded-lg bg-gray-100"
            />
          </div>

          <div
            v-else-if="products.length === 0"
            class="rounded-lg border border-dashed p-8 text-center"
          >
            <p class="font-medium text-gray-700">
              Produk tidak ditemukan
            </p>
            <p class="mt-1 text-sm text-gray-500">
              Coba kata kunci lain atau gunakan barcode.
            </p>
          </div>

          <div
            v-else
            class="grid gap-3 sm:grid-cols-2"
          >
            <button
              v-for="product in products"
              :key="product.id"
              type="button"
              class="rounded-lg border p-4 text-left transition hover:border-gray-400 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="product.stock <= 0"
              @click="addToCart(product)"
            >
              <div
                class="flex items-start justify-between gap-3"
              >
                <div class="min-w-0">
                  <p
                    class="font-medium text-gray-900"
                  >
                    {{ product.name }}
                  </p>

                  <p class="mt-1 text-xs text-gray-500">
                    {{ product.sku }}
                    <span v-if="product.barcode">
                      · {{ product.barcode }}
                    </span>
                  </p>
                </div>

                <span
                  class="shrink-0 rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600"
                >
                  {{ formatStock(product) }}
                </span>
              </div>

              <div
                class="mt-3 flex items-center justify-between gap-3"
              >
                <span
                  class="font-semibold text-gray-900"
                >
                  {{ formatCurrency(product.selling_price) }}
                </span>

                <span
                  class="text-xs text-gray-500"
                >
                  Klik untuk tambah
                </span>
              </div>
            </button>
          </div>
        </div>
      </section>

      <!-- Cart -->
      <section
        class="rounded-xl border bg-white p-4"
        aria-labelledby="cart-section-title"
      >
        <div
          class="flex items-center justify-between gap-3"
        >
          <div>
            <h2
              id="cart-section-title"
              class="text-lg font-semibold"
            >
              Keranjang
            </h2>
            <p class="text-sm text-gray-500">
              {{ cartItemCount }} item
            </p>
          </div>

          <button
            v-if="cart.length"
            type="button"
            class="min-h-11 rounded-lg px-3 text-sm font-medium text-red-600 hover:bg-red-50"
            @click="clearCart"
          >
            Kosongkan
          </button>
        </div>

        <div
          v-if="cart.length === 0"
          class="mt-4 rounded-lg border border-dashed p-8 text-center"
        >
          <p class="font-medium text-gray-700">
            Keranjang masih kosong
          </p>
          <p class="mt-1 text-sm text-gray-500">
            Pilih produk untuk memulai transaksi.
          </p>
        </div>

        <div
          v-else
          class="mt-4 space-y-3"
        >
          <article
            v-for="item in cart"
            :key="item.product.id"
            class="rounded-lg border p-3"
          >
            <div class="flex gap-3">
              <div class="min-w-0 flex-1">
                <p class="font-medium text-gray-900">
                  {{ item.product.name }}
                </p>

                <p class="mt-1 text-xs text-gray-500">
                  {{ formatCurrency(item.product.selling_price) }}
                  /
                  {{ item.product.unit }}
                </p>
              </div>

              <button
                type="button"
                class="min-h-11 rounded-lg px-2 text-sm text-red-600 hover:bg-red-50"
                :aria-label="`Hapus ${item.product.name}`"
                @click="removeFromCart(item.product.id)"
              >
                Hapus
              </button>
            </div>

            <div
              class="mt-3 flex items-center justify-between gap-3"
            >
              <div
                class="flex items-center rounded-lg border"
              >
                <button
                  type="button"
                  class="min-h-11 min-w-11 text-lg hover:bg-gray-50"
                  :aria-label="`Kurangi ${item.product.name}`"
                  @click="decreaseQuantity(item)"
                >
                  −
                </button>

                <span
                  class="min-w-10 text-center text-sm font-semibold"
                >
                  {{ item.quantity }}
                </span>

                <button
                  type="button"
                  class="min-h-11 min-w-11 text-lg hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
                  :aria-label="`Tambah ${item.product.name}`"
                  :disabled="
                    item.quantity >= item.product.stock
                  "
                  @click="increaseQuantity(item)"
                >
                  +
                </button>
              </div>

              <p class="font-semibold text-gray-900">
                {{
                  formatCurrency(
                    item.product.selling_price *
                      item.quantity,
                  )
                }}
              </p>
            </div>

            <p class="mt-2 text-xs text-gray-500">
              Stok tersedia:
              {{ formatStock(item.product) }}
            </p>
          </article>
        </div>

        <!-- Member -->
        <div class="mt-4 border-t pt-4">
          <div
            class="flex items-center justify-between gap-3"
          >
            <div>
              <h3 class="font-medium text-gray-900">
                Anggota
              </h3>

              <p
                v-if="selectedMember"
                class="mt-1 text-sm text-gray-500"
              >
                {{ selectedMember.memberNumber }}
                ·
                {{ selectedMember.name }}
              </p>

              <p
                v-else
                class="mt-1 text-sm text-gray-500"
              >
                Opsional
              </p>
            </div>

            <button
              type="button"
              class="min-h-11 rounded-lg border px-3 text-sm font-medium hover:bg-gray-50"
              @click="
                showMemberPicker = !showMemberPicker
              "
            >
              {{
                selectedMember
                  ? 'Ganti'
                  : 'Pilih anggota'
              }}
            </button>
          </div>

          <button
            v-if="selectedMember"
            type="button"
            class="mt-2 text-sm text-red-600"
            @click="removeMember"
          >
            Hapus anggota
          </button>

          <div
            v-if="showMemberPicker"
            class="mt-3 rounded-lg border bg-gray-50 p-3"
          >
            <input
              v-model="memberSearch"
              type="search"
              placeholder="Cari nomor, nama, atau telepon..."
              class="min-h-11 w-full rounded-lg border bg-white px-3 text-base outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-200"
              @input="handleMemberSearch"
            />

            <p
              v-if="memberError"
              class="mt-2 text-sm text-red-600"
              role="alert"
            >
              {{ memberError }}
            </p>

            <div
              v-if="loadingMembers"
              class="mt-3 text-sm text-gray-500"
            >
              Mencari anggota...
            </div>

            <div
              v-else-if="members.length"
              class="mt-3 space-y-2"
            >
              <button
                v-for="member in members"
                :key="member.id"
                type="button"
                class="min-h-11 w-full rounded-lg border bg-white p-3 text-left hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="member.status !== 'ACTIVE'"
                @click="selectMember(member)"
              >
                <p class="font-medium">
                  {{ member.name }}
                </p>

                <p class="text-xs text-gray-500">
                  {{ member.memberNumber }}
                  ·
                  {{ member.phone }}
                </p>
              </button>
            </div>

            <p
              v-else-if="memberSearch.trim()"
              class="mt-3 text-sm text-gray-500"
            >
              Anggota tidak ditemukan.
            </p>
          </div>
        </div>

        <!-- Total -->
        <div class="mt-4 border-t pt-4">
          <div
            class="flex items-center justify-between gap-3"
          >
            <span class="text-sm text-gray-500">
              Total sementara
            </span>

            <span
              class="text-2xl font-bold text-gray-900"
            >
              {{ formatCurrency(cartTotal) }}
            </span>
          </div>

          <p class="mt-2 text-xs text-gray-500">
            Pembayaran akan dilanjutkan pada tahap berikutnya.
          </p>
        </div>
      </section>
    </div>
  </div>
</template>