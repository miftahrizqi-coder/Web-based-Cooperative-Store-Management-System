<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getPurchasesReport } from '../../api/reports'
import { getSuppliers } from '../../api/suppliers'
import PeriodFilter from '../../components/reports/PeriodFilter.vue'
import ReportHeader from '../../components/reports/ReportHeader.vue'
import ReportTabs from '../../components/reports/ReportTabs.vue'
import { errorMessage } from '../../services/api'
import { useAuth } from '../../stores/auth'
import type { GroupBy, PurchasesReport } from '../../types/report'
import type { Supplier } from '../../types/supplier'
import { downloadCsv, formatCurrency, formatNumber, toDateInput } from '../../utils/format'

const { token } = useAuth()
const now = new Date()
const period = ref<{ dateFrom: string; dateTo: string; groupBy?: GroupBy }>({
  dateFrom: toDateInput(new Date(now.getFullYear(), 0, 1)),
  dateTo: toDateInput(),
  groupBy: 'month',
})
const supplierId = ref('')
const suppliers = ref<Supplier[]>([])
const report = ref<PurchasesReport | null>(null)
const isLoading = ref(false)
const loadError = ref('')

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    report.value = await getPurchasesReport({ ...period.value, supplierId: supplierId.value || undefined })
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat laporan pembelian.')
  } finally {
    isLoading.value = false
  }
}

function exportCsv() {
  if (!report.value) return
  downloadCsv(
    `laporan-pembelian-${period.value.dateFrom}-${period.value.dateTo}`,
    ['Supplier', 'Jumlah PO', 'Nilai PO', 'Jumlah pembelian', 'Jumlah barang', 'Total pembelian'],
    report.value.bySupplier.map((r) => [r.supplierName, r.poCount, r.poValue, r.purchaseCount, r.itemsQuantity, r.totalPurchases]),
  )
}

onMounted(async () => {
  try {
    suppliers.value = await getSuppliers(token.value ?? '')
  } catch {
    suppliers.value = []
  }
  await load()
})
</script>

<template>
  <main class="page">
    <div class="page-inner print-area">
      <ReportTabs />
      <ReportHeader
        title="Laporan Pembelian"
        :subtitle="`Periode ${period.dateFrom} s/d ${period.dateTo}. Pembelian dihitung dari barang yang diterima baik.`"
        :can-export="Boolean(report)"
        @export="exportCsv"
      />
      <PeriodFilter v-model="period" show-group-by :loading="isLoading" @apply="load">
        <label class="field">
          <span class="label">Supplier</span>
          <select v-model="supplierId" class="select">
            <option value="">Semua</option>
            <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">{{ supplier.name }}</option>
          </select>
        </label>
      </PeriodFilter>

      <div v-if="loadError" class="alert alert-error">{{ loadError }}</div>

      <template v-if="report">
        <section class="kpi-grid">
          <div class="kpi"><div class="kpi-label">Jumlah PO</div><div class="kpi-value">{{ formatNumber(report.summary.poCount) }}</div><div class="kpi-context">{{ report.summary.cancelledPoCount }} dibatalkan</div></div>
          <div class="kpi"><div class="kpi-label">Jumlah pembelian</div><div class="kpi-value">{{ formatNumber(report.summary.purchaseCount) }}</div></div>
          <div class="kpi"><div class="kpi-label">Jumlah barang</div><div class="kpi-value">{{ formatNumber(report.summary.itemsQuantity) }}</div></div>
          <div class="kpi"><div class="kpi-label">Total pembelian</div><div class="kpi-value">{{ formatCurrency(report.summary.totalPurchases) }}</div></div>
          <div class="kpi"><div class="kpi-label">Retur pembelian</div><div class="kpi-value">{{ formatCurrency(report.summary.purchaseReturns) }}</div></div>
        </section>

        <section class="card">
          <div class="card-header"><h2 class="card-title">Per supplier</h2></div>
          <div v-if="!report.bySupplier.length" class="empty">Tidak ada data.</div>
          <div v-else class="table-wrap">
            <table class="table">
              <thead><tr><th>Supplier</th><th class="num">PO</th><th class="num">Nilai PO</th><th class="num">Pembelian</th><th class="num">Barang</th><th class="num">Total pembelian</th></tr></thead>
              <tbody>
                <tr v-for="row in report.bySupplier" :key="row.supplierId">
                  <td>{{ row.supplierName }}</td>
                  <td class="num">{{ formatNumber(row.poCount) }}</td>
                  <td class="num">{{ formatCurrency(row.poValue) }}</td>
                  <td class="num">{{ formatNumber(row.purchaseCount) }}</td>
                  <td class="num">{{ formatNumber(row.itemsQuantity) }}</td>
                  <td class="num strong">{{ formatCurrency(row.totalPurchases) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="card">
          <div class="card-header"><h2 class="card-title">Pembelian berdasarkan periode</h2></div>
          <div class="table-wrap">
            <table class="table">
              <thead><tr><th>Periode</th><th class="num">Pembelian</th><th class="num">Barang</th><th class="num">Total</th></tr></thead>
              <tbody>
                <tr v-for="row in report.series" :key="row.period">
                  <td class="mono">{{ row.period }}</td>
                  <td class="num">{{ formatNumber(row.purchaseCount) }}</td>
                  <td class="num">{{ formatNumber(row.itemsQuantity) }}</td>
                  <td class="num">{{ formatCurrency(row.totalPurchases) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </div>
  </main>
</template>
