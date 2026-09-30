<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  deleteCategory,
  getCategories,
  updateCategoryStatus,
  type Category,
} from '../../api/categories'
import { useAuth } from '../../stores/auth'

const router = useRouter()
const { token } = useAuth()

const categories = ref<Category[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const actionError = ref('')
const actionLoadingId = ref<string | null>(null)

const activeCount = computed(
  () => categories.value.filter((category) => category.is_active).length,
)

const inactiveCount = computed(
  () => categories.value.filter((category) => !category.is_active).length,
)

const isEmpty = computed(
  () =>
    !isLoading.value &&
    !errorMessage.value &&
    categories.value.length === 0,
)

async function loadCategories() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  actionError.value = ''

  try {
    categories.value = await getCategories(token.value)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data Category.'
  } finally {
    isLoading.value = false
  }
}

function goToCreate() {
  router.push('/categories/create')
}

function goToEdit(categoryId: string) {
  router.push(`/categories/${categoryId}/edit`)
}

async function handleToggleStatus(category: Category) {
  if (!token.value || actionLoadingId.value) {
    return
  }

  actionLoadingId.value = category.id
  actionError.value = ''

  try {
    const updatedCategory = await updateCategoryStatus(
      token.value,
      category.id,
      !category.is_active,
    )

    const index = categories.value.findIndex(
      (item) => item.id === category.id,
    )

    if (index !== -1) {
      categories.value[index] = updatedCategory
    }
  } catch (error) {
    actionError.value =
      error instanceof Error
        ? error.message
        : 'Gagal memperbarui status Category.'
  } finally {
    actionLoadingId.value = null
  }
}

async function handleDelete(category: Category) {
  if (!token.value || actionLoadingId.value) {
    return
  }

  const confirmed = window.confirm(
    `Hapus Category "${category.name}"?`,
  )

  if (!confirmed) {
    return
  }

  actionLoadingId.value = category.id
  actionError.value = ''

  try {
    await deleteCategory(token.value, category.id)

    categories.value = categories.value.filter(
      (item) => item.id !== category.id,
    )
  } catch (error) {
    actionError.value =
      error instanceof Error
        ? error.message
        : 'Gagal menghapus Category.'
  } finally {
    actionLoadingId.value = null
  }
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
  }).format(new Date(value))
}

