<script setup lang="ts">
import { PAYMENT_METHOD_LABELS, type Sale } from '../../types/sale'
import { formatCurrency, formatDateTime, formatNumber } from '../../utils/format'

defineProps<{ sale: Sale }>()
</script>

<template>
  <div class="receipt">
    <div class="center strong">TOKO KOPERASI</div>
    <div class="center">Struk Penjualan</div>
    <hr>
    <div class="row"><span>No</span><span>{{ sale.invoiceNumber }}</span></div>
    <div class="row"><span>Tanggal</span><span>{{ formatDateTime(sale.createdAt) }}</span></div>
    <div class="row"><span>Kasir</span><span>{{ sale.cashierName || '-' }}</span></div>
    <div v-if="sale.memberNumber" class="row"><span>Anggota</span><span>{{ sale.memberNumber }}</span></div>
    <hr>
    <div v-for="item in sale.items" :key="item.productId">
      <div>{{ item.name }}</div>
      <div class="row">
        <span>{{ formatNumber(item.quantity) }} x {{ formatCurrency(item.price) }}</span>
        <span>{{ formatCurrency(item.subtotal) }}</span>
      </div>
    </div>
    <hr>
    <div class="row"><span>Subtotal</span><span>{{ formatCurrency(sale.subtotal) }}</span></div>
    <div v-if="sale.discount > 0" class="row"><span>Diskon</span><span>-{{ formatCurrency(sale.discount) }}</span></div>
    <div class="row strong"><span>Total</span><span>{{ formatCurrency(sale.total) }}</span></div>
    <div class="row"><span>{{ PAYMENT_METHOD_LABELS[sale.payment.method] }}</span><span>{{ formatCurrency(sale.payment.amount) }}</span></div>
    <div class="row"><span>Kembali</span><span>{{ formatCurrency(sale.payment.change) }}</span></div>
    <hr>
    <div v-if="sale.status === 'CANCELLED'" class="center strong">*** TRANSAKSI DIBATALKAN ***</div>
    <div class="center">Terima kasih telah berbelanja</div>
  </div>
</template>
