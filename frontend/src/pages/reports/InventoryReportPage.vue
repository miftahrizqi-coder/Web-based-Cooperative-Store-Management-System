<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getCategories } from '../../api/categories'
import { getInventoryReport } from '../../api/reports'
import PeriodFilter from '../../components/reports/PeriodFilter.vue'
import ReportHeader from '../../components/reports/ReportHeader.vue'
import ReportTabs from '../../components/reports/ReportTabs.vue'
import StockBadge from '../../components/ui/StockBadge.vue'
import { errorMessage } from '../../services/api'
import type { Category } from '../../types/category'
import { MOVEMENT_TYPE_LABELS, type StockMovementType } from '../../types/inventory'
import type { InventoryReport } from '../../types/report'
import { downloadCsv, firstDayOfMonth, formatCurrency, formatNumber, formatSigned, toDateInput } from '../../utils/format'

const period = ref({ dateFrom: firstDayOfMonth(), dateTo: toDateInput() })
const categoryId = ref('')
const categories = ref<Category[]>([])
const view = ref<'all' | 'low' | 'out'>('all')
const report = ref<InventoryReport | null>(null)
const isLoading = ref(false)
const loadError = ref('')

const rows = computed(() => {
  if (!report.value) return []
  if (view.value === 'low') return report.value.lowStock
  if (view.value === 'out') return report.value.outOfStock
  return report.value.products
})

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    report.value = await getInventoryReport({ ...period.value, categoryId: categoryId.value || undefined })
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat laporan inventory.')
  } finally {
    isLoading.value = false
  }
}

function exportCsv() {
  downloadCsv(
    `laporan-inventory-${period.value.dateFrom}-${period.value.dateTo}`,
    ['SKU', 'Produk', 'Kategori', 'Stok', 'Minimum', 'Status', 'Nilai stok', 'Stok masuk', 'Stok keluar', 'Adjustment'],
    rows.value.map((r) => [r.sku, r.name, r.categoryName, r.stock, r.minimumStock, r.stockStatus, r.stockValue, r.stockIn, r.stockOut, r.adjustment]),
  )
}

onMounted(async () => {
  try {
    categories.value = await getCategories()
  } catch {
    categories.value = []
  }
  await load()
})
</script>

<template>
  <main class="page">
    <div class="page-inner print-area">
      <ReportTabs />
      <ReportHeader
        title="Laporan Inventory"
        :subtitle="`Stok saat ini dan pergerakan stok ${period.dateFrom} s/d ${period.dateTo}.`"
        :can-export="Boolean(report)"
        @export="exportCsv"
      />
      <PeriodFilter v-model="period" :loading="isLoading" @apply="load">
        <label class="field">
          <span class="label">Kategori</span>
          <select v-model="categoryId" class="select">
            <option value="">Semua</option>
            <option v-for="category in categories" :key="category.id" :value="category.id">{{ category.name }}</option>
          </select>
        </label>
      </PeriodFilter>

      <div v-if="loadError" class="alert alert-error">{{ loadError }}</div>

      <template v-if="report">
        <section class="kpi-grid">
          <div class="kpi"><div class="kpi-label">Produk aktif</div><div class="kpi-value">{{ formatNumber(report.summary.totalProducts) }}</div></div>
          <div class="kpi"><div class="kpi-label">Nilai persediaan</div><div class="kpi-value">{{ formatCurrency(report.summary.totalStockValue) }}</div><div class="kpi-context">Stok × harga beli</div></div>
          <div class="kpi warning"><div class="kpi-label">Hampir habis</div><div class="kpi-value">{{ formatNumber(report.summary.lowStockCount) }}</div></div>
          <div class="kpi danger"><div class="kpi-label">Habis</div><div class="kpi-value">{{ formatNumber(report.summary.outOfStockCount) }}</div></div>
          <div class="kpi"><div class="kpi-label">Stok masuk</div><div class="kpi-value text-success">{{ formatNumber(report.summary.stockIn) }}</div></div>
          <div class="kpi"><div class="kpi-label">Stok keluar</div><div class="kpi-value text-danger">{{ formatNumber(report.summary.stockOut) }}</div></div>
          <div class="kpi"><div class="kpi-label">Stock adjustment</div><div class="kpi-value">{{ formatSigned(report.summary.adjustment) }}</div><div class="kpi-context">Adjustment + opname</div></div>
        </section>

        <section class="card">
          <div class="card-header"><h2 class="card-title">Pergerakan per jenis</h2></div>
          <div class="table-wrap">
            <table class="table">
              <thead><tr><th>Jenis</th><th class="num">Jumlah catatan</th><th class="num">Total qty</th></tr></thead>
              <tbody>
                <tr v-for="row in report.movementsByType" :key="row.type">
                  <td>{{ MOVEMENT_TYPE_LABELS[row.type as StockMovementType] ?? row.type }}</td>
                  <td class="num">{{ formatNumber(row.count) }}</td>
                  <td class="num">{{ formatSigned(row.quantity) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="card">
          <div class="card-header">
            <h2 class="card-title">Stok per produk</h2>
            <div class="tabs no-print" style="border: 0">
              <button type="button" class="tab" :class="{ active: view === 'all' }" @click="view = 'all'">Semua</button>
              <button type="button" class="tab" :class="{ active: view === 'low' }" @click="view = 'low'">Hampir habis</button>
              <button type="button" class="tab" :class="{ active: view === 'out' }" @click="view = 'out'">Habis</button>
            </div>
          </div>
          <div v-if="!rows.length" class="empty">Tidak ada data.</div>
          <div v-else class="table-wrap">
            <table class="table">
              <thead><tr><th>Produk</th><th>Kategori</th><th class="num">Stok</th><th class="num">Min.</th><th>Status</th><th class="num">Nilai</th><th class="num">Masuk</th><th class="num">Keluar</th><th class="num">Adj.</th></tr></thead>
              <tbody>
                <tr v-for="row in rows" :key="row.productId">
                  <td>{{ row.name }}<div class="mono muted">{{ row.sku }}</div></td>
                  <td>{{ row.categoryName }}</td>
                  <td class="num strong">{{ formatNumber(row.stock) }} {{ row.unit }}</td>
                  <td class="num">{{ formatNumber(row.minimumStock) }}</td>
                  <td><StockBadge :status="row.stockStatus" /></td>
                  <td class="num">{{ formatCurrency(row.stockValue) }}</td>
                  <td class="num">{{ formatNumber(row.stockIn) }}</td>
                  <td class="num">{{ formatNumber(row.stockOut) }}</td>
                  <td class="num">{{ formatSigned(row.adjustment) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </div>
  </main>
</template>
