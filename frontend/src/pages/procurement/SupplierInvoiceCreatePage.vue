<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createSupplierInvoice,
  getGoodsReceipts,
  getPurchases,
} from '../../api/procurement'
import type {
  GoodsReceipt,
  Purchase,
  SupplierInvoicePayload,
} from '../../types/procurement'

const route = useRoute()
const router = useRouter()

const goodsReceipts = ref<GoodsReceipt[]>([])
const purchases = ref<Purchase[]>([])

const selectedReceiptId = ref('')
const invoiceNumber = ref('')
const invoiceDate = ref('')
const dueDate = ref('')
const tax = ref(0)
const shippingCost = ref(0)

const isLoading = ref(true)
const isSubmitting = ref(false)
const errorMessage = ref('')
const validationMessage = ref('')

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)

const selectedReceipt = computed(() =>
  goodsReceipts.value.find(
    (receipt) => receipt.id === selectedReceiptId.value,
  ),
)

const selectedPurchase = computed(() => {
  if (!selectedReceipt.value) {
    return undefined
  }

  return purchases.value.find(
    (purchase) =>
      purchase.receiptId === selectedReceipt.value?.id,
  )
})

const subtotal = computed(
  () => selectedPurchase.value?.total ?? 0,
)

const total = computed(
  () =>
    subtotal.value +
    Number(tax.value || 0) +
    Number(shippingCost.value || 0),
)

const availableReceipts = computed(() => {
  return goodsReceipts.value.filter((receipt) => {
    return purchases.value.some(
      (purchase) =>
        purchase.receiptId === receipt.id,
    )
  })
})

const setDefaultDates = () => {
  const today = new Date()

  const todayString = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, '0'),
    String(today.getDate()).padStart(2, '0'),
  ].join('-')

  const due = new Date(today)
  due.setDate(due.getDate() + 30)

  const dueString = [
    due.getFullYear(),
    String(due.getMonth() + 1).padStart(2, '0'),
    String(due.getDate()).padStart(2, '0'),
  ].join('-')

  invoiceDate.value = todayString
  dueDate.value = dueString
}

const loadData = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const accessToken = localStorage.getItem('access_token')

    if (!accessToken) {
      throw new Error('Sesi login tidak ditemukan.')
    }

    const [receiptList, purchaseList] =
      await Promise.all([
        getGoodsReceipts(accessToken),
        getPurchases(accessToken),
      ])

    goodsReceipts.value = receiptList
    purchases.value = purchaseList

    const queryReceiptId =
      typeof route.query.receiptId === 'string'
        ? route.query.receiptId
        : ''

    if (
      queryReceiptId &&
      availableReceipts.value.some(
        (receipt) => receipt.id === queryReceiptId,
      )
    ) {
      selectedReceiptId.value = queryReceiptId
    } else if (availableReceipts.value.length === 1) {
      selectedReceiptId.value =
        availableReceipts.value[0].id
    }

    setDefaultDates()
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data supplier invoice.'
  } finally {
    isLoading.value = false
  }
}

const validateForm = () => {
  validationMessage.value = ''

  if (!selectedReceiptId.value) {
    validationMessage.value =
      'Goods Receipt wajib dipilih.'
    return false
  }

  if (!selectedPurchase.value) {
    validationMessage.value =
      'Purchase untuk Goods Receipt yang dipilih tidak ditemukan.'
    return false
  }

  if (!invoiceNumber.value.trim()) {
    validationMessage.value =
      'Nomor invoice supplier wajib diisi.'
    return false
  }

  if (!invoiceDate.value) {
    validationMessage.value =
      'Tanggal invoice wajib diisi.'
    return false
  }

  if (!dueDate.value) {
    validationMessage.value =
      'Tanggal jatuh tempo wajib diisi.'
    return false
  }

  if (dueDate.value < invoiceDate.value) {
    validationMessage.value =
      'Tanggal jatuh tempo tidak boleh lebih awal dari tanggal invoice.'
    return false
  }

  if (Number(tax.value) < 0) {
    validationMessage.value =
      'Tax tidak boleh kurang dari 0.'
    return false
  }

  if (Number(shippingCost.value) < 0) {
    validationMessage.value =
      'Biaya pengiriman tidak boleh kurang dari 0.'
    return false
  }

  return true
}

const toDateTime = (date: string) =>
  `${date}T00:00:00`

