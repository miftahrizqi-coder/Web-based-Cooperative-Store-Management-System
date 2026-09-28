<script setup lang="ts">
defineProps<{
  label: string
  value: string
  loading?: boolean
}>()
</script>

<template>
  <article class="rounded-xl border bg-white p-5">
    <template v-if="loading">
      <div
        class="h-4 w-28 animate-pulse rounded bg-gray-200"
        aria-hidden="true"
      />

      <div
        class="mt-3 h-8 w-20 animate-pulse rounded bg-gray-200"
        aria-hidden="true"
      />

      <span class="sr-only">
        Memuat {{ label }}
      </span>
    </template>

    <template v-else>
      <p class="text-sm text-gray-500">
        {{ label }}
      </p>

      <p class="mt-2 text-2xl font-semibold">
        {{ value }}
      </p>
    </template>
  </article>
</template>