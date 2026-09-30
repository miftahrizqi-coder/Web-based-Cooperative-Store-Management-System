<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createGoodsReceipt,
  getGoodsReceipts,
  getPurchaseOrder,
} from '../../api/procurement'
import type {
  GoodsReceiptPayload,
  PurchaseOrder,
} from '../../types/procurement'
import { useAuth } from '../../stores/auth'

interface ReceiptRow {
  productId: string
  name: string
  orderedQuantity: number
  previouslyReceivedQuantity: number
  receivedQuantity: number
  acceptedQuantity: number
  rejectedQuantity: number
  rejectionReason: string
}

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const purchaseOrder = ref<PurchaseOrder | null>(null)
const isLoading = ref(true)
const isSubmitting = ref(false)

const errorMessage = ref('')
const submitError = ref('')
const validationMessage = ref('')
const notes = ref('')

const rows = reactive<ReceiptRow[]>([])

const purchaseOrderId = computed(
  () => String(route.params.id),
)

/**
 * Quantity yang masih bisa diterima
 * sebelum receipt saat ini disimpan.
 */
function currentRemaining(row: ReceiptRow) {
  return Math.max(
    row.orderedQuantity -
      row.previouslyReceivedQuantity,
    0,
  )
}

function validateRows(): string | null {
  for (const row of rows) {
    const available = currentRemaining(row)

    if (row.receivedQuantity <= 0) {
      return `Jumlah diterima untuk ${row.name} harus lebih dari 0.`
    }

    if (row.receivedQuantity > available) {
      return `Jumlah diterima untuk ${row.name} melebihi sisa quantity yang dapat diterima.`
    }

    if (
      row.acceptedQuantity < 0 ||
      row.rejectedQuantity < 0
    ) {
      return `Quantity accepted/rejected untuk ${row.name} tidak valid.`
    }

    if (
      row.acceptedQuantity +
        row.rejectedQuantity !==
      row.receivedQuantity
    ) {
      return `Accepted + rejected untuk ${row.name} harus sama dengan received.`
    }

    if (
      row.rejectedQuantity > 0 &&
      !row.rejectionReason.trim()
    ) {
      return `Alasan penolakan wajib diisi untuk ${row.name}.`
    }
  }

  return null
}

function updateAcceptedFromReceived(row: ReceiptRow) {
  if (row.acceptedQuantity > row.receivedQuantity) {
    row.acceptedQuantity = row.receivedQuantity
  }

  row.rejectedQuantity =
    row.receivedQuantity -
    row.acceptedQuantity
}

function updateRejectedFromReceived(row: ReceiptRow) {
  if (row.rejectedQuantity > row.receivedQuantity) {
    row.rejectedQuantity = row.receivedQuantity
  }

  row.acceptedQuantity =
    row.receivedQuantity -
    row.rejectedQuantity
}

async function loadPurchaseOrder() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const [result, previousReceipts] =
      await Promise.all([
        getPurchaseOrder(
          token.value,
          purchaseOrderId.value,
        ),
        getGoodsReceipts(token.value),
      ])

    if (
      result.status !== 'ORDERED' &&
      result.status !== 'PARTIALLY_RECEIVED'
    ) {
      errorMessage.value =
        'Purchase Order ini belum dapat menerima barang. Status harus Ordered atau Partially Received.'
      return
    }

    purchaseOrder.value = result

    /**
     * Ambil hanya Goods Receipt yang berasal
     * dari Purchase Order ini.
     */
    const receiptsForPurchaseOrder =
      previousReceipts.filter(
        (receipt) =>
          receipt.purchaseOrderId ===
          purchaseOrderId.value,
      )

    rows.splice(0, rows.length)

    for (const item of result.items) {
      /**
       * Previously Received dihitung berdasarkan
       * seluruh receivedQuantity dari receipt sebelumnya.
       *
       * Bukan acceptedQuantity, karena quantity rejected
       * tetap sudah diterima secara fisik dan menjadi bagian
       * dari quantity PO yang sudah diproses.
       */
      const previouslyReceivedQuantity =
        receiptsForPurchaseOrder.reduce(
          (total, receipt) => {
            const receiptItem = receipt.items.find(
              (receivedItem) =>
                receivedItem.productId ===
                item.productId,
            )

            return (
              total +
              (receiptItem?.receivedQuantity ?? 0)
            )
          },
          0,
        )

      rows.push({
        productId: item.productId,
        name: item.name,
        orderedQuantity: item.quantity,
        previouslyReceivedQuantity,
        receivedQuantity: 0,
        acceptedQuantity: 0,
        rejectedQuantity: 0,
        rejectionReason: '',
      })
    }
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil purchase order.'
  } finally {
    isLoading.value = false
  }
}

