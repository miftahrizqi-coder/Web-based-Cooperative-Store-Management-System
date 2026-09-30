<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createUser } from '../../api/users'
import { useAuth } from '../../stores/auth'
import type { UserRole } from '../../types/auth'

/* Sesuaikan dengan route daftar pengguna */
const USERS_ROUTE = '/users'

const USERNAME_MIN = 3
const PASSWORD_MIN = 8
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const { token } = useAuth()
const router = useRouter()

/* ---------- State ---------- */
const name = ref('')
const username = ref('')
const email = ref('')
const password = ref('')
const role = ref<UserRole>('kasir')

const showPassword = ref(false)

const errors = ref({
  name: '',
  username: '',
  email: '',
  password: '',
  role: '',
})
const errorMessage = ref('')
const isLoading = ref(false)

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
const roleLabel = computed(
  () => roleOptions.find((o) => o.value === role.value)?.label ?? String(role.value),
)

const requirements = computed(() => [
  { label: 'Nama terisi', ok: name.value.trim().length > 0 },
  { label: `Username minimal ${USERNAME_MIN} karakter`, ok: username.value.trim().length >= USERNAME_MIN },
  { label: 'Format email valid', ok: EMAIL_PATTERN.test(email.value.trim()) },
  { label: `Password minimal ${PASSWORD_MIN} karakter`, ok: password.value.length >= PASSWORD_MIN },
  { label: 'Role dipilih', ok: !!role.value },
])

function inputClass(hasError: boolean): string {
  return hasError
    ? 'border-[#C0392B]'
    : 'border-[#D6DDD9] focus:border-[#176B4D]'
}

/* ---------- Validation ---------- */
const fieldOrder = ['name', 'username', 'email', 'password', 'role'] as const

