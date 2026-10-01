<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getUser, resetUserPassword, updateUser } from '../../api/users'
import { getMembers } from '../../api/members'
import type { Member } from '../../types/member'
import type { UserRole } from '../../types/auth'
import { useAuth } from '../../stores/auth'

/* Sesuaikan dengan route daftar pengguna */
const USERS_ROUTE = '/users'

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const userId = route.params.id as string

/* ---------- State ---------- */
const username = ref('')
const name = ref('')
const email = ref('')
const role = ref<UserRole>('kasir')
const isActive = ref(true)
const memberId = ref('')
const members = ref<Member[]>([])
const resetPasswordValue = ref('')
const resetMessage = ref('')
const resetError = ref('')
const resetting = ref(false)

/* Data terakhir yang tersimpan di server, dipakai untuk membandingkan perubahan */
const original = ref<{
  name: string
  email: string
  role: string
  isActive: boolean
} | null>(null)

const isLoading = ref(true)
const isSaving = ref(false)

const loadError = ref('')
const submitError = ref('')
const errors = ref({ name: '', email: '', role: '' })

const showConfirmation = ref(false)
const submitButtonRef = ref<HTMLButtonElement | null>(null)
const dialogRef = ref<HTMLElement | null>(null)
const cancelButtonRef = ref<HTMLButtonElement | null>(null)

const roleOptions: Array<{ value: string; label: string }> = [
  { value: 'admin', label: 'Admin' },
  { value: 'kasir', label: 'Kasir' },
  { value: 'pengurus', label: 'Pengurus' },
  { value: 'anggota', label: 'Anggota' },
]

/* Rincian hak akses Kasir mengacu pada DESIGN.md §1.6 dan §14.
   Role lain mengikuti PRD §3, sehingga tidak dirinci di sini. */
const kasirCan = [
  'Membuat transaksi penjualan',
  'Mencari atau memindai produk',
  'Memilih member',
  'Menerima pembayaran dan mencetak struk',
  'Melihat transaksi miliknya sendiri',
]
const kasirCannot = [
  'Mengubah harga',
  'Mengubah stok manual (stock adjustment)',
  'Mengelola supplier',
  'Menghapus transaksi',
]

/* ---------- Derived ---------- */
function roleLabelOf(value: string): string {
  return roleOptions.find((o) => o.value === value)?.label ?? value
}

const roleLabel = computed(() => roleLabelOf(String(role.value)))

const statusText = (active: boolean) => (active ? 'Aktif' : 'Nonaktif')

const changes = computed(() => {
  const o = original.value
  if (!o) return []

  const list: Array<{ key: string; label: string; from: string; to: string }> = []

  if (name.value.trim() !== o.name) {
    list.push({ key: 'name', label: 'Nama', from: o.name, to: name.value.trim() || '(kosong)' })
  }
  if (email.value.trim() !== o.email) {
    list.push({ key: 'email', label: 'Email', from: o.email, to: email.value.trim() || '(kosong)' })
  }
  if (String(role.value) !== o.role) {
    list.push({ key: 'role', label: 'Role', from: roleLabelOf(o.role), to: roleLabel.value })
  }
  if (isActive.value !== o.isActive) {
    list.push({
      key: 'status',
      label: 'Status',
      from: statusText(o.isActive),
      to: statusText(isActive.value),
    })
  }
  return list
})

const isDirty = computed(() => changes.value.length > 0)

const isDeactivating = computed(() => !!original.value?.isActive && !isActive.value)
const isReactivating = computed(() => !!original.value && !original.value.isActive && isActive.value)
const isRoleChanging = computed(() => !!original.value && String(role.value) !== original.value.role)
const needsConfirmation = computed(() => isDeactivating.value || isRoleChanging.value)

const requirements = computed(() => [
  { label: 'Nama terisi', ok: name.value.trim().length > 0 },
  { label: 'Format email valid', ok: EMAIL_PATTERN.test(email.value.trim()) },
  { label: 'Role dipilih', ok: !!role.value },
])

function inputClass(hasError: boolean): string {
  return hasError ? 'border-[#C0392B]' : 'border-[#D6DDD9] focus:border-[#176B4D]'
}

