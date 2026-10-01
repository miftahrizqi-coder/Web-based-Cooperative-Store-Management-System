<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { getAuditLogs } from '../../api/auditLogs'
import PaginationBar from '../../components/ui/PaginationBar.vue'
import { errorMessage } from '../../services/api'
import { AUDIT_ACTIONS, AUDIT_MODULES, type AuditLog } from '../../types/audit'
import { downloadCsv, formatDateTime } from '../../utils/format'

const filters = reactive({ module: '', action: '', search: '', dateFrom: '', dateTo: '' })
const logs = ref<AuditLog[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const isLoading = ref(true)
const loadError = ref('')
const expanded = ref<string | null>(null)

function actionClass(action: string): string {
  if (['DELETE', 'CANCEL', 'REJECT', 'LOGIN_FAILED'].includes(action)) return 'badge-danger'
  if (['STOCK_ADJUSTMENT', 'STOCK_OPNAME', 'PASSWORD_RESET'].includes(action)) return 'badge-warning'
  if (['APPROVE', 'PAYMENT', 'SALE', 'PURCHASE'].includes(action)) return 'badge-success'
  if (['LOGIN', 'LOGOUT'].includes(action)) return 'badge-info'
  return 'badge-neutral'
}

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    const result = await getAuditLogs({ ...filters, page: page.value, pageSize })
    logs.value = result.items
    total.value = result.total
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat audit log.')
  } finally {
    isLoading.value = false
  }
}

function applyFilters() {
  if (page.value !== 1) page.value = 1
  else void load()
}

function exportCsv() {
  downloadCsv(
    'audit-log',
    ['Waktu', 'Pengguna', 'Aksi', 'Modul', 'Deskripsi', 'Referensi', 'IP'],
    logs.value.map((log) => [
      formatDateTime(log.createdAt), log.userName ?? log.userId ?? '', log.action, log.module,
      log.description, log.referenceId ?? '', log.ipAddress ?? '',
    ]),
  )
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
            <span>Administrasi</span><span>/</span><span aria-current="page">Audit Log</span>
          </nav>
          <h1 class="page-title">Audit Log</h1>
          <p class="page-subtitle">
            Jejak aktivitas penting: login, perubahan data, penjualan, pembatalan, penyesuaian stok, approval, dan pembayaran.
          </p>
        </div>
        <div class="header-actions">
          <button type="button" class="btn btn-secondary" :disabled="logs.length === 0" @click="exportCsv">Ekspor CSV</button>
        </div>
      </header>

      <form class="card card-body" @submit.prevent="applyFilters">
        <div class="filter-bar">
          <label class="field">
            <span class="label">Modul</span>
            <select v-model="filters.module" class="select">
              <option value="">Semua</option>
              <option v-for="module in AUDIT_MODULES" :key="module" :value="module">{{ module }}</option>
            </select>
          </label>
          <label class="field">
            <span class="label">Aksi</span>
            <select v-model="filters.action" class="select">
              <option value="">Semua</option>
              <option v-for="action in AUDIT_ACTIONS" :key="action" :value="action">{{ action }}</option>
            </select>
          </label>
          <label class="field">
            <span class="label">Cari deskripsi</span>
            <input v-model="filters.search" type="search" class="input">
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
        <div v-if="isLoading" class="card-body"><div class="skeleton" style="height: 160px" /></div>
        <div v-else-if="loadError" class="card-body"><div class="alert alert-error">{{ loadError }}</div></div>
        <div v-else-if="logs.length === 0" class="empty">Tidak ada aktivitas untuk filter ini.</div>
        <template v-else>
          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Waktu</th>
                  <th>Pengguna</th>
                  <th>Aksi</th>
                  <th>Modul</th>
                  <th>Deskripsi</th>
                  <th>IP</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="log in logs" :key="log.id">
                  <tr style="cursor: pointer" @click="expanded = expanded === log.id ? null : log.id">
                    <td class="small">{{ formatDateTime(log.createdAt) }}</td>
                    <td>{{ log.userName || log.userId || '-' }}</td>
                    <td><span class="badge" :class="actionClass(log.action)">{{ log.action }}</span></td>
                    <td class="mono">{{ log.module }}</td>
                    <td>{{ log.description }}</td>
                    <td class="mono muted">{{ log.ipAddress || '-' }}</td>
                  </tr>
                  <tr v-if="expanded === log.id && (log.metadata || log.referenceId)">
                    <td colspan="6" style="background: var(--c-bg)">
                      <div class="small">Referensi: <span class="mono">{{ log.referenceId || '-' }}</span></div>
                      <pre v-if="log.metadata" class="mono" style="white-space: pre-wrap; margin: 8px 0 0">{{ JSON.stringify(log.metadata, null, 2) }}</pre>
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
