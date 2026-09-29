<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  approvePurchaseOrder,
  cancelPurchaseOrder,
  getPurchaseOrder,
  orderPurchaseOrder,
  submitPurchaseOrder,
} from '../../api/procurement'

import type {
  PurchaseOrder,
  PurchaseOrderStatus,
} from '../../types/procurement'

import { useAuth } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const { token, currentUser } = useAuth()

const purchaseOrder = ref<PurchaseOrder | null>(null)

const isLoading = ref(true)
const isActionLoading = ref(false)

const errorMessage = ref('')
const actionError = ref('')

const purchaseOrderId = computed(
  () => String(route.params.id),
)

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatDate(value: string | null) {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function statusLabel(status: PurchaseOrderStatus) {
  const labels: Record<PurchaseOrderStatus, string> = {
    DRAFT: 'Draft',
    PENDING_APPROVAL: 'Menunggu persetujuan',
    APPROVED: 'Disetujui',
    ORDERED: 'Dipesan',
    PARTIALLY_RECEIVED: 'Sebagian diterima',
    RECEIVED: 'Diterima',
    COMPLETED: 'Selesai',
    CANCELLED: 'Dibatalkan',
  }

  return labels[status]
}

function statusClass(status: PurchaseOrderStatus) {
  const classes: Record<PurchaseOrderStatus, string> = {
    DRAFT: 'bg-gray-100 text-gray-700',
    PENDING_APPROVAL: 'bg-yellow-100 text-yellow-800',
    APPROVED: 'bg-green-100 text-green-800',
    ORDERED: 'bg-blue-100 text-blue-800',
    PARTIALLY_RECEIVED: 'bg-orange-100 text-orange-800',
    RECEIVED: 'bg-emerald-100 text-emerald-800',
    COMPLETED: 'bg-green-100 text-green-800',
    CANCELLED: 'bg-red-100 text-red-800',
  }

  return classes[status]
}

const canEdit = computed(
  () =>
    purchaseOrder.value?.status === 'DRAFT' &&
    (currentUser.value?.role === 'admin' ||
      currentUser.value?.role === 'pengurus'),
)

const canSubmit = computed(
  () =>
    purchaseOrder.value?.status === 'DRAFT' &&
    (currentUser.value?.role === 'admin' ||
      currentUser.value?.role === 'pengurus'),
)

const canApprove = computed(() => {
  if (!purchaseOrder.value) {
    return false
  }

  return (
    purchaseOrder.value.status === 'PENDING_APPROVAL' &&
    (currentUser.value?.role === 'admin' ||
      currentUser.value?.role === 'pengurus') &&
    purchaseOrder.value.createdBy !== currentUser.value?.id
  )
})

const canOrder = computed(
  () =>
    purchaseOrder.value?.status === 'APPROVED' &&
    (currentUser.value?.role === 'admin' ||
      currentUser.value?.role === 'pengurus'),
)

const canCancel = computed(
  () =>
    Boolean(purchaseOrder.value) &&
    ['DRAFT', 'PENDING_APPROVAL', 'APPROVED'].includes(
      purchaseOrder.value!.status,
    ) &&
    (currentUser.value?.role === 'admin' ||
      currentUser.value?.role === 'pengurus'),
)

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
    purchaseOrder.value = await getPurchaseOrder(
      token.value,
      purchaseOrderId.value,
    )
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil detail purchase order.'
  } finally {
    isLoading.value = false
  }
}

async function runAction(
  action:
    | 'submit'
    | 'approve'
    | 'order'
    | 'cancel',
) {
  if (!token.value || !purchaseOrder.value) {
    actionError.value =
      'Sesi atau data purchase order tidak tersedia.'
    return
  }

  const messages = {
    submit: 'Kirim purchase order ini untuk persetujuan?',
    approve: 'Setujui purchase order ini?',
    order: 'Tandai purchase order sebagai sudah dipesan?',
    cancel: 'Batalkan purchase order ini?',
  }

  if (!window.confirm(messages[action])) {
    return
  }

  actionError.value = ''
  isActionLoading.value = true

  try {
    if (action === 'submit') {
      await submitPurchaseOrder(
        token.value,
        purchaseOrder.value.id,
      )
    }

    if (action === 'approve') {
      await approvePurchaseOrder(
        token.value,
        purchaseOrder.value.id,
      )
    }

    if (action === 'order') {
      await orderPurchaseOrder(
        token.value,
        purchaseOrder.value.id,
      )
    }

    if (action === 'cancel') {
      await cancelPurchaseOrder(
        token.value,
        purchaseOrder.value.id,
      )
    }

    await loadPurchaseOrder()
  } catch (error) {
    actionError.value =
      error instanceof Error
        ? error.message
        : 'Aksi purchase order gagal.'
  } finally {
    isActionLoading.value = false
  }
}

onMounted(loadPurchaseOrder)
</script>

