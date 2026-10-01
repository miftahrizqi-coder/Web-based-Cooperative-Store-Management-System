<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { getSales } from '../../api/sales'
import PaginationBar from '../../components/ui/PaginationBar.vue'
import { errorMessage } from '../../services/api'
import { useAuth } from '../../stores/auth'
import { PAYMENT_METHOD_LABELS, type Sale, type SaleStatus } from '../../types/sale'
import { formatCurrency, formatDateTime } from '../../utils/format'

const { currentUser } = useAuth()
const isCashier = computed(() => currentUser.value?.role === 'kasir')

const filters = reactive({ search: '', status: '' as SaleStatus | '', dateFrom: '', dateTo: '' })
const sales = ref<Sale[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const isLoading = ref(true)
const loadError = ref('')

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    const result = await getSales({ ...filters, page: page.value, pageSize })
    sales.value = result.items
    total.value = result.total
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat riwayat penjualan.')
  } finally {
    isLoading.value = false
  }
}

function applyFilters() {
  if (page.value !== 1) page.value = 1
  else void load()
}

watch(page, load)
onMounted(load)
</script>

<template>
  <main class="page">
    <div class="page-inner">
      <header class="page-header">
        <div>
          <nav class="breadcrumb" aria-label="Breadcrumb">
            <span>Penjualan</span><span>/</span><span aria-current="page">Riwayat</span>
          </nav>
          <h1 class="page-title">Riwayat Penjualan</h1>
          <p class="page-subtitle">
            {{ isCashier ? 'Transaksi yang Anda buat.' : 'Seluruh transaksi penjualan. Transaksi tidak dihapus, hanya dapat dibatalkan.' }}
          </p>
        </div>
        <div class="header-actions">
          <RouterLink v-if="currentUser?.role !== 'pengurus'" to="/pos" class="btn btn-primary">Transaksi baru</RouterLink>
        </div>
      </header>

      <form class="card card-body" @submit.prevent="applyFilters">
        <div class="filter-bar">
          <label class="field">
            <span class="label">No. invoice</span>
            <input v-model="filters.search" type="search" class="input" placeholder="TRX-…">
          </label>
          <label class="field">
            <span class="label">Status</span>
            <select v-model="filters.status" class="select">
              <option value="">Semua</option>
              <option value="COMPLETED">Selesai</option>
              <option value="CANCELLED">Dibatalkan</option>
            </select>
          </label>
          <label class="field">
            <span class="label">Dari</span>
            <input v-model="filters.dateFrom" type="date" class="input">
          </label>
          <label class="field">
            <span class="label">Sampai</span>
            <input v-model="filters.dateTo" type="date" class="input">
          </label>
          <div class="field"><button type="submit" class="btn btn-secondary">Terapkan</button></div>
        </div>
      </form>

      <section class="card">
        <div v-if="isLoading" class="card-body">
          <div v-for="row in 6" :key="row" class="skeleton" style="height: 18px; margin-bottom: 12px" />
        </div>
        <div v-else-if="loadError" class="card-body"><div class="alert alert-error">{{ loadError }}</div></div>
        <div v-else-if="sales.length === 0" class="empty">
          <strong>Belum ada transaksi</strong>
          Tidak ada transaksi untuk filter ini.
        </div>
        <template v-else>
          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Waktu</th>
                  <th v-if="!isCashier">Kasir</th>
                  <th>Anggota</th>
                  <th>Pembayaran</th>
                  <th class="num">Total</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="sale in sales" :key="sale.id">
                  <td><RouterLink :to="`/sales/${sale.id}`" class="mono strong">{{ sale.invoiceNumber }}</RouterLink></td>
                  <td>{{ formatDateTime(sale.createdAt) }}</td>
                  <td v-if="!isCashier">{{ sale.cashierName || '-' }}</td>
                  <td>{{ sale.memberName ? `${sale.memberNumber} · ${sale.memberName}` : '-' }}</td>
                  <td>{{ PAYMENT_METHOD_LABELS[sale.payment.method] }}</td>
                  <td class="num strong">{{ formatCurrency(sale.total) }}</td>
                  <td>
                    <span class="badge" :class="sale.status === 'COMPLETED' ? 'badge-success' : 'badge-danger'">
                      {{ sale.status === 'COMPLETED' ? 'Selesai' : 'Dibatalkan' }}
                    </span>
                    <span v-if="sale.items.some((i) => i.returnedQuantity > 0)" class="badge badge-warning">Ada retur</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <PaginationBar v-model:page="page" :page-size="pageSize" :total="total" />
        </template>
      </section>
    </div>
  </main>
</template>