/* ---------- Data ---------- */
async function loadUser() {
  isLoading.value = true
  loadError.value = ''

  if (!token.value) {
    loadError.value = 'Sesi login tidak ditemukan. Silakan masuk kembali.'
    isLoading.value = false
    return
  }

  try {
    const user = await getUser(token.value, userId)

    username.value = user.username
    name.value = user.name
    email.value = user.email
    role.value = user.role
    isActive.value = user.is_active
    memberId.value = user.memberId ?? ''
    try {
      members.value = await getMembers()
    } catch {
      members.value = []
    }

    original.value = {
      name: user.name.trim(),
      email: user.email.trim(),
      role: String(user.role),
      isActive: user.is_active,
    }
  } catch (error) {
    loadError.value =
      error instanceof Error ? error.message : 'Data pengguna tidak dapat diambil.'
  } finally {
    isLoading.value = false
  }
}

/* ---------- Validation ---------- */
const fieldOrder = ['name', 'email', 'role'] as const

function validateForm(): boolean {
  errors.value = { name: '', email: '', role: '' }

  if (!name.value.trim()) {
    errors.value.name = 'Nama wajib diisi.'
  }

  if (!email.value.trim()) {
    errors.value.email = 'Email wajib diisi.'
  } else if (!EMAIL_PATTERN.test(email.value.trim())) {
    errors.value.email = 'Format email tidak valid. Contoh: nama@koperasi.id'
  }

  if (role.value === 'anggota' && !memberId.value) {
    errors.value.role = 'Pilih data anggota yang ditautkan ke akun ini.'
  }

  if (!role.value) {
    errors.value.role = 'Role wajib dipilih.'
  }

  return !Object.values(errors.value).some(Boolean)
}

async function focusFirstInvalid() {
  await nextTick()
  const first = fieldOrder.find((key) => errors.value[key])
  if (first) document.getElementById(first)?.focus()
}

watch(name, () => (errors.value.name = ''))
watch(email, () => (errors.value.email = ''))
watch(role, () => (errors.value.role = ''))

/* ---------- Actions ---------- */
function handleCancel() {
  router.push(USERS_ROUTE)
}

function toggleActive() {
  isActive.value = !isActive.value
}

async function handleSubmit() {
  submitError.value = ''

  if (!validateForm()) {
    await focusFirstInvalid()
    return
  }

  if (!isDirty.value) return

  if (needsConfirmation.value) {
    showConfirmation.value = true
    return
  }

  await saveChanges()
}

function closeConfirmation() {
  if (isSaving.value) return
  showConfirmation.value = false
}

watch(showConfirmation, async (open) => {
  await nextTick()
  if (open) {
    cancelButtonRef.value?.focus()
  } else {
    submitButtonRef.value?.focus()
  }
})

function onDialogKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    e.preventDefault()
    closeConfirmation()
    return
  }

  if (e.key !== 'Tab' || !dialogRef.value) return

  const focusable = dialogRef.value.querySelectorAll<HTMLElement>(
    'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
  )
  if (focusable.length === 0) return

  const first = focusable[0]
  const last = focusable[focusable.length - 1]

  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault()
    first.focus()
  }
}

async function saveChanges() {
  if (!validateForm()) {
    showConfirmation.value = false
    await focusFirstInvalid()
    return
  }

  if (!token.value) {
    submitError.value = 'Sesi login tidak ditemukan. Silakan masuk kembali.'
    showConfirmation.value = false
    return
  }

  isSaving.value = true
  submitError.value = ''

  try {
    await updateUser(token.value, userId, {
      name: name.value.trim(),
      email: email.value.trim(),
      role: role.value,
      is_active: isActive.value,
      memberId: role.value === 'anggota' ? memberId.value || null : null,
    })

    await router.push(USERS_ROUTE)
  } catch (error) {
    const detail = error instanceof Error ? error.message : 'Terjadi kesalahan pada server.'
    submitError.value = `Perubahan gagal disimpan dan data pengguna tidak berubah. ${detail} Periksa data lalu coba lagi.`
    showConfirmation.value = false
  } finally {
    isSaving.value = false
  }
}

onMounted(loadUser)

async function handleResetPassword() {
  resetMessage.value = ''
  resetError.value = ''
  if (resetPasswordValue.value.length < 8) {
    resetError.value = 'Password baru minimal 8 karakter.'
    return
  }
  if (!window.confirm('Reset password pengguna ini? Pengguna harus login ulang dengan password baru.')) return
  resetting.value = true
  try {
    await resetUserPassword(userId, resetPasswordValue.value)
    resetPasswordValue.value = ''
    resetMessage.value = 'Password berhasil direset. Sampaikan password baru secara aman kepada pengguna.'
  } catch (error) {
    resetError.value = error instanceof Error ? error.message : 'Gagal mereset password.'
  } finally {
    resetting.value = false
  }
}
</script>

