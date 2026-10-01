<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { getGoodsReceipts } from '../../api/procurement'
import { createPurchaseReturn, createSalesReturn } from '../../api/returns'
import { getSale, getSaleByInvoice } from '../../api/sales'
import { errorMessage } from '../../services/api'
import { useAuth } from '../../stores/auth'
import type { GoodsReceipt } from '../../types/procurement'
import { RETURN_REASON_LABELS, type ReturnReason, type ReturnType } from '../../types/returns'
import type { Sale } from '../../types/sale'
import { formatCurrency, formatDateTime, formatNumber } from '../../utils/format'

interface Line {
  productId: string
  sku: string
  name: string
  price: number
  maxQuantity: number
  quantity: number
}

const route = useRoute()
const router = useRouter()
const { hasRole, token } = useAuth()

const type = ref<ReturnType>(route.query.type === 'PURCHASE' && hasRole('admin', 'pengurus') ? 'PURCHASE' : 'SALE')
const invoiceNumber = ref('')
const sale = ref<Sale | null>(null)
const receipts = ref<GoodsReceipt[]>([])
const receiptId = ref(typeof route.query.receiptId === 'string' ? route.query.receiptId : '')
const lines = reactive<Line[]>([])
const reason = ref<ReturnReason>('BARANG_RUSAK')
const notes = ref('')
const loading = ref(false)
const saving = ref(false)
const formError = ref('')

const selectedReceipt = computed(() => receipts.value.find((r) => r.id === receiptId.value) ?? null)
const selectedLines = computed(() => lines.filter((l) => l.quantity > 0))
const totalAmount = computed(() => selectedLines.value.reduce((sum, l) => sum + l.price * l.quantity, 0))
const reasons = Object.entries(RETURN_REASON_LABELS) as [ReturnReason, string][]

function setLinesFromSale(value: Sale) {
  lines.splice(0)
  const ratio = value.subtotal ? value.total / value.subtotal : 1
  for (const item of value.items) {
    const max = item.quantity - item.returnedQuantity
    if (max <= 0) continue
    lines.push({
      productId: item.productId,
      sku: item.sku,
      name: item.name,
      price: Math.round(item.price * ratio * 100) / 100,
      maxQuantity: max,
      quantity: 0,
    })
  }
}

function setLinesFromReceipt() {
  lines.splice(0)
  const receipt = selectedReceipt.value
  if (!receipt) return
  for (const item of receipt.items) {
    const max = item.acceptedQuantity - (item.returnedQuantity ?? 0)
    if (max <= 0) continue
    lines.push({
      productId: item.productId,
      sku: item.sku ?? '-',
      name: item.name,
      price: item.unitPrice ?? 0,
      maxQuantity: max,
      quantity: 0,
    })
  }
}

async function findSale() {
  formError.value = ''
  sale.value = null
  lines.splice(0)
  if (!invoiceNumber.value.trim()) {
    formError.value = 'Masukkan nomor invoice transaksi.'
    return
  }
  loading.value = true
  try {
    const found = await getSaleByInvoice(invoiceNumber.value)
    if (found.status !== 'COMPLETED') {
      formError.value = 'Transaksi sudah dibatalkan, tidak dapat diretur.'
      return
    }
    sale.value = found
    setLinesFromSale(found)
    if (lines.length === 0) formError.value = 'Semua item transaksi ini sudah diretur.'
  } catch (error) {
    formError.value = errorMessage(error, 'Transaksi tidak ditemukan.')
  } finally {
    loading.value = false
  }
}

async function submit() {
  formError.value = ''
  if (selectedLines.value.length === 0) {
    formError.value = 'Isi jumlah retur minimal untuk satu produk.'
    return
  }
  const invalid = selectedLines.value.find((l) => l.quantity > l.maxQuantity)
  if (invalid) {
    formError.value = `Jumlah retur ${invalid.name} melebihi batas (${formatNumber(invalid.maxQuantity)}).`
    return
  }
  saving.value = true
  const items = selectedLines.value.map((l) => ({ productId: l.productId, quantity: l.quantity }))
  try {
    if (type.value === 'SALE') {
      await createSalesReturn({
        saleId: sale.value?.id ?? null,
        invoiceNumber: null,
        items,
        reason: reason.value,
        notes: notes.value.trim() || null,
      })
    } else {
      await createPurchaseReturn({
        receiptId: receiptId.value,
        items,
        reason: reason.value,
        notes: notes.value.trim() || null,
      })
    }
    await router.push('/returns')
  } catch (error) {
    formError.value = errorMessage(error, 'Gagal mengajukan retur.')
  } finally {
    saving.value = false
  }
}

async function switchType(value: ReturnType) {
  type.value = value
  lines.splice(0)
  formError.value = ''
  if (value === 'PURCHASE' && receipts.value.length === 0) {
    try {
      receipts.value = await getGoodsReceipts(token.value ?? '')
    } catch (error) {
      formError.value = errorMessage(error, 'Gagal memuat penerimaan barang.')
    }
  }
  if (value === 'PURCHASE') setLinesFromReceipt()
}

