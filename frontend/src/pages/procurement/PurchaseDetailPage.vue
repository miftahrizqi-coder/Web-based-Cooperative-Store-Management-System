<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPurchase } from '../../api/procurement'
import type { PaymentStatus, Purchase } from '../../types/procurement'
import { useAuth } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const purchase = ref<Purchase | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')

const purchaseId = String(route.params.id)

const paymentStatusLabel: Record<PaymentStatus, string> = {
  UNPAID: 'Belum Dibayar',
  PARTIALLY_PAID: 'Sebagian Dibayar',
  PAID: 'Lunas',
  OVERDUE: 'Jatuh Tempo',
}

const paymentStatusClass: Record<PaymentStatus, string> = {
  UNPAID: 'border-amber-200 bg-amber-50 text-amber-800',
  PARTIALLY_PAID: 'border-amber-200 bg-amber-50 text-amber-800',
  PAID: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  OVERDUE: 'border-red-200 bg-red-50 text-red-800',
}

const paymentStatusDotClass: Record<PaymentStatus, string> = {
  UNPAID: 'bg-amber-500',
  PARTIALLY_PAID: 'bg-amber-500',
  PAID: 'bg-emerald-600',
  OVERDUE: 'bg-red-600',
}

const totalQuantity = computed(() => {
  return (
    purchase.value?.items.reduce(
      (total, item) => total + item.quantity,
      0,
    ) ?? 0
  )
})

const itemCount = computed(() => purchase.value?.items.length ?? 0)

