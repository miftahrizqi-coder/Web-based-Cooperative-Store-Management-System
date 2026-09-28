<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'
import { getNavigationItems } from '../router/navigation'

const { currentUser } = useAuth()
const router = useRouter()
const { clearAuth } = useAuth()

const visibleNavigationItems = computed(() => {
  if (!currentUser.value) {
    return []
  }

  return getNavigationItems(currentUser.value.role)
})

const isSidebarOpen = ref(false)

function handleLogout() {
  clearAuth()
  router.push('/login')
}
</script>
<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Mobile overlay -->
    <div
      v-if="isSidebarOpen"
      class="fixed inset-0 z-40 bg-black/30 md:hidden"
      @click="isSidebarOpen = false"
    />

    <!-- Sidebar -->
    <aside
      class="fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r bg-white transition-transform duration-200 md:translate-x-0"
      :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="border-b px-6 py-4">
        <h1 class="text-lg font-semibold">Koprom</h1>
        <p class="text-sm text-gray-500">Koperasi Romantis</p>
      </div>

      <nav class="flex-1 p-4">
        <RouterLink
          v-for="item in visibleNavigationItems"
          :key="item.to"
          :to="item.to"
          class="block rounded-lg px-3 py-2 text-sm font-medium hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-400"
          active-class="bg-gray-100"
          @click="isSidebarOpen = false"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <!-- Logout -->
      <div class="border-t p-4">
        <button
          type="button"
          class="w-full rounded-lg px-3 py-2 text-left text-sm font-medium hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-400"
          @click="handleLogout"
        >
          Logout
        </button>
      </div>
    </aside>

    <!-- Main area -->
    <main class="min-h-screen md:ml-64">
      <header class="border-b bg-white px-4 py-4 md:px-6">
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 md:hidden"
            aria-label="Buka menu navigasi"
            @click="isSidebarOpen = true"
          >
            Menu
          </button>

          <h2 class="text-lg font-semibold">Dashboard</h2>
        </div>
      </header>

      <section class="p-4 md:p-6">
        <slot />
      </section>
    </main>
  </div>
</template>