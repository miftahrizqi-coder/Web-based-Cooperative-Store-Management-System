<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { changePassword } from '../../api/auth'
import { getMyMemberProfile, getMyTransaction, getMyTransactions } from '../../api/members'
import PaginationBar from '../../components/ui/PaginationBar.vue'
import { errorMessage } from '../../services/api'
import { useAuth } from '../../stores/auth'
import { ROLE_LABELS } from '../../types/auth'
import type { MemberWithStats } from '../../types/member'
import { PAYMENT_METHOD_LABELS, type Sale } from '../../types/sale'
import { formatCurrency, formatDate, formatDateTime, formatNumber } from '../../utils/format'

const { currentUser, setToken } = useAuth()
const isMember = computed(() => currentUser.value?.role === 'anggota')

// --- Anggota ---
const member = ref<MemberWithStats | null>(null)
const memberError = ref('')
const transactions = ref<Sale[]>([])
const txTotal = ref(0)
const txPage = ref(1)
const txPageSize = 10
const selectedSale = ref<Sale | null>(null)

async function loadMember() {
  memberError.value = ''
  try {
    member.value = await getMyMemberProfile()
    await loadTransactions()
  } catch (error) {
    memberError.value = errorMessage(error, 'Data anggota belum tersedia.')
  }
}

async function loadTransactions() {
  const result = await getMyTransactions(txPage.value, txPageSize)
  transactions.value = result.items
  txTotal.value = result.total
}

async function openSale(sale: Sale) {
  try {
    selectedSale.value = await getMyTransaction(sale.id)
  } catch (error) {
    memberError.value = errorMessage(error)
  }
}

watch(txPage, () => {
  loadTransactions().catch((error) => {
    memberError.value = errorMessage(error)
  })
})

// --- Ubah password ---
const passwordForm = reactive({ current: '', next: '', confirm: '' })
const passwordError = ref('')
const passwordSuccess = ref('')
const savingPassword = ref(false)

async function submitPassword() {
  passwordError.value = ''
  passwordSuccess.value = ''
  if (passwordForm.next.length < 8) {
    passwordError.value = 'Password baru minimal 8 karakter.'
    return
  }
  if (passwordForm.next !== passwordForm.confirm) {
    passwordError.value = 'Konfirmasi password tidak sama.'
    return
  }
  savingPassword.value = true
  try {
    const result = await changePassword(passwordForm.current, passwordForm.next)
    // Token lama dicabut server; simpan token baru agar sesi tetap aktif.
    setToken(result.token)
    passwordSuccess.value = 'Password berhasil diubah. Sesi di perangkat lain telah diakhiri.'
    Object.assign(passwordForm, { current: '', next: '', confirm: '' })
  } catch (error) {
    passwordError.value = errorMessage(error, 'Gagal mengubah password.')
  } finally {
    savingPassword.value = false
  }
}

onMounted(() => {
  if (isMember.value) void loadMember()
})
</script>

