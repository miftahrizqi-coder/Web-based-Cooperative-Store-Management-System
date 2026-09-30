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
      'border-[#C47A00]/20 bg-[#FFF8E8] text-[#8A5A00]',
    PARTIALLY_PAID:
      'border-[#2874A6]/20 bg-[#F3F8FB] text-[#2874A6]',
    PAID:
      'border-[#176B4D]/20 bg-[#F0F8F5] text-[#176B4D]',
    OVERDUE:
      'border-[#C0392B]/20 bg-[#FEF4F3] text-[#C0392B]',
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
  <section
    class="mx-auto w-full max-w-7xl space-y-6"
  >
    <!-- Breadcrumb -->
    <nav
      aria-label="Breadcrumb"
      class="text-sm text-[#6B756F]"
    >
      <ol class="flex flex-wrap items-center gap-2">
        <li>
          <span>Procurement</span>
        </li>

        <li aria-hidden="true">
          /
        </li>

        <li>
          <button
            type="button"
            class="font-medium text-[#46514B] underline-offset-2 hover:text-[#176B4D] hover:underline focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
            @click="backToList"
          >
            Supplier Invoice
          </button>
        </li>

        <li aria-hidden="true">
          /
        </li>

        <li
          class="font-medium text-[#17201C]"
          aria-current="page"
        >
          Detail
        </li>
      </ol>
    </nav>

    <!-- Page Header -->
    <header
      class="flex flex-col gap-4 border-b border-[#D6DDD9] pb-5 sm:flex-row sm:items-end sm:justify-between"
    >
      <div>
        <p
          class="text-sm font-semibold uppercase tracking-wide text-[#176B4D]"
        >
          Procurement
        </p>

        <h1
          class="mt-1 text-2xl font-semibold tracking-tight text-[#17201C] sm:text-3xl"
        >
          Detail Supplier Invoice
        </h1>

        <p
          class="mt-2 max-w-2xl text-sm leading-6 text-[#6B756F]"
        >
          Detail invoice, status pembayaran, referensi transaksi,
          dan ringkasan nilai invoice supplier.
        </p>
      </div>

      <button
        type="button"
        class="inline-flex min-h-11 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
        @click="backToList"
      >
        Kembali
      </button>
    </header>

    <!-- Loading -->
    <div
      v-if="isLoading"
      class="space-y-6"
      aria-live="polite"
      aria-busy="true"
    >
      <section
        class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
      >
        <div
          class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6"
        >
          <div
            class="h-5 w-32 animate-pulse rounded bg-[#E7ECE9]"
          />

          <div
            class="mt-3 h-7 w-64 max-w-full animate-pulse rounded bg-[#F1F4F2]"
          />
        </div>

        <div
          class="grid gap-5 p-5 sm:grid-cols-2 lg:grid-cols-4 sm:p-6"
        >
          <div
            v-for="item in 4"
            :key="item"
            class="space-y-2"
          >
            <div
              class="h-3 w-20 animate-pulse rounded bg-[#E7ECE9]"
            />

            <div
              class="h-5 w-32 animate-pulse rounded bg-[#F1F4F2]"
            />
          </div>
        </div>
      </section>

      <section
        class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
      >
        <div
          class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6"
        >
          <div
            class="h-5 w-44 animate-pulse rounded bg-[#E7ECE9]"
          />
        </div>

        <div
          class="grid gap-5 p-5 md:grid-cols-2 sm:p-6"
        >
          <div
            v-for="item in 2"
            :key="item"
            class="h-32 animate-pulse rounded-lg bg-[#F1F4F2]"
          />
        </div>
      </section>

      <section
        class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white p-5 sm:p-6"
      >
        <div
          class="h-5 w-40 animate-pulse rounded bg-[#E7ECE9]"
        />

        <div
          class="ml-auto mt-6 max-w-md space-y-4"
        >
          <div
            v-for="item in 4"
            :key="item"
            class="h-5 animate-pulse rounded bg-[#F1F4F2]"
          />
        </div>
      </section>
    </div>

    <!-- Error -->
    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-[#C0392B]/25 bg-[#FEF4F3] p-5 sm:p-6"
      role="alert"
    >
      <div class="flex gap-3">
        <div
          class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#C0392B]/10 text-[#C0392B]"
          aria-hidden="true"
        >
          !
        </div>

        <div class="min-w-0">
          <h2
            class="font-semibold text-[#8E2B22]"
          >
            Gagal memuat supplier invoice
          </h2>

          <p
            class="mt-1 text-sm leading-6 text-[#A33A2E]"
          >
            {{ errorMessage }}
          </p>

          <div class="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              class="inline-flex min-h-11 items-center justify-center rounded-lg bg-[#C0392B] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#A93226] focus:outline-none focus:ring-2 focus:ring-[#C0392B]/30"
              @click="loadInvoice"
            >
              Coba Lagi
            </button>

            <button
              type="button"
              class="inline-flex min-h-11 items-center justify-center rounded-lg border border-[#C0392B]/20 bg-white px-4 py-2 text-sm font-semibold text-[#8E2B22] transition hover:bg-[#FEF4F3] focus:outline-none focus:ring-2 focus:ring-[#C0392B]/30"
              @click="backToList"
            >
              Kembali
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Detail -->
    <template v-else-if="invoice">
      <!-- Status + Primary Information -->
      <section
        class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
      >
        <div
          class="border-b border-[#D6DDD9] px-5 py-5 sm:px-6"
        >
          <div
            class="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between"
          >
            <div class="min-w-0">
              <p
                class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
              >
                Nomor Invoice
              </p>

              <h2
                class="mt-1 break-all text-xl font-semibold tracking-tight text-[#17201C] sm:text-2xl"
              >
                {{ invoice.invoiceNumber }}
              </h2>
            </div>

            <span
              class="inline-flex w-fit shrink-0 items-center rounded-full border px-3 py-1.5 text-sm font-semibold"
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
        </div>

        <div
          class="grid gap-x-6 gap-y-5 p-5 sm:grid-cols-2 lg:grid-cols-4 sm:p-6"
        >
          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-[#6B756F]"
            >
              Supplier
            </p>

            <p
              class="mt-1 break-all font-medium text-[#17201C]"
            >
              {{ invoice.supplierId }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-[#6B756F]"
            >
              Tanggal Invoice
            </p>

            <p
              class="mt-1 font-medium text-[#17201C]"
            >
              {{ formatDate(invoice.invoiceDate) }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-[#6B756F]"
            >
              Jatuh Tempo
            </p>

            <p
              class="mt-1 font-medium text-[#17201C]"
            >
              {{ formatDate(invoice.dueDate) }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-[#6B756F]"
            >
              Status Pembayaran
            </p>

            <p
              class="mt-1 font-medium text-[#17201C]"
            >
              {{
                paymentStatusLabel(
                  invoice.paymentStatus,
                )
              }}
            </p>
          </div>
        </div>
      </section>

      <!-- Financial Summary -->
      <section
        class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
      >
        <div
          class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6"
        >
          <h2
            class="text-base font-semibold text-[#17201C]"
          >
            Ringkasan Invoice
          </h2>

          <p
            class="mt-1 text-sm text-[#6B756F]"
          >
            Rincian nilai finansial supplier invoice.
          </p>
        </div>

        <div class="p-5 sm:p-6">
          <dl class="ml-auto max-w-lg space-y-4">
            <div
              class="flex items-center justify-between gap-6 text-sm"
            >
              <dt class="text-[#6B756F]">
                Subtotal
              </dt>

              <dd
                class="font-medium tabular-nums text-[#17201C]"
              >
                {{ formatCurrency(invoice.subtotal) }}
              </dd>
            </div>

            <div
              class="flex items-center justify-between gap-6 text-sm"
            >
              <dt class="text-[#6B756F]">
                Tax
              </dt>

              <dd
                class="font-medium tabular-nums text-[#17201C]"
              >
                {{ formatCurrency(invoice.tax) }}
              </dd>
            </div>

            <div
              class="flex items-center justify-between gap-6 text-sm"
            >
              <dt class="text-[#6B756F]">
                Shipping Cost
              </dt>

              <dd
                class="font-medium tabular-nums text-[#17201C]"
              >
                {{ formatCurrency(invoice.shipping) }}
              </dd>
            </div>

            <div
              class="border-t border-[#D6DDD9] pt-4"
            >
              <div
                class="flex items-end justify-between gap-6"
              >
                <dt
                  class="font-semibold text-[#17201C]"
                >
                  Total Invoice
                </dt>

                <dd
                  class="text-xl font-bold tabular-nums text-[#176B4D] sm:text-2xl"
                >
                  {{ formatCurrency(invoice.total) }}
                </dd>
              </div>
            </div>
          </dl>
        </div>
      </section>

      <!-- Transaction References -->
      <section
        class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
      >
        <div
          class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6"
        >
          <h2
            class="text-base font-semibold text-[#17201C]"
          >
            Referensi Transaksi
          </h2>

          <p
            class="mt-1 text-sm text-[#6B756F]"
          >
            Dokumen transaksi yang menjadi dasar supplier invoice.
          </p>
        </div>

        <div
          class="grid gap-5 p-5 md:grid-cols-2 sm:p-6"
        >
          <!-- Purchase Order -->
          <article
            class="rounded-lg border border-[#D6DDD9] bg-[#F8FAF9] p-5"
          >
            <div
              class="flex items-start justify-between gap-4"
            >
              <div>
                <p
                  class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                >
                  Purchase Order
                </p>

                <p
                  class="mt-2 break-all font-mono text-sm font-medium text-[#17201C]"
                >
                  {{ invoice.purchaseOrderId }}
                </p>
              </div>

              <span
                class="shrink-0 rounded-full border border-[#D6DDD9] bg-white px-2.5 py-1 text-xs font-medium text-[#46514B]"
              >
                PO
              </span>
            </div>

            <button
              type="button"
              class="mt-5 inline-flex min-h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-3.5 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] hover:text-[#176B4D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
              @click="openPurchaseOrder"
            >
              Lihat Purchase Order
            </button>
          </article>

          <!-- Goods Receipt -->
          <article
            class="rounded-lg border border-[#D6DDD9] bg-[#F8FAF9] p-5"
          >
            <div
              class="flex items-start justify-between gap-4"
            >
              <div>
                <p
                  class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                >
                  Goods Receipt
                </p>

                <p
                  class="mt-2 break-all font-mono text-sm font-medium text-[#17201C]"
                >
                  {{ invoice.receiptId }}
                </p>
              </div>

              <span
                class="shrink-0 rounded-full border border-[#D6DDD9] bg-white px-2.5 py-1 text-xs font-medium text-[#46514B]"
              >
                GR
              </span>
            </div>

            <button
              type="button"
              class="mt-5 inline-flex min-h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-3.5 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] hover:text-[#176B4D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
              @click="openGoodsReceipt"
            >
              Lihat Goods Receipt
            </button>
          </article>
        </div>
      </section>

      <!-- Payment Status Information -->
      <section
        class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
      >
        <div
          class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6"
        >
          <h2
            class="text-base font-semibold text-[#17201C]"
          >
            Status Pembayaran
          </h2>
        </div>

        <div class="p-5 sm:p-6">
          <div
            class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p
                class="text-sm text-[#6B756F]"
              >
                Status invoice saat ini
              </p>

              <p
                class="mt-1 text-base font-semibold text-[#17201C]"
              >
                {{
                  paymentStatusLabel(
                    invoice.paymentStatus,
                  )
                }}
              </p>
            </div>

            <span
              class="inline-flex w-fit items-center rounded-full border px-3 py-1.5 text-sm font-semibold"
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
        </div>
      </section>

      <!-- Bottom Actions -->
      <div
        class="flex flex-col-reverse gap-3 border-t border-[#D6DDD9] pt-5 sm:flex-row sm:justify-between"
      >
        <button
          type="button"
          class="inline-flex min-h-11 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-5 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
          @click="backToList"
        >
          Kembali ke Supplier Invoice
        </button>

        <div
          class="flex flex-col gap-3 sm:flex-row"
        >
          <button
            type="button"
            class="inline-flex min-h-11 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-5 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
            @click="openGoodsReceipt"
          >
            Lihat Goods Receipt
          </button>

          <button
            type="button"
            class="inline-flex min-h-11 items-center justify-center rounded-lg bg-[#176B4D] px-5 py-2 text-sm font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30 focus:ring-offset-2"
            @click="openPurchaseOrder"
          >
            Lihat Purchase Order
          </button>
        </div>
      </div>
    </template>
  </section>
</template>