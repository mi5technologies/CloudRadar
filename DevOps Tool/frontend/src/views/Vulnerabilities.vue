<template>
  <div>
    <h1>Vulnerabilities</h1>
    <p class="muted">
      Scan for known CVEs in container images and check AMI vulnerability status.
      Select the checks you want to run below.
    </p>

    <div class="card">
      <div class="input-group" style="max-width: 320px;">
        <label>Region</label>
        <input v-model="region" placeholder="us-east-1" />
      </div>

      <ScriptSelector
        title="Vulnerability checks"
        :scripts="vulnScripts"
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
          {{ loading ? 'Scanning…' : 'Run vulnerability scan' }}
        </button>
        <span v-if="selectedChecks.length === 0" class="run-hint warn">Select at least one check</span>
        <span v-else class="run-hint">{{ selectedChecks.length }} of {{ vulnScripts.length }} checks selected</span>
      </div>

      <p v-if="error" class="muted" style="color: var(--error); margin-top: 8px;">{{ error }}</p>
    </div>

    <div v-if="result" class="card">
      <h2>Result</h2>
      <pre>{{ JSON.stringify(result, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'
import ScriptSelector from '../components/ScriptSelector.vue'

const vulnScripts = [
  { id: 'ecr', name: 'ECR Image Scan',          description: 'Pulls all ECR repositories and scans container image layers for critical and high CVEs using AWS Inspector / ECR native scanning.' },
  { id: 'ami', name: 'AMI Vulnerability Check', description: 'Checks EC2 instances for deprecated or vulnerable AMIs (age, public AMI usage, known vulnerable image IDs).' },
]

const region = ref('us-east-1')
const selectedChecks = ref(vulnScripts.map(s => s.id))
const loading = ref(false)
const error = ref('')
const result = ref(null)

async function run() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await api.runVulnerabilities(region.value.trim() || 'us-east-1', selectedChecks.value)
  } catch (e) {
    error.value = e.message || 'Failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
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
