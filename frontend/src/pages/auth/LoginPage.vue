<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch, type Ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login, getCurrentUser } from '../../api/auth'
import { useAuth } from '../../stores/auth'
import { getLandingPage } from '../../router/navigation'

/* ------------------------------------------------------------------ */
/* Config & types                                                      */
/* ------------------------------------------------------------------ */
const REMEMBER_KEY = 'koprom:last-username'
const THEME_KEY = 'koprom:theme'
const SOUND_KEY = 'koprom:sound'
const LOCK_KEY = 'koprom:lock-until'

const REQUEST_TIMEOUT_MS = 15_000
const SLOW_HINT_MS = 5_000
const DEFAULT_RETRY_AFTER_SEC = 60
const MAX_RETRY_AFTER_SEC = 900
const SUCCESS_DELAY_MS = 750
const PASSWORD_REVEAL_MS = 15_000
const IDLE_SLEEP_MS = 25_000
const MAX_QTY = 9

const appVersion = import.meta.env.VITE_APP_VERSION as string | undefined

type FailureKind = 'invalid' | 'rate-limit' | 'server' | 'network' | 'timeout'
type Status = 'idle' | 'loading' | 'success'
type ThemeMode = 'system' | 'light' | 'dark'
type MascotMode = 'watch' | 'hide' | 'peek' | 'sad' | 'happy' | 'think' | 'sleep'
type Field = 'username' | 'password'
type CashChoice = 'exact' | 'round' | 50_000 | 100_000
type Method = 'cash' | 'qris' | 'debit'

interface LoginFailure {
  kind: FailureKind
  message: string
  retryAfterSec?: number
}

class RequestTimeoutError extends Error {}

/* ------------------------------------------------------------------ */
/* Pure helpers                                                        */
/* ------------------------------------------------------------------ */
function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new RequestTimeoutError()), ms)
  })
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer))
}

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms))
const clamp = (v: number, min: number, max: number) => Math.min(Math.max(v, min), max)
const randomBetween = (min: number, max: number) => min + Math.random() * (max - min)
const prefersReducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
const isDesktop = () => window.matchMedia('(min-width: 1024px)').matches

function centerOf(el: Element | null | undefined): { x: number; y: number } {
  const r = el?.getBoundingClientRect()
  return r
    ? { x: r.left + r.width / 2, y: r.top + r.height / 2 }
    : { x: window.innerWidth / 2, y: window.innerHeight / 2 }
}

function readHeader(headers: unknown, name: string): string | undefined {
  if (!headers) return undefined
  if (typeof (headers as Headers).get === 'function') {
    return (headers as Headers).get(name) ?? undefined
  }
  const record = headers as Record<string, unknown>
  const value = record[name] ?? record[name.toLowerCase()]
  return typeof value === 'string' ? value : undefined
}

function classifyFailure(error: unknown): LoginFailure {
  if (error instanceof RequestTimeoutError) {
    return { kind: 'timeout', message: 'Server terlalu lama merespons. Coba lagi.' }
  }
  const e = error as {
    response?: { status?: number; headers?: unknown }
    status?: number
    code?: string
  }
  const status = e?.response?.status ?? e?.status

  if (status === 429) {
    const raw = Number.parseInt(readHeader(e.response?.headers, 'Retry-After') ?? '', 10)
    const retryAfterSec = Number.isFinite(raw)
      ? clamp(raw, 1, MAX_RETRY_AFTER_SEC)
      : DEFAULT_RETRY_AFTER_SEC
    return {
      kind: 'rate-limit',
      message: 'Terlalu banyak percobaan. Login dikunci sementara.',
      retryAfterSec,
    }
  }
  if (status && status >= 500) {
    return { kind: 'server', message: 'Server sedang bermasalah. Coba lagi sebentar lagi.' }
  }
  if (!navigator.onLine || e?.code === 'ERR_NETWORK' || error instanceof TypeError) {
    return {
      kind: 'network',
      message: 'Tidak dapat terhubung ke server. Periksa koneksi internet Anda.',
    }
  }
  return { kind: 'invalid', message: 'Username atau password tidak valid.' }
}

/** Hanya izinkan path internal agar tidak menjadi open redirect. */
function resolveSafeRedirect(target: unknown, loginPath: string): string | null {
  if (typeof target !== 'string') return null
  if (!target.startsWith('/') || target.startsWith('//')) return null
  if (target.includes('\\') || target.startsWith(loginPath)) return null
  return target
}

