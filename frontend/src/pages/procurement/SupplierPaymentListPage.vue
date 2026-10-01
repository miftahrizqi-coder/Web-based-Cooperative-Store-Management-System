```vue
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
const searchQuery = ref('')

const methodLabel: Record<SupplierPaymentMethod, string> = {
  CASH: 'Tunai',
  BANK_TRANSFER: 'Transfer Bank',
  DEBIT: 'Debit',
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

const filteredPayments = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  if (!query) {
    return payments.value
  }

  return payments.value.filter((payment) => {
    return [
      payment.paymentNumber,
      payment.invoiceId,
      payment.supplierId,
      payment.referenceNumber,
      methodLabel[payment.method],
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query))
  })
})

const totalPaid = computed(() =>
  payments.value.reduce(
    (total, payment) => total + payment.amount,
    0,
  ),
)

const filteredTotal = computed(() =>
  filteredPayments.value.reduce(
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

function openCreatePayment() {
  router.push('/supplier-payments/create')
}

onMounted(loadPayments)
</script>

<template>
  <section class="min-h-full bg-[#F8FAF9] text-[#17201C]">
    <div class="mx-auto max-w-[1440px] space-y-6 px-4 py-6 sm:px-6 lg:px-8">

      <!-- Breadcrumb -->
      <nav
        aria-label="Breadcrumb"
        class="flex items-center gap-2 text-[13px] leading-[18px] text-[#6B756F]"
      >
        <button
          type="button"
          class="rounded-md font-medium transition-colors hover:text-[#176B4D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
          @click="router.push('/dashboard')"
        >
          Dashboard
        </button>

        <span aria-hidden="true">
          /
        </span>

        <span class="font-medium text-[#46514B]">
          Pembayaran Supplier
        </span>
      </nav>

      <!-- Page Header -->
      <header
        class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
      >
        <div>
          <h1
            class="text-[28px] font-semibold leading-9 tracking-[-0.02em] text-[#17201C]"
          >
            Pembayaran Supplier
          </h1>

          <p class="mt-1 max-w-2xl text-sm leading-5 text-[#6B756F]">
            Riwayat pembayaran invoice supplier dan transaksi hutang yang
            sudah dicatat.
          </p>
        </div>

        <div class="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            :disabled="isLoading"
            class="inline-flex min-h-10 items-center justify-center rounded-md border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#46514B] transition-colors hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            @click="loadPayments"
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
                d="M20 11a8.1 8.1 0 0 0-15.5-2M4 5v4h4"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M4 13a8.1 8.1 0 0 0 15.5 2M20 19v-4h-4"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>

            Refresh
          </button>

          <button
            type="button"
            class="inline-flex min-h-10 items-center justify-center rounded-md bg-[#176B4D] px-4 text-sm font-semibold text-white shadow-[0_1px_2px_rgba(18,55,42,.08)] transition-colors hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="openCreatePayment"
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
                d="M12 5v14M5 12h14"
                stroke-linecap="round"
              />
            </svg>

            Catat Pembayaran
          </button>
        </div>
      </header>

      <!-- Loading -->
      <div
        v-if="isLoading"
        class="space-y-6"
        aria-busy="true"
        aria-label="Memuat pembayaran supplier"
      >
        <!-- KPI skeleton -->
        <div class="grid gap-4 sm:grid-cols-2">
          <div
            v-for="item in 2"
            :key="item"
            class="rounded-lg border border-[#D6DDD9] bg-white p-5 shadow-[0_1px_2px_rgba(18,55,42,.06)]"
          >
            <div class="h-4 w-32 animate-pulse rounded bg-[#F1F4F2]" />
            <div class="mt-3 h-8 w-44 animate-pulse rounded bg-[#F1F4F2]" />
          </div>
        </div>

        <!-- Table skeleton -->
        <div
          class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white shadow-[0_1px_2px_rgba(18,55,42,.06)]"
        >
          <div class="h-12 animate-pulse bg-[#F1F4F2]" />

          <div class="divide-y divide-[#E6EBE8]">
            <div
              v-for="item in 5"
              :key="item"
              class="grid grid-cols-4 gap-4 px-5 py-5"
            >
              <div class="h-4 animate-pulse rounded bg-[#F1F4F2]" />
              <div class="h-4 animate-pulse rounded bg-[#F1F4F2]" />
              <div class="h-4 animate-pulse rounded bg-[#F1F4F2]" />
              <div class="h-4 animate-pulse rounded bg-[#F1F4F2]" />
            </div>
          </div>
        </div>
      </div>

      <template v-else>

        <!-- KPI Summary -->
        <section
          class="grid gap-4 sm:grid-cols-2"
          aria-label="Ringkasan pembayaran supplier"
        >
          <article
            class="rounded-lg border border-[#D6DDD9] bg-white p-5 shadow-[0_1px_2px_rgba(18,55,42,.06)]"
          >
            <p class="text-[13px] leading-[18px] text-[#6B756F]">
              Total Pembayaran
            </p>

            <p
              class="mt-2 text-[28px] font-semibold leading-[34px] tracking-[-0.02em] text-[#12372A] tabular-nums"
            >
              {{ formatCurrency(totalPaid) }}
            </p>

            <p class="mt-1 text-xs text-[#6B756F]">
              Seluruh pembayaran supplier yang tercatat.
            </p>
          </article>

          <article
            class="rounded-lg border border-[#D6DDD9] bg-white p-5 shadow-[0_1px_2px_rgba(18,55,42,.06)]"
          >
            <p class="text-[13px] leading-[18px] text-[#6B756F]">
              Jumlah Transaksi
            </p>

            <p
              class="mt-2 text-[28px] font-semibold leading-[34px] tracking-[-0.02em] text-[#12372A] tabular-nums"
            >
              {{ payments.length }}
            </p>

            <p class="mt-1 text-xs text-[#6B756F]">
              Pembayaran supplier yang sudah dicatat.
            </p>
          </article>
        </section>

        <!-- Error -->
        <div
          v-if="errorMessage"
          class="rounded-lg border border-[#C0392B]/25 bg-[#FFF6F5] p-4"
          role="alert"
        >
          <div class="flex items-start gap-3">
            <span
              class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#C0392B]/10 text-sm font-bold text-[#C0392B]"
              aria-hidden="true"
            >
              !
            </span>

            <div class="min-w-0">
              <p class="font-semibold text-[#C0392B]">
                Gagal memuat pembayaran supplier
              </p>

              <p class="mt-1 text-sm leading-5 text-[#C0392B]/90">
                {{ errorMessage }}
              </p>

              <button
                type="button"
                class="mt-3 inline-flex min-h-9 items-center justify-center rounded-md border border-[#C0392B]/30 bg-white px-3 text-sm font-medium text-[#C0392B] transition-colors hover:bg-[#FFF6F5] focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-2"
                @click="loadPayments"
              >
                Coba Lagi
              </button>
            </div>
          </div>
        </div>

        <!-- Filter Bar -->
        <section
          class="rounded-lg border border-[#D6DDD9] bg-white p-4 shadow-[0_1px_2px_rgba(18,55,42,.06)]"
          aria-label="Filter pembayaran supplier"
        >
          <div
            class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"
          >
            <div class="relative w-full lg:max-w-md">
              <label
                for="payment-search"
                class="sr-only"
              >
                Cari pembayaran supplier
              </label>

              <svg
                class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6B756F]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                aria-hidden="true"
              >
                <circle
                  cx="11"
                  cy="11"
                  r="7"
                />
                <path
                  d="m20 20-4-4"
                  stroke-linecap="round"
                />
              </svg>

              <input
                id="payment-search"
                v-model="searchQuery"
                type="search"
                placeholder="Cari nomor pembayaran, invoice, supplier..."
                class="block min-h-10 w-full rounded-md border border-[#D6DDD9] bg-white py-2.5 pl-9 pr-3 text-sm text-[#17201C] outline-none transition placeholder:text-[#6B756F] hover:border-[#AEB9B3] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/15"
              />
            </div>

            <p class="text-[13px] leading-[18px] text-[#6B756F]">
              Menampilkan
              <span class="font-semibold text-[#46514B]">
                {{ filteredPayments.length }}
              </span>
              dari
              <span class="font-semibold text-[#46514B]">
                {{ payments.length }}
              </span>
              transaksi
            </p>
          </div>
        </section>

        <!-- Empty State -->
        <section
          v-if="payments.length === 0"
          class="rounded-lg border border-[#D6DDD9] bg-white p-10 text-center shadow-[0_1px_2px_rgba(18,55,42,.06)]"
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
              <rect
                x="3"
                y="5"
                width="18"
                height="14"
                rx="2"
              />
              <path
                d="M3 10h18M7 15h4"
                stroke-linecap="round"
              />
            </svg>
          </div>

          <h2 class="mt-4 text-lg font-semibold text-[#17201C]">
            Belum ada pembayaran supplier
          </h2>

          <p class="mx-auto mt-2 max-w-md text-sm leading-5 text-[#6B756F]">
            Belum ada transaksi pembayaran supplier yang tercatat.
            Catat pembayaran pertama untuk mulai menyimpan riwayat transaksi.
          </p>

          <button
            type="button"
            class="mt-5 inline-flex min-h-10 items-center justify-center rounded-md bg-[#176B4D] px-4 text-sm font-semibold text-white hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="openCreatePayment"
          >
            Catat Pembayaran
          </button>
        </section>

        <!-- Search Empty State -->
        <section
          v-else-if="filteredPayments.length === 0"
          class="rounded-lg border border-[#D6DDD9] bg-white p-10 text-center shadow-[0_1px_2px_rgba(18,55,42,.06)]"
        >
          <div
            class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#F1F4F2] text-[#6B756F]"
            aria-hidden="true"
          >
            <svg
              class="h-6 w-6"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
            >
              <circle
                cx="11"
                cy="11"
                r="7"
              />
              <path
                d="m20 20-4-4"
                stroke-linecap="round"
              />
            </svg>
          </div>

          <h2 class="mt-4 text-lg font-semibold text-[#17201C]">
            Tidak ada pembayaran yang cocok
          </h2>

          <p class="mt-2 text-sm leading-5 text-[#6B756F]">
            Coba gunakan kata kunci lain untuk mencari nomor pembayaran,
            invoice, supplier, atau referensi.
          </p>

          <button
            type="button"
            class="mt-5 inline-flex min-h-10 items-center justify-center rounded-md border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="searchQuery = ''"
          >
            Hapus Pencarian
          </button>
        </section>

        <!-- Data Table -->
        <section
          v-else
          class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white shadow-[0_1px_2px_rgba(18,55,42,.06)]"
        >
          <div
            class="flex flex-col gap-1 border-b border-[#E6EBE8] px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <h2 class="text-base font-semibold text-[#17201C]">
                Riwayat Pembayaran
              </h2>

              <p class="mt-0.5 text-xs text-[#6B756F]">
                Data pembayaran supplier yang sudah tercatat.
              </p>
            </div>

            <p class="text-xs text-[#6B756F]">
              Total hasil:
              <span class="font-semibold text-[#46514B]">
                {{ formatCurrency(filteredTotal) }}
              </span>
            </p>
          </div>

          <div class="overflow-x-auto">
            <table class="min-w-full">
              <caption class="sr-only">
                Daftar pembayaran supplier
              </caption>

              <thead class="sticky top-0 z-10 border-b border-[#E6EBE8] bg-[#F1F4F2]">
                <tr>
                  <th
                    scope="col"
                    class="whitespace-nowrap px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
                  >
                    Nomor Pembayaran
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
                  >
                    Invoice
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
                  >
                    Supplier
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]"
                  >
                    Jumlah
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
                  >
                    Metode
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
                  >
                    Tanggal
                  </th>

                  <th
                    scope="col"
                    class="whitespace-nowrap px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]"
                  >
                    Referensi
                  </th>
                </tr>
              </thead>

              <tbody class="divide-y divide-[#E6EBE8]">
                <tr
                  v-for="payment in filteredPayments"
                  :key="payment.id"
                  class="transition-colors hover:bg-[#F8FAF9]"
                >
                  <td class="whitespace-nowrap px-5 py-4">
                    <span class="text-sm font-semibold text-[#17201C]">
                      {{ payment.paymentNumber }}
                    </span>
                  </td>

                  <td class="whitespace-nowrap px-4 py-4">
                    <button
                      type="button"
                      class="rounded-md text-sm font-medium text-[#176B4D] underline-offset-2 hover:text-[#1F805D] hover:underline focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                      @click="openInvoice(payment.invoiceId)"
                    >
                      {{ payment.invoiceNumber || payment.invoiceId }}
                    </button>
                  </td>

                  <td class="whitespace-nowrap px-4 py-4 text-sm text-[#46514B]">
                    {{ payment.supplierName || payment.supplierId }}
                  </td>

                  <td
                    class="whitespace-nowrap px-4 py-4 text-right text-sm font-semibold tabular-nums text-[#17201C]"
                  >
                    {{ formatCurrency(payment.amount) }}
                  </td>

                  <td class="whitespace-nowrap px-4 py-4">
                    <span
                      class="inline-flex items-center rounded-full bg-[#F0F8F5] px-2.5 py-1 text-xs font-medium text-[#176B4D]"
                    >
                      {{ methodLabel[payment.method] }}
                    </span>
                  </td>

                  <td class="whitespace-nowrap px-4 py-4 text-sm text-[#46514B]">
                    {{ formatDate(payment.paymentDate) }}
                  </td>

                  <td class="whitespace-nowrap px-5 py-4 text-sm text-[#46514B]">
                    {{ payment.referenceNumber || '-' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Table footer -->
          <div
            class="flex flex-col gap-2 border-t border-[#E6EBE8] bg-[#F8FAF9] px-5 py-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <p class="text-xs text-[#6B756F]">
              {{ filteredPayments.length }} transaksi ditampilkan
            </p>

            <p class="text-xs text-[#6B756F]">
              Nilai transaksi:
              <span class="font-semibold tabular-nums text-[#46514B]">
                {{ formatCurrency(filteredTotal) }}
              </span>
            </p>
          </div>
        </section>
      </template>
    </div>
  </section>
</template>
```
