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
    DRAFT: 'border-[#D6DDD9] bg-[#F1F4F2] text-[#46514B]',
    PENDING_APPROVAL: 'border-[#B7791F]/30 bg-[#B7791F]/10 text-[#8A5A13]',
    APPROVED: 'border-[#16834B]/25 bg-[#16834B]/10 text-[#16834B]',
    ORDERED: 'border-[#2874A6]/25 bg-[#2874A6]/10 text-[#2874A6]',
    PARTIALLY_RECEIVED: 'border-[#B7791F]/30 bg-[#B7791F]/10 text-[#8A5A13]',
    RECEIVED: 'border-[#16834B]/25 bg-[#16834B]/10 text-[#16834B]',
    COMPLETED: 'border-[#16834B]/25 bg-[#16834B]/10 text-[#16834B]',
    CANCELLED: 'border-[#C0392B]/25 bg-[#C0392B]/10 text-[#C0392B]',
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

const canReceive = computed(
  () =>
    (purchaseOrder.value?.status === 'ORDERED' ||
      purchaseOrder.value?.status === 'PARTIALLY_RECEIVED') &&
    (currentUser.value?.role === 'admin' ||
      currentUser.value?.role === 'pengurus'),
)

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
  <section class="min-h-full bg-[#F8FAF9] text-[#17201C]">
    <div class="space-y-6">
      <!-- Breadcrumb + header -->
      <header class="space-y-4">
        <nav aria-label="Breadcrumb" class="text-sm text-[#6B756F]">
          <button
            type="button"
            class="font-medium text-[#176B4D] hover:text-[#12372A] hover:underline focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="router.push('/purchase-orders')"
          >
            Purchase Order
          </button>
          <span class="mx-2">/</span>
          <span>Detail</span>
        </nav>

        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="text-xs font-medium uppercase tracking-[0.08em] text-[#6B756F]">
              Purchase Order
            </p>
            <h1 class="mt-1 text-[28px] font-semibold leading-9 text-[#12372A]">
              {{ purchaseOrder?.poNumber || 'Detail Purchase Order' }}
            </h1>
            <p class="mt-1 text-sm text-[#6B756F]">
              Detail pengadaan, item, nilai transaksi, dan status proses.
            </p>
          </div>

          <div v-if="purchaseOrder" class="flex flex-wrap items-center gap-3">
            <span
              class="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-semibold"
              :class="statusClass(purchaseOrder.status)"
            >
              {{ statusLabel(purchaseOrder.status) }}
            </span>

            <button
              v-if="canEdit"
              type="button"
              class="rounded-lg border border-[#D6DDD9] bg-white px-4 py-2.5 text-sm font-medium text-[#46514B] shadow-sm hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
              @click="router.push(`/purchase-orders/${purchaseOrder.id}/edit`)"
            >
              Edit PO
            </button>
          </div>
        </div>
      </header>

      <!-- Loading -->
      <div v-if="isLoading" class="space-y-4" aria-busy="true" aria-label="Memuat purchase order">
        <div class="h-28 animate-pulse rounded-xl border border-[#E6EBE8] bg-white" />
        <div class="h-24 animate-pulse rounded-xl border border-[#E6EBE8] bg-white" />
        <div class="h-72 animate-pulse rounded-xl border border-[#E6EBE8] bg-white" />
      </div>

      <!-- Error -->
      <div
        v-else-if="errorMessage"
        class="rounded-xl border border-[#C0392B]/25 bg-[#C0392B]/5 p-5"
        role="alert"
      >
        <h2 class="font-semibold text-[#C0392B]">Purchase order gagal dimuat</h2>
        <p class="mt-1 text-sm text-[#46514B]">{{ errorMessage }}</p>
        <button
          type="button"
          class="mt-4 rounded-lg border border-[#C0392B]/40 bg-white px-4 py-2 text-sm font-medium text-[#C0392B] hover:bg-[#C0392B]/5 focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-2"
          @click="loadPurchaseOrder"
        >
          Coba lagi
        </button>
      </div>

      <template v-else-if="purchaseOrder">
        <!-- Action error -->
        <div
          v-if="actionError"
          class="flex items-start justify-between gap-4 rounded-xl border border-[#C0392B]/25 bg-[#C0392B]/5 p-4"
          role="alert"
        >
          <p class="text-sm text-[#C0392B]">{{ actionError }}</p>
          <button
            type="button"
            class="shrink-0 text-sm font-medium text-[#C0392B] underline focus:outline-none focus:ring-2 focus:ring-[#C0392B]"
            @click="actionError = ''"
          >
            Tutup
          </button>
        </div>

        <!-- Lifecycle -->
        <section class="rounded-xl border border-[#D6DDD9] bg-white p-5 shadow-sm" aria-labelledby="lifecycle-title">
          <div class="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 id="lifecycle-title" class="text-lg font-semibold text-[#12372A]">
                Lifecycle Purchase Order
              </h2>
              <p class="text-sm text-[#6B756F]">
                Status menunjukkan posisi PO dalam proses pengadaan.
              </p>
            </div>
            <span class="text-sm font-medium text-[#46514B]">
              {{ statusLabel(purchaseOrder.status) }}
            </span>
          </div>

          <div class="mt-6 overflow-x-auto pb-1">
            <div class="flex min-w-[760px] items-start">
              <template
                v-for="(step, index) in [
                  ['DRAFT', 'Draft'],
                  ['PENDING_APPROVAL', 'Menunggu persetujuan'],
                  ['APPROVED', 'Disetujui'],
                  ['ORDERED', 'Dipesan'],
                  ['PARTIALLY_RECEIVED', 'Sebagian diterima'],
                  ['RECEIVED', 'Diterima'],
                  ['COMPLETED', 'Selesai'],
                ]"
                :key="step[0]"
              >
                <div class="flex min-w-[100px] flex-1 flex-col items-center text-center">
                  <div
                    class="flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-bold"
                    :class="
                      [
                        'DRAFT',
                        'PENDING_APPROVAL',
                        'APPROVED',
                        'ORDERED',
                        'PARTIALLY_RECEIVED',
                        'RECEIVED',
                        'COMPLETED',
                      ].indexOf(purchaseOrder.status) >= index
                        ? 'border-[#176B4D] bg-[#176B4D] text-white'
                        : 'border-[#D6DDD9] bg-white text-[#6B756F]'
                    "
                    :aria-current="
                      purchaseOrder.status === step[0] ? 'step' : undefined
                    "
                  >
                    {{ index + 1 }}
                  </div>
                  <span
                    class="mt-2 max-w-[110px] text-xs leading-4"
                    :class="
                      purchaseOrder.status === step[0]
                        ? 'font-semibold text-[#12372A]'
                        : 'text-[#6B756F]'
                    "
                  >
                    {{ step[1] }}
                  </span>
                </div>

                <div
                  v-if="index < 6"
                  class="mt-4 h-px flex-1 bg-[#D6DDD9]"
                  :class="
                    [
                      'DRAFT',
                      'PENDING_APPROVAL',
                      'APPROVED',
                      'ORDERED',
                      'PARTIALLY_RECEIVED',
                      'RECEIVED',
                      'COMPLETED',
                    ].indexOf(purchaseOrder.status) > index
                      ? 'bg-[#176B4D]'
                      : 'bg-[#D6DDD9]'
                  "
                />
              </template>
            </div>
          </div>

          <div
            v-if="purchaseOrder.status === 'CANCELLED'"
            class="mt-4 rounded-lg border border-[#C0392B]/25 bg-[#C0392B]/5 px-4 py-3 text-sm text-[#C0392B]"
          >
            PO ini dibatalkan dan tidak melanjutkan lifecycle penerimaan.
          </div>
        </section>

        <!-- Summary / metadata -->
        <section class="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
          <div class="rounded-xl border border-[#D6DDD9] bg-white p-5 shadow-sm">
            <div class="flex items-center justify-between gap-4">
              <div>
                <h2 class="text-lg font-semibold text-[#12372A]">Supplier & Metadata</h2>
                <p class="mt-1 text-sm text-[#6B756F]">
                  Informasi utama yang terkait dengan PO ini.
                </p>
              </div>
            </div>

            <dl class="mt-5 grid gap-x-6 gap-y-5 sm:grid-cols-2">
              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">Supplier</dt>
                <dd class="mt-1 break-all text-sm font-semibold text-[#17201C]">
                  {{ purchaseOrder.supplierId }}
                </dd>
              </div>
              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">Dibuat</dt>
                <dd class="mt-1 text-sm text-[#17201C]">{{ formatDate(purchaseOrder.createdAt) }}</dd>
              </div>
              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">Target pengiriman</dt>
                <dd class="mt-1 text-sm text-[#17201C]">{{ formatDate(purchaseOrder.expectedDeliveryDate) }}</dd>
              </div>
              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">Disetujui oleh</dt>
                <dd class="mt-1 break-all text-sm text-[#17201C]">{{ purchaseOrder.approvedBy || '-' }}</dd>
              </div>
              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">PO ID</dt>
                <dd class="mt-1 break-all font-mono text-xs text-[#46514B]">{{ purchaseOrder.id }}</dd>
              </div>
              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">Status saat ini</dt>
                <dd class="mt-1 text-sm font-medium text-[#12372A]">{{ statusLabel(purchaseOrder.status) }}</dd>
              </div>
            </dl>
          </div>

          <div class="rounded-xl border border-[#D6DDD9] bg-white p-5 shadow-sm">
            <p class="text-sm font-medium text-[#46514B]">Nilai purchase order</p>
            <p class="mt-2 text-3xl font-bold tracking-tight text-[#12372A]">
              {{ formatCurrency(purchaseOrder.grandTotal) }}
            </p>
            <div class="mt-5 border-t border-[#E6EBE8] pt-4">
              <div class="flex items-center justify-between text-sm">
                <span class="text-[#6B756F]">Jumlah item</span>
                <span class="font-semibold tabular-nums text-[#17201C]">{{ purchaseOrder.items.length }}</span>
              </div>
              <div class="mt-2 flex items-center justify-between text-sm">
                <span class="text-[#6B756F]">Status</span>
                <span class="font-medium text-[#17201C]">{{ statusLabel(purchaseOrder.status) }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Items -->
        <section class="rounded-xl border border-[#D6DDD9] bg-white shadow-sm" aria-labelledby="items-title">
          <div class="flex flex-col gap-1 border-b border-[#E6EBE8] p-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 id="items-title" class="text-lg font-semibold text-[#12372A]">Item Purchase Order</h2>
              <p class="mt-1 text-sm text-[#6B756F]">
                Produk yang dipesan beserta quantity dan nilai per item.
              </p>
            </div>
            <span class="text-sm text-[#6B756F]">
              {{ purchaseOrder.items.length }} item
            </span>
          </div>

          <div v-if="purchaseOrder.items.length" class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <caption class="sr-only">Daftar item purchase order {{ purchaseOrder.poNumber }}</caption>
              <thead class="border-b border-[#E6EBE8] bg-[#F1F4F2]">
                <tr>
                  <th class="px-5 py-3 text-left font-semibold text-[#46514B]">Produk</th>
                  <th class="px-5 py-3 text-left font-semibold text-[#46514B]">SKU</th>
                  <th class="px-5 py-3 text-right font-semibold text-[#46514B]">Qty</th>
                  <th class="px-5 py-3 text-right font-semibold text-[#46514B]">Harga</th>
                  <th class="px-5 py-3 text-right font-semibold text-[#46514B]">Subtotal</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#E6EBE8]">
                <tr
                  v-for="item in purchaseOrder.items"
                  :key="item.productId"
                  class="hover:bg-[#F8FAF9]"
                >
                  <td class="px-5 py-4">
                    <p class="font-semibold text-[#17201C]">{{ item.name }}</p>
                    <p class="mt-0.5 text-xs text-[#6B756F]">{{ item.productId }}</p>
                  </td>
                  <td class="px-5 py-4 font-mono text-xs text-[#46514B]">{{ item.sku }}</td>
                  <td class="px-5 py-4 text-right tabular-nums font-medium text-[#17201C]">{{ item.quantity }}</td>
                  <td class="px-5 py-4 text-right tabular-nums text-[#46514B]">{{ formatCurrency(item.unitPrice) }}</td>
                  <td class="px-5 py-4 text-right tabular-nums font-semibold text-[#17201C]">{{ formatCurrency(item.subtotal) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-else class="p-8 text-center">
            <p class="font-medium text-[#17201C]">Belum ada item pada purchase order.</p>
            <p class="mt-1 text-sm text-[#6B756F]">Tidak ada data produk yang dapat ditampilkan.</p>
          </div>
        </section>

        <!-- Financial + receiving -->
        <section class="grid gap-4 xl:grid-cols-2">
          <div class="rounded-xl border border-[#D6DDD9] bg-white p-5 shadow-sm">
            <h2 class="text-lg font-semibold text-[#12372A]">Financial Summary</h2>
            <p class="mt-1 text-sm text-[#6B756F]">Rincian pembentuk nilai purchase order.</p>

            <dl class="mt-5 space-y-3 text-sm">
              <div class="flex justify-between gap-4">
                <dt class="text-[#6B756F]">Subtotal</dt>
                <dd class="tabular-nums font-medium text-[#17201C]">{{ formatCurrency(purchaseOrder.subtotal) }}</dd>
              </div>
              <div class="flex justify-between gap-4">
                <dt class="text-[#6B756F]">Diskon</dt>
                <dd class="tabular-nums font-medium text-[#17201C]">- {{ formatCurrency(purchaseOrder.discount) }}</dd>
              </div>
              <div class="flex justify-between gap-4">
                <dt class="text-[#6B756F]">Pajak</dt>
                <dd class="tabular-nums font-medium text-[#17201C]">{{ formatCurrency(purchaseOrder.tax) }}</dd>
              </div>
              <div class="flex justify-between gap-4">
                <dt class="text-[#6B756F]">Pengiriman</dt>
                <dd class="tabular-nums font-medium text-[#17201C]">{{ formatCurrency(purchaseOrder.shippingCost) }}</dd>
              </div>
              <div class="flex justify-between gap-4 border-t border-[#E6EBE8] pt-4">
                <dt class="font-semibold text-[#12372A]">Grand Total</dt>
                <dd class="tabular-nums text-lg font-bold text-[#12372A]">{{ formatCurrency(purchaseOrder.grandTotal) }}</dd>
              </div>
            </dl>
          </div>

          <div class="rounded-xl border border-[#D6DDD9] bg-white p-5 shadow-sm">
            <h2 class="text-lg font-semibold text-[#12372A]">Receiving Summary</h2>
            <p class="mt-1 text-sm text-[#6B756F]">
              Status penerimaan mengikuti lifecycle PO. Detail quantity penerimaan dicatat pada Goods Receipt.
            </p>

            <div class="mt-5 rounded-lg border border-[#DCEFE7] bg-[#F0F8F5] p-4">
              <p class="text-xs font-medium uppercase tracking-wide text-[#176B4D]">Status penerimaan</p>
              <p class="mt-1 font-semibold text-[#12372A]">
                {{
                  purchaseOrder.status === 'PARTIALLY_RECEIVED'
                    ? 'Sebagian barang telah diterima'
                    : purchaseOrder.status === 'RECEIVED' || purchaseOrder.status === 'COMPLETED'
                      ? 'Barang telah diterima'
                      : 'Belum ada penerimaan'
                }}
              </p>
            </div>

            <button
              v-if="canReceive"
              type="button"
              class="mt-4 w-full rounded-lg bg-[#176B4D] px-4 py-3 text-sm font-semibold text-white hover:bg-[#12372A] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
              @click="router.push(`/goods-receipts/create/${purchaseOrder.id}`)"
            >
              Buat Penerimaan Barang
            </button>
          </div>
        </section>

        <!-- Activity -->
        <section class="rounded-xl border border-[#D6DDD9] bg-white p-5 shadow-sm">
          <div>
            <h2 class="text-lg font-semibold text-[#12372A]">Activity & Traceability</h2>
            <p class="mt-1 text-sm text-[#6B756F]">
              Event yang tersedia dari metadata purchase order saat ini.
            </p>
          </div>

          <ol class="mt-5 border-l border-[#D6DDD9] pl-5">
            <li class="relative pb-5">
              <span class="absolute -left-[25px] top-1 h-3 w-3 rounded-full border-2 border-white bg-[#176B4D] ring-1 ring-[#176B4D]" />
              <p class="text-sm font-semibold text-[#17201C]">Purchase order dibuat</p>
              <p class="mt-1 text-xs text-[#6B756F]">{{ formatDate(purchaseOrder.createdAt) }}</p>
            </li>

            <li v-if="purchaseOrder.approvedBy" class="relative pb-5">
              <span class="absolute -left-[25px] top-1 h-3 w-3 rounded-full border-2 border-white bg-[#16834B] ring-1 ring-[#16834B]" />
              <p class="text-sm font-semibold text-[#17201C]">Purchase order disetujui</p>
              <p class="mt-1 text-xs text-[#6B756F]">Oleh {{ purchaseOrder.approvedBy }}</p>
            </li>

            <li class="relative">
              <span
                class="absolute -left-[25px] top-1 h-3 w-3 rounded-full border-2 border-white ring-1"
                :class="purchaseOrder.status === 'CANCELLED'
                  ? 'bg-[#C0392B] ring-[#C0392B]'
                  : 'bg-[#176B4D] ring-[#176B4D]'"
              />
              <p class="text-sm font-semibold text-[#17201C]">Status saat ini: {{ statusLabel(purchaseOrder.status) }}</p>
              <p class="mt-1 text-xs text-[#6B756F]">
                Histori event yang lebih rinci mengikuti audit/activity data dari backend.
              </p>
            </li>
          </ol>
        </section>

        <!-- Actions -->
        <section class="sticky bottom-3 z-10 rounded-xl border border-[#D6DDD9] bg-white/95 p-4 shadow-lg backdrop-blur-sm">
          <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p class="text-sm font-semibold text-[#12372A]">Available Actions</p>
              <p class="text-xs text-[#6B756F]">
                Aksi ditampilkan berdasarkan status PO dan role pengguna.
              </p>
            </div>

            <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:justify-end">
              <button
                v-if="canSubmit"
                type="button"
                :disabled="isActionLoading"
                class="rounded-lg border border-[#176B4D] bg-white px-4 py-2.5 text-sm font-semibold text-[#176B4D] hover:bg-[#F0F8F5] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                @click="runAction('submit')"
              >
                Kirim untuk persetujuan
              </button>

              <button
                v-if="canApprove"
                type="button"
                :disabled="isActionLoading"
                class="rounded-lg bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#12372A] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                @click="runAction('approve')"
              >
                Setujui PO
              </button>

              <button
                v-if="canOrder"
                type="button"
                :disabled="isActionLoading"
                class="rounded-lg bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#12372A] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                @click="runAction('order')"
              >
                Tandai sudah dipesan
              </button>

              <button
                v-if="canReceive"
                type="button"
                class="rounded-lg bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#12372A] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                @click="router.push(`/goods-receipts/create/${purchaseOrder.id}`)"
              >
                Terima Barang
              </button>

              <button
                v-if="canCancel"
                type="button"
                :disabled="isActionLoading"
                class="rounded-lg border border-[#C0392B]/40 bg-white px-4 py-2.5 text-sm font-semibold text-[#C0392B] hover:bg-[#C0392B]/5 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-2"
                @click="runAction('cancel')"
              >
                Batalkan PO
              </button>
            </div>
          </div>
        </section>
      </template>
    </div>
  </section>
</template>