function validateForm(): boolean {
  errors.value = { name: '', username: '', email: '', password: '', role: '' }

  if (!name.value.trim()) {
    errors.value.name = 'Nama wajib diisi.'
  }

  if (!username.value.trim()) {
    errors.value.username = 'Username wajib diisi.'
  } else if (username.value.trim().length < USERNAME_MIN) {
    errors.value.username = `Username minimal ${USERNAME_MIN} karakter.`
  }

  if (!email.value.trim()) {
    errors.value.email = 'Email wajib diisi.'
  } else if (!EMAIL_PATTERN.test(email.value.trim())) {
    errors.value.email = 'Format email tidak valid. Contoh: nama@koperasi.id'
  }

  if (!password.value) {
    errors.value.password = 'Password wajib diisi.'
  } else if (password.value.length < PASSWORD_MIN) {
    errors.value.password = `Password minimal ${PASSWORD_MIN} karakter.`
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
watch(username, () => (errors.value.username = ''))
watch(email, () => (errors.value.email = ''))
watch(password, () => (errors.value.password = ''))
watch(role, () => (errors.value.role = ''))

/* ---------- Actions ---------- */
function handleCancel() {
  router.push(USERS_ROUTE)
}

async function handleSubmit() {
  errorMessage.value = ''

  if (!validateForm()) {
    await focusFirstInvalid()
    return
  }

  if (!token.value) {
    errorMessage.value = 'Sesi login tidak ditemukan. Silakan masuk kembali.'
    return
  }

  isLoading.value = true

  try {
    await createUser(token.value, {
      name: name.value.trim(),
      username: username.value.trim(),
      email: email.value.trim(),
      password: password.value,
      role: role.value,
    })

    await router.push(USERS_ROUTE)
  } catch (error) {
    const detail = error instanceof Error ? error.message : 'Terjadi kesalahan pada server.'
    errorMessage.value = `Pengguna gagal dibuat dan tidak ada akun yang tersimpan. ${detail} Periksa data lalu coba lagi.`
  } finally {
    isLoading.value = false
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
        <li aria-current="page" class="font-medium text-[#46514B]">Tambah Pengguna</li>
      </ol>
    </nav>

    <!-- Page header -->
    <header class="mb-6">
      <h1 class="text-[28px] font-semibold leading-9 text-[#17201C]">Tambah Pengguna</h1>
      <p class="mt-1 max-w-2xl text-sm leading-5 text-[#46514B]">
        Buat akun baru dan tentukan role-nya. Role menentukan apa yang boleh dilakukan pengguna
        di sistem, jadi pilih dengan hati-hati.
      </p>
    </header>

    <!-- Submit error -->
    <div
      v-if="errorMessage"
      class="mb-6 flex items-start gap-3 rounded-lg border border-[#F0C4BF] bg-[#FBEAE8] px-4 py-3"
      role="alert"
    >
      <span
        aria-hidden="true"
        class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#C0392B] text-xs font-bold text-white"
      >!</span>
      <p class="text-sm leading-5 text-[#8E271C]">{{ errorMessage }}</p>
    </div>

    <form novalidate @submit.prevent="handleSubmit">
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

              <!-- Username -->
              <div>
                <label for="username" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Username <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  <span class="sr-only">(wajib)</span>
                </label>
                <input
                  id="username"
                  v-model="username"
                  type="text"
                  autocomplete="username"
                  :aria-invalid="Boolean(errors.username)"
                  :aria-describedby="errors.username ? 'username-error' : 'username-hint'"
                  class="h-10 w-full rounded-lg border bg-white px-3 text-sm text-[#17201C] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
                  :class="inputClass(!!errors.username)"
                />
                <p
                  v-if="errors.username"
                  id="username-error"
                  role="alert"
                  class="mt-1.5 text-xs leading-4 text-[#C0392B]"
                >
                  {{ errors.username }}
                </p>
                <p v-else id="username-hint" class="mt-1.5 text-xs leading-4 text-[#6B756F]">
                  Minimal {{ USERNAME_MIN }} karakter. Dipakai pengguna untuk masuk.
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
            <legend class="sr-only">Keamanan dan akses</legend>
            <h2 class="text-lg font-semibold leading-[26px] text-[#17201C]">2. Keamanan dan akses</h2>
            <p class="mt-0.5 text-[13px] leading-[18px] text-[#6B756F]">
              Password awal dan role yang menentukan hak akses.
            </p>

            <div class="mt-4 space-y-5">
              <!-- Password -->
              <div>
                <label for="password" class="mb-1.5 block text-xs font-medium leading-4 text-[#46514B]">
                  Password <span class="text-[#C0392B]" aria-hidden="true">*</span>
                  <span class="sr-only">(wajib)</span>
                </label>
                <div class="relative">
                  <input
                    id="password"
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    autocomplete="new-password"
                    :aria-invalid="Boolean(errors.password)"
                    :aria-describedby="errors.password ? 'password-error' : 'password-hint'"
                    class="h-10 w-full rounded-lg border bg-white px-3 pr-20 text-sm text-[#17201C] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-[#176B4D]"
                    :class="inputClass(!!errors.password)"
                  />
                  <button
                    type="button"
                    :aria-pressed="showPassword"
                    class="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-md px-2.5 py-1 text-[13px] font-medium text-[#176B4D] hover:bg-[#F0F8F5] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D]"
                    @click="showPassword = !showPassword"
                  >
                    {{ showPassword ? 'Sembunyikan' : 'Tampilkan' }}
                    <span class="sr-only"> password</span>
                  </button>
                </div>

                <div class="mt-1.5 flex items-start justify-between gap-3 text-xs leading-4">
                  <p
                    v-if="errors.password"
                    id="password-error"
                    role="alert"
                    class="text-[#C0392B]"
                  >
                    {{ errors.password }}
                  </p>
                  <p v-else id="password-hint" class="text-[#6B756F]">
                    Minimal {{ PASSWORD_MIN }} karakter. Sampaikan password awal kepada pengguna
                    melalui jalur yang aman.
                  </p>
                  <span class="shrink-0 tabular-nums text-[#6B756F]">{{ password.length }} karakter</span>
                </div>
              </div>

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
            </div>
          </fieldset>
        </div>

        <!-- Context / summary -->
        <aside class="space-y-6 lg:sticky lg:top-6 lg:self-start" aria-label="Ringkasan pengguna baru">
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
            :disabled="isLoading"
            class="inline-flex h-10 items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 text-sm font-medium text-[#17201C] transition hover:bg-[#F1F4F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-50"
            @click="handleCancel"
          >
            Batal
          </button>

          <button
            type="submit"
            :disabled="isLoading"
            :aria-busy="isLoading"
            class="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-[#176B4D] px-5 text-sm font-medium text-white transition hover:bg-[#1F805D] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#176B4D] disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span
              v-if="isLoading"
              class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
              aria-hidden="true"
            />
            {{ isLoading ? 'Menyimpan…' : 'Simpan Pengguna' }}
          </button>
        </div>
      </div>
    </form>
  </main>
</template>