<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  createSupplier,
  getSupplier,
  updateSupplier,
} from '../../api/suppliers'

import type {
  CreateSupplierRequest,
  SupplierPaymentTermType,
  UpdateSupplierRequest,
} from '../../types/supplier'

import { useAuth } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const isEdit = computed(() => Boolean(route.params.id))

const isLoading = ref(false)
const isSaving = ref(false)
const errorMessage = ref('')

const supplierCode = ref('')
const name = ref('')
const companyName = ref('')
const contactPerson = ref('')
const phone = ref('')
const email = ref('')

const street = ref('')
const city = ref('')
const province = ref('')
const postalCode = ref('')

const paymentTermType = ref<SupplierPaymentTermType>('CASH')
const paymentTermDays = ref(0)

const hasBankAccount = ref(false)
const bankName = ref('')
const accountNumber = ref('')
const accountName = ref('')

const notes = ref('')

const errors = ref<Record<string, string>>({})

function validateForm() {
  errors.value = {}

  if (!supplierCode.value.trim()) {
    errors.value.supplierCode = 'Kode supplier wajib diisi.'
  }

  if (!name.value.trim()) {
    errors.value.name = 'Nama supplier wajib diisi.'
  }

  if (!companyName.value.trim()) {
    errors.value.companyName = 'Nama perusahaan wajib diisi.'
  }

  if (!contactPerson.value.trim()) {
    errors.value.contactPerson =
      'Contact person wajib diisi.'
  }

  if (!phone.value.trim()) {
    errors.value.phone = 'Nomor telepon wajib diisi.'
  }

  if (!email.value.trim()) {
    errors.value.email = 'Email wajib diisi.'
  }

  if (!street.value.trim()) {
    errors.value.street = 'Alamat wajib diisi.'
  }

  if (!city.value.trim()) {
    errors.value.city = 'Kota wajib diisi.'
  }

  if (!province.value.trim()) {
    errors.value.province =
      'Provinsi wajib diisi.'
  }

  if (!postalCode.value.trim()) {
    errors.value.postalCode =
      'Kode pos wajib diisi.'
  }

  if (
    paymentTermType.value === 'CREDIT' &&
    paymentTermDays.value <= 0
  ) {
    errors.value.paymentTermDays =
      'Jumlah hari kredit harus lebih dari 0.'
  }

  if (
    paymentTermType.value === 'CASH' &&
    paymentTermDays.value !== 0
  ) {
    errors.value.paymentTermDays =
      'Payment term Cash harus 0 hari.'
  }

  if (hasBankAccount.value) {
    if (!bankName.value.trim()) {
      errors.value.bankName =
        'Nama bank wajib diisi.'
    }

    if (!accountNumber.value.trim()) {
      errors.value.accountNumber =
        'Nomor rekening wajib diisi.'
    }

    if (!accountName.value.trim()) {
      errors.value.accountName =
        'Nama pemilik rekening wajib diisi.'
    }
  }

  return Object.keys(errors.value).length === 0
}

async function loadSupplier() {
  if (!isEdit.value) {
    return
  }

  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const supplier = await getSupplier(
      token.value,
      String(route.params.id),
    )

    supplierCode.value = supplier.supplierCode
    name.value = supplier.name
    companyName.value = supplier.companyName
    contactPerson.value = supplier.contactPerson
    phone.value = supplier.phone
    email.value = supplier.email

    street.value = supplier.address.street
    city.value = supplier.address.city
    province.value = supplier.address.province
    postalCode.value = supplier.address.postalCode

    paymentTermType.value =
      supplier.paymentTerm.type

    paymentTermDays.value =
      supplier.paymentTerm.days

    if (supplier.bankAccount) {
      hasBankAccount.value = true
      bankName.value =
        supplier.bankAccount.bankName
      accountNumber.value =
        supplier.bankAccount.accountNumber
      accountName.value =
        supplier.bankAccount.accountName
    }

    notes.value = supplier.notes ?? ''
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil data supplier.'
  } finally {
    isLoading.value = false
  }
}

function buildBankAccount() {
  if (!hasBankAccount.value) {
    return null
  }

  return {
    bankName: bankName.value.trim(),
    accountNumber: accountNumber.value.trim(),
    accountName: accountName.value.trim(),
  }
}

