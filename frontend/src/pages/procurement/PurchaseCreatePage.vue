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
  return items.value.reduce((total, item) => {
    return total + item.subtotal
  }, 0)
})

const total = computed(() => {
  return subtotal.value - discount.value
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
    validationMessage.value =
      'Goods Receipt tidak ditemukan.'
    return false
  }

  if (!purchaseOrder.value) {
    validationMessage.value =
      'Purchase Order terkait tidak ditemukan.'
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
    validationMessage.value =
      'Discount harus berupa angka yang valid.'
    return false
  }

  if (discount.value < 0) {
    validationMessage.value =
      'Discount tidak boleh kurang dari 0.'
    return false
  }

  if (discount.value > subtotal.value) {
    validationMessage.value =
      'Discount tidak boleh lebih besar dari subtotal.'
    return false
  }

  if (total.value < 0) {
    validationMessage.value =
      'Total Purchase tidak boleh kurang dari 0.'
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
    errorMessage.value =
      'Receipt ID tidak ditemukan pada URL.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  validationMessage.value = ''

  try {
    const receipt = await getGoodsReceipt(
      token.value,
      receiptId.value,
    )

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
    const purchase = await createPurchase(
      token.value,
      {
        receiptId: goodsReceipt.value.id,
        discount: discount.value,
      },
    )

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
  <section class="space-y-6">
    <div>
      <button
        type="button"
        class="text-sm font-medium text-green-800 hover:underline focus:outline-none focus:ring-2 focus:ring-green-700"
        @click="router.push('/goods-receipts')"
      >
        ← Kembali ke Penerimaan Barang
      </button>

      <h1 class="mt-3 text-2xl font-semibold text-gray-900">
        Buat Purchase
      </h1>

      <p class="mt-1 text-sm text-gray-600">
        Buat transaksi Purchase berdasarkan Goods Receipt yang sudah diterima.
      </p>
    </div>

    <div
      v-if="isLoading"
      class="space-y-4 rounded-xl border border-gray-200 bg-white p-6"
    >
      <div class="h-8 animate-pulse rounded bg-gray-100"></div>
      <div class="h-24 animate-pulse rounded bg-gray-100"></div>
      <div class="h-48 animate-pulse rounded bg-gray-100"></div>
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
      role="alert"
    >
      <h2 class="font-semibold text-red-800">
        Purchase gagal dimuat
      </h2>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
        @click="loadData"
      >
        Coba Lagi
      </button>
    </div>

    <template v-else-if="goodsReceipt && purchaseOrder">
      <section
        class="rounded-xl border border-gray-200 bg-white p-6"
      >
        <h2 class="text-lg font-semibold text-gray-900">
          Sumber Transaksi
        </h2>

        <div class="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Receipt
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ goodsReceipt.receiptNumber }}
            </p>

            <p class="mt-1 text-xs text-gray-500">
              {{ formatDate(goodsReceipt.receivedAt) }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Purchase Order
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ goodsReceipt.purchaseOrderId }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Supplier
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ goodsReceipt.supplierId }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Jumlah Item
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ items.length }}
            </p>
          </div>
        </div>
      </section>

      <div
        v-if="validationMessage"
        class="rounded-xl border border-yellow-200 bg-yellow-50 p-4"
        role="alert"
      >
        <p class="text-sm font-medium text-yellow-900">
          {{ validationMessage }}
        </p>
      </div>

      <section
        class="overflow-x-auto rounded-xl border border-gray-200 bg-white"
      >
        <div class="border-b border-gray-200 px-6 py-4">
          <h2 class="text-lg font-semibold text-gray-900">
            Item Purchase
          </h2>

          <p class="mt-1 text-sm text-gray-600">
            Hanya quantity yang diterima baik yang masuk ke Purchase.
            Harga mengikuti Purchase Order.
          </p>
        </div>

        <table class="min-w-full text-left text-sm">
          <thead class="border-b border-gray-200 bg-gray-50">
            <tr>
              <th class="px-4 py-3 font-medium text-gray-600">
                Produk
              </th>

              <th class="px-4 py-3 text-right font-medium text-gray-600">
                Qty
              </th>

              <th class="px-4 py-3 text-right font-medium text-gray-600">
                Harga
              </th>

              <th class="px-4 py-3 text-right font-medium text-gray-600">
                Subtotal
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="item in items"
              :key="item.productId"
            >
              <td class="px-4 py-4">
                <p class="font-medium text-gray-900">
                  {{ item.name }}
                </p>

                <p class="mt-1 text-xs text-gray-500">
                  SKU: {{ item.sku }}
                </p>

                <p class="mt-1 text-xs text-gray-400">
                  {{ item.productId }}
                </p>
              </td>

              <td class="px-4 py-4 text-right text-gray-700">
                {{ item.quantity }}
              </td>

              <td class="whitespace-nowrap px-4 py-4 text-right text-gray-700">
                {{ formatCurrency(item.unitPrice) }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-right font-medium text-gray-900"
              >
                {{ formatCurrency(item.subtotal) }}
              </td>
            </tr>

            <tr v-if="items.length === 0">
              <td
                colspan="4"
                class="px-6 py-10 text-center text-sm text-gray-500"
              >
                Tidak ada item dengan quantity diterima baik.
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section
        class="rounded-xl border border-gray-200 bg-white p-6"
      >
        <div class="ml-auto max-w-md space-y-4">
          <div class="flex items-center justify-between gap-4">
            <span class="text-sm text-gray-600">
              Subtotal
            </span>

            <span class="font-medium text-gray-900">
              {{ formatCurrency(subtotal) }}
            </span>
          </div>

          <div>
            <label
              for="discount"
              class="block text-sm font-medium text-gray-700"
            >
              Discount
            </label>

            <div class="mt-1">
              <input
                id="discount"
                v-model.number="discount"
                type="number"
                min="0"
                step="1"
                inputmode="numeric"
                class="block w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 focus:border-green-700 focus:outline-none focus:ring-2 focus:ring-green-700"
                :disabled="isSubmitting"
              />
            </div>

            <p class="mt-1 text-xs text-gray-500">
              Discount diinput secara manual dan tidak boleh melebihi
              subtotal.
            </p>
          </div>

          <div
            class="border-t border-gray-200 pt-4"
          >
            <div class="flex items-center justify-between gap-4">
              <span class="text-base font-semibold text-gray-900">
                Total
              </span>

              <span class="text-xl font-bold text-gray-900">
                {{ formatCurrency(total) }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <div
        v-if="errorMessage"
        class="rounded-xl border border-red-200 bg-red-50 p-4"
        role="alert"
      >
        <p class="text-sm font-medium text-red-900">
          {{ errorMessage }}
        </p>
      </div>

      <div
        class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end"
      >
        <button
          type="button"
          class="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="isSubmitting"
          @click="router.push(`/goods-receipts/${goodsReceipt.id}`)"
        >
          Batal
        </button>

        <button
          type="button"
          class="rounded-lg bg-green-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-900 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="isSubmitting || items.length === 0"
          @click="submitPurchase"
        >
          {{ isSubmitting ? 'Menyimpan...' : 'Simpan Purchase' }}
        </button>
      </div>
    </template>
  </section>
</template>