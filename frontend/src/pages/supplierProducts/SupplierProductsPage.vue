<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

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
const route = useRoute()
// Dipakai rute /suppliers/:id/products (PRD §36).
const supplierFilter = ref(typeof route.query.supplierId === 'string' ? route.query.supplierId : '')

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

    const matchesSupplier = !supplierFilter.value || item.supplierId === supplierFilter.value

    const matchesStatus =
      statusFilter.value === 'all' ||
      (statusFilter.value === 'active' && item.isActive) ||
      (statusFilter.value === 'inactive' && !item.isActive)

    return matchesSearch && matchesStatus && matchesSupplier
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
  return productMap.value.get(id)?.name ?? items.value.find((i) => i.productId === id)?.productName ?? 'Produk tidak ditemukan'
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
  <section class="space-y-6 text-[#17201C]">
    <!-- Breadcrumb + page header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <nav class="mb-2 text-xs font-medium text-[#6B756F]" aria-label="Breadcrumb">
          <span>Procurement</span>
          <span class="mx-2">/</span>
          <span class="text-[#46514B]">Produk Supplier</span>
        </nav>

        <p class="text-sm font-semibold uppercase tracking-wide text-[#176B4D]">
          Supplier Management
        </p>
        <h1 class="mt-1 text-2xl font-semibold tracking-tight text-[#17201C]">
          Produk Supplier
        </h1>
        <p class="mt-1 max-w-2xl text-sm leading-6 text-[#6B756F]">
          Kelola hubungan produk dengan supplier, harga pembelian, minimum order,
          dan lead time.
        </p>
      </div>

      <button
        type="button"
        class="inline-flex min-h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
        @click="openCreate"
      >
        Tambah Produk Supplier
      </button>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="rounded-lg border border-[#C0392B]/20 bg-[#FEF4F3] p-4 text-sm text-[#C0392B]"
      role="alert"
    >
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <span>{{ error }}</span>
        <button
          type="button"
          class="font-semibold underline underline-offset-2 focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-2"
          @click="loadData"
        >
          Coba lagi
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="rounded-xl border border-[#D6DDD9] bg-white p-4">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div class="grid flex-1 gap-4 md:grid-cols-[minmax(0,1fr)_180px]">
          <label class="block">
            <span class="mb-1.5 block text-sm font-medium text-[#46514B]">
              Cari produk supplier
            </span>
            <input
              v-model="search"
              type="search"
              placeholder="Produk, supplier, atau SKU supplier..."
              class="w-full rounded-lg border border-[#D6DDD9] bg-white px-3 py-2.5 text-sm text-[#17201C] outline-none placeholder:text-[#8A938E] focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/15"
            />
          </label>

          <label class="block">
            <span class="mb-1.5 block text-sm font-medium text-[#46514B]">
              Status
            </span>
            <select
              v-model="statusFilter"
              class="w-full rounded-lg border border-[#D6DDD9] bg-white px-3 py-2.5 text-sm text-[#17201C] outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/15"
            >
              <option value="all">Semua</option>
              <option value="active">Aktif</option>
              <option value="inactive">Nonaktif</option>
            </select>
          </label>

          <label class="block">
            <span class="mb-1.5 block text-sm font-medium text-[#46514B]">
              Supplier
            </span>
            <select
              v-model="supplierFilter"
              class="w-full rounded-lg border border-[#D6DDD9] bg-white px-3 py-2.5 text-sm text-[#17201C] outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/15"
            >
              <option value="">Semua supplier</option>
              <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">
                {{ supplier.name }}
              </option>
            </select>
          </label>
        </div>

        <p class="text-sm text-[#6B756F] lg:pb-2">
          <span class="font-semibold text-[#46514B]">{{ filteredItems.length }}</span>
          data ditemukan
        </p>
      </div>
    </div>

    <!-- Loading -->
    <div
      v-if="loading"
      class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
      aria-busy="true"
      aria-label="Memuat data Produk Supplier"
    >
      <div class="hidden md:block">
        <div class="h-11 border-b border-[#D6DDD9] bg-[#F8FAF9]" />
        <div class="space-y-0">
          <div
            v-for="n in 6"
            :key="n"
            class="h-16 animate-pulse border-b border-[#EEF1EF] bg-white"
          />
        </div>
      </div>

      <div class="space-y-3 p-4 md:hidden">
        <div
          v-for="n in 4"
          :key="n"
          class="h-36 animate-pulse rounded-lg bg-[#F1F4F2]"
        />
      </div>
    </div>

    <!-- Empty -->
    <div
      v-else-if="filteredItems.length === 0"
      class="rounded-xl border border-dashed border-[#D6DDD9] bg-white px-6 py-12 text-center"
    >
      <div class="mx-auto max-w-md">
        <p class="text-sm font-semibold text-[#46514B]">
          Tidak ada Produk Supplier
        </p>
        <p class="mt-1 text-sm leading-6 text-[#6B756F]">
          Belum ada relasi yang sesuai dengan pencarian atau filter yang dipilih.
          Tambahkan relasi produk dan supplier untuk mulai mengelola harga pembelian.
        </p>
        <button
          type="button"
          class="mt-5 inline-flex min-h-10 items-center justify-center rounded-lg bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
          @click="openCreate"
        >
          Tambah Produk Supplier
        </button>
      </div>
    </div>

    <!-- Desktop / tablet table -->
    <div
      v-else
      class="overflow-hidden rounded-xl border border-[#D6DDD9] bg-white"
    >
      <div class="hidden overflow-x-auto md:block">
        <table class="min-w-[980px] w-full text-left text-sm">
          <caption class="sr-only">
            Daftar hubungan produk dengan supplier
          </caption>
          <thead class="border-b border-[#D6DDD9] bg-[#F8FAF9]">
            <tr>
              <th class="px-4 py-3 font-semibold text-[#46514B]">
                Produk
              </th>
              <th class="px-4 py-3 font-semibold text-[#46514B]">
                Supplier
              </th>
              <th class="px-4 py-3 font-semibold text-[#46514B]">
                SKU Supplier
              </th>
              <th class="px-4 py-3 text-right font-semibold text-[#46514B]">
                Harga Beli
              </th>
              <th class="px-4 py-3 text-right font-semibold text-[#46514B]">
                Min. Order
              </th>
              <th class="px-4 py-3 text-right font-semibold text-[#46514B]">
                Lead Time
              </th>
              <th class="px-4 py-3 font-semibold text-[#46514B]">
                Status
              </th>
              <th class="px-4 py-3 text-right font-semibold text-[#46514B]">
                Aksi
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-[#EEF1EF]">
            <tr
              v-for="item in filteredItems"
              :key="item.id"
              class="transition hover:bg-[#F8FAF9]"
            >
              <td class="px-4 py-3.5">
                <div class="font-medium text-[#17201C]">
                  {{ productName(item.productId) }}
                </div>
                <div
                  v-if="item.isPreferred"
                  class="mt-1 text-xs font-medium text-[#176B4D]"
                >
                  Preferred supplier
                </div>
              </td>

              <td class="px-4 py-3.5 text-[#46514B]">
                {{ supplierName(item.supplierId) }}
              </td>

              <td class="px-4 py-3.5 font-mono text-xs text-[#46514B]">
                {{ item.supplierSku }}
              </td>

              <td class="px-4 py-3.5 text-right tabular-nums text-[#17201C]">
                {{ formatRupiah(item.purchasePrice) }}
              </td>

              <td class="px-4 py-3.5 text-right tabular-nums text-[#46514B]">
                {{ item.minimumOrder }}
              </td>

              <td class="px-4 py-3.5 text-right tabular-nums text-[#46514B]">
                {{ item.leadTimeDays }} hari
              </td>

              <td class="px-4 py-3.5">
                <span
                  class="inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium"
                  :class="
                    item.isActive
                      ? 'border-[#176B4D]/20 bg-[#F0F8F5] text-[#176B4D]'
                      : 'border-[#D6DDD9] bg-[#F1F4F2] text-[#46514B]'
                  "
                >
                  {{ item.isActive ? 'Aktif' : 'Nonaktif' }}
                </span>
              </td>

              <td class="px-4 py-3.5">
                <div class="flex justify-end gap-2">
                  <button
                    type="button"
                    class="rounded-lg border border-[#D6DDD9] bg-white px-3 py-1.5 text-xs font-semibold text-[#46514B] hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
                    @click="openEdit(item.id)"
                  >
                    Edit
                  </button>

                  <button
                    v-if="item.isActive"
                    type="button"
                    class="rounded-lg border border-[#C0392B]/20 bg-white px-3 py-1.5 text-xs font-semibold text-[#C0392B] hover:bg-[#FEF4F3] focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-1"
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

      <!-- Mobile operational cards -->
      <div class="divide-y divide-[#EEF1EF] md:hidden">
        <article
          v-for="item in filteredItems"
          :key="item.id"
          class="p-4"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <h2 class="truncate font-semibold text-[#17201C]">
                {{ productName(item.productId) }}
              </h2>
              <p class="mt-1 text-sm text-[#6B756F]">
                {{ supplierName(item.supplierId) }}
              </p>
            </div>

            <span
              class="shrink-0 rounded-full border px-2.5 py-1 text-xs font-medium"
              :class="
                item.isActive
                  ? 'border-[#176B4D]/20 bg-[#F0F8F5] text-[#176B4D]'
                  : 'border-[#D6DDD9] bg-[#F1F4F2] text-[#46514B]'
              "
            >
              {{ item.isActive ? 'Aktif' : 'Nonaktif' }}
            </span>
          </div>

          <div class="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
            <div>
              <p class="text-xs text-[#6B756F]">SKU Supplier</p>
              <p class="mt-0.5 break-all font-mono text-xs text-[#46514B]">
                {{ item.supplierSku }}
              </p>
            </div>

            <div>
              <p class="text-xs text-[#6B756F]">Harga Beli</p>
              <p class="mt-0.5 font-medium tabular-nums text-[#17201C]">
                {{ formatRupiah(item.purchasePrice) }}
              </p>
            </div>

            <div>
              <p class="text-xs text-[#6B756F]">Min. Order</p>
              <p class="mt-0.5 tabular-nums text-[#46514B]">
                {{ item.minimumOrder }}
              </p>
            </div>

            <div>
              <p class="text-xs text-[#6B756F]">Lead Time</p>
              <p class="mt-0.5 tabular-nums text-[#46514B]">
                {{ item.leadTimeDays }} hari
              </p>
            </div>
          </div>

          <div
            v-if="item.isPreferred"
            class="mt-3 text-xs font-medium text-[#176B4D]"
          >
            Preferred supplier
          </div>

          <div class="mt-4 flex gap-2 border-t border-[#EEF1EF] pt-4">
            <button
              type="button"
              class="flex-1 rounded-lg border border-[#D6DDD9] px-3 py-2 text-sm font-semibold text-[#46514B] hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
              @click="openEdit(item.id)"
            >
              Edit
            </button>

            <button
              v-if="item.isActive"
              type="button"
              class="flex-1 rounded-lg border border-[#C0392B]/20 px-3 py-2 text-sm font-semibold text-[#C0392B] hover:bg-[#FEF4F3] focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-1"
              @click="openDeactivate(item)"
            >
              Nonaktifkan
            </button>
          </div>
        </article>
      </div>
    </div>

    <!-- Deactivate confirmation -->
    <div
      v-if="showDeactivateDialog"
      class="fixed inset-0 z-50 flex items-center justify-center bg-[#17201C]/45 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="deactivate-title"
    >
      <div class="w-full max-w-md rounded-xl border border-[#D6DDD9] bg-white p-6 shadow-xl">
        <p class="text-xs font-semibold uppercase tracking-wide text-[#C0392B]">
          Konfirmasi tindakan
        </p>
        <h2
          id="deactivate-title"
          class="mt-1 text-lg font-semibold text-[#17201C]"
        >
          Nonaktifkan Produk Supplier?
        </h2>

        <p class="mt-2 text-sm leading-6 text-[#6B756F]">
          Relasi ini tidak akan dihapus. Data tetap tersimpan dan statusnya
          diubah menjadi nonaktif.
        </p>

        <div class="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            class="rounded-lg border border-[#D6DDD9] px-4 py-2.5 text-sm font-semibold text-[#46514B] hover:bg-[#F8FAF9] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-1"
            :disabled="actionLoading"
            @click="showDeactivateDialog = false"
          >
            Batal
          </button>

          <button
            type="button"
            class="rounded-lg bg-[#C0392B] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#A93226] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-2"
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
