<template>
  <div v-if="running" class="run-progress">
    <span class="run-progress-spinner"></span>
    <span class="run-progress-label">{{ message }}</span>
  </div>
</template>

<script setup>
defineProps({
  running: { type: Boolean, default: false },
  message: { type: String, default: 'Running…' },
})
</script>

<style scoped>
.run-progress {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-top: 12px;
  margin-bottom: 8px;
  background: rgba(14, 165, 233, 0.08);
  border: 1px solid rgba(14, 165, 233, 0.25);
  border-radius: 8px;
  font-size: 0.9rem;
  color: var(--text);
}
.run-progress-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: run-progress-spin 0.8s linear infinite;
  flex-shrink: 0;
}
@keyframes run-progress-spin {
  to { transform: rotate(360deg); }
}
.run-progress-label {
  font-weight: 500;
}
.theme-light .run-progress {
  background: rgba(2, 132, 199, 0.08);
  border-color: rgba(2, 132, 199, 0.2);
  color: #0f172a;
}
</style>
