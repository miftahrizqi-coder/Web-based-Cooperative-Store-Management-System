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
  <section class="supplier-form-page">
    <!-- Page Header -->
    <header class="page-header">
      <div>
        <button type="button" class="back-link" @click="cancel">
          <span aria-hidden="true">←</span>
          Kembali ke supplier
        </button>

        <div class="title-row">
          <div>
            <p class="eyebrow">Master Data / Supplier</p>
            <h1>
              {{ isEdit ? 'Edit supplier' : 'Tambah supplier' }}
            </h1>
            <p class="page-description">
              {{
                isEdit
                  ? 'Perbarui informasi supplier dan pastikan data tetap akurat.'
                  : 'Tambahkan supplier baru untuk mendukung proses pengadaan dan pembayaran.'
              }}
            </p>
          </div>

          <span class="mode-badge">
            {{ isEdit ? 'Edit data' : 'Data baru' }}
          </span>
        </div>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="isLoading" class="form-layout" aria-busy="true">
      <div class="main-form-column">
        <section v-for="section in 3" :key="section" class="form-section skeleton-section">
          <div class="skeleton skeleton-title" />
          <div class="skeleton-grid">
            <div v-for="field in 4" :key="field" class="skeleton skeleton-field" />
          </div>
        </section>
      </div>
      <aside class="context-column">
        <div class="context-panel skeleton-context">
          <div class="skeleton skeleton-title" />
          <div v-for="item in 4" :key="item" class="skeleton skeleton-line" />
        </div>
      </aside>
    </div>

    <!-- Load error -->
    <div
      v-else-if="errorMessage && isEdit"
      class="state-error"
      role="alert"
    >
      <div class="state-icon" aria-hidden="true">!</div>
      <div>
        <h2>Gagal memuat supplier</h2>
        <p>{{ errorMessage }}</p>
        <button type="button" class="secondary-button state-action" @click="loadSupplier">
          Coba lagi
        </button>
      </div>
    </div>

    <form v-else class="supplier-form" @submit.prevent="handleSubmit">
      <div
        v-if="errorMessage"
        class="state-error compact"
        role="alert"
      >
        <div class="state-icon" aria-hidden="true">!</div>
        <div>
          <strong>Supplier belum tersimpan</strong>
          <p>{{ errorMessage }}</p>
        </div>
      </div>

      <div class="form-layout">
        <!-- Main form -->
        <div class="main-form-column">
          <!-- Informasi utama -->
          <section class="form-section">
            <div class="section-heading">
              <div class="section-number">01</div>
              <div>
                <h2>Informasi Supplier</h2>
                <p>Informasi utama untuk identitas dan kontak supplier.</p>
              </div>
            </div>

            <div class="field-grid">
              <div class="field">
                <label for="supplierCode">Kode supplier <span>*</span></label>
                <input
                  id="supplierCode"
                  v-model="supplierCode"
                  :disabled="isEdit"
                  :aria-invalid="Boolean(errors.supplierCode)"
                  :aria-describedby="errors.supplierCode ? 'supplierCode-error' : undefined"
                  type="text"
                  placeholder="SUP-001"
                  autocomplete="off"
                  :class="{ 'has-error': errors.supplierCode }"
                />
                <p v-if="errors.supplierCode" id="supplierCode-error" class="field-error" role="alert">
                  {{ errors.supplierCode }}
                </p>
                <p v-else-if="isEdit" class="field-help">Kode supplier tidak dapat diubah.</p>
              </div>

              <div class="field">
                <label for="name">Nama supplier <span>*</span></label>
                <input
                  id="name"
                  v-model="name"
                  :aria-invalid="Boolean(errors.name)"
                  type="text"
                  placeholder="Supplier ABC"
                  autocomplete="organization"
                  :class="{ 'has-error': errors.name }"
                />
                <p v-if="errors.name" class="field-error" role="alert">{{ errors.name }}</p>
              </div>

              <div class="field">
                <label for="companyName">Nama perusahaan <span>*</span></label>
                <input
                  id="companyName"
                  v-model="companyName"
                  :aria-invalid="Boolean(errors.companyName)"
                  type="text"
                  placeholder="PT Supplier ABC Indonesia"
                  autocomplete="organization"
                  :class="{ 'has-error': errors.companyName }"
                />
                <p v-if="errors.companyName" class="field-error" role="alert">{{ errors.companyName }}</p>
              </div>

              <div class="field">
                <label for="contactPerson">Contact person <span>*</span></label>
                <input
                  id="contactPerson"
                  v-model="contactPerson"
                  :aria-invalid="Boolean(errors.contactPerson)"
                  type="text"
                  placeholder="Budi Santoso"
                  autocomplete="name"
                  :class="{ 'has-error': errors.contactPerson }"
                />
                <p v-if="errors.contactPerson" class="field-error" role="alert">{{ errors.contactPerson }}</p>
              </div>

              <div class="field">
                <label for="phone">Nomor telepon <span>*</span></label>
                <input
                  id="phone"
                  v-model="phone"
                  :aria-invalid="Boolean(errors.phone)"
                  type="tel"
                  placeholder="08123456789"
                  autocomplete="tel"
                  :class="{ 'has-error': errors.phone }"
                />
                <p v-if="errors.phone" class="field-error" role="alert">{{ errors.phone }}</p>
              </div>

              <div class="field">
                <label for="email">Email <span>*</span></label>
                <input
                  id="email"
                  v-model="email"
                  :aria-invalid="Boolean(errors.email)"
                  type="email"
                  placeholder="supplier@example.com"
                  autocomplete="email"
                  :class="{ 'has-error': errors.email }"
                />
                <p v-if="errors.email" class="field-error" role="alert">{{ errors.email }}</p>
              </div>
            </div>
          </section>

          <!-- Address -->
          <section class="form-section">
            <div class="section-heading">
              <div class="section-number">02</div>
              <div>
                <h2>Alamat</h2>
                <p>Alamat operasional supplier untuk kebutuhan administrasi.</p>
              </div>
            </div>

            <div class="field-grid">
              <div class="field field-full">
                <label for="street">Alamat lengkap <span>*</span></label>
                <input
                  id="street"
                  v-model="street"
                  :aria-invalid="Boolean(errors.street)"
                  type="text"
                  placeholder="Jl. Soekarno Hatta No. 10"
                  autocomplete="street-address"
                  :class="{ 'has-error': errors.street }"
                />
                <p v-if="errors.street" class="field-error" role="alert">{{ errors.street }}</p>
              </div>

              <div class="field">
                <label for="city">Kota <span>*</span></label>
                <input
                  id="city"
                  v-model="city"
                  :aria-invalid="Boolean(errors.city)"
                  type="text"
                  placeholder="Bandung"
                  autocomplete="address-level2"
                  :class="{ 'has-error': errors.city }"
                />
                <p v-if="errors.city" class="field-error" role="alert">{{ errors.city }}</p>
              </div>

              <div class="field">
                <label for="province">Provinsi <span>*</span></label>
                <input
                  id="province"
                  v-model="province"
                  :aria-invalid="Boolean(errors.province)"
                  type="text"
                  placeholder="Jawa Barat"
                  autocomplete="address-level1"
                  :class="{ 'has-error': errors.province }"
                />
                <p v-if="errors.province" class="field-error" role="alert">{{ errors.province }}</p>
              </div>

              <div class="field">
                <label for="postalCode">Kode pos <span>*</span></label>
                <input
                  id="postalCode"
                  v-model="postalCode"
                  :aria-invalid="Boolean(errors.postalCode)"
                  type="text"
                  inputmode="numeric"
                  placeholder="40286"
                  autocomplete="postal-code"
                  :class="{ 'has-error': errors.postalCode }"
                />
                <p v-if="errors.postalCode" class="field-error" role="alert">{{ errors.postalCode }}</p>
              </div>
            </div>
          </section>

          <!-- Payment -->
          <section class="form-section">
            <div class="section-heading">
              <div class="section-number">03</div>
              <div>
                <h2>Payment Term</h2>
                <p>Atur ketentuan pembayaran yang berlaku untuk supplier ini.</p>
              </div>
            </div>

            <div class="field-grid">
              <div class="field">
                <label for="paymentTermType">Tipe pembayaran <span>*</span></label>
                <select
                  id="paymentTermType"
                  v-model="paymentTermType"
                  @change="paymentTermDays = paymentTermType === 'CASH' ? 0 : paymentTermDays"
                >
                  <option value="CASH">Cash</option>
                  <option value="CREDIT">Credit</option>
                </select>
              </div>

              <div class="field">
                <label for="paymentTermDays">Jangka waktu <span>*</span></label>
                <div class="input-suffix">
                  <input
                    id="paymentTermDays"
                    v-model.number="paymentTermDays"
                    :disabled="paymentTermType === 'CASH'"
                    :aria-invalid="Boolean(errors.paymentTermDays)"
                    type="number"
                    min="0"
                    placeholder="30"
                    :class="{ 'has-error': errors.paymentTermDays }"
                  />
                  <span>hari</span>
                </div>
                <p v-if="errors.paymentTermDays" class="field-error" role="alert">{{ errors.paymentTermDays }}</p>
                <p v-else class="field-help">
                  {{ paymentTermType === 'CASH' ? 'Pembayaran dilakukan langsung.' : 'Masukkan jumlah hari kredit.' }}
                </p>
              </div>
            </div>
          </section>

          <!-- Bank -->
          <section class="form-section">
            <div class="section-heading">
              <div class="section-number">04</div>
              <div>
                <h2>Rekening Bank</h2>
                <p>Opsional. Data ini dapat digunakan saat pembayaran supplier.</p>
              </div>
            </div>

            <label class="check-row" for="hasBankAccount">
              <input id="hasBankAccount" v-model="hasBankAccount" type="checkbox" />
              <span>
                <strong>Tambahkan rekening bank</strong>
                <small>Aktifkan jika supplier memiliki rekening untuk kebutuhan pembayaran.</small>
              </span>
            </label>

            <div v-if="hasBankAccount" class="field-grid bank-fields">
              <div class="field">
                <label for="bankName">Nama bank <span>*</span></label>
                <input
                  id="bankName"
                  v-model="bankName"
                  :aria-invalid="Boolean(errors.bankName)"
                  type="text"
                  placeholder="BCA"
                  :class="{ 'has-error': errors.bankName }"
                />
                <p v-if="errors.bankName" class="field-error" role="alert">{{ errors.bankName }}</p>
              </div>

              <div class="field">
                <label for="accountNumber">Nomor rekening <span>*</span></label>
                <input
                  id="accountNumber"
                  v-model="accountNumber"
                  :aria-invalid="Boolean(errors.accountNumber)"
                  type="text"
                  inputmode="numeric"
                  placeholder="1234567890"
                  :class="{ 'has-error': errors.accountNumber }"
                />
                <p v-if="errors.accountNumber" class="field-error" role="alert">{{ errors.accountNumber }}</p>
              </div>

              <div class="field field-full">
                <label for="accountName">Nama pemilik rekening <span>*</span></label>
                <input
                  id="accountName"
                  v-model="accountName"
                  :aria-invalid="Boolean(errors.accountName)"
                  type="text"
                  placeholder="PT Supplier ABC Indonesia"
                  :class="{ 'has-error': errors.accountName }"
                />
                <p v-if="errors.accountName" class="field-error" role="alert">{{ errors.accountName }}</p>
              </div>
            </div>
          </section>

          <!-- Notes -->
          <section class="form-section">
            <div class="section-heading">
              <div class="section-number">05</div>
              <div>
                <h2>Catatan</h2>
                <p>Informasi tambahan yang perlu diketahui tim operasional.</p>
              </div>
            </div>

            <div class="field">
              <label for="notes">Catatan <span class="optional">Opsional</span></label>
              <textarea
                id="notes"
                v-model="notes"
                rows="4"
                placeholder="Contoh: supplier prioritas, jadwal pengiriman, atau informasi tambahan lainnya."
              />
            </div>
          </section>
        </div>

        <!-- Context / Summary -->
        <aside class="context-column">
          <div class="context-panel sticky-panel">
            <div class="context-heading">
              <span class="context-icon" aria-hidden="true">✓</span>
              <div>
                <h2>Ringkasan</h2>
                <p>Periksa data sebelum disimpan.</p>
              </div>
            </div>

            <dl class="summary-list">
              <div>
                <dt>Kode supplier</dt>
                <dd>{{ supplierCode || '—' }}</dd>
              </div>
              <div>
                <dt>Nama supplier</dt>
                <dd>{{ name || '—' }}</dd>
              </div>
              <div>
                <dt>Perusahaan</dt>
                <dd>{{ companyName || '—' }}</dd>
              </div>
              <div>
                <dt>Kontak</dt>
                <dd>{{ contactPerson || '—' }}</dd>
              </div>
              <div>
                <dt>Pembayaran</dt>
                <dd>
                  {{ paymentTermType === 'CASH' ? 'Cash' : `Credit ${paymentTermDays || 0} hari` }}
                </dd>
              </div>
            </dl>

            <div class="status-preview">
              <span>Status setelah disimpan</span>
              <strong><i aria-hidden="true" /> ACTIVE</strong>
            </div>

            <div class="context-note">
              <strong>Catatan</strong>
              <p>
                Supplier akan tersedia di master data dan dapat digunakan pada proses pengadaan.
              </p>
            </div>
          </div>
        </aside>
      </div>

      <!-- Sticky footer -->
      <footer class="form-footer">
        <div class="footer-meta">
          <span class="required-mark">*</span>
          <span>Field wajib diisi</span>
        </div>

        <div class="footer-actions">
          <button type="button" class="secondary-button" :disabled="isSaving" @click="cancel">
            Batal
          </button>
          <button type="submit" class="primary-button" :disabled="isSaving">
            <span v-if="isSaving" class="button-spinner" aria-hidden="true" />
            {{ isSaving ? 'Menyimpan...' : isEdit ? 'Simpan perubahan' : 'Simpan supplier' }}
          </button>
        </div>
      </footer>
    </form>
  </section>
