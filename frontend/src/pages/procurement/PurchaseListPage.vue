<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getPurchases } from '../../api/procurement'
import type { PaymentStatus, Purchase } from '../../types/procurement'

const router = useRouter()

const purchases = ref<Purchase[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

const accessToken = localStorage.getItem('access_token')

const formatDate = (value: string) =>
  new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)

const paymentStatusLabel: Record<PaymentStatus, string> = {
  UNPAID: 'Belum Dibayar',
  PARTIALLY_PAID: 'Sebagian Dibayar',
  PAID: 'Lunas',
  OVERDUE: 'Jatuh Tempo',
}

const paymentStatusClass: Record<PaymentStatus, string> = {
  UNPAID: 'bg-red-50 text-red-700 ring-red-200',
  PARTIALLY_PAID: 'bg-amber-50 text-amber-800 ring-amber-200',
  PAID: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  OVERDUE: 'bg-red-50 text-red-700 ring-red-200',
}

const totalPurchase = computed(() =>
  purchases.value.reduce((total, purchase) => total + purchase.total, 0),
)

const loadPurchases = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    if (!accessToken) throw new Error('Sesi login tidak ditemukan.')
    purchases.value = await getPurchases(accessToken)
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : 'Gagal mengambil data purchase.'
  } finally {
    isLoading.value = false
  }
}

const openDetail = (purchaseId: string) => {
  router.push(`/purchases/${purchaseId}`)
}

onMounted(loadPurchases)
</script>

