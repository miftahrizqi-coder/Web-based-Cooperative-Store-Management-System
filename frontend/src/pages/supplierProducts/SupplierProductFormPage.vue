<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  createSupplierProduct,
  getSupplierProduct,
  updateSupplierProduct,
} from '../../api/supplierProducts'
import { getProducts } from '../../api/products'
import { getSuppliers } from '../../api/suppliers'

import type { Product } from '../../types/product'
import type { Supplier } from '../../types/supplier'

const route = useRoute()
const router = useRouter()

const id = computed(() => route.params.id as string | undefined)
const isEdit = computed(() => Boolean(id.value))

const products = ref<Product[]>([])
const suppliers = ref<Supplier[]>([])

const loading = ref(true)
const saving = ref(false)
const error = ref('')

const supplierId = ref('')
const productId = ref('')
const supplierSku = ref('')
const purchasePrice = ref<number | null>(null)
const minimumOrder = ref<number | null>(1)
const leadTimeDays = ref<number | null>(0)
const isPreferred = ref(false)
const isActive = ref(true)

const selectedSupplier = computed(() =>
  suppliers.value.find((item) => item.id === supplierId.value),
)

const selectedProduct = computed(() =>
  products.value.find((item) => item.id === productId.value),
)

function validate() {
  if (!supplierId.value) {
    return 'Supplier wajib dipilih.'
  }

  if (!productId.value) {
    return 'Produk wajib dipilih.'
  }

  if (!supplierSku.value.trim()) {
    return 'SKU supplier wajib diisi.'
  }

  if (
    purchasePrice.value === null ||
    purchasePrice.value < 0
  ) {
    return 'Harga beli tidak boleh negatif.'
  }

  if (
    minimumOrder.value === null ||
    minimumOrder.value < 1
  ) {
    return 'Minimum order minimal 1.'
  }

  if (
    leadTimeDays.value === null ||
    leadTimeDays.value < 0
  ) {
    return 'Lead time tidak boleh negatif.'
  }

  return ''
}

async function loadData() {
  loading.value = true
  error.value = ''

  try {
    const accessToken = localStorage.getItem('access_token')

    if (!accessToken) {
      throw new Error('Sesi login tidak ditemukan.')
    }

    const [productList, supplierList] = await Promise.all([
      getProducts(accessToken),
      getSuppliers(accessToken),
    ])

    products.value = productList
    suppliers.value = supplierList

    if (isEdit.value && id.value) {
      const item = await getSupplierProduct(id.value)

      supplierId.value = item.supplierId
      productId.value = item.productId
      supplierSku.value = item.supplierSku
      purchasePrice.value = item.purchasePrice
      minimumOrder.value = item.minimumOrder
      leadTimeDays.value = item.leadTimeDays
      isPreferred.value = item.isPreferred
      isActive.value = item.isActive
    }
  } catch (err) {
    error.value =
      err instanceof Error
        ? err.message
        : 'Gagal memuat data.'
  } finally {
    loading.value = false
  }
}

async function save() {
  error.value = ''

  const validationError = validate()

  if (validationError) {
    error.value = validationError
    return
  }

  saving.value = true

  try {
    if (isEdit.value && id.value) {
      await updateSupplierProduct(id.value, {
        supplierSku: supplierSku.value.trim(),
        purchasePrice: purchasePrice.value!,
        minimumOrder: minimumOrder.value!,
        leadTimeDays: leadTimeDays.value!,
        isPreferred: isPreferred.value,
      })
    } else {
      await createSupplierProduct({
        supplierId: supplierId.value,
        productId: productId.value,
        supplierSku: supplierSku.value.trim(),
        purchasePrice: purchasePrice.value!,
        minimumOrder: minimumOrder.value!,
        leadTimeDays: leadTimeDays.value!,
        isPreferred: isPreferred.value,
        isActive: true,
      })
    }

    router.push('/supplier-products')
  } catch (err) {
    error.value =
      err instanceof Error
        ? err.message
        : 'Gagal menyimpan Produk Supplier.'
  } finally {
    saving.value = false
  }
}