</template>

<style scoped>
.supplier-form-page {
  --primary-900: #12372a;
  --primary-800: #164a38;
  --primary-700: #176b4d;
  --primary-600: #1f805d;
  --primary-100: #dcefe7;
  --primary-50: #f0f8f5;
  --neutral-950: #17201c;
  --neutral-700: #46514b;
  --neutral-500: #6b756f;
  --neutral-300: #d6ddd9;
  --neutral-200: #e6ebe8;
  --neutral-100: #f1f4f2;
  --neutral-50: #f8faf9;
  --white: #ffffff;
  --success: #16834b;
  --danger: #c0392b;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--neutral-950);
}

.page-header {
  margin-bottom: 24px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--neutral-700);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.back-link:hover {
  color: var(--primary-700);
}

.back-link:focus-visible,
.primary-button:focus-visible,
.secondary-button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
.check-row input:focus-visible {
  outline: 2px solid var(--primary-700);
  outline-offset: 2px;
}

.title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--neutral-500);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.title-row h1 {
  margin: 0;
  color: var(--neutral-950);
  font-size: 28px;
  line-height: 36px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.page-description {
  max-width: 700px;
  margin: 6px 0 0;
  color: var(--neutral-700);
  font-size: 14px;
  line-height: 20px;
}

.mode-badge {
  flex: 0 0 auto;
  border: 1px solid var(--primary-100);
  border-radius: 999px;
  padding: 6px 10px;
  background: var(--primary-50);
  color: var(--primary-800);
  font-size: 12px;
  font-weight: 600;
}

.form-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  align-items: start;
  gap: 24px;
}

