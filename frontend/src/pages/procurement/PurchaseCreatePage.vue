<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createPurchase,
  getGoodsReceipt,
  getPurchaseOrder,
} from '../../api/procurement'
import type {
  GoodsReceipt,
  PurchaseOrder,
} from '../../types/procurement'
import { useAuth } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const goodsReceipt = ref<GoodsReceipt | null>(null)
const purchaseOrder = ref<PurchaseOrder | null>(null)

const discount = ref(0)

const isLoading = ref(true)
const isSubmitting = ref(false)
const errorMessage = ref('')
const validationMessage = ref('')

const receiptId = computed(() => String(route.query.receiptId || ''))

interface PurchasePreviewItem {
  productId: string
  name: string
  sku: string
  quantity: number
  unitPrice: number
  subtotal: number
}

const items = computed<PurchasePreviewItem[]>(() => {
  if (!goodsReceipt.value || !purchaseOrder.value) {
    return []
  }

  return goodsReceipt.value.items
    .filter((receiptItem) => receiptItem.acceptedQuantity > 0)
    .map((receiptItem) => {
      const purchaseOrderItem = purchaseOrder.value?.items.find(
        (item) => item.productId === receiptItem.productId,
      )

      const unitPrice = purchaseOrderItem?.unitPrice ?? 0
      const quantity = receiptItem.acceptedQuantity

      return {
        productId: receiptItem.productId,
        name: receiptItem.name,
        sku: purchaseOrderItem?.sku ?? '-',
        quantity,
        unitPrice,
        subtotal: quantity * unitPrice,
      }
    })
})

const subtotal = computed(() => {
  return items.value.reduce((total, item) => total + item.subtotal, 0)
})

const total = computed(() => {
  return subtotal.value - discount.value
})

const totalQuantity = computed(() => {
  return items.value.reduce((total, item) => total + item.quantity, 0)
})

