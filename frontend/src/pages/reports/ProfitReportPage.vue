<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getProfitReport } from '../../api/reports'
import PeriodFilter from '../../components/reports/PeriodFilter.vue'
import ReportHeader from '../../components/reports/ReportHeader.vue'
import ReportTabs from '../../components/reports/ReportTabs.vue'
import { errorMessage } from '../../services/api'
import { EXPENSE_CATEGORY_LABELS, type ExpenseCategory } from '../../types/expense'
import type { GroupBy, ProfitReport } from '../../types/report'
import { downloadCsv, firstDayOfMonth, formatCurrency, toDateInput } from '../../utils/format'

const period = ref<{ dateFrom: string; dateTo: string; groupBy?: GroupBy }>({
  dateFrom: firstDayOfMonth(),
  dateTo: toDateInput(),
  groupBy: 'month',
})
const report = ref<ProfitReport | null>(null)
const isLoading = ref(false)
const loadError = ref('')

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    report.value = await getProfitReport(period.value)
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat laporan laba.')
  } finally {
    isLoading.value = false
  }
}

function exportCsv() {
  if (!report.value) return
  downloadCsv(
    `laporan-laba-${period.value.dateFrom}-${period.value.dateTo}`,
    ['Periode', 'Penjualan bersih', 'HPP', 'Laba kotor', 'Pengeluaran', 'Laba bersih'],
    report.value.series.map((r) => [r.period, r.sales, r.cogs, r.grossProfit, r.expenses, r.netProfit]),
  )
}

onMounted(load)
</script>

<template>
  <main class="page">
    <div class="page-inner print-area">
      <ReportTabs />
      <ReportHeader
        title="Laporan Laba Dasar"
        :subtitle="`Periode ${period.dateFrom} s/d ${period.dateTo}.`"
        :can-export="Boolean(report)"
        @export="exportCsv"
      />
      <PeriodFilter v-model="period" show-group-by :loading="isLoading" @apply="load" />

      <div v-if="loadError" class="alert alert-error">{{ loadError }}</div>

      <template v-if="report">
        <div class="alert alert-warning">
          <strong>Metode HPP:</strong> {{ report.cogsMethodDescription }}
        </div>

        <section class="card">
          <div class="card-header"><h2 class="card-title">Ringkasan laba rugi</h2></div>
          <div class="table-wrap">
            <table class="table" style="max-width: 640px">
              <tbody>
                <tr><td>Total penjualan</td><td class="num">{{ formatCurrency(report.summary.totalSales) }}</td></tr>
                <tr><td>− Retur penjualan</td><td class="num">{{ formatCurrency(report.summary.salesReturns) }}</td></tr>
                <tr><td class="strong">Penjualan bersih</td><td class="num strong">{{ formatCurrency(report.summary.netSales) }}</td></tr>
                <tr><td>− HPP</td><td class="num">{{ formatCurrency(report.summary.cogs) }}</td></tr>
                <tr><td class="strong">= Laba kotor <span class="muted small">(margin {{ report.summary.grossMargin }}%)</span></td><td class="num strong">{{ formatCurrency(report.summary.grossProfit) }}</td></tr>
                <tr><td>− Pengeluaran</td><td class="num">{{ formatCurrency(report.summary.expenses) }}</td></tr>
              </tbody>
              <tfoot>
                <tr>
                  <td>= Laba bersih</td>
                  <td class="num" :class="report.summary.netProfit < 0 ? 'text-danger' : 'text-success'">{{ formatCurrency(report.summary.netProfit) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </section>

        <div style="display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr))">
          <section class="card">
            <div class="card-header"><h2 class="card-title">Per periode</h2></div>
            <div class="table-wrap">
              <table class="table">
                <thead><tr><th>Periode</th><th class="num">Penjualan</th><th class="num">HPP</th><th class="num">Laba kotor</th><th class="num">Pengeluaran</th><th class="num">Laba bersih</th></tr></thead>
                <tbody>
                  <tr v-for="row in report.series" :key="row.period">
                    <td class="mono">{{ row.period }}</td>
                    <td class="num">{{ formatCurrency(row.sales) }}</td>
                    <td class="num">{{ formatCurrency(row.cogs) }}</td>
                    <td class="num">{{ formatCurrency(row.grossProfit) }}</td>
                    <td class="num">{{ formatCurrency(row.expenses) }}</td>
                    <td class="num strong" :class="{ 'text-danger': row.netProfit < 0 }">{{ formatCurrency(row.netProfit) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
          <section class="card">
            <div class="card-header"><h2 class="card-title">Pengeluaran per kategori</h2></div>
            <div v-if="!report.expensesByCategory.length" class="empty">Tidak ada pengeluaran.</div>
            <div v-else class="table-wrap">
              <table class="table">
                <tbody>
                  <tr v-for="row in report.expensesByCategory" :key="row.category">
                    <td>{{ EXPENSE_CATEGORY_LABELS[row.category as ExpenseCategory] ?? row.category }}</td>
                    <td class="num">{{ formatCurrency(row.amount) }}</td>
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
