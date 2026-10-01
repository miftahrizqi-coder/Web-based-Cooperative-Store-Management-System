<script setup lang="ts">
import type { GroupBy } from '../../types/report'
import { firstDayOfMonth, toDateInput } from '../../utils/format'

const model = defineModel<{ dateFrom: string; dateTo: string; groupBy?: GroupBy }>({ required: true })
defineProps<{ showGroupBy?: boolean; loading?: boolean }>()
const emit = defineEmits<{ (e: 'apply'): void }>()

function preset(kind: 'today' | 'week' | 'month' | 'year') {
  const now = new Date()
  let from = new Date(now)
  if (kind === 'week') from.setDate(now.getDate() - 6)
  if (kind === 'month') from = new Date(firstDayOfMonth())
  if (kind === 'year') from = new Date(now.getFullYear(), 0, 1)
  model.value = { ...model.value, dateFrom: toDateInput(from), dateTo: toDateInput(now) }
  emit('apply')
}
</script>

<template>
  <form class="card card-body no-print" @submit.prevent="emit('apply')">
    <div class="filter-bar">
      <label class="field">
        <span class="label">Dari</span>
        <input v-model="model.dateFrom" type="date" class="input">
      </label>
      <label class="field">
        <span class="label">Sampai</span>
        <input v-model="model.dateTo" type="date" class="input">
      </label>
      <label v-if="showGroupBy" class="field">
        <span class="label">Kelompokkan per</span>
        <select v-model="model.groupBy" class="select">
          <option value="day">Hari</option>
          <option value="week">Minggu</option>
          <option value="month">Bulan</option>
        </select>
      </label>
      <slot />
      <div class="field">
        <button type="submit" class="btn btn-primary" :disabled="loading">{{ loading ? 'Memuat…' : 'Tampilkan' }}</button>
      </div>
    </div>
    <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px">
      <button type="button" class="btn btn-ghost btn-sm" @click="preset('today')">Hari ini</button>
      <button type="button" class="btn btn-ghost btn-sm" @click="preset('week')">7 hari</button>
      <button type="button" class="btn btn-ghost btn-sm" @click="preset('month')">Bulan ini</button>
      <button type="button" class="btn btn-ghost btn-sm" @click="preset('year')">Tahun ini</button>
    </div>
  </form>
</template>