<template>
  <main class="mx-auto w-full max-w-[1440px] font-sans text-[#17201C]">
    <!-- Breadcrumb -->
    <nav aria-label="Breadcrumb" class="mb-3 text-[13px] leading-[18px] text-[#6B756F]">
      <ol class="flex items-center gap-2">
        <li>Administrasi</li>
        <li aria-hidden="true">/</li>
        <li>
          <router-link
            :to="USERS_ROUTE"
            class="rounded-sm hover:text-[#176B4D] hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          >
            Pengguna
          </router-link>
        </li>
        <li aria-hidden="true">/</li>
        <li aria-current="page" class="font-medium text-[#46514B]">Edit Pengguna</li>
      </ol>
    </nav>

    <!-- Page header -->
    <header class="mb-6">
      <div class="flex flex-wrap items-center gap-3">
        <h1 class="text-[28px] font-semibold leading-9 text-[#17201C]">Edit Pengguna</h1>
        <span
          v-if="original"
          class="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium"
          :class="
            original.isActive
              ? 'border-[#B9DFC9] bg-[#E7F4EC] text-[#0F6B3A]'
              : 'border-[#D6DDD9] bg-[#F1F4F2] text-[#46514B]'
          "
        >
          <span
            class="h-1.5 w-1.5 rounded-full"
            :class="original.isActive ? 'bg-[#16834B]' : 'bg-[#6B756F]'"
            aria-hidden="true"
          />
          {{ statusText(original.isActive) }}
        </span>
      </div>
      <p class="mt-1 max-w-2xl text-sm leading-5 text-[#46514B]">
        <template v-if="original">
          Perbarui informasi dan akses <span class="font-medium text-[#17201C]">{{ original.name }}</span>
          <span class="text-[#6B756F]"> (@{{ username }})</span>. Perubahan role dan status langsung
          memengaruhi apa yang bisa dilakukan pengguna.
        </template>
        <template v-else>Perbarui informasi dan akses pengguna.</template>
      </p>
    </header>

    <!-- Submit error -->
    <div
      v-if="submitError"
      class="mb-6 flex items-start gap-3 rounded-lg border border-[#F0C4BF] bg-[#FBEAE8] px-4 py-3"
      role="alert"
    >
      <span
        aria-hidden="true"
        class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#C0392B] text-xs font-bold text-white"
      >!</span>
      <p class="text-sm leading-5 text-[#8E271C]">{{ submitError }}</p>
    </div>

    <!-- Loading -->
    <div
      v-if="isLoading"
      class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]"
      role="status"
      aria-label="Memuat data pengguna"
    >
      <div class="animate-pulse space-y-6 rounded-lg border border-[#D6DDD9] bg-white p-6">
        <div class="h-4 w-32 rounded bg-[#E6EBE8]" />
        <div class="h-10 rounded-lg bg-[#E6EBE8]" />
        <div class="h-4 w-24 rounded bg-[#E6EBE8]" />
        <div class="h-10 rounded-lg bg-[#E6EBE8]" />
        <div class="h-4 w-24 rounded bg-[#E6EBE8]" />
        <div class="h-10 rounded-lg bg-[#E6EBE8]" />
      </div>
      <div class="animate-pulse space-y-4 rounded-lg border border-[#D6DDD9] bg-white p-6">
        <div class="h-4 w-28 rounded bg-[#E6EBE8]" />
        <div class="h-16 rounded-lg bg-[#E6EBE8]" />
        <div class="h-16 rounded-lg bg-[#E6EBE8]" />
      </div>
    </div>

    <!-- Load error -->
    <div
      v-else-if="loadError"
      class="rounded-lg border border-[#F0C4BF] bg-white p-8 text-center"
      role="alert"
    >
      <h2 class="text-lg font-semibold text-[#17201C]">Data pengguna gagal dimuat</h2>
      <p class="mx-auto mt-1 max-w-md text-sm leading-5 text-[#46514B]">
        {{ loadError }} Tidak ada perubahan pada data pengguna. Periksa koneksi lalu coba lagi, atau
        kembali ke daftar pengguna.
      </p>
      <div class="mt-5 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <button
          type="button"
          class="inline-flex h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          @click="loadUser"
        >
          Muat ulang
        </button>
        <button
          type="button"
          class="inline-flex h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
          @click="handleCancel"
        >
          Kembali ke Daftar Pengguna
        </button>
      </div>
    </div>

    <!-- Form -->
    <form v-else novalidate @submit.prevent="handleSubmit">
      <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <!-- Main form -->
        <div class="space-y-6">
          <!-- Section 1 -->
          <fieldset class="rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6">
            <legend class="sr-only">Informasi akun</legend>
            <h2 class="text-lg font-semibold leading-[26px] text-[#17201C]">1. Informasi akun</h2>
            <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">
              Identitas pengguna yang dipakai untuk masuk dan dihubungi.
            </p>

            <div class="mt-4 space-y-5">
              <!-- Username (read-only) -->
              <div>
                <label for="username" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Username
                </label>
                <input
                  id="username"
                  :value="username"
                  type="text"
                  readonly
                  aria-readonly="true"
                  aria-describedby="username-hint"
                  class="h-10 w-full cursor-not-allowed rounded-lg border border-[#E6EBE8] bg-[#F1F4F2] px-3 text-sm text-[#6B756F] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
                />
                <p id="username-hint" class="mt-1.5 text-xs leading-4 text-[#6B756F]">
                  Username tidak dapat diubah agar riwayat aktivitas pengguna tetap konsisten.
                </p>
              </div>

              <!-- Nama -->
              <div>
                <label for="name" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Nama lengkap <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  <span class="sr-only">(wajib)</span>
                </label>
                <input
                  id="name"
                  v-model="name"
                  type="text"
                  autocomplete="name"
                  :aria-invalid="Boolean(errors.name)"
                  :aria-describedby="errors.name ? 'name-error' : undefined"
                  class="h-10 w-full rounded-lg border bg-white px-3 text-sm text-[#17201C] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
                  :class="inputClass(!!errors.name)"
                />
                <p v-if="errors.name" id="name-error" role="alert" class="mt-1.5 text-xs leading-4 text-[#C0392B]">
                  {{ errors.name }}
                </p>
              </div>

              <!-- Email -->
              <div>
                <label for="email" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Email <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  <span class="sr-only">(wajib)</span>
                </label>
                <input
                  id="email"
                  v-model="email"
                  type="email"
                  autocomplete="email"
                  placeholder="nama@koperasi.id"
                  :aria-invalid="Boolean(errors.email)"
                  :aria-describedby="errors.email ? 'email-error' : undefined"
                  class="h-10 w-full rounded-lg border bg-white px-3 text-sm text-[#17201C] placeholder:text-[#6B756F] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
                  :class="inputClass(!!errors.email)"
                />
                <p v-if="errors.email" id="email-error" role="alert" class="mt-1.5 text-xs leading-4 text-[#C0392B]">
                  {{ errors.email }}
                </p>
              </div>
            </div>
          </fieldset>

          <!-- Section 2 -->
          <fieldset class="rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6">
            <legend class="sr-only">Akses dan status</legend>
            <h2 class="text-lg font-semibold leading-[26px] text-[#17201C]">2. Akses dan status</h2>
            <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">
              Role menentukan hak akses. Status menentukan apakah pengguna bisa masuk.
            </p>

            <div class="mt-4 space-y-5">
              <!-- Role -->
              <div>
                <label for="role" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Role <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  <span class="sr-only">(wajib)</span>
                </label>
                <select
                  id="role"
                  v-model="role"
                  :aria-invalid="Boolean(errors.role)"
                  :aria-describedby="errors.role ? 'role-error' : 'role-hint'"
                  class="h-10 w-full rounded-lg border bg-white px-3 text-sm text-[#17201C] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D] sm:max-w-xs"
                  :class="inputClass(!!errors.role)"
                >
                  <option v-for="option in roleOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <p v-if="errors.role" id="role-error" role="alert" class="mt-1.5 text-xs leading-4 text-[#C0392B]">
                  {{ errors.role }}
                </p>
                <p v-else id="role-hint" class="mt-1.5 text-xs leading-4 text-[#6B756F]">
                  Ringkasan hak akses role terpilih tampil di panel samping.
                </p>
              </div>

              <!-- Tautan data anggota (wajib untuk role anggota) -->
              <div v-if="role === 'anggota'">
                <label for="member" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Data anggota <span class="text-[#C0392B]" aria-hidden="true">*</span>
                </label>
                <select
                  id="member"
                  v-model="memberId"
                  class="h-10 w-full rounded-lg border border-[#D6DDD9] bg-white px-3 text-sm text-[#17201C] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D] sm:max-w-md"
                >
                  <option value="" disabled>Pilih anggota</option>
                  <option v-for="member in members" :key="member.id" :value="member.id">
                    {{ member.memberNumber }} — {{ member.name }}
                  </option>
                </select>
              </div>

              <!-- Status -->
              <div>
                <p id="active-label" class="mb-1.5 text-xs font-medium leading-4 text-[#46514B]">
                  Status pengguna
                </p>

                <div class="flex items-center gap-3">
                  <button
                    id="is-active"
                    type="button"
                    role="switch"
                    :aria-checked="isActive"
                    aria-labelledby="active-label active-state"
                    aria-describedby="active-hint"
                    class="relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
                    :class="isActive ? 'bg-[#176B4D]' : 'bg-[#6B756F]'"
                    @click="toggleActive"
                  >
                    <span
                      class="inline-block h-5 w-5 rounded-full bg-white shadow-sm transition-transform"
                      :class="isActive ? 'translate-x-[22px]' : 'translate-x-0.5'"
                      aria-hidden="true"
                    />
                  </button>

                  <span id="active-state" class="text-sm font-medium text-[#17201C]">
                    {{ isActive ? 'Aktif' : 'Nonaktif' }}
                  </span>
                </div>

                <p id="active-hint" class="mt-1.5 text-xs leading-4 text-[#6B756F]">
                  Pengguna nonaktif tidak dapat login. Akun tidak dihapus, sehingga riwayat
                  aktivitasnya tetap tersimpan dan dapat diaktifkan kembali.
                </p>

                <p
                  v-if="isDeactivating"
                  class="mt-3 rounded-lg border border-[#EBD5A6] bg-[#FBF3E2] px-3 py-2.5 text-[13px] leading-[18px] text-[#6B4A0F]"
                  role="status"
                >
                  Pengguna akan dinonaktifkan setelah perubahan disimpan dan tidak bisa masuk lagi.
                </p>
                <p
                  v-else-if="isReactivating"
                  class="mt-3 rounded-lg border border-[#B9DFC9] bg-[#E7F4EC] px-3 py-2.5 text-[13px] leading-[18px] text-[#0F5C33]"
                  role="status"
                >
                  Pengguna akan bisa masuk kembali setelah perubahan disimpan.
                </p>
              </div>
            </div>
          </fieldset>
        </div>

        <!-- Context / summary -->
        <aside class="space-y-6 lg:sticky lg:top-6 lg:self-start" aria-label="Ringkasan perubahan pengguna">
          <div class="rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6">
            <h2 class="text-lg font-semibold leading-[26px] text-[#17201C]">Perubahan</h2>

            <p v-if="!isDirty" class="mt-3 text-sm leading-5 text-[#6B756F]" role="status">
              Belum ada perubahan. Ubah salah satu field untuk mengaktifkan tombol simpan.
            </p>

            <dl v-else class="mt-3 divide-y divide-[#E6EBE8] rounded-lg border border-[#E6EBE8] bg-[#F8FAF9]" role="status">
              <div v-for="change in changes" :key="change.key" class="px-4 py-3">
                <dt class="text-xs font-medium text-[#6B756F]">{{ change.label }}</dt>
                <dd class="mt-0.5 break-words text-[13px] leading-[18px] text-[#17201C]">
                  <span class="text-[#6B756F] line-through decoration-[#6B756F]">{{ change.from }}</span>
                  <span class="mx-1.5" aria-hidden="true">→</span>
                  <span class="sr-only"> menjadi </span>
                  <span class="font-semibold">{{ change.to }}</span>
                </dd>
              </div>
            </dl>
          </div>

          <div class="rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6">
            <h2 class="text-lg font-semibold leading-[26px] text-[#17201C]">Hak akses role</h2>

            <div class="mt-3 flex items-center gap-2" role="status" aria-live="polite">
              <span
                class="inline-flex items-center rounded-full border border-[#B9DFC9] bg-[#E7F4EC] px-2.5 py-0.5 text-xs font-medium text-[#0F6B3A]"
              >
                {{ roleLabel }}
              </span>
              <span class="text-[13px] text-[#6B756F]">role yang dipilih</span>
            </div>

            <div v-if="role === 'kasir'" class="mt-4 space-y-4 text-[13px] leading-[18px]">
              <div>
                <p class="font-semibold text-[#17201C]">Dapat</p>
                <ul class="mt-1.5 space-y-1.5">
                  <li v-for="item in kasirCan" :key="item" class="flex items-start gap-2 text-[#17201C]">
                    <span aria-hidden="true" class="mt-px font-bold text-[#16834B]">✓</span>
                    <span><span class="sr-only">Dapat: </span>{{ item }}</span>
                  </li>
                </ul>
              </div>
              <div>
                <p class="font-semibold text-[#17201C]">Tidak dapat</p>
                <ul class="mt-1.5 space-y-1.5">
                  <li v-for="item in kasirCannot" :key="item" class="flex items-start gap-2 text-[#46514B]">
                    <span aria-hidden="true" class="mt-px font-bold text-[#6B756F]">✕</span>
                    <span><span class="sr-only">Tidak dapat: </span>{{ item }}</span>
                  </li>
                </ul>
              </div>
            </div>

            <p v-else class="mt-4 text-[13px] leading-[18px] text-[#46514B]">
              Hak akses role {{ roleLabel }} mengikuti ketentuan role di PRD §3. Pembatasan akses
              tetap diterapkan oleh sistem, bukan hanya oleh tampilan menu.
            </p>
          </div>

          <div class="rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6">
            <h2 class="text-base font-semibold leading-6 text-[#17201C]">Status validasi</h2>
            <ul class="mt-3 space-y-2">
              <li
                v-for="req in requirements"
                :key="req.label"
                class="flex items-start gap-2.5 text-[13px] leading-[18px]"
                :class="req.ok ? 'text-[#17201C]' : 'text-[#6B756F]'"
              >
                <span
                  aria-hidden="true"
                  class="mt-px flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
                  :class="req.ok ? 'bg-[#16834B] text-white' : 'border border-[#D6DDD9] bg-white text-transparent'"
                >✓</span>
                <span>
                  {{ req.label }}
                  <span class="sr-only">— {{ req.ok ? 'terpenuhi' : 'belum terpenuhi' }}</span>
                </span>
              </li>
            </ul>
          </div>
        </aside>
      </div>

      <!-- Sticky footer -->
      <div
        class="sticky bottom-0 z-10 -mx-4 mt-6 border-t border-[#D6DDD9] bg-white px-4 py-3 sm:mx-0 sm:rounded-lg sm:border sm:px-6 sm:py-4 sm:shadow-[0_1px_2px_rgba(18,55,42,.06)]"
      >
        <div class="flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
          <button
            type="button"
            :disabled="isSaving"
            class="inline-flex h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
            @click="handleCancel"
          >
            Batal
          </button>

          <div class="flex flex-col-reverse items-stretch gap-3 sm:flex-row sm:items-center">
            <p v-if="!isDirty" class="text-[13px] leading-[18px] text-[#6B756F]">
              Belum ada perubahan untuk disimpan.
            </p>
            <p v-else class="text-[13px] leading-[18px] tabular-nums text-[#46514B]">
              {{ changes.length }} perubahan belum disimpan
            </p>

            <button
              ref="submitButtonRef"
              type="submit"
              :disabled="isSaving || !isDirty"
              :aria-busy="isSaving"
              class="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-[#176B4D] px-5 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span
                v-if="isSaving"
                class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
                aria-hidden="true"
              />
              {{ isSaving ? 'Menyimpan…' : needsConfirmation ? 'Tinjau Perubahan' : 'Simpan Perubahan' }}
            </button>
          </div>
        </div>
      </div>
    </form>

    <!-- Reset password oleh admin (PRD §8) -->
    <section class="mt-6 rounded-lg border border-[#D6DDD9] bg-white p-5 sm:p-6" aria-labelledby="reset-title">
      <h2 id="reset-title" class="text-lg font-semibold text-[#17201C]">Reset password</h2>
      <p class="mt-1 text-[13px] text-[#6B756F]">
        Atur password baru untuk pengguna ini. Semua sesi login pengguna tersebut akan diakhiri.
      </p>
      <form class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end" @submit.prevent="handleResetPassword">
        <label class="block sm:w-72">
          <span class="mb-1.5 block text-xs font-medium text-[#46514B]">Password baru (min. 8 karakter)</span>
          <input
            v-model="resetPasswordValue"
            type="password"
            minlength="8"
            autocomplete="new-password"
            class="h-10 w-full rounded-lg border border-[#D6DDD9] px-3 text-sm focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
          >
        </label>
        <button
          type="submit"
          :disabled="resetting || resetPasswordValue.length < 8"
          class="h-10 rounded-lg border border-[#C0392B]/40 bg-white px-4 text-sm font-semibold text-[#C0392B] hover:bg-[#FDF0EE] disabled:opacity-50"
        >
          {{ resetting ? 'Mereset…' : 'Reset password' }}
        </button>
      </form>
      <p v-if="resetMessage" class="mt-3 text-sm text-[#16834B]" role="status">{{ resetMessage }}</p>
      <p v-if="resetError" class="mt-3 text-sm text-[#C0392B]" role="alert">{{ resetError }}</p>
    </section>

    <!-- Confirmation dialog -->
    <div
      v-if="showConfirmation"
      class="fixed inset-0 z-50 flex items-center justify-center bg-[#12372A]/50 p-4"
      @click.self="closeConfirmation"
    >
      <div
        ref="dialogRef"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirmation-title"
        aria-describedby="confirmation-desc"
        class="w-full max-w-md rounded-xl bg-white p-6 shadow-[0_12px_32px_rgba(18,55,42,.12)]"
        @keydown="onDialogKeydown"
      >
        <h2 id="confirmation-title" class="text-lg font-semibold leading-[26px] text-[#17201C]">
          {{ isDeactivating ? 'Nonaktifkan pengguna?' : 'Konfirmasi perubahan role' }}
        </h2>

        <p id="confirmation-desc" class="mt-1 text-sm leading-5 text-[#46514B]">
          Periksa perubahan berikut untuk
          <span class="font-medium text-[#17201C]">{{ original?.name }}</span>
          (@{{ username }}) sebelum disimpan.
        </p>

        <dl class="mt-4 divide-y divide-[#E6EBE8] rounded-lg border border-[#E6EBE8] bg-[#F8FAF9] text-sm">
          <div v-for="change in changes" :key="change.key" class="flex items-baseline justify-between gap-3 px-4 py-2.5">
            <dt class="text-[#46514B]">{{ change.label }}</dt>
            <dd class="break-words text-right text-[#17201C]">
              <span class="text-[#6B756F]">{{ change.from }}</span>
              <span class="mx-1" aria-hidden="true">→</span>
              <span class="sr-only"> menjadi </span>
              <span class="font-semibold">{{ change.to }}</span>
            </dd>
          </div>
        </dl>

        <div class="mt-3 space-y-2">
          <p
            v-if="isDeactivating"
            class="rounded-lg border border-[#F0C4BF] bg-[#FBEAE8] px-4 py-3 text-[13px] leading-[18px] text-[#8E271C]"
          >
            Pengguna tidak akan bisa login. Akun tidak dihapus dan dapat diaktifkan kembali kapan saja.
          </p>
          <p
            v-if="isRoleChanging"
            class="rounded-lg border border-[#EBD5A6] bg-[#FBF3E2] px-4 py-3 text-[13px] leading-[18px] text-[#6B4A0F]"
          >
            Hak akses pengguna akan berubah mengikuti role {{ roleLabel }}.
          </p>
        </div>

        <div class="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            ref="cancelButtonRef"
            type="button"
            :disabled="isSaving"
            class="inline-flex h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
            @click="closeConfirmation"
          >
            Batal
          </button>

          <button
            type="button"
            :disabled="isSaving"
            :aria-busy="isSaving"
            class="inline-flex h-10 items-center justify-center gap-2 rounded-lg px-4 text-sm font-medium text-white transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-60"
            :class="isDeactivating ? 'bg-[#C0392B] hover:bg-[#A32F23]' : 'bg-[#176B4D] hover:bg-[#1F805D]'"
            @click="saveChanges"
          >
            <span
              v-if="isSaving"
              class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
              aria-hidden="true"
            />
            {{ isSaving ? 'Menyimpan…' : isDeactivating ? 'Nonaktifkan dan Simpan' : 'Simpan Perubahan' }}
          </button>
        </div>
      </div>
    </div>
  </main>
</template>