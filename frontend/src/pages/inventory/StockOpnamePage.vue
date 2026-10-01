<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { createStockOpname, getInventory, getStockOpnames } from '../../api/inventory'
import PaginationBar from '../../components/ui/PaginationBar.vue'
import { errorMessage } from '../../services/api'
import type { InventoryItem, StockOpname } from '../../types/inventory'
import { formatDateTime, formatNumber, formatSigned } from '../../utils/format'

/**
 * Alur PRD §21: ambil stok sistem -> hitung stok fisik -> bandingkan ->
 * jika selisih, adjustment otomatis (movement STOCK_OPNAME) dengan alasan.
 */
interface CountRow {
  productId: string
  sku: string
  name: string
  unit: string
  systemStock: number
  physicalStock: number | null
  reason: string
}

const inventory = ref<InventoryItem[]>([])
const rows = reactive<Record<string, CountRow>>({})
const search = ref('')
const onlyCounted = ref(false)
const notes = ref('')
const isLoading = ref(true)
const saving = ref(false)
const loadError = ref('')
const formError = ref('')
const result = ref<StockOpname | null>(null)

const history = ref<StockOpname[]>([])
const historyTotal = ref(0)
const historyPage = ref(1)
const expanded = ref<string | null>(null)

// v-model.number menghasilkan '' saat input dikosongkan.
function isCounted(row: CountRow): boolean {
  return typeof row.physicalStock === 'number' && Number.isFinite(row.physicalStock)
}

const visibleRows = computed(() => {
  const term = search.value.trim().toLowerCase()
  return Object.values(rows).filter((row) => {
    if (onlyCounted.value && !isCounted(row)) return false
    if (!term) return true
    return row.name.toLowerCase().includes(term) || row.sku.toLowerCase().includes(term)
  })
})

const countedRows = computed(() => Object.values(rows).filter(isCounted))
const differenceRows = computed(() =>
  countedRows.value.filter((row) => (row.physicalStock ?? 0) !== row.systemStock),
)

function difference(row: CountRow): number {
  return isCounted(row) ? (row.physicalStock as number) - row.systemStock : 0
}

async function loadInventory() {
  isLoading.value = true
  loadError.value = ''
  try {
    inventory.value = await getInventory(null)
    for (const key of Object.keys(rows)) delete rows[key]
    for (const item of inventory.value) {
      rows[item.productId] = {
        productId: item.productId,
        sku: item.sku,
        name: item.name,
        unit: item.unit,
        systemStock: item.stock,
        physicalStock: null,
        reason: '',
      }
    }
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat stok sistem.')
  } finally {
    isLoading.value = false
  }
}

async function loadHistory() {
  try {
    const page = await getStockOpnames(historyPage.value, 10)
    history.value = page.items
    historyTotal.value = page.total
  } catch {
    history.value = []
  }
}

function matchSystem(row: CountRow) {
  row.physicalStock = row.systemStock
}

async function submit() {
  formError.value = ''
  result.value = null
  if (countedRows.value.length === 0) {
    formError.value = 'Isi stok fisik minimal untuk satu produk.'
    return
  }
  const missingReason = differenceRows.value.find((row) => !row.reason.trim())
  if (missingReason) {
    formError.value = `Alasan selisih wajib diisi untuk ${missingReason.name}.`
    return
  }
  if (
    differenceRows.value.length > 0 &&
    !window.confirm(`${differenceRows.value.length} produk memiliki selisih dan stoknya akan disesuaikan. Lanjutkan?`)
  ) {
    return
  }

  saving.value = true
  try {
    result.value = await createStockOpname({
      notes: notes.value.trim() || null,
      items: countedRows.value.map((row) => ({
        productId: row.productId,
        physicalStock: row.physicalStock as number,
        systemStock: row.systemStock,
        reason: row.reason.trim() || null,
      })),
    })
    notes.value = ''
    await Promise.all([loadInventory(), loadHistory()])
  } catch (error) {
    formError.value = errorMessage(error, 'Gagal menyimpan stock opname.')
  } finally {
    saving.value = false
  }
}

async function changeHistoryPage(page: number) {
  historyPage.value = page
  await loadHistory()
}

onMounted(async () => {
  await Promise.all([loadInventory(), loadHistory()])
})
</script>

