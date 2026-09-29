<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { getActivities } from '../../api/procurement'

import type {
  Activity,
  ActivityEntityType,
  ActivityType,
} from '../../types/procurement'

const activities = ref<Activity[]>([])
const loading = ref(true)
const error = ref('')

const entityType = ref<ActivityEntityType | ''>('')
const activityType = ref<ActivityType | ''>('')

const entityLabels: Record<ActivityEntityType, string> = {
  PURCHASE_ORDER: 'Purchase Order',
  GOODS_RECEIPT: 'Goods Receipt',
  PURCHASE: 'Purchase',
  SUPPLIER_INVOICE: 'Supplier Invoice',
  SUPPLIER_PAYMENT: 'Supplier Payment',
}

const activityLabels: Record<ActivityType, string> = {
  CREATED: 'Dibuat',
  UPDATED: 'Diperbarui',
  SUBMITTED: 'Diajukan',
  APPROVED: 'Disetujui',
  ORDERED: 'Ordered',
  CANCELLED: 'Dibatalkan',
}

function getToken(): string {
  const token = localStorage.getItem('access_token')

  if (!token) {
    throw new Error('Sesi login tidak ditemukan.')
  }

  return token
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

async function loadActivities() {
  loading.value = true
  error.value = ''

  try {
    activities.value = await getActivities(
      getToken(),
      {
        entityType:
          entityType.value || undefined,
        activityType:
          activityType.value || undefined,
      },
    )
  } catch (err) {
    error.value =
      err instanceof Error
        ? err.message
        : 'Gagal memuat Activity Timeline.'
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  entityType.value = ''
  activityType.value = ''
}

watch(
  [entityType, activityType],
  () => {
    void loadActivities()
  },
)

onMounted(() => {
  void loadActivities()
})
</script>

<template>
  <section class="space-y-6">
    <div>
      <h1 class="text-2xl font-semibold text-slate-900">
        Activity Timeline
      </h1>

      <p class="mt-1 text-sm text-slate-600">
        Riwayat aktivitas procurement.
      </p>
    </div>

    <div
      class="grid gap-4 rounded-xl border border-slate-200 bg-white p-4 md:grid-cols-3"
    >
      <div>
        <label
          for="entity-type"
          class="mb-1 block text-sm font-medium text-slate-700"
        >
          Jenis data
        </label>

        <select
          id="entity-type"
          v-model="entityType"
          class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
        >
          <option value="">Semua</option>

          <option
            v-for="(label, value) in entityLabels"
            :key="value"
            :value="value"
          >
            {{ label }}
          </option>
        </select>
      </div>

      <div>
        <label
          for="activity-type"
          class="mb-1 block text-sm font-medium text-slate-700"
        >
          Aktivitas
        </label>

        <select
          id="activity-type"
          v-model="activityType"
          class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
        >
          <option value="">Semua</option>

          <option
            v-for="(label, value) in activityLabels"
            :key="value"
            :value="value"
          >
            {{ label }}
          </option>
        </select>
      </div>

      <div class="flex items-end">
        <button
          type="button"
          class="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          @click="resetFilters"
        >
          Reset Filter
        </button>
      </div>
    </div>

    <div
      v-if="loading"
      class="space-y-4"
      aria-live="polite"
    >
      <div
        v-for="index in 5"
        :key="index"
        class="animate-pulse rounded-xl border border-slate-200 bg-white p-5"
      >
        <div class="h-4 w-32 rounded bg-slate-200" />
        <div class="mt-3 h-4 w-3/4 rounded bg-slate-200" />
        <div class="mt-2 h-3 w-40 rounded bg-slate-200" />
      </div>
    </div>

    <div
      v-else-if="error"
      class="rounded-xl border border-red-200 bg-red-50 p-5"
    >
      <h2 class="font-semibold text-red-800">
        Activity Timeline gagal dimuat
      </h2>

      <p class="mt-1 text-sm text-red-700">
        {{ error }}
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800"
        @click="loadActivities"
      >
        Coba Lagi
      </button>
    </div>

    <div
      v-else-if="activities.length === 0"
      class="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center"
    >
      <h2 class="font-semibold text-slate-800">
        Belum ada aktivitas
      </h2>

      <p class="mt-1 text-sm text-slate-500">
        Tidak ada aktivitas yang sesuai dengan filter saat ini.
      </p>
    </div>

    <div
      v-else
      class="relative"
    >
      <div
        class="absolute bottom-0 left-3 top-0 w-px bg-slate-200"
        aria-hidden="true"
      />

      <div class="space-y-6">
        <article
          v-for="activity in activities"
          :key="activity.id"
          class="relative pl-8"
        >
          <div
            class="absolute left-0 top-1.5 h-2.5 w-2.5 rounded-full bg-slate-600 ring-4 ring-white"
            aria-hidden="true"
          />

          <div
            class="rounded-xl border border-slate-200 bg-white p-5"
          >
            <div
              class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between"
            >
              <div class="min-w-0">
                <div class="flex flex-wrap gap-2">
                  <span
                    class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700"
                  >
                    {{ entityLabels[activity.entityType] }}
                  </span>

                  <span
                    class="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700"
                  >
                    {{ activityLabels[activity.activityType] }}
                  </span>
                </div>

                <p class="mt-3 font-medium text-slate-900">
                  {{ activity.description }}
                </p>
              </div>

              <time
                class="shrink-0 text-xs text-slate-500"
                :datetime="activity.createdAt"
              >
                {{ formatDate(activity.createdAt) }}
              </time>
            </div>

            <div
              class="mt-4 flex flex-wrap gap-x-5 gap-y-2 border-t border-slate-100 pt-3 text-xs text-slate-500"
            >
              <span>
                Referensi:
                <strong class="font-medium text-slate-700">
                  {{ activity.referenceNumber || '-' }}
                </strong>
              </span>

              <span>
                Actor:
                <strong class="font-medium text-slate-700">
                  {{ activity.actorId }}
                </strong>
              </span>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>