.main-form-column,
.supplier-form {
  min-width: 0;
}

.main-form-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-section,
.context-panel {
  border: 1px solid var(--neutral-300);
  border-radius: 8px;
  background: var(--white);
}

.form-section {
  padding: 24px;
}

.section-heading {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 20px;
}

.section-number {
  display: grid;
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  place-items: center;
  border-radius: 6px;
  background: var(--primary-50);
  color: var(--primary-700);
  font-size: 11px;
  font-weight: 700;
}

.section-heading h2,
.context-heading h2 {
  margin: 0;
  color: var(--neutral-950);
  font-size: 18px;
  line-height: 26px;
  font-weight: 600;
}

.section-heading p,
.context-heading p {
  margin: 3px 0 0;
  color: var(--neutral-500);
  font-size: 13px;
  line-height: 18px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px 16px;
}

.field-full {
  grid-column: 1 / -1;
}

.field {
  min-width: 0;
}

.field label {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 7px;
  color: var(--neutral-700);
  font-size: 13px;
  line-height: 18px;
  font-weight: 600;
}

.field label span:not(.optional) {
  color: var(--danger);
}

.field label .optional {
  color: var(--neutral-500);
  font-size: 12px;
  font-weight: 400;
}

.field input,
.field select,
.field textarea {
  display: block;
  width: 100%;
  border: 1px solid var(--neutral-300);
  border-radius: 6px;
  background: var(--white);
  color: var(--neutral-950);
  font: inherit;
  font-size: 14px;
  line-height: 20px;
  transition: border-color 120ms ease, box-shadow 120ms ease, background 120ms ease;
}

