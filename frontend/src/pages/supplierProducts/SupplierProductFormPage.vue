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
  <section class="mx-auto max-w-3xl space-y-6">
    <div>
      <button
        type="button"
        class="text-sm font-medium text-slate-600 hover:text-slate-900"
        @click="cancel"
      >
        ← Kembali
      </button>

      <h1 class="mt-3 text-2xl font-semibold text-slate-900">
        {{ isEdit ? 'Edit Produk Supplier' : 'Tambah Produk Supplier' }}
      </h1>

      <p class="mt-1 text-sm text-slate-600">
        Hubungkan produk dengan supplier dan tentukan kondisi pembeliannya.
      </p>
    </div>

    <div
      v-if="loading"
      class="rounded-xl border border-slate-200 bg-white p-6"
      aria-busy="true"
    >
      <div class="space-y-4">
        <div
          v-for="n in 6"
          :key="n"
          class="h-10 animate-pulse rounded bg-slate-100"
        />
      </div>
    </div>

    <form
      v-else
      class="space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      @submit.prevent="save"
    >
      <div
        v-if="error"
        class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        role="alert"
      >
        {{ error }}
      </div>

      <div class="grid gap-5 md:grid-cols-2">
        <label class="block">
          <span class="mb-1 block text-sm font-medium text-slate-700">
            Produk *
          </span>

          <select
            v-model="productId"
            :disabled="isEdit"
            required
            class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 disabled:bg-slate-100"
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
            class="mt-1 block text-xs text-slate-500"
          >
            Harga jual:
            {{ selectedProduct.selling_price ?? selectedProduct.selling_price }}
          </span>
        </label>

        <label class="block">
          <span class="mb-1 block text-sm font-medium text-slate-700">
            Supplier *
          </span>

          <select
            v-model="supplierId"
            :disabled="isEdit"
            required
            class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 disabled:bg-slate-100"
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
            class="mt-1 block text-xs text-slate-500"
          >
            Status: {{ selectedSupplier.status }}
          </span>
        </label>
      </div>

      <div class="border-t border-slate-200 pt-6">
        <h2 class="text-base font-semibold text-slate-900">
          Informasi Pembelian
        </h2>

        <div class="mt-4 grid gap-5 md:grid-cols-2">
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-slate-700">
              SKU Supplier *
            </span>

            <input
              v-model="supplierSku"
              type="text"
              required
              maxlength="100"
              placeholder="BUKU-ABC-001"
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
            />
          </label>

          <label class="block">
            <span class="mb-1 block text-sm font-medium text-slate-700">
              Harga Beli *
            </span>

            <input
              v-model.number="purchasePrice"
              type="number"
              min="0"
              step="1"
              required
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
            />
          </label>

          <label class="block">
            <span class="mb-1 block text-sm font-medium text-slate-700">
              Minimum Order *
            </span>

            <input
              v-model.number="minimumOrder"
              type="number"
              min="1"
              step="1"
              required
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
            />
          </label>

          <label class="block">
            <span class="mb-1 block text-sm font-medium text-slate-700">
              Lead Time (hari) *
            </span>

            <input
              v-model.number="leadTimeDays"
              type="number"
              min="0"
              step="1"
              required
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
            />
          </label>
        </div>
      </div>

      <label class="flex items-start gap-3 rounded-lg border border-slate-200 p-4">
        <input
          v-model="isPreferred"
          type="checkbox"
          class="mt-1 h-4 w-4 rounded border-slate-300 text-emerald-700 focus:ring-emerald-500"
        />

        <span>
          <span class="block text-sm font-medium text-slate-800">
            Preferred supplier
          </span>

          <span class="mt-1 block text-xs text-slate-500">
            Satu produk boleh memiliki lebih dari satu preferred supplier.
          </span>
        </span>
      </label>

      <div class="flex justify-end gap-3 border-t border-slate-200 pt-5">
        <button
          type="button"
          class="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          :disabled="saving"
          @click="cancel"
        >
          Batal
        </button>

        <button
          type="submit"
          class="rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800 disabled:opacity-50"
          :disabled="saving"
        >
          {{ saving ? 'Menyimpan...' : 'Simpan' }}
        </button>
      </div>
    </form>
  </section>
</template>