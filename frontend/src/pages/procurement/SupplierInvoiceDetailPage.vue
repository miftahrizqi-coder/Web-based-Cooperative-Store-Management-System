<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSupplierInvoice } from '../../api/procurement'
import type {
  SupplierInvoice,
  SupplierInvoicePaymentStatus,
} from '../../types/procurement'

const route = useRoute()
const router = useRouter()

const invoice = ref<SupplierInvoice | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')

const invoiceId = computed(() =>
  typeof route.params.id === 'string'
    ? route.params.id
    : '',
)

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)

const formatDate = (value: string | null) => {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
  }).format(new Date(value))
}

const paymentStatusLabel = (
  status: SupplierInvoicePaymentStatus,
) => {
  const labels: Record<
    SupplierInvoicePaymentStatus,
    string
  > = {
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
  const classes: Record<
    SupplierInvoicePaymentStatus,
    string
  > = {
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

const loadInvoice = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const accessToken = localStorage.getItem(
      'access_token',
    )

    if (!accessToken) {
      throw new Error(
        'Sesi login tidak ditemukan.',
      )
    }

    if (!invoiceId.value) {
      throw new Error(
        'ID supplier invoice tidak ditemukan.',
      )
    }

    invoice.value = await getSupplierInvoice(
      accessToken,
      invoiceId.value,
    )
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil detail supplier invoice.'
  } finally {
    isLoading.value = false
  }
}

const backToList = () => {
  router.push('/supplier-invoices')
}

const openPurchaseOrder = () => {
  if (!invoice.value) {
    return
  }

  router.push(
    `/purchase-orders/${invoice.value.purchaseOrderId}`,
  )
}

const openGoodsReceipt = () => {
  if (!invoice.value) {
    return
  }

  router.push(
    `/goods-receipts/${invoice.value.receiptId}`,
  )
}

onMounted(loadInvoice)
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
          Detail Supplier Invoice
        </h1>

        <p class="mt-1 text-sm text-slate-500">
          Detail invoice dan referensi transaksi supplier.
        </p>
      </div>

      <button
        type="button"
        class="min-h-11 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        @click="backToList"
      >
        Kembali
      </button>
    </div>

    <div
      v-if="isLoading"
      class="space-y-6"
    >
      <div
        class="animate-pulse rounded-xl border border-slate-200 bg-white p-6"
      >
        <div
          class="h-6 w-56 rounded bg-slate-200"
        />

        <div
          class="mt-5 grid gap-4 sm:grid-cols-2"
        >
          <div
            class="h-12 rounded bg-slate-100"
          />

          <div
            class="h-12 rounded bg-slate-100"
          />

          <div
            class="h-12 rounded bg-slate-100"
          />

          <div
            class="h-12 rounded bg-slate-100"
          />
        </div>
      </div>

      <div
        class="animate-pulse rounded-xl border border-slate-200 bg-white p-6"
      >
        <div
          class="h-5 w-40 rounded bg-slate-200"
        />

        <div
          class="mt-5 space-y-3"
        >
          <div
            class="h-5 rounded bg-slate-100"
          />

          <div
            class="h-5 rounded bg-slate-100"
          />

          <div
            class="h-5 rounded bg-slate-100"
          />
        </div>
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
        @click="loadInvoice"
      >
        Coba Lagi
      </button>
    </div>

    <template v-else-if="invoice">
      <div
        class="rounded-xl border border-slate-200 bg-white p-6"
      >
        <div
          class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
        >
          <div>
            <p
              class="text-sm text-slate-500"
            >
              Nomor Invoice
            </p>

            <h2
              class="mt-1 text-xl font-semibold text-slate-900"
            >
              {{ invoice.invoiceNumber }}
            </h2>
          </div>

          <span
            class="inline-flex w-fit rounded-full px-3 py-1.5 text-sm font-medium"
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
        </div>

        <div
          class="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4"
        >
          <div>
            <p class="text-xs text-slate-500">
              Supplier
            </p>

            <p
              class="mt-1 font-medium text-slate-900"
            >
              {{ invoice.supplierId }}
            </p>
          </div>

          <div>
            <p class="text-xs text-slate-500">
              Tanggal Invoice
            </p>

            <p
              class="mt-1 font-medium text-slate-900"
            >
              {{ formatDate(invoice.invoiceDate) }}
            </p>
          </div>

          <div>
            <p class="text-xs text-slate-500">
              Jatuh Tempo
            </p>

            <p
              class="mt-1 font-medium text-slate-900"
            >
              {{ formatDate(invoice.dueDate) }}
            </p>
          </div>

          <div>
            <p class="text-xs text-slate-500">
              Status Pembayaran
            </p>

            <p
              class="mt-1 font-medium text-slate-900"
            >
              {{
                paymentStatusLabel(
                  invoice.paymentStatus,
                )
              }}
            </p>
          </div>
        </div>
      </div>

      <div
        class="rounded-xl border border-slate-200 bg-white p-6"
      >
        <h2
          class="text-lg font-semibold text-slate-900"
        >
          Referensi Transaksi
        </h2>

        <div
          class="mt-5 grid gap-4 md:grid-cols-2"
        >
          <div
            class="rounded-lg border border-slate-200 p-4"
          >
            <p class="text-xs text-slate-500">
              Purchase Order
            </p>

            <p
              class="mt-1 break-all font-medium text-slate-900"
            >
              {{ invoice.purchaseOrderId }}
            </p>

            <button
              type="button"
              class="mt-3 min-h-10 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              @click="openPurchaseOrder"
            >
              Lihat Purchase Order
            </button>
          </div>

          <div
            class="rounded-lg border border-slate-200 p-4"
          >
            <p class="text-xs text-slate-500">
              Goods Receipt
            </p>

            <p
              class="mt-1 break-all font-medium text-slate-900"
            >
              {{ invoice.receiptId }}
            </p>

            <button
              type="button"
              class="mt-3 min-h-10 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              @click="openGoodsReceipt"
            >
              Lihat Goods Receipt
            </button>
          </div>
        </div>
      </div>

      <div
        class="rounded-xl border border-slate-200 bg-white p-6"
      >
        <h2
          class="text-lg font-semibold text-slate-900"
        >
          Ringkasan Invoice
        </h2>

        <div
          class="mt-5 ml-auto max-w-md space-y-3"
        >
          <div
            class="flex items-center justify-between gap-4 text-sm"
          >
            <span class="text-slate-500">
              Subtotal
            </span>

            <span
              class="font-medium text-slate-900"
            >
              {{ formatCurrency(invoice.subtotal) }}
            </span>
          </div>

          <div
            class="flex items-center justify-between gap-4 text-sm"
          >
            <span class="text-slate-500">
              Tax
            </span>

            <span
              class="font-medium text-slate-900"
            >
              {{ formatCurrency(invoice.tax) }}
            </span>
          </div>

          <div
            class="flex items-center justify-between gap-4 text-sm"
          >
            <span class="text-slate-500">
              Shipping Cost
            </span>

            <span
              class="font-medium text-slate-900"
            >
              {{
                formatCurrency(
                  invoice.shipping,
                )
              }}
            </span>
          </div>

          <div
            class="border-t border-slate-200 pt-4"
          >
            <div
              class="flex items-center justify-between gap-4"
            >
              <span
                class="font-semibold text-slate-900"
              >
                Total
              </span>

              <span
                class="text-xl font-semibold text-slate-900"
              >
                {{ formatCurrency(invoice.total) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>