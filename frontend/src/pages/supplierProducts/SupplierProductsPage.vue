<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  getSupplierProducts,
  updateSupplierProductStatus,
} from '../../api/supplierProducts'
import { getProducts } from '../../api/products'
import { getSuppliers } from '../../api/suppliers'

import type { SupplierProduct } from '../../types/supplierProduct'
import type { Product } from '../../types/product'
import type { Supplier } from '../../types/supplier'

const router = useRouter()

const items = ref<SupplierProduct[]>([])
const products = ref<Product[]>([])
const suppliers = ref<Supplier[]>([])

const loading = ref(true)
const error = ref('')
const search = ref('')
const statusFilter = ref('all')

const showDeactivateDialog = ref(false)
const selectedItem = ref<SupplierProduct | null>(null)
const actionLoading = ref(false)

const productMap = computed(() => {
  return new Map(products.value.map((item) => [item.id, item]))
})

const supplierMap = computed(() => {
  return new Map(suppliers.value.map((item) => [item.id, item]))
})

const filteredItems = computed(() => {
  const keyword = search.value.trim().toLowerCase()

  return items.value.filter((item) => {
    const product = productMap.value.get(item.productId)
    const supplier = supplierMap.value.get(item.supplierId)

    const matchesSearch =
      !keyword ||
      item.supplierSku.toLowerCase().includes(keyword) ||
      product?.name.toLowerCase().includes(keyword) ||
      supplier?.name.toLowerCase().includes(keyword)

    const matchesStatus =
      statusFilter.value === 'all' ||
      (statusFilter.value === 'active' && item.isActive) ||
      (statusFilter.value === 'inactive' && !item.isActive)

    return matchesSearch && matchesStatus
  })
})

