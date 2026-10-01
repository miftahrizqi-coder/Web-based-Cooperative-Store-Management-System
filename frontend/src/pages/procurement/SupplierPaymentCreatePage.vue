<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  createSupplierPayment,
  getSupplierPayables,
} from '../../api/procurement'
import type {
  SupplierPayable,
  SupplierPaymentMethod,
} from '../../types/procurement'

const router = useRouter()

const accessToken = localStorage.getItem('access_token')

const payables = ref<SupplierPayable[]>([])
const selectedInvoiceId = ref('')
const amount = ref<number | null>(null)
const method = ref<SupplierPaymentMethod>('BANK_TRANSFER')
const paymentDate = ref(
  new Date().toISOString().slice(0, 10),
)
const referenceNumber = ref('')
const notes = ref('')

const isLoading = ref(true)
const isSubmitting = ref(false)
const errorMessage = ref('')
const validationMessage = ref('')

const paymentMethods: Array<{
  value: SupplierPaymentMethod
  label: string
}> = [
  {
    value: 'CASH',
    label: 'Tunai',
  },
  {
    value: 'BANK_TRANSFER',
    label: 'Transfer Bank',
  },
  {
    value: 'DEBIT',
    label: 'Debit',
  },
  {
    value: 'OTHER',
    label: 'Lainnya',
  },
]

const selectedPayable = computed(() =>
  payables.value.find(
    (payable) =>
      payable.invoiceId === selectedInvoiceId.value,
  ),
)

const outstanding = computed(
  () => selectedPayable.value?.outstanding ?? 0,
)

const formattedOutstanding = computed(() =>
  new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(outstanding.value),
)

const formattedAmount = computed(() =>
  new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(amount.value ?? 0),
)

const paymentStatusLabel: Record<string, string> = {
  UNPAID: 'Belum Dibayar',
  PARTIALLY_PAID: 'Sebagian Dibayar',
  OVERDUE: 'Jatuh Tempo',
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

async function loadPayables() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    if (!accessToken) {
      throw new Error(
        'Sesi login tidak ditemukan.',
      )
    }

    const result =
      await getSupplierPayables(accessToken)

    payables.value = result.filter(
      (payable) =>
        payable.outstanding > 0 &&
        payable.paymentStatus !== 'PAID',
    )
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil daftar hutang supplier.'
  } finally {
    isLoading.value = false
  }
}

function validateForm(): boolean {
  validationMessage.value = ''

  if (!selectedInvoiceId.value) {
    validationMessage.value =
      'Invoice wajib dipilih.'
    return false
  }

  if (!selectedPayable.value) {
    validationMessage.value =
      'Invoice yang dipilih tidak ditemukan.'
    return false
  }

  if (
    amount.value === null ||
    !Number.isFinite(amount.value) ||
    amount.value <= 0
  ) {
    validationMessage.value =
      'Jumlah pembayaran harus lebih besar dari 0.'
    return false
  }

  if (amount.value > outstanding.value) {
    validationMessage.value =
      `Jumlah pembayaran tidak boleh melebihi outstanding ${formattedOutstanding.value}.`
    return false
  }

  if (!method.value) {
    validationMessage.value =
      'Metode pembayaran wajib dipilih.'
    return false
  }

  if (!paymentDate.value) {
    validationMessage.value =
      'Tanggal pembayaran wajib diisi.'
    return false
  }

  return true
}

async function submitPayment() {
  if (!validateForm()) {
    return
  }

  const confirmed = window.confirm(
    [
      'Simpan pembayaran supplier?',
      '',
      `Invoice: ${selectedPayable.value?.invoiceNumber}`,
      `Jumlah: ${formattedAmount.value}`,
      `Metode: ${
        paymentMethods.find(
          (item) => item.value === method.value,
        )?.label
      }`,
    ].join('\n'),
  )

  if (!confirmed) {
    return
  }

  if (!accessToken) {
    errorMessage.value =
      'Sesi login tidak ditemukan.'
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    await createSupplierPayment(
      accessToken,
      {
        invoiceId: selectedInvoiceId.value,
        amount: amount.value as number,
        method: method.value,
        paymentDate: new Date(
          `${paymentDate.value}T00:00:00`,
        ).toISOString(),
        referenceNumber:
          referenceNumber.value.trim() || null,
        notes: notes.value.trim() || null,
      },
    )

    router.push('/supplier-payments')
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mencatat pembayaran supplier.'
  } finally {
    isSubmitting.value = false
  }
}