onMounted(loadCategories)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div
      class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <h1 class="text-2xl font-semibold text-[#26332D]">
          Category
        </h1>

        <p class="mt-1 text-sm text-[#68736D]">
          Kelola master kategori produk.
        </p>
      </div>

      <button
        type="button"
        class="inline-flex min-h-10 items-center justify-center rounded-lg bg-[#26332D] px-4 py-2 text-sm font-medium text-white transition hover:bg-[#34433B]"
        @click="goToCreate"
      >
        + Tambah Category
      </button>
    </div>

    <!-- Summary -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <div
        class="rounded-xl border border-[#DCE3DF] bg-white p-4"
      >
        <p class="text-sm text-[#68736D]">
          Total Category
        </p>

        <p class="mt-2 text-2xl font-semibold text-[#26332D]">
          {{ categories.length }}
        </p>
      </div>

      <div
        class="rounded-xl border border-[#DCE3DF] bg-white p-4"
      >
        <p class="text-sm text-[#68736D]">
          Active
        </p>

        <p class="mt-2 text-2xl font-semibold text-[#16834B]">
          {{ activeCount }}
        </p>
      </div>

      <div
        class="rounded-xl border border-[#DCE3DF] bg-white p-4"
      >
        <p class="text-sm text-[#68736D]">
          Inactive
        </p>

        <p class="mt-2 text-2xl font-semibold text-[#6B756F]">
          {{ inactiveCount }}
        </p>
      </div>
    </div>

    <!-- Error -->
    <div
      v-if="errorMessage"
      class="rounded-xl border border-[#E8B9B3] bg-[#FDF0EE] px-4 py-3 text-sm text-[#C0392B]"
    >
      <div
        class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
      >
        <span>{{ errorMessage }}</span>

        <button
          type="button"
          class="font-medium underline"
          @click="loadCategories"
        >
          Coba lagi
        </button>
      </div>
    </div>

    <!-- Action Error -->
    <div
      v-if="actionError"
      class="rounded-xl border border-[#E8B9B3] bg-[#FDF0EE] px-4 py-3 text-sm text-[#C0392B]"
    >
      {{ actionError }}
    </div>

    <!-- Loading -->
    <div
      v-if="isLoading"
      class="rounded-xl border border-[#DCE3DF] bg-white p-8 text-center text-sm text-[#68736D]"
    >
      Memuat Category...
    </div>

    <!-- Empty -->
    <div
      v-else-if="isEmpty"
      class="rounded-xl border border-dashed border-[#C8D1CC] bg-white p-10 text-center"
    >
      <h2 class="text-base font-semibold text-[#26332D]">
        Belum ada Category
      </h2>

      <p class="mt-1 text-sm text-[#68736D]">
        Tambahkan Category untuk mulai mengelompokkan produk.
      </p>

      <button
        type="button"
        class="mt-4 inline-flex min-h-10 items-center justify-center rounded-lg bg-[#26332D] px-4 py-2 text-sm font-medium text-white"
        @click="goToCreate"
      >
        Tambah Category
      </button>
    </div>

    <!-- Desktop -->
    <div
      v-else
      class="hidden overflow-hidden rounded-xl border border-[#DCE3DF] bg-white md:block"
    >
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead
            class="border-b border-[#DCE3DF] bg-[#F7F9F8]"
          >
            <tr
              class="text-left text-xs font-semibold uppercase tracking-wide text-[#68736D]"
            >
              <th class="px-5 py-3">
                Nama
              </th>

              <th class="px-5 py-3">
                Description
              </th>

              <th class="px-5 py-3">
                Status
              </th>

              <th class="px-5 py-3">
                Dibuat
              </th>

              <th class="px-5 py-3 text-right">
                Action
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-[#EDF1EE]">
            <tr
              v-for="category in categories"
              :key="category.id"
              class="hover:bg-[#FAFBFA]"
            >
              <td class="px-5 py-4">
                <div class="font-medium text-[#26332D]">
                  {{ category.name }}
                </div>
              </td>

              <td class="max-w-md px-5 py-4 text-[#68736D]">
                <span v-if="category.description">
                  {{ category.description }}
                </span>

                <span
                  v-else
                  class="text-[#9AA39E]"
                >
                  —
                </span>
              </td>

              <td class="px-5 py-4">
                <span
                  v-if="category.is_active"
                  class="inline-flex rounded-full border border-[#B9DEC9] bg-[#F0F8F5] px-2.5 py-1 text-xs font-medium text-[#16834B]"
                >
                  Active
                </span>

                <span
                  v-else
                  class="inline-flex rounded-full border border-[#D6DDD9] bg-[#F1F4F2] px-2.5 py-1 text-xs font-medium text-[#6B756F]"
                >
                  Inactive
                </span>
              </td>

              <td class="px-5 py-4 text-[#68736D]">
                {{ formatDate(category.created_at) }}
              </td>

              <td class="px-5 py-4">
                <div class="flex justify-end gap-2">
                  <button
                    type="button"
                    class="rounded-lg border border-[#DCE3DF] px-3 py-2 text-xs font-medium text-[#46534C] hover:bg-[#F7F9F8]"
                    @click="goToEdit(category.id)"
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    :disabled="actionLoadingId === category.id"
                    class="rounded-lg border border-[#DCE3DF] px-3 py-2 text-xs font-medium text-[#46534C] hover:bg-[#F7F9F8] disabled:cursor-not-allowed disabled:opacity-50"
                    @click="handleToggleStatus(category)"
                  >
                    {{
                      actionLoadingId === category.id
                        ? 'Memproses...'
                        : category.is_active
                          ? 'Nonaktifkan'
                          : 'Aktifkan'
                    }}
                  </button>

                  <button
                    type="button"
                    :disabled="actionLoadingId === category.id"
                    class="rounded-lg border border-[#E8B9B3] px-3 py-2 text-xs font-medium text-[#C0392B] hover:bg-[#FDF0EE] disabled:cursor-not-allowed disabled:opacity-50"
                    @click="handleDelete(category)"
                  >
                    Hapus
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Mobile -->
    <div
      v-if="!isLoading && !isEmpty"
      class="space-y-3 md:hidden"
    >
      <div
        v-for="category in categories"
        :key="category.id"
        class="rounded-xl border border-[#DCE3DF] bg-white p-4"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h2 class="font-semibold text-[#26332D]">
              {{ category.name }}
            </h2>

            <p class="mt-1 text-sm text-[#68736D]">
              {{ category.description || 'Tidak ada description.' }}
            </p>
          </div>

          <span
            v-if="category.is_active"
            class="shrink-0 rounded-full border border-[#B9DEC9] bg-[#F0F8F5] px-2.5 py-1 text-xs font-medium text-[#16834B]"
          >
            Active
          </span>

          <span
            v-else
            class="shrink-0 rounded-full border border-[#D6DDD9] bg-[#F1F4F2] px-2.5 py-1 text-xs font-medium text-[#6B756F]"
          >
            Inactive
          </span>
        </div>

        <div class="mt-4 text-xs text-[#9AA39E]">
          Dibuat {{ formatDate(category.created_at) }}
        </div>

        <div class="mt-4 grid grid-cols-3 gap-2">
          <button
            type="button"
            class="min-h-10 rounded-lg border border-[#DCE3DF] px-2 text-xs font-medium text-[#46534C]"
            @click="goToEdit(category.id)"
          >
            Edit
          </button>

          <button
            type="button"
            :disabled="actionLoadingId === category.id"
            class="min-h-10 rounded-lg border border-[#DCE3DF] px-2 text-xs font-medium text-[#46534C] disabled:opacity-50"
            @click="handleToggleStatus(category)"
          >
            {{
              category.is_active
                ? 'Nonaktifkan'
                : 'Aktifkan'
            }}
          </button>

          <button
            type="button"
            :disabled="actionLoadingId === category.id"
            class="min-h-10 rounded-lg border border-[#E8B9B3] px-2 text-xs font-medium text-[#C0392B] disabled:opacity-50"
            @click="handleDelete(category)"
          >
            Hapus
          </button>
        </div>
      </div>
    </div>
  </div>
</template>