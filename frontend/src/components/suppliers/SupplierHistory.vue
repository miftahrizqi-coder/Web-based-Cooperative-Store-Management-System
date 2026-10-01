<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  getSupplierInvoicesOf,
  getSupplierPaymentsOf,
  getSupplierProductsOf,
  getSupplierPurchaseOrders,
  getSupplierPurchases,
  getSupplierReceipts,
  getSupplierSummary,
  type SupplierSummary,
} from '../../api/suppliers'
import { errorMessage } from '../../services/api'
import type {
  GoodsReceipt,
  Purchase,
  PurchaseOrder,
  SupplierInvoice,
  SupplierPayment,
} from '../../types/procurement'
import type { SupplierProduct } from '../../types/supplierProduct'
import { formatCurrency, formatDate, formatNumber } from '../../utils/format'

const props = defineProps<{ supplierId: string }>()

type Tab = 'products' | 'orders' | 'receipts' | 'purchases' | 'invoices' | 'payments'
const tab = ref<Tab>('products')
const summary = ref<SupplierSummary | null>(null)
const products = ref<SupplierProduct[]>([])
const orders = ref<PurchaseOrder[]>([])
const receipts = ref<GoodsReceipt[]>([])
const purchases = ref<Purchase[]>([])
const invoices = ref<SupplierInvoice[]>([])
const payments = ref<SupplierPayment[]>([])
const loadError = ref('')

onMounted(async () => {
  const id = props.supplierId
  try {
    const [s, p, o, r, pu, i, pa] = await Promise.all([
      getSupplierSummary(id),
      getSupplierProductsOf(id),
      getSupplierPurchaseOrders(id),
      getSupplierReceipts(id),
      getSupplierPurchases(id),
      getSupplierInvoicesOf(id),
      getSupplierPaymentsOf(id),
    ])
    summary.value = s
    products.value = p
    orders.value = o
    receipts.value = r
    purchases.value = pu
    invoices.value = i
    payments.value = pa
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat riwayat supplier.')
  }
})

const tabs: { key: Tab; label: string }[] = [
  { key: 'products', label: 'Produk disuplai' },
  { key: 'orders', label: 'Riwayat PO' },
  { key: 'receipts', label: 'Penerimaan' },
  { key: 'purchases', label: 'Pembelian' },
  { key: 'invoices', label: 'Invoice' },
  { key: 'payments', label: 'Pembayaran' },
]
</script>

