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
      return 'border border-[#176B4D]/20 bg-[#F0F8F5] text-[#176B4D]'
    case 'INACTIVE':
      return 'border border-[#D6DDD9] bg-[#F1F4F2] text-[#46514B]'
    case 'BLACKLISTED':
      return 'border border-[#C0392B]/20 bg-[#FEF4F3] text-[#C0392B]'
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
  <section class="mx-auto max-w-7xl space-y-6 px-4 py-5 sm:px-6 lg:px-8">
    <nav class="text-sm text-[#6B756F]" aria-label="Breadcrumb">
      <button
        type="button"
        class="rounded focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
        @click="router.push('/suppliers')"
      >
        Suppliers
      </button>
      <span class="mx-2">/</span>
      <span class="text-[#46514B]">Detail Supplier</span>
    </nav>

    <div v-if="supplier" class="border-b border-[#D6DDD9] pb-5">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-3">
            <h1 class="text-2xl font-semibold tracking-tight text-[#17201C] sm:text-3xl">
              {{ supplier.name }}
            </h1>
            <span
              class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold"
              :class="statusClass(supplier.status)"
            >
              {{ statusLabel(supplier.status) }}
            </span>
          </div>
          <p class="mt-2 text-sm text-[#6B756F]">
            <span class="font-mono text-[#46514B]">{{ supplier.supplierCode }}</span>
            <span class="mx-2">·</span>
            {{ supplier.companyName }}
          </p>
        </div>

        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-lg border border-[#D6DDD9] bg-white px-4 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
            @click="router.push(`/suppliers/${supplier.id}/edit`)"
          >
            Edit Supplier
          </button>
          <button
            v-if="supplier.status === 'ACTIVE'"
            type="button"
            :disabled="isUpdatingStatus"
            class="rounded-lg border border-[#D6DDD9] bg-white px-4 py-2 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#176B4D]/30"
            @click="changeStatus('INACTIVE')"
          >
            Nonaktifkan
          </button>
          <button
            v-if="supplier.status !== 'BLACKLISTED'"
            type="button"
            :disabled="isUpdatingStatus"
            class="rounded-lg border border-[#C0392B]/25 bg-white px-4 py-2 text-sm font-semibold text-[#C0392B] transition hover:bg-[#FEF4F3] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#C0392B]/20"
            @click="changeStatus('BLACKLISTED')"
          >
            Blacklist
          </button>
        </div>
      </div>
    </div>

    <div v-if="isLoading" class="space-y-5" aria-busy="true">
      <div class="h-40 animate-pulse rounded-xl border border-[#D6DDD9] bg-[#F8FAF9]" />
      <div class="h-40 animate-pulse rounded-xl border border-[#D6DDD9] bg-[#F8FAF9]" />
      <div class="h-40 animate-pulse rounded-xl border border-[#D6DDD9] bg-[#F8FAF9]" />
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-[#C0392B]/20 bg-[#FEF4F3] p-5"
      role="alert"
    >
      <h2 class="font-semibold text-[#9F2F25]">Gagal memuat supplier</h2>
      <p class="mt-1 text-sm text-[#C0392B]">{{ errorMessage }}</p>
      <button
        type="button"
        class="mt-4 rounded-lg border border-[#C0392B]/25 bg-white px-4 py-2 text-sm font-semibold text-[#C0392B] hover:bg-[#FEF4F3] focus:outline-none focus:ring-2 focus:ring-[#C0392B]/20"
        @click="loadSupplier"
      >
        Coba lagi
      </button>
    </div>

    <template v-else-if="supplier">
      <div
        v-if="actionError"
        class="rounded-xl border border-[#C0392B]/20 bg-[#FEF4F3] p-4 text-sm text-[#C0392B]"
        role="alert"
      >
        {{ actionError }}
      </div>

      <!-- Informasi utama -->
      <section class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white">
        <div class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6">
          <h2 class="text-base font-semibold text-[#17201C]">Informasi Supplier</h2>
          <p class="mt-1 text-sm text-[#6B756F]">Informasi kontak utama supplier.</p>
        </div>

        <dl class="grid gap-x-8 gap-y-6 px-5 py-5 sm:grid-cols-2 lg:grid-cols-3 sm:px-6">
          <div>
            <dt class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]">Contact Person</dt>
            <dd class="mt-1 text-sm text-[#17201C]">{{ supplier.contactPerson }}</dd>
          </div>
          <div>
            <dt class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]">Telepon</dt>
            <dd class="mt-1 text-sm text-[#17201C]">{{ supplier.phone }}</dd>
          </div>
          <div class="min-w-0">
            <dt class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]">Email</dt>
            <dd class="mt-1 break-all text-sm text-[#17201C]">{{ supplier.email }}</dd>
          </div>
        </dl>
      </section>

      <div class="grid gap-6 lg:grid-cols-2">
        <!-- Alamat -->
        <section class="rounded-xl border border-[#D6DDD9] bg-white">
          <div class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6">
            <h2 class="text-base font-semibold text-[#17201C]">Alamat</h2>
          </div>
          <div class="px-5 py-5 text-sm leading-6 text-[#46514B] sm:px-6">
            <p>{{ supplier.address.street }}</p>
            <p>{{ supplier.address.city }}, {{ supplier.address.province }} {{ supplier.address.postalCode }}</p>
          </div>
        </section>

        <!-- Payment -->
        <section class="rounded-xl border border-[#D6DDD9] bg-white">
          <div class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6">
            <h2 class="text-base font-semibold text-[#17201C]">Payment Term</h2>
          </div>
          <div class="px-5 py-5 sm:px-6">
            <p class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]">Tipe</p>
            <p class="mt-1 text-sm font-medium text-[#17201C]">
              {{ supplier.paymentTerm.type === 'CASH' ? 'Cash' : `Credit ${supplier.paymentTerm.days} hari` }}
            </p>
          </div>
        </section>
      </div>

      <!-- Rekening bank -->
      <section class="rounded-xl border border-[#D6DDD9] bg-white">
        <div class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6">
          <h2 class="text-base font-semibold text-[#17201C]">Rekening Bank</h2>
        </div>
        <div v-if="supplier.bankAccount" class="grid gap-6 px-5 py-5 sm:grid-cols-2 lg:grid-cols-3 sm:px-6">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]">Bank</p>
            <p class="mt-1 text-sm text-[#17201C]">{{ supplier.bankAccount.bankName }}</p>
          </div>
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]">Nomor Rekening</p>
            <p class="mt-1 font-mono text-sm text-[#17201C]">{{ supplier.bankAccount.accountNumber }}</p>
          </div>
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-[#6B756F]">Nama Rekening</p>
            <p class="mt-1 text-sm text-[#17201C]">{{ supplier.bankAccount.accountName }}</p>
          </div>
        </div>
        <p v-else class="px-5 py-5 text-sm text-[#6B756F] sm:px-6">
          Belum ada rekening bank.
        </p>
      </section>

      <!-- Catatan -->
      <section class="rounded-xl border border-[#D6DDD9] bg-white">
        <div class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6">
          <h2 class="text-base font-semibold text-[#17201C]">Catatan</h2>
        </div>
        <p v-if="supplier.notes" class="whitespace-pre-wrap px-5 py-5 text-sm leading-6 text-[#46514B] sm:px-6">
          {{ supplier.notes }}
        </p>
        <p v-else class="px-5 py-5 text-sm text-[#6B756F] sm:px-6">
          Tidak ada catatan.
        </p>
      </section>

      <!-- Riwayat -->
      <section class="rounded-xl border border-[#D6DDD9] bg-white">
        <div class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6">
          <h2 class="text-base font-semibold text-[#17201C]">Riwayat Supplier</h2>
          <p class="mt-1 text-sm text-[#6B756F]">Modul terkait yang akan menampilkan aktivitas supplier.</p>
        </div>
        <div class="grid gap-0 sm:grid-cols-2 lg:grid-cols-3">
          <div class="border-b border-[#D6DDD9] p-5 sm:border-r">
            <h3 class="text-sm font-semibold text-[#17201C]">Produk yang Disuplai</h3>
            <p class="mt-1 text-sm text-[#6B756F]">Belum tersedia.</p>
          </div>
          <div class="border-b border-[#D6DDD9] p-5 lg:border-r">
            <h3 class="text-sm font-semibold text-[#17201C]">Riwayat PO</h3>
            <p class="mt-1 text-sm text-[#6B756F]">Akan terhubung dengan modul Procurement.</p>
          </div>
          <div class="border-b border-[#D6DDD9] p-5 sm:border-r lg:border-r-0">
            <h3 class="text-sm font-semibold text-[#17201C]">Riwayat Penerimaan</h3>
            <p class="mt-1 text-sm text-[#6B756F]">Akan terhubung dengan Goods Receipt.</p>
          </div>
          <div class="border-b border-[#D6DDD9] p-5 lg:border-b-0 lg:border-r">
            <h3 class="text-sm font-semibold text-[#17201C]">Riwayat Pembelian</h3>
            <p class="mt-1 text-sm text-[#6B756F]">Akan terhubung dengan Purchase.</p>
          </div>
          <div class="border-b border-[#D6DDD9] p-5 sm:border-r sm:border-b-0">
            <h3 class="text-sm font-semibold text-[#17201C]">Riwayat Invoice</h3>
            <p class="mt-1 text-sm text-[#6B756F]">Akan terhubung dengan Supplier Invoice.</p>
          </div>
          <div class="p-5">
            <h3 class="text-sm font-semibold text-[#17201C]">Riwayat Pembayaran</h3>
            <p class="mt-1 text-sm text-[#6B756F]">Akan terhubung dengan Supplier Payment.</p>
          </div>
        </div>
      </section>

      <!-- Hutang -->
      <section class="rounded-xl border border-[#D6DDD9] bg-white">
        <div class="border-b border-[#D6DDD9] px-5 py-4 sm:px-6">
          <h2 class="text-base font-semibold text-[#17201C]">Informasi Hutang</h2>
        </div>
        <div class="px-5 py-6 sm:px-6">
          <div class="rounded-lg border border-dashed border-[#D6DDD9] bg-[#F8FAF9] p-5 text-center">
            <p class="text-sm text-[#6B756F]">
              Informasi hutang supplier akan tersedia setelah modul invoice dan pembayaran terhubung.
            </p>
          </div>
        </div>
      </section>

      <!-- Metadata -->
      <section class="border-t border-[#D6DDD9] pt-4">
        <div class="grid gap-2 text-xs text-[#6B756F] sm:grid-cols-2">
          <p>Dibuat: {{ formatDate(supplier.createdAt) }}</p>
          <p class="sm:text-right">Diperbarui: {{ formatDate(supplier.updatedAt) }}</p>
        </div>
      </section>
    </template>
  </section>
</template>