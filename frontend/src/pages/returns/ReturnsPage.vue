<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { approveReturn, getReturns, rejectReturn } from '../../api/returns'
import PaginationBar from '../../components/ui/PaginationBar.vue'
import { errorMessage } from '../../services/api'
import { useAuth } from '../../stores/auth'
import {
  RETURN_REASON_LABELS,
  RETURN_STATUS_LABELS,
  type ReturnRecord,
  type ReturnStatus,
  type ReturnType,
} from '../../types/returns'
import { formatCurrency, formatDateTime, formatNumber } from '../../utils/format'

const { currentUser, hasRole } = useAuth()
const canApprove = computed(() => hasRole('admin', 'pengurus'))
const isCashier = computed(() => currentUser.value?.role === 'kasir')

const filters = reactive({ type: '' as ReturnType | '', status: '' as ReturnStatus | '' })
const returns = ref<ReturnRecord[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const isLoading = ref(true)
const loadError = ref('')
const actionError = ref('')
const busyId = ref<string | null>(null)
const expanded = ref<string | null>(null)

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    const result = await getReturns({ ...filters, page: page.value, pageSize })
    returns.value = result.items
    total.value = result.total
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat retur.')
  } finally {
    isLoading.value = false
  }
}

function applyFilters() {
  if (page.value !== 1) page.value = 1
  else void load()
}

function statusClass(status: ReturnStatus) {
  return status === 'APPROVED' ? 'badge-success' : status === 'REJECTED' ? 'badge-danger' : 'badge-warning'
}

async function approve(ret: ReturnRecord) {
  const effect =
    ret.type === 'SALE'
      ? 'Stok akan bertambah dan refund dicatat.'
      : 'Stok akan berkurang dan hutang supplier dikoreksi.'
  if (!window.confirm(`Setujui retur ${ret.returnNumber}? ${effect}`)) return
  busyId.value = ret.id
  actionError.value = ''
  try {
    await approveReturn(ret.id)
    await load()
  } catch (error) {
    actionError.value = errorMessage(error, 'Gagal menyetujui retur.')
  } finally {
    busyId.value = null
  }
}

