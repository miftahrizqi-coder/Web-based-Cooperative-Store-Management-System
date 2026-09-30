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
    const accessToken = localStorage.getItem(
      'access_token',
    )

    if (!accessToken) {
      throw new Error(
        'Sesi login tidak ditemukan.',
      )
    }

    invoices.value =
      await getSupplierInvoices(accessToken)
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

        <li
          class="font-medium text-[#17201C]"
          aria-current="page"
        >
          Supplier Invoice
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
          Supplier Invoice
        </h1>

        <p
          class="mt-2 max-w-2xl text-sm leading-6 text-[#6B756F]"
        >
          Kelola invoice supplier yang berasal dari
          transaksi purchase.
        </p>
      </div>

      <button
        type="button"
        class="inline-flex min-h-11 items-center justify-center rounded-lg bg-[#176B4D] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30 focus:ring-offset-2"
        @click="createInvoice"
      >
        <svg
          class="mr-2 h-4 w-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 5v14M5 12h14"
          />
        </svg>

        Buat Supplier Invoice
      </button>
    </header>

    <!-- Summary -->
    <div
      class="grid gap-4 sm:grid-cols-2"
    >
      <article
        class="rounded-xl border border-[#D6DDD9] bg-white p-5"
      >
        <div
          class="flex items-start justify-between gap-4"
        >
          <div>
            <p
              class="text-sm font-medium text-[#6B756F]"
            >
              Total Invoice
            </p>

            <p
              class="mt-2 text-2xl font-bold tabular-nums text-[#17201C]"
            >
              {{ invoices.length }}
            </p>

            <p
              class="mt-1 text-sm text-[#6B756F]"
            >
              Seluruh supplier invoice
            </p>
          </div>

          <div
            class="flex h-10 w-10 items-center justify-center rounded-lg bg-[#F0F8F5] text-[#176B4D]"
            aria-hidden="true"
          >
            <svg
              class="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M7 3.75h10a1.25 1.25 0 0 1 1.25 1.25v14A1.25 1.25 0 0 1 17 20.25H7A1.25 1.25 0 0 1 5.75 19V5A1.25 1.25 0 0 1 7 3.75Z"
              />

              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M8.5 8h7M8.5 11.5h7M8.5 15h4"
              />
            </svg>
          </div>
        </div>
      </article>

      <article
        class="rounded-xl border border-[#D6DDD9] bg-white p-5"
      >
        <div
          class="flex items-start justify-between gap-4"
        >
          <div class="min-w-0">
            <p
              class="text-sm font-medium text-[#6B756F]"
            >
              Invoice Belum Lunas
            </p>

            <p
              class="mt-2 text-2xl font-bold tabular-nums text-[#17201C]"
            >
              {{ unpaidCount }}
            </p>

            <p
              class="mt-1 break-words text-sm text-[#6B756F]"
            >
              Nilai:
              {{ formatCurrency(outstandingTotal) }}
            </p>
          </div>

          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#FFF8E8] text-[#8A5A00]"
            aria-hidden="true"
          >
            <svg
              class="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
            >
              <circle
                cx="12"
                cy="12"
                r="8.25"
              />

              <path
                stroke-linecap="round"
                d="M12 7.75v4.75l3 1.75"
              />
            </svg>
          </div>
        </div>
      </article>
    </div>

    <!-- Loading -->
    <div
      v-if="isLoading"
      class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
      aria-live="polite"
      aria-busy="true"
    >
      <div
        class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6"
      >
        <div
          class="h-5 w-48 animate-pulse rounded bg-[#E7ECE9]"
        />

        <div
          class="mt-2 h-4 w-72 max-w-full animate-pulse rounded bg-[#F1F4F2]"
        />
      </div>

      <div class="space-y-3 p-5 sm:p-6">
        <div
          v-for="row in 5"
          :key="row"
          class="grid gap-3 md:grid-cols-6"
        >
          <div
            v-for="column in 6"
            :key="column"
            class="h-10 animate-pulse rounded bg-[#F1F4F2]"
          />
        </div>
      </div>
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

          <button
            type="button"
            class="mt-4 inline-flex min-h-11 items-center justify-center rounded-lg bg-[#C0392B] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#A93226] focus:outline-none focus:ring-2 focus:ring-[#C0392B]/30"
            @click="loadInvoices"
          >
            Coba Lagi
          </button>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div
      v-else-if="invoices.length === 0"
      class="rounded-xl border border-dashed border-[#C8D1CC] bg-white px-6 py-12 text-center sm:px-10"
    >
      <div
        class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#F0F8F5] text-[#176B4D]"
        aria-hidden="true"
      >
        <svg
          class="h-6 w-6"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M7 3.75h10A1.25 1.25 0 0 1 18.25 5v14A1.25 1.25 0 0 1 17 20.25H7A1.25 1.25 0 0 1 5.75 19V5A1.25 1.25 0 0 1 7 3.75Z"
          />

          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M9 9h6M9 12.5h6M9 16h3"
          />
        </svg>
      </div>

      <h2
        class="mt-4 text-lg font-semibold text-[#17201C]"
      >
        Belum ada supplier invoice
      </h2>

      <p
        class="mx-auto mt-2 max-w-md text-sm leading-6 text-[#6B756F]"
      >
        Supplier invoice dibuat berdasarkan purchase
        yang sudah tersedia.
      </p>

      <button
        type="button"
        class="mt-5 inline-flex min-h-11 items-center justify-center rounded-lg bg-[#176B4D] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30 focus:ring-offset-2"
        @click="createInvoice"
      >
        Buat Supplier Invoice
      </button>
    </div>

    <!-- Desktop / Tablet Table -->
    <div
      v-else
      class="hidden overflow-hidden rounded-xl border border-[#D6DDD9] bg-white md:block"
    >
      <div
        class="flex flex-col gap-2 border-b border-[#D6DDD9] px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6"
      >
        <div>
          <h2
            class="text-base font-semibold text-[#17201C]"
          >
            Daftar Supplier Invoice
          </h2>

          <p
            class="mt-1 text-sm text-[#6B756F]"
          >
            {{ invoices.length }} invoice tersedia
          </p>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table
          class="min-w-[1050px] w-full text-left text-sm"
        >
          <caption class="sr-only">
            Daftar supplier invoice
          </caption>

          <thead
            class="border-b border-[#D6DDD9] bg-[#F8FAF9]"
          >
            <tr>
              <th
                scope="col"
                class="px-5 py-3.5 font-semibold text-[#46514B]"
              >
                Invoice
              </th>

              <th
                scope="col"
                class="px-5 py-3.5 font-semibold text-[#46514B]"
              >
                Supplier
              </th>

              <th
                scope="col"
                class="px-5 py-3.5 font-semibold text-[#46514B]"
              >
                Purchase
              </th>

              <th
                scope="col"
                class="px-5 py-3.5 font-semibold text-[#46514B]"
              >
                Tanggal
              </th>

              <th
                scope="col"
                class="px-5 py-3.5 text-right font-semibold text-[#46514B]"
              >
                Total
              </th>

              <th
                scope="col"
                class="px-5 py-3.5 font-semibold text-[#46514B]"
              >
                Status
              </th>

              <th
                scope="col"
                class="px-5 py-3.5 text-right font-semibold text-[#46514B]"
              >
                Aksi
              </th>
            </tr>
          </thead>

          <tbody
            class="divide-y divide-[#E7ECE9]"
          >
            <tr
              v-for="invoice in invoices"
              :key="invoice.id"
              class="transition hover:bg-[#F8FAF9]"
            >
              <td class="px-5 py-4">
                <button
                  type="button"
                  class="text-left focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
                  @click="openDetail(invoice.id)"
                >
                  <span
                    class="font-semibold text-[#176B4D] underline-offset-2 hover:underline"
                  >
                    {{ invoice.invoiceNumber }}
                  </span>

                  <span
                    class="mt-1 block max-w-[190px] truncate font-mono text-xs text-[#6B756F]"
                    :title="invoice.id"
                  >
                    ID {{ invoice.id }}
                  </span>
                </button>
              </td>

              <td
                class="max-w-[180px] px-5 py-4 text-[#46514B]"
              >
                <span
                  class="block truncate"
                  :title="invoice.supplierId"
                >
                  {{ invoice.supplierId }}
                </span>
              </td>

              <td
                class="max-w-[180px] px-5 py-4"
              >
                <button
                  type="button"
                  class="max-w-full truncate font-mono text-xs text-[#46514B] underline-offset-2 hover:text-[#176B4D] hover:underline focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
                  :title="invoice.purchaseId"
                  @click="openDetail(invoice.id)"
                >
                  {{ invoice.purchaseId }}
                </button>
              </td>

              <td
                class="whitespace-nowrap px-5 py-4 text-[#46514B]"
              >
                {{ formatDate(invoice.invoiceDate) }}
              </td>

              <td
                class="whitespace-nowrap px-5 py-4 text-right font-semibold tabular-nums text-[#17201C]"
              >
                {{ formatCurrency(invoice.total) }}
              </td>

              <td class="px-5 py-4">
                <span
                  class="inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold"
                  :class="
                    paymentStatusClass(
                      invoice.paymentStatus,
                    )
                  "
                >
                  <span
                    class="mr-1.5 h-1.5 w-1.5 rounded-full bg-current"
                    aria-hidden="true"
                  />

                  {{
                    paymentStatusLabel(
                      invoice.paymentStatus,
                    )
                  }}
                </span>
              </td>

              <td
                class="whitespace-nowrap px-5 py-4 text-right"
              >
                <button
                  type="button"
                  class="inline-flex min-h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-3.5 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] hover:text-[#176B4D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
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

    <!-- Mobile Cards -->
    <div
      v-if="!isLoading && !errorMessage && invoices.length > 0"
      class="space-y-3 md:hidden"
    >
      <div
        class="border-b border-[#D6DDD9] pb-2"
      >
        <h2
          class="text-base font-semibold text-[#17201C]"
        >
          Daftar Supplier Invoice
        </h2>

        <p
          class="mt-1 text-sm text-[#6B756F]"
        >
          {{ invoices.length }} invoice tersedia
        </p>
      </div>

      <article
        v-for="invoice in invoices"
        :key="invoice.id"
        class="rounded-xl border border-[#D6DDD9] bg-white p-4"
      >
        <div
          class="flex items-start justify-between gap-3"
        >
          <div class="min-w-0">
            <button
              type="button"
              class="block max-w-full text-left focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
              @click="openDetail(invoice.id)"
            >
              <span
                class="block truncate font-semibold text-[#176B4D] underline-offset-2 hover:underline"
              >
                {{ invoice.invoiceNumber }}
              </span>
            </button>

            <p
              class="mt-1 truncate font-mono text-xs text-[#6B756F]"
            >
              {{ invoice.id }}
            </p>
          </div>

          <span
            class="inline-flex shrink-0 items-center rounded-full border px-2.5 py-1 text-xs font-semibold"
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

        <dl
          class="mt-4 grid grid-cols-2 gap-x-4 gap-y-4"
        >
          <div>
            <dt
              class="text-xs text-[#6B756F]"
            >
              Supplier
            </dt>

            <dd
              class="mt-1 truncate text-sm font-medium text-[#17201C]"
              :title="invoice.supplierId"
            >
              {{ invoice.supplierId }}
            </dd>
          </div>

          <div>
            <dt
              class="text-xs text-[#6B756F]"
            >
              Tanggal
            </dt>

            <dd
              class="mt-1 text-sm font-medium text-[#17201C]"
            >
              {{ formatDate(invoice.invoiceDate) }}
            </dd>
          </div>

          <div>
            <dt
              class="text-xs text-[#6B756F]"
            >
              Purchase
            </dt>

            <dd
              class="mt-1 truncate font-mono text-xs font-medium text-[#46514B]"
              :title="invoice.purchaseId"
            >
              {{ invoice.purchaseId }}
            </dd>
          </div>

          <div>
            <dt
              class="text-xs text-[#6B756F]"
            >
              Total
            </dt>

            <dd
              class="mt-1 text-sm font-bold tabular-nums text-[#17201C]"
            >
              {{ formatCurrency(invoice.total) }}
            </dd>
          </div>
        </dl>

        <div
          class="mt-4 border-t border-[#E7ECE9] pt-3"
        >
          <button
            type="button"
            class="inline-flex min-h-10 w-full items-center justify-center rounded-lg bg-[#176B4D] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
            @click="openDetail(invoice.id)"
          >
            Lihat Detail
          </button>
        </div>
      </article>
    </div>
  </section>
</template>