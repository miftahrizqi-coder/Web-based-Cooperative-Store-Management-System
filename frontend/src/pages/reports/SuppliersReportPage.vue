<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getSuppliersReport } from '../../api/reports'
import ReportHeader from '../../components/reports/ReportHeader.vue'
import ReportTabs from '../../components/reports/ReportTabs.vue'
import { errorMessage } from '../../services/api'
import type { SuppliersReport } from '../../types/report'
import { downloadCsv, formatCurrency, formatNumber } from '../../utils/format'

const report = ref<SuppliersReport | null>(null)
const isLoading = ref(true)
const loadError = ref('')

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    report.value = await getSuppliersReport()
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat laporan supplier.')
  } finally {
    isLoading.value = false
  }
}

function exportCsv() {
  if (!report.value) return
  downloadCsv(
    'laporan-supplier',
    ['Kode', 'Supplier', 'Status', 'Barang disuplai', 'Jumlah PO', 'Total pembelian', 'Invoice', 'Total invoice', 'Total pembayaran', 'Retur', 'Sisa hutang'],
    report.value.suppliers.map((s) => [s.supplierCode, s.supplierName, s.status, s.productsSupplied, s.poCount, s.totalPurchases, s.invoiceCount, s.totalInvoiced, s.totalPaid, s.totalReturned, s.outstanding]),
  )
}

onMounted(load)
</script>

<template>
  <main class="page">
    <div class="page-inner print-area">
      <ReportTabs />
      <ReportHeader title="Laporan Supplier" subtitle="Ringkasan pembelian, invoice, pembayaran, dan hutang per supplier (seluruh periode)." :can-export="Boolean(report)" @export="exportCsv" />

      <div v-if="loadError" class="alert alert-error">{{ loadError }}</div>
      <div v-if="isLoading" class="skeleton" style="height: 160px" />

      <template v-if="report">
        <section class="kpi-grid">
          <div class="kpi"><div class="kpi-label">Supplier</div><div class="kpi-value">{{ report.summary.supplierCount }}</div><div class="kpi-context">{{ report.summary.activeSupplierCount }} aktif</div></div>
          <div class="kpi"><div class="kpi-label">Total pembelian</div><div class="kpi-value">{{ formatCurrency(report.summary.totalPurchases) }}</div></div>
          <div class="kpi"><div class="kpi-label">Total invoice</div><div class="kpi-value">{{ formatCurrency(report.summary.totalInvoiced) }}</div></div>
          <div class="kpi"><div class="kpi-label">Total pembayaran</div><div class="kpi-value">{{ formatCurrency(report.summary.totalPaid) }}</div></div>
          <div class="kpi danger"><div class="kpi-label">Sisa hutang</div><div class="kpi-value">{{ formatCurrency(report.summary.outstanding) }}</div></div>
        </section>

        <section class="card">
          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Supplier</th><th>Status</th><th class="num">Barang</th><th class="num">PO</th>
                  <th class="num">Pembelian</th><th class="num">Invoice</th><th class="num">Dibayar</th><th class="num">Retur</th><th class="num">Sisa hutang</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in report.suppliers" :key="row.supplierId">
                  <td>
                    <RouterLink :to="`/suppliers/${row.supplierId}`" class="strong no-print">{{ row.supplierName }}</RouterLink>
                    <div class="mono muted">{{ row.supplierCode }}</div>
                  </td>
                  <td><span class="badge" :class="row.status === 'ACTIVE' ? 'badge-success' : row.status === 'BLACKLISTED' ? 'badge-danger' : 'badge-neutral'">{{ row.status }}</span></td>
                  <td class="num">{{ formatNumber(row.productsSupplied) }}</td>
                  <td class="num">{{ formatNumber(row.poCount) }}</td>
                  <td class="num">{{ formatCurrency(row.totalPurchases) }}</td>
                  <td class="num">{{ formatCurrency(row.totalInvoiced) }}<div class="muted small">{{ row.invoiceCount }} invoice</div></td>
                  <td class="num">{{ formatCurrency(row.totalPaid) }}</td>
                  <td class="num">{{ formatCurrency(row.totalReturned) }}</td>
                  <td class="num strong" :class="{ 'text-danger': row.overdueCount > 0 }">
                    {{ formatCurrency(row.outstanding) }}
                    <div v-if="row.overdueCount" class="small">{{ row.overdueCount }} lewat jatuh tempo</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </div>
  </main>
</template>
