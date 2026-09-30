<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { getActivities } from '../../api/procurement'

import type {
  Activity,
  ActivityEntityType,
  ActivityType,
} from '../../types/procurement'

/**
 * Catatan token (DESIGN.md §3):
 * Warna ditulis sebagai arbitrary value Tailwind agar langsung bekerja
 * tanpa mengubah tailwind.config.
 *
 *  primary-900 #12372A | primary-700 #176B4D | primary-600 #1F805D
 *  primary-100 #DCEFE7 | primary-50 #F0F8F5
 *  neutral-950 #17201C | neutral-700 #46514B | neutral-500 #6B756F
 *  neutral-300 #D6DDD9 | neutral-200 #E6EBE8 | neutral-100 #F1F4F2 | neutral-50 #F8FAF9
 *  success #16834B | warning #B7791F (teks #7A4F0F) | danger #C0392B (teks #8E2A20) | info #2874A6
 */

const PAGE_SIZE = 30

const activities = ref<Activity[]>([])
const loading = ref(true)
const error = ref('')

const entityType = ref<ActivityEntityType | ''>('')
const activityType = ref<ActivityType | ''>('')
const search = ref('')
const visibleCount = ref(PAGE_SIZE)

let requestId = 0

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
  ORDERED: 'Dipesan',
  CANCELLED: 'Dibatalkan',
}

/* ------------------------------------------------------------------ */
/* Data                                                                */
/* ------------------------------------------------------------------ */

function getToken(): string {
  const token = localStorage.getItem('access_token')

  if (!token) {
    throw new Error('Sesi login tidak ditemukan.')
  }

  return token
}

async function loadActivities() {
  const current = ++requestId

  loading.value = true
  error.value = ''

  try {
    const result = await getActivities(getToken(), {
      entityType: entityType.value || undefined,
      activityType: activityType.value || undefined,
    })

    // Abaikan respons lama bila filter sudah berubah lagi.
    if (current === requestId) {
      activities.value = result
    }
  } catch (err) {
    if (current === requestId) {
      error.value =
        err instanceof Error
          ? err.message
          : 'Gagal memuat Activity Timeline.'
    }
  } finally {
    if (current === requestId) {
      loading.value = false
    }
  }
}

function resetFilters() {
  entityType.value = ''
  activityType.value = ''
  search.value = ''
}

const hasActiveFilter = computed(
  () =>
    entityType.value !== '' ||
    activityType.value !== '' ||
    search.value.trim() !== '',
)

watch([entityType, activityType], () => {
  visibleCount.value = PAGE_SIZE
  void loadActivities()
})

watch(search, () => {
  visibleCount.value = PAGE_SIZE
})

/* ------------------------------------------------------------------ */
/* Turunan: filter, urutan terbaru, grup per hari                      */
/* ------------------------------------------------------------------ */

const filteredActivities = computed(() => {
  const keyword = search.value.trim().toLowerCase()

  return [...activities.value]
    .filter((activity) => {
      if (!keyword) return true

      return (
        (activity.description ?? '').toLowerCase().includes(keyword) ||
        (activity.referenceNumber ?? '').toLowerCase().includes(keyword) ||
        String(activity.actorId ?? '').toLowerCase().includes(keyword)
      )
    })
    .sort(
      (a, b) =>
        new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    )
})

const visibleActivities = computed(() =>
  filteredActivities.value.slice(0, visibleCount.value),
)

const hasMore = computed(
  () => filteredActivities.value.length > visibleCount.value,
)

