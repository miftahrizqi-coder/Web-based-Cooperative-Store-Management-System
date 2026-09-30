<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../../stores/auth'
import { createGoodsReceipt, getPurchaseOrder } from '../../api/procurement'

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const purchaseOrderId = route.params.id as string

interface PurchaseOrderItem {
  supplierProductId: string
  productId: string
  sku: string
  name: string
  quantity: number
  unitPrice: number
}

interface PurchaseOrder {
  id: string
  poNumber: string
  supplierId: string
  status: string
  items: PurchaseOrderItem[]
}

interface ReceiptItemForm {
  productId: string
  name: string
  orderedQuantity: number
  previouslyReceivedQuantity: number
  remainingQuantity: number
  receivedQuantity: number
  acceptedQuantity: number
  rejectedQuantity: number
  rejectionReason: string
}

const purchaseOrder = ref<PurchaseOrder | null>(null)
const items = ref<ReceiptItemForm[]>([])
const notes = ref('')

const isLoading = ref(true)
const isSaving = ref(false)
const errorMessage = ref('')
const fieldError = ref('')

const canSubmit = computed(() => {
  if (!purchaseOrder.value || items.value.length === 0) {
    return false
  }

  return items.value.every((item) => {
    if (item.receivedQuantity <= 0) {
      return false
    }

    if (item.acceptedQuantity < 0 || item.rejectedQuantity < 0) {
      return false
    }

    if (
      item.acceptedQuantity + item.rejectedQuantity !==
      item.receivedQuantity
    ) {
      return false
    }

    if (
      item.receivedQuantity >
      item.remainingQuantity
    ) {
      return false
    }

    if (
      item.rejectedQuantity > 0 &&
      !item.rejectionReason.trim()
    ) {
      return false
    }

    return true
  })
})

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(Number(value) || 0)
}

function goBack() {
  router.push(`/purchases/${purchaseOrderId}`)
}

function createFormItems(order: PurchaseOrder) {
  items.value = order.items.map((item) => ({
    productId: item.productId,
    name: item.name,
    orderedQuantity: item.quantity,
    previouslyReceivedQuantity: 0,
    remainingQuantity: item.quantity,
    receivedQuantity: 0,
    acceptedQuantity: 0,
    rejectedQuantity: 0,
    rejectionReason: '',
  }))
}

async function loadPurchaseOrder() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  if (!purchaseOrderId) {
    errorMessage.value =
      'Purchase Order tidak ditemukan.'
    isLoading.value = false
    return
  }

  try {
    const result = await getPurchaseOrder(
      token.value,
      purchaseOrderId,
    )

    purchaseOrder.value = result as PurchaseOrder

    createFormItems(purchaseOrder.value)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data Purchase Order.'
  } finally {
    isLoading.value = false
  }
}

function updateReceivedQuantity(item: ReceiptItemForm) {
  if (item.receivedQuantity < 0) {
    item.receivedQuantity = 0
  }

  if (
    item.receivedQuantity >
    item.remainingQuantity
  ) {
    item.receivedQuantity =
      item.remainingQuantity
  }

  if (
    item.acceptedQuantity >
    item.receivedQuantity
  ) {
    item.acceptedQuantity =
      item.receivedQuantity
  }

  item.rejectedQuantity =
    Math.max(
      item.receivedQuantity -
        item.acceptedQuantity,
      0,
    )
}

function updateAcceptedQuantity(item: ReceiptItemForm) {
  if (item.acceptedQuantity < 0) {
    item.acceptedQuantity = 0
  }

  if (
    item.acceptedQuantity >
    item.receivedQuantity
  ) {
    item.acceptedQuantity =
      item.receivedQuantity
  }

  item.rejectedQuantity =
    item.receivedQuantity -
    item.acceptedQuantity
}

function updateRejectedQuantity(item: ReceiptItemForm) {
  if (item.rejectedQuantity < 0) {
    item.rejectedQuantity = 0
  }

  if (
    item.rejectedQuantity >
    item.receivedQuantity
  ) {
    item.rejectedQuantity =
      item.receivedQuantity
  }

  item.acceptedQuantity =
    item.receivedQuantity -
    item.rejectedQuantity
}

