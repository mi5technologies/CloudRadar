<template>
  <div>
    <h1>Governance report</h1>
    <p class="muted">
      Check tag compliance and resource policies. Select the checks you want to run.
    </p>

    <div class="card">
      <div class="input-group" style="max-width: 240px;">
        <label>Output format</label>
        <select v-model="output">
          <option value="json">JSON</option>
          <option value="html">HTML (view in browser)</option>
          <option value="pdf">PDF (print / save)</option>
        </select>
      </div>
      <div v-if="output === 'pdf'" class="output-hint">
        <span>ℹ</span> The report will open in a new tab — use your browser's <strong>Print → Save as PDF</strong> to save it.
      </div>

      <ScriptSelector
        title="Governance checks"
        :scripts="govScripts"
        v-model="selectedChecks"
        :disabled="loading"
      />

      <div class="run-bar">
        <button
          class="btn btn-run"
          :disabled="loading || selectedChecks.length === 0"
          @click="run"
        >
          <span v-if="loading" class="btn-spinner"></span>
          <span v-else>▶</span>
          {{ loading ? 'Running report…' : 'Run governance report' }}
        </button>
        <span v-if="selectedChecks.length === 0" class="run-hint warn">Select at least one check</span>
        <span v-else class="run-hint">{{ selectedChecks.length }} of {{ govScripts.length }} checks selected</span>
      </div>

      <p v-if="error" class="muted" style="color: var(--error); margin-top: 8px;">{{ error }}</p>
    </div>

    <div v-if="result && output === 'json'" class="card">
      <h2>Result</h2>
      <pre>{{ typeof result === 'string' ? result.slice(0, 4000) : JSON.stringify(result, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'
import ScriptSelector from '../components/ScriptSelector.vue'
import { openPrintWindow } from '../utils/pdf'

const govScripts = [
  { id: 'tags',       name: 'Tag Compliance',         description: 'Checks all resources for required tags (e.g. Environment, Owner, CostCenter). Reports missing, incorrect, or inconsistently named tags.' },
  { id: 'policy',     name: 'Resource Policy Checks', description: 'Validates resource policies: forbidden instance types in production, minimum backup retention periods, required encryption settings.' },
  { id: 'violations', name: 'Policy Violations',      description: 'Detects resources that violate governance policies: publicly exposed resources, unencrypted storage, over-privileged IAM roles.' },
]

const output = ref('json')
const selectedChecks = ref(govScripts.map(s => s.id))
const loading = ref(false)
const error = ref('')
const result = ref(null)

async function run() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const reqOutput = output.value === 'pdf' ? 'html' : output.value
    const data = await api.runGovernance(reqOutput, selectedChecks.value)
    if (output.value === 'pdf' || output.value === 'html') {
      const html = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
      openPrintWindow(html, 'Governance Report')
    } else {
      result.value = data
    }
  } catch (e) {
    error.value = e.message || 'Failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.output-hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.82rem;
  color: var(--text-muted);
  background: rgba(14,165,233,0.07);
  border: 1px solid rgba(14,165,233,0.18);
  border-radius: 7px;
  padding: 8px 12px;
  margin-bottom: 14px;
  line-height: 1.5;
}
.output-hint span { flex-shrink: 0; color: var(--accent); font-weight: 700; }
.run-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  margin-top: 6px;
}
.btn-run {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: linear-gradient(135deg, #0ea5e9, #6366f1);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-run:disabled { opacity: 0.45; cursor: not-allowed; }
.btn-run:not(:disabled):hover { opacity: 0.88; }
.btn-spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.run-hint { font-size: 0.82rem; color: var(--text-muted); }
.run-hint.warn { color: #f97316; }
</style>
