<script setup lang="ts">
import {
  computed,
  onMounted,
  ref,
} from 'vue'

import DashboardKpiCard from '../../components/dashboard/DashboardKpiCard.vue'

import {
  getInventoryAlerts,
} from '../../api/inventory'

import type {
  StockAlert,
} from '../../types/inventory'

type DashboardState =
  | 'loading'
  | 'loaded'
  | 'partial_error'

const dashboardState =
  ref<DashboardState>('loaded')

const stockAlerts = ref<StockAlert[]>([])
const stockAlertLoading = ref(true)
const stockAlertError = ref('')

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

const outOfStockAlerts = computed(() =>
  stockAlerts.value.filter(
    (alert) =>
      alert.status === 'OUT_OF_STOCK',
  ),
)

const lowStockAlerts = computed(() =>
  stockAlerts.value.filter(
    (alert) =>
      alert.status === 'LOW_STOCK',
  ),
)

const stockAlertCount = computed(
  () => stockAlerts.value.length,
)

const hasStockAlerts = computed(
  () => stockAlerts.value.length > 0,
)

async function loadStockAlerts() {
  stockAlertLoading.value = true
  stockAlertError.value = ''

  const accessToken =
    localStorage.getItem(
      'access_token',
    )

  if (!accessToken) {
    stockAlertError.value =
      'Sesi login tidak ditemukan.'
    stockAlertLoading.value = false
    return
  }

  try {
    stockAlerts.value =
      await getInventoryAlerts(
        accessToken,
      )
  } catch (error) {
    stockAlertError.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil notifikasi stok.'

    dashboardState.value =
      'partial_error'
  } finally {
    stockAlertLoading.value = false
  }
}

function formatNumber(
  value: number,
) {
  return new Intl.NumberFormat(
    'id-ID',
  ).format(value)
}

onMounted(() => {
  loadStockAlerts()
})
</script>