function validate() {
  fieldError.value = ''

  if (!purchaseOrder.value) {
    fieldError.value =
      'Purchase Order tidak ditemukan.'
    return false
  }

  if (items.value.length === 0) {
    fieldError.value =
      'Tidak ada item yang dapat diterima.'
    return false
  }

  for (const item of items.value) {
    if (!item.productId) {
      fieldError.value =
        `Product ID untuk ${item.name} tidak ditemukan.`
      return false
    }

    if (item.receivedQuantity <= 0) {
      fieldError.value =
        `Jumlah diterima untuk ${item.name} harus lebih dari 0.`
      return false
    }

    if (
      item.receivedQuantity >
      item.remainingQuantity
    ) {
      fieldError.value =
        `Jumlah diterima untuk ${item.name} melebihi sisa PO.`
      return false
    }

    if (
      item.acceptedQuantity +
        item.rejectedQuantity !==
      item.receivedQuantity
    ) {
      fieldError.value =
        `Jumlah diterima, diterima baik, dan ditolak untuk ${item.name} tidak sesuai.`
      return false
    }

    if (
      item.rejectedQuantity > 0 &&
      !item.rejectionReason.trim()
    ) {
      fieldError.value =
        `Alasan penolakan untuk ${item.name} wajib diisi.`
      return false
    }
  }

  return true
}

async function handleSubmit() {
  errorMessage.value = ''

  if (!validate()) {
    return
  }

  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    return
  }

  isSaving.value = true

  try {
    const payload = {
      purchaseOrderId,
      items: items.value.map((item) => ({
        productId: item.productId,
        name: item.name,
        receivedQuantity: item.receivedQuantity,
        acceptedQuantity: item.acceptedQuantity,
        rejectedQuantity: item.rejectedQuantity,
        rejectionReason:
          item.rejectedQuantity > 0
            ? item.rejectionReason.trim()
            : null,
      })),
      notes: notes.value.trim() || null,
    }

    const receipt = await createGoodsReceipt(
      token.value,
      payload,
    )

    await router.push(
      `/goods-receipts/${receipt.id}`,
    )
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Penerimaan gagal disimpan. Tidak ada perubahan pada stok. Coba lagi.'
  } finally {
    isSaving.value = false
  }
}

onMounted(loadPurchaseOrder)
</script>

