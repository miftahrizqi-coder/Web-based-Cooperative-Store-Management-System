<script setup lang="ts">
import {
  computed,
  onMounted,
  ref,
} from 'vue'

import {
  getDashboardAnalytics,
} from '../../api/dashboard'

import {
  getInventoryAlerts,
} from '../../api/inventory'

import type {
  DashboardAnalytics,
} from '../../types/dashboard'

import type {
  StockAlert,
} from '../../types/inventory'

type DashboardState =
  | 'loading'
  | 'loaded'
  | 'partial_error'

const dashboardState = ref<DashboardState>('loading')

const stockAlerts = ref<StockAlert[]>([])
const stockAlertLoading = ref(true)
const stockAlertError = ref('')

/**
 * Dashboard KPI mengikuti DESIGN.md §7.2.
 * Nilai tetap "—" sampai endpoint KPI tersedia.
 */
const dashboardAnalytics = ref<DashboardAnalytics | null>(null)

const kpis = computed(() => {
  const analytics = dashboardAnalytics.value

  return [
    {
      label: 'Penjualan hari ini',
      value: analytics
        ? formatCurrency(analytics.sales_today)
        : '—',
      context: 'Hari ini',
      kind: 'money',
    },
    {
      label: 'Jumlah transaksi',
      value: analytics
        ? formatNumber(analytics.transaction_count_today)
        : '—',
      context: 'Hari ini',
      kind: 'number',
    },
    {
      label: 'Total produk',
      value: analytics
        ? formatNumber(analytics.total_products)
        : '—',
      context: 'Produk aktif',
      kind: 'number',
    },
    {
      label: 'Total anggota',
      value: analytics
        ? formatNumber(analytics.total_members)
        : '—',
      context: 'Anggota terdaftar',
      kind: 'number',
    },
    {
      label: 'Low / out of stock',
      value: analytics
        ? formatNumber(analytics.low_stock_count)
        : '—',
      context: 'Perlu perhatian',
      kind: 'warning',
    },
    {
      label: 'Active PO',
      value: analytics
        ? formatNumber(analytics.active_po_count)
        : '—',
      context: 'Pengadaan aktif',
      kind: 'number',
    },
    {
      label: 'Hutang supplier',
      value: analytics
        ? formatCurrency(analytics.supplier_payable)
        : '—',
      context: 'Outstanding',
      kind: 'money',
    },
    {
      label: 'Invoice jatuh tempo',
      value: analytics
        ? formatNumber(analytics.overdue_invoice_count)
        : '—',
      context: 'Perlu pembayaran',
      kind: 'warning',
    },
    {
      label: 'Expenses',
      value:
        analytics?.expenses !== null &&
        analytics?.expenses !== undefined
          ? formatCurrency(analytics.expenses)
          : '—',
      context: 'Periode berjalan',
      kind: 'money',
    },
  ]
})

const outOfStockAlerts = computed(() =>
  stockAlerts.value.filter(
    (alert) => alert.status === 'OUT_OF_STOCK',
  ),
)

const lowStockAlerts = computed(() =>
  stockAlerts.value.filter(
    (alert) => alert.status === 'LOW_STOCK',
  ),
)

const stockAlertCount = computed(
  () => stockAlerts.value.length,
)

const hasStockAlerts = computed(
  () => stockAlerts.value.length > 0,
)

const dashboardLoaded = computed(
  () => dashboardState.value === 'loaded',
)

async function loadDashboardAnalytics() {
  const accessToken = localStorage.getItem(
    'access_token',
  )

  if (!accessToken) {
    dashboardState.value = 'partial_error'
    return
  }

  try {
    dashboardAnalytics.value =
      await getDashboardAnalytics(accessToken)

    dashboardState.value = 'loaded'
  } catch {
    dashboardState.value = 'partial_error'
  }
}

