<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  page: number
  pageSize: number
  total: number
}>()

const emit = defineEmits<{ (e: 'update:page', value: number): void }>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const start = computed(() => (props.total === 0 ? 0 : (props.page - 1) * props.pageSize + 1))
const end = computed(() => Math.min(props.page * props.pageSize, props.total))

function go(page: number) {
  if (page >= 1 && page <= totalPages.value && page !== props.page) emit('update:page', page)
}
</script>

<template>
  <div class="pagination">
    <span>Menampilkan {{ start }}–{{ end }} dari {{ total }} data</span>
    <div class="pagination-buttons">
      <button type="button" class="btn btn-secondary btn-sm" :disabled="page <= 1" @click="go(page - 1)">
        Sebelumnya
      </button>
      <span class="btn btn-sm" aria-live="polite">{{ page }} / {{ totalPages }}</span>
      <button type="button" class="btn btn-secondary btn-sm" :disabled="page >= totalPages" @click="go(page + 1)">
        Berikutnya
      </button>
    </div>
  </div>
</template>
