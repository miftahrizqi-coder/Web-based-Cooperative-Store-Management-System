<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getPayablesReport } from '../../api/reports'
import ReportHeader from '../../components/reports/ReportHeader.vue'
import ReportTabs from '../../components/reports/ReportTabs.vue'
import { errorMessage } from '../../services/api'
import type { PayablesReport } from '../../types/report'
import { downloadCsv, formatCurrency, formatDate } from '../../utils/format'

const outstandingOnly = ref(true)
const report = ref<PayablesReport | null>(null)
const isLoading = ref(true)
const loadError = ref('')

const statusLabels: Record<string, string> = {
  UNPAID: 'Belum dibayar',
  PARTIALLY_PAID: 'Dibayar sebagian',
  PAID: 'Lunas',
  OVERDUE: 'Lewat jatuh tempo',
}

function statusClass(status: string) {
  return status === 'PAID' ? 'badge-success' : status === 'OVERDUE' ? 'badge-danger' : status === 'PARTIALLY_PAID' ? 'badge-warning' : 'badge-neutral'
}

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    report.value = await getPayablesReport({ outstandingOnly: outstandingOnly.value })
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat laporan hutang.')
  } finally {
    isLoading.value = false
  }
}

function exportCsv() {
  if (!report.value) return
  downloadCsv(
    'laporan-hutang',
    ['Supplier', 'Invoice', 'Total', 'Dibayar', 'Retur', 'Sisa', 'Jatuh tempo', 'Status'],
    report.value.invoices.map((r) => [r.supplierName ?? r.supplierId, r.invoiceNumber, r.total, r.paid, r.returned, r.outstanding, formatDate(r.dueDate), statusLabels[r.paymentStatus] ?? r.paymentStatus]),
  )
}

onMounted(load)
</script>

<template>
  <main class="page">
    <div class="page-inner print-area">
      <ReportTabs />
      <ReportHeader title="Laporan Hutang Supplier" subtitle="Sisa hutang = total invoice − kredit retur − total pembayaran." :can-export="Boolean(report)" @export="exportCsv" />

      <div class="card card-body no-print">
        <label style="display: flex; gap: 8px; align-items: center">
          <input v-model="outstandingOnly" type="checkbox" @change="load">
          Hanya invoice yang masih memiliki sisa hutang
        </label>
      </div>

      <div v-if="loadError" class="alert alert-error">{{ loadError }}</div>
      <div v-if="isLoading" class="skeleton" style="height: 160px" />

      <template v-if="report">
        <section class="kpi-grid">
          <div class="kpi"><div class="kpi-label">Total invoice</div><div class="kpi-value">{{ formatCurrency(report.summary.total) }}</div><div class="kpi-context">{{ report.summary.invoiceCount }} invoice</div></div>
          <div class="kpi"><div class="kpi-label">Dibayar</div><div class="kpi-value">{{ formatCurrency(report.summary.paid) }}</div></div>
          <div class="kpi"><div class="kpi-label">Kredit retur</div><div class="kpi-value">{{ formatCurrency(report.summary.returned) }}</div></div>
          <div class="kpi danger"><div class="kpi-label">Sisa hutang</div><div class="kpi-value">{{ formatCurrency(report.summary.outstanding) }}</div></div>
          <div class="kpi danger"><div class="kpi-label">Lewat jatuh tempo</div><div class="kpi-value">{{ formatCurrency(report.summary.overdueAmount) }}</div><div class="kpi-context">{{ report.summary.overdueCount }} invoice</div></div>
        </section>

        <section class="card">
          <div class="card-header"><h2 class="card-title">Umur hutang</h2></div>
          <div class="card-body">
            <dl class="dl">
              <div><dt>Belum jatuh tempo</dt><dd>{{ formatCurrency(report.aging.current) }}</dd></div>
              <div><dt>1–30 hari</dt><dd>{{ formatCurrency(report.aging['1-30']) }}</dd></div>
              <div><dt>31–60 hari</dt><dd>{{ formatCurrency(report.aging['31-60']) }}</dd></div>
              <div><dt>61–90 hari</dt><dd>{{ formatCurrency(report.aging['61-90']) }}</dd></div>
              <div><dt>&gt; 90 hari</dt><dd class="text-danger">{{ formatCurrency(report.aging['>90']) }}</dd></div>
            </dl>
          </div>
        </section>

        <section class="card">
          <div v-if="!report.invoices.length" class="empty">Tidak ada hutang.</div>
          <div v-else class="table-wrap">
            <table class="table">
              <thead>
                <tr><th>Supplier</th><th>Invoice</th><th class="num">Total</th><th class="num">Dibayar</th><th class="num">Retur</th><th class="num">Sisa</th><th>Jatuh tempo</th><th>Status</th></tr>
              </thead>
              <tbody>
                <tr v-for="row in report.invoices" :key="row.invoiceId">
                  <td>{{ row.supplierName || row.supplierId }}</td>
                  <td><RouterLink :to="`/supplier-invoices/${row.invoiceId}`" class="mono">{{ row.invoiceNumber }}</RouterLink></td>
                  <td class="num">{{ formatCurrency(row.total) }}</td>
                  <td class="num">{{ formatCurrency(row.paid) }}</td>
                  <td class="num">{{ formatCurrency(row.returned) }}</td>
                  <td class="num strong">{{ formatCurrency(row.outstanding) }}</td>
                  <td>
                    {{ formatDate(row.dueDate) }}
                    <div v-if="row.isOverdue" class="small text-danger">{{ row.daysOverdue }} hari lewat</div>
                  </td>
                  <td><span class="badge" :class="statusClass(row.paymentStatus)">{{ statusLabels[row.paymentStatus] ?? row.paymentStatus }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </div>
  </main>
</template>
