<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { getInventory, getStockMovements } from '../../api/inventory'
import PaginationBar from '../../components/ui/PaginationBar.vue'
import { errorMessage } from '../../services/api'
import {
  MOVEMENT_TYPE_LABELS,
  type InventoryItem,
  type StockMovement,
  type StockMovementType,
} from '../../types/inventory'
import { downloadCsv, formatDateTime, formatNumber, formatSigned } from '../../utils/format'

const route = useRoute()

const filters = reactive({
  productId: typeof route.query.productId === 'string' ? route.query.productId : '',
  type: '' as StockMovementType | '',
  dateFrom: '',
  dateTo: '',
})
const products = ref<InventoryItem[]>([])
const movements = ref<StockMovement[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const isLoading = ref(true)
const loadError = ref('')

const typeOptions = Object.entries(MOVEMENT_TYPE_LABELS) as [StockMovementType, string][]

function referenceLink(movement: StockMovement): string | null {
  switch (movement.referenceType) {
    case 'SALE':
    case 'SALE_CANCEL':
      return movement.referenceId ? `/sales/${movement.referenceId}` : null
    case 'GOODS_RECEIPT':
      return movement.referenceId ? `/goods-receipts/${movement.referenceId}` : null
    case 'SALE_RETURN':
    case 'PURCHASE_RETURN':
      return '/returns'
    default:
      return null
  }
}

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    const result = await getStockMovements({ ...filters, page: page.value, pageSize })
    movements.value = result.items
    total.value = result.total
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat stock movement.')
  } finally {
    isLoading.value = false
  }
}

function applyFilters() {
  if (page.value !== 1) {
    page.value = 1
  } else {
    void load()
  }
}

function exportCsv() {
  downloadCsv(
    'stock-movement',
    ['Waktu', 'SKU', 'Produk', 'Jenis', 'Qty', 'Stok sebelum', 'Stok sesudah', 'Referensi', 'Alasan', 'Oleh'],
    movements.value.map((m) => [
      formatDateTime(m.createdAt), m.sku, m.productName, MOVEMENT_TYPE_LABELS[m.type], m.quantity,
      m.stockBefore, m.stockAfter, m.referenceNumber ?? m.referenceType ?? '', m.reason ?? '', m.createdByName ?? m.createdBy,
    ]),
  )
}

watch(page, load)

onMounted(async () => {
  try {
    products.value = await getInventory(null)
  } catch {
    products.value = []
  }
  await load()
})
</script>

<template>
  <main class="page">
    <div class="page-inner">
      <header class="page-header">
        <div>
          <nav class="breadcrumb" aria-label="Breadcrumb">
            <RouterLink to="/inventory">Inventory</RouterLink><span>/</span><span aria-current="page">Stock Movement</span>
          </nav>
          <h1 class="page-title">Stock Movement</h1>
          <p class="page-subtitle">
            Kartu stok: setiap perubahan stok tercatat dengan jumlah bertanda (+ masuk, − keluar), stok sebelum dan sesudah.
          </p>
        </div>
        <div class="header-actions">
          <button type="button" class="btn btn-secondary" :disabled="movements.length === 0" @click="exportCsv">Ekspor CSV</button>
        </div>
      </header>

      <form class="card card-body" @submit.prevent="applyFilters">
        <div class="filter-bar">
          <label class="field">
            <span class="label">Produk</span>
            <select v-model="filters.productId" class="select">
              <option value="">Semua produk</option>
              <option v-for="product in products" :key="product.productId" :value="product.productId">
                {{ product.sku }} — {{ product.name }}
              </option>
            </select>
          </label>
          <label class="field">
            <span class="label">Jenis</span>
            <select v-model="filters.type" class="select">
              <option value="">Semua jenis</option>
              <option v-for="[value, label] in typeOptions" :key="value" :value="value">{{ label }}</option>
            </select>
          </label>
          <label class="field">
            <span class="label">Dari tanggal</span>
            <input v-model="filters.dateFrom" type="date" class="input">
          </label>
          <label class="field">
            <span class="label">Sampai tanggal</span>
            <input v-model="filters.dateTo" type="date" class="input">
          </label>
          <div class="field">
            <button type="submit" class="btn btn-secondary">Terapkan</button>
          </div>
        </div>
      </form>

      <section class="card">
        <div v-if="isLoading" class="card-body">
          <div v-for="row in 6" :key="row" class="skeleton" style="height: 18px; margin-bottom: 12px" />
        </div>
        <div v-else-if="loadError" class="card-body"><div class="alert alert-error">{{ loadError }}</div></div>
        <div v-else-if="movements.length === 0" class="empty">
          <strong>Belum ada pergerakan stok</strong>
          Tidak ada data untuk filter ini.
        </div>
        <template v-else>
          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Waktu</th>
                  <th>Produk</th>
                  <th>Jenis</th>
                  <th class="num">Qty</th>
                  <th class="num">Sebelum</th>
                  <th class="num">Sesudah</th>
                  <th>Referensi</th>
                  <th>Oleh</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="movement in movements" :key="movement.id">
                  <td class="small">{{ formatDateTime(movement.createdAt) }}</td>
                  <td>
                    <div class="strong">{{ movement.productName }}</div>
                    <div class="mono muted">{{ movement.sku }}</div>
                  </td>
                  <td><span class="badge badge-neutral">{{ MOVEMENT_TYPE_LABELS[movement.type] }}</span></td>
                  <td class="num strong" :class="movement.quantity >= 0 ? 'text-success' : 'text-danger'">
                    {{ formatSigned(movement.quantity) }}
                  </td>
                  <td class="num">{{ formatNumber(movement.stockBefore) }}</td>
                  <td class="num">{{ formatNumber(movement.stockAfter) }}</td>
                  <td>
                    <RouterLink v-if="referenceLink(movement)" :to="referenceLink(movement)!" class="mono">
                      {{ movement.referenceNumber || movement.referenceType }}
                    </RouterLink>
                    <span v-else class="mono">{{ movement.referenceNumber || movement.referenceType || '-' }}</span>
                    <div v-if="movement.reason" class="muted small">{{ movement.reason }}</div>
                  </td>
                  <td class="small">{{ movement.createdByName || '-' }}</td>
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