<template>
  <div class="space-y-6">
    <header>
      <h1
        class="text-2xl font-semibold text-gray-900"
      >
        Dashboard
      </h1>

      <p
        class="mt-1 text-sm text-gray-600"
      >
        Ringkasan operasional toko koperasi.
      </p>
    </header>

    <section
      aria-labelledby="dashboard-kpi-heading"
    >
      <div class="mb-3">
        <h2
          id="dashboard-kpi-heading"
          class="text-base font-semibold text-gray-900"
        >
          Ringkasan
        </h2>
      </div>

      <div
        class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
      >
        <DashboardKpiCard
          v-for="label in kpis"
          :key="label"
          :label="label"
          value="—"
          :loading="
            dashboardState === 'loading'
          "
        />
      </div>
    </section>

    <section
      aria-labelledby="performance-heading"
    >
      <h2
        id="performance-heading"
        class="text-base font-semibold text-gray-900"
      >
        Performance
      </h2>

      <div
        class="mt-3 rounded-xl border bg-white p-6"
      >
        <div
          class="flex min-h-72 items-center justify-center"
        >
          <div class="text-center">
            <p
              class="text-sm font-medium text-gray-700"
            >
              Sales / Transaction Analytics
            </p>

            <p
              class="mt-1 text-sm text-gray-500"
            >
              Grafik penjualan dan transaksi akan
              ditampilkan di sini.
            </p>
          </div>
        </div>
      </div>
    </section>

    <section
      aria-labelledby="stock-alert-heading"
    >
      <div
        class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <h2
            id="stock-alert-heading"
            class="text-base font-semibold text-gray-900"
          >
            Operational attention
          </h2>

          <p
            class="mt-1 text-sm text-gray-500"
          >
            Notifikasi stok minimum dan stok habis.
          </p>
        </div>

        <span
          v-if="!stockAlertLoading"
          class="inline-flex w-fit items-center rounded-full px-3 py-1 text-xs font-medium"
          :class="
            hasStockAlerts
              ? 'bg-red-100 text-red-700'
              : 'bg-green-100 text-green-700'
          "
        >
          {{
            stockAlertCount
          }}
          alert
        </span>
      </div>

      <div
        class="mt-3 rounded-xl border bg-white p-5"
      >
        <!-- Loading -->
        <div
          v-if="stockAlertLoading"
          class="space-y-3"
          aria-live="polite"
        >
          <div
            class="h-16 animate-pulse rounded-lg bg-gray-100"
          />

          <div
            class="h-16 animate-pulse rounded-lg bg-gray-100"
          />

          <div
            class="h-16 animate-pulse rounded-lg bg-gray-100"
          />
        </div>

        <!-- Error -->
        <div
          v-else-if="stockAlertError"
          class="rounded-lg border border-red-200 bg-red-50 p-4"
          aria-live="assertive"
        >
          <p
            class="font-medium text-red-800"
          >
            Notifikasi stok tidak dapat dimuat
          </p>

          <p
            class="mt-1 text-sm text-red-700"
          >
            {{ stockAlertError }}
          </p>

          <button
            type="button"
            class="mt-3 rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
            @click="loadStockAlerts"
          >
            Coba Lagi
          </button>
        </div>

        <!-- Empty -->
        <div
          v-else-if="!hasStockAlerts"
          class="py-6 text-center"
        >
          <p
            class="text-sm font-medium text-green-700"
          >
            Tidak ada notifikasi stok.
          </p>

          <p
            class="mt-1 text-sm text-gray-500"
          >
            Semua stok berada di atas batas minimum.
          </p>
        </div>

        <!-- Alerts -->
        <div
          v-else
          class="space-y-4"
        >
          <!-- Out of stock -->
          <div
            v-if="outOfStockAlerts.length > 0"
          >
            <div
              class="mb-2 flex items-center justify-between"
            >
              <h3
                class="font-medium text-red-700"
              >
                Out of Stock
              </h3>

              <span
                class="text-sm text-gray-500"
              >
                {{
                  outOfStockAlerts.length
                }}
                produk
              </span>
            </div>

            <div class="space-y-2">
              <article
                v-for="alert in outOfStockAlerts"
                :key="alert.product_id"
                class="rounded-lg border border-red-200 bg-red-50 p-4"
              >
                <div
                  class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div class="min-w-0">
                    <p
                      class="font-medium text-gray-900"
                    >
                      {{ alert.name }}
                    </p>

                    <p
                      class="mt-1 text-xs text-gray-500"
                    >
                      SKU:
                      {{ alert.sku }}
                    </p>
                  </div>

                  <div
                    class="grid grid-cols-2 gap-4 text-sm sm:text-right"
                  >
                    <div>
                      <p
                        class="text-xs text-gray-500"
                      >
                        Stok
                      </p>

                      <p
                        class="font-semibold text-red-700"
                      >
                        {{
                          formatNumber(
                            alert.stock,
                          )
                        }}
                      </p>
                    </div>

                    <div>
                      <p
                        class="text-xs text-gray-500"
                      >
                        Minimum
                      </p>

                      <p
                        class="font-semibold text-gray-900"
                      >
                        {{
                          formatNumber(
                            alert.minimum_stock,
                          )
                        }}
                      </p>
                    </div>
                  </div>
                </div>
              </article>
            </div>
          </div>

          <!-- Low stock -->
          <div
            v-if="lowStockAlerts.length > 0"
          >
            <div
              class="mb-2 flex items-center justify-between"
            >
              <h3
                class="font-medium text-amber-700"
              >
                Low Stock
              </h3>

              <span
                class="text-sm text-gray-500"
              >
                {{
                  lowStockAlerts.length
                }}
                produk
              </span>
            </div>

            <div class="space-y-2">
              <article
                v-for="alert in lowStockAlerts"
                :key="alert.product_id"
                class="rounded-lg border border-amber-200 bg-amber-50 p-4"
              >
                <div
                  class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div class="min-w-0">
                    <p
                      class="font-medium text-gray-900"
                    >
                      {{ alert.name }}
                    </p>

                    <p
                      class="mt-1 text-xs text-gray-500"
                    >
                      SKU:
                      {{ alert.sku }}
                    </p>
                  </div>

                  <div
                    class="grid grid-cols-2 gap-4 text-sm sm:text-right"
                  >
                    <div>
                      <p
                        class="text-xs text-gray-500"
                      >
                        Stok
                      </p>

                      <p
                        class="font-semibold text-amber-700"
                      >
                        {{
                          formatNumber(
                            alert.stock,
                          )
                        }}
                      </p>
                    </div>

                    <div>
                      <p
                        class="text-xs text-gray-500"
                      >
                        Minimum
                      </p>

                      <p
                        class="font-semibold text-gray-900"
                      >
                        {{
                          formatNumber(
                            alert.minimum_stock,
                          )
                        }}
                      </p>
                    </div>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section
      aria-labelledby="procurement-heading"
    >
      <h2
        id="procurement-heading"
        class="text-base font-semibold text-gray-900"
      >
        Procurement / Payables
      </h2>

      <div
        class="mt-3 rounded-xl border bg-white p-5"
      >
        <p
          class="text-sm text-gray-500"
        >
          Data purchase order dan hutang supplier akan
          ditampilkan di sini.
        </p>
      </div>
    </section>

    <section
      aria-labelledby="best-selling-heading"
    >
      <h2
        id="best-selling-heading"
        class="text-base font-semibold text-gray-900"
      >
        Best Selling Products
      </h2>

      <div
        class="mt-3 rounded-xl border bg-white p-5"
      >
        <p
          class="text-sm text-gray-500"
        >
          Data produk terlaris akan ditampilkan di sini.
        </p>
      </div>
    </section>
  </div>
</template>