<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSaleDetail } from '../../api/pos'
import type { SaleResponse } from '../../types/pos'

const route = useRoute()
const router = useRouter()

const sale = ref<SaleResponse | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')

const accessToken = localStorage.getItem('access_token')

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatDate(value: string) {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return '-'
  }

  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'long',
    timeStyle: 'short',
  }).format(date)
}

function getPaymentMethodLabel(
  method: SaleResponse['paymentMethod'],
) {
  const labels: Record<SaleResponse['paymentMethod'], string> = {
    CASH: 'Tunai',
    BANK_TRANSFER: 'Transfer Bank',
    DEBIT: 'Debit',
    OTHER: 'Lainnya',
  }

  return labels[method]
}

function getStatusLabel(status: SaleResponse['status']) {
  return status === 'CANCELLED'
    ? 'Dibatalkan'
    : 'Lunas'
}

function goBack() {
  router.push('/sales')
}

async function loadSaleDetail() {
  errorMessage.value = ''
  isLoading.value = true
  sale.value = null

  try {
    if (!accessToken) {
      throw new Error('Sesi login tidak ditemukan.')
    }

    const saleId = route.params.id

    if (typeof saleId !== 'string' || !saleId.trim()) {
      throw new Error('ID transaksi tidak valid.')
    }

    sale.value = await getSaleDetail(
      accessToken,
      saleId,
    )
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal memuat detail transaksi.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadSaleDetail)
</script>

<template>
  <main class="space-y-6">
    <!-- Header -->
    <section>
      <button
        type="button"
        class="inline-flex min-h-10 items-center gap-2 rounded-lg px-2 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
        @click="goBack"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          class="h-4 w-4"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="m15 18-6-6 6-6"
          />
        </svg>

        Kembali ke riwayat penjualan
      </button>

      <div class="mt-4">
        <p class="text-sm font-medium text-emerald-700">
          Penjualan
        </p>

        <h1 class="text-2xl font-bold tracking-tight text-slate-900">
          Detail Transaksi
        </h1>

        <p class="mt-1 text-sm text-slate-500">
          Detail transaksi penjualan dan pembayaran.
        </p>
      </div>
    </section>

    <!-- Loading -->
    <section
      v-if="isLoading"
      class="space-y-6"
      aria-label="Memuat detail transaksi"
    >
      <div class="rounded-xl border border-slate-200 bg-white p-6">
        <div class="h-6 w-48 animate-pulse rounded bg-slate-200" />
        <div class="mt-3 h-4 w-64 animate-pulse rounded bg-slate-200" />

        <div class="mt-6 grid gap-4 sm:grid-cols-3">
          <div
            v-for="index in 3"
            :key="index"
            class="h-16 animate-pulse rounded-lg bg-slate-100"
          />
        </div>
      </div>

      <div class="rounded-xl border border-slate-200 bg-white">
        <div class="border-b border-slate-200 p-6">
          <div class="h-5 w-32 animate-pulse rounded bg-slate-200" />
        </div>

        <div class="space-y-4 p-6">
          <div
            v-for="index in 4"
            :key="index"
            class="h-12 animate-pulse rounded bg-slate-100"
          />
        </div>
      </div>
    </section>

    <!-- Error -->
    <section
      v-else-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
      role="alert"
    >
      <h2 class="font-semibold text-red-800">
        Detail transaksi gagal dimuat
      </h2>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>

      <div class="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          class="inline-flex min-h-11 items-center justify-center rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          @click="loadSaleDetail"
        >
          Coba lagi
        </button>

        <button
          type="button"
          class="inline-flex min-h-11 items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
          @click="goBack"
        >
          Kembali
        </button>
      </div>
    </section>

    <!-- Detail -->
    <template v-else-if="sale">
      <!-- Summary -->
      <section
        class="rounded-xl border border-slate-200 bg-white p-5 sm:p-6"
      >
        <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Nomor transaksi
            </p>

            <h2 class="mt-1 text-xl font-bold text-slate-900">
              {{ sale.saleNumber }}
            </h2>

            <p class="mt-1 text-sm text-slate-500">
              {{ formatDate(sale.createdAt) }}
            </p>
          </div>

          <span
            class="inline-flex w-fit rounded-full px-3 py-1.5 text-sm font-semibold"
            :class="
              sale.status === 'CANCELLED'
                ? 'bg-red-100 text-red-700'
                : 'bg-emerald-100 text-emerald-700'
            "
          >
            {{ getStatusLabel(sale.status) }}
          </span>
        </div>

        <div class="mt-6 grid gap-4 sm:grid-cols-3">
          <div class="rounded-lg bg-slate-50 p-4">
            <p class="text-xs font-medium text-slate-500">
              Jumlah item
            </p>

            <p class="mt-1 text-lg font-bold text-slate-900">
              {{ sale.items.length }} item
            </p>
          </div>

          <div class="rounded-lg bg-slate-50 p-4">
            <p class="text-xs font-medium text-slate-500">
              Metode pembayaran
            </p>

            <p class="mt-1 text-lg font-bold text-slate-900">
              {{ getPaymentMethodLabel(sale.paymentMethod) }}
            </p>
          </div>

          <div class="rounded-lg bg-slate-50 p-4">
            <p class="text-xs font-medium text-slate-500">
              Total
            </p>

            <p class="mt-1 text-lg font-bold text-slate-900">
              {{ formatCurrency(sale.total) }}
            </p>
          </div>
        </div>
      </section>

      <!-- Member -->
      <section
        class="rounded-xl border border-slate-200 bg-white p-5 sm:p-6"
      >
        <h2 class="text-base font-semibold text-slate-900">
          Anggota
        </h2>

        <div class="mt-4 rounded-lg bg-slate-50 p-4">
          <p
            v-if="sale.memberId"
            class="break-all text-sm text-slate-700"
          >
            Member ID:
            <span class="font-medium">
              {{ sale.memberId }}
            </span>
          </p>

          <p
            v-else
            class="text-sm text-slate-500"
          >
            Transaksi ini tidak menggunakan anggota.
          </p>
        </div>
      </section>

      <!-- Items -->
      <section
        class="overflow-hidden rounded-xl border border-slate-200 bg-white"
      >
        <div class="border-b border-slate-200 px-5 py-4 sm:px-6">
          <h2 class="font-semibold text-slate-900">
            Item Penjualan
          </h2>
        </div>

        <!-- Desktop -->
        <div class="hidden overflow-x-auto md:block">
          <table class="min-w-full divide-y divide-slate-200">
            <thead class="bg-slate-50">
              <tr>
                <th
                  scope="col"
                  class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                >
                  Produk
                </th>

                <th
                  scope="col"
                  class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500"
                >
                  Qty
                </th>

                <th
                  scope="col"
                  class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500"
                >
                  Harga
                </th>

                <th
                  scope="col"
                  class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500"
                >
                  Subtotal
                </th>
              </tr>
            </thead>

            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="item in sale.items"
                :key="`${sale.id}-${item.productId}`"
              >
                <td class="px-6 py-4">
                  <p class="font-medium text-slate-900">
                    {{ item.name }}
                  </p>

                  <p class="mt-1 text-xs text-slate-500">
                    {{ item.sku }} · {{ item.unit }}
                  </p>
                </td>

                <td class="whitespace-nowrap px-6 py-4 text-right text-sm text-slate-600">
                  {{ item.quantity }}
                </td>

                <td class="whitespace-nowrap px-6 py-4 text-right text-sm text-slate-600">
                  {{ formatCurrency(item.unitPrice) }}
                </td>

                <td class="whitespace-nowrap px-6 py-4 text-right text-sm font-semibold text-slate-900">
                  {{ formatCurrency(item.subtotal) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Mobile -->
        <div class="divide-y divide-slate-200 md:hidden">
          <article
            v-for="item in sale.items"
            :key="`${sale.id}-${item.productId}`"
            class="space-y-3 p-4"
          >
            <div>
              <h3 class="font-medium text-slate-900">
                {{ item.name }}
              </h3>

              <p class="mt-1 text-xs text-slate-500">
                {{ item.sku }} · {{ item.unit }}
              </p>
            </div>

            <dl class="grid grid-cols-3 gap-3 text-sm">
              <div>
                <dt class="text-xs text-slate-500">
                  Qty
                </dt>

                <dd class="mt-1 font-medium text-slate-800">
                  {{ item.quantity }}
                </dd>
              </div>

              <div>
                <dt class="text-xs text-slate-500">
                  Harga
                </dt>

                <dd class="mt-1 font-medium text-slate-800">
                  {{ formatCurrency(item.unitPrice) }}
                </dd>
              </div>

              <div class="text-right">
                <dt class="text-xs text-slate-500">
                  Subtotal
                </dt>

                <dd class="mt-1 font-semibold text-slate-900">
                  {{ formatCurrency(item.subtotal) }}
                </dd>
              </div>
            </dl>
          </article>
        </div>
      </section>

      <!-- Payment -->
      <section
        class="rounded-xl border border-slate-200 bg-white p-5 sm:p-6"
      >
        <h2 class="text-base font-semibold text-slate-900">
          Ringkasan Pembayaran
        </h2>

        <dl class="mt-4 space-y-3 text-sm">
          <div class="flex items-center justify-between gap-4">
            <dt class="text-slate-500">
              Subtotal
            </dt>

            <dd class="font-medium text-slate-900">
              {{ formatCurrency(sale.subtotal) }}
            </dd>
          </div>

          <div class="flex items-center justify-between gap-4">
            <dt class="text-slate-500">
              Total
            </dt>

            <dd class="font-bold text-slate-900">
              {{ formatCurrency(sale.total) }}
            </dd>
          </div>

          <div class="flex items-center justify-between gap-4">
            <dt class="text-slate-500">
              Dibayar
            </dt>

            <dd class="font-medium text-slate-900">
              {{ formatCurrency(sale.paidAmount) }}
            </dd>
          </div>

          <div class="flex items-center justify-between gap-4">
            <dt class="text-slate-500">
              Kembalian
            </dt>

            <dd class="font-medium text-slate-900">
              {{ formatCurrency(sale.changeAmount) }}
            </dd>
          </div>

          <div class="border-t border-slate-200 pt-3">
            <div class="flex items-center justify-between gap-4">
              <dt class="font-semibold text-slate-900">
                Metode pembayaran
              </dt>

              <dd class="font-semibold text-slate-900">
                {{ getPaymentMethodLabel(sale.paymentMethod) }}
              </dd>
            </div>
          </div>
        </dl>
      </section>
    </template>
  </main>
</template>