<template>
  <section class="space-y-6">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <button
          type="button"
          class="text-sm font-medium text-green-800 hover:underline focus:outline-none focus:ring-2 focus:ring-green-700"
          @click="router.push('/purchase-orders')"
        >
          ← Kembali ke Purchase Order
        </button>

        <h1 class="mt-3 text-2xl font-semibold text-gray-900">
          {{ purchaseOrder?.poNumber || 'Detail Purchase Order' }}
        </h1>
      </div>

      <span
        v-if="purchaseOrder"
        class="self-start rounded-full px-3 py-1.5 text-sm font-medium"
        :class="statusClass(purchaseOrder.status)"
      >
        {{ statusLabel(purchaseOrder.status) }}
      </span>
    </div>

    <div
      v-if="isLoading"
      class="space-y-4 rounded-xl border border-gray-200 bg-white p-6"
    >
      <div class="h-8 animate-pulse rounded bg-gray-100" />
      <div class="h-32 animate-pulse rounded bg-gray-100" />
      <div class="h-48 animate-pulse rounded bg-gray-100" />
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
      role="alert"
    >
      <h2 class="font-semibold text-red-800">
        Purchase order gagal dimuat
      </h2>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
        @click="loadPurchaseOrder"
      >
        Coba lagi
      </button>
    </div>

    <template v-else-if="purchaseOrder">
      <div
        v-if="actionError"
        class="rounded-xl border border-red-200 bg-red-50 p-4"
        role="alert"
      >
        <p class="text-sm text-red-700">
          {{ actionError }}
        </p>
      </div>

      <section class="rounded-xl border border-gray-200 bg-white p-6">
        <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
              Supplier
            </p>

            <p class="mt-1 font-medium text-gray-900">
              {{ purchaseOrder.supplierId }}
            </p>
          </div>

          <div>
            <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
              Dibuat
            </p>

            <p class="mt-1 text-sm text-gray-900">
              {{ formatDate(purchaseOrder.createdAt) }}
            </p>
          </div>

          <div>
            <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
              Target pengiriman
            </p>

            <p class="mt-1 text-sm text-gray-900">
              {{ formatDate(purchaseOrder.expectedDeliveryDate) }}
            </p>
          </div>

          <div>
            <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
              Disetujui
            </p>

            <p class="mt-1 text-sm text-gray-900">
              {{ purchaseOrder.approvedBy || '-' }}
            </p>
          </div>
        </div>
      </section>

      <section class="overflow-x-auto rounded-xl border border-gray-200 bg-white">
        <table class="min-w-full text-left text-sm">
          <thead class="border-b border-gray-200 bg-gray-50">
            <tr>
              <th class="px-4 py-3 font-medium text-gray-600">
                Produk
              </th>

              <th class="px-4 py-3 font-medium text-gray-600">
                SKU
              </th>

              <th class="px-4 py-3 font-medium text-gray-600">
                Qty
              </th>

              <th class="px-4 py-3 font-medium text-gray-600">
                Harga
              </th>

              <th class="px-4 py-3 font-medium text-gray-600">
                Subtotal
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="item in purchaseOrder.items"
              :key="item.productId"
            >
              <td class="px-4 py-3 font-medium text-gray-900">
                {{ item.name }}
              </td>

              <td class="px-4 py-3 text-gray-700">
                {{ item.sku }}
              </td>

              <td class="px-4 py-3 text-gray-700">
                {{ item.quantity }}
              </td>

              <td class="px-4 py-3 text-gray-700">
                {{ formatCurrency(item.unitPrice) }}
              </td>

              <td class="px-4 py-3 font-medium text-gray-900">
                {{ formatCurrency(item.subtotal) }}
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="rounded-xl border border-gray-200 bg-white p-6">
        <dl class="ml-auto max-w-sm space-y-3 text-sm">
          <div class="flex justify-between">
            <dt class="text-gray-600">
              Subtotal
            </dt>

            <dd class="font-medium text-gray-900">
              {{ formatCurrency(purchaseOrder.subtotal) }}
            </dd>
          </div>

          <div class="flex justify-between">
            <dt class="text-gray-600">
              Diskon
            </dt>

            <dd class="font-medium text-gray-900">
              - {{ formatCurrency(purchaseOrder.discount) }}
            </dd>
          </div>

          <div class="flex justify-between">
            <dt class="text-gray-600">
              Pajak
            </dt>

            <dd class="font-medium text-gray-900">
              {{ formatCurrency(purchaseOrder.tax) }}
            </dd>
          </div>

          <div class="flex justify-between">
            <dt class="text-gray-600">
              Pengiriman
            </dt>

            <dd class="font-medium text-gray-900">
              {{ formatCurrency(purchaseOrder.shippingCost) }}
            </dd>
          </div>

          <div class="flex justify-between border-t border-gray-200 pt-3 text-base">
            <dt class="font-semibold text-gray-900">
              Grand Total
            </dt>

            <dd class="font-semibold text-gray-900">
              {{ formatCurrency(purchaseOrder.grandTotal) }}
            </dd>
          </div>
        </dl>
      </section>

      <section
        class="flex flex-col gap-3 rounded-xl border border-gray-200 bg-white p-6 sm:flex-row sm:flex-wrap sm:justify-end"
      >
        <button
          v-if="canEdit"
          type="button"
          class="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
          @click="router.push(`/purchase-orders/${purchaseOrder.id}/edit`)"
        >
          Edit
        </button>

        <button
          v-if="canSubmit"
          type="button"
          :disabled="isActionLoading"
          class="rounded-lg border border-green-300 px-4 py-2.5 text-sm font-medium text-green-800 hover:bg-green-50 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
          @click="runAction('submit')"
        >
          Kirim untuk persetujuan
        </button>

        <button
          v-if="canApprove"
          type="button"
          :disabled="isActionLoading"
          class="rounded-lg bg-green-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-900 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
          @click="runAction('approve')"
        >
          Setujui PO
        </button>

        <button
          v-if="canOrder"
          type="button"
          :disabled="isActionLoading"
          class="rounded-lg border border-blue-300 px-4 py-2.5 text-sm font-medium text-blue-800 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-700 focus:ring-offset-2"
          @click="runAction('order')"
        >
          Tandai sudah dipesan
        </button>

        <button
          v-if="canCancel"
          type="button"
          :disabled="isActionLoading"
          class="rounded-lg border border-red-300 px-4 py-2.5 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
          @click="runAction('cancel')"
        >
          Batalkan PO
        </button>
      </section>
    </template>
  </section>
</template>