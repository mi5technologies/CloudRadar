<template>
  <div>
    <h1>Findings</h1>
    <p class="muted">Security findings from the last successful scan. Run a Security Scan first to populate this list.</p>
    <div v-if="summary" class="card card-summary">
      <h2>Last scan</h2>
      <p class="muted">{{ summary.cloud }} · {{ summary.region || '—' }} · {{ summary.findings_count }} findings · Risk {{ summary.risk_score ?? '—' }}</p>
    </div>
    <div class="card">
      <div class="card-head">
        <h2>Findings ({{ findings.length }})</h2>
        <button class="btn btn-secondary" @click="load" :disabled="loading">Refresh</button>
      </div>
      <div v-if="loading" class="muted">Loading…</div>
      <div v-else-if="!findings.length" class="muted">No findings. Run a Security Scan to see results.</div>
      <div v-else class="findings-table-wrap">
        <table class="findings-table">
          <thead>
            <tr>
              <th>Severity</th>
              <th>Rule</th>
              <th>Resource type</th>
              <th>Resource ID</th>
              <th>Title</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(f, i) in findings" :key="i">
              <tr :class="'sev-' + (f.severity || 'medium')">
                <td><span class="badge" :class="'badge-' + (f.severity || 'medium')">{{ f.severity || 'medium' }}</span></td>
                <td><code>{{ f.rule_id || '—' }}</code></td>
                <td>{{ f.resource_type || '—' }}</td>
                <td><code class="resource-id">{{ f.resource_id || '—' }}</code></td>
                <td>{{ f.title || '—' }}</td>
                <td>
                  <button
                    v-if="isRemediable(f)"
                    class="btn-remediate"
                    @click="toggleRemediate(i)"
                  >
                    {{ remediateOpen === i ? 'Close' : 'Remediate' }}
                  </button>
                </td>
              </tr>
              <tr v-if="remediateOpen === i && isRemediable(f)" class="remediate-row">
                <td colspan="6">
                  <div class="remediate-panel">
                    <div class="remediate-options">
                      <label class="checkbox-label">
                        <input type="checkbox" v-model="remediateState[i].dry_run" />
                        Dry run first
                      </label>
                      <div class="inline-input-group">
                        <label>Region</label>
                        <input v-model="remediateState[i].region" type="text" placeholder="us-east-1" />
                      </div>
                      <button
                        class="btn btn-primary btn-sm"
                        :disabled="remediateState[i].loading"
                        @click="applyRemediate(f, i)"
                      >
                        {{ remediateState[i].loading ? 'Applying…' : 'Apply fix' }}
                      </button>
                    </div>
                    <div v-if="remediateState[i].result" class="remediate-result" :class="remediateState[i].ok ? 'result-ok' : 'result-err'">
                      {{ remediateState[i].result }}
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const findings = ref([])
const summary = ref(null)
const loading = ref(false)
const remediateOpen = ref(null)
const remediateState = ref({})

const REMEDIABLE_TYPES = ['s3', 'iam_role', 'security_group']

function isRemediable(finding) {
  return REMEDIABLE_TYPES.includes(finding.resource_type)
}

function toggleRemediate(i) {
  if (remediateOpen.value === i) {
    remediateOpen.value = null
  } else {
    remediateOpen.value = i
    if (!remediateState.value[i]) {
      remediateState.value[i] = { dry_run: true, region: 'us-east-1', loading: false, result: '', ok: false }
    }
  }
}

async function applyRemediate(finding, i) {
  const state = remediateState.value[i]
  state.loading = true
  state.result = ''
  try {
    const res = await api.remediate(finding, state.dry_run, state.region)
    state.result = typeof res === 'string' ? res : JSON.stringify(res)
    state.ok = true
  } catch (e) {
    state.result = e.message || 'Remediation failed.'
    state.ok = false
  } finally {
    state.loading = false
  }
}

async function load() {
  loading.value = true
  try {
    const data = await api.getFindings()
    findings.value = data.findings || []
    summary.value = data.summary || null
    remediateOpen.value = null
    remediateState.value = {}
  } catch {
    findings.value = []
    summary.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.card-head h2 { margin: 0; }
.card-summary {
  margin-bottom: 20px;
  background: var(--bg-card);
}
.findings-table-wrap {
  overflow-x: auto;
  margin-top: 12px;
}
.findings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}
.findings-table th,
.findings-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
.findings-table th {
  color: var(--text-muted);
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.findings-table .resource-id {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
}
.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}
.badge-critical { background: var(--error); color: #fff; }
.badge-high { background: #f97316; color: #fff; }
.badge-medium { background: var(--running); color: #1a1a1a; }
.badge-low { background: var(--success); color: #0f172a; }

.btn-remediate {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  border: none;
  cursor: pointer;
  background: rgba(14, 165, 233, 0.12);
  color: var(--accent);
  transition: background 0.15s;
  white-space: nowrap;
}
.btn-remediate:hover { background: rgba(14, 165, 233, 0.22); }

.btn-sm {
  padding: 7px 14px;
  font-size: 0.85rem;
}

.remediate-row td {
  background: rgba(14, 165, 233, 0.04);
  border-bottom: 2px solid var(--accent);
}
.remediate-panel {
  padding: 12px 4px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.remediate-options {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.88rem;
  cursor: pointer;
}
.inline-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.88rem;
}
.inline-input-group label {
  color: var(--text-muted);
  white-space: nowrap;
}
.inline-input-group input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: rgba(15, 23, 42, 0.8);
  color: var(--text);
  font-size: 0.88rem;
  width: 130px;
}
.inline-input-group input:focus {
  outline: none;
  border-color: var(--accent);
}
.remediate-result {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-all;
}
.result-ok {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success);
  border: 1px solid rgba(34, 197, 94, 0.2);
}
.result-err {
  background: rgba(239, 68, 68, 0.1);
  color: var(--error);
  border: 1px solid rgba(239, 68, 68, 0.2);
}
</style>
