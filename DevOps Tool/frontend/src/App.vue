<template>
  <div class="app-layout" :class="{ 'no-sidebar': noSidebar }">
    <Sidebar v-if="!noSidebar" />
    <main class="main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'

const route = useRoute()
const noSidebar = computed(() => !!route.meta.noSidebar)
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
  margin-left: 260px;
  padding: 24px 32px 48px;
  max-width: 1200px;
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
