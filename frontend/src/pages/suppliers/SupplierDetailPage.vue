<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  getSupplier,
  updateSupplierStatus,
} from '../../api/suppliers'

import type {
  Supplier,
  SupplierStatus,
} from '../../types/supplier'

import { useAuth } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const supplier = ref<Supplier | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')
const actionError = ref('')
const isUpdatingStatus = ref(false)

async function loadSupplier() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    supplier.value = await getSupplier(
      token.value,
      String(route.params.id),
    )
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil detail supplier.'
  } finally {
    isLoading.value = false
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

async function changeStatus(status: SupplierStatus) {
  if (!supplier.value || !token.value) {
    return
  }

  const actionText =
    status === 'BLACKLISTED'
      ? 'memasukkan supplier ke blacklist'
      : 'menonaktifkan supplier'

  const confirmed = window.confirm(
    `Apakah Anda yakin ingin ${actionText} "${supplier.value.name}"?`,
  )

  if (!confirmed) {
    return
  }

  isUpdatingStatus.value = true
  actionError.value = ''

  try {
    supplier.value = await updateSupplierStatus(
      token.value,
      supplier.value.id,
      status,
    )
  } catch (error) {
    actionError.value =
      error instanceof Error
        ? error.message
        : 'Gagal memperbarui status supplier.'
  } finally {
    isUpdatingStatus.value = false
  }
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

onMounted(loadSupplier)
</script>

<template>
  <section class="mx-auto max-w-6xl space-y-6">
    <header>
      <button
        type="button"
        class="mb-4 text-sm font-medium text-gray-600 hover:text-gray-900"
        @click="router.push('/suppliers')"
      >
        ← Kembali ke supplier
      </button>

      <div
        v-if="supplier"
        class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
      >
        <div>
          <div class="flex flex-wrap items-center gap-3">
            <h1 class="text-2xl font-semibold text-gray-900">
              {{ supplier.name }}
            </h1>

            <span
              class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium"
              :class="statusClass(supplier.status)"
            >
              {{ statusLabel(supplier.status) }}
            </span>
          </div>

          <p class="mt-1 text-sm text-gray-600">
            {{ supplier.supplierCode }}
            ·
            {{ supplier.companyName }}
          </p>
        </div>

        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            @click="router.push(`/suppliers/${supplier.id}/edit`)"
          >
            Edit
          </button>

          <button
            v-if="supplier.status === 'ACTIVE'"
            type="button"
            :disabled="isUpdatingStatus"
            class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            @click="changeStatus('INACTIVE')"
          >
            Nonaktifkan
          </button>

          <button
            v-if="supplier.status !== 'BLACKLISTED'"
            type="button"
            :disabled="isUpdatingStatus"
            class="rounded-lg border border-red-200 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
            @click="changeStatus('BLACKLISTED')"
          >
            Blacklist
          </button>
        </div>
      </div>
    </header>

    <div
      v-if="isLoading"
      class="space-y-4"
    >
      <div class="h-40 animate-pulse rounded-xl bg-gray-100" />
      <div class="h-40 animate-pulse rounded-xl bg-gray-100" />
      <div class="h-40 animate-pulse rounded-xl bg-gray-100" />
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
      role="alert"
    >
      <h2 class="font-medium text-red-800">
        Gagal memuat supplier
      </h2>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-700"
        @click="loadSupplier"
      >
        Coba lagi
      </button>
    </div>

    <template v-else-if="supplier">
      <div
        v-if="actionError"
        class="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        role="alert"
      >
        {{ actionError }}
      </div>

      <!-- Informasi kontak -->
      <section class="rounded-xl border border-gray-200 bg-white p-6">
        <h2 class="text-lg font-semibold text-gray-900">
          Informasi Supplier
        </h2>

        <div class="mt-5 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div>
            <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
              Contact Person
            </p>
            <p class="mt-1 text-sm text-gray-900">
              {{ supplier.contactPerson }}
            </p>
          </div>

          <div>
            <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
              Telepon
            </p>
            <p class="mt-1 text-sm text-gray-900">
              {{ supplier.phone }}
            </p>
          </div>

          <div>
            <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
              Email
            </p>
            <p class="mt-1 break-all text-sm text-gray-900">
              {{ supplier.email }}
            </p>
          </div>
        </div>
      </section>

      <!-- Alamat -->
      <section class="rounded-xl border border-gray-200 bg-white p-6">
        <h2 class="text-lg font-semibold text-gray-900">
          Alamat
        </h2>

        <div class="mt-4 text-sm leading-6 text-gray-700">
          <p>{{ supplier.address.street }}</p>
          <p>
            {{ supplier.address.city }},
            {{ supplier.address.province }}
            {{ supplier.address.postalCode }}
          </p>
        </div>
      </section>

      <!-- Payment -->
      <section class="grid gap-6 lg:grid-cols-2">
        <div class="rounded-xl border border-gray-200 bg-white p-6">
          <h2 class="text-lg font-semibold text-gray-900">
            Payment Term
          </h2>

          <div class="mt-4">
            <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
              Tipe
            </p>

            <p class="mt-1 text-sm text-gray-900">
              {{
                supplier.paymentTerm.type === 'CASH'
                  ? 'Cash'
                  : `Credit ${supplier.paymentTerm.days} hari`
              }}
            </p>
          </div>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-6">
          <h2 class="text-lg font-semibold text-gray-900">
            Rekening Bank
          </h2>

          <div
            v-if="supplier.bankAccount"
            class="mt-4 space-y-3"
          >
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
                Bank
              </p>
              <p class="mt-1 text-sm text-gray-900">
                {{ supplier.bankAccount.bankName }}
              </p>
            </div>

            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
                Nomor Rekening
              </p>
              <p class="mt-1 text-sm text-gray-900">
                {{ supplier.bankAccount.accountNumber }}
              </p>
            </div>

            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
                Nama Rekening
              </p>
              <p class="mt-1 text-sm text-gray-900">
                {{ supplier.bankAccount.accountName }}
              </p>
            </div>
          </div>

          <p
            v-else
            class="mt-4 text-sm text-gray-500"
          >
            Belum ada rekening bank.
          </p>
        </div>
      </section>

      <!-- Catatan -->
      <section class="rounded-xl border border-gray-200 bg-white p-6">
        <h2 class="text-lg font-semibold text-gray-900">
          Catatan
        </h2>

        <p
          v-if="supplier.notes"
          class="mt-4 whitespace-pre-wrap text-sm leading-6 text-gray-700"
        >
          {{ supplier.notes }}
        </p>

        <p
          v-else
          class="mt-4 text-sm text-gray-500"
        >
          Tidak ada catatan.
        </p>
      </section>

      <!-- Riwayat -->
      <section class="rounded-xl border border-gray-200 bg-white p-6">
        <h2 class="text-lg font-semibold text-gray-900">
          Riwayat Supplier
        </h2>

        <div class="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div class="rounded-lg border border-gray-200 p-4">
            <h3 class="font-medium text-gray-900">
              Produk yang Disuplai
            </h3>
            <p class="mt-1 text-sm text-gray-500">
              Belum tersedia.
            </p>
          </div>

          <div class="rounded-lg border border-gray-200 p-4">
            <h3 class="font-medium text-gray-900">
              Riwayat PO
            </h3>
            <p class="mt-1 text-sm text-gray-500">
              Akan terhubung dengan modul Procurement.
            </p>
          </div>

          <div class="rounded-lg border border-gray-200 p-4">
            <h3 class="font-medium text-gray-900">
              Riwayat Penerimaan
            </h3>
            <p class="mt-1 text-sm text-gray-500">
              Akan terhubung dengan Goods Receipt.
            </p>
          </div>

          <div class="rounded-lg border border-gray-200 p-4">
            <h3 class="font-medium text-gray-900">
              Riwayat Pembelian
            </h3>
            <p class="mt-1 text-sm text-gray-500">
              Akan terhubung dengan Purchase.
            </p>
          </div>

          <div class="rounded-lg border border-gray-200 p-4">
            <h3 class="font-medium text-gray-900">
              Riwayat Invoice
            </h3>
            <p class="mt-1 text-sm text-gray-500">
              Akan terhubung dengan Supplier Invoice.
            </p>
          </div>

          <div class="rounded-lg border border-gray-200 p-4">
            <h3 class="font-medium text-gray-900">
              Riwayat Pembayaran
            </h3>
            <p class="mt-1 text-sm text-gray-500">
              Akan terhubung dengan Supplier Payment.
            </p>
          </div>
        </div>
      </section>

      <!-- Hutang -->
      <section class="rounded-xl border border-gray-200 bg-white p-6">
        <h2 class="text-lg font-semibold text-gray-900">
          Informasi Hutang
        </h2>

        <div class="mt-4 rounded-lg border border-dashed border-gray-300 p-6 text-center">
          <p class="text-sm text-gray-600">
            Informasi hutang supplier akan tersedia setelah modul
            invoice dan pembayaran terhubung.
          </p>
        </div>
      </section>

      <!-- Metadata -->
      <section class="rounded-xl border border-gray-200 bg-gray-50 p-4">
        <div class="grid gap-3 text-xs text-gray-500 sm:grid-cols-2">
          <p>
            Dibuat:
            {{ formatDate(supplier.createdAt) }}
          </p>

          <p>
            Diperbarui:
            {{ formatDate(supplier.updatedAt) }}
          </p>
        </div>
      </section>
    </template>
  </section>
</template>