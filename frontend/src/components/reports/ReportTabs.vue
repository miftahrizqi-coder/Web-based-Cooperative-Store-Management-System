<script setup lang="ts">
import { RouterLink } from 'vue-router'

const tabs = [
  { to: '/reports/sales', label: 'Penjualan' },
  { to: '/reports/purchases', label: 'Pembelian' },
  { to: '/reports/inventory', label: 'Inventory' },
  { to: '/reports/suppliers', label: 'Supplier' },
  { to: '/reports/payables', label: 'Hutang' },
  { to: '/reports/profit', label: 'Laba' },
]
</script>

<template>
  <nav class="tabs no-print" aria-label="Jenis laporan">
    <RouterLink v-for="tab in tabs" :key="tab.to" :to="tab.to" class="tab">{{ tab.label }}</RouterLink>
  </nav>
</template>
