<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  getSupplierInvoices,
} from '../../api/procurement'
import type {
  SupplierInvoice,
  SupplierInvoicePaymentStatus,
} from '../../types/procurement'

const router = useRouter()

const invoices = ref<SupplierInvoice[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

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

const paymentStatusLabel = (
  status: SupplierInvoicePaymentStatus,
) => {
  const labels: Record<SupplierInvoicePaymentStatus, string> = {
    UNPAID: 'Belum Dibayar',
    PARTIALLY_PAID: 'Sebagian Dibayar',
    PAID: 'Lunas',
    OVERDUE: 'Jatuh Tempo',
  }

  return labels[status]
}

const paymentStatusClass = (
  status: SupplierInvoicePaymentStatus,
) => {
  const classes: Record<SupplierInvoicePaymentStatus, string> = {
    UNPAID:
      'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
    PARTIALLY_PAID:
      'bg-blue-50 text-blue-700 ring-1 ring-blue-200',
    PAID:
      'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
    OVERDUE:
      'bg-red-50 text-red-700 ring-1 ring-red-200',
  }

  return classes[status]
}

const unpaidCount = computed(
  () =>
    invoices.value.filter(
      (invoice) =>
        invoice.paymentStatus === 'UNPAID' ||
        invoice.paymentStatus === 'OVERDUE',
    ).length,
)

const outstandingTotal = computed(() =>
  invoices.value
    .filter(
      (invoice) =>
        invoice.paymentStatus !== 'PAID',
    )
    .reduce(
      (total, invoice) => total + invoice.total,
      0,
    ),
)

const loadInvoices = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const accessToken = localStorage.getItem('access_token')

    if (!accessToken) {
      throw new Error('Sesi login tidak ditemukan.')
    }

    invoices.value = await getSupplierInvoices(accessToken)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data supplier invoice.'
  } finally {
    isLoading.value = false
  }
}

const openDetail = (invoiceId: string) => {
  router.push(`/supplier-invoices/${invoiceId}`)
}

const createInvoice = () => {
  router.push('/supplier-invoices/create')
}

onMounted(loadInvoices)
</script>

<template>
  <section class="space-y-6">
    <div
      class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
    >
      <div>
        <p
          class="text-sm font-medium text-emerald-700"
        >
          Procurement
        </p>

        <h1
          class="mt-1 text-2xl font-semibold text-slate-900"
        >
          Supplier Invoice
        </h1>

        <p class="mt-1 text-sm text-slate-500">
          Kelola invoice supplier yang berasal dari
          transaksi purchase.
        </p>
      </div>

      <button
        type="button"
        class="inline-flex min-h-11 items-center justify-center rounded-lg bg-emerald-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
        @click="createInvoice"
      >
        Buat Supplier Invoice
      </button>
    </div>

    <div
      class="grid gap-4 sm:grid-cols-2"
    >
      <div
        class="rounded-xl border border-slate-200 bg-white p-5"
      >
        <p class="text-sm text-slate-500">
          Total Invoice
        </p>

        <p
          class="mt-2 text-2xl font-semibold text-slate-900"
        >
          {{ invoices.length }}
        </p>
      </div>

      <div
        class="rounded-xl border border-slate-200 bg-white p-5"
      >
        <p class="text-sm text-slate-500">
          Invoice Belum Lunas
        </p>

        <p
          class="mt-2 text-2xl font-semibold text-slate-900"
        >
          {{ unpaidCount }}
        </p>

        <p class="mt-1 text-sm text-slate-500">
          Nilai invoice belum lunas:
          {{ formatCurrency(outstandingTotal) }}
        </p>
      </div>
    </div>

    <div
      v-if="isLoading"
      class="rounded-xl border border-slate-200 bg-white p-6"
    >
      <div class="animate-pulse space-y-4">
        <div
          class="h-5 w-48 rounded bg-slate-200"
        />

        <div
          class="h-10 w-full rounded bg-slate-100"
        />

        <div
          class="h-10 w-full rounded bg-slate-100"
        />

        <div
          class="h-10 w-full rounded bg-slate-100"
        />
      </div>
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
    >
      <h2
        class="font-semibold text-red-800"
      >
        Gagal memuat supplier invoice
      </h2>

      <p
        class="mt-1 text-sm text-red-700"
      >
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-4 min-h-11 rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800"
        @click="loadInvoices"
      >
        Coba Lagi
      </button>
    </div>

    <div
      v-else-if="invoices.length === 0"
      class="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center"
    >
      <h2
        class="text-lg font-semibold text-slate-900"
      >
        Belum ada supplier invoice
      </h2>

      <p
        class="mx-auto mt-2 max-w-md text-sm text-slate-500"
      >
        Supplier invoice dibuat berdasarkan purchase
        yang sudah tersedia.
      </p>

      <button
        type="button"
        class="mt-5 min-h-11 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        @click="createInvoice"
      >
        Buat Supplier Invoice
      </button>
    </div>

    <div
      v-else
      class="overflow-hidden rounded-xl border border-slate-200 bg-white"
    >
      <div
        class="overflow-x-auto"
      >
        <table
          class="min-w-[900px] w-full text-left text-sm"
        >
          <thead
            class="border-b border-slate-200 bg-slate-50"
          >
            <tr>
              <th
                class="px-4 py-3 font-semibold text-slate-700"
              >
                Invoice
              </th>

              <th
                class="px-4 py-3 font-semibold text-slate-700"
              >
                Supplier
              </th>

              <th
                class="px-4 py-3 font-semibold text-slate-700"
              >
                Purchase
              </th>

              <th
                class="px-4 py-3 font-semibold text-slate-700"
              >
                Tanggal
              </th>

              <th
                class="px-4 py-3 text-right font-semibold text-slate-700"
              >
                Total
              </th>

              <th
                class="px-4 py-3 font-semibold text-slate-700"
              >
                Status
              </th>

              <th
                class="px-4 py-3 text-right font-semibold text-slate-700"
              >
                Aksi
              </th>
            </tr>
          </thead>

          <tbody
            class="divide-y divide-slate-100"
          >
            <tr
              v-for="invoice in invoices"
              :key="invoice.id"
              class="hover:bg-slate-50"
            >
              <td class="px-4 py-4">
                <p
                  class="font-medium text-slate-900"
                >
                  {{ invoice.invoiceNumber }}
                </p>

                <p
                  class="mt-1 text-xs text-slate-500"
                >
                  {{ invoice.id }}
                </p>
              </td>

              <td
                class="px-4 py-4 text-slate-700"
              >
                {{ invoice.supplierId }}
              </td>

              <td
                class="px-4 py-4 text-slate-700"
              >
                {{ invoice.purchaseId }}
              </td>

              <td
                class="px-4 py-4 text-slate-700"
              >
                {{ formatDate(invoice.invoiceDate) }}
              </td>

              <td
                class="px-4 py-4 text-right font-medium text-slate-900"
              >
                {{ formatCurrency(invoice.total) }}
              </td>

              <td class="px-4 py-4">
                <span
                  class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium"
                  :class="
                    paymentStatusClass(
                      invoice.paymentStatus,
                    )
                  "
                >
                  {{
                    paymentStatusLabel(
                      invoice.paymentStatus,
                    )
                  }}
                </span>
              </td>

              <td
                class="px-4 py-4 text-right"
              >
                <button
                  type="button"
                  class="min-h-10 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  @click="openDetail(invoice.id)"
                >
                  Detail
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>