const hasInvalidPrice = computed(() => {
  return items.value.some((item) => item.unitPrice < 0)
})

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatDate(value: string | null) {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function validateForm() {
  validationMessage.value = ''

  if (!goodsReceipt.value) {
    validationMessage.value = 'Goods Receipt tidak ditemukan.'
    return false
  }

  if (!purchaseOrder.value) {
    validationMessage.value = 'Purchase Order terkait tidak ditemukan.'
    return false
  }

  if (items.value.length === 0) {
    validationMessage.value =
      'Tidak ada quantity diterima baik yang dapat dibuat menjadi Purchase.'
    return false
  }

  if (hasInvalidPrice.value) {
    validationMessage.value =
      'Harga pembelian pada Purchase Order tidak valid.'
    return false
  }

  if (!Number.isFinite(discount.value)) {
    validationMessage.value = 'Discount harus berupa angka yang valid.'
    return false
  }

  if (discount.value < 0) {
    validationMessage.value = 'Discount tidak boleh kurang dari 0.'
    return false
  }

  if (discount.value > subtotal.value) {
    validationMessage.value =
      'Discount tidak boleh lebih besar dari subtotal.'
    return false
  }

  if (total.value < 0) {
    validationMessage.value = 'Total Purchase tidak boleh kurang dari 0.'
    return false
  }

  return true
}

async function loadData() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  if (!receiptId.value) {
    errorMessage.value = 'Receipt ID tidak ditemukan pada URL.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  validationMessage.value = ''

  try {
    const receipt = await getGoodsReceipt(token.value, receiptId.value)

    goodsReceipt.value = receipt

    purchaseOrder.value = await getPurchaseOrder(
      token.value,
      receipt.purchaseOrderId,
    )
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data untuk membuat Purchase.'
  } finally {
    isLoading.value = false
  }
}

async function submitPurchase() {
  if (!validateForm()) {
    return
  }

  if (!token.value || !goodsReceipt.value) {
    errorMessage.value =
      'Sesi login atau Goods Receipt tidak tersedia.'
    return
  }

  const confirmed = window.confirm(
    `Buat Purchase dari ${goodsReceipt.value.receiptNumber} dengan total ${formatCurrency(total.value)}?`,
  )

  if (!confirmed) {
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''
  validationMessage.value = ''

  try {
    const purchase = await createPurchase(token.value, {
      receiptId: goodsReceipt.value.id,
      discount: discount.value,
    })

    router.push(`/purchases/${purchase.id}`)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal membuat Purchase.'
  } finally {
    isSubmitting.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <section class="min-h-full bg-[#F8FAF9] text-[#17201C]">
    <div class="mx-auto max-w-[1440px] space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      <!-- Breadcrumb + page header -->
      <header class="space-y-3">
        <nav
          aria-label="Breadcrumb"
          class="flex items-center gap-2 text-[13px] leading-[18px] text-[#6B756F]"
        >
          <button
            type="button"
            class="rounded-md font-medium transition-colors hover:text-[#176B4D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="router.push('/goods-receipts')"
          >
            Penerimaan Barang
          </button>

          <span aria-hidden="true">/</span>

          <span class="font-medium text-[#46514B]">
            Buat Purchase
          </span>
        </nav>

        <div>
          <h1 class="text-[28px] font-semibold leading-9 tracking-[-0.02em] text-[#17201C]">
            Buat Purchase
          </h1>

          <p class="mt-1 max-w-3xl text-sm leading-5 text-[#6B756F]">
            Buat transaksi Purchase berdasarkan Goods Receipt yang sudah
            diterima. Hanya quantity yang diterima baik yang akan masuk ke
            transaksi.
          </p>
        </div>
      </header>

      <!-- Loading state -->
      <div
        v-if="isLoading"
        class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]"
        aria-busy="true"
        aria-label="Memuat data Purchase"
      >
        <div class="space-y-5 rounded-lg border border-[#D6DDD9] bg-white p-6 shadow-[0_1px_2px_rgba(18,55,42,.06)]">
          <div class="space-y-2">
            <div class="h-6 w-40 animate-pulse rounded bg-[#F1F4F2]" />
            <div class="h-4 w-3/4 animate-pulse rounded bg-[#F1F4F2]" />
          </div>

          <div class="h-12 animate-pulse rounded-lg bg-[#F1F4F2]" />
          <div class="h-12 animate-pulse rounded-lg bg-[#F1F4F2]" />

          <div class="overflow-hidden rounded-lg border border-[#E6EBE8]">
            <div class="h-11 animate-pulse bg-[#F1F4F2]" />
            <div class="space-y-3 p-4">
              <div class="h-12 animate-pulse rounded bg-[#F8FAF9]" />
              <div class="h-12 animate-pulse rounded bg-[#F8FAF9]" />
              <div class="h-12 animate-pulse rounded bg-[#F8FAF9]" />
            </div>
          </div>
        </div>

        <aside class="h-fit space-y-5 rounded-lg border border-[#D6DDD9] bg-white p-6 shadow-[0_1px_2px_rgba(18,55,42,.06)]">
          <div class="h-6 w-36 animate-pulse rounded bg-[#F1F4F2]" />
          <div class="space-y-4">
            <div class="h-12 animate-pulse rounded bg-[#F1F4F2]" />
            <div class="h-12 animate-pulse rounded bg-[#F1F4F2]" />
            <div class="h-12 animate-pulse rounded bg-[#F1F4F2]" />
          </div>
        </aside>
      </div>

      <!-- Global load error -->
      <div
        v-else-if="errorMessage && !goodsReceipt"
        class="rounded-lg border border-[#C0392B]/25 bg-[#FFF6F5] p-6"
        role="alert"
      >
        <div class="flex items-start gap-3">
          <div class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#C0392B]/10 text-[#C0392B]">
            !
          </div>

          <div class="min-w-0">
            <h2 class="text-base font-semibold text-[#C0392B]">
              Purchase gagal dimuat
            </h2>

            <p class="mt-1 text-sm leading-5 text-[#C0392B]/90">
              {{ errorMessage }}
            </p>

            <button
              type="button"
              class="mt-4 inline-flex items-center justify-center rounded-md border border-[#C0392B]/30 bg-white px-4 py-2 text-sm font-medium text-[#C0392B] transition-colors hover:bg-[#FFF6F5] focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-2"
              @click="loadData"
            >
              Coba Lagi
            </button>
          </div>
        </div>
      </div>

      <template v-else-if="goodsReceipt && purchaseOrder">
        <!-- Validation error -->
        <div
          v-if="validationMessage"
          class="rounded-lg border border-[#B7791F]/30 bg-[#FFF9EE] p-4"
          role="alert"
        >
          <div class="flex items-start gap-3">
            <span
              class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#B7791F]/15 text-xs font-bold text-[#B7791F]"
              aria-hidden="true"
            >
              !
            </span>

            <p class="text-sm font-medium leading-5 text-[#76520F]">
              {{ validationMessage }}
            </p>
          </div>
        </div>

        <!-- Create/Edit layout: Main Form + Context/Summary -->
        <div class="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <!-- Main form -->
          <main class="min-w-0 space-y-6">
            <section class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white shadow-[0_1px_2px_rgba(18,55,42,.06)]">
              <div class="border-b border-[#E6EBE8] px-5 py-5 sm:px-6">
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <h2 class="text-[18px] font-semibold leading-[26px] text-[#17201C]">
                      Item Purchase
                    </h2>

                    <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                      Item berasal dari quantity accepted pada Goods Receipt.
                      Harga mengikuti Purchase Order.
                    </p>
                  </div>

                  <span class="shrink-0 rounded-full bg-[#F0F8F5] px-3 py-1 text-xs font-semibold text-[#176B4D]">
                    {{ items.length }} item
                  </span>
                </div>
              </div>

              <div class="overflow-x-auto">
                <table class="min-w-full text-left text-sm">
                  <caption class="sr-only">
                    Daftar item yang akan dibuat menjadi Purchase
                  </caption>

                  <thead class="border-b border-[#E6EBE8] bg-[#F1F4F2]">
                    <tr>
                      <th
                        scope="col"
                        class="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-[#46514B]"
                      >
                        Produk
                      </th>

                      <th
                        scope="col"
                        class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]"
                      >
                        Qty
                      </th>

                      <th
                        scope="col"
                        class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]"
                      >
                        Harga
                      </th>

                      <th
                        scope="col"
                        class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]"
                      >
                        Subtotal
                      </th>
                    </tr>
                  </thead>

                  <tbody class="divide-y divide-[#E6EBE8]">
                    <tr
                      v-for="item in items"
                      :key="item.productId"
                      class="transition-colors hover:bg-[#F8FAF9]"
                    >
                      <td class="px-5 py-4">
                        <p class="font-medium text-[#17201C]">
                          {{ item.name }}
                        </p>

                        <div class="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-[#6B756F]">
                          <span>SKU: {{ item.sku }}</span>
                          <span>Product ID: {{ item.productId }}</span>
                        </div>
                      </td>

                      <td class="px-4 py-4 text-right tabular-nums text-[#46514B]">
                        {{ item.quantity }}
                      </td>

                      <td class="whitespace-nowrap px-4 py-4 text-right tabular-nums text-[#46514B]">
                        {{ formatCurrency(item.unitPrice) }}
                      </td>

                      <td class="whitespace-nowrap px-5 py-4 text-right font-semibold tabular-nums text-[#17201C]">
                        {{ formatCurrency(item.subtotal) }}
                      </td>
                    </tr>

                    <tr v-if="items.length === 0">
                      <td
                        colspan="4"
                        class="px-6 py-12 text-center"
                      >
                        <div class="mx-auto max-w-md">
                          <p class="text-sm font-medium text-[#17201C]">
                            Belum ada item yang dapat dibuat menjadi Purchase.
                          </p>

                          <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                            Goods Receipt ini belum memiliki quantity accepted
                            yang lebih dari 0.
                          </p>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <!-- Discount form -->
            <section class="rounded-lg border border-[#D6DDD9] bg-white p-5 shadow-[0_1px_2px_rgba(18,55,42,.06)] sm:p-6">
              <div class="max-w-xl">
                <h2 class="text-[18px] font-semibold leading-[26px] text-[#17201C]">
                  Penyesuaian Purchase
                </h2>

                <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                  Masukkan discount bila diperlukan. Nilai tidak boleh negatif
                  atau melebihi subtotal.
                </p>

                <div class="mt-5">
                  <label
                    for="discount"
                    class="block text-sm font-medium text-[#46514B]"
                  >
                    Discount
                  </label>

                  <div class="relative mt-2">
                    <span
                      class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-sm font-medium text-[#6B756F]"
                    >
                      Rp
                    </span>

                    <input
                      id="discount"
                      v-model.number="discount"
                      type="number"
                      min="0"
                      step="1"
                      inputmode="numeric"
                      :disabled="isSubmitting"
                      class="block w-full rounded-md border border-[#D6DDD9] bg-white py-2.5 pl-10 pr-3 text-sm tabular-nums text-[#17201C] outline-none transition placeholder:text-[#6B756F] hover:border-[#AEB9B3] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/15 disabled:cursor-not-allowed disabled:bg-[#F1F4F2] disabled:opacity-70"
                      aria-describedby="discount-help"
                    />
                  </div>

                  <p
                    id="discount-help"
                    class="mt-2 text-xs leading-4 text-[#6B756F]"
                  >
                    Discount diinput secara manual dan tidak boleh melebihi
                    subtotal.
                  </p>
                </div>
              </div>
            </section>

            <!-- Contextual error during submit -->
            <div
              v-if="errorMessage"
              class="rounded-lg border border-[#C0392B]/25 bg-[#FFF6F5] p-4"
              role="alert"
            >
              <p class="text-sm font-medium leading-5 text-[#C0392B]">
                {{ errorMessage }}
              </p>
            </div>
          </main>

          <!-- Context / Summary -->
          <aside class="space-y-5 lg:sticky lg:top-6">
            <section class="rounded-lg border border-[#D6DDD9] bg-white p-5 shadow-[0_1px_2px_rgba(18,55,42,.06)] sm:p-6">
              <div class="flex items-center justify-between gap-3">
                <h2 class="text-[18px] font-semibold leading-[26px] text-[#17201C]">
                  Ringkasan
                </h2>

                <span class="rounded-full bg-[#DCEFE7] px-2.5 py-1 text-xs font-semibold text-[#176B4D]">
                  Siap dibuat
                </span>
              </div>

              <dl class="mt-5 divide-y divide-[#E6EBE8]">
                <div class="flex items-start justify-between gap-4 py-3 first:pt-0">
                  <dt class="text-[13px] leading-[18px] text-[#6B756F]">
                    Subtotal
                  </dt>

                  <dd class="text-right text-sm font-medium tabular-nums text-[#17201C]">
                    {{ formatCurrency(subtotal) }}
                  </dd>
                </div>

                <div class="flex items-start justify-between gap-4 py-3">
                  <dt class="text-[13px] leading-[18px] text-[#6B756F]">
                    Discount
                  </dt>

                  <dd class="text-right text-sm font-medium tabular-nums text-[#46514B]">
                    {{ formatCurrency(discount) }}
                  </dd>
                </div>

                <div class="flex items-start justify-between gap-4 py-4">
                  <dt class="text-sm font-semibold text-[#17201C]">
                    Total
                  </dt>

                  <dd class="text-right text-[22px] font-bold leading-[30px] tabular-nums text-[#12372A]">
                    {{ formatCurrency(total) }}
                  </dd>
                </div>
              </dl>

              <div class="mt-2 rounded-md bg-[#F0F8F5] p-3">
                <p class="text-xs font-medium text-[#176B4D]">
                  Dampak transaksi
                </p>

                <p class="mt-1 text-xs leading-4 text-[#46514B]">
                  Purchase dibuat berdasarkan quantity accepted dari Goods
                  Receipt. Tidak ada perubahan stok langsung dari halaman ini.
                </p>
              </div>
            </section>

            <section class="rounded-lg border border-[#D6DDD9] bg-white p-5 shadow-[0_1px_2px_rgba(18,55,42,.06)] sm:p-6">
              <h2 class="text-[18px] font-semibold leading-[26px] text-[#17201C]">
                Sumber Transaksi
              </h2>

              <dl class="mt-4 space-y-4">
                <div>
                  <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
                    Receipt
                  </dt>

                  <dd class="mt-1">
                    <p class="text-sm font-semibold text-[#17201C]">
                      {{ goodsReceipt.receiptNumber }}
                    </p>

                    <p class="mt-1 text-xs text-[#6B756F]">
                      {{ formatDate(goodsReceipt.receivedAt) }}
                    </p>
                  </dd>
                </div>

                <div>
                  <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
                    Purchase Order
                  </dt>

                  <dd class="mt-1 break-all text-sm font-medium text-[#17201C]">
                    {{ goodsReceipt.purchaseOrderId }}
                  </dd>
                </div>

                <div>
                  <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
                    Supplier
                  </dt>

                  <dd class="mt-1 break-all text-sm font-medium text-[#17201C]">
                    {{ goodsReceipt.supplierId }}
                  </dd>
                </div>
              </dl>
            </section>

            <section class="rounded-lg border border-[#E6EBE8] bg-[#F1F4F2] p-5">
              <h2 class="text-sm font-semibold text-[#17201C]">
                Data Purchase
              </h2>

              <dl class="mt-3 grid grid-cols-2 gap-4">
                <div>
                  <dt class="text-xs text-[#6B756F]">
                    Item
                  </dt>
                  <dd class="mt-1 text-base font-semibold tabular-nums text-[#17201C]">
                    {{ items.length }}
                  </dd>
                </div>

                <div>
                  <dt class="text-xs text-[#6B756F]">
                    Total Qty
                  </dt>
                  <dd class="mt-1 text-base font-semibold tabular-nums text-[#17201C]">
                    {{ totalQuantity }}
                  </dd>
                </div>
              </dl>
            </section>
          </aside>
        </div>

        <!-- Sticky footer -->
        <footer
          class="sticky bottom-0 z-20 -mx-4 border-t border-[#D6DDD9] bg-white/95 px-4 py-4 backdrop-blur sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8"
        >
          <div class="mx-auto flex max-w-[1440px] flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p class="hidden text-[13px] leading-[18px] text-[#6B756F] sm:block">
              Periksa item, discount, dan total sebelum menyimpan Purchase.
            </p>

            <div class="flex flex-col-reverse gap-3 sm:flex-row">
              <button
                type="button"
                class="inline-flex min-h-10 items-center justify-center rounded-md border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#46514B] transition-colors hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="isSubmitting"
                @click="router.push(`/goods-receipts/${goodsReceipt.id}`)"
              >
                Batal
              </button>

              <button
                type="button"
                class="inline-flex min-h-10 items-center justify-center rounded-md bg-[#176B4D] px-5 text-sm font-semibold text-white shadow-[0_1px_2px_rgba(18,55,42,.08)] transition-colors hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="isSubmitting || items.length === 0"
                @click="submitPurchase"
              >
                <svg
                  v-if="isSubmitting"
                  class="mr-2 h-4 w-4 animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden="true"
                >
                  <circle
                    class="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    stroke-width="4"
                  />
                  <path
                    class="opacity-90"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                  />
                </svg>

                {{ isSubmitting ? 'Menyimpan...' : 'Simpan Purchase' }}
              </button>
            </div>
          </div>
        </footer>
      </template>
    </div>
  </section>
</template>
