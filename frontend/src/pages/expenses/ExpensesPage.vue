<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { createExpense, deleteExpense, getExpenses, updateExpense } from '../../api/expenses'
import PaginationBar from '../../components/ui/PaginationBar.vue'
import { errorMessage } from '../../services/api'
import { useAuth } from '../../stores/auth'
import { EXPENSE_CATEGORY_LABELS, type Expense, type ExpenseCategory } from '../../types/expense'
import { dateInputToIso, firstDayOfMonth, formatCurrency, formatDate, toDateInput } from '../../utils/format'

const { hasRole } = useAuth()
const canManage = computed(() => hasRole('admin'))
const categoryOptions = Object.entries(EXPENSE_CATEGORY_LABELS) as [ExpenseCategory, string][]

const filters = reactive({
  category: '' as ExpenseCategory | '',
  search: '',
  dateFrom: firstDayOfMonth(),
  dateTo: toDateInput(),
})
const expenses = ref<Expense[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const isLoading = ref(true)
const loadError = ref('')
const actionError = ref('')

const modalOpen = ref(false)
const editing = ref<Expense | null>(null)
const saving = ref(false)
const formError = ref('')
const form = reactive({ category: 'ELECTRICITY' as ExpenseCategory, description: '', amount: 0, date: toDateInput() })

const pageTotal = computed(() => expenses.value.reduce((sum, e) => sum + e.amount, 0))

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    const result = await getExpenses({ ...filters, page: page.value, pageSize })
    expenses.value = result.items
    total.value = result.total
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat pengeluaran.')
  } finally {
    isLoading.value = false
  }
}

function applyFilters() {
  if (page.value !== 1) page.value = 1
  else void load()
}

function openCreate() {
  editing.value = null
  Object.assign(form, { category: 'ELECTRICITY', description: '', amount: 0, date: toDateInput() })
  formError.value = ''
  modalOpen.value = true
}

function openEdit(expense: Expense) {
  editing.value = expense
  Object.assign(form, {
    category: expense.category,
    description: expense.description,
    amount: expense.amount,
    date: toDateInput(expense.date),
  })
  formError.value = ''
  modalOpen.value = true
}

async function save() {
  formError.value = ''
  if (!form.description.trim()) {
    formError.value = 'Keterangan wajib diisi.'
    return
  }
  if (!(form.amount > 0)) {
    formError.value = 'Nominal harus lebih dari 0.'
    return
  }
  saving.value = true
  const payload = {
    category: form.category,
    description: form.description.trim(),
    amount: form.amount,
    date: dateInputToIso(form.date),
  }
  try {
    if (editing.value) await updateExpense(editing.value.id, payload)
    else await createExpense(payload)
    modalOpen.value = false
    await load()
  } catch (error) {
    formError.value = errorMessage(error, 'Gagal menyimpan pengeluaran.')
  } finally {
    saving.value = false
  }
}

async function remove(expense: Expense) {
  if (!window.confirm(`Hapus pengeluaran ${expense.expenseNumber} (${formatCurrency(expense.amount)})? Tindakan ini tercatat di audit log.`)) return
  actionError.value = ''
  try {
    await deleteExpense(expense.id)
    await load()
  } catch (error) {
    actionError.value = errorMessage(error, 'Gagal menghapus pengeluaran.')
  }
}

watch(page, load)
onMounted(load)
</script>