function goBack() {
  router.push('/supplier-payments')
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

        <li>
          <button
            type="button"
            class="font-medium text-[#46514B] underline-offset-2 hover:text-[#176B4D] hover:underline focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
            @click="goBack"
          >
            Supplier Payment
          </button>
        </li>

        <li aria-hidden="true">
          /
        </li>

        <li
          class="font-medium text-[#17201C]"
          aria-current="page"
        >
          Catat Pembayaran
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
          Catat Pembayaran Supplier
        </h1>

        <p
          class="mt-2 max-w-2xl text-sm leading-6 text-[#6B756F]"
        >
          Catat pembayaran untuk satu supplier invoice
          dan kurangi nilai outstanding yang masih harus dibayar.
        </p>
      </div>

      <button
        type="button"
        class="inline-flex min-h-11 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="isSubmitting"
        @click="goBack"
      >
        Kembali
      </button>
    </header>

    <!-- Loading -->
    <div
      v-if="isLoading"
      class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]"
      aria-live="polite"
      aria-busy="true"
    >
      <div class="space-y-6">
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
              class="mt-2 h-4 w-72 max-w-full animate-pulse rounded bg-[#F1F4F2]"
            />
          </div>

          <div class="space-y-5 p-5 sm:p-6">
            <div
              class="h-11 animate-pulse rounded-lg bg-[#F1F4F2]"
            />

            <div
              class="grid gap-4 sm:grid-cols-3"
            >
              <div
                v-for="item in 3"
                :key="item"
                class="h-20 animate-pulse rounded-lg bg-[#F1F4F2]"
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
              class="h-5 w-32 animate-pulse rounded bg-[#E7ECE9]"
            />
          </div>

          <div
            class="grid gap-5 p-5 sm:grid-cols-2 sm:p-6"
          >
            <div
              v-for="item in 5"
              :key="item"
              class="space-y-2"
            >
              <div
                class="h-4 w-32 animate-pulse rounded bg-[#E7ECE9]"
              />

              <div
                class="h-11 animate-pulse rounded-lg bg-[#F1F4F2]"
              />
            </div>
          </div>
        </section>
      </div>

      <aside
        class="h-80 animate-pulse rounded-xl border border-[#D6DDD9] bg-[#F1F4F2]"
      />
    </div>

    <!-- Loading Error -->
    <div
      v-else-if="
        errorMessage &&
        payables.length === 0
      "
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
            Gagal memuat invoice
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
              @click="loadPayables"
            >
              Coba Lagi
            </button>

            <button
              type="button"
              class="inline-flex min-h-11 items-center justify-center rounded-lg border border-[#C0392B]/20 bg-white px-4 py-2 text-sm font-semibold text-[#8E2B22] transition hover:bg-[#FEF4F3] focus:outline-none focus:ring-2 focus:ring-[#C0392B]/30"
              @click="goBack"
            >
              Kembali
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div
      v-else-if="payables.length === 0"
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
        Tidak ada invoice yang dapat dibayar
      </h2>

      <p
        class="mx-auto mt-2 max-w-lg text-sm leading-6 text-[#6B756F]"
      >
        Semua supplier invoice sudah lunas atau
        belum memiliki outstanding.
      </p>

      <button
        type="button"
        class="mt-5 inline-flex min-h-11 items-center justify-center rounded-lg bg-[#176B4D] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30 focus:ring-offset-2"
        @click="goBack"
      >
        Kembali ke Pembayaran
      </button>
    </div>

    <!-- Form -->
    <form
      v-else
      class="space-y-6"
      @submit.prevent="submitPayment"
    >
      <div
        class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]"
      >
        <!-- Main Form -->
        <div class="space-y-6">
          <!-- Error -->
          <div
            v-if="errorMessage"
            class="rounded-xl border border-[#C0392B]/25 bg-[#FEF4F3] p-4"
            role="alert"
          >
            <div class="flex gap-3">
              <div
                class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#C0392B]/10 text-sm font-bold text-[#C0392B]"
                aria-hidden="true"
              >
                !
              </div>

              <div>
                <p
                  class="font-semibold text-[#8E2B22]"
                >
                  Gagal menyimpan pembayaran
                </p>

                <p
                  class="mt-1 text-sm leading-6 text-[#A33A2E]"
                >
                  {{ errorMessage }}
                </p>
              </div>
            </div>
          </div>

          <!-- Validation -->
          <div
            v-if="validationMessage"
            class="rounded-xl border border-[#C47A00]/25 bg-[#FFF8E8] p-4"
            role="alert"
          >
            <div class="flex gap-3">
              <div
                class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#C47A00]/10 text-sm font-bold text-[#8A5A00]"
                aria-hidden="true"
              >
                !
              </div>

              <p
                class="text-sm leading-6 text-[#8A5A00]"
              >
                {{ validationMessage }}
              </p>
            </div>
          </div>

          <!-- Invoice Section -->
          <section
            class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
          >
            <div
              class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6"
            >
              <h2
                class="text-base font-semibold text-[#17201C]"
              >
                Invoice
              </h2>

              <p
                class="mt-1 text-sm text-[#6B756F]"
              >
                Pilih invoice supplier yang memiliki
                outstanding.
              </p>
            </div>

            <div class="space-y-5 p-5 sm:p-6">
              <div>
                <label
                  for="invoice"
                  class="block text-sm font-semibold text-[#46514B]"
                >
                  Invoice
                  <span
                    class="text-[#C0392B]"
                    aria-hidden="true"
                  >
                    *
                  </span>
                </label>

                <select
                  id="invoice"
                  v-model="selectedInvoiceId"
                  required
                  class="mt-2 min-h-11 w-full rounded-lg border border-[#C8D1CC] bg-white px-3 py-2 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                >
                  <option value="">
                    Pilih invoice
                  </option>

                  <option
                    v-for="payable in payables"
                    :key="payable.invoiceId"
                    :value="payable.invoiceId"
                  >
                    {{ payable.invoiceNumber }}
                    —
                    {{ formatCurrency(payable.outstanding) }}
                    outstanding
                  </option>
                </select>

                <p
                  class="mt-2 text-xs text-[#6B756F]"
                >
                  Hanya invoice yang masih memiliki
                  outstanding yang ditampilkan.
                </p>
              </div>

              <!-- Selected Invoice -->
              <div
                v-if="selectedPayable"
                class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-[#F8FAF9]"
              >
                <div
                  class="border-b border-[#D6DDD9] px-4 py-3"
                >
                  <div
                    class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <p
                        class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                      >
                        Invoice Terpilih
                      </p>

                      <p
                        class="mt-1 font-semibold text-[#17201C]"
                      >
                        {{ selectedPayable.invoiceNumber }}
                      </p>
                    </div>

                    <span
                      class="inline-flex w-fit items-center rounded-full border border-[#C47A00]/20 bg-[#FFF8E8] px-2.5 py-1 text-xs font-semibold text-[#8A5A00]"
                    >
                      {{
                        paymentStatusLabel[
                          selectedPayable
                            .paymentStatus
                        ] ||
                        selectedPayable.paymentStatus
                      }}
                    </span>
                  </div>
                </div>

                <dl
                  class="grid gap-4 p-4 sm:grid-cols-3"
                >
                  <div>
                    <dt
                      class="text-xs text-[#6B756F]"
                    >
                      Supplier
                    </dt>

                    <dd
                      class="mt-1 break-all text-sm font-medium text-[#17201C]"
                    >
                      {{ selectedPayable.supplierName || selectedPayable.supplierId }}
                    </dd>
                  </div>

                  <div>
                    <dt
                      class="text-xs text-[#6B756F]"
                    >
                      Total Invoice
                    </dt>

                    <dd
                      class="mt-1 text-sm font-medium tabular-nums text-[#17201C]"
                    >
                      {{
                        formatCurrency(
                          selectedPayable.total,
                        )
                      }}
                    </dd>
                  </div>

                  <div>
                    <dt
                      class="text-xs text-[#6B756F]"
                    >
                      Outstanding
                    </dt>

                    <dd
                      class="mt-1 text-sm font-bold tabular-nums text-[#176B4D]"
                    >
                      {{ formattedOutstanding }}
                    </dd>
                  </div>

                  <div>
                    <dt
                      class="text-xs text-[#6B756F]"
                    >
                      Sudah Dibayar
                    </dt>

                    <dd
                      class="mt-1 text-sm font-medium tabular-nums text-[#46514B]"
                    >
                      {{
                        formatCurrency(
                          selectedPayable.paid,
                        )
                      }}
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
                      {{
                        formatDate(
                          selectedPayable.dueDate,
                        )
                      }}
                    </dd>
                  </div>

                  <div>
                    <dt
                      class="text-xs text-[#6B756F]"
                    >
                      Invoice ID
                    </dt>

                    <dd
                      class="mt-1 truncate font-mono text-xs font-medium text-[#46514B]"
                      :title="selectedPayable.invoiceId"
                    >
                      {{ selectedPayable.invoiceId }}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </section>

          <!-- Payment Section -->
          <section
            class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
          >
            <div
              class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6"
            >
              <h2
                class="text-base font-semibold text-[#17201C]"
              >
                Detail Pembayaran
              </h2>

              <p
                class="mt-1 text-sm text-[#6B756F]"
              >
                Masukkan nominal dan informasi pembayaran
                supplier.
              </p>
            </div>

            <div
              class="grid gap-5 p-5 sm:grid-cols-2 sm:p-6"
            >
              <!-- Amount -->
              <div>
                <label
                  for="amount"
                  class="block text-sm font-semibold text-[#46514B]"
                >
                  Jumlah Pembayaran
                  <span
                    class="text-[#C0392B]"
                    aria-hidden="true"
                  >
                    *
                  </span>
                </label>

                <div class="relative mt-2">
                  <span
                    class="pointer-events-none absolute inset-y-0 left-3 flex items-center text-sm text-[#6B756F]"
                  >
                    Rp
                  </span>

                  <input
                    id="amount"
                    v-model.number="amount"
                    type="number"
                    min="1"
                    step="1"
                    inputmode="numeric"
                    required
                    placeholder="Masukkan jumlah"
                    class="min-h-11 w-full rounded-lg border border-[#C8D1CC] bg-white py-2 pl-10 pr-3 text-right text-sm tabular-nums text-[#17201C] outline-none transition placeholder:text-[#9AA39E] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                  />
                </div>

                <p
                  class="mt-2 text-xs text-[#6B756F]"
                >
                  Maksimal:
                  {{ formattedOutstanding }}
                </p>
              </div>

              <!-- Method -->
              <div>
                <label
                  for="method"
                  class="block text-sm font-semibold text-[#46514B]"
                >
                  Metode Pembayaran
                  <span
                    class="text-[#C0392B]"
                    aria-hidden="true"
                  >
                    *
                  </span>
                </label>

                <select
                  id="method"
                  v-model="method"
                  required
                  class="mt-2 min-h-11 w-full rounded-lg border border-[#C8D1CC] bg-white px-3 py-2 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                >
                  <option
                    v-for="item in paymentMethods"
                    :key="item.value"
                    :value="item.value"
                  >
                    {{ item.label }}
                  </option>
                </select>
              </div>

              <!-- Payment Date -->
              <div>
                <label
                  for="paymentDate"
                  class="block text-sm font-semibold text-[#46514B]"
                >
                  Tanggal Pembayaran
                  <span
                    class="text-[#C0392B]"
                    aria-hidden="true"
                  >
                    *
                  </span>
                </label>

                <input
                  id="paymentDate"
                  v-model="paymentDate"
                  type="date"
                  required
                  class="mt-2 min-h-11 w-full rounded-lg border border-[#C8D1CC] bg-white px-3 py-2 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                />
              </div>

              <!-- Reference -->
              <div>
                <label
                  for="referenceNumber"
                  class="block text-sm font-semibold text-[#46514B]"
                >
                  Nomor Referensi
                  <span
                    class="font-normal text-[#9AA39E]"
                  >
                    (opsional)
                  </span>
                </label>

                <input
                  id="referenceNumber"
                  v-model="referenceNumber"
                  type="text"
                  autocomplete="off"
                  placeholder="Nomor transfer / bukti pembayaran"
                  class="mt-2 min-h-11 w-full rounded-lg border border-[#C8D1CC] bg-white px-3 py-2 text-sm text-[#17201C] outline-none transition placeholder:text-[#9AA39E] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                />
              </div>

              <!-- Notes -->
              <div class="sm:col-span-2">
                <label
                  for="notes"
                  class="block text-sm font-semibold text-[#46514B]"
                >
                  Catatan
                  <span
                    class="font-normal text-[#9AA39E]"
                  >
                    (opsional)
                  </span>
                </label>

                <textarea
                  id="notes"
                  v-model="notes"
                  rows="4"
                  placeholder="Catatan pembayaran"
                  class="mt-2 w-full resize-y rounded-lg border border-[#C8D1CC] px-3 py-2 text-sm text-[#17201C] outline-none transition placeholder:text-[#9AA39E] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                />
              </div>
            </div>
          </section>

          <!-- Actions -->
          <div
            class="flex flex-col-reverse gap-3 border-t border-[#D6DDD9] pt-5 sm:flex-row sm:justify-end"
          >
            <button
              type="button"
              class="inline-flex min-h-11 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-5 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="isSubmitting"
              @click="goBack"
            >
              Batal
            </button>

            <button
              type="submit"
              :disabled="isSubmitting"
              class="inline-flex min-h-11 items-center justify-center rounded-lg bg-[#176B4D] px-5 py-2 text-sm font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <svg
                v-if="isSubmitting"
                class="mr-2 h-4 w-4 animate-spin"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="9"
                  stroke="currentColor"
                  stroke-width="3"
                />

                <path
                  class="opacity-90"
                  fill="currentColor"
                  d="M4 12a8 8 0 0 1 8-8v3a5 5 0 0 0-5 5H4Z"
                />
              </svg>

              {{
                isSubmitting
                  ? 'Menyimpan...'
                  : 'Simpan Pembayaran'
              }}
            </button>
          </div>
        </div>

        <!-- Summary -->
        <aside
          class="xl:sticky xl:top-6 xl:self-start"
        >
          <section
            class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
          >
            <div
              class="border-b border-[#D6DDD9] bg-[#F8FAF9] px-5 py-4"
            >
              <p
                class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
              >
                Ringkasan
              </p>

              <h2
                class="mt-1 text-base font-semibold text-[#17201C]"
              >
                Pembayaran Supplier
              </h2>
            </div>

            <div class="p-5">
              <div
                v-if="selectedPayable"
                class="space-y-5"
              >
                <div>
                  <p
                    class="text-xs text-[#6B756F]"
                  >
                    Invoice
                  </p>

                  <p
                    class="mt-1 break-all font-semibold text-[#17201C]"
                  >
                    {{ selectedPayable.invoiceNumber }}
                  </p>
                </div>

                <div>
                  <p
                    class="text-xs text-[#6B756F]"
                  >
                    Supplier
                  </p>

                  <p
                    class="mt-1 break-all font-medium text-[#17201C]"
                  >
                    {{ selectedPayable.supplierName || selectedPayable.supplierId }}
                  </p>
                </div>

                <div
                  class="border-t border-[#D6DDD9] pt-4"
                >
                  <div
                    class="flex items-center justify-between gap-4 text-sm"
                  >
                    <span class="text-[#6B756F]">
                      Outstanding
                    </span>

                    <span
                      class="font-semibold tabular-nums text-[#17201C]"
                    >
                      {{ formattedOutstanding }}
                    </span>
                  </div>

                  <div
                    class="mt-3 flex items-center justify-between gap-4 text-sm"
                  >
                    <span class="text-[#6B756F]">
                      Pembayaran
                    </span>

                    <span
                      class="font-semibold tabular-nums text-[#176B4D]"
                    >
                      {{ formattedAmount }}
                    </span>
                  </div>

                  <div
                    class="mt-4 border-t border-[#D6DDD9] pt-4"
                  >
                    <div
                      class="flex items-end justify-between gap-4"
                    >
                      <span
                        class="font-semibold text-[#17201C]"
                      >
                        Sisa Setelah Bayar
                      </span>

                      <span
                        class="text-lg font-bold tabular-nums text-[#176B4D]"
                      >
                        {{
                          formatCurrency(
                            Math.max(
                              0,
                              outstanding -
                                (amount || 0),
                            ),
                          )
                        }}
                      </span>
                    </div>
                  </div>
                </div>

                <div
                  class="rounded-lg border border-[#D6DDD9] bg-[#F8FAF9] p-3.5"
                >
                  <p
                    class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
                  >
                    Metode
                  </p>

                  <p
                    class="mt-1 text-sm font-medium text-[#17201C]"
                  >
                    {{
                      paymentMethods.find(
                        (item) =>
                          item.value === method,
                      )?.label
                    }}
                  </p>
                </div>
              </div>

              <div
                v-else
                class="py-2"
              >
                <p
                  class="text-sm leading-6 text-[#6B756F]"
                >
                  Pilih invoice untuk melihat ringkasan
                  pembayaran.
                </p>
              </div>
            </div>
          </section>

          <div
            class="mt-4 rounded-xl border border-[#D6DDD9] bg-[#F8FAF9] p-4"
          >
            <p
              class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]"
            >
              Informasi
            </p>

            <p
              class="mt-2 text-sm leading-6 text-[#46514B]"
            >
              Jumlah pembayaran tidak boleh melebihi
              outstanding invoice yang dipilih.
            </p>
          </div>
        </aside>
      </div>
    </form>
  </section>
</template>