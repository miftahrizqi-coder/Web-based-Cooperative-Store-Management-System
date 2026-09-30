<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'
import { getNavigationItems } from '../router/navigation'

const { currentUser, clearAuth } = useAuth()
const router = useRouter()

const isSidebarOpen = ref(false)

const visibleNavigationItems = computed(() => {
  if (!currentUser.value) {
    return []
  }

  return getNavigationItems(currentUser.value.role)
})

/**
 * DESIGN.md §4 mendefinisikan navigation berdasarkan domain.
 * Pengelompokan dilakukan dari route agar tidak mengubah
 * contract getNavigationItems() yang sudah digunakan aplikasi.
 */
const navigationGroups = [
  {
    label: 'Overview',
    matches: (path: string) =>
      path === '/' ||
      path === '/dashboard' ||
      path.startsWith('/dashboard/'),
  },
  {
    label: 'Master Data',
    matches: (path: string) =>
      /^\/(products|categories|suppliers|members)(\/|$)/.test(path),
  },
  {
    label: 'Procurement',
    matches: (path: string) =>
      /^\/(purchase-orders|goods-receipts|purchases|supplier-invoices|supplier-payments|supplier-debt)(\/|$)/.test(path),
  },
  {
    label: 'Inventory',
    matches: (path: string) =>
      /^\/(inventory|stock|stock-movement|stock-opname)(\/|$)/.test(path),
  },
  {
    label: 'Sales',
    matches: (path: string) =>
      /^\/(pos|sales|returns)(\/|$)/.test(path),
  },
  {
    label: 'Finance',
    matches: (path: string) =>
      /^\/expenses(\/|$)/.test(path),
  },
  {
    label: 'Reports',
    matches: (path: string) =>
      /^\/(reports|sales-report|purchase-report|inventory-report|supplier-report|payables-report|profit-report)(\/|$)/.test(path),
  },
  {
    label: 'Administration',
    matches: (path: string) =>
      /^\/(users|audit-logs)(\/|$)/.test(path),
  },
  {
    label: 'Account',
    matches: (path: string) =>
      /^\/(profile|account)(\/|$)/.test(path),
  },
]

const groupedNavigation = computed(() => {
  const items = visibleNavigationItems.value

  return navigationGroups
    .map((group) => ({
      ...group,
      items: items.filter((item) => group.matches(item.to)),
    }))
    .filter((group) => group.items.length > 0)
})

const ungroupedNavigation = computed(() => {
  const groupedItems = new Set(
    groupedNavigation.value.flatMap((group) => group.items),
  )

  return visibleNavigationItems.value.filter(
    (item) => !groupedItems.has(item),
  )
})

const currentRoleLabel = computed(() => {
  const role = currentUser.value?.role

  if (!role) {
    return ''
  }

  const labels: Record<string, string> = {
    ADMIN: 'Admin',
    ADMINISTRATOR: 'Admin',
    KASIR: 'Kasir',
    PENGURUS: 'Pengurus',
    ANGGOTA: 'Anggota',
  }

  return labels[role] ?? role
})

const userInitial = computed(() => {
  const source =
    currentUser.value?.name ||
    currentUser.value?.username ||
    currentUser.value?.email ||
    'U'

  return source.trim().charAt(0).toUpperCase()
})

function handleLogout() {
  isSidebarOpen.value = false
  clearAuth()
  router.push('/login')
}

function closeSidebar() {
  isSidebarOpen.value = false
}
</script>