<template>
  <main class="page">
    <div class="page-inner">
      <header class="page-header">
        <div>
          <nav class="breadcrumb" aria-label="Breadcrumb">
            <span>Keuangan</span><span>/</span><span aria-current="page">Pengeluaran</span>
          </nav>
          <h1 class="page-title">Pengeluaran Operasional</h1>
          <p class="page-subtitle">Biaya listrik, air, internet, transportasi, ATK, perawatan, dan operasional lainnya.</p>
        </div>
        <div v-if="canManage" class="header-actions">
          <button type="button" class="btn btn-primary" @click="openCreate">+ Catat pengeluaran</button>
        </div>
      </header>

      <form class="card card-body" @submit.prevent="applyFilters">
        <div class="filter-bar">
          <label class="field">
            <span class="label">Kategori</span>
            <select v-model="filters.category" class="select">
              <option value="">Semua</option>
              <option v-for="[value, label] in categoryOptions" :key="value" :value="value">{{ label }}</option>
            </select>
          </label>
          <label class="field">
            <span class="label">Cari keterangan</span>
            <input v-model="filters.search" type="search" class="input">
          </label>
          <label class="field">
            <span class="label">Dari</span>
            <input v-model="filters.dateFrom" type="date" class="input">
          </label>
          <label class="field">
            <span class="label">Sampai</span>
            <input v-model="filters.dateTo" type="date" class="input">
          </label>
          <div class="field"><button type="submit" class="btn btn-secondary">Terapkan</button></div>
        </div>
      </form>

      <div v-if="actionError" class="alert alert-error" role="alert">{{ actionError }}</div>

      <section class="card">
        <div v-if="isLoading" class="card-body"><div class="skeleton" style="height: 120px" /></div>
        <div v-else-if="loadError" class="card-body"><div class="alert alert-error">{{ loadError }}</div></div>
        <div v-else-if="expenses.length === 0" class="empty"><strong>Belum ada pengeluaran</strong>Tidak ada data pada periode ini.</div>
        <template v-else>
          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Nomor</th>
                  <th>Tanggal</th>
                  <th>Kategori</th>
                  <th>Keterangan</th>
                  <th class="num">Nominal</th>
                  <th>Dicatat oleh</th>
                  <th v-if="canManage" class="actions">Aksi</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="expense in expenses" :key="expense.id">
                  <td class="mono">{{ expense.expenseNumber }}</td>
                  <td>{{ formatDate(expense.date) }}</td>
                  <td><span class="badge badge-neutral">{{ EXPENSE_CATEGORY_LABELS[expense.category] }}</span></td>
                  <td>{{ expense.description }}</td>
                  <td class="num strong">{{ formatCurrency(expense.amount) }}</td>
                  <td class="small">{{ expense.createdByName || '-' }}</td>
                  <td v-if="canManage" class="actions">
                    <button type="button" class="btn btn-ghost btn-sm" @click="openEdit(expense)">Ubah</button>
                    <button type="button" class="btn btn-ghost btn-sm text-danger" @click="remove(expense)">Hapus</button>
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td colspan="4">Total halaman ini</td>
                  <td class="num">{{ formatCurrency(pageTotal) }}</td>
                  <td :colspan="canManage ? 2 : 1" />
                </tr>
              </tfoot>
            </table>
          </div>
          <PaginationBar v-model:page="page" :page-size="pageSize" :total="total" />
        </template>
      </section>
    </div>

    <div v-if="modalOpen" class="modal-backdrop" @click.self="modalOpen = false">
      <form class="modal" role="dialog" aria-modal="true" aria-labelledby="expense-modal-title" @submit.prevent="save">
        <div class="modal-header">
          <h2 id="expense-modal-title" class="card-title">{{ editing ? `Ubah ${editing.expenseNumber}` : 'Catat pengeluaran' }}</h2>
          <button type="button" class="btn btn-ghost btn-sm" aria-label="Tutup" @click="modalOpen = false">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="formError" class="alert alert-error" role="alert">{{ formError }}</div>
          <div class="form-grid cols-2">
            <label class="field">
              <span class="label">Kategori <span class="req">*</span></span>
              <select v-model="form.category" class="select">
                <option v-for="[value, label] in categoryOptions" :key="value" :value="value">{{ label }}</option>
              </select>
            </label>
            <label class="field">
              <span class="label">Tanggal <span class="req">*</span></span>
              <input v-model="form.date" type="date" class="input" required>
            </label>
            <label class="field span-full">
              <span class="label">Keterangan <span class="req">*</span></span>
              <input v-model="form.description" class="input" maxlength="500" required>
            </label>
            <label class="field">
              <span class="label">Nominal (Rp) <span class="req">*</span></span>
              <input v-model.number="form.amount" type="number" min="1" step="100" class="input num" required>
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="modalOpen = false">Batal</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Menyimpan…' : 'Simpan' }}</button>
        </div>
      </form>
    </div>
  </main>
</template>
