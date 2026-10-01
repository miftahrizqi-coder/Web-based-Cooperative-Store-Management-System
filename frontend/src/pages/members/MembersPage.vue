<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { deactivateMember, getMembers } from '../../api/members'
import PaginationBar from '../../components/ui/PaginationBar.vue'
import { errorMessage } from '../../services/api'
import { useAuth } from '../../stores/auth'
import type { Member, MemberStatus } from '../../types/member'
import { formatDate } from '../../utils/format'

const { hasRole } = useAuth()
const canManage = computed(() => hasRole('admin'))

const members = ref<Member[]>([])
const isLoading = ref(true)
const loadError = ref('')
const actionError = ref('')
const search = ref('')
const status = ref<MemberStatus | ''>('')
const page = ref(1)
const pageSize = 15

const paged = computed(() => members.value.slice((page.value - 1) * pageSize, page.value * pageSize))

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    members.value = await getMembers({ search: search.value, status: status.value })
    page.value = 1
  } catch (error) {
    loadError.value = errorMessage(error, 'Gagal memuat data anggota.')
  } finally {
    isLoading.value = false
  }
}

async function deactivate(member: Member) {
  if (!window.confirm(`Nonaktifkan anggota ${member.memberNumber} - ${member.name}?`)) return
  actionError.value = ''
  try {
    await deactivateMember(member.id)
    await load()
  } catch (error) {
    actionError.value = errorMessage(error, 'Gagal menonaktifkan anggota.')
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
            <span>Master Data</span><span>/</span><span aria-current="page">Anggota</span>
          </nav>
          <h1 class="page-title">Anggota Koperasi</h1>
          <p class="page-subtitle">Data anggota, status keanggotaan, dan riwayat belanja.</p>
        </div>
        <div v-if="canManage" class="header-actions">
          <RouterLink to="/members/create" class="btn btn-primary">+ Tambah anggota</RouterLink>
        </div>
      </header>

      <form class="card card-body" @submit.prevent="load">
        <div class="filter-bar">
          <label class="field">
            <span class="label">Cari</span>
            <input v-model="search" type="search" class="input" placeholder="Nomor, nama, atau telepon">
          </label>
          <label class="field">
            <span class="label">Status</span>
            <select v-model="status" class="select">
              <option value="">Semua</option>
              <option value="ACTIVE">Aktif</option>
              <option value="INACTIVE">Nonaktif</option>
            </select>
          </label>
          <div class="field">
            <button type="submit" class="btn btn-secondary">Terapkan</button>
          </div>
        </div>
      </form>

      <div v-if="actionError" class="alert alert-error" role="alert">{{ actionError }}</div>

      <section class="card">
        <div v-if="isLoading" class="card-body">
          <div v-for="row in 5" :key="row" class="skeleton" style="height: 20px; margin-bottom: 12px" />
        </div>
        <div v-else-if="loadError" class="card-body">
          <div class="alert alert-error">{{ loadError }}</div>
        </div>
        <div v-else-if="members.length === 0" class="empty">
          <strong>Belum ada anggota</strong>
          Data anggota yang sesuai filter tidak ditemukan.
        </div>
        <template v-else>
          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>No. Anggota</th>
                  <th>Nama</th>
                  <th>Telepon</th>
                  <th>Bergabung</th>
                  <th>Status</th>
                  <th class="actions">Aksi</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="member in paged" :key="member.id">
                  <td class="mono">{{ member.memberNumber }}</td>
                  <td>
                    <RouterLink :to="`/members/${member.id}`" class="strong">{{ member.name }}</RouterLink>
                    <div class="muted small">{{ member.email || '-' }}</div>
                  </td>
                  <td>{{ member.phone }}</td>
                  <td>{{ formatDate(member.joinedAt) }}</td>
                  <td>
                    <span class="badge" :class="member.status === 'ACTIVE' ? 'badge-success' : 'badge-neutral'">
                      {{ member.status === 'ACTIVE' ? 'Aktif' : 'Nonaktif' }}
                    </span>
                  </td>
                  <td class="actions">
                    <RouterLink :to="`/members/${member.id}`" class="btn btn-ghost btn-sm">Detail</RouterLink>
                    <template v-if="canManage">
                      <RouterLink :to="`/members/${member.id}/edit`" class="btn btn-ghost btn-sm">Ubah</RouterLink>
                      <button
                        v-if="member.status === 'ACTIVE'"
                        type="button"
                        class="btn btn-ghost btn-sm text-danger"
                        @click="deactivate(member)"
                      >
                        Nonaktifkan
                      </button>
                    </template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <PaginationBar v-model:page="page" :page-size="pageSize" :total="members.length" />
        </template>
      </section>
    </div>
  </main>
</template>