async function submitReceipt() {
  if (!token.value || !purchaseOrder.value) {
    submitError.value =
      'Sesi atau data Purchase Order tidak tersedia.'
    return
  }

  validationMessage.value = ''

  const validationError = validateRows()

  if (validationError) {
    validationMessage.value = validationError
    return
  }

  if (
    !window.confirm(
      'Simpan penerimaan barang ini? Quantity accepted akan menambah stok.',
    )
  ) {
    return
  }

  isSubmitting.value = true
  submitError.value = ''

  const payload: GoodsReceiptPayload = {
    purchaseOrderId: purchaseOrder.value.id,
    items: rows.map((row) => ({
      productId: row.productId,
      name: row.name,
      receivedQuantity: row.receivedQuantity,
      acceptedQuantity: row.acceptedQuantity,
      rejectedQuantity: row.rejectedQuantity,
      rejectionReason:
        row.rejectedQuantity > 0
          ? row.rejectionReason.trim()
          : null,
    })),
    notes: notes.value.trim() || null,
  }

  try {
    const receipt = await createGoodsReceipt(
      token.value,
      payload,
    )

    router.push(
      `/goods-receipts/${receipt.id}`,
    )
  } catch (error) {
    submitError.value =
      error instanceof Error
        ? error.message
        : 'Gagal membuat penerimaan barang.'
  } finally {
    isSubmitting.value = false
  }
}

onMounted(loadPurchaseOrder)
</script>

