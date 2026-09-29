<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getPurchases } from '../../api/procurement'
import type { PaymentStatus, Purchase } from '../../types/procurement'

const router = useRouter()

const purchases = ref<Purchase[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

const accessToken = localStorage.getItem('access_token')

const formatDate = (value: string) => {
  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

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

const totalPurchase = computed(() => {
  return purchases.value.reduce((total, purchase) => {
    return total + purchase.total
  }, 0)
})

const loadPurchases = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    if (!accessToken) {
      throw new Error('Sesi login tidak ditemukan.')
    }

    purchases.value = await getPurchases(accessToken)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data purchase.'
  } finally {
    isLoading.value = false
  }
}

const openDetail = (purchaseId: string) => {
  router.push(`/purchases/${purchaseId}`)
}

onMounted(loadPurchases)
</script>

<template>
  <section class="space-y-6">
    <div
      class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <h1 class="text-2xl font-bold text-slate-900">
          Purchase
        </h1>
        <p class="mt-1 text-sm text-slate-600">
          Daftar transaksi pembelian yang terbentuk dari penerimaan barang.
        </p>
      </div>

      <div
        v-if="!isLoading && !errorMessage"
        class="rounded-lg border border-slate-200 bg-white px-4 py-3"
      >
        <p class="text-xs font-medium uppercase tracking-wide text-slate-500">
          Total Purchase
        </p>
        <p class="mt-1 text-lg font-semibold text-slate-900">
          {{ purchases.length }}
        </p>
      </div>
    </div>

    <div
      v-if="isLoading"
      class="overflow-hidden rounded-xl border border-slate-200 bg-white"
    >
      <div class="animate-pulse space-y-4 p-6">
        <div class="h-5 w-48 rounded bg-slate-200"></div>
        <div class="h-10 w-full rounded bg-slate-100"></div>
        <div class="h-10 w-full rounded bg-slate-100"></div>
        <div class="h-10 w-full rounded bg-slate-100"></div>
        <div class="h-10 w-full rounded bg-slate-100"></div>
      </div>
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
    >
      <h2 class="text-base font-semibold text-red-900">
        Gagal memuat Purchase
      </h2>

      <p class="mt-2 text-sm text-red-800">
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg bg-red-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-red-900 focus:outline-none focus:ring-2 focus:ring-red-700 focus:ring-offset-2"
        @click="loadPurchases"
      >
        Coba Lagi
      </button>
    </div>

    <div
      v-else-if="purchases.length === 0"
      class="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center"
    >
      <h2 class="text-base font-semibold text-slate-900">
        Belum ada Purchase
      </h2>

      <p class="mx-auto mt-2 max-w-md text-sm text-slate-600">
        Purchase akan tersedia setelah Goods Receipt yang valid diproses
        menjadi transaksi pembelian.
      </p>
    </div>

    <div v-else class="space-y-4">
      <div
        class="grid gap-4 sm:grid-cols-2"
      >
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <p class="text-xs font-medium uppercase tracking-wide text-slate-500">
            Jumlah Purchase
          </p>
          <p class="mt-1 text-xl font-semibold text-slate-900">
            {{ purchases.length }}
          </p>
        </div>

        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <p class="text-xs font-medium uppercase tracking-wide text-slate-500">
            Nilai Purchase
          </p>
          <p class="mt-1 text-xl font-semibold text-slate-900">
            {{ formatCurrency(totalPurchase) }}
          </p>
        </div>
      </div>

      <div
        class="overflow-hidden rounded-xl border border-slate-200 bg-white"
      >
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-200">
            <thead class="bg-slate-50">
              <tr>
                <th
                  scope="col"
                  class="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600"
                >
                  Purchase
                </th>

                <th
                  scope="col"
                  class="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600"
                >
                  Supplier
                </th>

                <th
                  scope="col"
                  class="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600"
                >
                  PO
                </th>

                <th
                  scope="col"
                  class="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600"
                >
                  Receipt
                </th>

                <th
                  scope="col"
                  class="whitespace-nowrap px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-600"
                >
                  Total
                </th>

                <th
                  scope="col"
                  class="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600"
                >
                  Pembayaran
                </th>

                <th
                  scope="col"
                  class="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600"
                >
                  Dibuat
                </th>

                <th
                  scope="col"
                  class="whitespace-nowrap px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-600"
                >
                  Aksi
                </th>
              </tr>
            </thead>

            <tbody class="divide-y divide-slate-200 bg-white">
              <tr
                v-for="purchase in purchases"
                :key="purchase.id"
                class="hover:bg-slate-50"
              >
                <td class="whitespace-nowrap px-4 py-4">
                  <div class="font-medium text-slate-900">
                    {{ purchase.purchaseNumber }}
                  </div>

                  <div class="mt-1 text-xs text-slate-500">
                    {{ purchase.items.length }} item
                  </div>
                </td>

                <td class="whitespace-nowrap px-4 py-4 text-sm text-slate-700">
                  {{ purchase.supplierId }}
                </td>

                <td class="whitespace-nowrap px-4 py-4 text-sm text-slate-700">
                  {{ purchase.purchaseOrderId }}
                </td>

                <td class="whitespace-nowrap px-4 py-4 text-sm text-slate-700">
                  {{ purchase.receiptId }}
                </td>

                <td
                  class="whitespace-nowrap px-4 py-4 text-right text-sm font-semibold text-slate-900"
                >
                  {{ formatCurrency(purchase.total) }}
                </td>

                <td class="whitespace-nowrap px-4 py-4">
                  <span
                    class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium"
                    :class="paymentStatusClass[purchase.paymentStatus]"
                  >
                    {{ paymentStatusLabel[purchase.paymentStatus] }}
                  </span>
                </td>

                <td class="whitespace-nowrap px-4 py-4 text-sm text-slate-600">
                  {{ formatDate(purchase.createdAt) }}
                </td>

                <td class="whitespace-nowrap px-4 py-4 text-right">
                  <button
                    type="button"
                    class="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2"
                    @click="openDetail(purchase.id)"
                  >
                    Detail
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>
</template>