<template>
  <main class="page">
    <div class="page-inner" style="max-width: 1100px">
      <header>
        <h1 class="page-title">Profil Saya</h1>
        <p class="page-subtitle">Informasi akun{{ isMember ? ', keanggotaan, dan riwayat belanja Anda' : '' }}.</p>
      </header>

      <section class="card">
        <div class="card-header"><h2 class="card-title">Akun</h2></div>
        <div class="card-body">
          <dl class="dl">
            <div><dt>Nama</dt><dd>{{ currentUser?.name }}</dd></div>
            <div><dt>Username</dt><dd class="mono">{{ currentUser?.username }}</dd></div>
            <div><dt>Email</dt><dd>{{ currentUser?.email }}</dd></div>
            <div><dt>Role</dt><dd>{{ currentUser ? ROLE_LABELS[currentUser.role] : '-' }}</dd></div>
          </dl>
        </div>
      </section>

      <template v-if="isMember">
        <div v-if="memberError" class="alert alert-warning">{{ memberError }}</div>
        <template v-if="member">
          <section class="kpi-grid">
            <div class="kpi">
              <div class="kpi-label">Nomor anggota</div>
              <div class="kpi-value mono" style="font-size: 20px">{{ member.memberNumber }}</div>
              <div class="kpi-context">Bergabung {{ formatDate(member.joinedAt) }}</div>
            </div>
            <div class="kpi">
              <div class="kpi-label">Status keanggotaan</div>
              <div class="kpi-value" style="font-size: 18px">
                <span class="badge" :class="member.status === 'ACTIVE' ? 'badge-success' : 'badge-neutral'">
                  {{ member.status === 'ACTIVE' ? 'Aktif' : 'Nonaktif' }}
                </span>
              </div>
            </div>
            <div class="kpi">
              <div class="kpi-label">Total belanja</div>
              <div class="kpi-value">{{ formatCurrency(member.totalSpending) }}</div>
              <div class="kpi-context">{{ member.transactionCount }} transaksi</div>
            </div>
          </section>

          <section class="card">
            <div class="card-header"><h2 class="card-title">Riwayat transaksi</h2></div>
            <div v-if="transactions.length === 0" class="empty">Belum ada transaksi.</div>
            <template v-else>
              <div class="table-wrap">
                <table class="table">
                  <thead>
                    <tr><th>Invoice</th><th>Tanggal</th><th>Item</th><th class="num">Total</th><th>Status</th><th class="actions" /></tr>
                  </thead>
                  <tbody>
                    <tr v-for="sale in transactions" :key="sale.id">
                      <td class="mono">{{ sale.invoiceNumber }}</td>
                      <td>{{ formatDateTime(sale.createdAt) }}</td>
                      <td>{{ sale.items.length }} produk</td>
                      <td class="num">{{ formatCurrency(sale.total) }}</td>
                      <td>
                        <span class="badge" :class="sale.status === 'COMPLETED' ? 'badge-success' : 'badge-danger'">
                          {{ sale.status === 'COMPLETED' ? 'Selesai' : 'Dibatalkan' }}
                        </span>
                      </td>
                      <td class="actions"><button type="button" class="btn btn-ghost btn-sm" @click="openSale(sale)">Detail</button></td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <PaginationBar v-model:page="txPage" :page-size="txPageSize" :total="txTotal" />
            </template>
          </section>
        </template>
      </template>

      <section class="card">
        <div class="card-header"><h2 class="card-title">Ubah password</h2></div>
        <form class="card-body" @submit.prevent="submitPassword">
          <div v-if="passwordError" class="alert alert-error" role="alert" style="margin-bottom: 12px">{{ passwordError }}</div>
          <div v-if="passwordSuccess" class="alert alert-success" role="status" style="margin-bottom: 12px">{{ passwordSuccess }}</div>
          <div class="form-grid cols-3">
            <label class="field">
              <span class="label">Password saat ini</span>
              <input v-model="passwordForm.current" type="password" class="input" autocomplete="current-password" required>
            </label>
            <label class="field">
              <span class="label">Password baru</span>
              <input v-model="passwordForm.next" type="password" class="input" autocomplete="new-password" minlength="8" required>
            </label>
            <label class="field">
              <span class="label">Ulangi password baru</span>
              <input v-model="passwordForm.confirm" type="password" class="input" autocomplete="new-password" required>
            </label>
          </div>
          <div style="margin-top: 14px">
            <button type="submit" class="btn btn-primary" :disabled="savingPassword">
              {{ savingPassword ? 'Menyimpan…' : 'Ubah password' }}
            </button>
          </div>
        </form>
      </section>
    </div>

    <div v-if="selectedSale" class="modal-backdrop" @click.self="selectedSale = null">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="sale-modal-title">
        <div class="modal-header">
          <h2 id="sale-modal-title" class="card-title mono">{{ selectedSale.invoiceNumber }}</h2>
          <button type="button" class="btn btn-ghost btn-sm" aria-label="Tutup" @click="selectedSale = null">✕</button>
        </div>
        <div class="modal-body">
          <div class="small muted">{{ formatDateTime(selectedSale.createdAt) }} · {{ PAYMENT_METHOD_LABELS[selectedSale.payment.method] }}</div>
          <table class="table">
            <thead><tr><th>Produk</th><th class="num">Qty</th><th class="num">Harga</th><th class="num">Subtotal</th></tr></thead>
            <tbody>
              <tr v-for="item in selectedSale.items" :key="item.productId">
                <td>{{ item.name }}</td>
                <td class="num">{{ formatNumber(item.quantity) }}</td>
                <td class="num">{{ formatCurrency(item.price) }}</td>
                <td class="num">{{ formatCurrency(item.subtotal) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr v-if="selectedSale.discount > 0"><td colspan="3">Diskon</td><td class="num">-{{ formatCurrency(selectedSale.discount) }}</td></tr>
              <tr><td colspan="3">Total</td><td class="num">{{ formatCurrency(selectedSale.total) }}</td></tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  </main>
</template>