async function handleSubmit() {
  if (!validateForm()) {
    return
  }

  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    return
  }

  isSaving.value = true
  errorMessage.value = ''

  const baseData = {
    name: name.value.trim(),
    companyName: companyName.value.trim(),
    contactPerson: contactPerson.value.trim(),
    phone: phone.value.trim(),
    email: email.value.trim(),
    address: {
      street: street.value.trim(),
      city: city.value.trim(),
      province: province.value.trim(),
      postalCode: postalCode.value.trim(),
    },
    paymentTerm: {
      type: paymentTermType.value,
      days: paymentTermDays.value,
    },
    bankAccount: buildBankAccount(),
    notes: notes.value.trim(),
  }

  try {
    if (isEdit.value) {
      const data: UpdateSupplierRequest = baseData

      await updateSupplier(
        token.value,
        String(route.params.id),
        data,
      )
    } else {
      const data: CreateSupplierRequest = {
        supplierCode: supplierCode.value.trim(),
        ...baseData,
        status: 'ACTIVE',
      }

      await createSupplier(token.value, data)
    }

    await router.push('/suppliers')
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal menyimpan supplier.'
  } finally {
    isSaving.value = false
  }
}

function cancel() {
  router.push('/suppliers')
}

onMounted(loadSupplier)
</script>

