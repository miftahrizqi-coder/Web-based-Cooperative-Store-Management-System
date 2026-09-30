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
  UNPAID:
    'border-[#C47A00]/20 bg-[#FFF8E8] text-[#8A5A00]',
  PARTIALLY_PAID:
    'border-[#2874A6]/20 bg-[#F3F8FB] text-[#2874A6]',
  PAID:
    'border-[#176B4D]/20 bg-[#F0F8F5] text-[#176B4D]',
  OVERDUE:
    'border-[#C0392B]/20 bg-[#FEF4F3] text-[#C0392B]',
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

const overdueCount = computed(
  () =>
    payables.value.filter(
      (payable) => payable.paymentStatus === 'OVERDUE',
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
          Hutang Supplier
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
          Hutang Supplier
        </h1>

        <p
          class="mt-2 max-w-2xl text-sm leading-6 text-[#6B756F]"
        >
          Ringkasan hutang supplier berdasarkan invoice,
          pembayaran, dan nilai outstanding.
        </p>
      </div>

      <button
        type="button"
        class="inline-flex min-h-11 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="isLoading"
        @click="loadPayables"
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
            d="M20 11a8.1 8.1 0 0 0-14.9-4M4 5v4h4M4 13a8.1 8.1 0 0 0 14.9 4M20 19v-4h-4"
          />
        </svg>

        Refresh
      </button>
    </header>

    <!-- Loading Summary -->
    <div
      v-if="isLoading"
      class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      aria-live="polite"
      aria-busy="true"
    >
      <div
        v-for="item in 4"
        :key="item"
        class="h-32 animate-pulse rounded-xl border border-[#D6DDD9] bg-[#F1F4F2]"
      />
    </div>

    <!-- Summary -->
    <div
      v-else
      class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
    >
      <!-- Total Invoice -->
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
              Total Invoice
            </p>

            <p
              class="mt-2 break-words text-xl font-bold tabular-nums text-[#17201C]"
            >
              {{ formatCurrency(totalPayable) }}
            </p>

            <p
              class="mt-1 text-xs text-[#6B756F]"
            >
              Nilai seluruh invoice
            </p>
          </div>

          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#F0F8F5] text-[#176B4D]"
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
                d="M7 3.75h10A1.25 1.25 0 0 1 18.25 5v14A1.25 1.25 0 0 1 17 20.25H7A1.25 1.25 0 0 1 5.75 19V5A1.25 1.25 0 0 1 7 3.75Z"
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

      <!-- Total Paid -->
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
              Total Dibayar
            </p>

            <p
              class="mt-2 break-words text-xl font-bold tabular-nums text-[#176B4D]"
            >
              {{ formatCurrency(totalPaid) }}
            </p>

            <p
              class="mt-1 text-xs text-[#6B756F]"
            >
              Pembayaran yang sudah tercatat
            </p>
          </div>

          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#F0F8F5] text-[#176B4D]"
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
                d="M7 12.5 10.25 16 17 8.75"
              />

              <circle
                cx="12"
                cy="12"
                r="8.5"
              />
            </svg>
          </div>
        </div>
      </article>

      <!-- Outstanding -->
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
              Outstanding
            </p>

            <p
              class="mt-2 break-words text-xl font-bold tabular-nums text-[#17201C]"
            >
              {{ formatCurrency(totalOutstanding) }}
            </p>

            <p
              class="mt-1 text-xs text-[#6B756F]"
            >
              Nilai yang masih harus dibayar
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

      <!-- Unpaid -->
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
              Invoice Belum Lunas
            </p>

            <p
              class="mt-2 text-xl font-bold tabular-nums text-[#17201C]"
            >
              {{ unpaidCount }}
            </p>

            <p
              class="mt-1 text-xs text-[#6B756F]"
            >
              {{ overdueCount }} invoice jatuh tempo
            </p>
          </div>

          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#FEF4F3] text-[#C0392B]"
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
                d="M12 8v4"
              />

              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 15.5v.01"
              />

              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M10.15 4.5 3.9 15.35a2 2 0 0 0 1.73 3h12.74a2 2 0 0 0 1.73-3L13.85 4.5a2.13 2.13 0 0 0-3.7 0Z"
              />
            </svg>
          </div>
        </div>
      </article>
    </div>

    <!-- Error -->
    <div
      v-if="errorMessage"
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
            Gagal memuat hutang supplier
          </h2>

          <p
            class="mt-1 text-sm leading-6 text-[#A33A2E]"
          >
            {{ errorMessage }}
          </p>

          <button
            type="button"
            class="mt-4 inline-flex min-h-11 items-center justify-center rounded-lg bg-[#C0392B] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#A93226] focus:outline-none focus:ring-2 focus:ring-[#C0392B]/30"
            @click="loadPayables"
          >
            Coba Lagi
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="!isLoading && payables.length === 0"
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
        Belum ada hutang supplier
      </h2>

      <p
        class="mx-auto mt-2 max-w-md text-sm leading-6 text-[#6B756F]"
      >
        Hutang supplier akan muncul setelah supplier
        invoice dibuat.
      </p>
    </div>

    <!-- Desktop / Tablet Table -->
    <div
      v-else-if="payables.length > 0"
      class="hidden overflow-hidden rounded-xl border border-[#D6DDD9] bg-white md:block"
    >
      <div
        class="flex flex-col gap-2 border-b border-[#D6DDD9] px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6"
      >
        <div>
          <h2
            class="text-base font-semibold text-[#17201C]"
          >
            Daftar Hutang Supplier
          </h2>

          <p
            class="mt-1 text-sm text-[#6B756F]"
          >
            {{ payables.length }} invoice tercatat
          </p>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table
          class="min-w-[1050px] w-full text-left text-sm"
        >
          <caption class="sr-only">
            Daftar hutang supplier
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
                class="px-5 py-3.5 text-right font-semibold text-[#46514B]"
              >
                Total
              </th>

              <th
                scope="col"
                class="px-5 py-3.5 text-right font-semibold text-[#46514B]"
              >
                Dibayar
              </th>

              <th
                scope="col"
                class="px-5 py-3.5 text-right font-semibold text-[#46514B]"
              >
                Outstanding
              </th>

              <th
                scope="col"
                class="px-5 py-3.5 font-semibold text-[#46514B]"
              >
                Jatuh Tempo
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
              v-for="payable in payables"
              :key="payable.invoiceId"
              class="transition hover:bg-[#F8FAF9]"
            >
              <!-- Invoice -->
              <td class="px-5 py-4">
                <button
                  type="button"
                  class="text-left focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
                  @click="openInvoice(payable.invoiceId)"
                >
                  <span
                    class="font-semibold text-[#176B4D] underline-offset-2 hover:underline"
                  >
                    {{ payable.invoiceNumber }}
                  </span>

                  <span
                    class="mt-1 block max-w-[180px] truncate font-mono text-xs text-[#6B756F]"
                    :title="payable.invoiceId"
                  >
                    ID {{ payable.invoiceId }}
                  </span>
                </button>
              </td>

              <!-- Supplier -->
              <td
                class="max-w-[190px] px-5 py-4 text-[#46514B]"
              >
                <span
                  class="block truncate"
                  :title="payable.supplierId"
                >
                  {{ payable.supplierId }}
                </span>
              </td>

              <!-- Total -->
              <td
                class="whitespace-nowrap px-5 py-4 text-right font-medium tabular-nums text-[#17201C]"
              >
                {{ formatCurrency(payable.total) }}
              </td>

              <!-- Paid -->
              <td
                class="whitespace-nowrap px-5 py-4 text-right tabular-nums text-[#46514B]"
              >
                {{ formatCurrency(payable.paid) }}
              </td>

              <!-- Outstanding -->
              <td
                class="whitespace-nowrap px-5 py-4 text-right font-semibold tabular-nums text-[#17201C]"
              >
                {{ formatCurrency(payable.outstanding) }}
              </td>

              <!-- Due Date -->
              <td
                class="whitespace-nowrap px-5 py-4 text-[#46514B]"
              >
                {{ formatDate(payable.dueDate) }}
              </td>

              <!-- Status -->
              <td class="px-5 py-4">
                <span
                  class="inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold"
                  :class="
                    paymentStatusClass[
                      payable.paymentStatus
                    ]
                  "
                >
                  <span
                    class="mr-1.5 h-1.5 w-1.5 rounded-full bg-current"
                    aria-hidden="true"
                  />

                  {{
                    paymentStatusLabel[
                      payable.paymentStatus
                    ]
                  }}
                </span>
              </td>

              <!-- Action -->
              <td
                class="whitespace-nowrap px-5 py-4 text-right"
              >
                <button
                  type="button"
                  class="inline-flex min-h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-3.5 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] hover:text-[#176B4D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
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

    <!-- Mobile Cards -->
    <div
      v-if="
        !isLoading &&
        !errorMessage &&
        payables.length > 0
      "
      class="space-y-3 md:hidden"
    >
      <div
        class="border-b border-[#D6DDD9] pb-2"
      >
        <h2
          class="text-base font-semibold text-[#17201C]"
        >
          Daftar Hutang Supplier
        </h2>

        <p
          class="mt-1 text-sm text-[#6B756F]"
        >
          {{ payables.length }} invoice tercatat
        </p>
      </div>

      <article
        v-for="payable in payables"
        :key="payable.invoiceId"
        class="rounded-xl border border-[#D6DDD9] bg-white p-4"
      >
        <!-- Card Header -->
        <div
          class="flex items-start justify-between gap-3"
        >
          <div class="min-w-0">
            <button
              type="button"
              class="block max-w-full text-left focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
              @click="openInvoice(payable.invoiceId)"
            >
              <span
                class="block truncate font-semibold text-[#176B4D] underline-offset-2 hover:underline"
              >
                {{ payable.invoiceNumber }}
              </span>
            </button>

            <p
              class="mt-1 truncate font-mono text-xs text-[#6B756F]"
            >
              {{ payable.invoiceId }}
            </p>
          </div>

          <span
            class="inline-flex shrink-0 items-center rounded-full border px-2.5 py-1 text-xs font-semibold"
            :class="
              paymentStatusClass[
                payable.paymentStatus
              ]
            "
          >
            {{
              paymentStatusLabel[
                payable.paymentStatus
              ]
            }}
          </span>
        </div>

        <!-- Card Data -->
        <dl
          class="mt-4 grid grid-cols-2 gap-x-4 gap-y-4"
        >
          <div
            class="col-span-2"
          >
            <dt
              class="text-xs text-[#6B756F]"
            >
              Supplier
            </dt>

            <dd
              class="mt-1 truncate text-sm font-medium text-[#17201C]"
              :title="payable.supplierId"
            >
              {{ payable.supplierId }}
            </dd>
          </div>

          <div>
            <dt
              class="text-xs text-[#6B756F]"
            >
              Total
            </dt>

            <dd
              class="mt-1 text-sm font-medium tabular-nums text-[#17201C]"
            >
              {{ formatCurrency(payable.total) }}
            </dd>
          </div>

          <div>
            <dt
              class="text-xs text-[#6B756F]"
            >
              Dibayar
            </dt>

            <dd
              class="mt-1 text-sm font-medium tabular-nums text-[#46514B]"
            >
              {{ formatCurrency(payable.paid) }}
            </dd>
          </div>

          <div>
            <dt
              class="text-xs text-[#6B756F]"
            >
              Outstanding
            </dt>

            <dd
              class="mt-1 text-sm font-bold tabular-nums text-[#17201C]"
            >
              {{ formatCurrency(payable.outstanding) }}
            </dd>
          </div>

          <div>
            <dt
              class="text-xs text-[#6B756F]"
            >
              Jatuh Tempo
            </dt>

            <dd
              class="mt-1 text-sm font-medium text-[#17201C]"
            >
              {{ formatDate(payable.dueDate) }}
            </dd>
          </div>
        </dl>

        <!-- Card Action -->
        <div
          class="mt-4 border-t border-[#E7ECE9] pt-3"
        >
          <button
            type="button"
            class="inline-flex min-h-10 w-full items-center justify-center rounded-lg bg-[#176B4D] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
            @click="openInvoice(payable.invoiceId)"
          >
            Lihat Invoice
          </button>
        </div>
      </article>
    </div>
  </section>
</template>