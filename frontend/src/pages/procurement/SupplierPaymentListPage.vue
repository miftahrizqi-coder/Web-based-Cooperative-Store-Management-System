<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getSupplierPayments } from '../../api/procurement'
import type {
  SupplierPayment,
  SupplierPaymentMethod,
} from '../../types/procurement'

const router = useRouter()

const accessToken = localStorage.getItem('access_token')

const payments = ref<SupplierPayment[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

const methodLabel: Record<SupplierPaymentMethod, string> = {
  CASH: 'Tunai',
  BANK_TRANSFER: 'Transfer Bank',
  GIRO: 'Giro',
  OTHER: 'Lainnya',
}

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)

const formatDate = (value: string) =>
  new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
  }).format(new Date(value))

const totalPaid = computed(() =>
  payments.value.reduce(
    (total, payment) => total + payment.amount,
    0,
  ),
)

async function loadPayments() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    if (!accessToken) {
      throw new Error('Sesi login tidak ditemukan.')
    }

    payments.value = await getSupplierPayments(accessToken)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil daftar pembayaran supplier.'
  } finally {
    isLoading.value = false
  }
}

function openInvoice(invoiceId: string) {
  router.push(`/supplier-invoices/${invoiceId}`)
}

onMounted(loadPayments)
</script>

<template>
  <div class="space-y-6">
    <div
      class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <h1 class="text-2xl font-semibold text-slate-900">
          Pembayaran Supplier
        </h1>

        <p class="mt-1 text-sm text-slate-500">
          Riwayat pembayaran invoice supplier.
        </p>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          @click="loadPayments"
        >
          Refresh
        </button>

        <button
          type="button"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          @click="router.push('/supplier-payments/create')"
        >
          Catat Pembayaran
        </button>
      </div>
    </div>

    <div
      v-if="isLoading"
      class="grid gap-4 sm:grid-cols-2"
    >
      <div
        v-for="item in 2"
        :key="item"
        class="h-24 animate-pulse rounded-xl bg-slate-100"
      />
    </div>

    <div
      v-else
      class="grid gap-4 sm:grid-cols-2"
    >
      <div class="rounded-xl border border-slate-200 bg-white p-5">
        <p class="text-sm text-slate-500">
          Total Pembayaran
        </p>

        <p class="mt-2 text-xl font-semibold text-slate-900">
          {{ formatCurrency(totalPaid) }}
        </p>
      </div>

      <div class="rounded-xl border border-slate-200 bg-white p-5">
        <p class="text-sm text-slate-500">
          Jumlah Transaksi
        </p>

        <p class="mt-2 text-xl font-semibold text-slate-900">
          {{ payments.length }}
        </p>
      </div>
    </div>

    <div
      v-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-4"
    >
      <p class="font-medium text-red-800">
        Gagal memuat pembayaran supplier
      </p>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-3 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        @click="loadPayments"
      >
        Coba Lagi
      </button>
    </div>

    <div
      v-else-if="!isLoading && payments.length === 0"
      class="rounded-xl border border-slate-200 bg-white p-10 text-center"
    >
      <h2 class="text-lg font-semibold text-slate-900">
        Belum ada pembayaran supplier
      </h2>

      <p class="mt-2 text-sm text-slate-500">
        Pembayaran supplier yang sudah dicatat akan muncul di sini.
      </p>
    </div>

    <div
      v-else-if="payments.length > 0"
      class="overflow-hidden rounded-xl border border-slate-200 bg-white"
    >
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200">
          <thead class="bg-slate-50">
            <tr>
              <th
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Nomor Pembayaran
              </th>

              <th
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Invoice
              </th>

              <th
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Supplier
              </th>

              <th
                class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Jumlah
              </th>

              <th
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Metode
              </th>

              <th
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Tanggal
              </th>

              <th
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Referensi
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-slate-200">
            <tr
              v-for="payment in payments"
              :key="payment.id"
              class="hover:bg-slate-50"
            >
              <td class="whitespace-nowrap px-4 py-4 text-sm font-medium text-slate-900">
                {{ payment.paymentNumber }}
              </td>

              <td class="whitespace-nowrap px-4 py-4">
                <button
                  type="button"
                  class="text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline"
                  @click="openInvoice(payment.invoiceId)"
                >
                  {{ payment.invoiceId }}
                </button>
              </td>

              <td class="whitespace-nowrap px-4 py-4 text-sm text-slate-700">
                {{ payment.supplierId }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-right text-sm font-medium text-slate-900"
              >
                {{ formatCurrency(payment.amount) }}
              </td>

              <td class="whitespace-nowrap px-4 py-4 text-sm text-slate-700">
                {{ methodLabel[payment.method] }}
              </td>

              <td class="whitespace-nowrap px-4 py-4 text-sm text-slate-700">
                {{ formatDate(payment.paymentDate) }}
              </td>

              <td class="whitespace-nowrap px-4 py-4 text-sm text-slate-700">
                {{ payment.referenceNumber || '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>