.field input,
.field select {
  min-height: 42px;
  padding: 10px 12px;
}

.field textarea {
  min-height: 104px;
  resize: vertical;
  padding: 10px 12px;
}

.field input::placeholder,
.field textarea::placeholder {
  color: #8a948e;
}

.field input:hover,
.field select:hover,
.field textarea:hover {
  border-color: #b8c3bd;
}

.field input:focus,
.field select:focus,
.field textarea:focus {
  border-color: var(--primary-700);
  box-shadow: 0 0 0 3px rgba(23, 107, 77, 0.10);
  outline: none;
}

.field input:disabled {
  background: var(--neutral-100);
  color: var(--neutral-500);
  cursor: not-allowed;
}

.field input.has-error,
.field select.has-error,
.field textarea.has-error {
  border-color: var(--danger);
}

.field input.has-error:focus,
.field select.has-error:focus,
.field textarea.has-error:focus {
  box-shadow: 0 0 0 3px rgba(192, 57, 43, 0.10);
}

.field-error {
  margin: 5px 0 0;
  color: var(--danger);
  font-size: 12px;
  line-height: 16px;
}

.field-help {
  margin: 5px 0 0;
  color: var(--neutral-500);
  font-size: 12px;
  line-height: 16px;
}

.input-suffix {
  display: grid;
  grid-template-columns: 1fr auto;
}

