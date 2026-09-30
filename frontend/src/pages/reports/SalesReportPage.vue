<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useAuth } from '../../stores/auth'
import { getSalesReport } from '../../api/reports'
import type { SalesReport } from '../../types/salesReport'

const { token } = useAuth()

const today = new Date().toISOString().slice(0, 10)

const startDate = ref(today)
const endDate = ref(today)

const report = ref<SalesReport | null>(null)

const isLoading = ref(false)
const errorMessage = ref('')
const fieldError = ref('')

const hasData = computed(() => {
  if (!report.value) {
    return false
  }

  return (
    report.value.total_transactions > 0 ||
    report.value.total_items_sold > 0 ||
    report.value.total_sales > 0
  )
})

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(Number(value) || 0)
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('id-ID', {
    maximumFractionDigits: 2,
  }).format(Number(value) || 0)
}

function validateDateRange() {
  fieldError.value = ''

  if (!startDate.value || !endDate.value) {
    fieldError.value = 'Tanggal mulai dan tanggal akhir wajib diisi.'
    return false
  }

  if (startDate.value > endDate.value) {
    fieldError.value =
      'Tanggal mulai tidak boleh lebih besar dari tanggal akhir.'
    return false
  }

  return true
}

async function loadReport() {
  errorMessage.value = ''

  if (!validateDateRange()) {
    return
  }

  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    return
  }

  isLoading.value = true

  try {
    report.value = await getSalesReport(token.value, {
      start_date: startDate.value,
      end_date: endDate.value,
    })
  } catch (error) {
    report.value = null

    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Laporan penjualan gagal dimuat.'
  } finally {
    isLoading.value = false
  }
}

function setToday() {
  startDate.value = today
  endDate.value = today
  loadReport()
}

function setLast7Days() {
  const end = new Date()
  const start = new Date()

  start.setDate(start.getDate() - 6)

  startDate.value = start.toISOString().slice(0, 10)
  endDate.value = end.toISOString().slice(0, 10)

  loadReport()
}

function setLast30Days() {
  const end = new Date()
  const start = new Date()

  start.setDate(start.getDate() - 29)

  startDate.value = start.toISOString().slice(0, 10)
  endDate.value = end.toISOString().slice(0, 10)

  loadReport()
}

