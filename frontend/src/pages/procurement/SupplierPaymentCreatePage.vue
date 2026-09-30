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
    value: 'GIRO',
    label: 'Giro',
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

async function loadPayables() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    if (!accessToken) {
      throw new Error('Sesi login tidak ditemukan.')
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
    const payment = await createSupplierPayment(
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
    return payment
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mencatat pembayaran supplier.'
  } finally {
    isSubmitting.value = false
  }
}

onMounted(loadPayables)
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-6">
    <div
      class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <h1 class="text-2xl font-semibold text-slate-900">
          Catat Pembayaran Supplier
        </h1>

        <p class="mt-1 text-sm text-slate-500">
          Catat pembayaran untuk satu supplier invoice.
        </p>
      </div>

      <button
        type="button"
        class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        @click="router.push('/supplier-payments')"
      >
        Kembali
      </button>
    </div>

    <div
      v-if="isLoading"
      class="space-y-4"
    >
      <div
        class="h-20 animate-pulse rounded-xl bg-slate-100"
      />

      <div
        class="h-72 animate-pulse rounded-xl bg-slate-100"
      />
    </div>

    <div
      v-else-if="errorMessage && payables.length === 0"
      class="rounded-xl border border-red-200 bg-red-50 p-4"
    >
      <p class="font-medium text-red-800">
        Gagal memuat invoice
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
      v-else-if="payables.length === 0"
      class="rounded-xl border border-slate-200 bg-white p-10 text-center"
    >
      <h2 class="text-lg font-semibold text-slate-900">
        Tidak ada invoice yang dapat dibayar
      </h2>

      <p class="mt-2 text-sm text-slate-500">
        Semua supplier invoice sudah lunas atau belum memiliki outstanding.
      </p>

      <button
        type="button"
        class="mt-5 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        @click="router.push('/supplier-payments')"
      >
        Kembali ke Pembayaran
      </button>
    </div>

    <form
      v-else
      class="space-y-6"
      @submit.prevent="submitPayment"
    >
      <div
        v-if="errorMessage"
        class="rounded-xl border border-red-200 bg-red-50 p-4"
      >
        <p class="font-medium text-red-800">
          Gagal menyimpan pembayaran
        </p>

        <p class="mt-1 text-sm text-red-700">
          {{ errorMessage }}
        </p>
      </div>

      <div
        v-if="validationMessage"
        class="rounded-xl border border-yellow-200 bg-yellow-50 p-4"
      >
        <p class="text-sm text-yellow-800">
          {{ validationMessage }}
        </p>
      </div>

      <section
        class="rounded-xl border border-slate-200 bg-white p-6"
      >
        <h2 class="text-lg font-semibold text-slate-900">
          Invoice
        </h2>

        <div class="mt-5 space-y-4">
          <div>
            <label
              for="invoice"
              class="mb-1 block text-sm font-medium text-slate-700"
            >
              Invoice
            </label>

            <select
              id="invoice"
              v-model="selectedInvoiceId"
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
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
          </div>

          <div
            v-if="selectedPayable"
            class="grid gap-4 rounded-lg bg-slate-50 p-4 sm:grid-cols-3"
          >
            <div>
              <p class="text-xs text-slate-500">
                Supplier
              </p>

              <p class="mt-1 text-sm font-medium text-slate-900">
                {{ selectedPayable.supplierId }}
              </p>
            </div>

            <div>
              <p class="text-xs text-slate-500">
                Total Invoice
              </p>

              <p class="mt-1 text-sm font-medium text-slate-900">
                {{ formatCurrency(selectedPayable.total) }}
              </p>
            </div>

            <div>
              <p class="text-xs text-slate-500">
                Outstanding
              </p>

              <p class="mt-1 text-sm font-semibold text-slate-900">
                {{ formattedOutstanding }}
              </p>
            </div>

            <div>
              <p class="text-xs text-slate-500">
                Sudah Dibayar
              </p>

              <p class="mt-1 text-sm font-medium text-slate-900">
                {{ formatCurrency(selectedPayable.paid) }}
              </p>
            </div>

            <div>
              <p class="text-xs text-slate-500">
                Status
              </p>

              <p class="mt-1 text-sm font-medium text-slate-900">
                {{
                  paymentStatusLabel[
                    selectedPayable.paymentStatus
                  ] || selectedPayable.paymentStatus
                }}
              </p>
            </div>

            <div>
              <p class="text-xs text-slate-500">
                Jatuh Tempo
              </p>

              <p class="mt-1 text-sm font-medium text-slate-900">
                {{
                  new Intl.DateTimeFormat('id-ID', {
                    dateStyle: 'medium',
                  }).format(
                    new Date(selectedPayable.dueDate),
                  )
                }}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section
        class="rounded-xl border border-slate-200 bg-white p-6"
      >
        <h2 class="text-lg font-semibold text-slate-900">
          Pembayaran
        </h2>

        <div class="mt-5 grid gap-4 sm:grid-cols-2">
          <div>
            <label
              for="amount"
              class="mb-1 block text-sm font-medium text-slate-700"
            >
              Jumlah Pembayaran
            </label>

            <input
              id="amount"
              v-model.number="amount"
              type="number"
              min="1"
              step="1"
              inputmode="numeric"
              placeholder="Masukkan jumlah"
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
            />

            <p class="mt-1 text-xs text-slate-500">
              Maksimal:
              {{ formattedOutstanding }}
            </p>
          </div>

          <div>
            <label
              for="method"
              class="mb-1 block text-sm font-medium text-slate-700"
            >
              Metode Pembayaran
            </label>

            <select
              id="method"
              v-model="method"
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
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

          <div>
            <label
              for="paymentDate"
              class="mb-1 block text-sm font-medium text-slate-700"
            >
              Tanggal Pembayaran
            </label>

            <input
              id="paymentDate"
              v-model="paymentDate"
              type="date"
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
            />
          </div>

          <div>
            <label
              for="referenceNumber"
              class="mb-1 block text-sm font-medium text-slate-700"
            >
              Nomor Referensi
              <span class="font-normal text-slate-400">
                (opsional)
              </span>
            </label>

            <input
              id="referenceNumber"
              v-model="referenceNumber"
              type="text"
              placeholder="Nomor transfer / bukti pembayaran"
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
            />
          </div>

          <div class="sm:col-span-2">
            <label
              for="notes"
              class="mb-1 block text-sm font-medium text-slate-700"
            >
              Catatan
              <span class="font-normal text-slate-400">
                (opsional)
              </span>
            </label>

            <textarea
              id="notes"
              v-model="notes"
              rows="3"
              placeholder="Catatan pembayaran"
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
            />
          </div>
        </div>
      </section>

      <div class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <button
          type="button"
          class="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          @click="router.push('/supplier-payments')"
        >
          Batal
        </button>

        <button
          type="submit"
          :disabled="isSubmitting"
          class="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {{
            isSubmitting
              ? 'Menyimpan...'
              : 'Simpan Pembayaran'
          }}
        </button>
      </div>
    </form>
  </div>
</template>