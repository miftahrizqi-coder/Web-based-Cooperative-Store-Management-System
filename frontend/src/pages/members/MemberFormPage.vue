<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { createMember, getMember, updateMember } from '../../api/members'
import { errorMessage } from '../../services/api'
import type { MemberStatus } from '../../types/member'
import { dateInputToIso, toDateInput } from '../../utils/format'

const route = useRoute()
const router = useRouter()
const memberId = computed(() => (route.params.id ? String(route.params.id) : null))
const isEdit = computed(() => Boolean(memberId.value))

const form = reactive({
  memberNumber: '',
  name: '',
  phone: '',
  email: '',
  address: '',
  joinedAt: toDateInput(),
  status: 'ACTIVE' as MemberStatus,
})
const isLoading = ref(false)
const saving = ref(false)
const formError = ref('')

async function load() {
  if (!memberId.value) return
  isLoading.value = true
  try {
    const member = await getMember(memberId.value)
    form.memberNumber = member.memberNumber
    form.name = member.name
    form.phone = member.phone
    form.email = member.email ?? ''
    form.address = member.address ?? ''
    form.joinedAt = toDateInput(member.joinedAt)
    form.status = member.status
  } catch (error) {
    formError.value = errorMessage(error, 'Gagal memuat anggota.')
  } finally {
    isLoading.value = false
  }
}

async function save() {
  formError.value = ''
  if (!form.name.trim() || !form.phone.trim()) {
    formError.value = 'Nama dan telepon wajib diisi.'
    return
  }
  if (isEdit.value && !form.memberNumber.trim()) {
    formError.value = 'Nomor anggota wajib diisi.'
    return
  }
  saving.value = true
  const payload = {
    memberNumber: form.memberNumber.trim() || null,
    name: form.name.trim(),
    phone: form.phone.trim(),
    email: form.email.trim() || null,
    address: form.address.trim() || null,
    joinedAt: form.joinedAt ? dateInputToIso(form.joinedAt) : null,
    status: form.status,
  }
  try {
    const member = memberId.value
      ? await updateMember(memberId.value, payload)
      : await createMember(payload)
    await router.push(`/members/${member.id}`)
  } catch (error) {
    formError.value = errorMessage(error, 'Gagal menyimpan anggota.')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="page">
    <div class="page-inner" style="max-width: 860px">
      <header>
        <nav class="breadcrumb" aria-label="Breadcrumb">
          <RouterLink to="/members">Anggota</RouterLink><span>/</span>
          <span aria-current="page">{{ isEdit ? 'Ubah' : 'Tambah' }}</span>
        </nav>
        <h1 class="page-title">{{ isEdit ? 'Ubah anggota' : 'Tambah anggota' }}</h1>
        <p class="page-subtitle">Nomor anggota dibuat otomatis (KOP-001, KOP-002, …) bila dikosongkan.</p>
      </header>

      <form class="card" @submit.prevent="save">
        <div class="card-body">
          <div v-if="isLoading" class="skeleton" style="height: 160px" />
          <template v-else>
            <div v-if="formError" class="alert alert-error" role="alert" style="margin-bottom: 14px">{{ formError }}</div>
            <div class="form-grid cols-2">
              <label class="field">
                <span class="label">Nomor anggota <span v-if="isEdit" class="req">*</span></span>
                <input v-model="form.memberNumber" class="input mono" maxlength="50" :placeholder="isEdit ? '' : 'Otomatis'">
              </label>
              <label class="field">
                <span class="label">Status</span>
                <select v-model="form.status" class="select">
                  <option value="ACTIVE">Aktif</option>
                  <option value="INACTIVE">Nonaktif</option>
                </select>
              </label>
              <label class="field">
                <span class="label">Nama <span class="req">*</span></span>
                <input v-model="form.name" class="input" maxlength="200" required>
              </label>
              <label class="field">
                <span class="label">Telepon <span class="req">*</span></span>
                <input v-model="form.phone" class="input" maxlength="30" inputmode="tel" required>
              </label>
              <label class="field">
                <span class="label">Email</span>
                <input v-model="form.email" type="email" class="input" maxlength="200">
              </label>
              <label class="field">
                <span class="label">Tanggal bergabung</span>
                <input v-model="form.joinedAt" type="date" class="input">
              </label>
              <label class="field span-full">
                <span class="label">Alamat</span>
                <textarea v-model="form.address" class="textarea" maxlength="500" />
              </label>
            </div>
          </template>
        </div>
        <div class="modal-footer">
          <RouterLink to="/members" class="btn btn-secondary">Batal</RouterLink>
          <button type="submit" class="btn btn-primary" :disabled="saving || isLoading">
            {{ saving ? 'Menyimpan…' : 'Simpan' }}
          </button>
        </div>
      </form>
    </div>
  </main>
</template>
