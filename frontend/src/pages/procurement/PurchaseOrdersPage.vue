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
  <section class="min-h-full bg-[#F8FAF9]">
    <div class="mx-auto max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8">
      <!-- Breadcrumb -->
      <nav class="mb-5" aria-label="Breadcrumb">
        <ol class="flex flex-wrap items-center gap-2 text-xs text-[#6B756F]">
          <li>
            <span class="font-medium text-[#176B4D]">Procurement</span>
          </li>
          <li aria-hidden="true">/</li>
          <li class="text-[#46514B]">Purchase Orders</li>
        </ol>
      </nav>

      <!-- Page header -->
      <header class="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.08em] text-[#176B4D]">
            Procurement
          </p>
          <h1 class="mt-1 text-[28px] font-semibold leading-9 text-[#17201C]">
            Purchase Order
          </h1>
          <p class="mt-1 text-sm leading-5 text-[#6B756F]">
            Kelola purchase order, persetujuan, dan proses pemesanan supplier.
          </p>
        </div>

        <button
          v-if="canCreate()"
          type="button"
          class="inline-flex min-h-10 items-center justify-center rounded-md bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
          @click="router.push('/purchase-orders/create')"
        >
          Tambah PO
        </button>
      </header>

      <!-- Action error -->
      <div
        v-if="actionError"
        class="mb-5 rounded-lg border border-[#C0392B]/25 bg-[#FEF4F3] p-4"
        role="alert"
      >
        <p class="text-sm font-medium text-[#C0392B]">
          {{ actionError }}
        </p>
      </div>

      <!-- Filter bar -->
      <section class="mb-5 rounded-lg border border-[#D6DDD9] bg-white p-4">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <label class="w-full sm:max-w-xs">
            <span class="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-[#46514B]">
              Status
            </span>
            <select
              v-model="statusFilter"
              class="w-full rounded-md border border-[#D6DDD9] bg-white px-3 py-2.5 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
            >
              <option value="ALL">Semua status</option>
              <option value="DRAFT">Draft</option>
              <option value="PENDING_APPROVAL">Menunggu persetujuan</option>
              <option value="APPROVED">Disetujui</option>
              <option value="ORDERED">Dipesan</option>
              <option value="PARTIALLY_RECEIVED">Sebagian diterima</option>
              <option value="RECEIVED">Diterima</option>
              <option value="COMPLETED">Selesai</option>
              <option value="CANCELLED">Dibatalkan</option>
            </select>
          </label>

          <p class="text-xs text-[#6B756F]">
            Menampilkan
            <span class="font-semibold text-[#46514B]">{{ filteredPurchaseOrders.length }}</span>
            purchase order
          </p>
        </div>
      </section>

      <!-- Loading -->
      <div
        v-if="isLoading"
        class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
        aria-busy="true"
        aria-label="Memuat purchase order"
      >
        <div class="hidden animate-pulse sm:block">
          <div class="h-11 border-b border-[#E6EBE8] bg-[#F1F4F2]"></div>
          <div v-for="index in 6" :key="index" class="mx-4 my-3 h-12 rounded bg-[#F1F4F2]"></div>
        </div>
        <div class="space-y-3 p-4 sm:hidden">
          <div v-for="index in 5" :key="index" class="h-24 rounded bg-[#F1F4F2] animate-pulse"></div>
        </div>
      </div>

      <!-- Error -->
      <div
        v-else-if="errorMessage"
        class="rounded-lg border border-[#C0392B]/25 bg-[#FEF4F3] p-6"
        role="alert"
      >
        <h2 class="text-base font-semibold text-[#17201C]">
          Purchase order gagal dimuat
        </h2>
        <p class="mt-1 text-sm text-[#C0392B]">
          {{ errorMessage }}
        </p>
        <button
          type="button"
          class="mt-4 rounded-md border border-[#C0392B]/40 bg-white px-4 py-2 text-sm font-semibold text-[#C0392B] hover:bg-[#FEF4F3] focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-2"
          @click="loadPurchaseOrders"
        >
          Coba lagi
        </button>
      </div>

      <!-- Empty -->
      <div
        v-else-if="filteredPurchaseOrders.length === 0"
        class="rounded-lg border border-dashed border-[#D6DDD9] bg-white px-6 py-10 text-center"
      >
        <div class="mx-auto max-w-md">
          <p class="text-base font-semibold text-[#17201C]">
            Tidak ada purchase order
          </p>
          <p class="mt-1 text-sm leading-5 text-[#6B756F]">
            {{
              statusFilter === 'ALL'
                ? 'Belum ada purchase order. Buat PO pertama untuk mulai proses pengadaan.'
                : 'Tidak ada purchase order dengan status yang dipilih.'
            }}
          </p>

          <button
            v-if="canCreate()"
            type="button"
            class="mt-5 rounded-md bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="router.push('/purchase-orders/create')"
          >
            Buat PO
          </button>
        </div>
      </div>

      <!-- Desktop/tablet table -->
      <div
        v-else
        class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
      >
        <div class="hidden overflow-x-auto md:block">
          <table class="min-w-[980px] w-full text-sm">
            <caption class="sr-only">
              Daftar purchase order
            </caption>
            <thead class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F1F4F2]">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                  Nomor PO
                </th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                  Supplier
                </th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                  Tanggal
                </th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                  Target
                </th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                  Total
                </th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                  Status
                </th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                  Aksi
                </th>
              </tr>
            </thead>

            <tbody class="divide-y divide-[#E6EBE8]">
              <tr
                v-for="purchaseOrder in filteredPurchaseOrders"
                :key="purchaseOrder.id"
                class="transition hover:bg-[#F8FAF9]"
              >
                <td class="px-4 py-3.5">
                  <button
                    type="button"
                    class="rounded font-semibold text-[#176B4D] underline-offset-2 hover:underline focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
                    @click="router.push(`/purchase-orders/${purchaseOrder.id}`)"
                  >
                    {{ purchaseOrder.poNumber }}
                  </button>
                  <p class="mt-0.5 text-xs text-[#6B756F]">
                    ID {{ purchaseOrder.id.slice(0, 8) }}
                  </p>
                </td>

                <td class="px-4 py-3.5">
                  <span class="font-medium text-[#17201C]">
                    {{ purchaseOrder.supplierName || purchaseOrder.supplierId }}
                  </span>
                </td>

                <td class="px-4 py-3.5 whitespace-nowrap text-[#46514B]">
                  {{ formatDate(purchaseOrder.createdAt) }}
                </td>

                <td class="px-4 py-3.5 whitespace-nowrap text-[#46514B]">
                  {{ formatDate(purchaseOrder.expectedDeliveryDate) }}
                </td>

                <td class="px-4 py-3.5 text-right font-semibold tabular-nums text-[#17201C]">
                  {{ formatCurrency(purchaseOrder.grandTotal) }}
                </td>

                <td class="px-4 py-3.5">
                  <span
                    class="inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium"
                    :class="statusClass(purchaseOrder.status)"
                  >
                    {{ statusLabel(purchaseOrder.status) }}
                  </span>
                </td>

                <td class="px-4 py-3.5">
                  <div class="flex min-w-[250px] flex-wrap justify-end gap-2">
                    <button
                      type="button"
                      class="rounded-md border border-[#D6DDD9] bg-white px-3 py-1.5 text-xs font-semibold text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
                      @click="router.push(`/purchase-orders/${purchaseOrder.id}`)"
                    >
                      Detail
                    </button>

                    <button
                      v-if="canSubmit(purchaseOrder)"
                      type="button"
                      :disabled="actionLoadingId === purchaseOrder.id"
                      class="rounded-md border border-[#176B4D]/30 bg-[#F0F8F5] px-3 py-1.5 text-xs font-semibold text-[#176B4D] hover:bg-[#DCEFE7] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
                      @click="runAction(purchaseOrder, 'submit')"
                    >
                      Kirim
                    </button>

                    <button
                      v-if="canApprove(purchaseOrder)"
                      type="button"
                      :disabled="actionLoadingId === purchaseOrder.id"
                      class="rounded-md border border-[#176B4D]/30 bg-[#F0F8F5] px-3 py-1.5 text-xs font-semibold text-[#176B4D] hover:bg-[#DCEFE7] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
                      @click="runAction(purchaseOrder, 'approve')"
                    >
                      Setujui
                    </button>

                    <button
                      v-if="canOrder(purchaseOrder)"
                      type="button"
                      :disabled="actionLoadingId === purchaseOrder.id"
                      class="rounded-md border border-[#2874A6]/30 bg-[#F3F8FB] px-3 py-1.5 text-xs font-semibold text-[#2874A6] hover:bg-[#E5F0F7] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#2874A6] focus:ring-offset-1"
                      @click="runAction(purchaseOrder, 'order')"
                    >
                      Tandai dipesan
                    </button>

                    <button
                      v-if="canCancel(purchaseOrder)"
                      type="button"
                      :disabled="actionLoadingId === purchaseOrder.id"
                      class="rounded-md border border-[#C0392B]/30 bg-[#FEF4F3] px-3 py-1.5 text-xs font-semibold text-[#C0392B] hover:bg-[#FCE8E6] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-1"
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

        <!-- Mobile operational rows -->
        <div class="divide-y divide-[#E6EBE8] md:hidden">
          <article
            v-for="purchaseOrder in filteredPurchaseOrders"
            :key="purchaseOrder.id"
            class="p-4"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <button
                  type="button"
                  class="truncate rounded text-left text-sm font-semibold text-[#176B4D] underline-offset-2 hover:underline focus:outline-none focus:ring-2 focus:ring-[#176B4D]"
                  @click="router.push(`/purchase-orders/${purchaseOrder.id}`)"
                >
                  {{ purchaseOrder.poNumber }}
                </button>
                <p class="mt-1 truncate text-xs text-[#6B756F]">
                  Supplier: {{ purchaseOrder.supplierName || purchaseOrder.supplierId }}
                </p>
              </div>

              <span
                class="inline-flex shrink-0 items-center rounded-full border px-2.5 py-1 text-xs font-medium"
                :class="statusClass(purchaseOrder.status)"
              >
                {{ statusLabel(purchaseOrder.status) }}
              </span>
            </div>

            <dl class="mt-4 grid grid-cols-2 gap-x-4 gap-y-3">
              <div>
                <dt class="text-xs text-[#6B756F]">Tanggal</dt>
                <dd class="mt-0.5 text-sm text-[#46514B]">
                  {{ formatDate(purchaseOrder.createdAt) }}
                </dd>
              </div>
              <div>
                <dt class="text-xs text-[#6B756F]">Target</dt>
                <dd class="mt-0.5 text-sm text-[#46514B]">
                  {{ formatDate(purchaseOrder.expectedDeliveryDate) }}
                </dd>
              </div>
              <div class="col-span-2 border-t border-[#E6EBE8] pt-3">
                <dt class="text-xs text-[#6B756F]">Total</dt>
                <dd class="mt-0.5 text-base font-semibold tabular-nums text-[#17201C]">
                  {{ formatCurrency(purchaseOrder.grandTotal) }}
                </dd>
              </div>
            </dl>

            <div class="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                class="rounded-md border border-[#D6DDD9] bg-white px-3 py-2 text-xs font-semibold text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
                @click="router.push(`/purchase-orders/${purchaseOrder.id}`)"
              >
                Detail
              </button>

              <button
                v-if="canSubmit(purchaseOrder)"
                type="button"
                :disabled="actionLoadingId === purchaseOrder.id"
                class="rounded-md bg-[#176B4D] px-3 py-2 text-xs font-semibold text-white hover:bg-[#1F805D] disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
                @click="runAction(purchaseOrder, 'submit')"
              >
                Kirim
              </button>

              <button
                v-if="canApprove(purchaseOrder)"
                type="button"
                :disabled="actionLoadingId === purchaseOrder.id"
                class="rounded-md bg-[#176B4D] px-3 py-2 text-xs font-semibold text-white hover:bg-[#1F805D] disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
                @click="runAction(purchaseOrder, 'approve')"
              >
                Setujui
              </button>

              <button
                v-if="canOrder(purchaseOrder)"
                type="button"
                :disabled="actionLoadingId === purchaseOrder.id"
                class="rounded-md bg-[#2874A6] px-3 py-2 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#2874A6] focus:ring-offset-1"
                @click="runAction(purchaseOrder, 'order')"
              >
                Tandai dipesan
              </button>

              <button
                v-if="canCancel(purchaseOrder)"
                type="button"
                :disabled="actionLoadingId === purchaseOrder.id"
                class="rounded-md bg-[#C0392B] px-3 py-2 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-1"
                @click="runAction(purchaseOrder, 'cancel')"
              >
                Batalkan
              </button>
            </div>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>