function formatSeconds(total: number): string {
  if (total < 60) return `${total} dtk`
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`
}

function greetingFor(date: Date): string {
  const h = date.getHours()
  if (h < 11) return 'Selamat pagi'
  if (h < 15) return 'Selamat siang'
  if (h < 18) return 'Selamat sore'
  return 'Selamat malam'
}

function safeStorageGet(key: string): string {
  try {
    return localStorage.getItem(key) ?? ''
  } catch {
    return ''
  }
}

function safeStorageSet(key: string, value: string | null) {
  try {
    if (value) localStorage.setItem(key, value)
    else localStorage.removeItem(key)
  } catch {
    // Storage bisa diblokir (mode privat, kebijakan browser). Abaikan.
  }
}

/** Angka yang bergerak halus menuju nilai baru (untuk total struk). */
function useTweenedNumber(source: Ref<number>, duration = 260) {
  const shown = ref(source.value)
  let raf = 0
  watch(source, (to) => {
    cancelAnimationFrame(raf)
    if (prefersReducedMotion()) {
      shown.value = to
      return
    }
    const from = shown.value
    const start = performance.now()
    const step = (t: number) => {
      const p = Math.min((t - start) / duration, 1)
      shown.value = Math.round(from + (to - from) * (1 - Math.pow(1 - p, 3)))
      if (p < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
  })
  onBeforeUnmount(() => cancelAnimationFrame(raf))
  return shown
}

/* ------------------------------------------------------------------ */
/* Efek suara (opsional, default mati, dibuat saat ada gesture user)   */
/* ------------------------------------------------------------------ */
const soundOn = ref(safeStorageGet(SOUND_KEY) === '1')
let audioCtx: AudioContext | null = null

function playTones(freqs: number[], step = 0.08) {
  if (!soundOn.value) return
  try {
    const Ctor =
      window.AudioContext ??
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!Ctor) return
    audioCtx ??= new Ctor()
    if (audioCtx.state === 'suspended') void audioCtx.resume()
    const ctx = audioCtx
    freqs.forEach((freq, i) => {
      const t0 = ctx.currentTime + i * step
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'triangle'
      osc.frequency.value = freq
      gain.gain.setValueAtTime(0.0001, t0)
      gain.gain.exponentialRampToValueAtTime(0.09, t0 + 0.012)
      gain.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.14)
      osc.connect(gain).connect(ctx.destination)
      osc.start(t0)
      osc.stop(t0 + 0.16)
    })
  } catch {
    // Audio tidak tersedia: abaikan, ini hanya hiasan.
  }
}

/* ---------- Pola QR untuk simulasi QRIS (bukan kode yang bisa dipindai) ---------- */
const QR_SIZE = 25
const QR_QUIET = 2

function hashSeed(text: string): number {
  let h = 2166136261
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

function mulberry32(seed: number) {
  let a = seed
  return () => {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** Bangun path SVG untuk matriks 25x25: tiga penanda sudut, garis waktu, penanda kecil, dan data acak dari seed. */
function buildQrPath(seedText: string): string {
  const n = QR_SIZE
  const rand = mulberry32(hashSeed(seedText))
  const grid = Array.from({ length: n }, () => Array<boolean>(n).fill(false))
  const reserved = Array.from({ length: n }, () => Array<boolean>(n).fill(false))

  const reserve = (x0: number, y0: number, w: number, h: number) => {
    for (let y = y0; y < y0 + h; y++) for (let x = x0; x < x0 + w; x++) reserved[y][x] = true
  }
  const finder = (ox: number, oy: number) => {
    for (let y = 0; y < 7; y++) {
      for (let x = 0; x < 7; x++) {
        const ring = x === 0 || x === 6 || y === 0 || y === 6
        const core = x >= 2 && x <= 4 && y >= 2 && y <= 4
        grid[oy + y][ox + x] = ring || core
      }
    }
  }

  finder(0, 0)
  finder(n - 7, 0)
  finder(0, n - 7)
  reserve(0, 0, 8, 8)
  reserve(n - 8, 0, 8, 8)
  reserve(0, n - 8, 8, 8)

  for (let i = 8; i < n - 8; i++) {
    grid[6][i] = i % 2 === 0
    grid[i][6] = i % 2 === 0
    reserved[6][i] = true
    reserved[i][6] = true
  }

  const ax = n - 9
  for (let y = 0; y < 5; y++) {
    for (let x = 0; x < 5; x++) {
      grid[ax + y][ax + x] = x === 0 || x === 4 || y === 0 || y === 4 || (x === 2 && y === 2)
    }
  }
  reserve(ax, ax, 5, 5)

  for (let y = 0; y < n; y++) {
    for (let x = 0; x < n; x++) {
      if (!reserved[y][x]) grid[y][x] = rand() < 0.5
    }
  }

  let d = ''
  for (let y = 0; y < n; y++) {
    let x = 0
    while (x < n) {
      if (!grid[y][x]) {
        x++
        continue
      }
      const start = x
      while (x < n && grid[y][x]) x++
      d += `M${start + QR_QUIET} ${y + QR_QUIET}h${x - start}v1h-${x - start}z`
    }
  }
  return d
}

/** Bunyi "tek-tek-tek" printer termal saat struk keluar. */
const feedTicks = () => playTones(Array.from({ length: 9 }, () => 240), 0.17)

/* ------------------------------------------------------------------ */
/* Form state                                                          */
/* ------------------------------------------------------------------ */
const router = useRouter()
const route = useRoute()
const { setAuth } = useAuth()

const username = ref('')
const password = ref('')
const rememberUsername = ref(false)
const showPassword = ref(false)
const capsLockOn = ref(false)
const status = ref<Status>('idle')
const isOffline = ref(!navigator.onLine)
const focusedField = ref<Field | null>(null)

const failure = ref<LoginFailure | null>(null)
const failureCount = ref(0)
const usernameError = ref('')
const passwordError = ref('')
const slowHint = ref(false)
const liveMessage = ref('')

const lockSeconds = ref(0)
const lockTotal = ref(0)
let lockUntil = 0
let attempt = 0

let lockTimer: ReturnType<typeof setInterval> | undefined
let revealTimer: ReturnType<typeof setTimeout> | undefined
let clockTimer: ReturnType<typeof setInterval> | undefined
let blinkTimer: ReturnType<typeof setTimeout> | undefined
let blinkOffTimer: ReturnType<typeof setTimeout> | undefined
let bubbleTimer: ReturnType<typeof setTimeout> | undefined
let pokeTimer: ReturnType<typeof setTimeout> | undefined
let idleTimer: ReturnType<typeof setInterval> | undefined
let slowTimer: ReturnType<typeof setTimeout> | undefined
let pointerRaf = 0

const usernameInput = ref<HTMLInputElement | null>(null)
const passwordInput = ref<HTMLInputElement | null>(null)
const submitButton = ref<HTMLButtonElement | null>(null)

const isLoading = computed(() => status.value === 'loading')
const isSuccess = computed(() => status.value === 'success')
const isBusy = computed(() => status.value !== 'idle')
const isLocked = computed(() => lockSeconds.value > 0)
const canSubmit = computed(() => !isBusy.value && !isLocked.value)
const lockProgress = computed(() =>
  lockTotal.value ? clamp(lockSeconds.value / lockTotal.value, 0, 1) : 0,
)

const submitLabel = computed(() => {
  if (isLocked.value) return `Coba lagi dalam ${formatSeconds(lockSeconds.value)}`
  if (isSuccess.value) return 'Berhasil masuk'
  return isLoading.value ? 'Memproses...' : 'Masuk'
})

const notice = computed(() => {
  switch (route.query.reason) {
    case 'expired':
      return 'Sesi Anda berakhir. Masuk kembali untuk melanjutkan.'
    case 'logout':
      return 'Anda sudah keluar.'
    default:
      return ''
  }
})

const describedByPassword = computed(
  () =>
    [passwordError.value ? 'password-error' : '', capsLockOn.value ? 'capslock-hint' : '']
      .filter(Boolean)
      .join(' ') || undefined,
)

const announce = (message: string) => (liveMessage.value = message)

/* ---------- Waktu, sapaan, tema ---------- */
const now = ref(new Date())
const greeting = computed(() => greetingFor(now.value))
const dateFormatter = new Intl.DateTimeFormat('id-ID', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})
const timeFormatter = new Intl.DateTimeFormat('id-ID', { hour: '2-digit', minute: '2-digit' })
const todayLabel = computed(
  () => `${dateFormatter.format(now.value)}, ${timeFormatter.format(now.value)}`,
)

const THEME_ORDER: ThemeMode[] = ['system', 'light', 'dark']
const THEME_LABEL: Record<ThemeMode, string> = { system: 'Sistem', light: 'Terang', dark: 'Gelap' }
const THEME_ICON: Record<ThemeMode, string> = {
  system: 'M5 4h14a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2zM8 21h8M12 17v4',
  light:
    'M12 8a4 4 0 100 8 4 4 0 000-8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4',
  dark: 'M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z',
}
const EYE_ICON = 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7zM12 9a3 3 0 100 6 3 3 0 000-6z'
const EYE_OFF_ICON =
  'M9.9 5.1A10 10 0 0112 5c6.5 0 10 7 10 7a17 17 0 01-3.2 4.2M6.1 6.1A17 17 0 002 12s3.5 7 10 7a9.7 9.7 0 004-.9M9.9 9.9a3 3 0 004.2 4.2M3 3l18 18'
const SOUND_ON_ICON = 'M11 5 6 9H3v6h3l5 4zM15.5 8.5a5 5 0 010 7M18.5 5.5a9 9 0 010 13'
const SOUND_OFF_ICON = 'M11 5 6 9H3v6h3l5 4zM22 9l-6 6M16 9l6 6'

const storedTheme = safeStorageGet(THEME_KEY)
const theme = ref<ThemeMode>(
  THEME_ORDER.includes(storedTheme as ThemeMode) ? (storedTheme as ThemeMode) : 'system',
)

function cycleTheme() {
  const next = THEME_ORDER[(THEME_ORDER.indexOf(theme.value) + 1) % THEME_ORDER.length]
  theme.value = next
  safeStorageSet(THEME_KEY, next === 'system' ? null : next)
  announce(`Tema ${THEME_LABEL[next]}`)
}

function toggleSound() {
  soundOn.value = !soundOn.value
  safeStorageSet(SOUND_KEY, soundOn.value ? '1' : null)
  announce(soundOn.value ? 'Efek suara aktif' : 'Efek suara mati')
  playTones([660, 990])
}

/* ------------------------------------------------------------------ */
/* Partikel koin (sukses login, bayar, maskot digelitik)               */
/* ------------------------------------------------------------------ */
interface Piece {
  id: number
  x: number
  y: number
  dx: number
  dy: number
  rot: number
}

const pieces = ref<Piece[]>([])
let pieceId = 0

function burst(x: number, y: number, count = 14) {
  if (prefersReducedMotion()) return
  const fresh: Piece[] = Array.from({ length: count }, () => {
    const angle = randomBetween(-Math.PI * 0.95, -Math.PI * 0.05)
    const dist = randomBetween(60, 150)
    return {
      id: ++pieceId,
      x,
      y,
      dx: Math.cos(angle) * dist,
      dy: Math.sin(angle) * dist,
      rot: randomBetween(-360, 360),
    }
  })
  pieces.value.push(...fresh)
  const ids = new Set(fresh.map((p) => p.id))
  setTimeout(() => (pieces.value = pieces.value.filter((p) => !ids.has(p.id))), 1200)
}

/* ------------------------------------------------------------------ */
/* Maskot gajah mamut                                                 */
/* ------------------------------------------------------------------ */
const mascotEl = ref<SVGSVGElement | null>(null)
const mascotButton = ref<HTMLButtonElement | null>(null)
const pointerLook = ref({ x: 0, y: 0 })
const blinking = ref(false)
const bouncing = ref(false)
const sleeping = ref(false)
const bubble = ref('')
let bubbleIndex = 0
let pokeCount = 0
let lastActivity = Date.now()

const MASCOT_LINES = [
  'Grrmph! Semoga hari ini ramai.',
  'Sudah cek stok pagi ini?',
  'Kembalian jangan sampai salah, ya.',
  'Sedikit demi sedikit, lama-lama jadi bukit.',
]
const EYES = [
  { cx: 44, cy: 54 },
  { cx: 76, cy: 54 },
]

const arcUp = (e: { cx: number; cy: number }) =>
  `M${e.cx - 8} ${e.cy + 3} Q${e.cx} ${e.cy - 7} ${e.cx + 8} ${e.cy + 3}`
const arcDown = (e: { cx: number; cy: number }) =>
  `M${e.cx - 7} ${e.cy} Q${e.cx} ${e.cy + 6} ${e.cx + 7} ${e.cy}`

const mascotMode = computed<MascotMode>(() => {
  if (isSuccess.value) return 'happy'
  if (isLoading.value) return 'think'
  if (failure.value && !password.value) return 'sad'
  if (showPassword.value && (focusedField.value === 'password' || password.value)) return 'peek'
  if (focusedField.value === 'password') return 'hide'
  if (sleeping.value) return 'sleep'
  return 'watch'
})

const look = computed(() => {
  switch (mascotMode.value) {
    case 'sad':
      return { x: 0, y: 0.8 }
    case 'peek':
      return { x: 0.6, y: 0.7 }
    case 'think':
      return { x: 0, y: 0 }
    default:
      if (focusedField.value === 'username') {
        // Mata "membaca" mengikuti panjang teks yang diketik
        const t = Math.min(username.value.length / 18, 1)
        return { x: -0.8 + t * 1.6, y: 0.7 }
      }
      return pointerLook.value
  }
})

const pupilStyle = computed(() => ({
  transform: `translate(${look.value.x * 3.5}px, ${look.value.y * 3}px)`,
}))

const hoofs = computed(() => {
  const m = mascotMode.value
  const rest = { l: 'translate(34px, 116px)', r: 'translate(86px, 116px)' }
  const cover = { l: 'translate(44px, 54px)', r: 'translate(76px, 54px)' }
  return {
    l: m === 'hide' || m === 'peek' ? cover.l : rest.l,
    r: m === 'hide' ? cover.r : rest.r,
  }
})

function touchActivity() {
  lastActivity = Date.now()
  sleeping.value = false
}

function onWindowPointerMove(e: PointerEvent) {
  touchActivity()
  if (e.pointerType !== 'mouse' || prefersReducedMotion()) return
  cancelAnimationFrame(pointerRaf)
  pointerRaf = requestAnimationFrame(() => {
    const r = mascotEl.value?.getBoundingClientRect()
    if (!r) return
    pointerLook.value = {
      x: clamp((e.clientX - (r.left + r.width / 2)) / 240, -1, 1),
      y: clamp((e.clientY - (r.top + r.height / 2)) / 240, -1, 1),
    }
  })
}

function scheduleBlink() {
  blinkTimer = setTimeout(() => {
    blinking.value = true
    blinkOffTimer = setTimeout(() => (blinking.value = false), 130)
    scheduleBlink()
  }, randomBetween(2600, 5200))
}

function pokeMascot() {
  touchActivity()
  bouncing.value = false
  requestAnimationFrame(() => (bouncing.value = true))

  pokeCount += 1
  clearTimeout(pokeTimer)
  pokeTimer = setTimeout(() => (pokeCount = 0), 1400)

  if (pokeCount >= 5) {
    pokeCount = 0
    bubble.value = 'Hihi, geli! Ini koin untukmu.'
    const c = centerOf(mascotButton.value)
    burst(c.x, c.y, 12)
    playTones([784, 988, 1175])
  } else {
    bubble.value = MASCOT_LINES[bubbleIndex++ % MASCOT_LINES.length]
    playTones([520])
  }
  announce(bubble.value)
  clearTimeout(bubbleTimer)
  bubbleTimer = setTimeout(() => (bubble.value = ''), 2800)
}

/* ------------------------------------------------------------------ */
/* Simulasi kasir di panel merek                                       */
/* ------------------------------------------------------------------ */
const rupiah = new Intl.NumberFormat('id-ID')
const products = [
  { id: 'beras', name: 'Beras 5 kg', price: 68_000 },
  { id: 'minyak', name: 'Minyak 1 L', price: 17_500 },
  { id: 'gula', name: 'Gula 1 kg', price: 16_000 },
  { id: 'telur', name: 'Telur 1 kg', price: 29_000 },
  { id: 'kopi', name: 'Kopi 200 g', price: 24_000 },
  { id: 'mie', name: 'Mie instan', price: 3_500 },
]
type Product = (typeof products)[number]

const METHODS: { value: Method; label: string }[] = [
  { value: 'cash', label: 'Tunai' },
  { value: 'qris', label: 'QRIS' },
  { value: 'debit', label: 'Debit' },
]
const METHOD_LABEL: Record<Method, string> = { cash: 'Tunai', qris: 'QRIS', debit: 'Debit' }

const cashOptions: { value: CashChoice; label: string }[] = [
  { value: 'exact', label: 'Pas' },
  { value: 'round', label: 'Bulatkan' },
  { value: 50_000, label: '50rb' },
  { value: 100_000, label: '100rb' },
]

const cart = ref<Record<string, number>>({ beras: 1, minyak: 1 })
const paid = ref(false)
const method = ref<Method>('cash')
const cashChoice = ref<CashChoice>('round')
const accountNumber = ref('') // hanya digit
const accountTouched = ref(false)
const receiptNo = ref(128)
const stampKey = ref(0)
const scanKey = ref(0)
const printKey = ref(0)
const feeding = ref(!prefersReducedMotion())
const deskEl = ref<HTMLElement | null>(null)
const payButton = ref<HTMLButtonElement | null>(null)
const printedAt = ref(new Date())
const receiptStamp = computed(
  () => `${new Intl.DateTimeFormat('id-ID').format(printedAt.value)} ${timeFormatter.format(printedAt.value)}`,
)
const receiptCode = computed(() => `KP-${String(receiptNo.value).padStart(6, '0')}`)

const cartLines = computed(() =>
  products
    .filter((p) => (cart.value[p.id] ?? 0) > 0)
    .map((p) => ({ ...p, qty: cart.value[p.id], subtotal: p.price * cart.value[p.id] })),
)
const receiptTotal = computed(() => cartLines.value.reduce((sum, l) => sum + l.subtotal, 0))

/** Pola QR berubah setiap nominal atau nomor struk berubah, seperti QRIS dinamis. */
const qrPath = computed(() => buildQrPath(`${receiptCode.value}:${receiptTotal.value}`))
const qrViewBox = `0 0 ${QR_SIZE + QR_QUIET * 2} ${QR_SIZE + QR_QUIET * 2}`

/** Pilihan nominal yang tidak lagi cukup otomatis turun ke "Bulatkan". */
const activeCash = computed<CashChoice>(() =>
  typeof cashChoice.value === 'number' && cashChoice.value < receiptTotal.value
    ? 'round'
    : cashChoice.value,
)
const receiptCash = computed(() => {
  const total = receiptTotal.value
  if (activeCash.value === 'exact') return total
  if (typeof activeCash.value === 'number') return activeCash.value
  return Math.ceil(total / 5_000) * 5_000
})
const receiptChange = computed(() => receiptCash.value - receiptTotal.value)

/* Nomor rekening (debit): hanya digit, tampil per 4 angka, minimal 10 digit */
const accountDisplay = computed(() => accountNumber.value.replace(/(\d{4})(?=\d)/g, '$1 '))
const accountValid = computed(() => accountNumber.value.length >= 10)
const maskedAccount = computed(() =>
  accountNumber.value.length >= 4 ? `\u2022\u2022\u2022\u2022${accountNumber.value.slice(-4)}` : '',
)
const canPay = computed(
  () => receiptTotal.value > 0 && (method.value !== 'debit' || accountValid.value),
)

const shownTotal = useTweenedNumber(receiptTotal)
const shownCash = useTweenedNumber(receiptCash)
const shownChange = useTweenedNumber(receiptChange)

const cashDisabled = (value: CashChoice) =>
  typeof value === 'number' && value < receiptTotal.value

function addItem(p: Product) {
  if (paid.value) return
  const next = Math.min((cart.value[p.id] ?? 0) + 1, MAX_QTY)
  cart.value[p.id] = next
  scanKey.value += 1
  playTones([880])
  announce(`${p.name} ditambahkan, jumlah ${next}. Total ${rupiah.format(receiptTotal.value)} rupiah.`)
}

function removeItem(p: Product) {
  if (paid.value) return
  cart.value[p.id] = Math.max((cart.value[p.id] ?? 0) - 1, 0)
  playTones([520])
  announce(`${p.name} dikurangi.`)
}

function setMethod(value: Method) {
  if (paid.value || method.value === value) return
  method.value = value
  playTones([700])
  if (value === 'debit') {
    void nextTick(() => deskEl.value?.querySelector<HTMLInputElement>('.kp-acct')?.focus())
  }
}

function onAccountInput(e: Event) {
  const el = e.target as HTMLInputElement
  accountNumber.value = el.value.replace(/\D/g, '').slice(0, 16)
  el.value = accountDisplay.value
}

function chooseCash(value: CashChoice) {
  if (paid.value || cashDisabled(value)) return
  cashChoice.value = value
  playTones([700])
}

function payCart() {
  if (paid.value || !canPay.value) return
  const origin = centerOf(payButton.value)
  paid.value = true
  stampKey.value += 1
  playTones([660, 880, 1320])
  burst(origin.x, origin.y, 16)
  announce(
    method.value === 'cash'
      ? `Pembayaran lunas. Kembalian ${rupiah.format(receiptChange.value)} rupiah.`
      : `Pembayaran ${METHOD_LABEL[method.value]} lunas.`,
  )
  void nextTick(() => deskEl.value?.querySelector<HTMLElement>('.kp-new')?.focus())
}

function clearCart() {
  if (paid.value) return
  cart.value = {}
  announce('Keranjang dikosongkan.')
}

/** Mulai transaksi baru: struk baru dicetak dari printer. */
function newTransaction() {
  cart.value = {}
  paid.value = false
  scanKey.value = 0
  accountNumber.value = ''
  accountTouched.value = false
  receiptNo.value += 1
  printedAt.value = new Date()
  printKey.value += 1
  feeding.value = !prefersReducedMotion()
  feedTicks()
  announce('Transaksi baru dimulai.')
  void nextTick(() => deskEl.value?.querySelector<HTMLElement>('.kp-chip')?.focus())
}

/* Pintasan 1-6 menambah barang saat fokus tidak berada di kolom teks. */
function onGlobalKeydown(e: KeyboardEvent) {
  touchActivity()
  if (e.metaKey || e.ctrlKey || e.altKey || !isDesktop()) return
  const t = e.target as HTMLElement | null
  if (t && (t.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName))) return
  const index = Number(e.key) - 1
  if (e.key.length === 1 && Number.isInteger(index) && index >= 0 && index < products.length) {
    addItem(products[index])
  }
}

/* ---------- Tilt struk + spotlight mengikuti pointer ---------- */
const tilt = ref({ x: 0, y: 0 })
const spot = ref({ x: 50, y: 30, on: false })

function onAsideMove(event: PointerEvent) {
  if (event.pointerType !== 'mouse' || prefersReducedMotion()) return
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const px = (event.clientX - rect.left) / rect.width
  const py = (event.clientY - rect.top) / rect.height
  tilt.value = { x: -(py - 0.5) * 6, y: (px - 0.5) * 8 }
  spot.value = { x: event.clientX - rect.left, y: event.clientY - rect.top, on: true }
}

function onAsideLeave() {
  tilt.value = { x: 0, y: 0 }
  spot.value = { ...spot.value, on: false }
}

/* ---------- Ripple tombol utama ---------- */
const ripples = ref<{ id: number; x: number; y: number }[]>([])
let rippleId = 0

function addRipple(e: PointerEvent) {
  if (prefersReducedMotion()) return
  const r = (e.currentTarget as HTMLElement).getBoundingClientRect()
  ripples.value.push({ id: ++rippleId, x: e.clientX - r.left, y: e.clientY - r.top })
}

const removeRipple = (id: number) => (ripples.value = ripples.value.filter((r) => r.id !== id))

/* ---------- Transisi sukses: layar hijau membesar dari tombol ---------- */
const wipe = ref<{ x: number; y: number; name: string } | null>(null)

/* ------------------------------------------------------------------ */
/* Lockout (berbasis timestamp), reveal, validasi                      */
/* ------------------------------------------------------------------ */
function stopLock() {
  if (lockTimer) clearInterval(lockTimer)
  lockTimer = undefined
  lockUntil = 0
  lockSeconds.value = 0
  lockTotal.value = 0
  safeStorageSet(LOCK_KEY, null)
}

function tickLock() {
  // Hitung dari waktu akhir, bukan decrement, agar akurat saat tab di-throttle.
  const remaining = Math.ceil((lockUntil - Date.now()) / 1000)
  if (remaining <= 0) {
    stopLock()
    failure.value = null
    void nextTick(() => passwordInput.value?.focus())
    return
  }
  lockSeconds.value = remaining
}

function startLockUntil(until: number) {
  stopLock()
  lockUntil = until
  lockTotal.value = Math.max(Math.ceil((until - Date.now()) / 1000), 1)
  safeStorageSet(LOCK_KEY, String(until))
  tickLock()
  lockTimer = setInterval(tickLock, 500)
}

const startLock = (seconds: number) => startLockUntil(Date.now() + seconds * 1000)

watch(showPassword, (visible) => {
  clearTimeout(revealTimer)
  if (visible) revealTimer = setTimeout(() => (showPassword.value = false), PASSWORD_REVEAL_MS)
})

const hidePasswordWhenAway = () => {
  if (document.hidden) showPassword.value = false
}

function validateUsername(): boolean {
  usernameError.value = username.value.trim() ? '' : 'Username wajib diisi.'
  return !usernameError.value
}

function validatePassword(): boolean {
  passwordError.value = password.value ? '' : 'Password wajib diisi.'
  return !passwordError.value
}

function onUsernameBlur() {
  focusedField.value = null
  if (username.value) validateUsername()
}

function onPasswordBlur() {
  focusedField.value = null
  capsLockOn.value = false
}

/** Enter di username: pindah ke password dulu bila password masih kosong. */
function onUsernameEnter() {
  if (username.value.trim() && !password.value) passwordInput.value?.focus()
  else void handleSubmit()
}

/** Escape di kolom password: sembunyikan password yang sedang terlihat. */
function onPasswordEscape() {
  if (showPassword.value) showPassword.value = false
}

const updateCapsLock = (e: KeyboardEvent) =>
  (capsLockOn.value = e.getModifierState?.('CapsLock') ?? false)

const syncOnlineStatus = () => {
  isOffline.value = !navigator.onLine
  announce(isOffline.value ? 'Koneksi terputus.' : 'Koneksi kembali tersambung.')
}

function clearSlowHint() {
  clearTimeout(slowTimer)
  slowHint.value = false
}

/* ------------------------------------------------------------------ */
/* Submit                                                              */
/* ------------------------------------------------------------------ */
async function handleSubmit() {
  if (!canSubmit.value) return

  failure.value = null
  const usernameOk = validateUsername()
  const passwordOk = validatePassword()

  if (!usernameOk || !passwordOk) {
    ;(usernameOk ? passwordInput : usernameInput).value?.focus()
    return
  }

  const myAttempt = ++attempt
  status.value = 'loading'
  slowTimer = setTimeout(() => (slowHint.value = true), SLOW_HINT_MS)
  const cleanUsername = username.value.trim()

  let session: { token: string; user: Awaited<ReturnType<typeof getCurrentUser>> }
  try {
    session = await withTimeout(
      (async () => {
        const result = await login(cleanUsername, password.value)
        const user = await getCurrentUser(result.token)
        return { token: result.token, user }
      })(),
      REQUEST_TIMEOUT_MS,
    )
  } catch (error) {
    clearSlowHint()
    if (myAttempt !== attempt) return // dibatalkan pengguna

    const result = classifyFailure(error)
    failure.value = result
    failureCount.value += 1
    password.value = ''
    status.value = 'idle'
    playTones([220, 180], 0.1)

    await nextTick() // field baru aktif kembali setelah render
    if (result.kind === 'rate-limit') startLock(result.retryAfterSec ?? DEFAULT_RETRY_AFTER_SEC)
    else passwordInput.value?.focus()
    return
  }

  clearSlowHint()
  if (myAttempt !== attempt) return // dibatalkan saat menunggu

  safeStorageSet(REMEMBER_KEY, rememberUsername.value ? cleanUsername : null)
  setAuth(session.token, session.user)

  status.value = 'success'
  playTones([660, 880, 1320])

  const origin = centerOf(submitButton.value)
  const profile = session.user as { name?: string; fullName?: string; username?: string }

  if (!prefersReducedMotion()) {
    burst(origin.x, origin.y, 14)
    wipe.value = {
      x: origin.x,
      y: origin.y,
      name: profile.name ?? profile.fullName ?? profile.username ?? cleanUsername,
    }
    await sleep(SUCCESS_DELAY_MS)
  }

  try {
    const redirect = resolveSafeRedirect(route.query.redirect, route.path)
    await router.replace(redirect ?? getLandingPage(session.user.role))
  } catch {
    // Kegagalan navigasi tidak boleh dilaporkan sebagai "kredensial salah".
    wipe.value = null
    status.value = 'idle'
    failure.value = {
      kind: 'server',
      message: 'Login berhasil, tetapi halaman tujuan gagal dibuka. Muat ulang halaman.',
    }
  }
}

/** Batalkan permintaan yang sedang menunggu (hasilnya diabaikan). */
function cancelLogin() {
  if (!isLoading.value) return
  attempt += 1
  clearSlowHint()
  status.value = 'idle'
  announce('Login dibatalkan.')
  void nextTick(() => passwordInput.value?.focus())
}

/* ------------------------------------------------------------------ */
/* Lifecycle                                                           */
/* ------------------------------------------------------------------ */
const previousTitle = document.title

onMounted(() => {
  document.title = 'Masuk - Koprom'
  window.addEventListener('online', syncOnlineStatus)
  window.addEventListener('offline', syncOnlineStatus)
  window.addEventListener('pointermove', onWindowPointerMove)
  window.addEventListener('pointerdown', touchActivity)
  window.addEventListener('keydown', onGlobalKeydown)
  document.addEventListener('visibilitychange', hidePasswordWhenAway)
  clockTimer = setInterval(() => (now.value = new Date()), 15_000)

  if (!prefersReducedMotion()) {
    scheduleBlink()
    idleTimer = setInterval(() => {
      if (!focusedField.value && !isBusy.value && Date.now() - lastActivity > IDLE_SLEEP_MS) {
        sleeping.value = true
      }
    }, 2000)
  }

  // Pulihkan kunci login bila halaman dimuat ulang saat masih terkunci.
  const storedLock = Number(safeStorageGet(LOCK_KEY))
  if (storedLock > Date.now()) {
    failure.value = {
      kind: 'rate-limit',
      message: 'Terlalu banyak percobaan. Login dikunci sementara.',
    }
    startLockUntil(storedLock)
  }

  const saved = safeStorageGet(REMEMBER_KEY)
  if (saved) {
    username.value = saved
    rememberUsername.value = true
    passwordInput.value?.focus()
  } else {
    usernameInput.value?.focus()
  }
})

onBeforeUnmount(() => {
  attempt += 1 // abaikan respons yang masih berjalan
  if (lockTimer) clearInterval(lockTimer)
  if (clockTimer) clearInterval(clockTimer)
  if (idleTimer) clearInterval(idleTimer)
  ;[revealTimer, blinkTimer, blinkOffTimer, bubbleTimer, pokeTimer, slowTimer].forEach((t) =>
    clearTimeout(t),
  )
  cancelAnimationFrame(pointerRaf)
  document.title = previousTitle
  window.removeEventListener('online', syncOnlineStatus)
  window.removeEventListener('offline', syncOnlineStatus)
  window.removeEventListener('pointermove', onWindowPointerMove)
  window.removeEventListener('pointerdown', touchActivity)
  window.removeEventListener('keydown', onGlobalKeydown)
  document.removeEventListener('visibilitychange', hidePasswordWhenAway)
  void audioCtx?.close()
})
</script>

<template>
  <main
    class="kp grid min-h-screen font-['Inter',ui-sans-serif,system-ui,sans-serif] lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)]"
    :data-theme="theme"
  >
    <!-- Pengumuman untuk screen reader (satu sumber) -->
    <p class="sr-only" role="status" aria-live="polite">{{ liveMessage }}</p>

    <!-- ============================================================ -->
    <!-- Panel form (di DOM lebih dulu agar Tab langsung ke login)     -->
    <!-- ============================================================ -->
    <section
      class="relative flex items-center justify-center px-4 py-8 sm:px-6 lg:order-2"
      aria-labelledby="login-title"
    >
      <button
        type="button"
        class="kp-icon-btn absolute right-3 top-3 flex h-10 w-10 items-center justify-center rounded-lg"
        :aria-label="`Tema: ${THEME_LABEL[theme]}. Klik untuk mengganti.`"
        :title="`Tema: ${THEME_LABEL[theme]}`"
        @click="cycleTheme"
      >
        <svg
          class="h-5 w-5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path :d="THEME_ICON[theme]" />
        </svg>
      </button>

      <div class="w-full max-w-sm">
        <div class="mb-6 flex items-center gap-3 lg:hidden">
          <div
            class="flex h-10 w-10 items-center justify-center rounded-lg bg-[#164A38] text-lg font-bold text-white"
            aria-hidden="true"
          >
            K
          </div>
          <div>
            <p class="kp-strong text-base font-semibold leading-5">Koprom</p>
            <p class="kp-muted text-[13px] leading-[18px]">Koperasi Romantis</p>
          </div>
        </div>

        <header class="flex items-start justify-between gap-4">
          <div>
            <h1 id="login-title" class="kp-text text-[26px] font-semibold leading-9">
              {{ greeting }}
            </h1>
            <p class="kp-muted mt-1 text-sm leading-5">Masuk ke Koprom dengan akun Anda.</p>
            <p class="kp-subtle mt-3 text-[13px] leading-[18px]">{{ todayLabel }}</p>
          </div>

          <!-- Maskot gajah mamut: klik / Enter untuk menyapa, 5x cepat untuk kejutan -->
          <div class="relative shrink-0">
            <button
              ref="mascotButton"
              type="button"
              class="kp-mascot-btn block select-none rounded-xl"
              :class="{ 'kp-bounce': bouncing }"
              aria-label="Sapa maskot gajah mamut"
              @click="pokeMascot"
              @animationend.self="bouncing = false"
            >
              <svg
                ref="mascotEl"
                class="kp-mascot block h-[76px] w-[88px]"
                viewBox="0 0 120 104"
                aria-hidden="true"
              >
                <g :key="failureCount" :class="{ 'kp-shake': failure }">
                  <!-- telinga besar -->
                  <ellipse cx="21" cy="58" rx="17" ry="23" class="kp-mm-ear" />
                  <ellipse cx="99" cy="58" rx="17" ry="23" class="kp-mm-ear" />
                  <ellipse cx="22" cy="60" rx="9" ry="15" class="kp-mm-ear-in" />
                  <ellipse cx="98" cy="60" rx="9" ry="15" class="kp-mm-ear-in" />
                  <!-- kepala -->
                  <ellipse cx="60" cy="58" rx="36" ry="36" class="kp-mm" />
                  <!-- gading melengkung -->
                  <path d="M48 72 C34 74 28 86 31 99 C36 90 43 85 51 83 Z" class="kp-mm-tusk" />
                  <path d="M72 72 C86 74 92 86 89 99 C84 90 77 85 69 83 Z" class="kp-mm-tusk" />
                  <!-- belalai -->
                  <path d="M51 64 L69 64 L67 90 Q66 101 57 101 Q50 101 51 93 Q56 95 57 89 Z" class="kp-mm-trunk" />
                  <path d="M53 72 H67 M54 79 H66 M55 86 H65" class="kp-mm-wrinkle" />
                  <!-- bulu lebat di kepala -->
                  <path d="M25 46 Q26 26 40 27 Q44 14 54 22 Q60 8 68 22 Q78 14 82 27 Q95 26 95 46 Q78 34 60 36 Q42 34 25 46 Z" class="kp-mm-fur" />
                  <circle cx="34" cy="68" r="5.5" class="kp-mm-blush" :opacity="mascotMode === 'happy' ? 0.85 : 0.45" />
                  <circle cx="86" cy="68" r="5.5" class="kp-mm-blush" :opacity="mascotMode === 'happy' ? 0.85 : 0.45" />

                  <template v-for="eye in EYES" :key="eye.cx">
                    <path v-if="mascotMode === 'happy'" :d="arcUp(eye)" class="kp-mm-line" />
                    <path v-else-if="mascotMode === 'sleep'" :d="arcDown(eye)" class="kp-mm-line" />
                    <g v-else class="kp-eye" :class="{ 'is-blink': blinking }">
                      <circle :cx="eye.cx" :cy="eye.cy" r="8" fill="#fff" />
                      <g class="kp-pupil" :style="pupilStyle">
                        <g :class="{ 'kp-orbit': mascotMode === 'think' }">
                          <circle :cx="eye.cx" :cy="eye.cy" r="4" fill="#0F2A20" />
                          <circle :cx="eye.cx + 1.6" :cy="eye.cy - 1.6" r="1.3" fill="#fff" />
                        </g>
                      </g>
                    </g>
                  </template>

                  <template v-if="mascotMode === 'sad'">
                    <path d="M35 43 L52 39" class="kp-mm-line" />
                    <path d="M68 39 L85 43" class="kp-mm-line" />
                  </template>
                </g>

                <text v-if="mascotMode === 'sleep'" x="92" y="24" class="kp-z">z</text>
                <text v-if="mascotMode === 'sleep'" x="100" y="14" class="kp-z kp-z-late">z</text>

                <g v-if="isSuccess" class="kp-coin">
                  <circle cx="60" cy="18" r="8" fill="#f2c14e" stroke="#c99a2e" stroke-width="2" />
                  <circle cx="60" cy="18" r="3.5" fill="none" stroke="#c99a2e" stroke-width="1.5" />
                </g>

                <g class="kp-hoof" :style="{ transform: hoofs.l }">
                  <ellipse rx="13" ry="11" class="kp-mm-paw" />
                  <path d="M-4 -2 V4 M4 -2 V4" class="kp-mm-line" stroke-width="2" />
                </g>
                <g class="kp-hoof" :style="{ transform: hoofs.r }">
                  <ellipse rx="13" ry="11" class="kp-mm-paw" />
                  <path d="M-4 -2 V4 M4 -2 V4" class="kp-mm-line" stroke-width="2" />
                </g>
              </svg>
            </button>
            <p v-if="bubble" class="kp-bubble" aria-hidden="true">{{ bubble }}</p>
          </div>
        </header>

        <div class="mt-6 space-y-3 empty:hidden">
          <p v-if="isOffline" class="kp-alert kp-alert-warn" role="status">
            Anda sedang offline. Sambungkan internet untuk masuk.
          </p>
          <p v-if="notice" class="kp-alert kp-alert-info" role="status">{{ notice }}</p>
        </div>

        <form class="mt-6 space-y-5" novalidate @submit.prevent="handleSubmit">
          <div aria-live="assertive">
            <div
              v-if="failure"
              :key="failureCount"
              class="kp-alert kp-alert-danger kp-nudge flex-col"
              role="alert"
            >
              <div class="flex items-start gap-2">
                <svg class="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm-.75-11.5a.75.75 0 011.5 0v4a.75.75 0 01-1.5 0v-4zM10 14.5a1 1 0 100-2 1 1 0 000 2z"
                    clip-rule="evenodd"
                  />
                </svg>
                <span>{{ failure.message }}</span>
              </div>
              <div v-if="isLocked" class="kp-lock-track" aria-hidden="true">
                <span class="kp-lock-bar" :style="{ transform: `scaleX(${lockProgress})` }"></span>
              </div>
            </div>
          </div>

          <div>
            <label for="username" class="kp-text block text-sm font-medium leading-5">Username</label>
            <input
              id="username"
              ref="usernameInput"
              v-model="username"
              name="username"
              type="text"
              inputmode="text"
              autocomplete="username"
              autocapitalize="none"
              autocorrect="off"
              spellcheck="false"
              :disabled="isBusy"
              :aria-invalid="Boolean(usernameError)"
              :aria-describedby="usernameError ? 'username-error' : undefined"
              class="kp-field mt-2 block w-full rounded-lg px-3 py-2.5 text-base leading-6"
              @focus="focusedField = 'username'"
              @blur="onUsernameBlur"
              @input="usernameError && validateUsername()"
              @keydown.enter.prevent="onUsernameEnter"
            />
            <p v-if="usernameError" id="username-error" class="kp-danger-text mt-2 text-[13px] leading-[18px]">
              {{ usernameError }}
            </p>
          </div>

          <div>
            <label for="password" class="kp-text block text-sm font-medium leading-5">Password</label>
            <div class="relative mt-2">
              <input
                id="password"
                ref="passwordInput"
                v-model="password"
                name="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                :disabled="isBusy"
                :aria-invalid="Boolean(passwordError)"
                :aria-describedby="describedByPassword"
                class="kp-field block w-full rounded-lg py-2.5 pl-3 pr-11 text-base leading-6"
                @focus="focusedField = 'password'"
                @blur="onPasswordBlur"
                @keydown="updateCapsLock"
                @keydown.esc="onPasswordEscape"
                @keyup="updateCapsLock"
                @input="passwordError && validatePassword()"
              />
              <button
                type="button"
                :disabled="isBusy"
                :aria-pressed="showPassword"
                :aria-label="showPassword ? 'Sembunyikan password' : 'Tampilkan password'"
                class="kp-icon-btn absolute inset-y-0 right-0 flex w-11 items-center justify-center rounded-r-lg"
                @click="showPassword = !showPassword"
              >
                <svg
                  class="h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.75"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                >
                  <path :d="showPassword ? EYE_OFF_ICON : EYE_ICON" />
                </svg>
              </button>
            </div>
            <p v-if="capsLockOn" id="capslock-hint" class="kp-muted mt-2 flex items-center gap-1.5 text-[13px] leading-[18px]">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M12 4 5 12h4v4h6v-4h4zM9 20h6" />
              </svg>
              Caps Lock sedang aktif.
            </p>
            <p v-if="passwordError" id="password-error" class="kp-danger-text mt-2 text-[13px] leading-[18px]">
              {{ passwordError }}
            </p>
          </div>

          <label class="kp-muted flex cursor-pointer items-center gap-2 text-sm leading-5">
            <input
              v-model="rememberUsername"
              type="checkbox"
              name="remember"
              :disabled="isBusy"
              class="kp-check h-4 w-4 rounded"
            />
            Ingat username di perangkat ini
          </label>

          <div>
            <button
              ref="submitButton"
              type="submit"
              :disabled="!canSubmit"
              :aria-busy="isLoading"
              :data-state="status"
              class="kp-btn relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-lg px-4 py-2.5 text-sm font-semibold"
              @pointerdown="addRipple"
            >
              <span
                v-for="r in ripples"
                :key="r.id"
                class="kp-ripple"
                :style="{ left: `${r.x}px`, top: `${r.y}px` }"
                @animationend="removeRipple(r.id)"
              ></span>
              <svg
                v-if="isLoading"
                class="h-4 w-4 animate-spin motion-reduce:animate-none"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              <svg
                v-else-if="isSuccess"
                class="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="3"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path class="kp-check-draw" d="M5 12.5l4.5 4.5L19 7.5" />
              </svg>
              <span class="relative">{{ submitLabel }}</span>
            </button>

            <div class="mt-2 min-h-5 text-center text-[13px] leading-5" aria-live="polite">
              <template v-if="isLoading">
                <span class="kp-muted">{{ slowHint ? 'Koneksi lambat, mohon tunggu... ' : '' }}</span>
                <button type="button" class="kp-link" @click="cancelLogin">Batalkan</button>
              </template>
            </div>
          </div>

          <span class="sr-only" role="status">
            {{ isLoading ? 'Sedang memproses login' : isSuccess ? 'Login berhasil, mengalihkan halaman' : '' }}
          </span>
        </form>

        <p class="kp-subtle mt-6 text-[13px] leading-[18px]">
          Lupa password? Hubungi pengurus koperasi untuk reset akun.
        </p>

        <footer class="kp-divider kp-subtle mt-8 border-t pt-4 text-[13px] leading-[18px]">
          © {{ now.getFullYear() }} Koprom<template v-if="appVersion"> · v{{ appVersion }}</template>
        </footer>
      </div>
    </section>

    <!-- ============================================================ -->
    <!-- Panel merek + simulasi kasir (desktop)                        -->
    <!-- ============================================================ -->
    <aside
      class="kp-ledger relative hidden overflow-hidden bg-[#164A38] p-10 text-white lg:order-1 lg:flex lg:flex-col lg:justify-between"
      :class="{ 'is-spot': spot.on }"
      :style="{ '--mx': `${spot.x}px`, '--my': `${spot.y}px` }"
      aria-label="Simulasi kasir Koprom"
      @pointermove="onAsideMove"
      @pointerleave="onAsideLeave"
    >
      <div class="relative z-10 flex items-center justify-between gap-3">
        <div class="flex items-center gap-3" aria-hidden="true">
          <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-white text-lg font-bold text-[#164A38]">
            K
          </div>
          <div>
            <p class="text-base font-semibold leading-5">Koprom</p>
            <p class="text-[13px] leading-[18px] text-white/70">Koperasi Romantis</p>
          </div>
        </div>

        <button
          type="button"
          class="kp-ghost flex h-9 items-center gap-2 !px-3"
          :aria-pressed="soundOn"
          @click="toggleSound"
        >
          <svg
            class="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path :d="soundOn ? SOUND_ON_ICON : SOUND_OFF_ICON" />
          </svg>
          Suara {{ soundOn ? 'aktif' : 'mati' }}
        </button>
      </div>

      <div class="relative z-10 mx-auto w-full max-w-xs">
        <!-- Printer + struk -->
        <div class="kp-tilt" :style="{ '--tx': `${tilt.x}deg`, '--ty': `${tilt.y}deg` }">
          <div class="kp-printer" aria-hidden="true">
            <span class="kp-printer-label">KP-58 Printer</span>
            <span class="kp-led" :class="{ 'is-busy': feeding }"></span>
          </div>

          <div class="kp-slot" :class="{ 'is-feeding': feeding }">
            <div :key="printKey" class="kp-receipt" @animationend.self="feeding = false">
              <div class="kp-drop" :class="{ 'is-torn': paid }">
                <div
                  class="kp-receipt-paper relative bg-[#F7FBF9] px-6 pb-7 pt-5 font-mono text-[13px] leading-6 text-[#12261E]"
                  :class="{ 'is-torn': paid }"
                >
                  <p class="text-center font-semibold">KOPROM</p>
                  <p class="text-center text-[12px] text-[#3F5A4F]">{{ receiptStamp }}</p>
                  <div class="my-2 border-t border-dashed border-[#6B8579]"></div>

                  <p v-if="!cartLines.length" class="py-2 text-center text-[#3F5A4F]">
                    Belum ada barang
                  </p>

                  <TransitionGroup name="kp-line" tag="div" class="kp-lines" :class="{ 'is-locked': paid }">
                    <div v-for="line in cartLines" :key="line.id" class="kp-line">
                      <span class="kp-qty">
                        <button
                          type="button"
                          class="kp-step"
                          :aria-label="`Kurangi ${line.name}`"
                          :disabled="paid"
                          @click="removeItem(line)"
                        >
                          &minus;
                        </button>
                        <span>{{ line.qty }}&times;</span>
                        <button
                          type="button"
                          class="kp-step"
                          :aria-label="`Tambah ${line.name}`"
                          :disabled="paid || line.qty >= MAX_QTY"
                          @click="addItem(line)"
                        >
                          +
                        </button>
                      </span>
                      <span class="truncate">{{ line.name }}</span>
                      <span class="text-right">{{ rupiah.format(line.subtotal) }}</span>
                    </div>
                  </TransitionGroup>

                  <div class="my-2 border-t border-dashed border-[#6B8579]"></div>
                  <div class="flex justify-between font-semibold">
                    <span>Total</span><span>{{ rupiah.format(shownTotal) }}</span>
                  </div>
                  <template v-if="method === 'cash'">
                    <div class="flex justify-between text-[#3F5A4F]">
                      <span>Tunai</span><span>{{ rupiah.format(shownCash) }}</span>
                    </div>
                    <div class="flex justify-between text-[#3F5A4F]">
                      <span>Kembali</span><span>{{ rupiah.format(shownChange) }}</span>
                    </div>
                  </template>
                  <div v-else class="flex justify-between text-[#3F5A4F]">
                    <span>{{ METHOD_LABEL[method] }}</span><span>{{ rupiah.format(shownTotal) }}</span>
                  </div>
                  <div v-if="method === 'debit'" class="flex justify-between text-[#3F5A4F]">
                    <span>Rek.</span><span>{{ maskedAccount || '-' }}</span>
                  </div>

                  <div v-if="method === 'qris'" class="kp-qris">
                    <div class="kp-qr-frame" :class="{ 'is-dim': paid || !receiptTotal }">
                      <svg
                        :key="qrPath"
                        class="kp-qr kp-qr-in"
                        :viewBox="qrViewBox"
                        shape-rendering="crispEdges"
                        role="img"
                        aria-label="Kode QRIS simulasi"
                      >
                        <rect width="100%" height="100%" fill="#fff" />
                        <path :d="qrPath" fill="#12261E" />
                      </svg>
                      <span
                        v-if="paid && receiptTotal > 0"
                        :key="stampKey"
                        class="kp-stamp kp-stamp--in"
                      >
                        LUNAS
                      </span>
                    </div>
                    <p class="mt-1.5 text-center text-[12px] font-semibold leading-4">
                      {{ receiptTotal ? 'Pindai untuk membayar' : 'Pilih barang untuk membuat QR' }}
                    </p>
                    <p class="text-center text-[10px] leading-4 text-[#6B8579]">Simulasi, bukan kode sungguhan</p>
                  </div>
                  <div v-else class="kp-barcode mt-3 h-7"></div>
                  <p class="mt-1 text-center text-[11px] text-[#3F5A4F]">{{ receiptCode }}</p>

                  <span v-if="scanKey > 0 && !paid" :key="scanKey" class="kp-scan" aria-hidden="true"></span>

                  <span v-if="paid && receiptTotal > 0 && method !== 'qris'" :key="stampKey" class="kp-stamp">LUNAS</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Meja kasir: ringkas saat belanja, tenang saat sudah dibayar -->
        <div ref="deskEl" class="kp-desk">
          <Transition name="kp-swap" mode="out-in">
            <div v-if="!paid" key="shop" class="space-y-3">
              <div class="grid grid-cols-3 gap-1.5">
                <button
                  v-for="(p, i) in products"
                  :key="p.id"
                  type="button"
                  class="kp-chip relative text-left"
                  :aria-label="`Tambah ${p.name}`"
                  :aria-keyshortcuts="String(i + 1)"
                  @click="addItem(p)"
                >
                  <span class="block text-[12px] font-medium leading-4">{{ p.name }}</span>
                  <span class="block text-[11px] leading-4 text-white/60">{{ rupiah.format(p.price) }}</span>
                  <span v-if="cart[p.id]" :key="cart[p.id]" class="kp-badge">{{ cart[p.id] }}</span>
                </button>
              </div>

              <div class="kp-seg" role="radiogroup" aria-label="Metode pembayaran">
                <button
                  v-for="m in METHODS"
                  :key="m.value"
                  type="button"
                  role="radio"
                  :aria-checked="method === m.value"
                  @click="setMethod(m.value)"
                >
                  {{ m.label }}
                </button>
              </div>

              <div v-if="method === 'cash'" class="flex items-center gap-1.5" role="group" aria-label="Uang diterima">
                <span class="mr-0.5 text-[12px] leading-5 text-white/65">Diterima</span>
                <button
                  v-for="opt in cashOptions"
                  :key="opt.label"
                  type="button"
                  class="kp-pill"
                  :aria-pressed="activeCash === opt.value"
                  :disabled="cashDisabled(opt.value)"
                  @click="chooseCash(opt.value)"
                >
                  {{ opt.label }}
                </button>
              </div>

              <div v-if="method === 'debit'" class="flex flex-col gap-1">
                <div class="flex items-center gap-2">
                  <label for="acct" class="mr-0.5 shrink-0 text-[12px] leading-5 text-white/65">Rekening</label>
                  <input
                    id="acct"
                    class="kp-acct"
                    type="text"
                    inputmode="numeric"
                    autocomplete="off"
                    placeholder="10-16 digit nomor rekening"
                    :value="accountDisplay"
                    :aria-invalid="accountTouched && !accountValid"
                    aria-describedby="acct-hint"
                    @input="onAccountInput"
                    @blur="accountTouched = true"
                    @keydown.enter.prevent="payCart"
                  />
                </div>
                <p v-if="accountTouched && !accountValid" id="acct-hint" class="text-[11px] leading-4 text-[#ffb4a8]">
                  Nomor rekening harus 10 sampai 16 digit.
                </p>
              </div>

              <div class="flex items-center gap-2">
                <button
                  ref="payButton"
                  type="button"
                  class="kp-solid-light flex-1"
                  :disabled="!canPay"
                  @click="payCart"
                >
                  {{ method === 'qris' ? 'Konfirmasi' : 'Bayar' }}
                  {{ receiptTotal ? `Rp${rupiah.format(receiptTotal)}` : '' }}
                </button>
                <button type="button" class="kp-text-btn" :disabled="!cartLines.length" @click="clearCart">
                  Kosongkan
                </button>
              </div>
            </div>

            <div v-else key="done" class="kp-done">
              <span class="kp-done-icon" aria-hidden="true">
                <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                  <path class="kp-check-draw" d="M5 12.5l4.5 4.5L19 7.5" />
                </svg>
              </span>
              <p class="mt-3 text-base font-semibold leading-6">Pembayaran lunas</p>
              <p class="text-[12px] leading-4 text-white/65">{{ METHOD_LABEL[method] }}<template v-if="method === 'debit' && maskedAccount"> {{ maskedAccount }}</template> &middot; {{ receiptCode }}</p>

              <p class="mt-4 text-[12px] leading-4 text-white/65">
                {{ method === 'cash' ? 'Kembalian' : 'Total dibayar' }}
              </p>
              <p class="text-3xl font-semibold leading-9 tabular-nums">
                Rp{{ rupiah.format(method === 'cash' ? shownChange : shownTotal) }}
              </p>

              <button type="button" class="kp-solid-light kp-new mt-5 w-full" @click="newTransaction">
                Transaksi baru
              </button>
            </div>
          </Transition>
        </div>
      </div>

      <div class="relative z-10">
        <p class="max-w-md text-xl font-semibold leading-7">
          Kasir, stok, dan laporan toko dalam satu sistem.
        </p>
        <p class="mt-1 text-[13px] leading-[18px] text-white/70">
          Ketuk barang atau tekan tombol 1&ndash;6 untuk mencoba kasirnya.
        </p>
      </div>
    </aside>

    <!-- Partikel koin (dekoratif) -->
    <div class="pointer-events-none fixed inset-0 z-50" aria-hidden="true">
      <span
        v-for="piece in pieces"
        :key="piece.id"
        class="kp-piece"
        :style="{
          left: `${piece.x}px`,
          top: `${piece.y}px`,
          '--dx': `${piece.dx}px`,
          '--dy': `${piece.dy}px`,
          '--rot': `${piece.rot}deg`,
        }"
      ></span>
    </div>

    <!-- Transisi sukses: layar membesar dari tombol -->
    <div
      v-if="wipe"
      class="kp-wipe"
      :style="{ '--wx': `${wipe.x}px`, '--wy': `${wipe.y}px` }"
      role="status"
    >
      <div class="kp-wipe-text">
        <svg class="mx-auto h-10 w-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="10" />
          <path class="kp-check-draw" d="M7.5 12.5l3 3 6-7" />
        </svg>
        <p class="mt-3 text-xl font-semibold leading-7">Selamat datang, {{ wipe.name }}</p>
        <p class="mt-1 text-sm text-white/75">Menyiapkan halaman Anda...</p>
      </div>
    </div>
  </main>
</template>

<style scoped>
/* ---------- Design tokens (light default; dark via atribut atau preferensi sistem) ---------- */
.kp {
  --kp-bg: #F4FAF7;
  --kp-surface: #ffffff;
  --kp-text: #12261E;
  --kp-strong: #0F3527;
  --kp-muted: #3F5A4F;
  --kp-subtle: #587066;
  --kp-border: #CFE3DA;
  --kp-border-strong: #6B8579;
  --kp-disabled-bg: #EDF5F1;
  --kp-primary: #164A38;
  --kp-primary-hover: #1F6B51;
  --kp-primary-press: #0F3527;
  --kp-on-primary: #ffffff;
  --kp-focus: #164A38;
  --kp-danger: #b3321f;
  --kp-info: #1c5a8a;
  --kp-warn: #8a5a00;

  background: var(--kp-bg);
  color: var(--kp-text);
  color-scheme: light;
}

.kp[data-theme='dark'] {
  --kp-bg: #0E1A15;
  --kp-surface: #15251E;
  --kp-text: #E8F5EE;
  --kp-strong: #E8F5EE;
  --kp-muted: #A9C7B8;
  --kp-subtle: #86A596;
  --kp-border: #264238;
  --kp-border-strong: #4F7263;
  --kp-disabled-bg: #1B3028;
  --kp-primary: #86D9B5;
  --kp-primary-hover: #B0EBD0;
  --kp-primary-press: #5CC79C;
  --kp-on-primary: #052E20;
  --kp-focus: #86D9B5;
  --kp-danger: #ff8a7a;
  --kp-info: #8cc4f0;
  --kp-warn: #f0c36b;
  color-scheme: dark;
}

@media (prefers-color-scheme: dark) {
  .kp[data-theme='system'] {
    --kp-bg: #0E1A15;
    --kp-surface: #15251E;
    --kp-text: #E8F5EE;
    --kp-strong: #E8F5EE;
    --kp-muted: #A9C7B8;
    --kp-subtle: #86A596;
    --kp-border: #264238;
    --kp-border-strong: #4F7263;
    --kp-disabled-bg: #1B3028;
    --kp-primary: #86D9B5;
    --kp-primary-hover: #B0EBD0;
    --kp-primary-press: #5CC79C;
    --kp-on-primary: #052E20;
    --kp-focus: #86D9B5;
    --kp-danger: #ff8a7a;
    --kp-info: #8cc4f0;
    --kp-warn: #f0c36b;
    color-scheme: dark;
  }
}

.kp-text { color: var(--kp-text); }
.kp-strong { color: var(--kp-strong); }
.kp-muted { color: var(--kp-muted); }
.kp-subtle { color: var(--kp-subtle); }
.kp-danger-text { color: var(--kp-danger); }
.kp-divider { border-color: var(--kp-border); }

.kp :is(input, button):focus-visible {
  outline: 2px solid var(--kp-focus);
  outline-offset: 2px;
}
.kp-icon-btn:focus-visible { outline-offset: -2px; }

.kp-link {
  color: var(--kp-primary);
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.kp-link:hover { color: var(--kp-primary-hover); }

/* ---------- Field ---------- */
.kp-field {
  background: var(--kp-surface);
  color: var(--kp-text);
  border: 1px solid var(--kp-border);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.kp-field:hover:not(:disabled) { border-color: var(--kp-border-strong); }
.kp-field:focus-visible { border-color: var(--kp-primary); }
.kp-field[aria-invalid='true'] { border-color: var(--kp-danger); }
.kp-field:disabled {
  background: var(--kp-disabled-bg);
  color: var(--kp-subtle);
  cursor: not-allowed;
}
.kp-check { accent-color: var(--kp-primary); }

.kp-icon-btn { color: var(--kp-muted); }
.kp-icon-btn:hover:not(:disabled) { color: var(--kp-primary); }
.kp-icon-btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* ---------- Tombol utama + ripple ---------- */
.kp-btn {
  background: var(--kp-primary);
  color: var(--kp-on-primary);
  transition: background-color 0.15s, transform 0.1s;
}
.kp-btn:hover:not(:disabled) { background: var(--kp-primary-hover); }
.kp-btn:active:not(:disabled) { background: var(--kp-primary-press); transform: scale(0.99); }
.kp-btn:disabled { opacity: 0.7; cursor: not-allowed; }
.kp-btn[data-state='success']:disabled { opacity: 1; cursor: default; }

.kp-ripple {
  position: absolute;
  width: 8px;
  height: 8px;
  margin: -4px 0 0 -4px;
  border-radius: 9999px;
  background: currentColor;
  opacity: 0.3;
  pointer-events: none;
  animation: kp-ripple 0.6s ease-out forwards;
}
@keyframes kp-ripple {
  to { transform: scale(48); opacity: 0; }
}

.kp-check-draw {
  stroke-dasharray: 24;
  animation: kp-draw 0.3s ease-out both;
}
@keyframes kp-draw {
  from { stroke-dashoffset: 24; }
  to { stroke-dashoffset: 0; }
}

/* ---------- Alert ---------- */
.kp-alert {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  border-radius: 0.5rem;
  border: 1px solid color-mix(in srgb, var(--alert) 35%, transparent);
  background: color-mix(in srgb, var(--alert) 8%, transparent);
  color: var(--alert);
  padding: 0.625rem 0.75rem;
  font-size: 0.875rem;
  line-height: 1.25rem;
}
.kp-alert-danger { --alert: var(--kp-danger); }
.kp-alert-info { --alert: var(--kp-info); }
.kp-alert-warn { --alert: var(--kp-warn); }

.kp-nudge { animation: kp-nudge 0.32s ease-out; }
@keyframes kp-nudge {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.kp-lock-track {
  width: 100%;
  height: 4px;
  overflow: hidden;
  border-radius: 9999px;
  background: color-mix(in srgb, var(--alert) 18%, transparent);
}
.kp-lock-bar {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 9999px;
  background: var(--alert);
  transform-origin: left center;
  transition: transform 0.5s linear;
}

/* ---------- Maskot gajah mamut hijau ---------- */
.kp-mascot-btn { line-height: 0; }
.kp-mascot {
  --mm: #4FB38A;
  --mm-trunk: #8FD6B8;
  --mm-ear: #34966E;
  --mm-ear-in: #CDEFE0;
  --mm-fur: #1F6B51;
  --mm-dark: #0F3527;
  --mm-paw: #45A982;
  --mm-tusk: #f7edd0;
  --mm-tusk-edge: #d5c18f;
  --mm-blush: #F4A58A;
}
.kp-mm { fill: var(--mm); }
.kp-mm-ear { fill: var(--mm-ear); }
.kp-mm-ear-in { fill: var(--mm-ear-in); opacity: 0.7; }
.kp-mm-fur { fill: var(--mm-fur); }
.kp-mm-trunk { fill: var(--mm-trunk); stroke: var(--mm-ear); stroke-width: 1.5; stroke-linejoin: round; }
.kp-mm-wrinkle { fill: none; stroke: var(--mm-ear); stroke-width: 1.5; stroke-linecap: round; }
.kp-mm-tusk { fill: var(--mm-tusk); stroke: var(--mm-tusk-edge); stroke-width: 1.5; stroke-linejoin: round; }
.kp-mm-blush { fill: var(--mm-blush); }
.kp-mm-paw { fill: var(--mm-paw); stroke: var(--mm-dark); stroke-width: 1.5; }
.kp-mm-line {
  fill: none;
  stroke: var(--mm-dark);
  stroke-width: 3;
  stroke-linecap: round;
}
.kp-eye {
  transform-box: fill-box;
  transform-origin: center;
  transition: transform 0.08s;
}
.kp-eye.is-blink { transform: scaleY(0.1); }
.kp-pupil { transition: transform 0.12s ease-out; }
.kp-hoof { transition: transform 0.4s cubic-bezier(0.3, 1.3, 0.5, 1); }

.kp-orbit { animation: kp-orbit 0.9s linear infinite; }
@keyframes kp-orbit {
  0% { transform: translate(2.5px, 0); }
  25% { transform: translate(0, 2.5px); }
  50% { transform: translate(-2.5px, 0); }
  75% { transform: translate(0, -2.5px); }
  100% { transform: translate(2.5px, 0); }
}

.kp-z {
  fill: var(--kp-subtle);
  font-size: 13px;
  font-weight: 700;
  animation: kp-float 2s ease-in-out infinite;
}
.kp-z-late { animation-delay: 0.9s; font-size: 10px; }
@keyframes kp-float {
  0% { opacity: 0; transform: translateY(6px); }
  40% { opacity: 1; }
  100% { opacity: 0; transform: translateY(-8px); }
}

.kp-shake {
  transform-origin: 60px 58px;
  animation: kp-headshake 0.5s ease-in-out;
}
@keyframes kp-headshake {
  0%, 100% { transform: rotate(0); }
  20% { transform: rotate(-7deg); }
  45% { transform: rotate(6deg); }
  70% { transform: rotate(-4deg); }
}

.kp-coin { animation: kp-coin 0.5s ease-in both; }
@keyframes kp-coin {
  0% { transform: translateY(-34px); opacity: 1; }
  75% { transform: translateY(2px); opacity: 1; }
  100% { transform: translateY(6px) scaleY(0.2); opacity: 0; }
}

.kp-bounce { animation: kp-bounce 0.45s cubic-bezier(0.3, 1.5, 0.5, 1); }
@keyframes kp-bounce {
  0% { transform: scale(1); }
  35% { transform: scale(1.12, 0.9) translateY(2px); }
  70% { transform: scale(0.96, 1.06) translateY(-4px); }
  100% { transform: scale(1); }
}

.kp-bubble {
  position: absolute;
  right: 0;
  top: 100%;
  z-index: 5;
  margin-top: 0.25rem;
  width: max-content;
  max-width: 12rem;
  border: 1px solid var(--kp-border);
  border-radius: 0.5rem;
  background: var(--kp-surface);
  color: var(--kp-text);
  padding: 0.375rem 0.625rem;
  font-size: 0.8125rem;
  line-height: 1.125rem;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
  animation: kp-pop 0.2s ease-out;
}
@keyframes kp-pop {
  from { opacity: 0; transform: scale(0.92); }
  to { opacity: 1; transform: scale(1); }
}

/* ---------- Partikel koin ---------- */
.kp-piece {
  position: fixed;
  width: 10px;
  height: 10px;
  margin: -5px 0 0 -5px;
  border: 2px solid #c99a2e;
  border-radius: 9999px;
  background: #f2c14e;
  animation: kp-piece 1.1s cubic-bezier(0.2, 0.7, 0.4, 1) forwards;
}
@keyframes kp-piece {
  0% { opacity: 1; transform: translate(0, 0) rotate(0); }
  45% { opacity: 1; transform: translate(var(--dx), var(--dy)) rotate(calc(var(--rot) * 0.5)); }
  100% { opacity: 0; transform: translate(var(--dx), calc(var(--dy) + 90px)) rotate(var(--rot)); }
}

/* ---------- Transisi sukses ---------- */
.kp-wipe {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #164A38;
  color: #fff;
  text-align: center;
  clip-path: circle(0 at var(--wx) var(--wy));
  animation: kp-wipe 0.65s cubic-bezier(0.65, 0, 0.35, 1) forwards;
}
@keyframes kp-wipe {
  to { clip-path: circle(150vmax at var(--wx) var(--wy)); }
}
.kp-wipe-text { opacity: 0; animation: kp-fade-in 0.3s ease-out 0.35s forwards; }
@keyframes kp-fade-in {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ---------- Panel merek: kertas buku kas + spotlight ---------- */
.kp-ledger {
  background-image:
    linear-gradient(90deg, transparent 47px, rgba(255, 255, 255, 0.09) 47px 48px, transparent 48px),
    repeating-linear-gradient(0deg, transparent 0 31px, rgba(255, 255, 255, 0.045) 31px 32px);
}
.kp-ledger::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0;
  background: radial-gradient(340px circle at var(--mx, 50%) var(--my, 30%), rgba(255, 255, 255, 0.11), transparent 62%);
  transition: opacity 0.3s;
}
.kp-ledger.is-spot::after { opacity: 1; }
.kp-ledger :is(button):focus-visible {
  outline: 2px solid #fff;
  outline-offset: 2px;
}

/* ---------- Printer termal ---------- */
.kp-tilt {
  transform: rotate(-2deg) perspective(900px) rotateX(var(--tx, 0deg)) rotateY(var(--ty, 0deg));
  transition: transform 0.25s ease-out;
}
.kp-printer {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 2.25rem;
  padding: 0 0.875rem;
  border-radius: 0.75rem;
  background: #0C2A20;
  box-shadow: inset 0 -6px 0 rgba(0, 0, 0, 0.35), 0 6px 14px rgba(0, 0, 0, 0.25);
}
.kp-printer-label {
  color: rgba(255, 255, 255, 0.45);
  font-size: 10px;
  letter-spacing: 0.06em;
}
.kp-led {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 9999px;
  background: #6EE7B7;
  box-shadow: 0 0 8px #6EE7B7;
}
.kp-led.is-busy {
  background: #f2c14e;
  box-shadow: 0 0 8px #f2c14e;
  animation: kp-blink 0.35s steps(2, start) infinite;
}
@keyframes kp-blink {
  to { opacity: 0.25; }
}

/* Slot: menempel di bawah printer, memotong struk hanya saat sedang keluar */
.kp-slot {
  margin: -0.375rem 0.5rem 0;
  padding: 0 0.5rem 1.5rem;
}
.kp-slot.is-feeding { overflow: hidden; }

/* Struk keluar bergaris-garis (steps) seperti printer termal */
.kp-receipt {
  filter: drop-shadow(0 14px 22px rgba(0, 0, 0, 0.3));
  animation: kp-feed 1.7s steps(18, end) both;
}
@keyframes kp-feed {
  from { transform: translateY(-100%); }
  to { transform: translateY(0); }
}

/* Setelah dibayar: struk disobek, turun sedikit, tepi atas bergerigi */
.kp-drop {
  transform-origin: 50% 0;
  transition: transform 0.5s cubic-bezier(0.3, 1.3, 0.5, 1) 0.25s;
}
.kp-drop.is-torn { transform: translateY(18px) rotate(2.2deg); }

.kp-receipt-paper {
  overflow: hidden;
  clip-path: polygon(
    0 0, 100% 0, 100% calc(100% - 8px),
    95% 100%, 90% calc(100% - 8px), 85% 100%, 80% calc(100% - 8px),
    75% 100%, 70% calc(100% - 8px), 65% 100%, 60% calc(100% - 8px),
    55% 100%, 50% calc(100% - 8px), 45% 100%, 40% calc(100% - 8px),
    35% 100%, 30% calc(100% - 8px), 25% 100%, 20% calc(100% - 8px),
    15% 100%, 10% calc(100% - 8px), 5% 100%, 0 calc(100% - 8px)
  );
}
.kp-receipt-paper.is-torn {
  clip-path: polygon(
    0 8px, 5% 0, 10% 8px, 15% 0, 20% 8px, 25% 0, 30% 8px, 35% 0, 40% 8px, 45% 0,
    50% 8px, 55% 0, 60% 8px, 65% 0, 70% 8px, 75% 0, 80% 8px, 85% 0, 90% 8px, 95% 0, 100% 8px,
    100% calc(100% - 8px),
    95% 100%, 90% calc(100% - 8px), 85% 100%, 80% calc(100% - 8px),
    75% 100%, 70% calc(100% - 8px), 65% 100%, 60% calc(100% - 8px),
    55% 100%, 50% calc(100% - 8px), 45% 100%, 40% calc(100% - 8px),
    35% 100%, 30% calc(100% - 8px), 25% 100%, 20% calc(100% - 8px),
    15% 100%, 10% calc(100% - 8px), 5% 100%, 0 calc(100% - 8px)
  );
}

.kp-barcode {
  background: repeating-linear-gradient(
    90deg,
    #12261E 0 2px, transparent 2px 4px,
    #12261E 4px 5px, transparent 5px 8px,
    #12261E 8px 11px, transparent 11px 13px
  );
}
.kp-scan {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 2px;
  background: #22A06B;
  box-shadow: 0 0 10px 2px rgba(34, 160, 107, 0.55);
  pointer-events: none;
  animation: kp-scan 0.5s ease-in-out forwards;
}
@keyframes kp-scan {
  0% { top: 0; opacity: 0; }
  15% { opacity: 1; }
  85% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

/* Cap LUNAS di atas barcode, tidak menutupi angka */
.kp-stamp {
  position: absolute;
  left: 50%;
  bottom: 3.3rem;
  border: 2px solid #164A38;
  outline: 1.5px solid #164A38;
  outline-offset: 2px;
  border-radius: 6px;
  background: rgba(248, 250, 249, 0.78);
  color: #164A38;
  padding: 0 0.625rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  transform: translateX(-50%) rotate(-8deg);
  animation: kp-stamp 0.28s cubic-bezier(0.3, 1.4, 0.5, 1) 0.05s both;
}
@keyframes kp-stamp {
  from { opacity: 0; transform: translateX(-50%) rotate(-8deg) scale(1.8); }
  to { opacity: 0.95; transform: translateX(-50%) rotate(-8deg) scale(1); }
}

/* QRIS: bingkai QR di struk */
.kp-qris {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 0.75rem;
}
.kp-qr-frame {
  position: relative;
  width: 6.75rem;
  height: 6.75rem;
  border: 1px solid #CFE3DA;
  border-radius: 0.5rem;
  background: #fff;
  padding: 0.125rem;
}
.kp-qr {
  display: block;
  width: 100%;
  height: 100%;
  transition: opacity 0.3s;
}
.kp-qr-frame.is-dim .kp-qr { opacity: 0.25; }
.kp-qr-in { animation: kp-qr-in 0.25s ease-out; }
@keyframes kp-qr-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Cap LUNAS tepat di tengah QR */
.kp-stamp--in {
  top: 50%;
  bottom: auto;
  transform: translate(-50%, -50%) rotate(-8deg);
  animation-name: kp-stamp-in;
}
@keyframes kp-stamp-in {
  from { opacity: 0; transform: translate(-50%, -50%) rotate(-8deg) scale(1.8); }
  to { opacity: 0.95; transform: translate(-50%, -50%) rotate(-8deg) scale(1); }
}

/* Baris struk: stepper − qty + | nama | harga */
.kp-lines { position: relative; }
.kp-line {
  display: grid;
  grid-template-columns: 4.1rem minmax(0, 1fr) auto;
  align-items: center;
  column-gap: 0.25rem;
}
.kp-qty {
  display: inline-flex;
  align-items: center;
  gap: 0.125rem;
  white-space: nowrap;
}
.kp-step {
  width: 1.15rem;
  height: 1.15rem;
  border-radius: 4px;
  color: #164A38;
  font-weight: 700;
  line-height: 1.15rem;
  text-align: center;
  opacity: 0;
  transition: opacity 0.12s, background-color 0.12s;
}
.kp-step:hover:not(:disabled) { background: rgba(22, 74, 56, 0.14); }
.kp-step:disabled { color: #9DB8AA; cursor: not-allowed; }
.kp-line:hover .kp-step,
.kp-line:focus-within .kp-step { opacity: 1; }
.kp-lines.is-locked .kp-step { visibility: hidden; }
@media (hover: none) {
  .kp-step { opacity: 1; }
}
.kp-receipt .kp-step:focus-visible { outline-color: #164A38; outline-offset: 0; }

.kp-line-enter-active,
.kp-line-leave-active { transition: opacity 0.22s, transform 0.22s; }
.kp-line-enter-from,
.kp-line-leave-to { opacity: 0; transform: translateX(-8px); }
.kp-line-leave-active { position: absolute; left: 0; right: 0; }
.kp-line-move { transition: transform 0.22s; }

/* ---------- Meja kasir ---------- */
.kp-desk {
  min-height: 15rem;
  margin-top: 1rem;
}
.kp-swap-enter-active,
.kp-swap-leave-active { transition: opacity 0.18s, transform 0.18s; }
.kp-swap-enter-from,
.kp-swap-leave-to { opacity: 0; transform: translateY(6px); }

.kp-chip {
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.06);
  padding: 0.375rem 0.625rem;
  transition: background-color 0.15s, transform 0.1s;
}
.kp-chip:hover { background: rgba(255, 255, 255, 0.14); }
.kp-chip:active { transform: scale(0.96); }

.kp-badge {
  position: absolute;
  right: -0.375rem;
  top: -0.5rem;
  min-width: 1.25rem;
  height: 1.25rem;
  border-radius: 9999px;
  background: #fff;
  color: #164A38;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.25rem;
  text-align: center;
  animation: kp-pop 0.2s ease-out;
}

/* Metode pembayaran: satu kontrol segmented */
.kp-seg {
  display: flex;
  padding: 2px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 9999px;
}
.kp-seg button {
  flex: 1;
  border-radius: 9999px;
  padding: 0.25rem 0.5rem;
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
  font-weight: 500;
  line-height: 1.25rem;
  transition: background-color 0.15s, color 0.15s;
}
.kp-seg button:hover:not([aria-checked='true']) { background: rgba(255, 255, 255, 0.1); }
.kp-seg button[aria-checked='true'] { background: #fff; color: #164A38; font-weight: 600; }

.kp-pill {
  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 9999px;
  padding: 0 0.625rem;
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.375rem;
  transition: background-color 0.15s, color 0.15s;
}
.kp-pill:hover:not(:disabled) { background: rgba(255, 255, 255, 0.14); }
.kp-pill[aria-pressed='true'] { background: rgba(255, 255, 255, 0.92); border-color: transparent; color: #164A38; font-weight: 600; }
.kp-pill:disabled { opacity: 0.35; cursor: not-allowed; }

/* Input nomor rekening (debit) */
.kp-acct {
  min-width: 0;
  flex: 1;
  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  padding: 0.25rem 0.625rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  letter-spacing: 0.06em;
  line-height: 1.5rem;
}
.kp-acct::placeholder { color: rgba(255, 255, 255, 0.4); font-family: 'Inter', ui-sans-serif, system-ui, sans-serif; letter-spacing: 0; }
.kp-acct:hover { border-color: rgba(255, 255, 255, 0.4); }
.kp-acct:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }
.kp-acct[aria-invalid='true'] { border-color: #ffb4a8; }

.kp-solid-light,
.kp-ghost {
  border-radius: 0.5rem;
  padding: 0.5rem 0.875rem;
  font-size: 0.8125rem;
  font-weight: 600;
  transition: background-color 0.15s, opacity 0.15s;
}
.kp-solid-light { background: #fff; color: #164A38; }
.kp-solid-light:hover:not(:disabled) { background: #DCF3E8; }
.kp-ghost { border: 1px solid rgba(255, 255, 255, 0.3); color: #fff; }
.kp-ghost:hover:not(:disabled) { background: rgba(255, 255, 255, 0.12); }
.kp-solid-light:disabled,
.kp-ghost:disabled { opacity: 0.45; cursor: not-allowed; }

.kp-text-btn {
  padding: 0.5rem 0.25rem;
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.8125rem;
  font-weight: 500;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.kp-text-btn:hover:not(:disabled) { color: #fff; }
.kp-text-btn:disabled { opacity: 0.4; cursor: not-allowed; text-decoration: none; }

/* Keadaan sesudah bayar */
.kp-done {
  display: flex;
  min-height: 15rem;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.kp-done-icon {
  display: flex;
  width: 2.5rem;
  height: 2.5rem;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.14);
}

@media (prefers-reduced-motion: reduce) {
  .kp-receipt,
  .kp-stamp,
  .kp-nudge,
  .kp-check-draw,
  .kp-shake,
  .kp-coin,
  .kp-bounce,
  .kp-bubble,
  .kp-badge,
  .kp-ripple,
  .kp-scan,
  .kp-qr-in,
  .kp-stamp--in,
  .kp-orbit,
  .kp-z,
  .kp-led,
  .kp-piece,
  .kp-wipe,
  .kp-wipe-text {
    animation: none;
  }
  .kp-wipe { clip-path: none; }
  .kp-wipe-text { opacity: 1; }
  .kp-tilt,
  .kp-drop,
  .kp-hoof,
  .kp-pupil,
  .kp-eye,
  .kp-chip,
  .kp-btn,
  .kp-lock-bar,
  .kp-swap-enter-active,
  .kp-swap-leave-active,
  .kp-line-enter-active,
  .kp-line-leave-active,
  .kp-line-move { transition: none; }
}
</style>