<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { getReturns } from '../../api/returns'
import { cancelSale, getSale } from '../../api/sales'
import SaleReceipt from '../../components/sales/SaleReceipt.vue'
import { errorMessage } from '../../services/api'
import { useAuth } from '../../stores/auth'
import { RETURN_STATUS_LABELS, type ReturnRecord } from '../../types/returns'
import { PAYMENT_METHOD_LABELS, type Sale } from '../../types/sale'
import { formatCurrency, formatDateTime, formatNumber } from '../../utils/format'

const route = useRoute()
const { hasRole } = useAuth()
const saleId = computed(() => String(route.params.id))

const sale = ref<Sale | null>(null)
const returns = ref<ReturnRecord[]>([])
const isLoading = ref(true)
const loadError = ref('')
const actionError = ref('')
const cancelling = ref(false)

const canCancel = computed(() => sale.value?.status === 'COMPLETED' && hasRole('admin', 'pengurus'))
const canReturn = computed(
  () =>
    sale.value?.status === 'COMPLETED' &&
    sale.value.items.some((item) => item.returnedQuantity < item.quantity),
)
const showCost = computed(() => hasRole('admin', 'pengurus'))

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    sale.value = await getSale(saleId.value)
    returns.value = (await getReturns({ saleId: saleId.value, pageSize: 50 })).items
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat transaksi.')
  } finally {
    isLoading.value = false
  }
}

async function cancel() {
  if (!sale.value) return
  const reason = window.prompt(
    `Batalkan transaksi ${sale.value.invoiceNumber}? Stok akan dikembalikan.\nAlasan pembatalan:`,
  )
  if (reason === null) return
  cancelling.value = true
  actionError.value = ''
  try {
    await cancelSale(sale.value.id, reason.trim() || null)
    await load()
  } catch (error) {
    actionError.value = errorMessage(error, 'Gagal membatalkan transaksi.')
  } finally {
    cancelling.value = false
  }
}

function print() {
  window.print()
}

onMounted(load)
</script>

