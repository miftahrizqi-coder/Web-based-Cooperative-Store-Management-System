<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  createCategory,
  deactivateCategory,
  getCategories,
  updateCategory,
} from '../../api/categories'
import { errorMessage } from '../../services/api'
import type { Category } from '../../types/category'

const categories = ref<Category[]>([])
const isLoading = ref(true)
const loadError = ref('')
const actionError = ref('')
const search = ref('')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')

const modalOpen = ref(false)
const editing = ref<Category | null>(null)
const saving = ref(false)
const formError = ref('')
const form = reactive({ name: '', description: '', isActive: true })

const filtered = computed(() => {
  const term = search.value.trim().toLowerCase()
  return categories.value.filter((category) => {
    if (statusFilter.value === 'active' && !category.isActive) return false
    if (statusFilter.value === 'inactive' && category.isActive) return false
    if (!term) return true
    return (
      category.name.toLowerCase().includes(term) ||
      (category.description ?? '').toLowerCase().includes(term)
    )
  })
})

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    categories.value = await getCategories()
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat kategori.')
  } finally {
    isLoading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.name = ''
  form.description = ''
  form.isActive = true
  formError.value = ''
  modalOpen.value = true
}

function openEdit(category: Category) {
  editing.value = category
  form.name = category.name
  form.description = category.description ?? ''
  form.isActive = category.isActive
  formError.value = ''
  modalOpen.value = true
}

async function save() {
  if (!form.name.trim()) {
    formError.value = 'Nama kategori wajib diisi.'
    return
  }
  saving.value = true
  formError.value = ''
  const payload = {
    name: form.name.trim(),
    description: form.description.trim() || null,
    isActive: form.isActive,
  }
  try {
    if (editing.value) {
      await updateCategory(editing.value.id, payload)
    } else {
      await createCategory(payload)
    }
    modalOpen.value = false
    await load()
  } catch (error) {
    formError.value = errorMessage(error, 'Gagal menyimpan kategori.')
  } finally {
    saving.value = false
  }
}

async function deactivate(category: Category) {
  if (!window.confirm(`Nonaktifkan kategori "${category.name}"? Produk yang sudah ada tetap memakai kategori ini.`)) return
  actionError.value = ''
  try {
    await deactivateCategory(category.id)
    await load()
  } catch (error) {
    actionError.value = errorMessage(error, 'Gagal menonaktifkan kategori.')
  }
}

onMounted(load)
</script>

<template>
  <main class="page">
    <div class="page-inner">
      <header class="page-header">
        <div>
          <nav class="breadcrumb" aria-label="Breadcrumb">
            <span>Master Data</span><span>/</span><span aria-current="page">Kategori</span>
          </nav>
          <h1 class="page-title">Kategori Produk</h1>
          <p class="page-subtitle">Kelompokkan produk agar mudah dicari, difilter, dan dilaporkan.</p>
        </div>
        <div class="header-actions">
          <button type="button" class="btn btn-primary" @click="openCreate">+ Tambah kategori</button>
        </div>
      </header>

      <section class="card card-body">
        <div class="filter-bar">
          <label class="field">
            <span class="label">Cari</span>
            <input v-model="search" type="search" class="input" placeholder="Nama atau deskripsi">
          </label>
          <label class="field">
            <span class="label">Status</span>
            <select v-model="statusFilter" class="select">
              <option value="all">Semua</option>
              <option value="active">Aktif</option>
              <option value="inactive">Nonaktif</option>
            </select>
          </label>
        </div>
      </section>

      <div v-if="actionError" class="alert alert-error" role="alert">{{ actionError }}</div>

      <section class="card">
        <div v-if="isLoading" class="card-body">
          <div v-for="row in 4" :key="row" class="skeleton" style="height: 20px; margin-bottom: 12px" />
        </div>
        <div v-else-if="loadError" class="card-body">
          <div class="alert alert-error" role="alert">{{ loadError }}</div>
          <button type="button" class="btn btn-secondary" style="margin-top: 12px" @click="load">Coba lagi</button>
        </div>
        <div v-else-if="filtered.length === 0" class="empty">
          <strong>Belum ada kategori</strong>
          Tambahkan kategori pertama, mis. ATK, Makanan, Minuman.
        </div>
        <div v-else class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>Nama</th>
                <th>Deskripsi</th>
                <th class="num">Produk aktif</th>
                <th>Status</th>
                <th class="actions">Aksi</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="category in filtered" :key="category.id">
                <td class="strong">{{ category.name }}</td>
                <td class="muted">{{ category.description || '-' }}</td>
                <td class="num">
                  <RouterLink :to="{ path: '/products', query: { categoryId: category.id } }">
                    {{ category.productCount }}
                  </RouterLink>
                </td>
                <td>
                  <span class="badge" :class="category.isActive ? 'badge-success' : 'badge-neutral'">
                    {{ category.isActive ? 'Aktif' : 'Nonaktif' }}
                  </span>
                </td>
                <td class="actions">
                  <button type="button" class="btn btn-ghost btn-sm" @click="openEdit(category)">Ubah</button>
                  <button
                    v-if="category.isActive"
                    type="button"
                    class="btn btn-ghost btn-sm text-danger"
                    @click="deactivate(category)"
                  >
                    Nonaktifkan
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <div v-if="modalOpen" class="modal-backdrop" @click.self="modalOpen = false">
      <form class="modal" role="dialog" aria-modal="true" aria-labelledby="category-modal-title" @submit.prevent="save">
        <div class="modal-header">
          <h2 id="category-modal-title" class="card-title">{{ editing ? 'Ubah kategori' : 'Tambah kategori' }}</h2>
          <button type="button" class="btn btn-ghost btn-sm" aria-label="Tutup" @click="modalOpen = false">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="formError" class="alert alert-error" role="alert">{{ formError }}</div>
          <label class="field">
            <span class="label">Nama <span class="req">*</span></span>
            <input v-model="form.name" class="input" maxlength="100" required autofocus>
          </label>
          <label class="field">
            <span class="label">Deskripsi</span>
            <textarea v-model="form.description" class="textarea" maxlength="500" />
          </label>
          <label v-if="editing" style="display: flex; gap: 8px; align-items: center">
            <input v-model="form.isActive" type="checkbox">
            <span>Kategori aktif</span>
          </label>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="modalOpen = false">Batal</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Menyimpan…' : 'Simpan' }}</button>
        </div>
      </form>
    </div>
  </main>
</template>