function formatDate(value: string | null) {
  if (!value) return '-'

  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

async function loadPurchase() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  if (!purchaseId || purchaseId === 'undefined') {
    errorMessage.value = 'Purchase ID tidak ditemukan.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    purchase.value = await getPurchase(token.value, purchaseId)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil detail Purchase.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadPurchase)
</script>

<template>
  <main class="min-w-0 bg-[#F8FAF9] text-[#17201C]">
    <div class="mx-auto max-w-[1440px] space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      <!-- Breadcrumb -->
      <nav aria-label="Breadcrumb" class="flex items-center gap-2 text-sm text-[#6B756F]">
        <button
          type="button"
          class="rounded-md transition hover:text-[#176B4D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
          @click="router.push('/purchases')"
        >
          Purchases
        </button>
        <span aria-hidden="true">/</span>
        <span class="font-medium text-[#46514B]">
          {{ purchase?.purchaseNumber || 'Detail Purchase' }}
        </span>
      </nav>

      <!-- Loading -->
      <section
        v-if="isLoading"
        aria-label="Memuat detail purchase"
        class="space-y-4"
      >
        <div class="h-8 w-64 animate-pulse rounded-md bg-[#E6EBE8]" />
        <div class="h-4 w-96 max-w-full animate-pulse rounded bg-[#E6EBE8]" />

        <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div class="h-48 animate-pulse rounded-lg border border-[#D6DDD9] bg-white" />
          <div class="h-48 animate-pulse rounded-lg border border-[#D6DDD9] bg-white" />
        </div>

        <div class="h-72 animate-pulse rounded-lg border border-[#D6DDD9] bg-white" />
      </section>

      <!-- Error -->
      <section
        v-else-if="errorMessage"
        class="rounded-lg border border-red-200 bg-white p-6 shadow-[0_1px_2px_rgba(18,55,42,.06)]"
        role="alert"
      >
        <div class="flex items-start gap-3">
          <div class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-red-50 text-red-700">
            !
          </div>

          <div class="min-w-0">
            <h1 class="text-lg font-semibold text-[#17201C]">
              Purchase gagal dimuat
            </h1>
            <p class="mt-1 text-sm leading-5 text-[#6B756F]">
              {{ errorMessage }}
            </p>

            <button
              type="button"
              class="mt-4 inline-flex min-h-10 items-center justify-center rounded-md border border-[#D6DDD9] bg-white px-4 text-sm font-semibold text-[#176B4D] transition hover:bg-[#F0F8F5] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
              @click="loadPurchase"
            >
              Coba Lagi
            </button>
          </div>
        </div>
      </section>

      <template v-else-if="purchase">
        <!-- Page header -->
        <header class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-3">
              <h1 class="break-all text-2xl font-semibold leading-8 tracking-tight text-[#17201C] sm:text-[28px]">
                {{ purchase.purchaseNumber }}
              </h1>

              <span
                class="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold"
                :class="paymentStatusClass[purchase.paymentStatus]"
              >
                <span
                  class="h-1.5 w-1.5 rounded-full"
                  :class="paymentStatusDotClass[purchase.paymentStatus]"
                  aria-hidden="true"
                />
                {{ paymentStatusLabel[purchase.paymentStatus] }}
              </span>
            </div>

            <p class="mt-2 max-w-3xl text-sm leading-5 text-[#6B756F]">
              Detail transaksi pembelian berdasarkan Goods Receipt.
              Gunakan informasi di bawah untuk menelusuri supplier, item,
              nilai transaksi, dan status pembayaran.
            </p>
          </div>

          <button
            type="button"
            class="inline-flex min-h-10 shrink-0 items-center justify-center rounded-md border border-[#D6DDD9] bg-white px-4 text-sm font-semibold text-[#46514B] shadow-[0_1px_2px_rgba(18,55,42,.06)] transition hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="router.push('/purchases')"
          >
            ← Kembali
          </button>
        </header>

        <!-- Summary + financial -->
        <section class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div class="rounded-lg border border-[#D6DDD9] bg-white shadow-[0_1px_2px_rgba(18,55,42,.06)]">
            <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
              <h2 class="text-base font-semibold text-[#17201C]">
                Ringkasan Purchase
              </h2>
              <p class="mt-1 text-sm text-[#6B756F]">
                Informasi utama transaksi dan sumber penerimaan barang.
              </p>
            </div>

            <dl class="grid gap-x-6 gap-y-5 px-5 py-5 sm:grid-cols-2 sm:px-6 lg:grid-cols-3">
              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
                  Purchase Number
                </dt>
                <dd class="mt-1 break-all text-sm font-semibold text-[#17201C]">
                  {{ purchase.purchaseNumber }}
                </dd>
              </div>

              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
                  Supplier
                </dt>
                <dd class="mt-1 break-all text-sm font-medium text-[#17201C]">
                  {{ purchase.supplierName || purchase.supplierId }}
                </dd>
              </div>

              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
                  Purchase Order
                </dt>
                <dd class="mt-1 break-all text-sm font-medium text-[#17201C]">
                  {{ purchase.purchaseOrderId }}
                </dd>
              </div>

              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
                  Goods Receipt
                </dt>
                <dd class="mt-1 break-all text-sm font-medium text-[#17201C]">
                  {{ purchase.receiptId }}
                </dd>
              </div>

              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
                  Dibuat Oleh
                </dt>
                <dd class="mt-1 break-all text-sm font-medium text-[#17201C]">
                  {{ purchase.createdBy }}
                </dd>
              </div>

              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
                  Dibuat Pada
                </dt>
                <dd class="mt-1 text-sm text-[#17201C]">
                  {{ formatDate(purchase.createdAt) }}
                </dd>
              </div>
            </dl>
          </div>

          <aside class="rounded-lg border border-[#D6DDD9] bg-white shadow-[0_1px_2px_rgba(18,55,42,.06)]">
            <div class="border-b border-[#E6EBE8] px-5 py-4">
              <h2 class="text-base font-semibold text-[#17201C]">
                Ringkasan Keuangan
              </h2>
              <p class="mt-1 text-sm text-[#6B756F]">
                Nilai transaksi purchase.
              </p>
            </div>

            <div class="space-y-4 px-5 py-5">
              <div class="flex items-center justify-between gap-4 text-sm">
                <span class="text-[#6B756F]">Subtotal</span>
                <span class="font-medium tabular-nums text-[#17201C]">
                  {{ formatCurrency(purchase.subtotal) }}
                </span>
              </div>

              <div class="flex items-center justify-between gap-4 text-sm">
                <span class="text-[#6B756F]">Diskon</span>
                <span class="font-medium tabular-nums text-[#17201C]">
                  {{ formatCurrency(purchase.discount) }}
                </span>
              </div>

              <div class="border-t border-[#E6EBE8] pt-4">
                <div class="flex items-end justify-between gap-4">
                  <span class="text-sm font-semibold text-[#46514B]">Total</span>
                  <span class="text-xl font-bold tabular-nums text-[#12372A]">
                    {{ formatCurrency(purchase.total) }}
                  </span>
                </div>
              </div>

              <div class="rounded-md border px-3 py-3" :class="paymentStatusClass[purchase.paymentStatus]">
                <p class="text-xs font-medium uppercase tracking-wide opacity-80">
                  Status pembayaran
                </p>
                <p class="mt-1 text-sm font-semibold">
                  {{ paymentStatusLabel[purchase.paymentStatus] }}
                </p>
              </div>
            </div>
          </aside>
        </section>

        <!-- Operational summary -->
        <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div class="rounded-lg border border-[#D6DDD9] bg-white p-5 shadow-[0_1px_2px_rgba(18,55,42,.06)]">
            <p class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
              Jumlah jenis produk
            </p>
            <p class="mt-2 text-2xl font-bold tabular-nums text-[#12372A]">
              {{ itemCount }}
            </p>
            <p class="mt-1 text-sm text-[#6B756F]">
              Baris item pada transaksi
            </p>
          </div>

          <div class="rounded-lg border border-[#D6DDD9] bg-white p-5 shadow-[0_1px_2px_rgba(18,55,42,.06)]">
            <p class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
              Total quantity
            </p>
            <p class="mt-2 text-2xl font-bold tabular-nums text-[#12372A]">
              {{ totalQuantity }}
            </p>
            <p class="mt-1 text-sm text-[#6B756F]">
              Total unit yang tercatat
            </p>
          </div>

          <div class="rounded-lg border border-[#D6DDD9] bg-white p-5 shadow-[0_1px_2px_rgba(18,55,42,.06)] sm:col-span-2 lg:col-span-1">
            <p class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
              Dampak pembayaran
            </p>
            <p class="mt-2 text-base font-semibold text-[#17201C]">
              {{ paymentStatusLabel[purchase.paymentStatus] }}
            </p>
            <p class="mt-1 text-sm text-[#6B756F]">
              Status finansial purchase saat ini
            </p>
          </div>
        </section>

        <!-- Items -->
        <section class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white shadow-[0_1px_2px_rgba(18,55,42,.06)]">
          <div class="flex flex-col gap-1 border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
            <h2 class="text-base font-semibold text-[#17201C]">
              Item Purchase
            </h2>
            <p class="text-sm text-[#6B756F]">
              Produk yang tercatat dalam transaksi pembelian.
            </p>
          </div>

          <div class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <caption class="sr-only">
                Daftar item pada {{ purchase.purchaseNumber }}
              </caption>

              <thead class="border-b border-[#D6DDD9] bg-[#F1F4F2]">
                <tr>
                  <th scope="col" class="whitespace-nowrap px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B] sm:px-6">
                    Produk
                  </th>
                  <th scope="col" class="whitespace-nowrap px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                    Quantity
                  </th>
                  <th scope="col" class="whitespace-nowrap px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                    Harga
                  </th>
                  <th scope="col" class="whitespace-nowrap px-5 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B] sm:px-6">
                    Subtotal
                  </th>
                </tr>
              </thead>

              <tbody class="divide-y divide-[#E6EBE8]">
                <tr
                  v-for="item in purchase.items"
                  :key="item.productId"
                  class="transition hover:bg-[#F8FAF9]"
                >
                  <td class="px-5 py-4 sm:px-6">
                    <p class="font-semibold text-[#17201C]">
                      {{ item.name }}
                    </p>
                    <p class="mt-1 break-all text-xs text-[#6B756F]">
                      SKU/Product ID: {{ item.productId }}
                    </p>
                  </td>

                  <td class="px-4 py-4 text-right tabular-nums text-[#46514B]">
                    {{ item.quantity }}
                  </td>

                  <td class="whitespace-nowrap px-4 py-4 text-right tabular-nums text-[#46514B]">
                    {{ formatCurrency(item.price) }}
                  </td>

                  <td class="whitespace-nowrap px-5 py-4 text-right font-semibold tabular-nums text-[#17201C] sm:px-6">
                    {{ formatCurrency(item.subtotal) }}
                  </td>
                </tr>

                <tr v-if="purchase.items.length === 0">
                  <td colspan="4" class="px-6 py-12 text-center">
                    <p class="text-sm font-semibold text-[#17201C]">
                      Belum ada item purchase
                    </p>
                    <p class="mt-1 text-sm text-[#6B756F]">
                      Tidak ada item yang tersedia pada transaksi ini.
                    </p>
                  </td>
                </tr>
              </tbody>

              <tfoot v-if="purchase.items.length > 0" class="border-t border-[#D6DDD9] bg-[#F8FAF9]">
                <tr>
                  <th scope="row" class="px-5 py-3 text-left text-sm font-semibold text-[#46514B] sm:px-6">
                    Total
                  </th>
                  <td class="px-4 py-3 text-right text-sm font-semibold tabular-nums text-[#17201C]">
                    {{ totalQuantity }}
                  </td>
                  <td />
                  <td class="px-5 py-3 text-right text-sm font-bold tabular-nums text-[#12372A] sm:px-6">
                    {{ formatCurrency(purchase.total) }}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </section>

        <!-- Payment + traceability -->
        <section class="grid gap-4 lg:grid-cols-2">
          <div class="rounded-lg border border-[#D6DDD9] bg-white shadow-[0_1px_2px_rgba(18,55,42,.06)]">
            <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
              <h2 class="text-base font-semibold text-[#17201C]">
                Status Pembayaran
              </h2>
              <p class="mt-1 text-sm text-[#6B756F]">
                Status finansial yang diterima dari data purchase.
              </p>
            </div>

            <div class="px-5 py-5 sm:px-6">
              <div class="flex items-center gap-3">
                <span
                  class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full"
                  :class="paymentStatusClass[purchase.paymentStatus]"
                  aria-hidden="true"
                >
                  <span
                    class="h-2 w-2 rounded-full"
                    :class="paymentStatusDotClass[purchase.paymentStatus]"
                  />
                </span>

                <div>
                  <p class="text-sm font-semibold text-[#17201C]">
                    {{ paymentStatusLabel[purchase.paymentStatus] }}
                  </p>
                  <p class="mt-0.5 text-xs text-[#6B756F]">
                    Purchase {{ purchase.purchaseNumber }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div class="rounded-lg border border-[#D6DDD9] bg-white shadow-[0_1px_2px_rgba(18,55,42,.06)]">
            <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
              <h2 class="text-base font-semibold text-[#17201C]">
                Aktivitas & Traceability
              </h2>
              <p class="mt-1 text-sm text-[#6B756F]">
                Metadata transaksi yang tersedia pada data purchase.
              </p>
            </div>

            <div class="px-5 py-5 sm:px-6">
              <ol class="relative border-l border-[#D6DDD9] pl-5">
                <li class="relative">
                  <span class="absolute -left-[25px] top-1.5 h-2.5 w-2.5 rounded-full bg-[#176B4D] ring-4 ring-[#F0F8F5]" />
                  <p class="text-sm font-semibold text-[#17201C]">
                    Purchase dibuat
                  </p>
                  <p class="mt-1 text-xs text-[#6B756F]">
                    {{ formatDate(purchase.createdAt) }}
                  </p>
                  <p class="mt-2 text-sm text-[#46514B]">
                    Oleh {{ purchase.createdBy }}
                  </p>
                </li>
              </ol>
            </div>
          </div>
        </section>

        <!-- Back action -->
        <div class="flex justify-start border-t border-[#E6EBE8] pt-2">
          <button
            type="button"
            class="inline-flex min-h-10 items-center justify-center rounded-md border border-[#D6DDD9] bg-white px-4 text-sm font-semibold text-[#46514B] transition hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
            @click="router.push('/purchases')"
          >
            ← Kembali ke daftar Purchase
          </button>
        </div>
      </template>
    </div>
  </main>
</template>
