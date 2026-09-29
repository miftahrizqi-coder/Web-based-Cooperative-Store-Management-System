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
  <section class="mx-auto max-w-5xl space-y-6">
    <header>
      <p class="text-sm font-medium text-green-800">
        Procurement
      </p>

      <h1
        class="mt-1 text-2xl font-semibold text-gray-900"
      >
        {{
          isEditMode
            ? 'Edit Purchase Order'
            : 'Tambah Purchase Order'
        }}
      </h1>

      <p class="mt-1 text-sm text-gray-600">
        Isi supplier, produk, harga, dan informasi
        pengiriman.
      </p>
    </header>

    <div
      v-if="isLoading"
      class="space-y-4 rounded-xl border border-gray-200 bg-white p-6"
    >
      <div
        class="h-10 animate-pulse rounded bg-gray-100"
      ></div>

      <div
        class="h-10 animate-pulse rounded bg-gray-100"
      ></div>

      <div
        class="h-40 animate-pulse rounded bg-gray-100"
      ></div>
    </div>

    <div
      v-else
      class="space-y-6"
    >
      <div
        v-if="errorMessage"
        class="rounded-xl border border-red-200 bg-red-50 p-4"
        role="alert"
      >
        <p class="text-sm text-red-700">
          {{ errorMessage }}
        </p>
      </div>

      <form
        class="space-y-6"
        @submit.prevent="handleSubmit"
      >
        <section
          class="rounded-xl border border-gray-200 bg-white p-6"
        >
          <h2
            class="text-lg font-semibold text-gray-900"
          >
            Informasi Purchase Order
          </h2>

          <div
            class="mt-5 grid gap-5 md:grid-cols-2"
          >
            <label>
              <span
                class="mb-1 block text-sm font-medium text-gray-700"
              >
                Supplier
              </span>

              <select
                v-model="supplierId"
                :disabled="isLoadingSuppliers"
                class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
                :aria-invalid="
                  Boolean(supplierError)
                "
              >
                <option value="">
                  Pilih supplier
                </option>

                <option
                  v-for="supplier in activeSuppliers"
                  :key="supplier.id"
                  :value="supplier.id"
                >
                  {{ supplier.name }}
                  —
                  {{ supplier.supplierCode }}
                </option>
              </select>

              <p
                v-if="supplierError"
                class="mt-1 text-sm text-red-600"
              >
                {{ supplierError }}
              </p>
            </label>

            <label>
              <span
                class="mb-1 block text-sm font-medium text-gray-700"
              >
                Target pengiriman
              </span>

              <input
                v-model="expectedDeliveryDate"
                type="date"
                class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
              />
            </label>
          </div>
        </section>

        <section
          class="rounded-xl border border-gray-200 bg-white p-6"
        >
          <h2
            class="text-lg font-semibold text-gray-900"
          >
            Produk
          </h2>

          <div
            class="mt-5 grid gap-4 md:grid-cols-[2fr_1fr_1fr_auto]"
          >
            <label>
              <span
                class="mb-1 block text-sm font-medium text-gray-700"
              >
                Produk
              </span>

              <select
                v-model="selectedSupplierProductId"
                :disabled="
                  !supplierId ||
                  isLoadingSupplierProducts ||
                  isLoadingProducts
                "
                class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
                @change="
                  selectedSupplierProductChanged
                "
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
                  :key="
                    option.supplierProduct.id
                  "
                  :value="
                    option.supplierProduct.id
                  "
                >
                  {{ option.product.name }}
                  —
                  {{ option.product.sku }}
                </option>
              </select>
            </label>

            <label>
              <span
                class="mb-1 block text-sm font-medium text-gray-700"
              >
                Jumlah
              </span>

              <input
                v-model.number="selectedQuantity"
                type="number"
                min="1"
                step="1"
                class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
              />
            </label>

            <label>
              <span
                class="mb-1 block text-sm font-medium text-gray-700"
              >
                Harga beli
              </span>

              <input
                v-model.number="selectedUnitPrice"
                type="number"
                min="0"
                step="1"
                :disabled="
                  !selectedSupplierProductId
                "
                class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700 disabled:bg-gray-100"
              />
            </label>

            <button
              type="button"
              class="self-end rounded-lg border border-green-700 px-4 py-2 text-sm font-medium text-green-800 hover:bg-green-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
              @click="addItem"
            >
              Tambah
            </button>
          </div>

          <p
            v-if="productError"
            class="mt-3 text-sm text-red-600"
            role="alert"
          >
            {{ productError }}
          </p>

          <p
            v-if="itemsError"
            class="mt-3 text-sm text-red-600"
            role="alert"
          >
            {{ itemsError }}
          </p>

          <div
            v-if="items.length === 0"
            class="mt-5 rounded-lg border border-dashed border-gray-300 p-6 text-center"
          >
            <p class="text-sm text-gray-600">
              {{
                supplierId
                  ? 'Belum ada produk dalam purchase order.'
                  : 'Pilih supplier terlebih dahulu untuk memilih produk.'
              }}
            </p>
          </div>

          <div
            v-else
            class="mt-5 overflow-x-auto rounded-lg border border-gray-200"
          >
            <table
              class="min-w-full text-left text-sm"
            >
              <thead
                class="border-b border-gray-200 bg-gray-50"
              >
                <tr>
                  <th
                    class="px-4 py-3 font-medium text-gray-600"
                  >
                    Produk
                  </th>

                  <th
                    class="px-4 py-3 font-medium text-gray-600"
                  >
                    SKU
                  </th>

                  <th
                    class="px-4 py-3 font-medium text-gray-600"
                  >
                    Qty
                  </th>

                  <th
                    class="px-4 py-3 font-medium text-gray-600"
                  >
                    Harga
                  </th>

                  <th
                    class="px-4 py-3 font-medium text-gray-600"
                  >
                    Subtotal
                  </th>

                  <th
                    class="px-4 py-3 font-medium text-gray-600"
                  >
                    Aksi
                  </th>
                </tr>
              </thead>

              <tbody
                class="divide-y divide-gray-100"
              >
                <tr
                  v-for="item in items"
                  :key="item.supplierProductId"
                >
                  <td
                    class="px-4 py-3 font-medium text-gray-900"
                  >
                    {{ item.name }}
                  </td>

                  <td
                    class="px-4 py-3 text-gray-700"
                  >
                    {{ item.sku }}
                  </td>

                  <td
                    class="px-4 py-3 text-gray-700"
                  >
                    {{ item.quantity }}
                  </td>

                  <td
                    class="px-4 py-3 text-gray-700"
                  >
                    {{ formatCurrency(item.unitPrice) }}
                  </td>

                  <td
                    class="px-4 py-3 font-medium text-gray-900"
                  >
                    {{
                      formatCurrency(
                        item.quantity *
                          item.unitPrice,
                      )
                    }}
                  </td>

                  <td class="px-4 py-3">
                    <button
                      type="button"
                      class="rounded-md border border-red-300 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
                      @click="
                        removeItem(
                          item.supplierProductId,
                        )
                      "
                    >
                      Hapus
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section
          class="rounded-xl border border-gray-200 bg-white p-6"
        >
          <h2
            class="text-lg font-semibold text-gray-900"
          >
            Ringkasan biaya
          </h2>

          <div
            class="mt-5 grid gap-5 md:grid-cols-3"
          >
            <label>
              <span
                class="mb-1 block text-sm font-medium text-gray-700"
              >
                Diskon
              </span>

              <input
                v-model.number="discount"
                type="number"
                min="0"
                step="1"
                class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
              />
            </label>

            <label>
              <span
                class="mb-1 block text-sm font-medium text-gray-700"
              >
                Pajak
              </span>

              <input
                v-model.number="tax"
                type="number"
                min="0"
                step="1"
                class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
              />
            </label>

            <label>
              <span
                class="mb-1 block text-sm font-medium text-gray-700"
              >
                Biaya pengiriman
              </span>

              <input
                v-model.number="shippingCost"
                type="number"
                min="0"
                step="1"
                class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-700 focus:ring-2 focus:ring-green-700"
              />
            </label>
          </div>

          <div
            class="mt-6 border-t border-gray-200 pt-5"
          >
            <dl
              class="ml-auto max-w-sm space-y-3 text-sm"
            >
              <div class="flex justify-between">
                <dt class="text-gray-600">
                  Subtotal
                </dt>

                <dd
                  class="font-medium text-gray-900"
                >
                  {{ formatCurrency(subtotal) }}
                </dd>
              </div>

              <div class="flex justify-between">
                <dt class="text-gray-600">
                  Diskon
                </dt>

                <dd
                  class="font-medium text-gray-900"
                >
                  - {{ formatCurrency(discount) }}
                </dd>
              </div>

              <div class="flex justify-between">
                <dt class="text-gray-600">
                  Pajak
                </dt>

                <dd
                  class="font-medium text-gray-900"
                >
                  {{ formatCurrency(tax) }}
                </dd>
              </div>

              <div class="flex justify-between">
                <dt class="text-gray-600">
                  Pengiriman
                </dt>

                <dd
                  class="font-medium text-gray-900"
                >
                  {{ formatCurrency(shippingCost) }}
                </dd>
              </div>

              <div
                class="flex justify-between border-t border-gray-200 pt-3 text-base"
              >
                <dt
                  class="font-semibold text-gray-900"
                >
                  Grand Total
                </dt>

                <dd
                  class="font-semibold text-gray-900"
                >
                  {{ formatCurrency(grandTotal) }}
                </dd>
              </div>
            </dl>
          </div>
        </section>

        <div
          class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end"
        >
          <button
            type="button"
            class="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
            @click="
              router.push('/purchase-orders')
            "
          >
            Batal
          </button>

          <button
            type="submit"
            :disabled="isSaving"
            class="rounded-lg bg-green-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-900 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
          >
            {{
              isSaving
                ? 'Menyimpan...'
                : 'Simpan sebagai Draft'
            }}
          </button>
        </div>
      </form>
    </div>
  </section>
</template>