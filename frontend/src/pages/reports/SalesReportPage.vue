<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { getCategories } from '../../api/categories'
import { getMembers } from '../../api/members'
import { getProducts } from '../../api/products'
import { getSalesReport } from '../../api/reports'
import { getUsers } from '../../api/users'
import PeriodFilter from '../../components/reports/PeriodFilter.vue'
import ReportHeader from '../../components/reports/ReportHeader.vue'
import ReportTabs from '../../components/reports/ReportTabs.vue'
import { errorMessage } from '../../services/api'
import { useAuth } from '../../stores/auth'
import type { Category } from '../../types/category'
import type { Member } from '../../types/member'
import type { Product } from '../../types/product'
import type { GroupBy, SalesReport } from '../../types/report'
import { PAYMENT_METHOD_LABELS, type PaymentMethod } from '../../types/sale'
import type { User } from '../../types/user'
import { downloadCsv, firstDayOfMonth, formatCurrency, formatNumber, toDateInput } from '../../utils/format'

const { hasRole } = useAuth()

const period = ref<{ dateFrom: string; dateTo: string; groupBy?: GroupBy }>({
  dateFrom: firstDayOfMonth(),
  dateTo: toDateInput(),
  groupBy: 'day',
})
const extra = reactive({ cashierId: '', productId: '', categoryId: '', memberId: '' })
const cashiers = ref<User[]>([])
const products = ref<Product[]>([])
const categories = ref<Category[]>([])
const members = ref<Member[]>([])

const report = ref<SalesReport | null>(null)
const isLoading = ref(false)
const loadError = ref('')

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    report.value = await getSalesReport({ ...period.value, ...extra })
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat laporan penjualan.')
  } finally {
    isLoading.value = false
  }
}

function exportCsv() {
  if (!report.value) return
  downloadCsv(
    `laporan-penjualan-${period.value.dateFrom}-${period.value.dateTo}`,
    ['Periode', 'Jumlah transaksi', 'Barang terjual', 'Penjualan kotor', 'Diskon', 'Penjualan bersih'],
    report.value.series.map((row) => [row.period, row.transactionCount, row.itemsSold, row.grossSales, row.discount, row.netSales]),
  )
}

onMounted(async () => {
  const [productList, categoryList, memberList] = await Promise.allSettled([
    getProducts(null, {}),
    getCategories(),
    getMembers(),
  ])
  if (productList.status === 'fulfilled') products.value = productList.value
  if (categoryList.status === 'fulfilled') categories.value = categoryList.value
  if (memberList.status === 'fulfilled') members.value = memberList.value
  // Daftar kasir hanya bisa diambil admin (endpoint /api/users).
  if (hasRole('admin')) {
    try {
      cashiers.value = (await getUsers()).filter((u) => u.role === 'kasir' || u.role === 'admin')
    } catch {
      cashiers.value = []
    }
  }
  await load()
})
</script>

