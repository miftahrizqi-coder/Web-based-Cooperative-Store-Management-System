<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  getSuppliers,
  updateSupplierStatus,
} from '../../api/suppliers'
import type {
  Supplier,
  SupplierStatus,
} from '../../types/supplier'
import { useAuth } from '../../stores/auth'

const router = useRouter()
const { token } = useAuth()

const suppliers = ref<Supplier[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const actionError = ref('')
const search = ref('')
const statusFilter = ref<'ALL' | SupplierStatus>('ALL')
const updatingSupplierId = ref<string | null>(null)

async function loadSuppliers() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    suppliers.value = await getSuppliers(token.value)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data supplier.'
  } finally {
    isLoading.value = false
  }
}

const filteredSuppliers = () => {
  const keyword = search.value.trim().toLowerCase()

  return suppliers.value.filter((supplier) => {
    const matchesSearch =
      !keyword ||
      supplier.supplierCode.toLowerCase().includes(keyword) ||
      supplier.name.toLowerCase().includes(keyword) ||
      supplier.companyName.toLowerCase().includes(keyword) ||
      supplier.contactPerson.toLowerCase().includes(keyword)

    const matchesStatus =
      statusFilter.value === 'ALL' ||
      supplier.status === statusFilter.value

    return matchesSearch && matchesStatus
  })
}

async function changeStatus(
  supplier: Supplier,
  status: SupplierStatus,
) {
  if (!token.value) {
    actionError.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    return
  }

  const actionText =
    status === 'BLACKLISTED'
      ? 'memasukkan supplier ke blacklist'
      : 'menonaktifkan supplier'

  const confirmed = window.confirm(
    `Apakah Anda yakin ingin ${actionText} "${supplier.name}"?`,
  )

  if (!confirmed) {
    return
  }

  updatingSupplierId.value = supplier.id
  actionError.value = ''

  try {
    const updated = await updateSupplierStatus(
      token.value,
      supplier.id,
      status,
    )

    const index = suppliers.value.findIndex(
      (item) => item.id === supplier.id,
    )

    if (index !== -1) {
      suppliers.value[index] = updated
    }
  } catch (error) {
    actionError.value =
      error instanceof Error
        ? error.message
        : 'Gagal memperbarui status supplier.'
  } finally {
    updatingSupplierId.value = null
  }
}

function statusLabel(status: SupplierStatus) {
  switch (status) {
    case 'ACTIVE':
      return 'Aktif'
    case 'INACTIVE':
      return 'Nonaktif'
    case 'BLACKLISTED':
      return 'Blacklist'
  }
}

function statusClass(status: SupplierStatus) {
  switch (status) {
    case 'ACTIVE':
      return 'bg-green-50 text-green-700'
    case 'INACTIVE':
      return 'bg-gray-100 text-gray-700'
    case 'BLACKLISTED':
      return 'bg-red-50 text-red-700'
  }
}

onMounted(loadSuppliers)
</script>

