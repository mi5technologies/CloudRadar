<template>
  <teleport to="body">
    <div class="toast-container">
      <transition-group name="toast-slide" tag="div" class="toast-list">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="toast"
          :class="'toast-' + t.type"
          @click="remove(t.id)"
        >
          <span class="toast-icon">
            <svg v-if="t.type === 'success'" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
            <svg v-else-if="t.type === 'error'" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
            <svg v-else-if="t.type === 'warn'" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
            <svg v-else viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>
          </span>
          <span class="toast-message">{{ t.message }}</span>
          <button class="toast-close" @click.stop="remove(t.id)">×</button>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<script setup>
import { useToast } from '../composables/useToast'
const { toasts, remove } = useToast()
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  pointer-events: none;
}
.toast-list { display: flex; flex-direction: column; gap: 10px; align-items: flex-end; }
.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  min-width: 260px;
  max-width: 420px;
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
  pointer-events: all;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.25);
  border: 1px solid rgba(255,255,255,0.12);
  transition: transform 0.15s, box-shadow 0.15s;
}
.toast:hover { transform: translateY(-1px); box-shadow: 0 12px 28px rgba(0,0,0,0.3); }
.toast-success { background: rgba(34,197,94,0.18); color: #86efac; border-color: rgba(34,197,94,0.3); }
.toast-error   { background: rgba(239,68,68,0.18);  color: #fca5a5; border-color: rgba(239,68,68,0.3); }
.toast-warn    { background: rgba(245,158,11,0.18); color: #fcd34d; border-color: rgba(245,158,11,0.3); }
.toast-info    { background: rgba(14,165,233,0.18);  color: #7dd3fc; border-color: rgba(14,165,233,0.3); }
.toast-icon svg { width: 18px; height: 18px; flex-shrink: 0; }
.toast-message { flex: 1; line-height: 1.4; }
.toast-close { background: none; border: none; color: inherit; cursor: pointer; opacity: 0.6; font-size: 1.1rem; padding: 0 2px; line-height: 1; }
.toast-close:hover { opacity: 1; }

.toast-slide-enter-active { transition: all 0.25s ease; }
.toast-slide-leave-active { transition: all 0.2s ease; }
.toast-slide-enter-from   { opacity: 0; transform: translateX(40px); }
.toast-slide-leave-to     { opacity: 0; transform: translateX(40px); }
</style>