<template>
  <main class="page">
    <div class="page-inner">
      <header class="page-header no-print">
        <div>
          <nav class="breadcrumb" aria-label="Breadcrumb">
            <RouterLink to="/sales">Riwayat Penjualan</RouterLink><span>/</span><span aria-current="page">Detail</span>
          </nav>
          <h1 class="page-title mono">{{ sale?.invoiceNumber || 'Detail transaksi' }}</h1>
          <p v-if="sale" class="page-subtitle">
            {{ formatDateTime(sale.createdAt) }} · Kasir {{ sale.cashierName || '-' }}
          </p>
        </div>
        <div v-if="sale" class="header-actions">
          <button type="button" class="btn btn-secondary" @click="print">Cetak struk</button>
          <RouterLink
            v-if="canReturn"
            :to="{ path: '/returns/create', query: { type: 'SALE', saleId: sale.id } }"
            class="btn btn-outline"
          >
            Ajukan retur
          </RouterLink>
          <button v-if="canCancel" type="button" class="btn btn-danger" :disabled="cancelling" @click="cancel">
            {{ cancelling ? 'Membatalkan…' : 'Batalkan transaksi' }}
          </button>
        </div>
      </header>

      <div v-if="loadError" class="alert alert-error no-print">{{ loadError }}</div>
      <div v-if="actionError" class="alert alert-error no-print" role="alert">{{ actionError }}</div>
      <div v-if="isLoading" class="skeleton" style="height: 200px" />

      <template v-else-if="sale">
        <div v-if="sale.status === 'CANCELLED'" class="alert alert-warning no-print">
          Transaksi dibatalkan {{ formatDateTime(sale.cancelledAt) }}{{ sale.cancelReason ? `: ${sale.cancelReason}` : '' }}.
          Stok yang belum diretur sudah dikembalikan.
        </div>

        <div class="no-print" style="display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))">
          <section class="card">
            <div class="card-header"><h2 class="card-title">Item</h2></div>
            <div class="table-wrap">
              <table class="table">
                <thead>
                  <tr>
                    <th>Produk</th>
                    <th class="num">Qty</th>
                    <th class="num">Harga</th>
                    <th v-if="showCost" class="num">HPP</th>
                    <th class="num">Subtotal</th>
                    <th class="num">Diretur</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in sale.items" :key="item.productId">
                    <td>{{ item.name }}<div class="mono muted">{{ item.sku }}</div></td>
                    <td class="num">{{ formatNumber(item.quantity) }} {{ item.unit }}</td>
                    <td class="num">{{ formatCurrency(item.price) }}</td>
                    <td v-if="showCost" class="num muted">{{ formatCurrency(item.costPrice ?? 0) }}</td>
                    <td class="num">{{ formatCurrency(item.subtotal) }}</td>
                    <td class="num">{{ item.returnedQuantity ? formatNumber(item.returnedQuantity) : '-' }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr><td :colspan="showCost ? 4 : 3">Subtotal</td><td class="num">{{ formatCurrency(sale.subtotal) }}</td><td /></tr>
                  <tr v-if="sale.discount > 0"><td :colspan="showCost ? 4 : 3">Diskon</td><td class="num">-{{ formatCurrency(sale.discount) }}</td><td /></tr>
                  <tr><td :colspan="showCost ? 4 : 3">Total</td><td class="num">{{ formatCurrency(sale.total) }}</td><td /></tr>
                </tfoot>
              </table>
            </div>
          </section>

          <section class="card">
            <div class="card-header"><h2 class="card-title">Pembayaran</h2></div>
            <div class="card-body">
              <dl class="dl" style="grid-template-columns: 1fr 1fr">
                <div><dt>Status</dt><dd>
                  <span class="badge" :class="sale.status === 'COMPLETED' ? 'badge-success' : 'badge-danger'">
                    {{ sale.status === 'COMPLETED' ? 'Selesai' : 'Dibatalkan' }}
                  </span>
                </dd></div>
                <div><dt>Metode</dt><dd>{{ PAYMENT_METHOD_LABELS[sale.payment.method] }}</dd></div>
                <div><dt>Dibayar</dt><dd>{{ formatCurrency(sale.payment.amount) }}</dd></div>
                <div><dt>Kembalian</dt><dd>{{ formatCurrency(sale.payment.change) }}</dd></div>
                <div v-if="sale.payment.referenceNumber"><dt>Referensi</dt><dd class="mono">{{ sale.payment.referenceNumber }}</dd></div>
                <div><dt>Anggota</dt><dd>
                  <RouterLink v-if="sale.memberId && hasRole('admin', 'pengurus')" :to="`/members/${sale.memberId}`">
                    {{ sale.memberNumber }} · {{ sale.memberName }}
                  </RouterLink>
                  <span v-else>{{ sale.memberName ? `${sale.memberNumber} · ${sale.memberName}` : '-' }}</span>
                </dd></div>
              </dl>
            </div>
          </section>
        </div>

        <section v-if="returns.length" class="card no-print">
          <div class="card-header"><h2 class="card-title">Retur untuk transaksi ini</h2></div>
          <div class="table-wrap">
            <table class="table">
              <thead><tr><th>Nomor</th><th>Tanggal</th><th>Item</th><th class="num">Nilai</th><th>Status</th></tr></thead>
              <tbody>
                <tr v-for="ret in returns" :key="ret.id">
                  <td class="mono">{{ ret.returnNumber }}</td>
                  <td>{{ formatDateTime(ret.createdAt) }}</td>
                  <td class="small">{{ ret.items.map((i) => `${i.name} × ${formatNumber(i.quantity)}`).join(', ') }}</td>
                  <td class="num">{{ formatCurrency(ret.totalAmount) }}</td>
                  <td><span class="badge" :class="ret.status === 'APPROVED' ? 'badge-success' : ret.status === 'REJECTED' ? 'badge-danger' : 'badge-warning'">{{ RETURN_STATUS_LABELS[ret.status] }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <div class="print-area" style="display: none">
          <SaleReceipt :sale="sale" />
        </div>
      </template>
    </div>
  </main>
</template>

<style scoped>
@media print {
  .print-area { display: block !important; }
}
</style>