async function loadStockAlerts() {
  stockAlertLoading.value = true
  stockAlertError.value = ''

  const accessToken = localStorage.getItem(
    'access_token',
  )

  if (!accessToken) {
    stockAlertError.value =
      'Sesi login tidak ditemukan. Silakan masuk kembali.'
    dashboardState.value = 'partial_error'
    stockAlertLoading.value = false
    return
  }

  try {
    stockAlerts.value = await getInventoryAlerts(
      accessToken,
    )

    dashboardState.value = 'loaded'
  } catch (error) {
    stockAlertError.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil notifikasi stok.'

    dashboardState.value = 'partial_error'
  } finally {
    stockAlertLoading.value = false
  }
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('id-ID').format(value)
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

onMounted(() => {
  loadDashboardAnalytics()
  loadStockAlerts()
})
</script>

<template>
  <main
    class="dashboard-page"
    aria-labelledby="dashboard-title"
  >
    <!-- Page Header -->
    <header class="page-header">
      <div>
        <p class="eyebrow">OVERVIEW</p>

        <h1 id="dashboard-title">
          Dashboard
        </h1>

        <p class="page-description">
          Ringkasan operasional toko koperasi.
        </p>
      </div>

      <div
        class="header-status"
        aria-live="polite"
      >
        <span
          class="status-dot"
          :class="{
            'status-dot--active': dashboardLoaded,
            'status-dot--warning':
              dashboardState === 'partial_error',
          }"
          aria-hidden="true"
        />

        <span>
          {{
            dashboardState === 'partial_error'
              ? 'Sebagian data bermasalah'
              : 'Data operasional'
          }}
        </span>
      </div>
    </header>

    <!-- KPI Row -->
    <section
      class="dashboard-section"
      aria-labelledby="kpi-heading"
    >
      <div class="section-heading">
        <div>
          <h2 id="kpi-heading">
            Ringkasan
          </h2>

          <p>
            Indikator utama aktivitas toko.
          </p>
        </div>
      </div>

      <div class="kpi-grid">
        <article
          v-for="kpi in kpis"
          :key="kpi.label"
          class="kpi-card"
          :class="{
            'kpi-card--warning':
              kpi.kind === 'warning',
          }"
        >
          <div class="kpi-card__top">
            <span class="kpi-label">
              {{ kpi.label }}
            </span>

            <span
              v-if="kpi.kind === 'warning'"
              class="kpi-indicator kpi-indicator--warning"
              aria-hidden="true"
            >
              !
            </span>
          </div>

          <div
            v-if="dashboardState === 'loading'"
            class="skeleton skeleton--kpi-value"
            aria-label="Memuat data"
          />

          <p
            v-else
            class="kpi-value"
            :class="{
              'kpi-value--money':
                kpi.kind === 'money',
              'kpi-value--warning':
                kpi.kind === 'warning',
            }"
          >
            {{ kpi.value }}
          </p>

          <p class="kpi-context">
            {{ kpi.context }}
          </p>
        </article>
      </div>
    </section>

    <!-- Performance -->
    <section
      class="dashboard-section"
      aria-labelledby="performance-heading"
    >
      <div class="section-heading">
        <div>
          <p class="section-kicker">
            PERFORMANCE
          </p>

          <h2 id="performance-heading">
            Penjualan & transaksi
          </h2>

          <p>
            Pantau performa penjualan tanpa mencampurnya
            dengan operational attention.
          </p>
        </div>
      </div>

      <article class="surface-panel analytics-panel">
        <div class="analytics-toolbar">
          <div>
            <p class="panel-label">
              SALES / TRANSACTION ANALYTICS
            </p>

            <p class="panel-caption">
              Periode berjalan
            </p>
          </div>

          <div class="period-selector">
            <button
              type="button"
              class="period-button period-button--active"
              aria-pressed="true"
            >
              7 hari
            </button>

            <button
              type="button"
              class="period-button"
              aria-pressed="false"
            >
              30 hari
            </button>
          </div>
        </div>

        <div
          class="analytics-placeholder"
          role="img"
          aria-label="Area grafik penjualan dan transaksi"
        >
          <div class="chart-grid" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
          </div>

          <div class="chart-empty">
            <div class="chart-icon" aria-hidden="true">
              ↗
            </div>

            <p>
              Data penjualan belum tersedia
            </p>

            <span>
              Grafik akan muncul setelah data transaksi
              tersedia.
            </span>
          </div>
        </div>
      </article>
    </section>

    <!-- Operational Attention -->
    <section
      class="dashboard-section"
      aria-labelledby="attention-heading"
    >
      <div class="section-heading section-heading--attention">
        <div>
          <p class="section-kicker section-kicker--warning">
            OPERATIONAL ATTENTION
          </p>

          <h2 id="attention-heading">
            Perlu perhatian
          </h2>

          <p>
            Kondisi stok yang membutuhkan tindakan operasional.
          </p>
        </div>

        <span
          v-if="!stockAlertLoading"
          class="count-badge"
          :class="{
            'count-badge--danger': hasStockAlerts,
            'count-badge--success': !hasStockAlerts,
          }"
          aria-label="Jumlah alert stok"
        >
          {{ stockAlertCount }} alert
        </span>
      </div>

      <article class="surface-panel attention-panel">
        <!-- Loading -->
        <div
          v-if="stockAlertLoading"
          class="alert-loading"
          aria-live="polite"
          aria-label="Memuat notifikasi stok"
        >
          <div class="skeleton skeleton--row" />
          <div class="skeleton skeleton--row" />
          <div class="skeleton skeleton--row" />
        </div>

        <!-- Error -->
        <div
          v-else-if="stockAlertError"
          class="state-message state-message--error"
          role="alert"
        >
          <div class="state-message__icon">
            !
          </div>

          <div class="state-message__content">
            <h3>
              Notifikasi stok tidak dapat dimuat
            </h3>

            <p>
              {{ stockAlertError }}
              Tidak ada perubahan pada stok dari
              proses ini.
            </p>

            <button
              type="button"
              class="button button--primary"
              @click="loadStockAlerts"
            >
              Coba Lagi
            </button>
          </div>
        </div>

        <!-- Empty -->
        <div
          v-else-if="!hasStockAlerts"
          class="state-message state-message--success"
          role="status"
        >
          <div class="state-message__icon">
            ✓
          </div>

          <div class="state-message__content">
            <h3>
              Stok berada dalam kondisi normal
            </h3>

            <p>
              Tidak ada produk yang berada di bawah
              batas minimum atau kehabisan stok.
            </p>
          </div>
        </div>

        <!-- Alerts -->
        <div
          v-else
          class="alert-groups"
        >
          <!-- Out of stock -->
          <section
            v-if="outOfStockAlerts.length > 0"
            aria-labelledby="out-of-stock-heading"
          >
            <div class="alert-group-heading">
              <div>
                <h3 id="out-of-stock-heading">
                  Out of Stock
                </h3>

                <p>
                  Produk tanpa stok tersedia.
                </p>
              </div>

              <span class="semantic-badge semantic-badge--danger">
                {{ outOfStockAlerts.length }} produk
              </span>
            </div>

            <div class="alert-table">
              <div class="alert-table__header">
                <span>Produk</span>
                <span>SKU</span>
                <span class="numeric-column">
                  Stok
                </span>
                <span class="numeric-column">
                  Minimum
                </span>
              </div>

              <article
                v-for="alert in outOfStockAlerts"
                :key="alert.product_id"
                class="alert-row"
              >
                <div class="product-cell">
                  <strong>
                    {{ alert.name }}
                  </strong>

                  <span>
                    Produk membutuhkan pengadaan.
                  </span>
                </div>

                <span class="metadata">
                  {{ alert.sku }}
                </span>

                <strong class="numeric-column stock-danger">
                  {{ formatNumber(alert.stock) }}
                </strong>

                <span class="numeric-column">
                  {{ formatNumber(alert.minimum_stock) }}
                </span>
              </article>
            </div>
          </section>

          <!-- Low stock -->
          <section
            v-if="lowStockAlerts.length > 0"
            aria-labelledby="low-stock-heading"
          >
            <div class="alert-group-heading">
              <div>
                <h3 id="low-stock-heading">
                  Low Stock
                </h3>

                <p>
                  Produk mendekati batas minimum.
                </p>
              </div>

              <span class="semantic-badge semantic-badge--warning">
                {{ lowStockAlerts.length }} produk
              </span>
            </div>

            <div class="alert-table">
              <div class="alert-table__header">
                <span>Produk</span>
                <span>SKU</span>
                <span class="numeric-column">
                  Stok
                </span>
                <span class="numeric-column">
                  Minimum
                </span>
              </div>

              <article
                v-for="alert in lowStockAlerts"
                :key="alert.product_id"
                class="alert-row"
              >
                <div class="product-cell">
                  <strong>
                    {{ alert.name }}
                  </strong>

                  <span>
                    Periksa kebutuhan pengadaan.
                  </span>
                </div>

                <span class="metadata">
                  {{ alert.sku }}
                </span>

                <strong class="numeric-column stock-warning">
                  {{ formatNumber(alert.stock) }}
                </strong>

                <span class="numeric-column">
                  {{ formatNumber(alert.minimum_stock) }}
                </span>
              </article>
            </div>
          </section>
        </div>
      </article>
    </section>

    <!-- Procurement / Payables -->
    <section
      class="dashboard-section"
      aria-labelledby="procurement-heading"
    >
      <div class="section-heading">
        <div>
          <p class="section-kicker">
            PROCUREMENT
          </p>

          <h2 id="procurement-heading">
            Pengadaan & hutang supplier
          </h2>

          <p>
            Ringkasan PO aktif dan kewajiban pembayaran.
          </p>
        </div>
      </div>

      <div class="support-grid">
        <article class="surface-panel support-panel">
          <div class="support-panel__header">
            <div>
              <span class="panel-label">
                ACTIVE PO
              </span>

              <h3>
                Purchase Order
              </h3>
            </div>

            <span class="icon-box" aria-hidden="true">
              PO
            </span>
          </div>

          <div class="support-panel__value">
            —
          </div>

          <p class="support-panel__description">
            Purchase order yang masih berada dalam
            proses pengadaan.
          </p>
        </article>

        <article class="surface-panel support-panel">
          <div class="support-panel__header">
            <div>
              <span class="panel-label">
                PAYABLES
              </span>

              <h3>
                Hutang supplier
              </h3>
            </div>

            <span class="icon-box" aria-hidden="true">
              Rp
            </span>
          </div>

          <div class="support-panel__value">
            —
          </div>

          <p class="support-panel__description">
            Outstanding invoice yang perlu dipantau
            dan dibayarkan.
          </p>
        </article>
      </div>
    </section>

    <!-- Best Selling -->
    <section
      class="dashboard-section dashboard-section--last"
      aria-labelledby="best-selling-heading"
    >
      <div class="section-heading">
        <div>
          <p class="section-kicker">
            SALES
          </p>

          <h2 id="best-selling-heading">
            Produk terlaris
          </h2>

          <p>
            Produk dengan kontribusi penjualan tertinggi.
          </p>
        </div>
      </div>

      <article class="surface-panel best-selling-panel">
        <div class="table-header">
          <span>Produk</span>
          <span>SKU</span>
          <span class="numeric-column">
            Terjual
          </span>
          <span class="numeric-column">
            Penjualan
          </span>
        </div>

        <div class="table-empty">
          <div class="table-empty__icon" aria-hidden="true">
            —
          </div>

          <div>
            <h3>
              Belum ada data produk terlaris
            </h3>

            <p>
              Data akan muncul setelah transaksi penjualan
              tersedia.
            </p>
          </div>
        </div>
      </article>
    </section>
  </main>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  background: #f8faf9;
  color: #17201c;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  line-height: 20px;
}