<template>
  <main class="page">
    <div class="page-inner">
      <header class="page-header">
        <div>
          <nav class="breadcrumb" aria-label="Breadcrumb">
            <RouterLink to="/inventory">Inventory</RouterLink><span>/</span><span aria-current="page">Stock Opname</span>
          </nav>
          <h1 class="page-title">Stock Opname</h1>
          <p class="page-subtitle">
            Hitung stok fisik lalu bandingkan dengan stok sistem. Produk yang selisih disesuaikan otomatis dan tercatat di kartu stok.
          </p>
        </div>
        <div class="header-actions">
          <button type="button" class="btn btn-secondary" :disabled="isLoading" @click="loadInventory">Muat ulang stok sistem</button>
        </div>
      </header>

      <div v-if="result" class="alert alert-success" role="status">
        Stock opname <strong>{{ result.opnameNumber }}</strong> tersimpan: {{ result.totalItems }} produk dihitung,
        {{ result.itemsWithDifference }} disesuaikan.
      </div>
      <div v-if="formError" class="alert alert-error" role="alert">{{ formError }}</div>

      <section class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">Lembar hitung</h2>
            <p class="card-subtitle">
              {{ countedRows.length }} produk dihitung · {{ differenceRows.length }} selisih
            </p>
          </div>
          <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap">
            <input v-model="search" type="search" class="input" style="width: 220px" placeholder="Cari produk">
            <label class="small" style="display: flex; gap: 6px; align-items: center">
              <input v-model="onlyCounted" type="checkbox"> Hanya yang sudah dihitung
            </label>
          </div>
        </div>
        <div v-if="isLoading" class="card-body"><div class="skeleton" style="height: 160px" /></div>
        <div v-else-if="loadError" class="card-body"><div class="alert alert-error">{{ loadError }}</div></div>
        <div v-else-if="visibleRows.length === 0" class="empty">Tidak ada produk.</div>
        <div v-else class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>Produk</th>
                <th class="num">Stok sistem</th>
                <th class="num" style="width: 150px">Stok fisik</th>
                <th class="num">Selisih</th>
                <th style="min-width: 220px">Alasan selisih</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in visibleRows" :key="row.productId">
                <td>
                  <div class="strong">{{ row.name }}</div>
                  <div class="mono muted">{{ row.sku }}</div>
                </td>
                <td class="num">{{ formatNumber(row.systemStock) }} {{ row.unit }}</td>
                <td class="num">
                  <div style="display: flex; gap: 4px; align-items: center">
                    <input
                      v-model.number="row.physicalStock"
                      type="number"
                      min="0"
                      step="any"
                      class="input num"
                      :aria-label="`Stok fisik ${row.name}`"
                    >
                    <button type="button" class="btn btn-ghost btn-sm" title="Sama dengan sistem" @click="matchSystem(row)">=</button>
                  </div>
                </td>
                <td class="num strong" :class="difference(row) > 0 ? 'text-success' : difference(row) < 0 ? 'text-danger' : 'muted'">
                  {{ isCounted(row) ? formatSigned(difference(row)) : '-' }}
                </td>
                <td>
                  <input
                    v-if="isCounted(row) && difference(row) !== 0"
                    v-model="row.reason"
                    class="input"
                    maxlength="500"
                    placeholder="Mis. barang rusak / hilang"
                    :aria-label="`Alasan selisih ${row.name}`"
                  >
                  <span v-else class="muted small">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="card-body" style="border-top: 1px solid var(--c-border-soft)">
          <div class="form-grid cols-2" style="align-items: end">
            <label class="field">
              <span class="label">Catatan opname</span>
              <input v-model="notes" class="input" maxlength="1000" placeholder="Mis. Opname akhir bulan">
            </label>
            <div class="field" style="align-items: flex-end">
              <button type="button" class="btn btn-primary" :disabled="saving || countedRows.length === 0" @click="submit">
                {{ saving ? 'Menyimpan…' : 'Simpan stock opname' }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <section class="card">
        <div class="card-header"><h2 class="card-title">Riwayat stock opname</h2></div>
        <div v-if="history.length === 0" class="empty">Belum ada stock opname.</div>
        <template v-else>
          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Nomor</th>
                  <th>Waktu</th>
                  <th>Oleh</th>
                  <th class="num">Produk</th>
                  <th class="num">Selisih</th>
                  <th>Catatan</th>
                  <th class="actions" />
                </tr>
              </thead>
              <tbody>
                <template v-for="opname in history" :key="opname.id">
                  <tr>
                    <td class="mono">{{ opname.opnameNumber }}</td>
                    <td>{{ formatDateTime(opname.createdAt) }}</td>
                    <td>{{ opname.createdByName || '-' }}</td>
                    <td class="num">{{ opname.totalItems }}</td>
                    <td class="num">{{ opname.itemsWithDifference }}</td>
                    <td class="muted">{{ opname.notes || '-' }}</td>
                    <td class="actions">
                      <button type="button" class="btn btn-ghost btn-sm" @click="expanded = expanded === opname.id ? null : opname.id">
                        {{ expanded === opname.id ? 'Tutup' : 'Rincian' }}
                      </button>
                    </td>
                  </tr>
                  <tr v-if="expanded === opname.id">
                    <td colspan="7" style="background: var(--c-bg)">
                      <table class="table">
                        <thead>
                          <tr><th>Produk</th><th class="num">Sistem</th><th class="num">Fisik</th><th class="num">Selisih</th><th>Alasan</th></tr>
                        </thead>
                        <tbody>
                          <tr v-for="item in opname.items" :key="item.productId">
                            <td>{{ item.sku }} — {{ item.name }}</td>
                            <td class="num">{{ formatNumber(item.systemStock) }}</td>
                            <td class="num">{{ formatNumber(item.physicalStock) }}</td>
                            <td class="num" :class="item.difference < 0 ? 'text-danger' : item.difference > 0 ? 'text-success' : ''">
                              {{ formatSigned(item.difference) }}
                            </td>
                            <td class="muted">{{ item.reason || '-' }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
          <PaginationBar :page="historyPage" :page-size="10" :total="historyTotal" @update:page="changeHistoryPage" />
        </template>
      </section>
    </div>
  </main>
</template>
