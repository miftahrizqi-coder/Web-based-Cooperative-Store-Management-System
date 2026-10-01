<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { createGoodsReceipt, getPurchaseOrder, getPurchaseOrders } from '../../api/procurement'
import { errorMessage } from '../../services/api'
import { useAuth } from '../../stores/auth'
import type { PurchaseOrder } from '../../types/procurement'
import { formatCurrency, formatDate, formatNumber } from '../../utils/format'

/**
 * Penerimaan barang (PRD §15, BR-05, BR-06):
 * - bisa diterima sebagian; sisa tetap terbuka (PARTIALLY_RECEIVED),
 * - hanya jumlah "diterima baik" (accepted) yang menambah stok,
 * - barang ditolak wajib diberi alasan.
 */
interface Line {
  productId: string
  sku: string
  name: string
  ordered: number
  received: number
  remaining: number
  unitPrice: number
  receivedQuantity: number
  acceptedQuantity: number
  rejectionReason: string
}

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const openOrders = ref<PurchaseOrder[]>([])
const selectedPoId = ref(typeof route.params.id === 'string' ? route.params.id : '')
const po = ref<PurchaseOrder | null>(null)
const lines = reactive<Line[]>([])
const notes = ref('')
const isLoading = ref(true)
const saving = ref(false)
const formError = ref('')

const receivableStatuses = ['ORDERED', 'PARTIALLY_RECEIVED']
const canReceive = computed(() => Boolean(po.value && receivableStatuses.includes(po.value.status)))
const activeLines = computed(() => lines.filter((line) => line.receivedQuantity > 0))
const totals = computed(() => ({
  received: activeLines.value.reduce((sum, l) => sum + l.receivedQuantity, 0),
  accepted: activeLines.value.reduce((sum, l) => sum + l.acceptedQuantity, 0),
}))

function rejected(line: Line): number {
  return Math.max((line.receivedQuantity || 0) - (line.acceptedQuantity || 0), 0)
}

function lineError(line: Line): string {
  if (!line.receivedQuantity) return ''
  if (!Number.isInteger(line.receivedQuantity) || line.receivedQuantity < 0) return 'Jumlah harus bilangan bulat ≥ 0.'
  if (line.receivedQuantity > line.remaining) return `Melebihi sisa PO (${line.remaining}).`
  if (line.acceptedQuantity > line.receivedQuantity || line.acceptedQuantity < 0) return 'Diterima baik tidak boleh melebihi jumlah datang.'
  if (rejected(line) > 0 && !line.rejectionReason.trim()) return 'Alasan penolakan wajib diisi.'
  return ''
}

function setReceived(line: Line, value: number) {
  line.receivedQuantity = value
  line.acceptedQuantity = value
}

function receiveAllRemaining() {
  for (const line of lines) setReceived(line, line.remaining)
}

async function loadPo(id: string) {
  formError.value = ''
  lines.splice(0)
  po.value = null
  if (!id) return
  try {
    po.value = await getPurchaseOrder(token.value ?? '', id)
    for (const item of po.value.items) {
      const received = item.receivedQuantity ?? 0
      const remaining = item.remainingQuantity ?? Math.max(item.quantity - received, 0)
      if (remaining <= 0) continue
      lines.push({
        productId: item.productId,
        sku: item.sku,
        name: item.name,
        ordered: item.quantity,
        received,
        remaining,
        unitPrice: item.unitPrice,
        receivedQuantity: 0,
        acceptedQuantity: 0,
        rejectionReason: '',
      })
    }
  } catch (error) {
    formError.value = errorMessage(error, 'Gagal memuat Purchase Order.')
  }
}

async function selectPo() {
  await router.replace(selectedPoId.value ? `/goods-receipts/create/${selectedPoId.value}` : '/goods-receipts/create')
  await loadPo(selectedPoId.value)
}

async function submit() {
  formError.value = ''
  if (!po.value) return
  if (activeLines.value.length === 0) {
    formError.value = 'Isi jumlah barang datang minimal untuk satu produk.'
    return
  }
  const invalid = activeLines.value.find((line) => lineError(line))
  if (invalid) {
    formError.value = `${invalid.name}: ${lineError(invalid)}`
    return
  }
  saving.value = true
  try {
    const receipt = await createGoodsReceipt(token.value ?? '', {
      purchaseOrderId: po.value.id,
      notes: notes.value.trim() || null,
      items: activeLines.value.map((line) => ({
        productId: line.productId,
        name: line.name,
        receivedQuantity: line.receivedQuantity,
        acceptedQuantity: line.acceptedQuantity,
        rejectedQuantity: rejected(line),
        rejectionReason: rejected(line) > 0 ? line.rejectionReason.trim() : null,
      })),
    })
    await router.push(`/goods-receipts/${receipt.id}`)
  } catch (error) {
    formError.value = errorMessage(error, 'Gagal menyimpan penerimaan barang.')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const orders = await getPurchaseOrders(token.value ?? '')
    openOrders.value = orders.filter((order) => receivableStatuses.includes(order.status))
  } catch (error) {
    formError.value = errorMessage(error, 'Gagal memuat daftar PO.')
  }
  await loadPo(selectedPoId.value)
  isLoading.value = false
})
</script>