:global(button),
:global(input),
:global(select) {
  font: inherit;
}

.dashboard-page {
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
  padding: 32px;
  color: #17201c;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 32px;
}

.eyebrow,
.section-kicker {
  margin: 0 0 6px;
  color: #176b4d;
  font-size: 11px;
  font-weight: 700;
  line-height: 16px;
  letter-spacing: 0.08em;
}

.page-header h1 {
  margin: 0;
  color: #12372a;
  font-size: 28px;
  font-weight: 700;
  line-height: 36px;
  letter-spacing: -0.02em;
}

.page-description {
  margin: 6px 0 0;
  color: #6b756f;
  font-size: 14px;
  line-height: 20px;
}

.header-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 6px 10px;
  border: 1px solid #d6ddd9;
  border-radius: 8px;
  background: #fff;
  color: #46514b;
  font-size: 12px;
  font-weight: 500;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: #6b756f;
}

.status-dot--active {
  background: #16834b;
}

.status-dot--warning {
  background: #b7791f;
}

.dashboard-section {
  margin-bottom: 40px;
}

.dashboard-section--last {
  margin-bottom: 0;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 16px;
}

.section-heading h2 {
  margin: 0;
  color: #17201c;
  font-size: 22px;
  font-weight: 600;
  line-height: 30px;
  letter-spacing: -0.015em;
}