onMounted(loadReport)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-[#12372A]">
        Laporan Penjualan
      </h1>

      <p class="mt-1 text-sm text-slate-600">
        Ringkasan transaksi dan penjualan berdasarkan periode yang dipilih.
      </p>
    </div>

    <!-- Filter -->
    <section
      class="rounded-xl border border-slate-200 bg-white p-5"
    >
      <div
        class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"
      >
        <div class="grid flex-1 gap-4 sm:grid-cols-2">
          <div>
            <label
              for="start-date"
              class="block text-sm font-medium text-slate-700"
            >
              Tanggal mulai
            </label>

            <input
              id="start-date"
              v-model="startDate"
              type="date"
              class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
            />
          </div>

          <div>
            <label
              for="end-date"
              class="block text-sm font-medium text-slate-700"
            >
              Tanggal akhir
            </label>

            <input
              id="end-date"
              v-model="endDate"
              type="date"
              class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
            />
          </div>
        </div>

        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            @click="setToday"
          >
            Hari ini
          </button>

          <button
            type="button"
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            @click="setLast7Days"
          >
            7 hari
          </button>

          <button
            type="button"
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            @click="setLast30Days"
          >
            30 hari
          </button>

          <button
            type="button"
            class="rounded-lg bg-[#176B4D] px-4 py-2 text-sm font-semibold text-white hover:bg-[#12372A] disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="isLoading"
            @click="loadReport"
          >
            {{ isLoading ? 'Memuat...' : 'Tampilkan' }}
          </button>
        </div>
      </div>

      <div
        v-if="fieldError"
        class="mt-4 rounded-lg border border-[#E7B8B2] bg-[#FEF3F2] px-4 py-3 text-sm text-[#C0392B]"
      >
        {{ fieldError }}
      </div>
    </section>

    <!-- Loading -->
    <div
      v-if="isLoading"
      class="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-600"
    >
      Memuat laporan penjualan...
    </div>

    <!-- Error -->
    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-[#E7B8B2] bg-[#FEF3F2] p-5 text-sm text-[#C0392B]"
    >
      <p class="font-semibold">
        Laporan gagal dimuat
      </p>

      <p class="mt-1">
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-3 rounded-lg bg-[#C0392B] px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
        @click="loadReport"
      >
        Coba lagi
      </button>
    </div>

    <!-- Report -->
    <template v-else-if="report">
      <section
        class="grid gap-4 sm:grid-cols-2 xl:grid-cols-5"
      >
        <div
          class="rounded-xl border border-slate-200 bg-white p-5"
        >
          <p class="text-sm text-slate-500">
            Total transaksi
          </p>

          <p class="mt-2 text-2xl font-bold text-[#12372A]">
            {{ formatNumber(report.total_transactions) }}
          </p>
        </div>

        <div
          class="rounded-xl border border-slate-200 bg-white p-5"
        >
          <p class="text-sm text-slate-500">
            Total item terjual
          </p>

          <p class="mt-2 text-2xl font-bold text-[#12372A]">
            {{ formatNumber(report.total_items_sold) }}
          </p>
        </div>

        <div
          class="rounded-xl border border-slate-200 bg-white p-5"
        >
          <p class="text-sm text-slate-500">
            Total penjualan
          </p>

          <p class="mt-2 text-xl font-bold text-[#12372A]">
            {{ formatCurrency(report.total_sales) }}
          </p>
        </div>

        <div
          class="rounded-xl border border-slate-200 bg-white p-5"
        >
          <p class="text-sm text-slate-500">
            Discount
          </p>

          <p class="mt-2 text-xl font-bold text-[#12372A]">
            {{ formatCurrency(report.discount) }}
          </p>
        </div>

        <div
          class="rounded-xl border border-[#B9DEC9] bg-[#F0F8F5] p-5"
        >
          <p class="text-sm text-[#176B4D]">
            Revenue
          </p>

          <p class="mt-2 text-xl font-bold text-[#12372A]">
            {{ formatCurrency(report.revenue) }}
          </p>
        </div>
      </section>

      <section
        class="rounded-xl border border-slate-200 bg-white p-5"
      >
        <div
          class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <h2 class="font-semibold text-[#12372A]">
              Ringkasan periode
            </h2>

            <p class="mt-1 text-sm text-slate-500">
              {{ report.start_date }} sampai {{ report.end_date }}
            </p>
          </div>

          <div
            class="rounded-lg bg-slate-50 px-4 py-2 text-sm text-slate-600"
          >
            Transaksi PAID
          </div>
        </div>

        <div
          v-if="!hasData"
          class="mt-6 rounded-lg border border-dashed border-slate-300 p-8 text-center"
        >
          <p class="font-medium text-slate-700">
            Belum ada penjualan pada periode ini.
          </p>

          <p class="mt-1 text-sm text-slate-500">
            Coba pilih periode lain untuk melihat data penjualan.
          </p>
        </div>

        <div
          v-else
          class="mt-6 grid gap-4 md:grid-cols-2"
        >
          <div class="rounded-lg bg-slate-50 p-4">
            <p class="text-sm text-slate-500">
              Penjualan
            </p>

            <p class="mt-1 text-lg font-semibold text-[#12372A]">
              {{ formatCurrency(report.total_sales) }}
            </p>
          </div>

          <div class="rounded-lg bg-slate-50 p-4">
            <p class="text-sm text-slate-500">
              Revenue
            </p>

            <p class="mt-1 text-lg font-semibold text-[#176B4D]">
              {{ formatCurrency(report.revenue) }}
            </p>
          </div>
        </div>
      </section>
    </template>

    <!-- Empty -->
    <div
      v-else
      class="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center"
    >
      <p class="font-medium text-slate-700">
        Belum ada data laporan.
      </p>

      <p class="mt-1 text-sm text-slate-500">
        Pilih periode lalu tampilkan laporan.
      </p>
    </div>
  </div>
</template>