<template>
  <main class="page">
    <div class="page-inner print-area">
      <ReportTabs />
      <ReportHeader
        title="Laporan Penjualan"
        :subtitle="`Periode ${period.dateFrom} s/d ${period.dateTo}. Transaksi dibatalkan tidak dihitung; retur mengurangi pendapatan.`"
        :can-export="Boolean(report)"
        @export="exportCsv"
      />

      <PeriodFilter v-model="period" show-group-by :loading="isLoading" @apply="load">
        <label v-if="cashiers.length" class="field">
          <span class="label">Kasir</span>
          <select v-model="extra.cashierId" class="select">
            <option value="">Semua</option>
            <option v-for="user in cashiers" :key="user.id" :value="user.id">{{ user.name }}</option>
          </select>
        </label>
        <label class="field">
          <span class="label">Kategori</span>
          <select v-model="extra.categoryId" class="select">
            <option value="">Semua</option>
            <option v-for="category in categories" :key="category.id" :value="category.id">{{ category.name }}</option>
          </select>
        </label>
        <label class="field">
          <span class="label">Produk</span>
          <select v-model="extra.productId" class="select">
            <option value="">Semua</option>
            <option v-for="product in products" :key="product.id" :value="product.id">{{ product.sku }} — {{ product.name }}</option>
          </select>
        </label>
        <label class="field">
          <span class="label">Anggota</span>
          <select v-model="extra.memberId" class="select">
            <option value="">Semua</option>
            <option v-for="member in members" :key="member.id" :value="member.id">{{ member.memberNumber }} — {{ member.name }}</option>
          </select>
        </label>
      </PeriodFilter>

      <div v-if="loadError" class="alert alert-error">{{ loadError }}</div>

      <template v-if="report">
        <section class="kpi-grid">
          <div class="kpi"><div class="kpi-label">Jumlah transaksi</div><div class="kpi-value">{{ formatNumber(report.summary.transactionCount) }}</div><div class="kpi-context">{{ report.summary.cancelledCount }} dibatalkan</div></div>
          <div class="kpi"><div class="kpi-label">Barang terjual</div><div class="kpi-value">{{ formatNumber(report.summary.itemsSold) }}</div><div class="kpi-context">{{ formatNumber(report.summary.returnedItems) }} diretur</div></div>
          <div class="kpi"><div class="kpi-label">Total penjualan</div><div class="kpi-value">{{ formatCurrency(report.summary.grossSales) }}</div><div class="kpi-context">Sebelum diskon</div></div>
          <div class="kpi"><div class="kpi-label">Diskon</div><div class="kpi-value">{{ formatCurrency(report.summary.discount) }}</div></div>
          <div class="kpi"><div class="kpi-label">Retur penjualan</div><div class="kpi-value">{{ formatCurrency(report.summary.returns) }}</div></div>
          <div class="kpi"><div class="kpi-label">Pendapatan</div><div class="kpi-value" style="color: var(--c-primary)">{{ formatCurrency(report.summary.revenue) }}</div><div class="kpi-context">Rata-rata {{ formatCurrency(report.summary.averageTransaction) }}/transaksi</div></div>
        </section>

        <section class="card">
          <div class="card-header"><h2 class="card-title">Per periode</h2></div>
          <div class="table-wrap">
            <table class="table">
              <thead><tr><th>Periode</th><th class="num">Transaksi</th><th class="num">Barang</th><th class="num">Kotor</th><th class="num">Diskon</th><th class="num">Bersih</th></tr></thead>
              <tbody>
                <tr v-for="row in report.series" :key="row.period">
                  <td class="mono">{{ row.period }}</td>
                  <td class="num">{{ formatNumber(row.transactionCount) }}</td>
                  <td class="num">{{ formatNumber(row.itemsSold) }}</td>
                  <td class="num">{{ formatCurrency(row.grossSales) }}</td>
                  <td class="num">{{ formatCurrency(row.discount) }}</td>
                  <td class="num strong">{{ formatCurrency(row.netSales) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td>Total</td>
                  <td class="num">{{ formatNumber(report.summary.transactionCount) }}</td>
                  <td class="num">{{ formatNumber(report.summary.itemsSold) }}</td>
                  <td class="num">{{ formatCurrency(report.summary.grossSales) }}</td>
                  <td class="num">{{ formatCurrency(report.summary.discount) }}</td>
                  <td class="num">{{ formatCurrency(report.summary.totalSales) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </section>

        <div style="display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr))">
          <section class="card">
            <div class="card-header"><h2 class="card-title">Per produk</h2></div>
            <div v-if="!report.byProduct.length" class="empty">Tidak ada data.</div>
            <div v-else class="table-wrap">
              <table class="table">
                <thead><tr><th>Produk</th><th class="num">Qty</th><th class="num">Penjualan</th></tr></thead>
                <tbody>
                  <tr v-for="row in report.byProduct" :key="row.productId">
                    <td>{{ row.name }}<div class="mono muted">{{ row.sku }}</div></td>
                    <td class="num">{{ formatNumber(row.quantity) }}</td>
                    <td class="num">{{ formatCurrency(row.netSales) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
          <section class="card">
            <div class="card-header"><h2 class="card-title">Per kasir</h2></div>
            <div v-if="!report.byCashier.length" class="empty">Tidak ada data.</div>
            <div v-else class="table-wrap">
              <table class="table">
                <thead><tr><th>Kasir</th><th class="num">Transaksi</th><th class="num">Penjualan</th></tr></thead>
                <tbody>
                  <tr v-for="row in report.byCashier" :key="row.cashierId">
                    <td>{{ row.cashierName }}</td>
                    <td class="num">{{ formatNumber(row.transactionCount) }}</td>
                    <td class="num">{{ formatCurrency(row.netSales) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="card-header" style="border-top: 1px solid var(--c-border-soft)"><h2 class="card-title">Per metode pembayaran</h2></div>
            <div class="table-wrap">
              <table class="table">
                <tbody>
                  <tr v-for="row in report.byPaymentMethod" :key="row.method">
                    <td>{{ PAYMENT_METHOD_LABELS[row.method as PaymentMethod] ?? row.method }}</td>
                    <td class="num">{{ formatNumber(row.transactionCount) }} trx</td>
                    <td class="num">{{ formatCurrency(row.netSales) }}</td>
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