.section-heading p:not(.section-kicker) {
  margin: 4px 0 0;
  color: #6b756f;
  font-size: 13px;
  line-height: 18px;
}

.section-kicker--warning {
  color: #b7791f;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.kpi-card {
  min-height: 140px;
  padding: 20px;
  border: 1px solid #d6ddd9;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(18, 55, 42, 0.06);
}

.kpi-card--warning {
  background: #fffdf8;
}

.kpi-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.kpi-label {
  color: #46514b;
  font-size: 13px;
  font-weight: 500;
  line-height: 18px;
}

.kpi-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.kpi-indicator--warning {
  border: 1px solid #e4c995;
  background: #fff4d8;
  color: #8d5b0c;
}

.kpi-value {
  margin: 12px 0 0;
  color: #12372a;
  font-size: 28px;
  font-weight: 700;
  line-height: 34px;
  letter-spacing: -0.02em;
}

.kpi-value--money {
  font-variant-numeric: tabular-nums;
}

.kpi-value--warning {
  color: #8d5b0c;
}

.kpi-context {
  margin: 6px 0 0;
  color: #6b756f;
  font-size: 12px;
  line-height: 16px;
}

.surface-panel {
  border: 1px solid #d6ddd9;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(18, 55, 42, 0.06);
}

.analytics-panel {
  padding: 20px;
}