<template>
  <div style="display: flex; flex-direction: column; gap: 16px">
    <div v-if="loadError" class="alert alert-error">{{ loadError }}</div>

    <section v-if="summary" class="kpi-grid" aria-label="Informasi hutang supplier">
      <div class="kpi"><div class="kpi-label">Total pembelian</div><div class="kpi-value">{{ formatCurrency(summary.totalPurchases) }}</div><div class="kpi-context">{{ summary.purchaseOrderCount }} PO · {{ summary.activePurchaseOrderCount }} aktif</div></div>
      <div class="kpi"><div class="kpi-label">Total invoice</div><div class="kpi-value">{{ formatCurrency(summary.totalInvoiced) }}</div><div class="kpi-context">{{ summary.invoiceCount }} invoice</div></div>
      <div class="kpi"><div class="kpi-label">Total dibayar</div><div class="kpi-value">{{ formatCurrency(summary.totalPaid) }}</div><div class="kpi-context">Retur {{ formatCurrency(summary.totalReturned) }}</div></div>
      <div class="kpi" :class="{ danger: summary.outstanding > 0 }"><div class="kpi-label">Sisa hutang</div><div class="kpi-value">{{ formatCurrency(summary.outstanding) }}</div><div class="kpi-context">{{ summary.overdueInvoiceCount }} lewat jatuh tempo</div></div>
    </section>

    <section class="card">
      <nav class="tabs" style="padding: 0 12px" aria-label="Riwayat supplier">
        <button v-for="t in tabs" :key="t.key" type="button" class="tab" :class="{ active: tab === t.key }" @click="tab = t.key">{{ t.label }}</button>
      </nav>

      <div class="table-wrap">
        <table v-if="tab === 'products'" class="table">
          <thead><tr><th>Produk</th><th>SKU supplier</th><th class="num">Harga beli</th><th class="num">Min. order</th><th class="num">Lead time</th><th>Status</th></tr></thead>
          <tbody>
            <tr v-if="!products.length"><td colspan="6" class="empty">Belum ada produk.</td></tr>
            <tr v-for="item in products" :key="item.id">
              <td>{{ item.productName || item.productId }}<span v-if="item.isPreferred" class="badge badge-info" style="margin-left: 6px">Preferred</span></td>
              <td class="mono">{{ item.supplierSku }}</td>
              <td class="num">{{ formatCurrency(item.purchasePrice) }}</td>
              <td class="num">{{ formatNumber(item.minimumOrder) }}</td>
              <td class="num">{{ item.leadTimeDays }} hari</td>
              <td><span class="badge" :class="item.isActive ? 'badge-success' : 'badge-neutral'">{{ item.isActive ? 'Aktif' : 'Nonaktif' }}</span></td>
            </tr>
          </tbody>
        </table>

        <table v-else-if="tab === 'orders'" class="table">
          <thead><tr><th>No. PO</th><th>Tanggal</th><th>Status</th><th class="num">Total</th></tr></thead>
          <tbody>
            <tr v-if="!orders.length"><td colspan="4" class="empty">Belum ada PO.</td></tr>
            <tr v-for="order in orders" :key="order.id">
              <td><RouterLink :to="`/purchase-orders/${order.id}`" class="mono">{{ order.poNumber }}</RouterLink></td>
              <td>{{ formatDate(order.createdAt) }}</td>
              <td><span class="badge badge-neutral">{{ order.status }}</span></td>
              <td class="num">{{ formatCurrency(order.grandTotal) }}</td>
            </tr>
          </tbody>
        </table>

        <table v-else-if="tab === 'receipts'" class="table">
          <thead><tr><th>No. penerimaan</th><th>PO</th><th>Tanggal</th><th class="num">Diterima baik</th></tr></thead>
          <tbody>
            <tr v-if="!receipts.length"><td colspan="4" class="empty">Belum ada penerimaan.</td></tr>
            <tr v-for="receipt in receipts" :key="receipt.id">
              <td><RouterLink :to="`/goods-receipts/${receipt.id}`" class="mono">{{ receipt.receiptNumber }}</RouterLink></td>
              <td class="mono">{{ receipt.poNumber || receipt.purchaseOrderId }}</td>
              <td>{{ formatDate(receipt.receivedAt) }}</td>
              <td class="num">{{ formatNumber(receipt.items.reduce((sum, i) => sum + i.acceptedQuantity, 0)) }}</td>
            </tr>
          </tbody>
        </table>

        <table v-else-if="tab === 'purchases'" class="table">
          <thead><tr><th>No. pembelian</th><th>Tanggal</th><th>Status bayar</th><th class="num">Total</th></tr></thead>
          <tbody>
            <tr v-if="!purchases.length"><td colspan="4" class="empty">Belum ada pembelian.</td></tr>
            <tr v-for="purchase in purchases" :key="purchase.id">
              <td><RouterLink :to="`/purchases/${purchase.id}`" class="mono">{{ purchase.purchaseNumber }}</RouterLink></td>
              <td>{{ formatDate(purchase.createdAt) }}</td>
              <td><span class="badge badge-neutral">{{ purchase.paymentStatus }}</span></td>
              <td class="num">{{ formatCurrency(purchase.total) }}</td>
            </tr>
          </tbody>
        </table>

        <table v-else-if="tab === 'invoices'" class="table">
          <thead><tr><th>Invoice</th><th>Jatuh tempo</th><th>Status</th><th class="num">Total</th><th class="num">Sisa</th></tr></thead>
          <tbody>
            <tr v-if="!invoices.length"><td colspan="5" class="empty">Belum ada invoice.</td></tr>
            <tr v-for="invoice in invoices" :key="invoice.id">
              <td><RouterLink :to="`/supplier-invoices/${invoice.id}`" class="mono">{{ invoice.invoiceNumber }}</RouterLink></td>
              <td>{{ formatDate(invoice.dueDate) }}</td>
              <td><span class="badge" :class="invoice.paymentStatus === 'PAID' ? 'badge-success' : invoice.paymentStatus === 'OVERDUE' ? 'badge-danger' : 'badge-warning'">{{ invoice.paymentStatus }}</span></td>
              <td class="num">{{ formatCurrency(invoice.total) }}</td>
              <td class="num strong">{{ formatCurrency(invoice.outstanding) }}</td>
            </tr>
          </tbody>
        </table>

        <table v-else class="table">
          <thead><tr><th>No. pembayaran</th><th>Invoice</th><th>Tanggal</th><th>Metode</th><th class="num">Jumlah</th></tr></thead>
          <tbody>
            <tr v-if="!payments.length"><td colspan="5" class="empty">Belum ada pembayaran.</td></tr>
            <tr v-for="payment in payments" :key="payment.id">
              <td class="mono">{{ payment.paymentNumber }}</td>
              <td class="mono">{{ payment.invoiceNumber || payment.invoiceId }}</td>
              <td>{{ formatDate(payment.paymentDate) }}</td>
              <td>{{ payment.method }}</td>
              <td class="num">{{ formatCurrency(payment.amount) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
