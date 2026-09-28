<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppLayout from './layouts/AppLayout.vue'
import { useAuth } from './stores/auth'

const route = useRoute()
const { restoreSession } = useAuth()

onMounted(async () => {
  await restoreSession()
})
</script>

<template>
  <AppLayout v-if="route.path !== '/login'">
    <RouterView />
  </AppLayout>

  <RouterView v-else />
</template>