.analytics-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e6ebe8;
}

.panel-label {
  display: block;
  color: #46514b;
  font-size: 11px;
  font-weight: 700;
  line-height: 16px;
  letter-spacing: 0.06em;
}

.panel-caption {
  margin: 3px 0 0;
  color: #6b756f;
  font-size: 12px;
  line-height: 16px;
}

.period-selector {
  display: inline-flex;
  padding: 3px;
  border: 1px solid #d6ddd9;
  border-radius: 6px;
  background: #f1f4f2;
}

.period-button {
  min-height: 30px;
  padding: 5px 10px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: #6b756f;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
}

.period-button:hover {
  color: #12372a;
}

.period-button--active {
  background: #fff;
  color: #176b4d;
  box-shadow: 0 1px 2px rgba(18, 55, 42, 0.06);
}

.analytics-placeholder {
  position: relative;
  min-height: 310px;
  margin-top: 16px;
  overflow: hidden;
  border: 1px solid #e6ebe8;
  border-radius: 6px;
  background: #f8faf9;
}

.chart-grid {
  position: absolute;
  inset: 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.chart-grid span {
  width: 100%;
  height: 1px;
  background: #e6ebe8;
}

.chart-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 24px;
  text-align: center;
}

.chart-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  margin-bottom: 12px;
  border: 1px solid #c7ded4;
  border-radius: 8px;
  background: #f0f8f5;
  color: #176b4d;
  font-size: 18px;
  font-weight: 600;
}

