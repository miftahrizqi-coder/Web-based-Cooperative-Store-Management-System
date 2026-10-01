<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { getMember, getMemberTransactions } from '../../api/members'
import PaginationBar from '../../components/ui/PaginationBar.vue'
import { errorMessage } from '../../services/api'
import { useAuth } from '../../stores/auth'
import type { MemberWithStats } from '../../types/member'
import { PAYMENT_METHOD_LABELS, type Sale } from '../../types/sale'
import { formatCurrency, formatDate, formatDateTime } from '../../utils/format'

const route = useRoute()
const { hasRole } = useAuth()
const memberId = computed(() => String(route.params.id))

const member = ref<MemberWithStats | null>(null)
const sales = ref<Sale[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loadError = ref('')
const isLoading = ref(true)

async function loadTransactions() {
  const result = await getMemberTransactions(memberId.value, page.value, pageSize)
  sales.value = result.items
  total.value = result.total
}

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    member.value = await getMember(memberId.value)
    await loadTransactions()
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat detail anggota.')
  } finally {
    isLoading.value = false
  }
}

watch(page, () => {
  loadTransactions().catch((error) => {
    loadError.value = errorMessage(error)
  })
})

onMounted(load)
</script>

<template>
  <main class="page">
    <div class="page-inner">
      <header class="page-header">
        <div>
          <nav class="breadcrumb" aria-label="Breadcrumb">
            <RouterLink to="/members">Anggota</RouterLink><span>/</span><span aria-current="page">Detail</span>
          </nav>
          <h1 class="page-title">{{ member?.name || 'Detail anggota' }}</h1>
          <p class="page-subtitle mono">{{ member?.memberNumber }}</p>
        </div>
        <div v-if="member && hasRole('admin')" class="header-actions">
          <RouterLink :to="`/members/${member.id}/edit`" class="btn btn-secondary">Ubah</RouterLink>
        </div>
      </header>

      <div v-if="loadError" class="alert alert-error" role="alert">{{ loadError }}</div>
      <div v-if="isLoading" class="skeleton" style="height: 140px" />

      <template v-else-if="member">
        <div class="kpi-grid">
          <div class="kpi">
            <div class="kpi-label">Status</div>
            <div class="kpi-value" style="font-size: 18px">
              <span class="badge" :class="member.status === 'ACTIVE' ? 'badge-success' : 'badge-neutral'">
                {{ member.status === 'ACTIVE' ? 'Aktif' : 'Nonaktif' }}
              </span>
            </div>
            <div class="kpi-context">Bergabung {{ formatDate(member.joinedAt) }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-label">Total belanja</div>
            <div class="kpi-value">{{ formatCurrency(member.totalSpending) }}</div>
            <div class="kpi-context">Setelah retur</div>
          </div>
          <div class="kpi">
            <div class="kpi-label">Jumlah transaksi</div>
            <div class="kpi-value">{{ member.transactionCount }}</div>
            <div class="kpi-context">Terakhir {{ formatDate(member.lastTransactionAt) }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-label">Akun login</div>
            <div class="kpi-value" style="font-size: 16px">{{ member.hasUserAccount ? 'Sudah ada' : 'Belum ada' }}</div>
            <div class="kpi-context">Role anggota di menu Pengguna</div>
          </div>
        </div>

        <section class="card">
          <div class="card-header"><h2 class="card-title">Data anggota</h2></div>
          <div class="card-body">
            <dl class="dl">
              <div><dt>Telepon</dt><dd>{{ member.phone }}</dd></div>
              <div><dt>Email</dt><dd>{{ member.email || '-' }}</dd></div>
              <div><dt>Alamat</dt><dd>{{ member.address || '-' }}</dd></div>
            </dl>
          </div>
        </section>

        <section class="card">
          <div class="card-header"><h2 class="card-title">Riwayat transaksi</h2></div>
          <div v-if="sales.length === 0" class="empty">Belum ada transaksi.</div>
          <template v-else>
            <div class="table-wrap">
              <table class="table">
                <thead>
                  <tr>
                    <th>Invoice</th>
                    <th>Tanggal</th>
                    <th>Item</th>
                    <th>Pembayaran</th>
                    <th class="num">Total</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="sale in sales" :key="sale.id">
                    <td class="mono"><RouterLink :to="`/sales/${sale.id}`">{{ sale.invoiceNumber }}</RouterLink></td>
                    <td>{{ formatDateTime(sale.createdAt) }}</td>
                    <td>{{ sale.items.length }} produk</td>
                    <td>{{ PAYMENT_METHOD_LABELS[sale.payment.method] }}</td>
                    <td class="num">{{ formatCurrency(sale.total) }}</td>
                    <td>
                      <span class="badge" :class="sale.status === 'COMPLETED' ? 'badge-success' : 'badge-danger'">
                        {{ sale.status === 'COMPLETED' ? 'Selesai' : 'Dibatalkan' }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <PaginationBar v-model:page="page" :page-size="pageSize" :total="total" />
          </template>
        </section>
      </template>
    </div>
  </main>
</template>