function formatRupiah(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

function productName(id: string) {
  return productMap.value.get(id)?.name ?? 'Produk tidak ditemukan'
}

function supplierName(id: string) {
  return supplierMap.value.get(id)?.name ?? 'Supplier tidak ditemukan'
}

async function loadData() {
  loading.value = true
  error.value = ''

  try {
    const accessToken = localStorage.getItem('access_token')

    if (!accessToken) {
      throw new Error('Sesi login tidak ditemukan.')
    }
    const [supplierProducts, productList, supplierList] =
      await Promise.all([
        getSupplierProducts(),
        getProducts(accessToken),
        getSuppliers(accessToken),
      ])

    items.value = supplierProducts
    products.value = productList
    suppliers.value = supplierList
  } catch (err) {
    error.value =
      err instanceof Error
        ? err.message
        : 'Gagal memuat data Produk Supplier.'
  } finally {
    loading.value = false
  }
}

function openCreate() {
  router.push('/supplier-products/create')
}

function openEdit(id: string) {
  router.push(`/supplier-products/${id}/edit`)
}

function openDeactivate(item: SupplierProduct) {
  selectedItem.value = item
  showDeactivateDialog.value = true
}

async function confirmDeactivate() {
  if (!selectedItem.value) return

  actionLoading.value = true

  try {
    await updateSupplierProductStatus(
      selectedItem.value.id,
      false,
    )

    showDeactivateDialog.value = false
    selectedItem.value = null

    await loadData()
  } catch (err) {
    error.value =
      err instanceof Error
        ? err.message
        : 'Gagal menonaktifkan Produk Supplier.'
  } finally {
    actionLoading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <section class="space-y-6">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-slate-900">
          Produk Supplier
        </h1>
        <p class="mt-1 text-sm text-slate-600">
          Kelola hubungan produk dengan supplier dan harga pembeliannya.
        </p>
      </div>

      <button
        type="button"
        class="rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
        @click="openCreate"
      >
        Tambah Produk Supplier
      </button>
    </div>

    <div
      v-if="error"
      class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
      role="alert"
    >
      <div class="flex items-center justify-between gap-4">
        <span>{{ error }}</span>

        <button
          type="button"
          class="font-semibold underline"
          @click="loadData"
        >
          Coba lagi
        </button>
      </div>
    </div>

    <div class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="grid gap-3 md:grid-cols-[1fr_180px]">
        <label class="block">
          <span class="mb-1 block text-sm font-medium text-slate-700">
            Cari
          </span>

          <input
            v-model="search"
            type="search"
            placeholder="Cari produk, supplier, atau SKU supplier..."
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
          />
        </label>

        <label class="block">
          <span class="mb-1 block text-sm font-medium text-slate-700">
            Status
          </span>

          <select
            v-model="statusFilter"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
          >
            <option value="all">Semua</option>
            <option value="active">Aktif</option>
            <option value="inactive">Nonaktif</option>
          </select>
        </label>
      </div>
    </div>

    <div
      v-if="loading"
      class="rounded-xl border border-slate-200 bg-white p-6"
      aria-busy="true"
    >
      <div class="space-y-4">
        <div
          v-for="n in 5"
          :key="n"
          class="h-12 animate-pulse rounded bg-slate-100"
        />
      </div>
    </div>

    <div
      v-else-if="filteredItems.length === 0"
      class="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center"
    >
      <h2 class="font-semibold text-slate-900">
        Tidak ada Produk Supplier
      </h2>

      <p class="mt-1 text-sm text-slate-600">
        Belum ada relasi yang sesuai dengan pencarian atau filter.
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white"
        @click="openCreate"
      >
        Tambah Produk Supplier
      </button>
    </div>

    <div
      v-else
      class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
    >
      <div class="overflow-x-auto">
        <table class="min-w-[900px] w-full text-left text-sm">
          <thead class="border-b border-slate-200 bg-slate-50">
            <tr>
              <th class="px-4 py-3 font-semibold text-slate-700">
                Produk
              </th>
              <th class="px-4 py-3 font-semibold text-slate-700">
                Supplier
              </th>
              <th class="px-4 py-3 font-semibold text-slate-700">
                SKU Supplier
              </th>
              <th class="px-4 py-3 text-right font-semibold text-slate-700">
                Harga Beli
              </th>
              <th class="px-4 py-3 text-right font-semibold text-slate-700">
                Min. Order
              </th>
              <th class="px-4 py-3 text-right font-semibold text-slate-700">
                Lead Time
              </th>
              <th class="px-4 py-3 font-semibold text-slate-700">
                Status
              </th>
              <th class="px-4 py-3 text-right font-semibold text-slate-700">
                Aksi
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="item in filteredItems"
              :key="item.id"
              class="hover:bg-slate-50"
            >
              <td class="px-4 py-3">
                <div class="font-medium text-slate-900">
                  {{ productName(item.productId) }}
                </div>

                <div class="text-xs text-slate-500">
                  {{ item.isPreferred ? 'Preferred supplier' : '' }}
                </div>
              </td>

              <td class="px-4 py-3 text-slate-700">
                {{ supplierName(item.supplierId) }}
              </td>

              <td class="px-4 py-3 font-mono text-slate-700">
                {{ item.supplierSku }}
              </td>

              <td class="px-4 py-3 text-right text-slate-700">
                {{ formatRupiah(item.purchasePrice) }}
              </td>

              <td class="px-4 py-3 text-right text-slate-700">
                {{ item.minimumOrder }}
              </td>

              <td class="px-4 py-3 text-right text-slate-700">
                {{ item.leadTimeDays }} hari
              </td>

              <td class="px-4 py-3">
                <span
                  class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium"
                  :class="
                    item.isActive
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-slate-100 text-slate-600'
                  "
                >
                  {{ item.isActive ? 'Aktif' : 'Nonaktif' }}
                </span>
              </td>

              <td class="px-4 py-3 text-right">
                <div class="flex justify-end gap-2">
                  <button
                    type="button"
                    class="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                    @click="openEdit(item.id)"
                  >
                    Edit
                  </button>

                  <button
                    v-if="item.isActive"
                    type="button"
                    class="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
                    @click="openDeactivate(item)"
                  >
                    Nonaktifkan
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div
      v-if="showDeactivateDialog"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="deactivate-title"
    >
      <div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2
          id="deactivate-title"
          class="text-lg font-semibold text-slate-900"
        >
          Nonaktifkan Produk Supplier?
        </h2>

        <p class="mt-2 text-sm text-slate-600">
          Relasi ini tidak akan dihapus. Data tetap tersimpan sebagai
          riwayat.
        </p>

        <div class="mt-6 flex justify-end gap-3">
          <button
            type="button"
            class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold"
            :disabled="actionLoading"
            @click="showDeactivateDialog = false"
          >
            Batal
          </button>

          <button
            type="button"
            class="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            :disabled="actionLoading"
            @click="confirmDeactivate"
          >
            {{ actionLoading ? 'Memproses...' : 'Nonaktifkan' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>