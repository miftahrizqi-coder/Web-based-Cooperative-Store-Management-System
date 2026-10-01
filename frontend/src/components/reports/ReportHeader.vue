<script setup lang="ts">
defineProps<{ title: string; subtitle?: string; canExport?: boolean }>()
const emit = defineEmits<{ (e: 'export'): void }>()

function print() {
  window.print()
}
</script>

<template>
  <header class="page-header">
    <div>
      <nav class="breadcrumb no-print" aria-label="Breadcrumb">
        <span>Laporan</span><span>/</span><span aria-current="page">{{ title }}</span>
      </nav>
      <h1 class="page-title">{{ title }}</h1>
      <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
    </div>
    <div class="header-actions no-print">
      <button type="button" class="btn btn-secondary" :disabled="!canExport" @click="emit('export')">Ekspor CSV (Excel)</button>
      <button type="button" class="btn btn-secondary" :disabled="!canExport" @click="print">Cetak / PDF</button>
    </div>
  </header>
</template>