<template>
  <div class="app-shell">
    <!-- Mobile overlay -->
    <Transition name="fade">
      <button
        v-if="isSidebarOpen"
        type="button"
        class="sidebar-overlay"
        aria-label="Tutup menu navigasi"
        @click="closeSidebar"
      />
    </Transition>

    <!-- Sidebar -->
    <aside
      class="app-sidebar"
      :class="{ 'app-sidebar--open': isSidebarOpen }"
      aria-label="Navigasi utama"
    >
      <!-- Brand -->
      <div class="sidebar-brand">
        <RouterLink
          to="/dashboard"
          class="brand-link"
          aria-label="Koprom - Dashboard"
          @click="closeSidebar"
        >
          <span class="brand-mark" aria-hidden="true">
            K
          </span>

          <span class="brand-copy">
            <strong>Koprom</strong>
            <span>Koperasi Romantis</span>
          </span>
        </RouterLink>

        <button
          type="button"
          class="icon-button sidebar-close"
          aria-label="Tutup menu navigasi"
          @click="closeSidebar"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M6 6l12 12M18 6L6 18"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
        </button>
      </div>

      <!-- Role context -->
      <div
        v-if="currentUser"
        class="role-context"
      >
        <span class="role-context__label">
          AKSES
        </span>

        <span class="role-context__value">
          {{ currentRoleLabel }}
        </span>
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav">
        <template
          v-for="group in groupedNavigation"
          :key="group.label"
        >
          <div class="nav-group">
            <p class="nav-group__label">
              {{ group.label }}
            </p>

            <RouterLink
              v-for="item in group.items"
              :key="item.to"
              :to="item.to"
              class="nav-item"
              active-class="nav-item--active"
              @click="closeSidebar"
            >
              <span class="nav-item__indicator" aria-hidden="true" />

              <span class="nav-item__label">
                {{ item.label }}
              </span>
            </RouterLink>
          </div>
        </template>

        <!-- Fallback for routes not covered by the design grouping -->
        <div
          v-if="ungroupedNavigation.length > 0"
          class="nav-group nav-group--ungrouped"
        >
          <p class="nav-group__label">
            Lainnya
          </p>

          <RouterLink
            v-for="item in ungroupedNavigation"
            :key="item.to"
            :to="item.to"
            class="nav-item"
            active-class="nav-item--active"
            @click="closeSidebar"
          >
            <span class="nav-item__indicator" aria-hidden="true" />

            <span class="nav-item__label">
              {{ item.label }}
            </span>
          </RouterLink>
        </div>
      </nav>

      <!-- Account -->
      <div class="sidebar-footer">
        <div
          v-if="currentUser"
          class="user-summary"
        >
          <span
            class="user-avatar"
            aria-hidden="true"
          >
            {{ userInitial }}
          </span>

          <div class="user-summary__info">
            <strong>
              {{
                currentUser.name ||
                currentUser.username ||
                'Pengguna'
              }}
            </strong>

            <span>
              {{ currentRoleLabel }}
            </span>
          </div>
        </div>

        <button
          type="button"
          class="logout-button"
          @click="handleLogout"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M10 17l5-5-5-5M15 12H3M21 19V5a2 2 0 0 0-2-2h-6"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>

          <span>
            Keluar
          </span>
        </button>
      </div>
    </aside>

    <!-- Main workspace -->
    <div class="app-main">
      <!-- Top bar -->
      <header class="app-header">
        <div class="app-header__left">
          <button
            type="button"
            class="menu-button"
            aria-label="Buka menu navigasi"
            :aria-expanded="isSidebarOpen"
            @click="isSidebarOpen = true"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M4 6h16M4 12h16M4 18h16"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              />
            </svg>
          </button>

          <div class="header-context">
            <span class="header-context__eyebrow">
              KOPROM
            </span>

            <span class="header-context__title">
              Operasional Toko Koperasi
            </span>
          </div>
        </div>

        <div class="app-header__right">
          <span class="connection-status">
            <span
              class="connection-status__dot"
              aria-hidden="true"
            />

            Sistem aktif
          </span>

          <div
            v-if="currentUser"
            class="header-user"
          >
            <span
              class="header-user__avatar"
              aria-hidden="true"
            >
              {{ userInitial }}
            </span>

            <span class="header-user__text">
              <strong>
                {{
                  currentUser.name ||
                  currentUser.username ||
                  'Pengguna'
                }}
              </strong>

              <small>
                {{ currentRoleLabel }}
              </small>
            </span>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="app-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:global(*) {
  box-sizing: border-box;
}

:global(html) {
  min-height: 100%;
  background: #f8faf9;
}

