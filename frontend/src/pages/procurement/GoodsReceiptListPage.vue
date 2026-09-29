<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getGoodsReceipts } from '../../api/procurement'
import type { GoodsReceipt } from '../../types/procurement'
import { useAuth } from '../../stores/auth'

const router = useRouter()
const { token } = useAuth()

const goodsReceipts = ref<GoodsReceipt[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

function formatDate(value: string) {
  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

async function loadGoodsReceipts() {
  if (!token.value) {
    errorMessage.value =
      'Sesi login tidak ditemukan. Silakan login kembali.'
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    goodsReceipts.value = await getGoodsReceipts(token.value)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : 'Gagal mengambil daftar penerimaan barang.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadGoodsReceipts)
</script>

<template>
  <section class="space-y-6">
    <div
      class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">
          Penerimaan Barang
        </h1>

        <p class="mt-1 text-sm text-gray-600">
          Daftar penerimaan barang dari Purchase Order.
        </p>
      </div>

      <button
        type="button"
        class="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-700 focus:ring-offset-2"
        @click="loadGoodsReceipts"
      >
        Refresh
      </button>
    </div>

    <div
      v-if="isLoading"
      class="space-y-3 rounded-xl border border-gray-200 bg-white p-6"
    >
      <div class="h-10 animate-pulse rounded bg-gray-100" />
      <div class="h-10 animate-pulse rounded bg-gray-100" />
      <div class="h-10 animate-pulse rounded bg-gray-100" />
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-red-200 bg-red-50 p-6"
      role="alert"
    >
      <h2 class="font-semibold text-red-800">
        Penerimaan barang gagal dimuat
      </h2>

      <p class="mt-1 text-sm text-red-700">
        {{ errorMessage }}
      </p>

      <button
        type="button"
        class="mt-4 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
        @click="loadGoodsReceipts"
      >
        Coba lagi
      </button>
    </div>

    <div
      v-else-if="goodsReceipts.length === 0"
      class="rounded-xl border border-dashed border-gray-300 bg-white p-10 text-center"
    >
      <h2 class="font-semibold text-gray-900">
        Belum ada penerimaan barang
      </h2>

      <p class="mt-1 text-sm text-gray-600">
        Goods Receipt akan muncul setelah penerimaan barang dibuat dari
        Purchase Order.
      </p>
    </div>

    <div
      v-else
      class="overflow-x-auto rounded-xl border border-gray-200 bg-white"
    >
      <table class="min-w-full text-left text-sm">
        <thead class="border-b border-gray-200 bg-gray-50">
          <tr>
            <th class="px-4 py-3 font-medium text-gray-600">
              Nomor Receipt
            </th>

            <th class="px-4 py-3 font-medium text-gray-600">
              Purchase Order
            </th>

            <th class="px-4 py-3 font-medium text-gray-600">
              Supplier
            </th>

            <th class="px-4 py-3 font-medium text-gray-600">
              Diterima
            </th>

            <th class="px-4 py-3 font-medium text-gray-600">
              Jumlah Item
            </th>

            <th class="px-4 py-3 font-medium text-gray-600">
              Aksi
            </th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          <tr
            v-for="receipt in goodsReceipts"
            :key="receipt.id"
            class="hover:bg-gray-50"
          >
            <td class="px-4 py-3 font-medium text-gray-900">
              {{ receipt.receiptNumber }}
            </td>

            <td class="px-4 py-3 text-gray-700">
              {{ receipt.purchaseOrderId }}
            </td>

            <td class="px-4 py-3 text-gray-700">
              {{ receipt.supplierId }}
            </td>

            <td class="px-4 py-3 text-gray-700">
              {{ formatDate(receipt.receivedAt) }}
            </td>

            <td class="px-4 py-3 text-gray-700">
              {{ receipt.items.length }}
            </td>

            <td class="px-4 py-3">
              <button
                type="button"
                class="font-medium text-green-800 hover:underline focus:outline-none focus:ring-2 focus:ring-green-700"
                @click="router.push(`/goods-receipts/${receipt.id}`)"
              >
                Detail
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>