function dateKey(value: string): string {
  const date = new Date(value)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${date.getFullYear()}-${month}-${day}`
}

function dayHeading(key: string): string {
  const now = new Date()
  const yesterday = new Date()
  yesterday.setDate(now.getDate() - 1)

  const [year, month, day] = key.split('-').map(Number)
  const full = new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'full',
  }).format(new Date(year, month - 1, day))

  if (key === dateKey(now.toISOString())) return `Hari ini — ${full}`
  if (key === dateKey(yesterday.toISOString())) return `Kemarin — ${full}`

  return full
}

const groups = computed(() => {
  const map = new Map<string, Activity[]>()

  for (const activity of visibleActivities.value) {
    const key = dateKey(activity.createdAt)
    const list = map.get(key)

    if (list) {
      list.push(activity)
    } else {
      map.set(key, [activity])
    }
  }

  return [...map.entries()].map(([key, items]) => ({
    key,
    heading: dayHeading(key),
    items,
  }))
})

/* ------------------------------------------------------------------ */
/* Tampilan                                                            */
/* ------------------------------------------------------------------ */

function formatTime(value: string): string {
  return new Intl.DateTimeFormat('id-ID', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatFull(value: string): string {
  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'full',
    timeStyle: 'medium',
  }).format(new Date(value))
}

type Semantic = 'success' | 'warning' | 'danger' | 'info' | 'neutral'

function activitySemantic(type: ActivityType): Semantic {
  switch (type) {
    case 'APPROVED':
      return 'success'
    case 'SUBMITTED':
      return 'warning'
    case 'CANCELLED':
      return 'danger'
    case 'ORDERED':
    case 'CREATED':
      return 'info'
    default:
      return 'neutral'
  }
}

/** Badge selalu memuat label teks + ikon bentuk; warna bukan satu-satunya penanda. */
function badgeClass(semantic: Semantic): string {
  switch (semantic) {
    case 'success':
      return 'border-[#16834B]/25 bg-[#DCEFE7] text-[#12372A]'
    case 'warning':
      return 'border-[#B7791F]/30 bg-[#FBF3E2] text-[#7A4F0F]'
    case 'danger':
      return 'border-[#C0392B]/25 bg-[#FBEDEB] text-[#8E2A20]'
    case 'info':
      return 'border-[#2874A6]/25 bg-[#EAF3F9] text-[#1B5478]'
    default:
      return 'border-[#D6DDD9] bg-[#F1F4F2] text-[#46514B]'
  }
}

function markerClass(semantic: Semantic): string {
  switch (semantic) {
    case 'success':
      return 'bg-[#16834B]'
    case 'warning':
      return 'bg-[#B7791F]'
    case 'danger':
      return 'bg-[#C0392B]'
    case 'info':
      return 'bg-[#2874A6]'
    default:
      return 'bg-[#6B756F]'
  }
}

function entityText(type: ActivityEntityType): string {
  return entityLabels[type] ?? type
}

function activityText(type: ActivityType): string {
  return activityLabels[type] ?? type
}

onMounted(() => {
  void loadActivities()
})
</script>

<template>
  <section class="space-y-6 text-[#17201C]">
    <!-- Header: Breadcrumb -> Title -> Context -->
    <header class="space-y-3">
      <nav
        aria-label="Breadcrumb"
        class="text-[13px] leading-[18px] text-[#6B756F]"
      >
        <ol class="flex items-center gap-1.5">
          <li>Procurement</li>
          <li aria-hidden="true">/</li>
          <li
            aria-current="page"
            class="font-medium text-[#46514B]"
          >
            Activity Timeline
          </li>
        </ol>
      </nav>

      <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 class="text-[28px] font-semibold leading-9">
            Activity Timeline
          </h1>

          <p class="mt-1 max-w-2xl text-sm leading-5 text-[#46514B]">
            Riwayat aktivitas procurement, dari yang terbaru. Setiap
            perubahan tercatat sebagai kejadian baru dan tidak dapat
            diubah.
          </p>
        </div>

        <button
          type="button"
          class="focus-ring inline-flex min-h-10 shrink-0 items-center justify-center gap-2 rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-semibold hover:bg-[#F1F4F2] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="loading"
          @click="loadActivities"
        >
          <svg
            class="h-4 w-4"
            :class="loading ? 'animate-spin' : ''"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M16 10a6 6 0 1 1-1.8-4.3M16 3.5V6h-2.5" />
          </svg>
          Muat ulang
        </button>
      </div>
    </header>

    <!-- Filter bar -->
    <div class="rounded-lg border border-[#D6DDD9] bg-white p-4">
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)_auto]">
        <div>
          <label
            for="activity-search"
            class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]"
          >
            Cari aktivitas
          </label>

          <div class="relative">
            <svg
              class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6B756F]"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              aria-hidden="true"
            >
              <circle cx="9" cy="9" r="5.5" />
              <path d="m13 13 4 4" />
            </svg>

            <input
              id="activity-search"
              v-model="search"
              type="search"
              autocomplete="off"
              placeholder="Deskripsi, nomor referensi, atau pelaku"
              class="focus-ring min-h-11 w-full rounded-lg border border-[#D6DDD9] bg-white pl-9 pr-3 text-sm text-[#17201C] placeholder:text-[#6B756F] outline-none focus:border-[#176B4D]"
            />
          </div>
        </div>

        <div>
          <label
            for="entity-type"
            class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]"
          >
            Jenis data
          </label>

          <select
            id="entity-type"
            v-model="entityType"
            class="focus-ring min-h-11 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm text-[#17201C] outline-none focus:border-[#176B4D]"
          >
            <option value="">Semua jenis data</option>

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
            class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]"
          >
            Aktivitas
          </label>

          <select
            id="activity-type"
            v-model="activityType"
            class="focus-ring min-h-11 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm text-[#17201C] outline-none focus:border-[#176B4D]"
          >
            <option value="">Semua aktivitas</option>

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
            class="focus-ring min-h-11 w-full rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-semibold text-[#17201C] hover:bg-[#F1F4F2] disabled:cursor-not-allowed disabled:opacity-50 xl:w-auto"
            :disabled="!hasActiveFilter"
            @click="resetFilters"
          >
            Reset filter
          </button>
        </div>
      </div>

      <p
        v-if="!loading && !error"
        role="status"
        aria-live="polite"
        class="mt-3 text-[13px] tabular-nums text-[#46514B]"
      >
        <span class="font-medium text-[#17201C]">{{ filteredActivities.length }}</span>
        aktivitas
        <template v-if="hasActiveFilter">
          sesuai filter
        </template>
      </p>
    </div>

    <!-- Loading: skeleton -->
    <div
      v-if="loading"
      role="status"
      aria-busy="true"
      class="rounded-lg border border-[#D6DDD9] bg-white p-5"
    >
      <span class="sr-only">Memuat aktivitas...</span>

      <div class="h-4 w-56 animate-pulse rounded bg-[#E6EBE8]" />

      <div class="mt-5 space-y-6 border-l-2 border-[#E6EBE8] pl-6">
        <div
          v-for="index in 5"
          :key="index"
          class="space-y-2"
        >
          <div class="flex gap-2">
            <div class="h-5 w-20 animate-pulse rounded-full bg-[#E6EBE8]" />
            <div class="h-5 w-28 animate-pulse rounded-full bg-[#F1F4F2]" />
          </div>
          <div class="h-4 w-3/4 animate-pulse rounded bg-[#E6EBE8]" />
          <div class="h-3 w-1/3 animate-pulse rounded bg-[#F1F4F2]" />
        </div>
      </div>
    </div>

    <!-- Error: apa yang gagal, apakah data berubah, apa yang bisa dilakukan -->
    <div
      v-else-if="error"
      role="alert"
      class="rounded-lg border border-[#C0392B]/30 bg-[#FBEDEB] p-6"
    >
      <h2 class="text-base font-semibold text-[#8E2A20]">
        Activity Timeline tidak dapat dimuat
      </h2>

      <p class="mt-1 text-sm text-[#8E2A20]">
        {{ error }}
      </p>

      <p class="mt-1 text-sm text-[#46514B]">
        Halaman ini hanya menampilkan riwayat, jadi tidak ada data yang
        berubah. Periksa koneksi Anda, lalu coba lagi.
      </p>

      <button
        type="button"
        class="focus-ring mt-4 min-h-11 rounded-lg border border-[#C0392B]/40 bg-white px-4 text-sm font-semibold text-[#8E2A20] hover:bg-[#FBEDEB]"
        @click="loadActivities"
      >
        Coba lagi
      </button>
    </div>

    <!-- Empty: belum ada aktivitas sama sekali -->
    <div
      v-else-if="activities.length === 0 && !hasActiveFilter"
      class="rounded-lg border border-dashed border-[#D6DDD9] bg-white px-6 py-12 text-center"
    >
      <div
        class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#F0F8F5] text-[#176B4D]"
        aria-hidden="true"
      >
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="8.5" />
          <path d="M12 7.5V12l3 2" />
        </svg>
      </div>

      <h2 class="mt-4 text-base font-semibold">
        Belum ada aktivitas procurement
      </h2>

      <p class="mx-auto mt-1 max-w-md text-sm text-[#46514B]">
        Aktivitas muncul otomatis saat purchase order, penerimaan
        barang, invoice, atau pembayaran supplier dibuat dan diubah.
        Buat purchase order pertama untuk mulai mencatat riwayat.
      </p>
    </div>

    <!-- Empty: filter / pencarian tanpa hasil -->
    <div
      v-else-if="filteredActivities.length === 0"
      class="rounded-lg border border-[#D6DDD9] bg-white px-6 py-12 text-center"
    >
      <h2 class="text-base font-semibold">
        Tidak ada aktivitas yang cocok
      </h2>

      <p class="mx-auto mt-1 max-w-md text-sm text-[#46514B]">
        Tidak ada aktivitas untuk kombinasi pencarian dan filter saat
        ini. Periksa ejaan atau longgarkan filter.
      </p>

      <button
        type="button"
        class="focus-ring mt-5 min-h-11 rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-semibold hover:bg-[#F1F4F2]"
        @click="resetFilters"
      >
        Reset filter
      </button>
    </div>

    <!-- Timeline per hari -->
    <div
      v-else
      class="space-y-8"
    >
      <section
        v-for="group in groups"
        :key="group.key"
        :aria-labelledby="`day-${group.key}`"
      >
        <h2
          :id="`day-${group.key}`"
          class="mb-3 text-[13px] font-semibold leading-[18px] text-[#46514B]"
        >
          {{ group.heading }}
        </h2>

        <ol class="overflow-hidden rounded-lg border border-[#D6DDD9] bg-white">
          <li
            v-for="activity in group.items"
            :key="activity.id"
            class="relative flex gap-4 border-b border-[#E6EBE8] px-4 py-4 last:border-b-0 sm:gap-5 sm:px-5"
          >
            <!-- Waktu -->
            <time
              class="w-11 shrink-0 pt-0.5 text-[13px] font-medium leading-5 tabular-nums text-[#46514B]"
              :datetime="activity.createdAt"
              :title="formatFull(activity.createdAt)"
            >
              {{ formatTime(activity.createdAt) }}
              <span class="sr-only">, {{ formatFull(activity.createdAt) }}</span>
            </time>

            <!-- Marker timeline -->
            <div
              class="relative flex w-3 shrink-0 justify-center"
              aria-hidden="true"
            >
              <span
                class="absolute -bottom-4 -top-4 w-px bg-[#E6EBE8]"
              />
              <span
                class="relative mt-1.5 h-2.5 w-2.5 rounded-full ring-4 ring-white"
                :class="markerClass(activitySemantic(activity.activityType))"
              />
            </div>

            <!-- Kejadian: Aksi -> Objek -> Konteks -> Pelaku -->
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <span
                  class="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium"
                  :class="badgeClass(activitySemantic(activity.activityType))"
                >
                  <svg class="h-3 w-3" viewBox="0 0 12 12" aria-hidden="true">
                    <path
                      v-if="activitySemantic(activity.activityType) === 'success'"
                      d="m2.5 6.5 2.5 2.5 4.5-5.5"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.75"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                    <path
                      v-else-if="activitySemantic(activity.activityType) === 'warning'"
                      d="M6 1.5 11 10.5H1z"
                      fill="currentColor"
                    />
                    <path
                      v-else-if="activitySemantic(activity.activityType) === 'danger'"
                      d="M3 3l6 6M9 3l-6 6"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.75"
                      stroke-linecap="round"
                    />
                    <circle
                      v-else-if="activitySemantic(activity.activityType) === 'info'"
                      cx="6" cy="6" r="4" fill="currentColor"
                    />
                    <circle
                      v-else
                      cx="6" cy="6" r="3.25" fill="none" stroke="currentColor" stroke-width="1.5"
                    />
                  </svg>
                  {{ activityText(activity.activityType) }}
                </span>

                <span class="text-sm font-semibold">
                  {{ entityText(activity.entityType) }}
                </span>

                <span
                  v-if="activity.referenceNumber"
                  class="rounded border border-[#E6EBE8] bg-[#F8FAF9] px-1.5 py-0.5 text-[13px] font-medium tabular-nums text-[#17201C]"
                >
                  {{ activity.referenceNumber }}
                </span>
              </div>

              <p class="mt-1.5 text-sm leading-5 text-[#17201C]">
                {{ activity.description }}
              </p>

              <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                Oleh
                <span class="font-medium tabular-nums text-[#46514B]">{{ activity.actorId }}</span>
                <span v-if="!activity.referenceNumber">
                  — tanpa nomor referensi
                </span>
              </p>
            </div>
          </li>
        </ol>
      </section>

      <!-- Pagination -->
      <nav
        aria-label="Muat lebih banyak aktivitas"
        class="flex flex-col items-center gap-3 rounded-lg border border-[#D6DDD9] bg-[#F8FAF9] px-4 py-3 sm:flex-row sm:justify-between"
      >
        <p class="text-[13px] tabular-nums text-[#46514B]">
          Menampilkan
          <span class="font-medium text-[#17201C]">{{ visibleActivities.length }}</span>
          dari
          <span class="font-medium text-[#17201C]">{{ filteredActivities.length }}</span>
          aktivitas
        </p>

        <button
          v-if="hasMore"
          type="button"
          class="focus-ring min-h-11 rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-semibold hover:bg-[#F1F4F2]"
          @click="visibleCount += PAGE_SIZE"
        >
          Tampilkan {{ Math.min(PAGE_SIZE, filteredActivities.length - visibleCount) }} lagi
        </button>

        <p
          v-else
          class="text-[13px] text-[#6B756F]"
        >
          Semua aktivitas sudah ditampilkan.
        </p>
      </nav>
    </div>
  </section>
</template>

<style scoped>
/* Focus ring standar (DESIGN.md §13.2): 2px solid #176B4D, offset 2px */
.focus-ring:focus-visible {
  outline: 2px solid #176b4d;
  outline-offset: 2px;
}
</style>