<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const view = computed(() => {
  switch (props.status) {
    case 'OUT_OF_STOCK':
      return { label: 'Habis', cls: 'badge-danger' }
    case 'LOW_STOCK':
      return { label: 'Menipis', cls: 'badge-warning' }
    default:
      return { label: 'Tersedia', cls: 'badge-success' }
  }
})
</script>

<template>
  <span class="badge" :class="view.cls">{{ view.label }}</span>
</template>