:global(body) {
  min-height: 100%;
  margin: 0;
  background: #f8faf9;
  color: #17201c;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  line-height: 20px;
}

:global(button),
:global(a) {
  font: inherit;
}

:global(button) {
  -webkit-tap-highlight-color: transparent;
}

:global(a) {
  color: inherit;
}

.app-shell {
  min-height: 100vh;
  background: #f8faf9;
}

/* -------------------------------------------------------------------------- */
/* Sidebar                                                                    */
/* -------------------------------------------------------------------------- */

.app-sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 50;
  display: flex;
  width: 248px;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid #164a38;
  background: #164a38;
  color: #fff;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 76px;
  padding: 16px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.brand-link {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 11px;
  text-decoration: none;
}

.brand-mark {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 8px;
  background: #12372a;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
}

.brand-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.brand-copy strong {
  overflow: hidden;
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  line-height: 20px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.brand-copy span {
  overflow: hidden;
  margin-top: 1px;
  color: rgba(255, 255, 255, 0.64);
  font-size: 11px;
  line-height: 16px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-close {
  display: none;
}

.role-context {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 16px 14px 8px;
  padding: 9px 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  background: rgba(18, 55, 42, 0.48);
}

.role-context__label {
  color: rgba(255, 255, 255, 0.52);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.role-context__value {
  color: #dcefe7;
  font-size: 11px;
  font-weight: 600;
}

.sidebar-nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 10px 18px;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
}

.nav-group {
  margin-bottom: 20px;
}

.nav-group--ungrouped {
  margin-top: 8px;
}

.nav-group__label {
  margin: 0 9px 6px;
  color: rgba(255, 255, 255, 0.42);
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.nav-item {
  position: relative;
  display: flex;
  min-height: 38px;
  align-items: center;
  gap: 9px;
  margin: 2px 0;
  padding: 8px 9px;
  border: 1px solid transparent;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 13px;
  font-weight: 500;
  line-height: 18px;
  text-decoration: none;
  transition:
    background-color 120ms ease,
    color 120ms ease,
    border-color 120ms ease;
}

.nav-item:hover {
  border-color: rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.07);
  color: #fff;
}

.nav-item--active {
  border-color: rgba(220, 239, 231, 0.14);
  background: #12372a;
  color: #fff;
  font-weight: 600;
}

.nav-item--active .nav-item__indicator {
  background: #dcefe7;
}

.nav-item__indicator {
  width: 5px;
  height: 5px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.28);
}

.nav-item__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-footer {
  padding: 12px 12px 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-summary {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
  padding: 6px 5px 10px;
}

.user-avatar,
.header-user__avatar {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-weight: 700;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: #dcefe7;
  color: #164a38;
  font-size: 12px;
}

.user-summary__info {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.user-summary__info strong {
  overflow: hidden;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  line-height: 17px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-summary__info span {
  overflow: hidden;
  color: rgba(255, 255, 255, 0.55);
  font-size: 11px;
  line-height: 15px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-button {
  display: flex;
  width: 100%;
  min-height: 36px;
  align-items: center;
  gap: 9px;
  padding: 8px 9px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: rgba(255, 255, 255, 0.66);
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  text-align: left;
}

.logout-button svg {
  width: 16px;
  height: 16px;
}

.logout-button:hover {
  border-color: rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.07);
  color: #fff;
}

/* -------------------------------------------------------------------------- */
/* Main                                                                       */
/* -------------------------------------------------------------------------- */

.app-main {
  min-width: 0;
  min-height: 100vh;
  margin-left: 248px;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  min-height: 64px;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 12px 32px;
  border-bottom: 1px solid #d6ddd9;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 1px 2px rgba(18, 55, 42, 0.06);
  backdrop-filter: blur(8px);
}

.app-header__left,
.app-header__right {
  display: flex;
  min-width: 0;
  align-items: center;
}

.app-header__left {
  gap: 12px;
}

.app-header__right {
  gap: 18px;
}

.menu-button,
.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #d6ddd9;
  border-radius: 6px;
  background: #fff;
  color: #46514b;
  cursor: pointer;
}

.menu-button {
  display: none;
  width: 38px;
  height: 38px;
}

.menu-button svg,
.icon-button svg {
  width: 18px;
  height: 18px;
}

.header-context {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.header-context__eyebrow {
  color: #176b4d;
  font-size: 10px;
  font-weight: 700;
  line-height: 14px;
  letter-spacing: 0.08em;
}

.header-context__title {
  overflow: hidden;
  color: #46514b;
  font-size: 13px;
  font-weight: 500;
  line-height: 18px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.connection-status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: #6b756f;
  font-size: 12px;
  font-weight: 500;
}

.connection-status__dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: #16834b;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 14px;
  border-left: 1px solid #e6ebe8;
}

.header-user__avatar {
  width: 30px;
  height: 30px;
  background: #f0f8f5;
  color: #176b4d;
  font-size: 11px;
}

.header-user__text {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.header-user__text strong {
  overflow: hidden;
  color: #17201c;
  font-size: 12px;
  font-weight: 600;
  line-height: 16px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-user__text small {
  color: #6b756f;
  font-size: 11px;
  line-height: 15px;
}

.app-content {
  width: 100%;
  min-width: 0;
  padding: 32px;
}

/* -------------------------------------------------------------------------- */
/* Focus & transitions                                                        */
/* -------------------------------------------------------------------------- */

:focus-visible {
  outline: 2px solid #176b4d;
  outline-offset: 2px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 120ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* -------------------------------------------------------------------------- */
/* Tablet                                                                     */
/* -------------------------------------------------------------------------- */

@media (max-width: 1199px) {
  .app-sidebar {
    width: 232px;
  }

  .app-main {
    margin-left: 232px;
  }

  .app-header {
    padding-right: 24px;
    padding-left: 24px;
  }

  .app-content {
    padding: 24px;
  }
}

/* -------------------------------------------------------------------------- */
/* Mobile                                                                     */
/* DESIGN.md §12: sidebar → drawer, padding 16px                             */
/* -------------------------------------------------------------------------- */

@media (max-width: 767px) {
  .sidebar-overlay {
    position: fixed;
    inset: 0;
    z-index: 45;
    display: block;
    width: 100%;
    height: 100%;
    padding: 0;
    border: 0;
    background: rgba(18, 55, 42, 0.38);
    cursor: pointer;
  }

  .app-sidebar {
    width: min(288px, calc(100vw - 44px));
    transform: translateX(-100%);
    box-shadow: 0 12px 32px rgba(18, 55, 42, 0.12);
    transition: transform 180ms ease;
  }

  .app-sidebar--open {
    transform: translateX(0);
  }

  .sidebar-close {
    display: inline-flex;
    width: 34px;
    height: 34px;
    border-color: rgba(255, 255, 255, 0.12);
    background: transparent;
    color: rgba(255, 255, 255, 0.72);
  }

  .sidebar-close:hover {
    border-color: rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.07);
    color: #fff;
  }

  .app-main {
    margin-left: 0;
  }

  .app-header {
    min-height: 60px;
    padding: 10px 16px;
  }

  .menu-button {
    display: inline-flex;
  }

  .connection-status {
    display: none;
  }

  .header-user {
    padding-left: 0;
    border-left: 0;
  }

  .header-user__text {
    display: none;
  }

  .app-content {
    padding: 16px;
  }
}

/* -------------------------------------------------------------------------- */
/* Small mobile                                                              */
/* -------------------------------------------------------------------------- */

@media (max-width: 420px) {
  .header-context__title {
    max-width: 160px;
  }

  .header-user__avatar {
    width: 28px;
    height: 28px;
  }

  .app-content {
    padding: 16px;
  }
}

/* -------------------------------------------------------------------------- */
/* Reduced motion                                                            */
/* -------------------------------------------------------------------------- */

@media (prefers-reduced-motion: reduce) {
  .app-sidebar,
  .fade-enter-active,
  .fade-leave-active,
  .nav-item {
    transition: none;
  }
}
</style>
