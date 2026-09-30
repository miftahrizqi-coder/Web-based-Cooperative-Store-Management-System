<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getGoodsReceipt,
  getPurchases,
} from '../../api/procurement'
import type {
  GoodsReceipt,
  Purchase,
} from '../../types/procurement'
import { useAuth } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const goodsReceipt = ref<GoodsReceipt | null>(null)
const relatedPurchase = ref<Purchase | null>(null)

const isLoading = ref(true)
const errorMessage = ref('')
const purchaseLoadError = ref('')

const goodsReceiptId = String(route.params.id)

function formatDate(value: string | null) {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

const canCreatePurchase = computed(() => {
  return Boolean(goodsReceipt.value && !relatedPurchase.value)
})

async function loadGoodsReceipt() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  purchaseLoadError.value = ''

  try {
    const [receipt, purchases] = await Promise.all([
      getGoodsReceipt(token.value, goodsReceiptId),
      getPurchases(token.value),
    ])

    goodsReceipt.value = receipt

    relatedPurchase.value =
      purchases.find(
        (purchase) => purchase.receiptId === receipt.id,
      ) || null
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil detail penerimaan barang.'
  } finally {
    isLoading.value = false
  }
}

function openCreatePurchase() {
  if (!goodsReceipt.value) {
    return
  }

  router.push(
    `/purchases/create?receiptId=${goodsReceipt.value.id}`,
  )
}

function openPurchaseDetail() {
  if (!relatedPurchase.value) {
    return
  }

  router.push(
    `/purchases/${relatedPurchase.value.id}`,
  )
}

onMounted(loadGoodsReceipt)
</script>

<template>
  <section class="space-y-6">
    <div
      class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
    >
      <div>
        <button
          type="button"
          class="text-sm font-medium text-green-800 hover:underline focus:outline-none focus:ring-2 focus:ring-green-700"
          @click="router.push('/goods-receipts')"
        >
          ← Kembali ke Penerimaan Barang
        </button>

        <h1 class="mt-3 text-2xl font-semibold text-gray-900">
          {{ goodsReceipt?.receiptNumber || 'Detail Penerimaan Barang' }}
        </h1>

        <p class="mt-1 text-sm text-gray-600">
          Detail penerimaan barang dari Purchase Order.
        </p>
      </div>

      <div
        v-if="!isLoading && goodsReceipt"
        class="flex flex-wrap gap-2"
      >
        <button
          v-if="canCreatePurchase"
          type="button"
          class="rounded-lg bg-green-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-900 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
          @click="openCreatePurchase"
        >
          Buat Purchase
        </button>

        <button
          v-else-if="relatedPurchase"
          type="button"
          class="rounded-lg border border-green-700 px-4 py-2.5 text-sm font-medium text-green-800 hover:bg-green-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
          @click="openPurchaseDetail"
        >
          Lihat Purchase
        </button>
      </div>
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
        Penerimaan barang gagal dimuat
      </h2>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
        @click="loadGoodsReceipt"
      >
        Coba lagi
      </button>
    </div>

    <template v-else-if="goodsReceipt">
      <section
        v-if="purchaseLoadError"
        class="rounded-xl border border-yellow-200 bg-yellow-50 p-4"
        role="alert"
      >
        <h2 class="font-semibold text-yellow-900">
          Status Purchase belum dapat diperiksa
        </h2>

        <p class="mt-1 text-sm text-yellow-800">
          {{ purchaseLoadError }}
        </p>
      </section>

      <section
        v-if="relatedPurchase"
        class="rounded-xl border border-green-200 bg-green-50 p-6"
      >
        <div
          class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-green-700"
            >
              Purchase sudah dibuat
            </p>

            <p class="mt-1 text-lg font-semibold text-green-900">
              {{ relatedPurchase.purchaseNumber }}
            </p>

            <p class="mt-1 text-sm text-green-800">
              Total:
              {{ formatCurrency(relatedPurchase.total) }}
            </p>
          </div>

          <button
            type="button"
            class="rounded-lg border border-green-700 px-4 py-2.5 text-sm font-medium text-green-800 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
            @click="openPurchaseDetail"
          >
            Lihat Purchase
          </button>
        </div>
      </section>

      <section
        v-else
        class="rounded-xl border border-gray-200 bg-white p-6"
      >
        <div
          class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <h2 class="text-lg font-semibold text-gray-900">
              Purchase
            </h2>

            <p class="mt-1 text-sm text-gray-600">
              Goods Receipt ini belum memiliki transaksi Purchase.
            </p>
          </div>

          <button
            type="button"
            class="rounded-lg bg-green-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-900 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
            @click="openCreatePurchase"
          >
            Buat Purchase
          </button>
        </div>
      </section>

      <section
        class="rounded-xl border border-gray-200 bg-white p-6"
      >
        <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Nomor Receipt
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ goodsReceipt.receiptNumber }}
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
              Diterima
            </p>

            <p class="mt-1 text-sm text-gray-900">
              {{ formatDate(goodsReceipt.receivedAt) }}
            </p>
          </div>
        </div>
      </section>

      <section
        class="overflow-x-auto rounded-xl border border-gray-200 bg-white"
      >
        <table class="min-w-full text-left text-sm">
          <thead class="border-b border-gray-200 bg-gray-50">
            <tr>
              <th class="px-4 py-3 font-medium text-gray-600">
                Produk
              </th>

              <th class="px-4 py-3 text-right font-medium text-gray-600">
                Ordered
              </th>

              <th class="px-4 py-3 text-right font-medium text-gray-600">
                Sebelumnya
              </th>

              <th class="px-4 py-3 text-right font-medium text-gray-600">
                Diterima
              </th>

              <th class="px-4 py-3 text-right font-medium text-gray-600">
                Diterima Baik
              </th>

              <th class="px-4 py-3 text-right font-medium text-gray-600">
                Ditolak
              </th>

              <th class="px-4 py-3 font-medium text-gray-600">
                Alasan Penolakan
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="item in goodsReceipt.items"
              :key="item.productId"
            >
              <td class="px-4 py-3">
                <p class="font-medium text-gray-900">
                  {{ item.name }}
                </p>

                <p class="mt-1 text-xs text-gray-500">
                  {{ item.productId }}
                </p>
              </td>

              <td class="px-4 py-3 text-right text-gray-700">
                {{ item.orderedQuantity }}
              </td>

              <td class="px-4 py-3 text-right text-gray-700">
                {{ item.previouslyReceivedQuantity }}
              </td>

              <td class="px-4 py-3 text-right font-medium text-gray-900">
                {{ item.receivedQuantity }}
              </td>

              <td class="px-4 py-3 text-right font-medium text-green-700">
                {{ item.acceptedQuantity }}
              </td>

              <td class="px-4 py-3 text-right font-medium text-red-700">
                {{ item.rejectedQuantity }}
              </td>

              <td class="px-4 py-3 text-gray-700">
                {{ item.rejectionReason || '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section
        class="rounded-xl border border-gray-200 bg-white p-6"
      >
        <h2 class="text-lg font-semibold text-gray-900">
          Catatan
        </h2>

        <p class="mt-2 text-sm text-gray-700">
          {{ goodsReceipt.notes || 'Tidak ada catatan.' }}
        </p>
      </section>
    </template>
  </section>
</template>