.chart-empty p {
  margin: 0;
  color: #46514b;
  font-size: 14px;
  font-weight: 600;
}

.chart-empty span {
  max-width: 420px;
  margin-top: 4px;
  color: #6b756f;
  font-size: 13px;
  line-height: 18px;
}

.section-heading--attention {
  align-items: center;
}

.count-badge,
.semantic-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 4px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.count-badge--danger,
.semantic-badge--danger {
  border: 1px solid #e8bdb8;
  background: #fff3f1;
  color: #a52f25;
}

.count-badge--success {
  border: 1px solid #b9d8c9;
  background: #f0f8f5;
  color: #16834b;
}

.semantic-badge--warning {
  border: 1px solid #e4c995;
  background: #fff8e8;
  color: #8d5b0c;
}

.attention-panel {
  overflow: hidden;
}

.alert-loading {
  padding: 20px;
}

.skeleton {
  position: relative;
  overflow: hidden;
  background: #f1f4f2;
}

.skeleton::after {
  position: absolute;
  inset: 0;
  content: '';
  transform: translateX(-100%);
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.8),
    transparent
  );
  animation: skeleton-loading 1.4s infinite;
}

.skeleton--kpi-value {
  width: 120px;
  height: 34px;
  margin-top: 12px;
  border-radius: 5px;
}

.skeleton--row {
  height: 64px;
  margin-bottom: 8px;
  border-radius: 6px;
}

.skeleton--row:last-child {
  margin-bottom: 0;
}

@keyframes skeleton-loading {
  100% {
    transform: translateX(100%);
  }
}

.state-message {
  display: flex;
  gap: 14px;
  padding: 20px;
}

.state-message__icon {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 700;
}

.state-message--error {
  background: #fff8f7;
}

.state-message--error .state-message__icon {
  border: 1px solid #e8bdb8;
  background: #fff3f1;
  color: #c0392b;
}

.state-message--success {
  background: #f7fbf9;
}

.state-message--success .state-message__icon {
  border: 1px solid #b9d8c9;
  background: #f0f8f5;
  color: #16834b;
}

.state-message__content {
  min-width: 0;
}

.state-message h3 {
  margin: 0;
  color: #17201c;
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
}

.state-message p {
  max-width: 680px;
  margin: 4px 0 0;
  color: #6b756f;
  font-size: 13px;
  line-height: 18px;
}

.button {
  min-height: 36px;
  margin-top: 14px;
  padding: 7px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition:
    background-color 120ms ease,
    border-color 120ms ease,
    box-shadow 120ms ease;
}

.button--primary {
  border: 1px solid #176b4d;
  background: #176b4d;
  color: #fff;
}

.button--primary:hover {
  border-color: #1f805d;
  background: #1f805d;
}

.alert-groups {
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding: 20px;
}

.alert-group-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.alert-group-heading h3 {
  margin: 0;
  color: #17201c;
  font-size: 18px;
  font-weight: 600;
  line-height: 26px;
}

.alert-group-heading p {
  margin: 3px 0 0;
  color: #6b756f;
  font-size: 12px;
  line-height: 16px;
}

.alert-table {
  overflow: hidden;
  border: 1px solid #e6ebe8;
  border-radius: 6px;
}

.alert-table__header,
.alert-row {
  display: grid;
  grid-template-columns:
    minmax(220px, 2fr)
    minmax(120px, 1fr)
    minmax(80px, 0.7fr)
    minmax(90px, 0.7fr);
  gap: 16px;
  align-items: center;
}