<template>
  <section class="min-w-0 space-y-6 text-[#17201C]">
    <!-- Header -->
    <header class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div class="min-w-0">
        <nav aria-label="Breadcrumb" class="mb-2 text-xs text-[#6B756F]">
          <span>Procurement</span>
          <span class="mx-2">/</span>
          <span class="font-medium text-[#46514B]">Purchases</span>
        </nav>

        <h1 class="text-[28px] font-semibold leading-9 text-[#12372A]">
          Purchases
        </h1>
        <p class="mt-1 max-w-2xl text-sm leading-5 text-[#6B756F]">
          Daftar transaksi pembelian yang terbentuk dari penerimaan barang.
        </p>
      </div>

      <div
        v-if="!isLoading && !errorMessage"
        class="w-full rounded-lg border border-[#D6DDD9] bg-white px-4 py-3 shadow-[0_1px_2px_rgba(18,55,42,.06)] sm:w-auto"
      >
        <p class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
          Jumlah Purchase
        </p>
        <p class="mt-1 text-xl font-semibold text-[#12372A]">
          {{ purchases.length }}
        </p>
      </div>
    </header>

    <!-- Loading -->
    <div
      v-if="isLoading"
      class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white"
      aria-busy="true"
      aria-label="Memuat daftar purchase"
    >
      <div class="animate-pulse">
        <div class="border-b border-[#E6EBE8] px-5 py-4">
          <div class="h-5 w-48 rounded bg-[#E6EBE8]" />
          <div class="mt-2 h-4 w-72 max-w-full rounded bg-[#F1F4F2]" />
        </div>
        <div class="space-y-3 p-5">
          <div v-for="n in 6" :key="n" class="h-12 rounded bg-[#F1F4F2]" />
        </div>
      </div>
    </div>

    <!-- Error -->
    <div
      v-else-if="errorMessage"
      role="alert"
      class="rounded-lg border border-red-200 bg-red-50 p-5"
    >
      <h2 class="text-base font-semibold text-[#C0392B]">
        Gagal memuat Purchase
      </h2>
      <p class="mt-1 text-sm text-[#46514B]">{{ errorMessage }}</p>
      <button
        type="button"
        class="mt-4 rounded-md bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
        @click="loadPurchases"
      >
        Coba Lagi
      </button>
    </div>

    <!-- Empty -->
    <div
      v-else-if="purchases.length === 0"
      class="rounded-lg border border-dashed border-[#D6DDD9] bg-white p-10 text-center"
    >
      <div class="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-[#F0F8F5] text-[#176B4D]">
        <span aria-hidden="true">—</span>
      </div>
      <h2 class="mt-4 text-base font-semibold text-[#17201C]">
        Belum ada Purchase
      </h2>
      <p class="mx-auto mt-2 max-w-md text-sm leading-5 text-[#6B756F]">
        Purchase akan tersedia setelah Goods Receipt yang valid diproses
        menjadi transaksi pembelian.
      </p>
    </div>

    <!-- Loaded -->
    <div v-else class="space-y-4">
      <!-- Summary -->
      <div class="grid gap-4 sm:grid-cols-2">
        <div class="rounded-lg border border-[#D6DDD9] bg-white p-5">
          <p class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
            Jumlah Purchase
          </p>
          <p class="mt-1 text-[28px] font-semibold leading-[34px] text-[#12372A]">
            {{ purchases.length }}
          </p>
          <p class="mt-1 text-xs text-[#6B756F]">
            Total transaksi pembelian
          </p>
        </div>

        <div class="rounded-lg border border-[#D6DDD9] bg-white p-5">
          <p class="text-xs font-medium uppercase tracking-wide text-[#6B756F]">
            Nilai Purchase
          </p>
          <p class="mt-1 text-[28px] font-semibold leading-[34px] text-[#12372A]">
            {{ formatCurrency(totalPurchase) }}
          </p>
          <p class="mt-1 text-xs text-[#6B756F]">
            Akumulasi nilai seluruh purchase
          </p>
        </div>
      </div>

      <!-- Data table -->
      <div class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white">
        <div class="flex flex-col gap-1 border-b border-[#E6EBE8] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 class="text-base font-semibold text-[#17201C]">
              Daftar Transaksi
            </h2>
            <p class="mt-0.5 text-xs text-[#6B756F]">
              {{ purchases.length }} purchase tercatat
            </p>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="min-w-[900px] w-full">
            <caption class="sr-only">Daftar transaksi purchase</caption>
            <thead class="sticky top-0 z-10 border-b border-[#D6DDD9] bg-[#F8FAF9]">
              <tr>
                <th class="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">Purchase</th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">Supplier</th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">PO</th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">Receipt</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]">Total</th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">Pembayaran</th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">Dibuat</th>
                <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]">Aksi</th>
              </tr>
            </thead>

            <tbody class="divide-y divide-[#E6EBE8]">
              <tr
                v-for="purchase in purchases"
                :key="purchase.id"
                class="transition-colors hover:bg-[#F8FAF9]"
              >
                <td class="px-5 py-4 align-top">
                  <button
                    type="button"
                    class="text-left focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                    @click="openDetail(purchase.id)"
                  >
                    <span class="block text-sm font-semibold text-[#176B4D] hover:text-[#12372A]">
                      {{ purchase.purchaseNumber }}
                    </span>
                    <span class="mt-1 block text-xs text-[#6B756F]">
                      {{ purchase.items.length }} item
                    </span>
                  </button>
                </td>

                <td class="px-4 py-4 align-top text-sm text-[#46514B]">
                  <span class="font-mono text-xs">{{ purchase.supplierName || purchase.supplierId }}</span>
                </td>

                <td class="px-4 py-4 align-top text-sm text-[#46514B]">
                  <span class="font-mono text-xs">{{ purchase.purchaseOrderId }}</span>
                </td>

                <td class="px-4 py-4 align-top text-sm text-[#46514B]">
                  <span class="font-mono text-xs">{{ purchase.receiptId }}</span>
                </td>

                <td class="px-4 py-4 text-right align-top text-sm font-semibold tabular-nums text-[#17201C]">
                  {{ formatCurrency(purchase.total) }}
                </td>

                <td class="px-4 py-4 align-top">
                  <span
                    class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset"
                    :class="paymentStatusClass[purchase.paymentStatus]"
                  >
                    {{ paymentStatusLabel[purchase.paymentStatus] }}
                  </span>
                </td>

                <td class="px-4 py-4 align-top text-sm text-[#6B756F]">
                  {{ formatDate(purchase.createdAt) }}
                </td>

                <td class="px-5 py-4 text-right align-top">
                  <button
                    type="button"
                    class="rounded-md border border-[#D6DDD9] bg-white px-3 py-2 text-sm font-medium text-[#46514B] hover:border-[#176B4D] hover:bg-[#F0F8F5] hover:text-[#12372A] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
                    @click="openDetail(purchase.id)"
                  >
                    Lihat Detail
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Mobile note: table remains scrollable because purchase data is operational/scannable -->
        <div class="border-t border-[#E6EBE8] bg-[#F8FAF9] px-5 py-3 text-xs text-[#6B756F] lg:hidden">
          Geser tabel ke samping untuk melihat seluruh informasi transaksi.
        </div>
      </div>
    </div>
  </section>
</template>
