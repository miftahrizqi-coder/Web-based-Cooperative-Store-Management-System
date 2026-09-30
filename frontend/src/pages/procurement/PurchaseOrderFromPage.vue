<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  createPurchaseOrder,
  getPurchaseOrder,
  updatePurchaseOrder,
} from '../../api/procurement'
import { getProducts } from '../../api/products'
import { getSuppliers } from '../../api/suppliers'
import { getSupplierProducts } from '../../api/supplierProducts'

import type { Product } from '../../types/product'
import type { Supplier } from '../../types/supplier'
import type { SupplierProduct } from '../../types/supplierProduct'
import type {
  PurchaseOrderPayload,
} from '../../types/procurement'

import { useAuth } from '../../stores/auth'

interface FormItem {
  supplierProductId: string
  productId: string
  sku: string
  name: string
  quantity: number
  unitPrice: number
}

const route = useRoute()
const router = useRouter()
const { token } = useAuth()

const isEditMode = computed(() => Boolean(route.params.id))

const supplierId = ref('')
const expectedDeliveryDate = ref('')

const discount = ref(0)
const tax = ref(0)
const shippingCost = ref(0)

const suppliers = ref<Supplier[]>([])
const products = ref<Product[]>([])
const supplierProducts = ref<SupplierProduct[]>([])

const items = ref<FormItem[]>([])

const selectedSupplierProductId = ref('')
const selectedQuantity = ref(1)
const selectedUnitPrice = ref(0)

const isLoading = ref(false)
const isLoadingSuppliers = ref(false)
const isLoadingProducts = ref(false)
const isLoadingSupplierProducts = ref(false)
const isSaving = ref(false)

const errorMessage = ref('')
const supplierError = ref('')
const productError = ref('')
const itemsError = ref('')

const activeSuppliers = computed(() =>
  suppliers.value.filter(
    (supplier) => supplier.status === 'ACTIVE',
  ),
)

const activeSupplierProducts = computed(() =>
  supplierProducts.value.filter(
    (supplierProduct) =>
      supplierProduct.isActive &&
      supplierProduct.supplierId === supplierId.value,
  ),
)

const selectedSupplierProduct = computed(() =>
  supplierProducts.value.find(
    (item) => item.id === selectedSupplierProductId.value,
  ),
)

const selectedProduct = computed(() => {
  const supplierProduct = selectedSupplierProduct.value

  if (!supplierProduct) {
    return undefined
  }

  return products.value.find(
    (product) => product.id === supplierProduct.productId,
  )
})

const productOptions = computed(() =>
  activeSupplierProducts.value
    .map((supplierProduct) => {
      const product = products.value.find(
        (item) => item.id === supplierProduct.productId,
      )

      if (!product) {
        return null
      }

      return {
        supplierProduct,
        product,
      }
    })
    .filter(
      (
        item,
      ): item is {
        supplierProduct: SupplierProduct
        product: Product
      } => Boolean(item),
    ),
)

const subtotal = computed(() =>
  items.value.reduce(
    (total, item) =>
      total + item.quantity * item.unitPrice,
    0,
  ),
)

const grandTotal = computed(() =>
  Math.max(
    0,
    subtotal.value -
      discount.value +
      tax.value +
      shippingCost.value,
  ),
)

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value)
}

function selectedSupplierProductChanged() {
  const supplierProduct = selectedSupplierProduct.value

  if (!supplierProduct) {
    selectedUnitPrice.value = 0
    return
  }

  selectedUnitPrice.value =
    supplierProduct.purchasePrice
}

function resetProductSelection() {
  selectedSupplierProductId.value = ''
  selectedQuantity.value = 1
  selectedUnitPrice.value = 0
}

async function loadSuppliers() {
  if (!token.value) {
    return
  }

  isLoadingSuppliers.value = true
  supplierError.value = ''

  try {
    suppliers.value = await getSuppliers(token.value)
  } catch (error) {
    supplierError.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil daftar supplier.'
  } finally {
    isLoadingSuppliers.value = false
  }
}

async function loadProducts() {
  if (!token.value) {
    return
  }

  isLoadingProducts.value = true

  try {
    products.value = await getProducts(token.value)
  } catch (error) {
    productError.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil daftar produk.'
  } finally {
    isLoadingProducts.value = false
  }
}

