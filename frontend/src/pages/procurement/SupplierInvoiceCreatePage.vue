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

const selectedPurchase = computed(() =>{
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
  <section class="space-y-6">
    <div>
      <p
        class="text-sm font-medium text-emerald-700"
      >
        Procurement
      </p>

      <h1
        class="mt-1 text-2xl font-semibold text-slate-900"
      >
        Buat Supplier Invoice
      </h1>

      <p class="mt-1 text-sm text-slate-500">
        Buat invoice supplier berdasarkan Goods Receipt
        yang sudah memiliki Purchase.
      </p>
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
        Gagal memuat data
      </h2>

      <p
        class="mt-1 text-sm text-red-700"
      >
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-4 min-h-11 rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800"
        @click="loadData"
      >
        Coba Lagi
      </button>
    </div>

    <div
      v-else-if="availableReceipts.length === 0"
      class="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center"
    >
      <h2
        class="text-lg font-semibold text-slate-900"
      >
        Belum ada Goods Receipt yang dapat dibuatkan invoice
      </h2>

      <p
        class="mx-auto mt-2 max-w-lg text-sm text-slate-500"
      >
        Supplier Invoice hanya dapat dibuat dari Goods
        Receipt yang sudah memiliki Purchase.
      </p>

      <button
        type="button"
        class="mt-5 min-h-11 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        @click="cancel"
      >
        Kembali ke Supplier Invoice
      </button>
    </div>

    <form
      v-else
      class="space-y-6"
      @submit.prevent="submit"
    >
      <div
        class="rounded-xl border border-slate-200 bg-white p-6"
      >
        <h2
          class="text-lg font-semibold text-slate-900"
        >
          Referensi Transaksi
        </h2>

        <div class="mt-5 space-y-5">
          <div>
            <label
              for="receipt"
              class="block text-sm font-medium text-slate-700"
            >
              Goods Receipt
            </label>

            <select
              id="receipt"
              v-model="selectedReceiptId"
              class="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
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
          </div>

          <div
            v-if="selectedReceipt && selectedPurchase"
            class="grid gap-4 rounded-lg bg-slate-50 p-4 sm:grid-cols-2"
          >
            <div>
              <p class="text-xs text-slate-500">
                Goods Receipt
              </p>

              <p
                class="mt-1 font-medium text-slate-900"
              >
                {{ selectedReceipt.receiptNumber }}
              </p>
            </div>

            <div>
              <p class="text-xs text-slate-500">
                Purchase
              </p>

              <p
                class="mt-1 font-medium text-slate-900"
              >
                {{ selectedPurchase.purchaseNumber }}
              </p>
            </div>

            <div>
              <p class="text-xs text-slate-500">
                Supplier
              </p>

              <p
                class="mt-1 font-medium text-slate-900"
              >
                {{ selectedPurchase.supplierId }}
              </p>
            </div>

            <div>
              <p class="text-xs text-slate-500">
                Purchase Total
              </p>

              <p
                class="mt-1 font-medium text-slate-900"
              >
                {{ formatCurrency(selectedPurchase.total) }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div
        class="rounded-xl border border-slate-200 bg-white p-6"
      >
        <h2
          class="text-lg font-semibold text-slate-900"
        >
          Informasi Invoice
        </h2>

        <div
          class="mt-5 grid gap-5 md:grid-cols-2"
        >
          <div class="md:col-span-2">
            <label
              for="invoiceNumber"
              class="block text-sm font-medium text-slate-700"
            >
              Nomor Invoice Supplier
            </label>

            <input
              id="invoiceNumber"
              v-model="invoiceNumber"
              type="text"
              autocomplete="off"
              placeholder="Contoh: INV-SUP-001"
              class="mt-2 min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
            />
          </div>

          <div>
            <label
              for="invoiceDate"
              class="block text-sm font-medium text-slate-700"
            >
              Tanggal Invoice
            </label>

            <input
              id="invoiceDate"
              v-model="invoiceDate"
              type="date"
              class="mt-2 min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
            />
          </div>

          <div>
            <label
              for="dueDate"
              class="block text-sm font-medium text-slate-700"
            >
              Jatuh Tempo
            </label>

            <input
              id="dueDate"
              v-model="dueDate"
              type="date"
              class="mt-2 min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
            />
          </div>

          <div>
            <label
              for="tax"
              class="block text-sm font-medium text-slate-700"
            >
              Tax
            </label>

            <input
              id="tax"
              v-model.number="tax"
              type="number"
              min="0"
              step="1"
              class="mt-2 min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
            />
          </div>

          <div>
            <label
              for="shippingCost"
              class="block text-sm font-medium text-slate-700"
            >
              Shipping Cost
            </label>

            <input
              id="shippingCost"
              v-model.number="shippingCost"
              type="number"
              min="0"
              step="1"
              class="mt-2 min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
            />
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
          class="mt-5 space-y-3"
        >
          <div
            class="flex items-center justify-between gap-4 text-sm"
          >
            <span class="text-slate-500">
              Subtotal Purchase
            </span>

            <span
              class="font-medium text-slate-900"
            >
              {{ formatCurrency(subtotal) }}
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
              {{ formatCurrency(Number(tax) || 0) }}
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
                  Number(shippingCost) || 0,
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
                {{ formatCurrency(total) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="validationMessage"
        class="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800"
      >
        {{ validationMessage }}
      </div>

      <div
        class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end"
      >
        <button
          type="button"
          class="min-h-11 rounded-lg border border-slate-300 px-5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="isSubmitting"
          @click="cancel"
        >
          Batal
        </button>

        <button
          type="submit"
          class="min-h-11 rounded-lg bg-emerald-700 px-5 py-2 text-sm font-medium text-white hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="isSubmitting"
        >
          {{
            isSubmitting
              ? 'Menyimpan...'
              : 'Simpan Supplier Invoice'
          }}
        </button>
      </div>
    </form>
  </section>
</template>