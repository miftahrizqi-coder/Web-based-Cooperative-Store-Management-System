<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPurchase } from '../../api/procurement'
import type {
  PaymentStatus,
  Purchase,
} from '../../types/procurement'
import { useAuth } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const purchase = ref<Purchase | null>(null)

const isLoading = ref(true)
const errorMessage = ref('')

const purchaseId = String(route.params.id)

const paymentStatusLabel: Record<PaymentStatus, string> = {
  UNPAID: 'Belum Dibayar',
  PARTIALLY_PAID: 'Sebagian Dibayar',
  PAID: 'Lunas',
  OVERDUE: 'Jatuh Tempo',
}

const paymentStatusClass: Record<PaymentStatus, string> = {
  UNPAID: 'bg-red-100 text-red-800',
  PARTIALLY_PAID: 'bg-yellow-100 text-yellow-800',
  PAID: 'bg-green-100 text-green-800',
  OVERDUE: 'bg-orange-100 text-orange-800',
}

const totalQuantity = computed(() => {
  return (
    purchase.value?.items.reduce(
      (total, item) => total + item.quantity,
      0,
    ) ?? 0
  )
})

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

async function loadPurchase() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  if (!purchaseId || purchaseId === 'undefined') {
    errorMessage.value =
      'Purchase ID tidak ditemukan.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    purchase.value = await getPurchase(
      token.value,
      purchaseId,
    )
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil detail Purchase.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadPurchase)
</script>

<template>
  <section class="space-y-6">
    <div>
      <button
        type="button"
        class="text-sm font-medium text-green-800 hover:underline focus:outline-none focus:ring-2 focus:ring-green-700"
        @click="router.push('/purchases')"
      >
        ← Kembali ke Purchase
      </button>

      <div
        class="mt-3 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
      >
        <div>
          <h1 class="text-2xl font-semibold text-gray-900">
            {{ purchase?.purchaseNumber || 'Detail Purchase' }}
          </h1>

          <p class="mt-1 text-sm text-gray-600">
            Detail transaksi pembelian berdasarkan Goods Receipt.
          </p>
        </div>

        <span
          v-if="purchase"
          class="inline-flex w-fit rounded-full px-3 py-1 text-sm font-medium"
          :class="paymentStatusClass[purchase.paymentStatus]"
        >
          {{ paymentStatusLabel[purchase.paymentStatus] }}
        </span>
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
        Purchase gagal dimuat
      </h2>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
        @click="loadPurchase"
      >
        Coba Lagi
      </button>
    </div>

    <template v-else-if="purchase">
      <section
        class="rounded-xl border border-gray-200 bg-white p-6"
      >
        <h2 class="text-lg font-semibold text-gray-900">
          Informasi Purchase
        </h2>

        <div class="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Purchase Number
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ purchase.purchaseNumber }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Supplier
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ purchase.supplierId }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Purchase Order
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ purchase.purchaseOrderId }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Goods Receipt
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ purchase.receiptId }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Dibuat Oleh
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ purchase.createdBy }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Dibuat Pada
            </p>

            <p class="mt-1 text-sm text-gray-900">
              {{ formatDate(purchase.createdAt) }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Jumlah Item
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ purchase.items.length }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Total Quantity
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ totalQuantity }}
            </p>
          </div>
        </div>
      </section>

      <section
        class="overflow-x-auto rounded-xl border border-gray-200 bg-white"
      >
        <div class="border-b border-gray-200 px-6 py-4">
          <h2 class="text-lg font-semibold text-gray-900">
            Item Purchase
          </h2>
        </div>

        <table class="min-w-full text-left text-sm">
          <thead class="border-b border-gray-200 bg-gray-50">
            <tr>
              <th class="px-4 py-3 font-medium text-gray-600">
                Produk
              </th>

              <th class="px-4 py-3 text-right font-medium text-gray-600">
                Quantity
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
              v-for="item in purchase.items"
              :key="item.productId"
            >
              <td class="px-4 py-4">
                <p class="font-medium text-gray-900">
                  {{ item.name }}
                </p>

                <p class="mt-1 text-xs text-gray-500">
                  {{ item.productId }}
                </p>
              </td>

              <td class="px-4 py-4 text-right text-gray-700">
                {{ item.quantity }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-right text-gray-700"
              >
                {{ formatCurrency(item.price) }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-right font-medium text-gray-900"
              >
                {{ formatCurrency(item.subtotal) }}
              </td>
            </tr>

            <tr v-if="purchase.items.length === 0">
              <td
                colspan="4"
                class="px-6 py-10 text-center text-sm text-gray-500"
              >
                Tidak ada item pada Purchase ini.
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
              {{ formatCurrency(purchase.subtotal) }}
            </span>
          </div>

          <div class="flex items-center justify-between gap-4">
            <span class="text-sm text-gray-600">
              Discount
            </span>

            <span class="font-medium text-gray-900">
              {{ formatCurrency(purchase.discount) }}
            </span>
          </div>

          <div
            class="border-t border-gray-200 pt-4"
          >
            <div class="flex items-center justify-between gap-4">
              <span class="text-base font-semibold text-gray-900">
                Total
              </span>

              <span class="text-xl font-bold text-gray-900">
                {{ formatCurrency(purchase.total) }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <section
        class="rounded-xl border border-gray-200 bg-white p-6"
      >
        <div
          class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <h2 class="text-lg font-semibold text-gray-900">
              Status Pembayaran
            </h2>

            <p class="mt-1 text-sm text-gray-600">
              Status saat ini:
              {{ paymentStatusLabel[purchase.paymentStatus] }}
            </p>
          </div>

          <span
            class="inline-flex w-fit rounded-full px-3 py-1 text-sm font-medium"
            :class="paymentStatusClass[purchase.paymentStatus]"
          >
            {{ paymentStatusLabel[purchase.paymentStatus] }}
          </span>
        </div>
      </section>
    </template>
  </section>
</template>