<template>
  <section class="space-y-6">
    <div>
      <button
        type="button"
        class="text-sm font-medium text-green-800 hover:underline focus:outline-none focus:ring-2 focus:ring-green-700"
        @click="router.push('/purchase-orders')"
      >
        ← Kembali ke Purchase Order
      </button>

      <h1 class="mt-3 text-2xl font-semibold text-gray-900">
        Penerimaan Barang
      </h1>

      <p class="mt-1 text-sm text-gray-600">
        Catat barang yang diterima dari Purchase Order.
      </p>
    </div>

    <div
      v-if="isLoading"
      class="space-y-4 rounded-xl border border-gray-200 bg-white p-6"
    >
      <div class="h-8 animate-pulse rounded bg-gray-100"></div>
      <div class="h-48 animate-pulse rounded bg-gray-100"></div>
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
      role="alert"
    >
      <h2 class="font-semibold text-red-800">
        Goods Receipt tidak dapat dibuat
      </h2>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>
    </div>

    <template v-else-if="purchaseOrder">
      <div
        v-if="validationMessage"
        class="rounded-xl border border-yellow-200 bg-yellow-50 p-4"
        role="alert"
      >
        <p class="text-sm text-yellow-800">
          {{ validationMessage }}
        </p>
      </div>

      <div
        v-if="submitError"
        class="rounded-xl border border-red-200 bg-red-50 p-4"
        role="alert"
      >
        <p class="text-sm text-red-700">
          {{ submitError }}
        </p>
      </div>

      <section
        class="rounded-xl border border-gray-200 bg-white p-6"
      >
        <div class="grid gap-5 sm:grid-cols-2">
          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Purchase Order
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ purchaseOrder.poNumber }}
            </p>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500"
            >
              Status
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ purchaseOrder.status }}
            </p>
          </div>
        </div>
      </section>

      <section
        class="overflow-x-auto rounded-xl border border-gray-200 bg-white"
      >
        <table class="min-w-[1100px] w-full text-left text-sm">
          <thead
            class="border-b border-gray-200 bg-gray-50"
          >
            <tr>
              <th class="px-4 py-3 font-medium text-gray-600">
                Produk
              </th>

              <th class="px-4 py-3 font-medium text-gray-600">
                Ordered
              </th>

              <th class="px-4 py-3 font-medium text-gray-600">
                Previously Received
              </th>

              <th class="px-4 py-3 font-medium text-gray-600">
                Remaining
              </th>

              <th class="px-4 py-3 font-medium text-gray-600">
                Received
              </th>

              <th class="px-4 py-3 font-medium text-gray-600">
                Accepted
              </th>

              <th class="px-4 py-3 font-medium text-gray-600">
                Rejected
              </th>

              <th class="px-4 py-3 font-medium text-gray-600">
                Alasan Penolakan
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="row in rows"
              :key="row.productId"
            >
              <td class="px-4 py-4">
                <p class="font-medium text-gray-900">
                  {{ row.name }}
                </p>
              </td>

              <td class="px-4 py-4 text-gray-700">
                {{ row.orderedQuantity }}
              </td>

              <td class="px-4 py-4 text-gray-700">
                {{ row.previouslyReceivedQuantity }}
              </td>

              <td class="px-4 py-4 font-medium text-gray-900">
                {{ currentRemaining(row) }}
              </td>

              <td class="px-4 py-4">
                <input
                  v-model.number="row.receivedQuantity"
                  type="number"
                  min="1"
                  :max="currentRemaining(row)"
                  class="w-24 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-700 focus:outline-none focus:ring-2 focus:ring-green-700"
                />
              </td>

              <td class="px-4 py-4">
                <input
                  v-model.number="row.acceptedQuantity"
                  type="number"
                  min="0"
                  :max="row.receivedQuantity"
                  class="w-24 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-700 focus:outline-none focus:ring-2 focus:ring-green-700"
                  @input="updateAcceptedFromReceived(row)"
                />
              </td>

              <td class="px-4 py-4">
                <input
                  v-model.number="row.rejectedQuantity"
                  type="number"
                  min="0"
                  :max="row.receivedQuantity"
                  class="w-24 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-700 focus:outline-none focus:ring-2 focus:ring-green-700"
                  @input="updateRejectedFromReceived(row)"
                />
              </td>

              <td class="px-4 py-4">
                <input
                  v-model="row.rejectionReason"
                  type="text"
                  :disabled="row.rejectedQuantity <= 0"
                  placeholder="Alasan jika ditolak"
                  class="w-56 rounded-lg border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-100 disabled:text-gray-400 focus:border-green-700 focus:outline-none focus:ring-2 focus:ring-green-700"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <p class="text-sm text-gray-600">
        Remaining menunjukkan quantity yang masih dapat
        diterima sebelum penerimaan saat ini.
      </p>

      <section
        class="rounded-xl border border-gray-200 bg-white p-6"
      >
        <label
          for="goods-receipt-notes"
          class="block text-sm font-medium text-gray-700"
        >
          Catatan
        </label>

        <textarea
          id="goods-receipt-notes"
          v-model="notes"
          rows="4"
          class="mt-2 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-700 focus:outline-none focus:ring-2 focus:ring-green-700"
          placeholder="Catatan penerimaan barang (opsional)"
        ></textarea>
      </section>

      <section
        class="flex flex-col gap-3 rounded-xl border border-gray-200 bg-white p-6 sm:flex-row sm:justify-end"
      >
        <button
          type="button"
          :disabled="isSubmitting"
          class="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
          @click="router.push('/purchase-orders')"
        >
          Batal
        </button>

        <button
          type="button"
          :disabled="isSubmitting"
          class="rounded-lg bg-green-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-900 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
          @click="submitReceipt"
        >
          {{
            isSubmitting
              ? 'Menyimpan...'
              : 'Simpan Penerimaan'
          }}
        </button>
      </section>
    </template>
  </section>
</template>