async function loadSupplierProducts() {
  if (!token.value || !supplierId.value) {
    supplierProducts.value = []
    resetProductSelection()
    return
  }

  isLoadingSupplierProducts.value = true
  productError.value = ''

  try {
    supplierProducts.value =
      await getSupplierProducts({
        supplierId: supplierId.value,
        isActive: true,
      })

    resetProductSelection()
  } catch (error) {
    supplierProducts.value = []
    resetProductSelection()

    productError.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil produk supplier.'
  } finally {
    isLoadingSupplierProducts.value = false
  }
}

function addItem() {
  productError.value = ''

  if (!supplierId.value) {
    productError.value =
      'Supplier wajib dipilih terlebih dahulu.'
    return
  }

  if (!selectedSupplierProductId.value) {
    productError.value =
      'Produk wajib dipilih.'
    return
  }

  if (selectedQuantity.value <= 0) {
    productError.value =
      'Jumlah produk harus lebih dari 0.'
    return
  }

  if (selectedUnitPrice.value < 0) {
    productError.value =
      'Harga beli tidak boleh negatif.'
    return
  }

  const supplierProduct =
    selectedSupplierProduct.value

  const product = selectedProduct.value

  if (!supplierProduct || !product) {
    productError.value =
      'Data produk supplier tidak ditemukan.'
    return
  }

  const existingItem = items.value.find(
    (item) =>
      item.supplierProductId ===
      supplierProduct.id,
  )

  if (existingItem) {
    existingItem.quantity +=
      selectedQuantity.value
    existingItem.unitPrice =
      selectedUnitPrice.value
  } else {
    items.value.push({
      supplierProductId: supplierProduct.id,
      productId: product.id,
      sku: product.sku,
      name: product.name,
      quantity: selectedQuantity.value,
      unitPrice: selectedUnitPrice.value,
    })
  }

  resetProductSelection()
}

function removeItem(supplierProductId: string) {
  items.value = items.value.filter(
    (item) =>
      item.supplierProductId !==
      supplierProductId,
  )
}

function validateForm() {
  supplierError.value = ''
  itemsError.value = ''

  if (!supplierId.value) {
    supplierError.value =
      'Supplier wajib dipilih.'
  }

  if (items.value.length === 0) {
    itemsError.value =
      'Minimal satu produk harus ditambahkan.'
  }

  if (discount.value < 0) {
    errorMessage.value =
      'Diskon tidak boleh negatif.'
    return false
  }

  if (tax.value < 0) {
    errorMessage.value =
      'Pajak tidak boleh negatif.'
    return false
  }

  if (shippingCost.value < 0) {
    errorMessage.value =
      'Biaya pengiriman tidak boleh negatif.'
    return false
  }

  return (
    !supplierError.value &&
    !itemsError.value
  )
}

async function loadPurchaseOrder() {
  if (!token.value || !route.params.id) {
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const purchaseOrder =
      await getPurchaseOrder(
        token.value,
        String(route.params.id),
      )

    if (purchaseOrder.status !== 'DRAFT') {
      errorMessage.value =
        'Purchase order yang sudah dikirim tidak dapat diedit.'
      return
    }

    supplierId.value =
      purchaseOrder.supplierId

    expectedDeliveryDate.value =
      purchaseOrder.expectedDeliveryDate
        ? purchaseOrder.expectedDeliveryDate.slice(
            0,
            10,
          )
        : ''

    discount.value =
      purchaseOrder.discount

    tax.value = purchaseOrder.tax

    shippingCost.value =
      purchaseOrder.shippingCost

    items.value =
      purchaseOrder.items.map((item) => ({
        supplierProductId:
          item.supplierProductId,
        productId: item.productId,
        sku: item.sku,
        name: item.name,
        quantity: item.quantity,
        unitPrice: item.unitPrice,
      }))
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil purchase order.'
  } finally {
    isLoading.value = false
  }
}

async function handleSubmit() {
  errorMessage.value = ''

  if (!validateForm()) {
    return
  }

  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    return
  }

  const payload: PurchaseOrderPayload = {
    supplierId: supplierId.value,

    items: items.value.map((item) => ({
      supplierProductId:
        item.supplierProductId,
      productId: item.productId,
      sku: item.sku,
      name: item.name,
      quantity: item.quantity,
      unitPrice: item.unitPrice,
    })),

    discount: discount.value,
    tax: tax.value,
    shippingCost: shippingCost.value,

    expectedDeliveryDate:
      expectedDeliveryDate.value
        ? `${expectedDeliveryDate.value}T00:00:00`
        : null,
  }

  isSaving.value = true

  try {
    if (isEditMode.value) {
      await updatePurchaseOrder(
        token.value,
        String(route.params.id),
        payload,
      )
    } else {
      await createPurchaseOrder(
        token.value,
        payload,
      )
    }

    await router.push('/purchase-orders')
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal menyimpan purchase order.'
  } finally {
    isSaving.value = false
  }
}

