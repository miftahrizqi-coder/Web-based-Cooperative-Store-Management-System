<script setup lang="ts">
import { ref } from 'vue'
import DashboardKpiCard from '../../components/dashboard/DashboardKpiCard.vue'

type DashboardState = 'loading' | 'loaded' | 'partial_error'

const dashboardState = ref<DashboardState>('loaded')

const kpis = [
  'Penjualan hari ini',
  'Jumlah transaksi',
  'Total produk',
  'Total anggota',
  'Low/out of stock',
  'Active PO',
  'Hutang supplier',
  'Invoice jatuh tempo',
  'Expenses',
]
</script>

<template>
  <div class="space-y-6">
    <header>
      <h1 class="text-2xl font-semibold text-gray-900">
        Dashboard
      </h1>

      <p class="mt-1 text-sm text-gray-600">
        Ringkasan operasional toko koperasi.
      </p>
    </header>

    <section aria-labelledby="dashboard-kpi-heading">
      <div class="mb-3">
        <h2
          id="dashboard-kpi-heading"
          class="text-base font-semibold text-gray-900"
        >
          Ringkasan
        </h2>
      </div>

      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <DashboardKpiCard
            v-for="label in kpis"
            :key="label"
            :label="label"
            value="—"
            :loading="dashboardState === 'loading'"
        />
      </div>
    </section>

   <section aria-labelledby="performance-heading">
        <h2
            id="performance-heading"
            class="text-base font-semibold text-gray-900"
        >
            Performance
        </h2>

        <div class="mt-3 rounded-xl border bg-white p-6">
            <div class="flex min-h-72 items-center justify-center">
            <div class="text-center">
                <p class="text-sm font-medium text-gray-700">
                Sales / Transaction Analytics
                </p>

                <p class="mt-1 text-sm text-gray-500">
                Grafik penjualan dan transaksi akan ditampilkan di sini.
                </p>
            </div>
            </div>
        </div>
    </section>

    <section aria-labelledby="operations-heading">
      <h2
        id="operations-heading"
        class="text-base font-semibold text-gray-900"
      >
        Operational attention
      </h2>

      <div class="mt-3 rounded-xl border bg-white p-6">
        <p class="text-sm text-gray-500">
          Informasi stok, procurement, dan payables akan ditampilkan di sini.
        </p>
      </div>
    </section>

    <section aria-labelledby="operations-heading">
        <h2
            id="operations-heading"
            class="text-base font-semibold text-gray-900"
        >
            Operational attention
        </h2>

        <div class="mt-3 grid gap-4 md:grid-cols-2">
            <article class="rounded-xl border bg-white p-5">
            <h3 class="font-medium text-gray-900">
                Low / out of stock
            </h3>

            <p class="mt-2 text-sm text-gray-500">
                Belum ada data stok yang tersedia.
            </p>
            </article>

            <article class="rounded-xl border bg-white p-5">
            <h3 class="font-medium text-gray-900">
                Invoice jatuh tempo
            </h3>

            <p class="mt-2 text-sm text-gray-500">
                Belum ada data invoice yang tersedia.
            </p>
            </article>
        </div>
    </section>

    <section aria-labelledby="procurement-heading">
        <h2
            id="procurement-heading"
            class="text-base font-semibold text-gray-900"
        >
            Procurement / Payables
        </h2>

        <div class="mt-3 rounded-xl border bg-white p-5">
            <p class="text-sm text-gray-500">
            Data purchase order dan hutang supplier akan ditampilkan di sini.
            </p>
        </div>
    </section>

    <section aria-labelledby="best-selling-heading">
        <h2
            id="best-selling-heading"
            class="text-base font-semibold text-gray-900"
        >
            Best Selling Products
        </h2>

        <div class="mt-3 rounded-xl border bg-white p-5">
            <p class="text-sm text-gray-500">
            Data produk terlaris akan ditampilkan di sini.
            </p>
        </div>
    </section>
  </div>
</template>