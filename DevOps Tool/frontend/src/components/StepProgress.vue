<template>
  <div class="step-progress">
    <div class="step-progress-title">{{ title }}</div>
    <div v-if="steps.length === 0 && !error" class="step-progress-waiting">Waiting for execution logs…</div>
    <div class="steps" :class="{ 'steps-scroll': steps.length > 4 }">
      <div
        v-for="(step, i) in steps"
        :key="i"
        class="step"
        :class="[step.status === 'running' ? 'step-running' : '', step.status === 'success' ? 'step-success' : '', step.status === 'failed' ? 'step-failed' : '']"
      >
        <div class="step-indicator">
          <span v-if="step.status === 'running'" class="step-spinner"></span>
          <span v-else-if="step.status === 'success'" class="step-check">✓</span>
          <span v-else-if="step.status === 'failed'" class="step-x">✕</span>
          <span v-else class="step-dot"></span>
        </div>
        <div class="step-content">
          <div class="step-label">{{ step.step }}</div>
          <div v-if="step.detail" class="step-detail">{{ step.detail }}</div>
        </div>
      </div>
    </div>
    <div v-if="error" class="step-error">{{ error }}</div>
    <div v-if="done && summary" class="step-summary card">
      <h3>Result</h3>
      <pre>{{ JSON.stringify(summary, null, 2) }}</pre>
      <div v-if="downloads && downloads.length" class="downloads">
        <a v-for="d in downloads" :key="d.url" :href="d.url" class="btn btn-primary" target="_blank" rel="noopener">{{ d.label }}</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

defineProps({
  title: { type: String, default: 'Execution' },
  steps: { type: Array, default: () => [] },
  error: { type: String, default: '' },
  done: { type: Boolean, default: false },
  summary: { type: Object, default: null },
  downloads: { type: Array, default: () => [] },
})
</script>

<style scoped>
.step-progress {
  margin: 20px 0;
}
.step-progress-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text);
}
.step-progress-waiting {
  padding: 16px;
  color: var(--text-muted);
  font-size: 0.9rem;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 8px;
  margin-bottom: 12px;
}
.steps {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.steps-scroll {
  max-height: 420px;
  overflow-y: auto;
  overflow-x: hidden;
}
.step {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 2px;
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid transparent;
  transition: background 0.15s, border-color 0.15s;
}
.step-running {
  background: rgba(14, 165, 233, 0.08);
  border-color: rgba(14, 165, 233, 0.25);
}
.step-success {
  background: rgba(34, 197, 94, 0.06);
  border-color: rgba(34, 197, 94, 0.15);
}
.step-failed {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.25);
}
.step-indicator {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
}
.step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--text-muted);
  opacity: 0.5;
}
.step-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.step-check {
  color: var(--success);
  font-weight: 700;
}
.step-x {
  color: var(--error);
  font-weight: 700;
}
.step-content {
  flex: 1;
  min-width: 0;
}
.step-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text);
}
.step-detail {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 2px;
}
.step-error {
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #fca5a5;
  font-size: 0.9rem;
}
.step-summary {
  margin-top: 24px;
}
.step-summary h3 {
  margin: 0 0 12px;
  font-size: 1rem;
}
.step-summary pre {
  background: rgba(0, 0, 0, 0.25);
  padding: 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  overflow-x: auto;
  margin-bottom: 12px;
}
.downloads {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.downloads .btn {
  margin: 0;
}
</style>
