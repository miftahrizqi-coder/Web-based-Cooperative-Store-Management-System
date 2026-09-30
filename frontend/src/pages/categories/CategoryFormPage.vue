<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createCategory,
  getCategory,
  updateCategory,
} from '../../api/categories'
import { useAuth } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const isEdit = Boolean(route.params.id)
const categoryId = String(route.params.id || '')

const name = ref('')
const description = ref('')

const isLoading = ref(isEdit)
const isSaving = ref(false)
const errorMessage = ref('')
const nameError = ref('')

async function loadCategory() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  try {
    const category = await getCategory(
      token.value,
      categoryId,
    )

    name.value = category.name
    description.value = category.description ?? ''
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data Category.'
  } finally {
    isLoading.value = false
  }
}

function validate() {
  nameError.value = ''

  if (!name.value.trim()) {
    nameError.value = 'Nama Category wajib diisi.'
    return false
  }

  if (name.value.trim().length > 100) {
    nameError.value =
      'Nama Category maksimal 100 karakter.'
    return false
  }

  return true
}

async function handleSubmit() {
  if (!token.value || isSaving.value) {
    return
  }

  if (!validate()) {
    return
  }

  isSaving.value = true
  errorMessage.value = ''

  const payload = {
    name: name.value.trim(),
    description: description.value.trim() || null,
  }

  try {
    if (isEdit) {
      await updateCategory(
        token.value,
        categoryId,
        payload,
      )
    } else {
      await createCategory(token.value, payload)
    }

    router.push('/categories')
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : isEdit
          ? 'Gagal memperbarui Category.'
          : 'Gagal membuat Category.'
  } finally {
    isSaving.value = false
  }
}

function cancel() {
  router.push('/categories')
}

onMounted(() => {
  if (isEdit) {
    loadCategory()
  }
})
</script>

<template>
  <div class="mx-auto max-w-2xl space-y-6">
    <div>
      <button
        type="button"
        class="text-sm font-medium text-[#68736D] hover:text-[#26332D]"
        @click="cancel"
      >
        ← Kembali ke Category
      </button>

      <h1 class="mt-4 text-2xl font-semibold text-[#26332D]">
        {{ isEdit ? 'Edit Category' : 'Tambah Category' }}
      </h1>

      <p class="mt-1 text-sm text-[#68736D]">
        {{
          isEdit
            ? 'Perbarui informasi Category.'
            : 'Tambahkan Category baru untuk produk.'
        }}
      </p>
    </div>

    <div
      v-if="errorMessage"
      class="rounded-xl border border-[#E8B9B3] bg-[#FDF0EE] px-4 py-3 text-sm text-[#C0392B]"
    >
      {{ errorMessage }}
    </div>

    <div
      v-if="isLoading"
      class="rounded-xl border border-[#DCE3DF] bg-white p-8 text-center text-sm text-[#68736D]"
    >
      Memuat Category...
    </div>

    <form
      v-else
      class="rounded-xl border border-[#DCE3DF] bg-white p-5 sm:p-6"
      @submit.prevent="handleSubmit"
    >
      <div class="space-y-5">
        <div>
          <label
            for="category-name"
            class="block text-sm font-medium text-[#26332D]"
          >
            Nama Category
          </label>

          <input
            id="category-name"
            v-model="name"
            type="text"
            maxlength="100"
            autocomplete="off"
            class="mt-2 block min-h-11 w-full rounded-lg border border-[#C8D1CC] px-3 text-sm text-[#26332D] outline-none focus:border-[#26332D] focus:ring-1 focus:ring-[#26332D]"
            placeholder="Contoh: Sembako"
          />

          <p
            v-if="nameError"
            class="mt-1 text-sm text-[#C0392B]"
          >
            {{ nameError }}
          </p>
        </div>

        <div>
          <label
            for="category-description"
            class="block text-sm font-medium text-[#26332D]"
          >
            Description
          </label>

          <textarea
            id="category-description"
            v-model="description"
            maxlength="500"
            rows="4"
            class="mt-2 block w-full rounded-lg border border-[#C8D1CC] px-3 py-3 text-sm text-[#26332D] outline-none focus:border-[#26332D] focus:ring-1 focus:ring-[#26332D]"
            placeholder="Deskripsi Category (opsional)"
          />

          <p class="mt-1 text-xs text-[#9AA39E]">
            Maksimal 500 karakter.
          </p>
        </div>
      </div>

      <div
        class="mt-6 flex flex-col-reverse gap-3 border-t border-[#EDF1EE] pt-5 sm:flex-row sm:justify-end"
      >
        <button
          type="button"
          class="min-h-11 rounded-lg border border-[#DCE3DF] px-4 text-sm font-medium text-[#46534C] hover:bg-[#F7F9F8]"
          @click="cancel"
        >
          Batal
        </button>

        <button
          type="submit"
          :disabled="isSaving"
          class="min-h-11 rounded-lg bg-[#26332D] px-5 text-sm font-medium text-white hover:bg-[#34433B] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {{
            isSaving
              ? 'Menyimpan...'
              : isEdit
                ? 'Simpan Perubahan'
                : 'Simpan Category'
          }}
        </button>
      </div>
    </form>
  </div>
</template>