<template>
  <div class="space-y-6">
    <div>
      <button
        type="button"
        class="text-sm font-medium text-[#176B4D] hover:underline"
        @click="goBack"
      >
        ← Kembali ke Purchase Order
      </button>

      <h1 class="mt-3 text-2xl font-bold text-[#12372A]">
        Penerimaan Barang
      </h1>

      <p class="mt-1 text-sm text-slate-600">
        Catat barang yang diterima dari supplier berdasarkan Purchase Order.
      </p>
    </div>

    <div
      v-if="isLoading"
      class="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600"
    >
      Memuat Purchase Order...
    </div>

    <div
      v-else-if="errorMessage && !purchaseOrder"
      class="rounded-xl border border-[#E7B8B2] bg-[#FEF3F2] p-4 text-sm text-[#C0392B]"
    >
      {{ errorMessage }}
    </div>

    <form
      v-else-if="purchaseOrder"
      class="space-y-6"
      @submit.prevent="handleSubmit"
    >
      <section
        class="rounded-xl border border-slate-200 bg-white p-5"
      >
        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <p class="text-xs font-medium uppercase text-slate-500">
              Purchase Order
            </p>
            <p class="mt-1 font-semibold text-[#12372A]">
              {{ purchaseOrder.poNumber }}
            </p>
          </div>

          <div>
            <p class="text-xs font-medium uppercase text-slate-500">
              Status
            </p>
            <p class="mt-1 font-semibold text-[#12372A]">
              {{ purchaseOrder.status }}
            </p>
          </div>
        </div>
      </section>

      <div
        v-if="fieldError"
        class="rounded-xl border border-[#E7B8B2] bg-[#FEF3F2] p-4 text-sm text-[#C0392B]"
      >
        {{ fieldError }}
      </div>

      <div
        v-if="errorMessage"
        class="rounded-xl border border-[#E7B8B2] bg-[#FEF3F2] p-4 text-sm text-[#C0392B]"
      >
        {{ errorMessage }}
      </div>

      <section
        class="overflow-hidden rounded-xl border border-slate-200 bg-white"
      >
        <div class="border-b border-slate-200 p-5">
          <h2 class="font-semibold text-[#12372A]">
            Item penerimaan
          </h2>
          <p class="mt-1 text-sm text-slate-500">
            Jumlah diterima tidak boleh melebihi sisa Purchase Order.
          </p>
        </div>

        <div class="divide-y divide-slate-200">
          <div
            v-for="item in items"
            :key="item.productId"
            class="space-y-5 p-5"
          >
            <div>
              <p class="font-semibold text-[#12372A]">
                {{ item.name }}
              </p>

              <p class="mt-1 text-xs text-slate-500">
                Product ID: {{ item.productId }}
              </p>
            </div>

            <div class="grid gap-4 sm:grid-cols-3">
              <div>
                <label class="text-xs font-medium text-slate-500">
                  Jumlah PO
                </label>
                <p class="mt-1 font-semibold">
                  {{ item.orderedQuantity }}
                </p>
              </div>

              <div>
                <label class="text-xs font-medium text-slate-500">
                  Sudah diterima
                </label>
                <p class="mt-1 font-semibold">
                  {{ item.previouslyReceivedQuantity }}
                </p>
              </div>

              <div>
                <label class="text-xs font-medium text-slate-500">
                  Sisa
                </label>
                <p class="mt-1 font-semibold text-[#176B4D]">
                  {{ item.remainingQuantity }}
                </p>
              </div>
            </div>

            <div class="grid gap-4 sm:grid-cols-3">
              <div>
                <label
                  class="block text-sm font-medium text-slate-700"
                >
                  Jumlah diterima
                </label>

                <input
                  v-model.number="item.receivedQuantity"
                  type="number"
                  min="1"
                  :max="item.remainingQuantity"
                  class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                  @input="updateReceivedQuantity(item)"
                />
              </div>

              <div>
                <label
                  class="block text-sm font-medium text-slate-700"
                >
                  Diterima baik
                </label>

                <input
                  v-model.number="item.acceptedQuantity"
                  type="number"
                  min="0"
                  :max="item.receivedQuantity"
                  class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                  @input="updateAcceptedQuantity(item)"
                />
              </div>

              <div>
                <label
                  class="block text-sm font-medium text-slate-700"
                >
                  Ditolak
                </label>

                <input
                  v-model.number="item.rejectedQuantity"
                  type="number"
                  min="0"
                  :max="item.receivedQuantity"
                  class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                  @input="updateRejectedQuantity(item)"
                />
              </div>
            </div>

            <div
              v-if="item.rejectedQuantity > 0"
            >
              <label
                class="block text-sm font-medium text-slate-700"
              >
                Alasan penolakan
              </label>

              <textarea
                v-model="item.rejectionReason"
                rows="2"
                class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                placeholder="Contoh: barang rusak atau jumlah tidak sesuai."
              />
            </div>

            <div
              class="rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-600"
            >
              Total diterima:
              <strong class="text-slate-900">
                {{ item.receivedQuantity }}
              </strong>
              · Baik:
              <strong class="text-[#176B4D]">
                {{ item.acceptedQuantity }}
              </strong>
              · Ditolak:
              <strong class="text-[#C0392B]">
                {{ item.rejectedQuantity }}
              </strong>
            </div>
          </div>
        </div>
      </section>

      <section
        class="rounded-xl border border-slate-200 bg-white p-5"
      >
        <label
          class="block text-sm font-medium text-slate-700"
        >
          Catatan
        </label>

        <textarea
          v-model="notes"
          rows="3"
          class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
          placeholder="Catatan penerimaan barang (opsional)"
        />
      </section>

      <div
        class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end"
      >
        <button
          type="button"
          class="rounded-lg border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          :disabled="isSaving"
          @click="goBack"
        >
          Batal
        </button>

        <button
          type="submit"
          class="rounded-lg bg-[#176B4D] px-5 py-3 text-sm font-semibold text-white hover:bg-[#12372A] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="isSaving || !canSubmit"
        >
          {{ isSaving ? 'Menyimpan...' : 'Simpan Penerimaan' }}
        </button>
      </div>
    </form>
  </div>
</template>