watch(
  supplierId,
  async (newSupplierId, oldSupplierId) => {
    if (newSupplierId === oldSupplierId) {
      return
    }

    items.value = []
    await loadSupplierProducts()
  },
)

onMounted(async () => {
  await Promise.all([
    loadSuppliers(),
    loadProducts(),
  ])

  if (isEditMode.value) {
    await loadPurchaseOrder()
  }

  if (supplierId.value) {
    await loadSupplierProducts()
  }
})
</script>

<template>
  <section class="min-h-full bg-[#F8FAF9]">
    <div class="mx-auto max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8">
      <!-- Breadcrumb -->
      <nav class="mb-5" aria-label="Breadcrumb">
        <ol class="flex flex-wrap items-center gap-2 text-xs text-[#6B756F]">
          <li>
            <button
              type="button"
              class="rounded px-1 py-0.5 hover:text-[#176B4D] focus:outline-none focus:ring-2 focus:ring-[#176B4D]"
              @click="router.push('/purchase-orders')"
            >
              Procurement
            </button>
          </li>
          <li aria-hidden="true">/</li>
          <li class="text-[#46514B]">
            {{ isEditMode ? 'Edit Purchase Order' : 'Purchase Order Baru' }}
          </li>
        </ol>
      </nav>

      <!-- Page header -->
      <header class="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.08em] text-[#176B4D]">
            Procurement
          </p>
          <h1 class="mt-1 text-[28px] font-semibold leading-9 text-[#17201C]">
            {{ isEditMode ? 'Edit Purchase Order' : 'Buat Purchase Order' }}
          </h1>
          <p class="mt-1 max-w-2xl text-sm leading-5 text-[#6B756F]">
            Susun supplier, item yang dipesan, target pengiriman, dan rincian biaya
            sebelum purchase order disimpan sebagai draft.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span
            class="inline-flex items-center rounded-full border border-[#D6DDD9] bg-white px-3 py-1.5 text-xs font-medium text-[#46514B]"
          >
            Status
            <span class="mx-1.5 text-[#D6DDD9]">•</span>
            Draft
          </span>
        </div>
      </header>

      <!-- Global loading -->
      <div
        v-if="isLoading"
        class="rounded-lg border border-[#D6DDD9] bg-white p-6"
        aria-busy="true"
        aria-label="Memuat purchase order"
      >
        <div class="space-y-5 animate-pulse">
          <div class="h-5 w-48 rounded bg-[#F1F4F2]"></div>
          <div class="grid gap-4 md:grid-cols-2">
            <div class="h-10 rounded bg-[#F1F4F2]"></div>
            <div class="h-10 rounded bg-[#F1F4F2]"></div>
          </div>
          <div class="h-40 rounded bg-[#F1F4F2]"></div>
        </div>
      </div>

      <div v-else class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <form class="min-w-0 space-y-6" @submit.prevent="handleSubmit">
          <div
            v-if="errorMessage"
            class="rounded-lg border border-[#C0392B]/25 bg-[#FEF4F3] p-4"
            role="alert"
          >
            <p class="text-sm font-medium text-[#C0392B]">
              {{ errorMessage }}
            </p>
          </div>

          <!-- Main information -->
          <section class="rounded-lg border border-[#D6DDD9] bg-white">
            <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
              <h2 class="text-[18px] font-semibold leading-6 text-[#17201C]">
                Informasi purchase order
              </h2>
              <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                Tentukan supplier dan target pengiriman untuk PO ini.
              </p>
            </div>

            <div class="grid gap-5 p-5 sm:p-6 md:grid-cols-2">
              <label>
                <span class="mb-1.5 block text-sm font-medium text-[#46514B]">
                  Supplier <span class="text-[#C0392B]" aria-hidden="true">*</span>
                </span>
                <select
                  v-model="supplierId"
                  :disabled="isLoadingSuppliers"
                  class="w-full rounded-md border border-[#D6DDD9] bg-white px-3 py-2.5 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20 disabled:cursor-not-allowed disabled:bg-[#F1F4F2]"
                  :aria-invalid="Boolean(supplierError)"
                >
                  <option value="">Pilih supplier</option>
                  <option
                    v-for="supplier in activeSuppliers"
                    :key="supplier.id"
                    :value="supplier.id"
                  >
                    {{ supplier.name }} — {{ supplier.supplierCode }}
                  </option>
                </select>
                <p v-if="supplierError" class="mt-1.5 text-xs text-[#C0392B]" role="alert">
                  {{ supplierError }}
                </p>
              </label>

              <label>
                <span class="mb-1.5 block text-sm font-medium text-[#46514B]">
                  Target pengiriman
                </span>
                <input
                  v-model="expectedDeliveryDate"
                  type="date"
                  class="w-full rounded-md border border-[#D6DDD9] bg-white px-3 py-2.5 text-sm text-[#17201C] outline-none transition focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                />
                <span class="mt-1.5 block text-xs text-[#6B756F]">
                  Opsional. Digunakan sebagai target penerimaan dari supplier.
                </span>
              </label>
            </div>
          </section>

          <!-- Items -->
          <section class="rounded-lg border border-[#D6DDD9] bg-white">
            <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
              <div class="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h2 class="text-[18px] font-semibold leading-6 text-[#17201C]">
                    Item purchase order
                  </h2>
                  <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                    Tambahkan produk dari katalog supplier yang aktif.
                  </p>
                </div>
                <span class="text-xs font-medium text-[#6B756F]">
                  {{ items.length }} item
                </span>
              </div>
            </div>

            <div class="p-5 sm:p-6">
              <div class="rounded-md border border-[#E6EBE8] bg-[#F8FAF9] p-4">
                <div class="grid gap-4 md:grid-cols-[minmax(0,2fr)_120px_160px_auto] md:items-end">
                  <label>
                    <span class="mb-1.5 block text-sm font-medium text-[#46514B]">
                      Produk
                    </span>
                    <select
                      v-model="selectedSupplierProductId"
                      :disabled="!supplierId || isLoadingSupplierProducts || isLoadingProducts"
                      class="w-full rounded-md border border-[#D6DDD9] bg-white px-3 py-2.5 text-sm text-[#17201C] outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20 disabled:cursor-not-allowed disabled:bg-[#F1F4F2]"
                      @change="selectedSupplierProductChanged"
                    >
                      <option value="">
                        {{
                          !supplierId
                            ? 'Pilih supplier terlebih dahulu'
                            : isLoadingSupplierProducts
                              ? 'Memuat produk...'
                              : 'Pilih produk'
                        }}
                      </option>
                      <option
                        v-for="option in productOptions"
                        :key="option.supplierProduct.id"
                        :value="option.supplierProduct.id"
                      >
                        {{ option.product.name }} — {{ option.product.sku }}
                      </option>
                    </select>
                  </label>

                  <label>
                    <span class="mb-1.5 block text-sm font-medium text-[#46514B]">
                      Jumlah
                    </span>
                    <input
                      v-model.number="selectedQuantity"
                      type="number"
                      min="1"
                      step="1"
                      class="w-full rounded-md border border-[#D6DDD9] bg-white px-3 py-2.5 text-right text-sm text-[#17201C] outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                    />
                  </label>

                  <label>
                    <span class="mb-1.5 block text-sm font-medium text-[#46514B]">
                      Harga beli
                    </span>
                    <input
                      v-model.number="selectedUnitPrice"
                      type="number"
                      min="0"
                      step="1"
                      :disabled="!selectedSupplierProductId"
                      class="w-full rounded-md border border-[#D6DDD9] bg-white px-3 py-2.5 text-right text-sm text-[#17201C] outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20 disabled:cursor-not-allowed disabled:bg-[#F1F4F2]"
                    />
                  </label>

                  <button
                    type="button"
                    class="inline-flex min-h-10 items-center justify-center rounded-md bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="!supplierId || isLoadingSupplierProducts"
                    @click="addItem"
                  >
                    Tambah item
                  </button>
                </div>

                <p v-if="productError" class="mt-3 text-sm text-[#C0392B]" role="alert">
                  {{ productError }}
                </p>
              </div>

              <p v-if="itemsError" class="mt-3 text-sm text-[#C0392B]" role="alert">
                {{ itemsError }}
              </p>

              <div
                v-if="items.length === 0"
                class="mt-5 rounded-md border border-dashed border-[#D6DDD9] bg-white px-5 py-8 text-center"
              >
                <p class="text-sm font-medium text-[#46514B]">
                  Belum ada item purchase order
                </p>
                <p class="mt-1 text-xs text-[#6B756F]">
                  {{
                    supplierId
                      ? 'Pilih produk, isi jumlah dan harga beli, lalu tekan Tambah item.'
                      : 'Pilih supplier terlebih dahulu untuk memuat produk yang tersedia.'
                  }}
                </p>
              </div>

              <div
                v-else
                class="mt-5 overflow-x-auto rounded-md border border-[#D6DDD9]"
              >
                <table class="min-w-full text-sm">
                  <caption class="sr-only">Daftar item purchase order</caption>
                  <thead class="border-b border-[#D6DDD9] bg-[#F1F4F2]">
                    <tr>
                      <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                        Produk
                      </th>
                      <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                        SKU
                      </th>
                      <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                        Qty
                      </th>
                      <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                        Harga
                      </th>
                      <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                        Subtotal
                      </th>
                      <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[#46514B]">
                        Aksi
                      </th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[#E6EBE8]">
                    <tr v-for="item in items" :key="item.supplierProductId" class="hover:bg-[#F8FAF9]">
                      <td class="px-4 py-3">
                        <div class="font-medium text-[#17201C]">{{ item.name }}</div>
                      </td>
                      <td class="px-4 py-3 font-mono text-xs text-[#6B756F]">
                        {{ item.sku }}
                      </td>
                      <td class="px-4 py-3 text-right tabular-nums text-[#46514B]">
                        {{ item.quantity }}
                      </td>
                      <td class="px-4 py-3 text-right tabular-nums text-[#46514B]">
                        {{ formatCurrency(item.unitPrice) }}
                      </td>
                      <td class="px-4 py-3 text-right font-semibold tabular-nums text-[#17201C]">
                        {{ formatCurrency(item.quantity * item.unitPrice) }}
                      </td>
                      <td class="px-4 py-3 text-right">
                        <button
                          type="button"
                          class="rounded-md px-2.5 py-1.5 text-xs font-semibold text-[#C0392B] hover:bg-[#FEF4F3] focus:outline-none focus:ring-2 focus:ring-[#C0392B] focus:ring-offset-1"
                          @click="removeItem(item.supplierProductId)"
                        >
                          Hapus
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <!-- Cost adjustments -->
          <section class="rounded-lg border border-[#D6DDD9] bg-white">
            <div class="border-b border-[#E6EBE8] px-5 py-4 sm:px-6">
              <h2 class="text-[18px] font-semibold leading-6 text-[#17201C]">
                Penyesuaian biaya
              </h2>
              <p class="mt-1 text-[13px] leading-[18px] text-[#6B756F]">
                Masukkan diskon, pajak, dan biaya pengiriman jika ada.
              </p>
            </div>

            <div class="grid gap-5 p-5 sm:p-6 md:grid-cols-3">
              <label>
                <span class="mb-1.5 block text-sm font-medium text-[#46514B]">Diskon</span>
                <input
                  v-model.number="discount"
                  type="number"
                  min="0"
                  step="1"
                  class="w-full rounded-md border border-[#D6DDD9] px-3 py-2.5 text-right text-sm tabular-nums outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                />
              </label>
              <label>
                <span class="mb-1.5 block text-sm font-medium text-[#46514B]">Pajak</span>
                <input
                  v-model.number="tax"
                  type="number"
                  min="0"
                  step="1"
                  class="w-full rounded-md border border-[#D6DDD9] px-3 py-2.5 text-right text-sm tabular-nums outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                />
              </label>
              <label>
                <span class="mb-1.5 block text-sm font-medium text-[#46514B]">Biaya pengiriman</span>
                <input
                  v-model.number="shippingCost"
                  type="number"
                  min="0"
                  step="1"
                  class="w-full rounded-md border border-[#D6DDD9] px-3 py-2.5 text-right text-sm tabular-nums outline-none focus:border-[#176B4D] focus:ring-2 focus:ring-[#176B4D]/20"
                />
              </label>
            </div>
          </section>

          <!-- Mobile actions -->
          <div class="flex flex-col gap-3 pb-2 sm:flex-row sm:justify-end lg:hidden">
            <button
              type="button"
              class="rounded-md border border-[#D6DDD9] bg-white px-4 py-2.5 text-sm font-semibold text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
              @click="router.push('/purchase-orders')"
            >
              Batal
            </button>
            <button
              type="submit"
              :disabled="isSaving"
              class="rounded-md bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {{ isSaving ? 'Menyimpan...' : 'Simpan sebagai Draft' }}
            </button>
          </div>
        </form>

        <!-- Sticky context / summary -->
        <aside class="lg:sticky lg:top-6 lg:self-start">
          <section class="rounded-lg border border-[#D6DDD9] bg-white">
            <div class="border-b border-[#E6EBE8] px-5 py-4">
              <h2 class="text-base font-semibold text-[#17201C]">
                Ringkasan PO
              </h2>
              <p class="mt-1 text-xs text-[#6B756F]">
                Periksa dampak finansial sebelum menyimpan.
              </p>
            </div>

            <dl class="space-y-3 px-5 py-5 text-sm">
              <div class="flex items-start justify-between gap-4">
                <dt class="text-[#6B756F]">Supplier</dt>
                <dd class="max-w-[190px] text-right font-medium text-[#17201C]">
                  {{
                    suppliers.find((supplier) => supplier.id === supplierId)?.name ||
                    'Belum dipilih'
                  }}
                </dd>
              </div>

              <div class="flex items-center justify-between gap-4">
                <dt class="text-[#6B756F]">Total item</dt>
                <dd class="font-semibold tabular-nums text-[#17201C]">{{ items.length }}</dd>
              </div>

              <div class="flex items-center justify-between gap-4">
                <dt class="text-[#6B756F]">Total quantity</dt>
                <dd class="font-semibold tabular-nums text-[#17201C]">
                  {{ items.reduce((sum, item) => sum + item.quantity, 0) }}
                </dd>
              </div>

              <div class="border-t border-[#E6EBE8] pt-3">
                <div class="flex items-center justify-between gap-4">
                  <dt class="text-[#6B756F]">Subtotal</dt>
                  <dd class="font-medium tabular-nums text-[#17201C]">
                    {{ formatCurrency(subtotal) }}
                  </dd>
                </div>
                <div class="mt-2 flex items-center justify-between gap-4">
                  <dt class="text-[#6B756F]">Diskon</dt>
                  <dd class="font-medium tabular-nums text-[#46514B]">
                    − {{ formatCurrency(discount) }}
                  </dd>
                </div>
                <div class="mt-2 flex items-center justify-between gap-4">
                  <dt class="text-[#6B756F]">Pajak</dt>
                  <dd class="font-medium tabular-nums text-[#46514B]">
                    {{ formatCurrency(tax) }}
                  </dd>
                </div>
                <div class="mt-2 flex items-center justify-between gap-4">
                  <dt class="text-[#6B756F]">Pengiriman</dt>
                  <dd class="font-medium tabular-nums text-[#46514B]">
                    {{ formatCurrency(shippingCost) }}
                  </dd>
                </div>
              </div>

              <div class="mt-4 border-t border-[#D6DDD9] pt-4">
                <div class="flex items-end justify-between gap-4">
                  <dt class="font-semibold text-[#17201C]">Grand Total</dt>
                  <dd class="text-xl font-bold tabular-nums text-[#12372A]">
                    {{ formatCurrency(grandTotal) }}
                  </dd>
                </div>
              </div>
            </dl>

            <div class="border-t border-[#E6EBE8] bg-[#F8FAF9] px-5 py-4">
              <p class="text-xs font-medium text-[#46514B]">
                Draft belum masuk lifecycle approval sampai disubmit pada tahap berikutnya.
              </p>
            </div>
          </section>

          <div class="mt-4 hidden flex-col gap-3 lg:flex">
            <button
              type="button"
              class="rounded-md border border-[#D6DDD9] bg-white px-4 py-2.5 text-sm font-semibold text-[#46514B] hover:bg-[#F1F4F2] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2"
              @click="router.push('/purchase-orders')"
            >
              Batal
            </button>
            <button
              type="submit"
              form=""
              :disabled="isSaving"
              class="rounded-md bg-[#176B4D] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#1F805D] focus:outline-none focus:ring-2 focus:ring-[#176B4D] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              @click="handleSubmit"
            >
              {{ isSaving ? 'Menyimpan...' : 'Simpan sebagai Draft' }}
            </button>
          </div>
        </aside>
      </div>
    </div>
  </section>
</template>
