<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  approvePurchaseOrder,
  cancelPurchaseOrder,
  getPurchaseOrders,
  orderPurchaseOrder,
  submitPurchaseOrder,
} from '../../api/procurement'

import type {
  PurchaseOrder,
  PurchaseOrderStatus,
} from '../../types/procurement'

import { useAuth } from '../../stores/auth'

const router = useRouter()
const { token, currentUser } = useAuth()

const purchaseOrders = ref<PurchaseOrder[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const actionError = ref('')
const actionLoadingId = ref<string | null>(null)

const statusFilter = ref<'ALL' | PurchaseOrderStatus>('ALL')

const filteredPurchaseOrders = computed(() => {
  if (statusFilter.value === 'ALL') {
    return purchaseOrders.value
  }

  return purchaseOrders.value.filter(
    (purchaseOrder) =>
      purchaseOrder.status === statusFilter.value,
  )
})

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

async function loadPurchaseOrders() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    purchaseOrders.value =
      await getPurchaseOrders(token.value)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil purchase order.'
  } finally {
    isLoading.value = false
  }
}

function canCreate() {
  return (
    currentUser.value?.role === 'admin' ||
    currentUser.value?.role === 'pengurus'
  )
}

function canApprove(purchaseOrder: PurchaseOrder) {
  if (
    currentUser.value?.role !== 'admin' &&
    currentUser.value?.role !== 'pengurus'
  ) {
    return false
  }

  if (purchaseOrder.status !== 'PENDING_APPROVAL') {
    return false
  }

  return purchaseOrder.createdBy !== currentUser.value?.id
}

function canOrder(purchaseOrder: PurchaseOrder) {
  return (
    (currentUser.value?.role === 'admin' ||
      currentUser.value?.role === 'pengurus') &&
    purchaseOrder.status === 'APPROVED'
  )
}

function canSubmit(purchaseOrder: PurchaseOrder) {
  return (
    (currentUser.value?.role === 'admin' ||
      currentUser.value?.role === 'pengurus') &&
    purchaseOrder.status === 'DRAFT'
  )
}

function canCancel(purchaseOrder: PurchaseOrder) {
  return (
    (currentUser.value?.role === 'admin' ||
      currentUser.value?.role === 'pengurus') &&
    ['DRAFT', 'PENDING_APPROVAL', 'APPROVED'].includes(
      purchaseOrder.status,
    )
  )
}

async function runAction(
  purchaseOrder: PurchaseOrder,
  action:
    | 'submit'
    | 'approve'
    | 'order'
    | 'cancel',
) {
  if (!token.value) {
    actionError.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    return
  }

  actionError.value = ''

  const messages = {
    submit: 'Kirim purchase order ini untuk persetujuan?',
    approve: 'Setujui purchase order ini?',
    order: 'Tandai purchase order ini sebagai sudah dipesan?',
    cancel: 'Batalkan purchase order ini?',
  }

  if (!window.confirm(messages[action])) {
    return
  }

  actionLoadingId.value = purchaseOrder.id

  try {
    if (action === 'submit') {
      await submitPurchaseOrder(
        token.value,
        purchaseOrder.id,
      )
    }

    if (action === 'approve') {
      await approvePurchaseOrder(
        token.value,
        purchaseOrder.id,
      )
    }

    if (action === 'order') {
      await orderPurchaseOrder(
        token.value,
        purchaseOrder.id,
      )
    }

    if (action === 'cancel') {
      await cancelPurchaseOrder(
        token.value,
        purchaseOrder.id,
      )
    }

    await loadPurchaseOrders()
  } catch (error) {
    actionError.value =
      error instanceof Error
        ? error.message
        : 'Aksi purchase order gagal.'
  } finally {
    actionLoadingId.value = null
  }
}

onMounted(loadPurchaseOrders)
</script>