onMounted(async () => {
  if (type.value === 'PURCHASE') {
    await switchType('PURCHASE')
  } else if (typeof route.query.saleId === 'string') {
    try {
      const found = await getSale(route.query.saleId)
      invoiceNumber.value = found.invoiceNumber
      sale.value = found
      setLinesFromSale(found)
    } catch (error) {
      formError.value = errorMessage(error)
    }
  }
})
</script>

<template>
  <main class="page">
    <div class="page-inner" style="max-width: 1000px">
      <header>
        <nav class="breadcrumb" aria-label="Breadcrumb">
          <RouterLink to="/returns">Retur</RouterLink><span>/</span><span aria-current="page">Ajukan</span>
        </nav>
        <h1 class="page-title">Ajukan retur</h1>
        <p class="page-subtitle">
          Retur diajukan lalu disetujui Admin/Pengurus (bukan oleh pengaju). Stok berubah setelah disetujui.
        </p>
      </header>

      <div v-if="hasRole('admin', 'pengurus')" class="tabs" role="tablist">
        <button type="button" class="tab" :class="{ active: type === 'SALE' }" role="tab" :aria-selected="type === 'SALE'" @click="switchType('SALE')">
          Retur penjualan
        </button>
        <button type="button" class="tab" :class="{ active: type === 'PURCHASE' }" role="tab" :aria-selected="type === 'PURCHASE'" @click="switchType('PURCHASE')">
          Retur pembelian
        </button>
      </div>

      <div v-if="formError" class="alert alert-error" role="alert">{{ formError }}</div>

      <section class="card card-body">
        <form v-if="type === 'SALE'" class="filter-bar" @submit.prevent="findSale">
          <label class="field">
            <span class="label">Nomor invoice transaksi <span class="req">*</span></span>
            <input v-model="invoiceNumber" class="input mono" placeholder="TRX-20260928-0001">
          </label>
          <div class="field">
            <button type="submit" class="btn btn-secondary" :disabled="loading">{{ loading ? 'Mencari…' : 'Cari transaksi' }}</button>
          </div>
          <div v-if="sale" class="field small">
            <span class="muted">Transaksi</span>
            <span>{{ formatDateTime(sale.createdAt) }} · {{ formatCurrency(sale.total) }}</span>
          </div>
        </form>

        <label v-else class="field">
          <span class="label">Penerimaan barang (Goods Receipt) <span class="req">*</span></span>
          <select v-model="receiptId" class="select" @change="setLinesFromReceipt">
            <option value="" disabled>Pilih penerimaan</option>
            <option v-for="receipt in receipts" :key="receipt.id" :value="receipt.id">
              {{ receipt.receiptNumber }} · {{ receipt.supplierName || receipt.supplierId }} · {{ formatDateTime(receipt.receivedAt) }}
            </option>
          </select>
        </label>
      </section>

      <section v-if="lines.length" class="card">
        <div class="card-header"><h2 class="card-title">Pilih item & jumlah retur</h2></div>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>Produk</th>
                <th class="num">Bisa diretur</th>
                <th class="num">Harga</th>
                <th class="num" style="width: 140px">Jumlah retur</th>
                <th class="num">Subtotal</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="line in lines" :key="line.productId">
                <td>{{ line.name }}<div class="mono muted">{{ line.sku }}</div></td>
                <td class="num">{{ formatNumber(line.maxQuantity) }}</td>
                <td class="num">{{ formatCurrency(line.price) }}</td>
                <td class="num">
                  <input
                    v-model.number="line.quantity"
                    type="number"
                    min="0"
                    :max="line.maxQuantity"
                    :step="type === 'PURCHASE' ? 1 : 'any'"
                    class="input num"
                    :aria-label="`Jumlah retur ${line.name}`"
                  >
                </td>
                <td class="num">{{ formatCurrency(line.price * (line.quantity || 0)) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr><td colspan="4">Total nilai retur</td><td class="num">{{ formatCurrency(totalAmount) }}</td></tr>
            </tfoot>
          </table>
        </div>
        <div class="card-body">
          <div class="form-grid cols-2">
            <label class="field">
              <span class="label">Alasan <span class="req">*</span></span>
              <select v-model="reason" class="select">
                <option v-for="[value, label] in reasons" :key="value" :value="value">{{ label }}</option>
              </select>
            </label>
            <label class="field">
              <span class="label">Catatan</span>
              <input v-model="notes" class="input" maxlength="1000">
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <RouterLink to="/returns" class="btn btn-secondary">Batal</RouterLink>
          <button type="button" class="btn btn-primary" :disabled="saving" @click="submit">
            {{ saving ? 'Mengirim…' : 'Ajukan retur' }}
          </button>
        </div>
      </section>
    </div>
  </main>
</template>