const submit = async () => {
  if (!validateForm()) {
    return
  }

  const accessToken = localStorage.getItem('access_token')

  if (!accessToken) {
    validationMessage.value =
      'Sesi login tidak ditemukan.'
    return
  }

  const confirmed = window.confirm(
    `Buat Supplier Invoice ${invoiceNumber.value.trim()} dengan total ${formatCurrency(total.value)}?`,
  )

  if (!confirmed) {
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''
  validationMessage.value = ''

  try {
    const payload: SupplierInvoicePayload = {
      receiptId: selectedReceiptId.value,
      invoiceNumber: invoiceNumber.value.trim(),
      invoiceDate: toDateTime(invoiceDate.value),
      dueDate: toDateTime(dueDate.value),
      tax: Number(tax.value),
      shippingCost: Number(shippingCost.value),
    }

    const invoice = await createSupplierInvoice(
      accessToken,
      payload,
    )

    router.push(
      `/supplier-invoices/${invoice.id}`,
    )
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal membuat supplier invoice.'
  } finally {
    isSubmitting.value = false
  }
}

const cancel = () => {
  router.push('/supplier-invoices')
}

onMounted(loadData)
</script>

<template>
  <section class="mx-auto w-full max-w-7xl space-y-6">
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
            @click="cancel"
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
          Buat Invoice
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
          Buat Supplier Invoice
        </h1>

        <p
          class="mt-2 max-w-2xl text-sm leading-6 text-[#6B756F]"
        >
          Buat invoice supplier berdasarkan Goods Receipt
          yang sudah memiliki Purchase.
        </p>
      </div>

      <button
        type="button"
        class="inline-flex min-h-11 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="isSubmitting"
        @click="cancel"
      >
        Kembali
      </button>
    </header>

    <!-- Loading -->
    <div
      v-if="isLoading"
      class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
      aria-live="polite"
      aria-busy="true"
    >
      <div class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6">
        <div class="h-5 w-48 animate-pulse rounded bg-[#E7ECE9]" />
        <div class="mt-2 h-4 w-72 max-w-full animate-pulse rounded bg-[#F1F4F2]" />
      </div>

      <div class="space-y-6 p-5 sm:p-6">
        <div class="space-y-3">
          <div class="h-4 w-32 animate-pulse rounded bg-[#E7ECE9]" />
          <div class="h-11 w-full animate-pulse rounded-lg bg-[#F1F4F2]" />
        </div>

        <div class="grid gap-5 md:grid-cols-2">
          <div class="space-y-3 md:col-span-2">
            <div class="h-4 w-40 animate-pulse rounded bg-[#E7ECE9]" />
            <div class="h-11 w-full animate-pulse rounded-lg bg-[#F1F4F2]" />
          </div>

          <div class="space-y-3">
            <div class="h-4 w-32 animate-pulse rounded bg-[#E7ECE9]" />
            <div class="h-11 w-full animate-pulse rounded-lg bg-[#F1F4F2]" />
          </div>

          <div class="space-y-3">
            <div class="h-4 w-32 animate-pulse rounded bg-[#E7ECE9]" />
            <div class="h-11 w-full animate-pulse rounded-lg bg-[#F1F4F2]" />
          </div>
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
          <h2 class="font-semibold text-[#8E2B22]">
            Gagal memuat data
          </h2>

          <p class="mt-1 text-sm leading-6 text-[#A33A2E]">
            {{ errorMessage }}
          </p>

          <button
            type="button"
            class="mt-4 inline-flex min-h-11 items-center justify-center rounded-lg bg-[#C0392B] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#A93226] focus:outline-none focus:ring-2 focus:ring-[#C0392B]/30"
            @click="loadData"
          >
            Coba Lagi
          </button>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div
      v-else-if="availableReceipts.length === 0"
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
            d="M9 14.25 11.25 16.5 15 12.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
          />
        </svg>
      </div>

      <h2
        class="mt-4 text-lg font-semibold text-[#17201C]"
      >
        Belum ada Goods Receipt yang dapat dibuatkan invoice
      </h2>

      <p
        class="mx-auto mt-2 max-w-lg text-sm leading-6 text-[#6B756F]"
      >
        Supplier Invoice hanya dapat dibuat dari Goods
        Receipt yang sudah memiliki Purchase.
      </p>

      <button
        type="button"
        class="mt-5 inline-flex min-h-11 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
        @click="cancel"
      >
        Kembali ke Supplier Invoice
      </button>
    </div>

    <!-- Form -->
    <form
      v-else
      class="space-y-6"
      @submit.prevent="submit"
    >
      <div
        class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]"
      >
        <!-- Main Form -->
        <div class="space-y-6">
          <!-- Reference -->
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
                Pilih Goods Receipt sebagai dasar invoice supplier.
              </p>
            </div>

            <div class="space-y-5 p-5 sm:p-6">
              <div>
                <label
                  for="receipt"
                  class="block text-sm font-semibold text-[#46514B]"
                >
                  Goods Receipt
                  <span
                    class="text-[#C0392B]"
                    aria-hidden="true"
                  >
                    *
                  </span>
                </label>

                <select
                  id="receipt"
                  v-model="selectedReceiptId"
                  required
                  class="mt-2 min-h-11 w-full rounded-lg border border-[#C8D1CC] bg-white px-3 py-2 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                >
                  <option value="">
                    Pilih Goods Receipt
                  </option>

                  <option
                    v-for="receipt in availableReceipts"
                    :key="receipt.id"
                    :value="receipt.id"
                  >
                    {{ receipt.receiptNumber }}
                    — PO {{ receipt.purchaseOrderId }}
                  </option>
                </select>

                <p
                  class="mt-2 text-xs text-[#6B756F]"
                >
                  Invoice akan menggunakan Purchase yang terhubung
                  dengan Goods Receipt tersebut.
                </p>
              </div>

              <div
                v-if="selectedReceipt && selectedPurchase"
                class="rounded-lg border border-[#D6DDD9] bg-[#F8FAF9]"
              >
                <div
                  class="border-b border-[#D6DDD9] px-4 py-3"
                >
                  <h3
                    class="text-sm font-semibold text-[#46514B]"
                  >
                    Detail Referensi
                  </h3>
                </div>

                <dl
                  class="grid gap-x-6 gap-y-4 p-4 sm:grid-cols-2"
                >
                  <div>
                    <dt class="text-xs text-[#6B756F]">
                      Goods Receipt
                    </dt>

                    <dd
                      class="mt-1 font-medium text-[#17201C]"
                    >
                      {{ selectedReceipt.receiptNumber }}
                    </dd>
                  </div>

                  <div>
                    <dt class="text-xs text-[#6B756F]">
                      Purchase
                    </dt>

                    <dd
                      class="mt-1 font-medium text-[#17201C]"
                    >
                      {{ selectedPurchase.purchaseNumber }}
                    </dd>
                  </div>

                  <div>
                    <dt class="text-xs text-[#6B756F]">
                      Supplier
                    </dt>

                    <dd
                      class="mt-1 break-all font-medium text-[#17201C]"
                    >
                      {{ selectedPurchase.supplierName || selectedPurchase.supplierId }}
                    </dd>
                  </div>

                  <div>
                    <dt class="text-xs text-[#6B756F]">
                      Purchase Total
                    </dt>

                    <dd
                      class="mt-1 font-semibold tabular-nums text-[#17201C]"
                    >
                      {{ formatCurrency(selectedPurchase.total) }}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </section>

          <!-- Invoice Information -->
          <section
            class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
          >
            <div
              class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6"
            >
              <h2
                class="text-base font-semibold text-[#17201C]"
              >
                Informasi Invoice
              </h2>

              <p
                class="mt-1 text-sm text-[#6B756F]"
              >
                Masukkan informasi invoice yang diterbitkan supplier.
              </p>
            </div>

            <div
              class="grid gap-5 p-5 sm:p-6 md:grid-cols-2"
            >
              <div class="md:col-span-2">
                <label
                  for="invoiceNumber"
                  class="block text-sm font-semibold text-[#46514B]"
                >
                  Nomor Invoice Supplier
                  <span
                    class="text-[#C0392B]"
                    aria-hidden="true"
                  >
                    *
                  </span>
                </label>

                <input
                  id="invoiceNumber"
                  v-model="invoiceNumber"
                  type="text"
                  autocomplete="off"
                  required
                  placeholder="Contoh: INV-SUP-001"
                  class="mt-2 min-h-11 w-full rounded-lg border border-[#C8D1CC] px-3 py-2 text-sm text-[#17201C] outline-none transition placeholder:text-[#9AA39E] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                />
              </div>

              <div>
                <label
                  for="invoiceDate"
                  class="block text-sm font-semibold text-[#46514B]"
                >
                  Tanggal Invoice
                  <span
                    class="text-[#C0392B]"
                    aria-hidden="true"
                  >
                    *
                  </span>
                </label>

                <input
                  id="invoiceDate"
                  v-model="invoiceDate"
                  type="date"
                  required
                  class="mt-2 min-h-11 w-full rounded-lg border border-[#C8D1CC] bg-white px-3 py-2 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                />
              </div>

              <div>
                <label
                  for="dueDate"
                  class="block text-sm font-semibold text-[#46514B]"
                >
                  Jatuh Tempo
                  <span
                    class="text-[#C0392B]"
                    aria-hidden="true"
                  >
                    *
                  </span>
                </label>

                <input
                  id="dueDate"
                  v-model="dueDate"
                  type="date"
                  required
                  class="mt-2 min-h-11 w-full rounded-lg border border-[#C8D1CC] bg-white px-3 py-2 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                />
              </div>

              <div>
                <label
                  for="tax"
                  class="block text-sm font-semibold text-[#46514B]"
                >
                  Tax
                </label>

                <div class="relative mt-2">
                  <span
                    class="pointer-events-none absolute inset-y-0 left-3 flex items-center text-sm text-[#6B756F]"
                  >
                    Rp
                  </span>

                  <input
                    id="tax"
                    v-model.number="tax"
                    type="number"
                    min="0"
                    step="1"
                    inputmode="numeric"
                    class="min-h-11 w-full rounded-lg border border-[#C8D1CC] bg-white py-2 pl-10 pr-3 text-right text-sm tabular-nums text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                  />
                </div>
              </div>

              <div>
                <label
                  for="shippingCost"
                  class="block text-sm font-semibold text-[#46514B]"
                >
                  Shipping Cost
                </label>

                <div class="relative mt-2">
                  <span
                    class="pointer-events-none absolute inset-y-0 left-3 flex items-center text-sm text-[#6B756F]"
                  >
                    Rp
                  </span>

                  <input
                    id="shippingCost"
                    v-model.number="shippingCost"
                    type="number"
                    min="0"
                    step="1"
                    inputmode="numeric"
                    class="min-h-11 w-full rounded-lg border border-[#C8D1CC] bg-white py-2 pl-10 pr-3 text-right text-sm tabular-nums text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                  />
                </div>
              </div>
            </div>
          </section>

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

          <!-- Form Actions -->
          <div
            class="flex flex-col-reverse gap-3 border-t border-[#D6DDD9] pt-5 sm:flex-row sm:justify-end"
          >
            <button
              type="button"
              class="inline-flex min-h-11 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-5 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="isSubmitting"
              @click="cancel"
            >
              Batal
            </button>

            <button
              type="submit"
              class="inline-flex min-h-11 items-center justify-center rounded-lg bg-[#176B4D] px-5 py-2 text-sm font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="isSubmitting"
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
                  : 'Simpan Supplier Invoice'
              }}
            </button>
          </div>
        </div>

        <!-- Context / Summary -->
        <aside class="xl:sticky xl:top-6 xl:self-start">
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
                Supplier Invoice
              </h2>
            </div>

            <div class="p-5">
              <div
                v-if="selectedReceipt && selectedPurchase"
                class="space-y-4"
              >
                <div>
                  <p class="text-xs text-[#6B756F]">
                    Invoice
                  </p>

                  <p
                    class="mt-1 break-all font-medium text-[#17201C]"
                  >
                    {{ invoiceNumber || 'Belum diisi' }}
                  </p>
                </div>

                <div>
                  <p class="text-xs text-[#6B756F]">
                    Goods Receipt
                  </p>

                  <p
                    class="mt-1 font-medium text-[#17201C]"
                  >
                    {{ selectedReceipt.receiptNumber }}
                  </p>
                </div>

                <div>
                  <p class="text-xs text-[#6B756F]">
                    Purchase
                  </p>

                  <p
                    class="mt-1 font-medium text-[#17201C]"
                  >
                    {{ selectedPurchase.purchaseNumber }}
                  </p>
                </div>

                <div
                  class="border-t border-[#D6DDD9] pt-4"
                >
                  <div
                    class="flex items-center justify-between gap-4 text-sm"
                  >
                    <span class="text-[#6B756F]">
                      Subtotal
                    </span>

                    <span
                      class="font-medium tabular-nums text-[#17201C]"
                    >
                      {{ formatCurrency(subtotal) }}
                    </span>
                  </div>

                  <div
                    class="mt-3 flex items-center justify-between gap-4 text-sm"
                  >
                    <span class="text-[#6B756F]">
                      Tax
                    </span>

                    <span
                      class="font-medium tabular-nums text-[#17201C]"
                    >
                      {{ formatCurrency(Number(tax) || 0) }}
                    </span>
                  </div>

                  <div
                    class="mt-3 flex items-center justify-between gap-4 text-sm"
                  >
                    <span class="text-[#6B756F]">
                      Shipping
                    </span>

                    <span
                      class="font-medium tabular-nums text-[#17201C]"
                    >
                      {{
                        formatCurrency(
                          Number(shippingCost) || 0,
                        )
                      }}
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
                        Total
                      </span>

                      <span
                        class="text-xl font-bold tabular-nums text-[#176B4D]"
                      >
                        {{ formatCurrency(total) }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div
                v-else
                class="py-2"
              >
                <p
                  class="text-sm leading-6 text-[#6B756F]"
                >
                  Pilih Goods Receipt untuk melihat
                  ringkasan invoice.
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
              Total invoice dihitung dari Purchase Total,
              Tax, dan Shipping Cost.
            </p>
          </div>
        </aside>
      </div>
    </form>
  </section>
</template>