<template>
  <section class="space-y-6">
    <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="text-sm font-medium text-green-800">
          Procurement
        </p>

        <h1 class="mt-1 text-2xl font-semibold text-gray-900">
          Purchase Order
        </h1>

        <p class="mt-1 text-sm text-gray-600">
          Kelola purchase order dan proses persetujuannya.
        </p>
      </div>

      <button
        v-if="canCreate()"
        type="button"
        class="rounded-lg bg-green-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-900 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
        @click="router.push('/purchase-orders/create')"
      >
        Tambah PO
      </button>
    </header>

    <div
      v-if="actionError"
      class="rounded-xl border border-red-200 bg-red-50 p-4"
      role="alert"
    >
      <p class="text-sm text-red-700">
        {{ actionError }}
      </p>
    </div>

    <div
      class="flex flex-col gap-3 rounded-xl border border-gray-200 bg-white p-4 sm:flex-row sm:items-end"
    >
      <label class="w-full sm:max-w-xs">
        <span class="mb-1 block text-sm font-medium text-gray-700">
          Status
        </span>

        <select
          v-model="statusFilter"
          class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
        >
          <option value="ALL">Semua status</option>
          <option value="DRAFT">Draft</option>
          <option value="PENDING_APPROVAL">
            Menunggu persetujuan
          </option>
          <option value="APPROVED">Disetujui</option>
          <option value="ORDERED">Dipesan</option>
          <option value="PARTIALLY_RECEIVED">
            Sebagian diterima
          </option>
          <option value="RECEIVED">Diterima</option>
          <option value="COMPLETED">Selesai</option>
          <option value="CANCELLED">Dibatalkan</option>
        </select>
      </label>
    </div>

    <div
      v-if="isLoading"
      class="overflow-hidden rounded-xl border border-gray-200 bg-white"
    >
      <div class="space-y-3 p-4">
        <div
          v-for="index in 5"
          :key="index"
          class="h-14 animate-pulse rounded bg-gray-100"
        />
      </div>
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
        @click="loadPurchaseOrders"
      >
        Coba lagi
      </button>
    </div>

    <div
      v-else-if="filteredPurchaseOrders.length === 0"
      class="rounded-xl border border-gray-200 bg-white p-8 text-center"
    >
      <h2 class="font-semibold text-gray-900">
        Tidak ada purchase order
      </h2>

      <p class="mt-1 text-sm text-gray-600">
        Belum ada purchase order yang sesuai dengan filter.
      </p>

      <button
        v-if="canCreate()"
        type="button"
        class="mt-4 rounded-lg bg-green-800 px-4 py-2 text-sm font-medium text-white hover:bg-green-900 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
        @click="router.push('/purchase-orders/create')"
      >
        Tambah PO
      </button>
    </div>

    <div
      v-else
      class="overflow-x-auto rounded-xl border border-gray-200 bg-white"
    >
      <table class="min-w-full text-left text-sm">
        <thead class="border-b border-gray-200 bg-gray-50 text-gray-600">
          <tr>
            <th class="px-4 py-3 font-medium">
              Nomor PO
            </th>

            <th class="px-4 py-3 font-medium">
              Supplier
            </th>

            <th class="px-4 py-3 font-medium">
              Tanggal
            </th>

            <th class="px-4 py-3 font-medium">
              Jatuh/Target
            </th>

            <th class="px-4 py-3 font-medium">
              Total
            </th>

            <th class="px-4 py-3 font-medium">
              Status
            </th>

            <th class="px-4 py-3 font-medium">
              Aksi
            </th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          <tr
            v-for="purchaseOrder in filteredPurchaseOrders"
            :key="purchaseOrder.id"
          >
            <td class="px-4 py-3">
              <button
                type="button"
                class="font-medium text-green-800 hover:underline focus:outline-none focus:ring-2 focus:ring-green-700"
                @click="router.push(`/purchase-orders/${purchaseOrder.id}`)"
              >
                {{ purchaseOrder.poNumber }}
              </button>
            </td>

            <td class="px-4 py-3 text-gray-700">
              {{ purchaseOrder.supplierId }}
            </td>

            <td class="px-4 py-3 text-gray-700">
              {{ formatDate(purchaseOrder.createdAt) }}
            </td>

            <td class="px-4 py-3 text-gray-700">
              {{ formatDate(purchaseOrder.expectedDeliveryDate) }}
            </td>

            <td class="px-4 py-3 font-medium text-gray-900">
              {{ formatCurrency(purchaseOrder.grandTotal) }}
            </td>

            <td class="px-4 py-3">
              <span
                class="rounded-full px-2.5 py-1 text-xs font-medium"
                :class="statusClass(purchaseOrder.status)"
              >
                {{ statusLabel(purchaseOrder.status) }}
              </span>
            </td>

            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-2">
                <button
                  type="button"
                  class="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
                  @click="router.push(`/purchase-orders/${purchaseOrder.id}`)"
                >
                  Detail
                </button>

                <button
                  v-if="canSubmit(purchaseOrder)"
                  type="button"
                  :disabled="actionLoadingId === purchaseOrder.id"
                  class="rounded-md border border-green-300 px-3 py-1.5 text-xs font-medium text-green-800 hover:bg-green-50 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
                  @click="runAction(purchaseOrder, 'submit')"
                >
                  Kirim
                </button>

                <button
                  v-if="canApprove(purchaseOrder)"
                  type="button"
                  :disabled="actionLoadingId === purchaseOrder.id"
                  class="rounded-md border border-green-300 px-3 py-1.5 text-xs font-medium text-green-800 hover:bg-green-50 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
                  @click="runAction(purchaseOrder, 'approve')"
                >
                  Setujui
                </button>

                <button
                  v-if="canOrder(purchaseOrder)"
                  type="button"
                  :disabled="actionLoadingId === purchaseOrder.id"
                  class="rounded-md border border-blue-300 px-3 py-1.5 text-xs font-medium text-blue-800 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-700 focus:ring-offset-2"
                  @click="runAction(purchaseOrder, 'order')"
                >
                  Tandai dipesan
                </button>

                <button
                  v-if="canCancel(purchaseOrder)"
                  type="button"
                  :disabled="actionLoadingId === purchaseOrder.id"
                  class="rounded-md border border-red-300 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
                  @click="runAction(purchaseOrder, 'cancel')"
                >
                  Batalkan
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>