<template>
  <section class="space-y-6">
    <header class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">
          Supplier
        </h1>

        <p class="mt-1 text-sm text-gray-600">
          Kelola data supplier dan status kerja sama.
        </p>
      </div>

      <button
        type="button"
        class="rounded-lg bg-green-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-800 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
        @click="router.push('/suppliers/create')"
      >
        Tambah supplier
      </button>
    </header>

    <div
      v-if="isLoading"
      class="overflow-hidden rounded-xl border border-gray-200 bg-white"
    >
      <div class="space-y-4 p-6">
        <div class="h-10 animate-pulse rounded bg-gray-100" />
        <div class="h-10 animate-pulse rounded bg-gray-100" />
        <div class="h-10 animate-pulse rounded bg-gray-100" />
        <div class="h-10 animate-pulse rounded bg-gray-100" />
      </div>
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
    >
      <h2 class="font-medium text-red-800">
        Gagal memuat supplier
      </h2>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50"
        @click="loadSuppliers"
      >
        Coba lagi
      </button>
    </div>

    <template v-else>
      <div
        v-if="actionError"
        class="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        role="alert"
      >
        {{ actionError }}
      </div>

      <div class="rounded-xl border border-gray-200 bg-white p-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label
              for="supplier-search"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Cari supplier
            </label>

            <input
              id="supplier-search"
              v-model="search"
              type="search"
              placeholder="Kode, nama, perusahaan, atau kontak..."
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />
          </div>

          <div>
            <label
              for="supplier-status"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Status
            </label>

            <select
              id="supplier-status"
              v-model="statusFilter"
              class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            >
              <option value="ALL">
                Semua status
              </option>

              <option value="ACTIVE">
                Aktif
              </option>

              <option value="INACTIVE">
                Nonaktif
              </option>

              <option value="BLACKLISTED">
                Blacklist
              </option>
            </select>
          </div>
        </div>
      </div>

      <div
        v-if="filteredSuppliers().length === 0"
        class="rounded-xl border border-gray-200 bg-white p-8 text-center"
      >
        <h2 class="font-medium text-gray-900">
          Tidak ada supplier
        </h2>

        <p class="mt-1 text-sm text-gray-600">
          Tidak ada supplier yang sesuai dengan pencarian atau filter.
        </p>

        <button
          v-if="!search && statusFilter === 'ALL'"
          type="button"
          class="mt-4 rounded-lg bg-green-700 px-4 py-2 text-sm font-medium text-white hover:bg-green-800"
          @click="router.push('/suppliers/create')"
        >
          Tambah supplier
        </button>
      </div>

      <div
        v-else
        class="overflow-hidden rounded-xl border border-gray-200 bg-white"
      >
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                  Supplier
                </th>

                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                  Kontak
                </th>

                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                  Payment Term
                </th>

                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                  Status
                </th>

                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-600">
                  Aksi
                </th>
              </tr>
            </thead>

            <tbody class="divide-y divide-gray-200">
              <tr
                v-for="supplier in filteredSuppliers()"
                :key="supplier.id"
                class="hover:bg-gray-50"
              >
                <td class="px-4 py-4">
                  <div class="font-medium text-gray-900">
                    {{ supplier.name }}
                  </div>

                  <div class="mt-1 text-xs text-gray-500">
                    {{ supplier.supplierCode }}
                  </div>

                  <div class="mt-1 text-sm text-gray-600">
                    {{ supplier.companyName }}
                  </div>
                </td>

                <td class="px-4 py-4">
                  <div class="text-sm text-gray-900">
                    {{ supplier.contactPerson }}
                  </div>

                  <div class="mt-1 text-sm text-gray-600">
                    {{ supplier.phone }}
                  </div>

                  <div class="mt-1 text-sm text-gray-600">
                    {{ supplier.email }}
                  </div>
                </td>

                <td class="px-4 py-4 text-sm text-gray-700">
                  <span v-if="supplier.paymentTerm.type === 'CASH'">
                    Cash
                  </span>

                  <span v-else>
                    Kredit {{ supplier.paymentTerm.days }} hari
                  </span>
                </td>

                <td class="px-4 py-4">
                  <span
                    class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium"
                    :class="statusClass(supplier.status)"
                  >
                    {{ statusLabel(supplier.status) }}
                  </span>
                </td>

                <td class="px-4 py-4">
                  <div class="flex justify-end gap-2">
                    <button
                      type="button"
                      class="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                      @click="router.push(`/suppliers/${supplier.id}`)"
                    >
                      Detail
                    </button>

                    <button
                      type="button"
                      class="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                      @click="router.push(`/suppliers/${supplier.id}/edit`)"
                    >
                      Edit
                    </button>

                    <button
                      v-if="supplier.status === 'ACTIVE'"
                      type="button"
                      :disabled="updatingSupplierId === supplier.id"
                      class="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                      @click="changeStatus(supplier, 'INACTIVE')"
                    >
                      Nonaktifkan
                    </button>

                    <button
                      v-if="supplier.status !== 'BLACKLISTED'"
                      type="button"
                      :disabled="updatingSupplierId === supplier.id"
                      class="rounded-lg border border-red-200 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                      @click="changeStatus(supplier, 'BLACKLISTED')"
                    >
                      Blacklist
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </section>
</template>