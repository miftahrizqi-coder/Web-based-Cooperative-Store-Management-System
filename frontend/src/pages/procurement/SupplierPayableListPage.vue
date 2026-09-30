<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getSupplierPayables } from '../../api/procurement'
import type {
  PaymentStatus,
  SupplierPayable,
} from '../../types/procurement'

const router = useRouter()

const accessToken = localStorage.getItem('access_token')

const payables = ref<SupplierPayable[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

const paymentStatusLabel: Record<PaymentStatus, string> = {
  UNPAID: 'Belum Dibayar',
  PARTIALLY_PAID: 'Sebagian Dibayar',
  PAID: 'Lunas',
  OVERDUE: 'Jatuh Tempo',
}

const paymentStatusClass: Record<PaymentStatus, string> = {
  UNPAID: 'bg-red-100 text-red-700',
  PARTIALLY_PAID: 'bg-yellow-100 text-yellow-700',
  PAID: 'bg-green-100 text-green-700',
  OVERDUE: 'bg-orange-100 text-orange-700',
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

const totalPayable = computed(() =>
  payables.value.reduce(
    (total, payable) => total + payable.total,
    0,
  ),
)

const totalPaid = computed(() =>
  payables.value.reduce(
    (total, payable) => total + payable.paid,
    0,
  ),
)

const totalOutstanding = computed(() =>
  payables.value.reduce(
    (total, payable) => total + payable.outstanding,
    0,
  ),
)

const unpaidCount = computed(
  () =>
    payables.value.filter(
      (payable) => payable.paymentStatus !== 'PAID',
    ).length,
)

async function loadPayables() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    if (!accessToken) {
      throw new Error('Sesi login tidak ditemukan.')
    }

    payables.value = await getSupplierPayables(accessToken)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data hutang supplier.'
  } finally {
    isLoading.value = false
  }
}

function openInvoice(invoiceId: string) {
  router.push(`/supplier-invoices/${invoiceId}`)
}

onMounted(loadPayables)
</script>

<template>
  <div class="space-y-6">
    <div
      class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <h1 class="text-2xl font-semibold text-slate-900">
          Hutang Supplier
        </h1>
        <p class="mt-1 text-sm text-slate-500">
          Ringkasan hutang supplier berdasarkan invoice.
        </p>
      </div>

      <button
        type="button"
        class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        @click="loadPayables"
      >
        Refresh
      </button>
    </div>

    <div
      v-if="isLoading"
      class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
    >
      <div
        v-for="item in 4"
        :key="item"
        class="h-24 animate-pulse rounded-xl bg-slate-100"
      />
    </div>

    <div
      v-else
      class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
    >
      <div class="rounded-xl border border-slate-200 bg-white p-5">
        <p class="text-sm text-slate-500">
          Total Invoice
        </p>
        <p class="mt-2 text-xl font-semibold text-slate-900">
          {{ formatCurrency(totalPayable) }}
        </p>
      </div>

      <div class="rounded-xl border border-slate-200 bg-white p-5">
        <p class="text-sm text-slate-500">
          Total Dibayar
        </p>
        <p class="mt-2 text-xl font-semibold text-slate-900">
          {{ formatCurrency(totalPaid) }}
        </p>
      </div>

      <div class="rounded-xl border border-slate-200 bg-white p-5">
        <p class="text-sm text-slate-500">
          Outstanding
        </p>
        <p class="mt-2 text-xl font-semibold text-slate-900">
          {{ formatCurrency(totalOutstanding) }}
        </p>
      </div>

      <div class="rounded-xl border border-slate-200 bg-white p-5">
        <p class="text-sm text-slate-500">
          Invoice Belum Lunas
        </p>
        <p class="mt-2 text-xl font-semibold text-slate-900">
          {{ unpaidCount }}
        </p>
      </div>
    </div>

    <div
      v-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-4"
    >
      <p class="font-medium text-red-800">
        Gagal memuat hutang supplier
      </p>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-3 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        @click="loadPayables"
      >
        Coba Lagi
      </button>
    </div>

    <div
      v-else-if="!isLoading && payables.length === 0"
      class="rounded-xl border border-slate-200 bg-white p-10 text-center"
    >
      <h2 class="text-lg font-semibold text-slate-900">
        Belum ada hutang supplier
      </h2>

      <p class="mt-2 text-sm text-slate-500">
        Hutang akan muncul setelah supplier invoice dibuat.
      </p>
    </div>

    <div
      v-else-if="payables.length > 0"
      class="overflow-hidden rounded-xl border border-slate-200 bg-white"
    >
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200">
          <thead class="bg-slate-50">
            <tr>
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
                Total
              </th>

              <th
                class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Dibayar
              </th>

              <th
                class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Outstanding
              </th>

              <th
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Jatuh Tempo
              </th>

              <th
                class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Status
              </th>

              <th
                class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Aksi
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-slate-200">
            <tr
              v-for="payable in payables"
              :key="payable.invoiceId"
              class="hover:bg-slate-50"
            >
              <td class="whitespace-nowrap px-4 py-4">
                <button
                  type="button"
                  class="font-medium text-blue-600 hover:text-blue-800 hover:underline"
                  @click="openInvoice(payable.invoiceId)"
                >
                  {{ payable.invoiceNumber }}
                </button>
              </td>

              <td class="whitespace-nowrap px-4 py-4 text-sm text-slate-700">
                {{ payable.supplierId }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-right text-sm text-slate-700"
              >
                {{ formatCurrency(payable.total) }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-right text-sm text-slate-700"
              >
                {{ formatCurrency(payable.paid) }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-4 text-right text-sm font-medium text-slate-900"
              >
                {{ formatCurrency(payable.outstanding) }}
              </td>

              <td class="whitespace-nowrap px-4 py-4 text-sm text-slate-700">
                {{ formatDate(payable.dueDate) }}
              </td>

              <td class="whitespace-nowrap px-4 py-4">
                <span
                  class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium"
                  :class="paymentStatusClass[payable.paymentStatus]"
                >
                  {{ paymentStatusLabel[payable.paymentStatus] }}
                </span>
              </td>

              <td class="whitespace-nowrap px-4 py-4 text-right">
                <button
                  type="button"
                  class="text-sm font-medium text-blue-600 hover:text-blue-800"
                  @click="openInvoice(payable.invoiceId)"
                >
                  Lihat Invoice
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>