.input-suffix input {
  min-width: 0;
  border-radius: 6px 0 0 6px;
}

.input-suffix span {
  display: flex;
  min-width: 54px;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--neutral-300);
  border-left: 0;
  border-radius: 0 6px 6px 0;
  background: var(--neutral-100);
  color: var(--neutral-700);
  font-size: 13px;
}

.check-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--neutral-200);
  border-radius: 6px;
  background: var(--neutral-50);
  cursor: pointer;
}

.check-row:hover {
  border-color: var(--neutral-300);
}

.check-row input {
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
  margin: 2px 0 0;
  accent-color: var(--primary-700);
}

.check-row span {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.check-row strong {
  color: var(--neutral-950);
  font-size: 13px;
  line-height: 18px;
  font-weight: 600;
}

.check-row small {
  color: var(--neutral-500);
  font-size: 12px;
  line-height: 16px;
}

.bank-fields {
  margin-top: 16px;
}

.context-column {
  min-width: 0;
}

.sticky-panel {
  position: sticky;
  top: 24px;
}

.context-panel {
  padding: 20px;
}

.context-heading {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--neutral-200);
}

.context-icon {
  display: grid;
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  place-items: center;
  border-radius: 50%;
  background: var(--primary-100);
  color: var(--primary-700);
  font-size: 13px;
  font-weight: 700;
}

.summary-list {
  margin: 0;
}

.summary-list > div {
  display: grid;
  gap: 4px;
  padding: 13px 0;
  border-bottom: 1px solid var(--neutral-200);
}

.summary-list dt {
  color: var(--neutral-500);
  font-size: 12px;
  line-height: 16px;
}

.summary-list dd {
  margin: 0;
  overflow-wrap: anywhere;
  color: var(--neutral-950);
  font-size: 13px;
  line-height: 18px;
  font-weight: 600;
}

.status-preview {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 16px;
  padding: 12px;
  border-radius: 6px;
  background: var(--primary-50);
}

.status-preview span {
  color: var(--neutral-500);
  font-size: 12px;
}