<template>
  <main class="page">
    <div class="page-inner">
      <header class="page-header">
        <div>
          <nav class="breadcrumb" aria-label="Breadcrumb">
            <RouterLink to="/goods-receipts">Penerimaan Barang</RouterLink><span>/</span><span aria-current="page">Terima barang</span>
          </nav>
          <h1 class="page-title">Terima barang</h1>
          <p class="page-subtitle">
            Catat barang yang datang dari supplier. Hanya jumlah yang diterima baik yang menambah stok; penerimaan boleh sebagian.
          </p>
        </div>
      </header>

      <div v-if="formError" class="alert alert-error" role="alert">{{ formError }}</div>

      <section class="card card-body">
        <label class="field">
          <span class="label">Purchase Order <span class="req">*</span></span>
          <select v-model="selectedPoId" class="select" :disabled="isLoading" @change="selectPo">
            <option value="">Pilih PO berstatus Dipesan / Sebagian diterima</option>
            <option v-for="order in openOrders" :key="order.id" :value="order.id">
              {{ order.poNumber }} · {{ order.supplierName || order.supplierId }} · {{ order.status === 'ORDERED' ? 'Dipesan' : 'Sebagian diterima' }}
            </option>
          </select>
          <span v-if="!isLoading && openOrders.length === 0" class="hint">
            Tidak ada PO yang menunggu penerimaan. PO harus disetujui lalu ditandai "sudah dipesan".
          </span>
        </label>
      </section>

      <template v-if="po">
        <div v-if="!canReceive" class="alert alert-warning">
          PO {{ po.poNumber }} berstatus {{ po.status }} dan tidak dapat menerima barang.
        </div>

        <section class="card">
          <div class="card-header">
            <div>
              <h2 class="card-title">{{ po.poNumber }} · {{ po.supplierName || po.supplierId }}</h2>
              <p class="card-subtitle">
                Estimasi kirim {{ formatDate(po.expectedDeliveryDate) }} · Nilai PO {{ formatCurrency(po.grandTotal) }}
              </p>
            </div>
            <button v-if="canReceive && lines.length" type="button" class="btn btn-secondary btn-sm" @click="receiveAllRemaining">
              Isi semua sisa
            </button>
          </div>

          <div v-if="lines.length === 0" class="empty">Semua item PO sudah diterima.</div>
          <div v-else class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Produk</th>
                  <th class="num">Dipesan</th>
                  <th class="num">Sudah diterima</th>
                  <th class="num">Sisa</th>
                  <th class="num" style="width: 120px">Datang</th>
                  <th class="num" style="width: 120px">Diterima baik</th>
                  <th class="num">Ditolak</th>
                  <th style="min-width: 200px">Alasan penolakan</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="line in lines" :key="line.productId">
                  <td>{{ line.name }}<div class="mono muted">{{ line.sku }}</div></td>
                  <td class="num">{{ formatNumber(line.ordered) }}</td>
                  <td class="num">{{ formatNumber(line.received) }}</td>
                  <td class="num strong">{{ formatNumber(line.remaining) }}</td>
                  <td>
                    <input
                      :value="line.receivedQuantity"
                      type="number"
                      min="0"
                      :max="line.remaining"
                      step="1"
                      class="input num"
                      :disabled="!canReceive"
                      :aria-label="`Jumlah datang ${line.name}`"
                      @input="setReceived(line, Number(($event.target as HTMLInputElement).value) || 0)"
                    >
                  </td>
                  <td>
                    <input
                      v-model.number="line.acceptedQuantity"
                      type="number"
                      min="0"
                      :max="line.receivedQuantity"
                      step="1"
                      class="input num"
                      :disabled="!canReceive || !line.receivedQuantity"
                      :aria-label="`Diterima baik ${line.name}`"
                    >
                  </td>
                  <td class="num" :class="{ 'text-danger strong': rejected(line) > 0 }">{{ formatNumber(rejected(line)) }}</td>
                  <td>
                    <input
                      v-if="rejected(line) > 0"
                      v-model="line.rejectionReason"
                      class="input"
                      maxlength="500"
                      placeholder="Mis. kemasan rusak"
                      :aria-label="`Alasan penolakan ${line.name}`"
                    >
                    <span v-else class="muted small">—</span>
                    <div v-if="lineError(line)" class="small text-danger" style="margin-top: 4px">{{ lineError(line) }}</div>
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td colspan="4">Total penerimaan ini</td>
                  <td class="num">{{ formatNumber(totals.received) }}</td>
                  <td class="num">{{ formatNumber(totals.accepted) }}</td>
                  <td class="num">{{ formatNumber(totals.received - totals.accepted) }}</td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>

          <div v-if="lines.length" class="card-body">
            <label class="field">
              <span class="label">Catatan penerimaan</span>
              <textarea v-model="notes" class="textarea" maxlength="1000" placeholder="Mis. 2 dus penyok, sisa dikirim minggu depan" />
            </label>
          </div>
          <div v-if="lines.length" class="modal-footer">
            <RouterLink :to="`/purchase-orders/${po.id}`" class="btn btn-secondary">Kembali ke PO</RouterLink>
            <button type="button" class="btn btn-primary" :disabled="saving || !canReceive" @click="submit">
              {{ saving ? 'Menyimpan…' : 'Simpan penerimaan' }}
            </button>
          </div>
        </section>
      </template>
    </div>
  </main>
</template>
