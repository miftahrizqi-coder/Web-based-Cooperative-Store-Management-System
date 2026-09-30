<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getSales } from '../../api/pos'
import type { SaleResponse } from '../../types/pos'

const router = useRouter()

const sales = ref<SaleResponse[]>([])
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
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function getPaymentMethodLabel(method: SaleResponse['paymentMethod']) {
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

function viewSaleDetail(saleId: string) {
  router.push(`/sales/${saleId}`)
}

async function loadSales() {
  errorMessage.value = ''
  isLoading.value = true

  try {
    if (!accessToken) {
      throw new Error('Sesi login tidak ditemukan.')
    }

    sales.value = await getSales(accessToken)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal memuat riwayat penjualan.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadSales)
</script>

<template>
  <main class="space-y-6">
    <section>
      <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-sm font-medium text-emerald-700">
            Penjualan
          </p>

          <h1 class="text-2xl font-bold tracking-tight text-slate-900">
            Riwayat Penjualan
          </h1>

          <p class="mt-1 text-sm text-slate-500">
            Lihat transaksi penjualan yang sudah diproses.
          </p>
        </div>

        <button
          type="button"
          class="inline-flex min-h-11 items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
          :disabled="isLoading"
          @click="loadSales"
        >
          Muat ulang
        </button>
      </div>
    </section>

    <!-- Loading -->
    <section
      v-if="isLoading"
      class="overflow-hidden rounded-xl border border-slate-200 bg-white"
      aria-label="Memuat riwayat penjualan"
    >
      <div class="hidden border-b border-slate-200 px-6 py-4 md:grid md:grid-cols-6 md:gap-4">
        <div
          v-for="index in 6"
          :key="index"
          class="h-4 animate-pulse rounded bg-slate-200"
        />
      </div>

      <div class="divide-y divide-slate-100">
        <div
          v-for="index in 5"
          :key="index"
          class="space-y-3 px-4 py-5 md:grid md:grid-cols-6 md:items-center md:gap-4 md:space-y-0 md:px-6"
        >
          <div class="h-4 w-32 animate-pulse rounded bg-slate-200" />
          <div class="h-4 w-28 animate-pulse rounded bg-slate-200" />
          <div class="h-4 w-20 animate-pulse rounded bg-slate-200" />
          <div class="h-4 w-24 animate-pulse rounded bg-slate-200" />
          <div class="h-6 w-16 animate-pulse rounded-full bg-slate-200" />
          <div class="h-9 w-24 animate-pulse rounded-lg bg-slate-200" />
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
        Riwayat penjualan gagal dimuat
      </h2>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-4 inline-flex min-h-11 items-center justify-center rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        @click="loadSales"
      >
        Coba lagi
      </button>
    </section>

    <!-- Empty -->
    <section
      v-else-if="sales.length === 0"
      class="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center"
    >
      <div class="mx-auto max-w-md">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            class="h-6 w-6"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M3 7.5h18M5 4.5h14a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-11a2 2 0 0 1 2-2Z"
            />
          </svg>
        </div>

        <h2 class="mt-4 text-lg font-semibold text-slate-900">
          Belum ada transaksi penjualan
        </h2>

        <p class="mt-1 text-sm text-slate-500">
          Transaksi yang berhasil dibuat melalui POS akan muncul di halaman ini.
        </p>
      </div>
    </section>

    <!-- Sales table -->
    <section
      v-else
      class="overflow-hidden rounded-xl border border-slate-200 bg-white"
    >
      <div class="border-b border-slate-200 px-4 py-4 sm:px-6">
        <div class="flex items-center justify-between gap-4">
          <div>
            <h2 class="font-semibold text-slate-900">
              Daftar Transaksi
            </h2>

            <p class="mt-1 text-sm text-slate-500">
              {{ sales.length }} transaksi
            </p>
          </div>
        </div>
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
                Transaksi
              </th>

              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Tanggal
              </th>

              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Item
              </th>

              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Pembayaran
              </th>

              <th
                scope="col"
                class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Total
              </th>

              <th
                scope="col"
                class="px-6 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Status
              </th>

              <th
                scope="col"
                class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Aksi
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-slate-100 bg-white">
            <tr
              v-for="sale in sales"
              :key="sale.id"
              class="transition hover:bg-slate-50"
            >
              <td class="whitespace-nowrap px-6 py-4">
                <p class="font-medium text-slate-900">
                  {{ sale.saleNumber }}
                </p>

                <p class="mt-1 text-xs text-slate-500">
                  {{ sale.id }}
                </p>
              </td>

              <td class="whitespace-nowrap px-6 py-4 text-sm text-slate-600">
                {{ formatDate(sale.createdAt) }}
              </td>

              <td class="px-6 py-4 text-sm text-slate-600">
                {{ sale.items.length }} item
              </td>

              <td class="whitespace-nowrap px-6 py-4 text-sm text-slate-600">
                {{ getPaymentMethodLabel(sale.paymentMethod) }}
              </td>

              <td class="whitespace-nowrap px-6 py-4 text-right text-sm font-semibold text-slate-900">
                {{ formatCurrency(sale.total) }}
              </td>

              <td class="whitespace-nowrap px-6 py-4 text-center">
                <span
                  class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold"
                  :class="
                    sale.status === 'CANCELLED'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-emerald-100 text-emerald-700'
                  "
                >
                  {{ getStatusLabel(sale.status) }}
                </span>
              </td>

              <td class="whitespace-nowrap px-6 py-4 text-right">
                <button
                  type="button"
                  class="inline-flex min-h-10 items-center justify-center rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
                  @click="viewSaleDetail(sale.id)"
                >
                  Lihat detail
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Mobile -->
      <div class="divide-y divide-slate-200 md:hidden">
        <article
          v-for="sale in sales"
          :key="sale.id"
          class="space-y-4 p-4"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <h3 class="truncate font-semibold text-slate-900">
                {{ sale.saleNumber }}
              </h3>

              <p class="mt-1 text-xs text-slate-500">
                {{ formatDate(sale.createdAt) }}
              </p>
            </div>

            <span
              class="shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold"
              :class="
                sale.status === 'CANCELLED'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-emerald-100 text-emerald-700'
              "
            >
              {{ getStatusLabel(sale.status) }}
            </span>
          </div>

          <dl class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt class="text-xs text-slate-500">
                Item
              </dt>

              <dd class="mt-1 font-medium text-slate-800">
                {{ sale.items.length }} item
              </dd>
            </div>

            <div>
              <dt class="text-xs text-slate-500">
                Pembayaran
              </dt>

              <dd class="mt-1 font-medium text-slate-800">
                {{ getPaymentMethodLabel(sale.paymentMethod) }}
              </dd>
            </div>

            <div class="col-span-2">
              <dt class="text-xs text-slate-500">
                Total
              </dt>

              <dd class="mt-1 text-lg font-bold text-slate-900">
                {{ formatCurrency(sale.total) }}
              </dd>
            </div>
          </dl>

          <button
            type="button"
            class="inline-flex min-h-11 w-full items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
            @click="viewSaleDetail(sale.id)"
          >
            Lihat detail
          </button>
        </article>
      </div>
    </section>
  </main>
</template>