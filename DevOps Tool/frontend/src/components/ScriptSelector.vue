<template>
  <div class="script-selector">
    <div class="ss-header">
      <span class="ss-title">{{ title }}</span>
      <div class="ss-actions">
        <button class="btn btn-secondary btn-sm" :disabled="disabled" @click="selectAll">All</button>
        <button class="btn btn-secondary btn-sm" :disabled="disabled" @click="selectNone">None</button>
      </div>
    </div>
    <div class="ss-list">
      <label
        v-for="s in scripts"
        :key="s.id"
        class="ss-item"
        :class="{ 'ss-item-checked': modelValue.includes(s.id) }"
      >
        <input
          type="checkbox"
          :value="s.id"
          :checked="modelValue.includes(s.id)"
          :disabled="disabled"
          @change="toggle(s.id)"
        />
        <div class="ss-info">
          <span class="ss-name">{{ s.name }}</span>
          <span class="ss-desc">{{ s.description }}</span>
        </div>
      </label>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  title:      { type: String,  default: 'Select scripts to run' },
  scripts:    { type: Array,   required: true },
  modelValue: { type: Array,   required: true },
  disabled:   { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

function selectAll() {
  emit('update:modelValue', props.scripts.map(s => s.id))
}
function selectNone() {
  emit('update:modelValue', [])
}
function toggle(id) {
  const cur = [...props.modelValue]
  const idx = cur.indexOf(id)
  if (idx === -1) cur.push(id)
  else cur.splice(idx, 1)
  emit('update:modelValue', cur)
}
</script>

<style scoped>
.script-selector {
  margin-bottom: 18px;
}
.ss-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.ss-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.ss-actions {
  display: flex;
  gap: 6px;
}
.btn-sm {
  font-size: 0.78rem;
  padding: 3px 10px;
}

.ss-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ss-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 13px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid var(--border);
  border-left: 3px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
}
.ss-item:hover {
  background: rgba(14,165,233,0.08);
  border-color: rgba(14,165,233,0.2);
}
.ss-item-checked {
  border-color: rgba(14,165,233,0.3);
  border-left-color: #0ea5e9;
  background: rgba(14,165,233,0.08);
  box-shadow: 0 2px 8px rgba(14,165,233,0.1);
}
.ss-item input[type="checkbox"] {
  margin-top: 3px;
  flex-shrink: 0;
  cursor: pointer;
  accent-color: #0ea5e9;
}
.ss-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}
.ss-name {
  font-weight: 600;
  font-size: 0.88rem;
  color: var(--text);
}
.ss-desc {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.4;
}

/* ── Light theme glassmorphism ── */
:global(.theme-light) .ss-item {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-color: rgba(71, 85, 105, 0.16);
  border-left-color: transparent;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.04);
}
:global(.theme-light) .ss-item:hover {
  background: rgba(14, 165, 233, 0.07);
  border-color: rgba(14, 165, 233, 0.28);
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.08);
}
:global(.theme-light) .ss-item-checked {
  background: rgba(2, 132, 199, 0.07);
  border-color: rgba(2, 132, 199, 0.28);
  border-left-color: #0284c7;
  box-shadow: 0 2px 10px rgba(2, 132, 199, 0.12), 0 1px 3px rgba(0, 0, 0, 0.04);
}
:global(.theme-light) .ss-name { color: #0f172a; }
:global(.theme-light) .ss-desc { color: #475569; }
</style>