.status-preview strong {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--success);
  font-size: 12px;
  font-weight: 700;
}

.status-preview i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--success);
}

.context-note {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--neutral-200);
}

.context-note strong {
  color: var(--neutral-950);
  font-size: 12px;
}

.context-note p {
  margin: 5px 0 0;
  color: var(--neutral-500);
  font-size: 12px;
  line-height: 18px;
}

.form-footer {
  position: sticky;
  z-index: 10;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 24px;
  padding: 14px 0;
  border-top: 1px solid var(--neutral-300);
  background: rgba(248, 250, 249, 0.96);
  backdrop-filter: blur(8px);
}

.footer-meta {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--neutral-500);
  font-size: 12px;
}

.required-mark {
  color: var(--danger);
  font-weight: 700;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.primary-button,
.secondary-button {
  min-height: 40px;
  border-radius: 6px;
  padding: 9px 16px;
  font-size: 13px;
  line-height: 20px;
  font-weight: 600;
  cursor: pointer;
  transition: background 120ms ease, border-color 120ms ease, color 120ms ease, opacity 120ms ease;
}

.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid var(--primary-700);
  background: var(--primary-700);
  color: var(--white);
}

.primary-button:hover:not(:disabled) {
  border-color: var(--primary-600);
  background: var(--primary-600);
}

.secondary-button {
  border: 1px solid var(--neutral-300);
  background: var(--white);
  color: var(--neutral-700);
}

.secondary-button:hover:not(:disabled) {
  border-color: #b8c3bd;
  background: var(--neutral-100);
}

.primary-button:disabled,
.secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.button-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.45);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 700ms linear infinite;
}

.state-error {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
  border: 1px solid #efc8c4;
  border-radius: 8px;
  background: #fff8f7;
  color: var(--danger);
}

.state-error.compact {
  margin-bottom: 16px;
}

.state-error h2,
.state-error strong {
  display: block;
  margin: 0;
  color: #8f2c22;
  font-size: 14px;
  font-weight: 700;
}

.state-error p {
  margin: 4px 0 0;
  color: #a33b30;
  font-size: 13px;
  line-height: 18px;
}

.state-icon {
  display: grid;
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  place-items: center;
  border-radius: 50%;
  background: #f8dfdc;
  color: var(--danger);
  font-weight: 700;
}

.state-action {
  margin-top: 12px;
}

.skeleton-section {
  min-height: 220px;
}

.skeleton {
  background: linear-gradient(90deg, #f1f4f2 25%, #e6ebe8 37%, #f1f4f2 63%);
  background-size: 400% 100%;
  animation: skeleton 1.4s ease infinite;
  border-radius: 6px;
}

.skeleton-title {
  width: 180px;
  height: 20px;
  margin-bottom: 24px;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.skeleton-field {
  height: 62px;
}

.skeleton-context {
  min-height: 300px;
}

.skeleton-line {
  height: 42px;
  margin-top: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes skeleton {
  to { background-position: -200% 0; }
}

@media (max-width: 1199px) {
  .form-layout {
    grid-template-columns: minmax(0, 1fr) 270px;
    gap: 20px;
  }
}

@media (max-width: 900px) {
  .form-layout {
    grid-template-columns: 1fr;
  }

  .context-column {
    order: -1;
  }

  .sticky-panel {
    position: static;
  }

  .summary-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    column-gap: 20px;
  }
}

@media (max-width: 767px) {
  .page-header {
    margin-bottom: 20px;
  }

  .title-row {
    display: block;
  }

  .mode-badge {
    display: inline-flex;
    margin-top: 12px;
  }

  .title-row h1 {
    font-size: 24px;
    line-height: 32px;
  }

  .form-section,
  .context-panel {
    padding: 16px;
  }

  .field-grid,
  .skeleton-grid,
  .summary-list {
    grid-template-columns: 1fr;
  }

  .field-full {
    grid-column: auto;
  }

  .form-footer {
    flex-direction: column;
    align-items: stretch;
    margin-left: -16px;
    margin-right: -16px;
    padding: 12px 16px;
  }

  .footer-meta {
    order: 2;
  }

  .footer-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .footer-actions button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .footer-actions {
    grid-template-columns: 1fr;
  }
}
</style>