.alert-table__header {
  min-height: 40px;
  padding: 8px 16px;
  border-bottom: 1px solid #d6ddd9;
  background: #f8faf9;
  color: #6b756f;
  font-size: 11px;
  font-weight: 700;
  line-height: 16px;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.alert-row {
  min-height: 70px;
  padding: 12px 16px;
  border-bottom: 1px solid #e6ebe8;
  background: #fff;
}

.alert-row:last-child {
  border-bottom: 0;
}

.product-cell {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.product-cell strong {
  overflow: hidden;
  color: #17201c;
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-cell span,
.metadata {
  overflow: hidden;
  margin-top: 2px;
  color: #6b756f;
  font-size: 12px;
  line-height: 16px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.numeric-column {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.stock-danger {
  color: #c0392b;
}

.stock-warning {
  color: #b7791f;
}

.support-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.support-panel {
  min-height: 190px;
  padding: 20px;
}

.support-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.support-panel__header h3 {
  margin: 3px 0 0;
  color: #17201c;
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
}

.icon-box {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 36px;
  padding: 0 7px;
  border: 1px solid #c7ded4;
  border-radius: 8px;
  background: #f0f8f5;
  color: #176b4d;
  font-size: 11px;
  font-weight: 700;
}

.support-panel__value {
  margin-top: 22px;
  color: #12372a;
  font-size: 28px;
  font-weight: 700;
  line-height: 34px;
}

.support-panel__description {
  max-width: 520px;
  margin: 5px 0 0;
  color: #6b756f;
  font-size: 13px;
  line-height: 18px;
}

.best-selling-panel {
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns:
    minmax(240px, 2fr)
    minmax(120px, 1fr)
    minmax(100px, 0.7fr)
    minmax(120px, 0.9fr);
  gap: 16px;
  padding: 10px 16px;
  border-bottom: 1px solid #d6ddd9;
  background: #f8faf9;
  color: #6b756f;
  font-size: 11px;
  font-weight: 700;
  line-height: 16px;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.table-empty {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 150px;
  padding: 24px;
}

.table-empty__icon {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid #d6ddd9;
  border-radius: 8px;
  color: #6b756f;
  font-weight: 600;
}

.table-empty h3 {
  margin: 0;
  color: #46514b;
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
}

.table-empty p {
  margin: 4px 0 0;
  color: #6b756f;
  font-size: 13px;
  line-height: 18px;
}

button:focus-visible {
  outline: 2px solid #176b4d;
  outline-offset: 2px;
}

@media (max-width: 1199px) {
  .dashboard-page {
    padding: 24px;
  }

  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .support-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .dashboard-page {
    padding: 16px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 16px;
    margin-bottom: 24px;
  }

  .page-header h1 {
    font-size: 28px;
  }

  .header-status {
    width: 100%;
  }

  .dashboard-section {
    margin-bottom: 32px;
  }

  .section-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }

  .section-heading h2 {
    font-size: 20px;
    line-height: 28px;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .kpi-card {
    min-height: 126px;
  }

  .analytics-panel {
    padding: 16px;
  }

  .analytics-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .period-selector {
    width: 100%;
  }

  .period-button {
    flex: 1;
  }

  .analytics-placeholder {
    min-height: 240px;
  }

  .section-heading--attention {
    align-items: flex-start;
  }

  .count-badge {
    align-self: flex-start;
  }

  .alert-groups {
    padding: 16px;
  }

  .alert-group-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .alert-table {
    border: 0;
    border-radius: 0;
  }

  .alert-table__header {
    display: none;
  }

  .alert-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 8px 16px;
    padding: 14px 0;
    border-bottom: 1px solid #e6ebe8;
  }

  .alert-row .product-cell {
    grid-column: 1 / -1;
  }

  .alert-row .metadata {
    grid-column: 1;
  }

  .alert-row .numeric-column {
    grid-column: 2;
  }

  .alert-row .numeric-column:last-child {
    display: none;
  }

  .support-grid {
    gap: 8px;
  }

  .support-panel {
    min-height: 170px;
    padding: 16px;
  }

  .table-header {
    display: none;
  }

  .table-empty {
    min-height: 140px;
    padding: 20px 16px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton::after {
    animation: none;
  }

  .button {
    transition: none;
  }
}
</style>