async function reject(ret: ReturnRecord) {
  const reason = window.prompt(`Alasan menolak retur ${ret.returnNumber}:`)
  if (reason === null) return
  if (reason.trim().length < 3) {
    actionError.value = 'Alasan penolakan minimal 3 karakter.'
    return
  }
  busyId.value = ret.id
  actionError.value = ''
  try {
    await rejectReturn(ret.id, reason.trim())
    await load()
  } catch (error) {
    actionError.value = errorMessage(error, 'Gagal menolak retur.')
  } finally {
    busyId.value = null
  }
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
            <span>Penjualan</span><span>/</span><span aria-current="page">Retur</span>
          </nav>
          <h1 class="page-title">Retur</h1>
          <p class="page-subtitle">
            Retur penjualan (barang kembali dari pelanggan) dan retur pembelian (barang dikembalikan ke supplier).
            Stok baru berubah setelah retur disetujui.
          </p>
        </div>
        <div class="header-actions">
          <RouterLink :to="{ path: '/returns/create', query: { type: 'SALE' } }" class="btn btn-primary">+ Retur penjualan</RouterLink>
          <RouterLink v-if="canApprove" :to="{ path: '/returns/create', query: { type: 'PURCHASE' } }" class="btn btn-outline">
            + Retur pembelian
          </RouterLink>
        </div>
      </header>

      <form class="card card-body" @submit.prevent="applyFilters">
        <div class="filter-bar">
          <label v-if="!isCashier" class="field">
            <span class="label">Jenis</span>
            <select v-model="filters.type" class="select">
              <option value="">Semua</option>
              <option value="SALE">Retur penjualan</option>
              <option value="PURCHASE">Retur pembelian</option>
            </select>
          </label>
          <label class="field">
            <span class="label">Status</span>
            <select v-model="filters.status" class="select">
              <option value="">Semua</option>
              <option value="PENDING_APPROVAL">Menunggu approval</option>
              <option value="APPROVED">Disetujui</option>
              <option value="REJECTED">Ditolak</option>
            </select>
          </label>
          <div class="field"><button type="submit" class="btn btn-secondary">Terapkan</button></div>
        </div>
      </form>

      <div v-if="actionError" class="alert alert-error" role="alert">{{ actionError }}</div>

      <section class="card">
        <div v-if="isLoading" class="card-body"><div class="skeleton" style="height: 120px" /></div>
        <div v-else-if="loadError" class="card-body"><div class="alert alert-error">{{ loadError }}</div></div>
        <div v-else-if="returns.length === 0" class="empty"><strong>Belum ada retur</strong></div>
        <template v-else>
          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Nomor</th>
                  <th>Jenis</th>
                  <th>Referensi</th>
                  <th>Alasan</th>
                  <th class="num">Nilai</th>
                  <th>Status</th>
                  <th>Diajukan</th>
                  <th class="actions">Aksi</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="ret in returns" :key="ret.id">
                  <tr>
                    <td class="mono strong">{{ ret.returnNumber }}</td>
                    <td>{{ ret.type === 'SALE' ? 'Penjualan' : 'Pembelian' }}</td>
                    <td>
                      <RouterLink v-if="ret.saleId" :to="`/sales/${ret.saleId}`" class="mono">{{ ret.saleInvoiceNumber }}</RouterLink>
                      <template v-else>
                        <RouterLink v-if="ret.receiptId" :to="`/goods-receipts/${ret.receiptId}`" class="mono">{{ ret.receiptNumber || ret.receiptId }}</RouterLink>
                        <div class="muted small">{{ ret.supplierName }}</div>
                      </template>
                    </td>
                    <td>{{ RETURN_REASON_LABELS[ret.reason] }}</td>
                    <td class="num">{{ formatCurrency(ret.totalAmount) }}</td>
                    <td><span class="badge" :class="statusClass(ret.status)">{{ RETURN_STATUS_LABELS[ret.status] }}</span></td>
                    <td class="small">{{ formatDateTime(ret.createdAt) }}<div class="muted">{{ ret.createdByName }}</div></td>
                    <td class="actions">
                      <button type="button" class="btn btn-ghost btn-sm" @click="expanded = expanded === ret.id ? null : ret.id">
                        {{ expanded === ret.id ? 'Tutup' : 'Rincian' }}
                      </button>
                      <template v-if="canApprove && ret.status === 'PENDING_APPROVAL'">
                        <button
                          type="button"
                          class="btn btn-outline btn-sm"
                          :disabled="busyId === ret.id || ret.createdBy === currentUser?.id"
                          :title="ret.createdBy === currentUser?.id ? 'Pengaju tidak dapat menyetujui returnya sendiri' : undefined"
                          @click="approve(ret)"
                        >
                          Setujui
                        </button>
                        <button type="button" class="btn btn-ghost btn-sm text-danger" :disabled="busyId === ret.id" @click="reject(ret)">
                          Tolak
                        </button>
                      </template>
                    </td>
                  </tr>
                  <tr v-if="expanded === ret.id">
                    <td colspan="8" style="background: var(--c-bg)">
                      <table class="table">
                        <thead><tr><th>Produk</th><th class="num">Qty</th><th class="num">Harga</th><th class="num">Subtotal</th></tr></thead>
                        <tbody>
                          <tr v-for="item in ret.items" :key="item.productId">
                            <td>{{ item.sku }} — {{ item.name }}</td>
                            <td class="num">{{ formatNumber(item.quantity) }}</td>
                            <td class="num">{{ formatCurrency(item.price) }}</td>
                            <td class="num">{{ formatCurrency(item.subtotal) }}</td>
                          </tr>
                        </tbody>
                      </table>
                      <p v-if="ret.notes" class="small" style="margin: 8px 14px">Catatan: {{ ret.notes }}</p>
                      <p v-if="ret.approvedAt" class="small muted" style="margin: 8px 14px">
                        {{ ret.status === 'REJECTED' ? 'Ditolak' : 'Disetujui' }} oleh {{ ret.approvedByName || '-' }}
                        pada {{ formatDateTime(ret.approvedAt) }}{{ ret.rejectionReason ? ` — ${ret.rejectionReason}` : '' }}
                      </p>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
          <PaginationBar v-model:page="page" :page-size="pageSize" :total="total" />
        </template>
      </section>
    </div>
  </main>
</template>
