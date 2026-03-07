<template>
  <div class="app-layout" :class="{ 'no-sidebar': noSidebar }">
    <!-- Mobile hamburger overlay -->
    <transition name="overlay-fade">
      <div v-if="mobileOpen" class="mobile-overlay" @click="mobileOpen = false"></div>
    </transition>

    <Sidebar
      v-if="!noSidebar"
      :class="{ 'sidebar-mobile-open': mobileOpen }"
      @close-mobile="mobileOpen = false"
    />

    <!-- Mobile hamburger button -->
    <button v-if="!noSidebar" class="hamburger-btn" @click="mobileOpen = !mobileOpen" aria-label="Toggle sidebar">
      <svg v-if="!mobileOpen" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>

    <main class="main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>

  <!-- Global: Toast notifications -->
  <ToastContainer />

  <!-- Global: Command palette (Ctrl+K) -->
  <CommandPalette />
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import ToastContainer from './components/ToastContainer.vue'
import CommandPalette from './components/CommandPalette.vue'

const route = useRoute()
const noSidebar = computed(() => !!route.meta.noSidebar)
const mobileOpen = ref(false)
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}
.app-layout.no-sidebar .main {
  margin-left: 0;
  max-width: none;
}
.main {
  flex: 1;
  margin-left: var(--sidebar-width, 260px);
  padding: 24px 32px 48px;
  max-width: calc(1200px + var(--sidebar-width, 260px));
  transition: margin-left 0.22s ease;
}

/* ── Mobile hamburger ── */
.hamburger-btn {
  display: none;
  position: fixed;
  top: 14px;
  left: 14px;
  z-index: 1100;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text);
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(0,0,0,0.3);
  transition: background 0.15s;
}
.hamburger-btn:hover { background: var(--bg-hover); }

.mobile-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 999;
  backdrop-filter: blur(2px);
}
.overlay-fade-enter-active { transition: opacity 0.2s; }
.overlay-fade-leave-active { transition: opacity 0.18s; }
.overlay-fade-enter-from, .overlay-fade-leave-to { opacity: 0; }

@media (max-width: 768px) {
  .hamburger-btn { display: flex; }
  .main {
    margin-left: 0 !important;
    padding: 70px 16px 40px;
    max-width: 100%;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