<template>
  <section class="mx-auto max-w-5xl space-y-6">
    <header>
      <button
        type="button"
        class="mb-4 text-sm font-medium text-gray-600 hover:text-gray-900"
        @click="cancel"
      >
        ← Kembali ke supplier
      </button>

      <h1 class="text-2xl font-semibold text-gray-900">
        {{ isEdit ? 'Edit supplier' : 'Tambah supplier' }}
      </h1>

      <p class="mt-1 text-sm text-gray-600">
        {{
          isEdit
            ? 'Perbarui informasi supplier.'
            : 'Tambahkan supplier baru ke master data.'
        }}
      </p>
    </header>

    <div
      v-if="isLoading"
      class="space-y-4 rounded-xl border border-gray-200 bg-white p-6"
    >
      <div class="h-10 animate-pulse rounded bg-gray-100" />
      <div class="h-10 animate-pulse rounded bg-gray-100" />
      <div class="h-10 animate-pulse rounded bg-gray-100" />
      <div class="h-32 animate-pulse rounded bg-gray-100" />
    </div>

    <div
      v-else-if="errorMessage && isEdit"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
      role="alert"
    >
      <h2 class="font-medium text-red-800">
        Gagal memuat supplier
      </h2>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>
    </div>

    <form
      v-else
      class="space-y-6"
      @submit.prevent="handleSubmit"
    >
      <div
        v-if="errorMessage"
        class="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        role="alert"
      >
        {{ errorMessage }}
      </div>

      <!-- Informasi utama -->
      <section class="rounded-xl border border-gray-200 bg-white p-6">
        <h2 class="text-lg font-semibold text-gray-900">
          Informasi Supplier
        </h2>

        <div class="mt-5 grid gap-5 md:grid-cols-2">
          <div>
            <label
              for="supplierCode"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Kode supplier
            </label>

            <input
              id="supplierCode"
              v-model="supplierCode"
              :disabled="isEdit"
              type="text"
              placeholder="SUP-001"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100 disabled:bg-gray-100"
            />

            <p
              v-if="errors.supplierCode"
              class="mt-1 text-sm text-red-600"
            >
              {{ errors.supplierCode }}
            </p>
          </div>

          <div>
            <label
              for="name"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Nama supplier
            </label>

            <input
              id="name"
              v-model="name"
              type="text"
              placeholder="PT Supplier ABC"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />

            <p
              v-if="errors.name"
              class="mt-1 text-sm text-red-600"
            >
              {{ errors.name }}
            </p>
          </div>

          <div>
            <label
              for="companyName"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Nama perusahaan
            </label>

            <input
              id="companyName"
              v-model="companyName"
              type="text"
              placeholder="PT Supplier ABC Indonesia"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />

            <p
              v-if="errors.companyName"
              class="mt-1 text-sm text-red-600"
            >
              {{ errors.companyName }}
            </p>
          </div>

          <div>
            <label
              for="contactPerson"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Contact person
            </label>

            <input
              id="contactPerson"
              v-model="contactPerson"
              type="text"
              placeholder="Budi"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />

            <p
              v-if="errors.contactPerson"
              class="mt-1 text-sm text-red-600"
            >
              {{ errors.contactPerson }}
            </p>
          </div>

          <div>
            <label
              for="phone"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Nomor telepon
            </label>

            <input
              id="phone"
              v-model="phone"
              type="tel"
              placeholder="08123456789"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />

            <p
              v-if="errors.phone"
              class="mt-1 text-sm text-red-600"
            >
              {{ errors.phone }}
            </p>
          </div>

          <div>
            <label
              for="email"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Email
            </label>

            <input
              id="email"
              v-model="email"
              type="email"
              placeholder="supplier@example.com"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />

            <p
              v-if="errors.email"
              class="mt-1 text-sm text-red-600"
            >
              {{ errors.email }}
            </p>
          </div>
        </div>
      </section>

      <!-- Alamat -->
      <section class="rounded-xl border border-gray-200 bg-white p-6">
        <h2 class="text-lg font-semibold text-gray-900">
          Alamat
        </h2>

        <div class="mt-5 grid gap-5 md:grid-cols-2">
          <div class="md:col-span-2">
            <label
              for="street"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Jalan
            </label>

            <input
              id="street"
              v-model="street"
              type="text"
              placeholder="Jl. Soekarno Hatta No. 10"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />

            <p
              v-if="errors.street"
              class="mt-1 text-sm text-red-600"
            >
              {{ errors.street }}
            </p>
          </div>

          <div>
            <label
              for="city"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Kota
            </label>

            <input
              id="city"
              v-model="city"
              type="text"
              placeholder="Bandung"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />
          </div>

          <div>
            <label
              for="province"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Provinsi
            </label>

            <input
              id="province"
              v-model="province"
              type="text"
              placeholder="Jawa Barat"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />
          </div>

          <div>
            <label
              for="postalCode"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Kode pos
            </label>

            <input
              id="postalCode"
              v-model="postalCode"
              type="text"
              placeholder="40286"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />
          </div>
        </div>
      </section>

      <!-- Payment -->
      <section class="rounded-xl border border-gray-200 bg-white p-6">
        <h2 class="text-lg font-semibold text-gray-900">
          Payment Term
        </h2>

        <div class="mt-5 grid gap-5 md:grid-cols-2">
          <div>
            <label
              for="paymentTermType"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Tipe pembayaran
            </label>

            <select
              id="paymentTermType"
              v-model="paymentTermType"
              class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
              @change="paymentTermDays = paymentTermType === 'CASH' ? 0 : paymentTermDays"
            >
              <option value="CASH">
                Cash
              </option>

              <option value="CREDIT">
                Credit
              </option>
            </select>
          </div>

          <div>
            <label
              for="paymentTermDays"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Jangka waktu
            </label>

            <div class="flex">
              <input
                id="paymentTermDays"
                v-model.number="paymentTermDays"
                :disabled="paymentTermType === 'CASH'"
                type="number"
                min="0"
                class="w-full rounded-l-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100 disabled:bg-gray-100"
              />

              <span class="flex items-center rounded-r-lg border border-l-0 border-gray-300 bg-gray-50 px-3 text-sm text-gray-600">
                hari
              </span>
            </div>

            <p
              v-if="errors.paymentTermDays"
              class="mt-1 text-sm text-red-600"
            >
              {{ errors.paymentTermDays }}
            </p>
          </div>
        </div>
      </section>

      <!-- Bank -->
      <section class="rounded-xl border border-gray-200 bg-white p-6">
        <div class="flex items-start gap-3">
          <input
            id="hasBankAccount"
            v-model="hasBankAccount"
            type="checkbox"
            class="mt-1 h-4 w-4 rounded border-gray-300 text-green-700 focus:ring-green-500"
          />

          <div>
            <label
              for="hasBankAccount"
              class="font-medium text-gray-900"
            >
              Tambahkan rekening bank
            </label>

            <p class="mt-1 text-sm text-gray-600">
              Data rekening dapat digunakan untuk kebutuhan pembayaran supplier.
            </p>
          </div>
        </div>

        <div
          v-if="hasBankAccount"
          class="mt-5 grid gap-5 md:grid-cols-2"
        >
          <div>
            <label
              for="bankName"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Nama bank
            </label>

            <input
              id="bankName"
              v-model="bankName"
              type="text"
              placeholder="BCA"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />
          </div>

          <div>
            <label
              for="accountNumber"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Nomor rekening
            </label>

            <input
              id="accountNumber"
              v-model="accountNumber"
              type="text"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />
          </div>

          <div class="md:col-span-2">
            <label
              for="accountName"
              class="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Nama rekening
            </label>

            <input
              id="accountName"
              v-model="accountName"
              type="text"
              class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />
          </div>
        </div>
      </section>

      <!-- Notes -->
      <section class="rounded-xl border border-gray-200 bg-white p-6">
        <label
          for="notes"
          class="block text-sm font-medium text-gray-700"
        >
          Catatan
        </label>

        <textarea
          id="notes"
          v-model="notes"
          rows="4"
          placeholder="Catatan supplier..."
          class="mt-1.5 w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
        />
      </section>

      <div class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <button
          type="button"
          class="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
          @click="cancel"
        >
          Batal
        </button>

        <button
          type="submit"
          :disabled="isSaving"
          class="rounded-lg bg-green-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {{ isSaving ? 'Menyimpan...' : 'Simpan supplier' }}
        </button>
      </div>
    </form>
  </section>
</template>