function cancel() {
  router.push('/supplier-products')
}

onMounted(loadData)
</script>


<template>
  <section class="mx-auto max-w-6xl space-y-6 px-4 py-5 sm:px-6 lg:px-8">
    <nav aria-label="Breadcrumb" class="text-sm text-[#6B756F]">
      <button
        type="button"
        class="font-medium transition hover:text-[#176B4D] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#176B4D] focus-visible:ring-offset-2"
        @click="cancel"
      >
        Procurement
      </button>
      <span class="mx-2 text-[#A8B1AC]">/</span>
      <span>Supplier Products</span>
      <span class="mx-2 text-[#A8B1AC]">/</span>
      <span class="text-[#46514B]">{{ isEdit ? 'Edit' : 'Tambah' }}</span>
    </nav>

    <header class="flex flex-col gap-4 border-b border-[#D6DDD9] pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.12em] text-[#176B4D]">
          Procurement
        </p>
        <h1 class="mt-1 text-2xl font-semibold tracking-tight text-[#17201C] sm:text-3xl">
          {{ isEdit ? 'Edit Produk Supplier' : 'Tambah Produk Supplier' }}
        </h1>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-[#46514B]">
          Hubungkan produk dengan supplier dan tentukan kondisi pembelian yang digunakan.
        </p>
      </div>

      <button
        type="button"
        :disabled="saving"
        class="inline-flex w-full items-center justify-center rounded-lg border border-[#D6DDD9] bg-white px-4 py-2.5 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#176B4D] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
        @click="cancel"
      >
        ← Kembali
      </button>
    </header>

    <div
      v-if="loading"
      class="rounded-xl border border-[#D6DDD9] bg-white p-6"
      aria-busy="true"
      aria-label="Memuat formulir"
    >
      <div class="grid gap-6 md:grid-cols-2">
        <div v-for="n in 8" :key="n" class="space-y-2">
          <div class="h-4 w-28 animate-pulse rounded bg-[#E8ECEA]" />
          <div class="h-11 animate-pulse rounded-lg bg-[#F1F4F2]" />
        </div>
      </div>
    </div>

    <form
      v-else
      class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]"
      @submit.prevent="save"
    >
      <div class="rounded-xl border border-[#D6DDD9] bg-white">
        <div
          v-if="error"
          class="m-5 rounded-lg border border-[#C0392B]/20 bg-[#FEF4F3] p-4 text-sm text-[#C0392B]"
          role="alert"
        >
          <p class="font-semibold">Tidak dapat menyimpan data</p>
          <p class="mt-1">{{ error }}</p>
        </div>

        <div class="p-5 sm:p-6">
          <section>
            <div class="border-b border-[#D6DDD9] pb-4">
              <h2 class="text-base font-semibold text-[#17201C]">
                Relasi Produk & Supplier
              </h2>
              <p class="mt-1 text-sm text-[#6B756F]">
                Pilih produk dan supplier yang menjadi pasangan pembelian.
              </p>
            </div>

            <div class="mt-5 grid gap-5 md:grid-cols-2">
              <label class="block">
                <span class="mb-1.5 block text-sm font-semibold text-[#46514B]">
                  Produk <span class="text-[#C0392B]">*</span>
                </span>

                <select
                  v-model="productId"
                  :disabled="isEdit"
                  required
                  class="w-full rounded-lg border border-[#C9D1CD] bg-white px-3 py-2.5 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/10 disabled:cursor-not-allowed disabled:bg-[#F1F4F2] disabled:text-[#6B756F]"
                >
                  <option value="">Pilih produk</option>
                  <option
                    v-for="product in products"
                    :key="product.id"
                    :value="product.id"
                  >
                    {{ product.name }} — {{ product.sku }}
                  </option>
                </select>

                <span
                  v-if="selectedProduct"
                  class="mt-2 block text-xs text-[#6B756F]"
                >
                  SKU utama: <span class="font-medium text-[#46514B]">{{ selectedProduct.sku }}</span>
                </span>
              </label>

              <label class="block">
                <span class="mb-1.5 block text-sm font-semibold text-[#46514B]">
                  Supplier <span class="text-[#C0392B]">*</span>
                </span>

                <select
                  v-model="supplierId"
                  :disabled="isEdit"
                  required
                  class="w-full rounded-lg border border-[#C9D1CD] bg-white px-3 py-2.5 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/10 disabled:cursor-not-allowed disabled:bg-[#F1F4F2] disabled:text-[#6B756F]"
                >
                  <option value="">Pilih supplier</option>
                  <option
                    v-for="supplier in suppliers"
                    :key="supplier.id"
                    :value="supplier.id"
                  >
                    {{ supplier.name }} — {{ supplier.supplierCode }}
                  </option>
                </select>

                <span
                  v-if="selectedSupplier"
                  class="mt-2 block text-xs text-[#6B756F]"
                >
                  Kode supplier:
                  <span class="font-medium text-[#46514B]">{{ selectedSupplier.supplierCode }}</span>
                  <span class="mx-1">·</span>
                  Status:
                  <span class="font-medium text-[#46514B]">{{ selectedSupplier.status }}</span>
                </span>
              </label>
            </div>
          </section>

          <section class="mt-8 border-t border-[#D6DDD9] pt-6">
            <div class="border-b border-[#D6DDD9] pb-4">
              <h2 class="text-base font-semibold text-[#17201C]">
                Informasi Pembelian
              </h2>
              <p class="mt-1 text-sm text-[#6B756F]">
                Data berikut digunakan sebagai acuan saat melakukan pembelian dari supplier.
              </p>
            </div>

            <div class="mt-5 grid gap-5 md:grid-cols-2">
              <label class="block md:col-span-2">
                <span class="mb-1.5 block text-sm font-semibold text-[#46514B]">
                  SKU Supplier <span class="text-[#C0392B]">*</span>
                </span>
                <input
                  v-model="supplierSku"
                  type="text"
                  required
                  maxlength="100"
                  placeholder="Contoh: BUKU-ABC-001"
                  class="w-full rounded-lg border border-[#C9D1CD] bg-white px-3 py-2.5 text-sm text-[#17201C] outline-none transition placeholder:text-[#A0AAA4] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/10"
                />
              </label>

              <label class="block">
                <span class="mb-1.5 block text-sm font-semibold text-[#46514B]">
                  Harga Beli <span class="text-[#C0392B]">*</span>
                </span>
                <div class="relative">
                  <span class="pointer-events-none absolute inset-y-0 left-3 flex items-center text-sm text-[#6B756F]">
                    Rp
                  </span>
                  <input
                    v-model.number="purchasePrice"
                    type="number"
                    min="0"
                    step="1"
                    required
                    class="w-full rounded-lg border border-[#C9D1CD] bg-white py-2.5 pl-10 pr-3 text-right text-sm tabular-nums text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/10"
                  />
                </div>
              </label>

              <label class="block">
                <span class="mb-1.5 block text-sm font-semibold text-[#46514B]">
                  Minimum Order <span class="text-[#C0392B]">*</span>
                </span>
                <input
                  v-model.number="minimumOrder"
                  type="number"
                  min="1"
                  step="1"
                  required
                  class="w-full rounded-lg border border-[#C9D1CD] bg-white px-3 py-2.5 text-right text-sm tabular-nums text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/10"
                />
              </label>

              <label class="block">
                <span class="mb-1.5 block text-sm font-semibold text-[#46514B]">
                  Lead Time (hari) <span class="text-[#C0392B]">*</span>
                </span>
                <div class="relative">
                  <input
                    v-model.number="leadTimeDays"
                    type="number"
                    min="0"
                    step="1"
                    required
                    class="w-full rounded-lg border border-[#C9D1CD] bg-white py-2.5 pl-3 pr-16 text-right text-sm tabular-nums text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/10"
                  />
                  <span class="pointer-events-none absolute inset-y-0 right-3 flex items-center text-xs text-[#6B756F]">
                    hari
                  </span>
                </div>
              </label>
            </div>
          </section>

          <section class="mt-8 border-t border-[#D6DDD9] pt-6">
            <label class="flex cursor-pointer items-start gap-3 rounded-lg border border-[#D6DDD9] bg-[#F8FAF9] p-4 transition hover:border-[#B8C3BD]">
              <input
                v-model="isPreferred"
                type="checkbox"
                class="mt-0.5 h-4 w-4 rounded border-[#C9D1CD] text-[#176B4D] focus:ring-[#176B4D]"
              />

              <span>
                <span class="block text-sm font-semibold text-[#17201C]">
                  Preferred supplier
                </span>
                <span class="mt-1 block text-xs leading-5 text-[#6B756F]">
                  Tandai supplier ini sebagai pilihan utama untuk produk tersebut.
                </span>
              </span>
            </label>
          </section>

          <div class="mt-8 flex flex-col-reverse gap-3 border-t border-[#D6DDD9] pt-5 sm:flex-row sm:justify-end">
            <button
              type="button"
              class="w-full rounded-lg border border-[#C9D1CD] bg-white px-4 py-2.5 text-sm font-semibold text-[#46514B] transition hover:bg-[#F8FAF9] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#176B4D] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
              :disabled="saving"
              @click="cancel"
            >
              Batal
            </button>

            <button
              type="submit"
              class="w-full rounded-lg bg-[#176B4D] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#176B4D] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
              :disabled="saving"
            >
              {{ saving ? 'Menyimpan...' : (isEdit ? 'Simpan Perubahan' : 'Simpan Produk Supplier') }}
            </button>
          </div>
        </div>
      </div>

      <aside class="h-fit rounded-xl border border-[#D6DDD9] bg-[#F8FAF9] p-5 lg:sticky lg:top-5">
        <h2 class="text-sm font-semibold uppercase tracking-[0.08em] text-[#46514B]">
          Ringkasan
        </h2>

        <dl class="mt-4 divide-y divide-[#D6DDD9]">
          <div class="py-3 first:pt-0">
            <dt class="text-xs text-[#6B756F]">Produk</dt>
            <dd class="mt-1 text-sm font-semibold text-[#17201C]">
              {{ selectedProduct?.name || 'Belum dipilih' }}
            </dd>
          </div>

          <div class="py-3">
            <dt class="text-xs text-[#6B756F]">Supplier</dt>
            <dd class="mt-1 text-sm font-semibold text-[#17201C]">
              {{ selectedSupplier?.name || 'Belum dipilih' }}
            </dd>
          </div>

          <div class="py-3">
            <dt class="text-xs text-[#6B756F]">Harga beli</dt>
            <dd class="mt-1 text-right text-base font-semibold tabular-nums text-[#17201C]">
              {{ purchasePrice === null ? '—' : `Rp ${purchasePrice.toLocaleString('id-ID')}` }}
            </dd>
          </div>

          <div class="py-3">
            <dt class="text-xs text-[#6B756F]">Minimum order</dt>
            <dd class="mt-1 text-right text-sm font-semibold tabular-nums text-[#17201C]">
              {{ minimumOrder ?? '—' }}
            </dd>
          </div>

          <div class="py-3 last:pb-0">
            <dt class="text-xs text-[#6B756F]">Lead time</dt>
            <dd class="mt-1 text-right text-sm font-semibold tabular-nums text-[#17201C]">
              {{ leadTimeDays ?? '—' }} hari
            </dd>
          </div>
        </dl>

        <div class="mt-5 rounded-lg border border-[#D6DDD9] bg-white p-3 text-xs leading-5 text-[#6B756F]">
          Field bertanda <span class="font-semibold text-[#C0392B]">*</span> wajib diisi.
          Saat edit, produk dan supplier tidak dapat diubah.
        </div>
      </aside>
    </form>
  </section>
</template>
