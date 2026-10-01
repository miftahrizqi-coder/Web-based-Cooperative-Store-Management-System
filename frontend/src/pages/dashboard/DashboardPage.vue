<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getDashboard } from '../../api/reports'
import { errorMessage } from '../../services/api'
import { useAuth } from '../../stores/auth'
import type { DashboardData } from '../../types/report'
import { formatCurrency, formatDate, formatNumber } from '../../utils/format'

const { currentUser } = useAuth()
const data = ref<DashboardData | null>(null)
const isLoading = ref(true)
const loadError = ref('')

const isCashier = computed(() => currentUser.value?.role === 'kasir')
const isAdmin = computed(() => currentUser.value?.role === 'admin')

const chartMax = computed(() => Math.max(1, ...(data.value?.salesChart ?? []).map((d) => d.total)))

function shortDay(value: string): string {
  const date = new Date(`${value}T00:00:00`)
  return new Intl.DateTimeFormat('id-ID', { day: '2-digit', month: 'short' }).format(date)
}

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    data.value = await getDashboard()
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat dashboard.')
  } finally {
    isLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="page">
    <div class="page-inner">
      <header class="page-header">
        <div>
          <h1 class="page-title">Dashboard Toko Koperasi</h1>
          <p class="page-subtitle">
            {{ isCashier ? 'Ringkasan penjualan Anda hari ini.' : 'Kondisi penjualan, stok, pengadaan, dan hutang supplier.' }}
            <span v-if="data"> · {{ formatDate(data.date) }}</span>
          </p>
        </div>
        <div class="header-actions">
          <RouterLink v-if="isCashier || isAdmin" to="/pos" class="btn btn-primary">Buka POS</RouterLink>
          <button type="button" class="btn btn-secondary" :disabled="isLoading" @click="load">Muat ulang</button>
        </div>
      </header>

      <div v-if="loadError" class="alert alert-error" role="alert">
        {{ loadError }}
        <button type="button" class="btn btn-ghost btn-sm" @click="load">Coba lagi</button>
      </div>

      <div v-if="isLoading && !data" class="kpi-grid">
        <div v-for="index in 8" :key="index" class="kpi"><div class="skeleton" style="height: 48px" /></div>
      </div>

      <template v-if="data">
        <section class="kpi-grid" aria-label="Ringkasan">
          <div class="kpi">
            <div class="kpi-label">Penjualan hari ini</div>
            <div class="kpi-value">{{ formatCurrency(data.todaySales) }}</div>
            <div class="kpi-context">{{ isCashier ? 'Transaksi Anda' : 'Semua kasir' }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-label">Transaksi hari ini</div>
            <div class="kpi-value">{{ formatNumber(data.todayTransactions) }}</div>
            <div class="kpi-context">Status selesai</div>
          </div>
          <template v-if="!isCashier">
            <RouterLink :to="isAdmin ? '/products' : '/inventory'" class="kpi" style="text-decoration: none; color: inherit">
              <div class="kpi-label">Total produk</div>
              <div class="kpi-value">{{ formatNumber(data.totalProducts) }}</div>
              <div class="kpi-context">Produk aktif</div>
            </RouterLink>
            <RouterLink to="/members" class="kpi" style="text-decoration: none; color: inherit">
              <div class="kpi-label">Total anggota</div>
              <div class="kpi-value">{{ formatNumber(data.totalMembers) }}</div>
              <div class="kpi-context">Anggota aktif</div>
            </RouterLink>
            <RouterLink to="/inventory" class="kpi" :class="{ warning: (data.lowStockCount ?? 0) > 0 }" style="text-decoration: none; color: inherit">
              <div class="kpi-label">Stok menipis</div>
              <div class="kpi-value">{{ formatNumber(data.lowStockCount) }}</div>
              <div class="kpi-context">≤ stok minimum</div>
            </RouterLink>
            <RouterLink to="/inventory" class="kpi" :class="{ danger: (data.outOfStockCount ?? 0) > 0 }" style="text-decoration: none; color: inherit">
              <div class="kpi-label">Produk habis</div>
              <div class="kpi-value">{{ formatNumber(data.outOfStockCount) }}</div>
              <div class="kpi-context">Stok 0</div>
            </RouterLink>
            <RouterLink to="/purchase-orders" class="kpi" style="text-decoration: none; color: inherit">
              <div class="kpi-label">Purchase Order aktif</div>
              <div class="kpi-value">{{ formatNumber(data.activePurchaseOrders) }}</div>
              <div class="kpi-context">{{ data.pendingApprovalPurchaseOrders }} menunggu approval</div>
            </RouterLink>
            <RouterLink to="/supplier-payables" class="kpi" style="text-decoration: none; color: inherit">
              <div class="kpi-label">Hutang supplier</div>
              <div class="kpi-value">{{ formatCurrency(data.supplierPayables) }}</div>
              <div class="kpi-context">Sisa belum dibayar</div>
            </RouterLink>
            <RouterLink to="/reports/payables" class="kpi" :class="{ danger: (data.overdueInvoiceCount ?? 0) > 0 }" style="text-decoration: none; color: inherit">
              <div class="kpi-label">Invoice jatuh tempo</div>
              <div class="kpi-value">{{ formatNumber(data.dueInvoiceCount) }}</div>
              <div class="kpi-context">{{ data.overdueInvoiceCount }} lewat jatuh tempo · ≤ 7 hari</div>
            </RouterLink>
            <RouterLink to="/expenses" class="kpi" style="text-decoration: none; color: inherit">
              <div class="kpi-label">Pengeluaran bulan ini</div>
              <div class="kpi-value">{{ formatCurrency(data.monthExpenses) }}</div>
              <div class="kpi-context">Penjualan bulan ini {{ formatCurrency(data.monthSales) }}</div>
            </RouterLink>
          </template>
        </section>

        <div v-if="!isCashier && ((data.pendingReturns ?? 0) > 0 || (data.pendingReceipts ?? 0) > 0)" class="alert alert-info">
          <RouterLink v-if="(data.pendingReturns ?? 0) > 0" to="/returns">{{ data.pendingReturns }} retur menunggu approval</RouterLink>
          <span v-if="(data.pendingReturns ?? 0) > 0 && (data.pendingReceipts ?? 0) > 0"> · </span>
          <RouterLink v-if="(data.pendingReceipts ?? 0) > 0" to="/goods-receipts">{{ data.pendingReceipts }} PO menunggu penerimaan barang</RouterLink>
        </div>

        <section class="card">
          <div class="card-header">
            <div>
              <h2 class="card-title">Grafik penjualan 14 hari</h2>
              <p class="card-subtitle">Total penjualan harian (transaksi selesai)</p>
            </div>
          </div>
          <div class="card-body">
            <div class="bar-chart" role="img" aria-label="Grafik batang penjualan harian">
              <div v-for="day in data.salesChart" :key="day.date" class="bar-col" :title="`${shortDay(day.date)}: ${formatCurrency(day.total)} (${day.transactions} transaksi)`">
                <div class="bar" :style="{ height: `${Math.round((day.total / chartMax) * 100)}%` }" />
                <span class="bar-label">{{ shortDay(day.date) }}</span>
              </div>
            </div>
          </div>
        </section>

        <div v-if="!isCashier" style="display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr))">
          <section class="card">
            <div class="card-header">
              <h2 class="card-title">Stok menipis & habis</h2>
              <RouterLink to="/reports/inventory" class="btn btn-ghost btn-sm">Laporan</RouterLink>
            </div>
            <div v-if="!data.lowStockProducts?.length && !data.outOfStockProducts?.length" class="empty">Semua stok aman.</div>
            <div v-else class="table-wrap">
              <table class="table">
                <thead><tr><th>Produk</th><th class="num">Stok</th><th class="num">Min.</th></tr></thead>
                <tbody>
                  <tr v-for="item in data.outOfStockProducts" :key="`out-${item.productId}`">
                    <td>{{ item.name }} <span class="badge badge-danger">Habis</span></td>
                    <td class="num text-danger">{{ formatNumber(item.stock) }}</td>
                    <td class="num">{{ formatNumber(item.minimumStock) }}</td>
                  </tr>
                  <tr v-for="item in data.lowStockProducts" :key="`low-${item.productId}`">
                    <td>{{ item.name }}</td>
                    <td class="num" style="color: var(--c-warning)">{{ formatNumber(item.stock) }} {{ item.unit }}</td>
                    <td class="num">{{ formatNumber(item.minimumStock) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section class="card">
            <div class="card-header">
              <h2 class="card-title">Produk terlaris bulan ini</h2>
              <RouterLink to="/reports/sales" class="btn btn-ghost btn-sm">Laporan</RouterLink>
            </div>
            <div v-if="!data.topProducts?.length" class="empty">Belum ada penjualan bulan ini.</div>
            <div v-else class="table-wrap">
              <table class="table">
                <thead><tr><th>Produk</th><th class="num">Terjual</th><th class="num">Nilai</th></tr></thead>
                <tbody>
                  <tr v-for="item in data.topProducts" :key="item.productId">
                    <td>{{ item.name }}<div class="mono muted">{{ item.sku }}</div></td>
                    <td class="num">{{ formatNumber(item.quantity) }}</td>
                    <td class="num">{{ formatCurrency(item.total) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section class="card">
            <div class="card-header">
              <h2 class="card-title">Invoice jatuh tempo</h2>
              <RouterLink to="/supplier-payables" class="btn btn-ghost btn-sm">Hutang</RouterLink>
            </div>
            <div v-if="!data.dueInvoices?.length" class="empty">Tidak ada invoice jatuh tempo dalam 7 hari.</div>
            <div v-else class="table-wrap">
              <table class="table">
                <thead><tr><th>Invoice</th><th>Jatuh tempo</th><th class="num">Sisa</th></tr></thead>
                <tbody>
                  <tr v-for="invoice in data.dueInvoices" :key="invoice.invoiceId">
                    <td>
                      <RouterLink :to="`/supplier-invoices/${invoice.invoiceId}`" class="mono">{{ invoice.invoiceNumber }}</RouterLink>
                      <div class="muted small">{{ invoice.supplierName }}</div>
                    </td>
                    <td>
                      {{ formatDate(invoice.dueDate) }}
                      <span v-if="invoice.isOverdue" class="badge badge-danger">Lewat</span>
                    </td>
                    <td class="num">{{ formatCurrency(invoice.outstanding) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </template>
    </div>
  </main>
</template>
