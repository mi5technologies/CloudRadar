<template>
  <div class="ai-view">
    <div class="ai-header">
      <div>
        <h1>AI Usage Security</h1>
        <p class="muted">Verify guardrails, content filters, and safety settings for AWS Bedrock, Vertex AI, and Azure OpenAI.</p>
      </div>
      <div class="ai-header-actions">
        <button class="btn btn-primary" @click="runScan" :disabled="loading">
          <svg v-if="!loading" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
            <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="spin">
            <path d="M21 12a9 9 0 11-9-9"/>
          </svg>
          {{ loading ? 'Scanning…' : 'Run AI scan' }}
        </button>
        <button v-if="findings.length" class="btn btn-secondary" @click="exportCSV">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Export CSV
        </button>
      </div>
    </div>

    <div class="cloud-tabs">
      <button v-for="c in CLOUDS" :key="c.id"
        class="cloud-tab" :class="[`cloud-tab-${c.id}`, { active: selectedCloud === c.id }]"
        @click="selectCloud(c.id)">
        <span class="cloud-tab-icon" v-html="c.svg"></span>
        <span class="cloud-tab-label">{{ c.label }}</span>
        <span v-if="summaryByCloud[c.id]" class="cloud-tab-badge">
          {{ summaryByCloud[c.id].total_findings }}
        </span>
      </button>
    </div>

    <!-- Configure checks -->
    <div class="card checks-card" v-if="!loading">
      <div class="checks-header" @click="checksOpen = !checksOpen">
        <div class="checks-header-left">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
          </svg>
          <span class="checks-title">Configure checks</span>
          <span class="checks-summary-badge">{{ enabledCount }} / {{ allChecks.length }} enabled</span>
        </div>
        <div class="checks-header-right">
          <button class="checks-select-all" @click.stop="selectAllChecks(true)">Select all</button>
          <button class="checks-select-all" @click.stop="selectAllChecks(false)">Deselect all</button>
          <svg class="checks-arrow" :class="{ open: checksOpen }" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </div>

      <transition name="panel-slide">
        <div v-if="checksOpen" class="checks-body">
          <p class="checks-hint muted">
            Deselect any check you want to deliberately skip. Your selection is remembered per cloud.
          </p>
          <div v-for="cat in CHECK_CATEGORIES" :key="cat.id" class="check-cat-block">
            <div class="check-cat-header">
              <label class="check-cat-toggle">
                <input type="checkbox"
                  :checked="isCatAllSelected(cat.id)"
                  :indeterminate.prop="isCatIndeterminate(cat.id)"
                  @change="toggleCategory(cat.id, $event.target.checked)"
                />
                <span class="cat-dot" :style="{ background: cat.color }"></span>
                <span class="check-cat-label">{{ cat.label }}</span>
                <span class="check-cat-count muted">{{ checksForCloud(cat.id).length }} check{{ checksForCloud(cat.id).length !== 1 ? 's' : '' }}</span>
              </label>
            </div>
            <div class="check-grid">
              <label v-for="chk in checksForCloud(cat.id)" :key="chk.rule_id" class="check-item"
                :class="{ 'check-item-disabled': !enabledRules.has(chk.rule_id) }">
                <input type="checkbox"
                  :checked="enabledRules.has(chk.rule_id)"
                  @change="toggleRule(chk.rule_id, $event.target.checked)"
                />
                <div class="check-item-body">
                  <div class="check-item-top">
                    <span class="check-item-name">{{ chk.title }}</span>
                    <span class="sev-badge" :class="'sev-' + chk.severity">{{ chk.severity }}</span>
                  </div>
                  <div class="check-item-desc muted">{{ chk.desc }}</div>
                </div>
              </label>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <div v-if="error" class="card error-card">
      <p style="color: var(--error); margin:0">{{ error }}</p>
    </div>

    <div v-else-if="!hasData && !loading" class="card no-scan-card">
      <div class="no-scan-inner">
        <div class="no-scan-icon" v-html="CLOUDS.find(c => c.id === selectedCloud)?.svg"></div>
        <div>
          <h3>No {{ cloudLabel }} AI scan yet</h3>
          <p>Run the AI Usage Security scan to check guardrails, content filters, and safety settings for your {{ cloudLabel }} AI services.</p>
          <button class="btn btn-primary" style="margin-top:12px" @click="runScan" :disabled="loading">
            Scan {{ cloudLabel }}
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="loading" class="card loading-card">
      <div class="skeleton-row" v-for="i in 4" :key="i"></div>
    </div>

    <template v-else-if="hasData">
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-icon-wrap" style="background: rgba(239,68,68,0.12)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">Total findings</div>
            <div class="kpi-value">{{ summary.total_findings }}</div>
            <div class="kpi-sub">AI security issues</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon-wrap" style="background: rgba(239,68,68,0.12)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">Critical</div>
            <div class="kpi-value">{{ summary.critical || 0 }}</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon-wrap" style="background: rgba(249,115,22,0.12)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">High</div>
            <div class="kpi-value">{{ summary.high || 0 }}</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon-wrap" style="background: rgba(234,179,8,0.12)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#eab308" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">Medium / Low</div>
            <div class="kpi-value">{{ (summary.medium || 0) + (summary.low || 0) }}</div>
          </div>
        </div>
      </div>

      <div class="card findings-card" v-if="findings.length">
        <h2>AI security findings</h2>
        <table class="cost-table">
          <thead>
            <tr>
              <th>Resource</th>
              <th>Severity</th>
              <th>Finding</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="f in findings" :key="f.rule_id + f.resource_id"
              class="finding-row" :class="'sev-row-' + f.severity"
              @click="selectedFinding = selectedFinding === f ? null : f">
              <td>
                <div class="res-name">{{ f.resource_name }}</div>
                <div class="res-type">{{ f.resource_type }} · {{ f.region }}</div>
              </td>
              <td>
                <span class="sev-badge" :class="'sev-' + f.severity">{{ f.severity }}</span>
              </td>
              <td class="finding-title">{{ f.title }}</td>
            </tr>
          </tbody>
        </table>

        <transition name="slide-down">
          <div v-if="selectedFinding" class="finding-detail">
            <div class="detail-header">
              <span class="sev-badge" :class="'sev-' + selectedFinding.severity">{{ selectedFinding.severity }}</span>
              <strong>{{ selectedFinding.title }}</strong>
              <button class="close-btn" @click="selectedFinding = null">✕</button>
            </div>
            <div class="detail-body">
              <p class="detail-label">Detail</p>
              <p>{{ selectedFinding.detail }}</p>
              <p class="detail-label">Remediation</p>
              <p class="detail-remediation">{{ selectedFinding.remediation }}</p>
              <div class="detail-meta">
                <span><strong>Rule:</strong> {{ selectedFinding.rule_id }}</span>
                <span><strong>Resource:</strong> {{ selectedFinding.resource_id }}</span>
                <span><strong>Region:</strong> {{ selectedFinding.region }}</span>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <div v-else class="card success-card">
        <div class="success-inner">
          <span class="success-icon">✓</span>
          <div>
            <h3>No AI security findings</h3>
            <p>Your {{ cloudLabel }} AI configuration looks good. Continue to monitor guardrails and content filters as you add new models.</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { logAudit } from '../utils/auditLog.js'

const CLOUDS = [
  { id: 'aws', label: 'AWS',
    svg: `<svg width="22" height="22" viewBox="0 0 40 40"><path d="M11.4 23.8c-.3.3-.4.7-.2 1.1.3.5.9.5 1.3.3l2.3-1 .5.5v.7l-2 1.8c-.4.3-.5.8-.2 1.2.2.4.7.5 1.1.3l2.9-1.4.9.9v.9l-2.9 2.5c-.4.3-.5.9-.2 1.3.3.4.8.5 1.2.2l3.6-2.4 2.2 2.2c1.3 1.3 3.3.4 3.3-1.4V28l4.1-4.1c.5-.5.5-1.4 0-1.9l-6.3-6.3a1.34 1.34 0 00-1.9 0L17 20l-3.7-.6-1.9 4.4z" fill="#FF9900"/></svg>` },
  { id: 'gcp', label: 'Google Cloud',
    svg: `<svg width="22" height="22" viewBox="0 0 40 40"><path d="M20 8.8l5.5 5.5H26a8 8 0 11-8 8h-3a11 11 0 1011-11h-.9L20 8.8z" fill="#4285F4"/><path d="M20 8.8L14.5 14.3H14a8 8 0 000 16h3a11 11 0 010-22h3z" fill="#34A853"/></svg>` },
  { id: 'azure', label: 'Azure',
    svg: `<svg width="22" height="22" viewBox="0 0 40 40"><path d="M16 6l-8 22h6l10-12-8 12h14L22 6l-6 14L16 6z" fill="#0078D4"/></svg>` },
]

const CHECK_CATEGORIES = [
  { id: 'aws', label: 'AWS Bedrock', color: '#FF9900' },
  { id: 'gcp', label: 'Google Vertex AI', color: '#4285F4' },
  { id: 'azure', label: 'Azure OpenAI', color: '#0078D4' },
]

const ALL_CHECKS = [
  { rule_id: 'ai.bedrock.no_guardrails', cloud: 'aws', severity: 'high',
    title: 'No Bedrock Guardrails configured', desc: 'Foundation models available but no Guardrails defined. Prompts and completions are not filtered.' },
  { rule_id: 'ai.bedrock.guardrail_not_ready', cloud: 'aws', severity: 'medium',
    title: 'Guardrail not ready', desc: 'A Bedrock Guardrail exists but status is not READY.' },
  { rule_id: 'ai.aws.unavailable', cloud: 'aws', severity: 'low',
    title: 'Bedrock API unavailable', desc: 'Could not connect to Bedrock. Check credentials and permissions.' },
  { rule_id: 'ai.vertex.safety_review', cloud: 'gcp', severity: 'low',
    title: 'Review Vertex AI safety settings', desc: 'Manually verify safety settings on Vertex AI endpoints.' },
  { rule_id: 'ai.gcp.unavailable', cloud: 'gcp', severity: 'low',
    title: 'Vertex AI API unavailable', desc: 'Could not initialize Vertex AI.' },
  { rule_id: 'ai.gcp.sdk_missing', cloud: 'gcp', severity: 'low',
    title: 'Vertex AI SDK not installed', desc: 'google-cloud-aiplatform is required.' },
  { rule_id: 'ai.azure.content_filter_review', cloud: 'azure', severity: 'low',
    title: 'Review Azure OpenAI content filters', desc: 'Verify content filters are enabled on Azure OpenAI accounts.' },
  { rule_id: 'ai.azure.unavailable', cloud: 'azure', severity: 'low',
    title: 'Azure OpenAI API unavailable', desc: 'Could not connect to Azure Cognitive Services.' },
  { rule_id: 'ai.azure.sdk_missing', cloud: 'azure', severity: 'low',
    title: 'Azure Cognitive Services SDK not installed', desc: 'azure-mgmt-cognitiveservices is required.' },
]

const selectedCloud = ref('aws')
const loading = ref(false)
const error = ref('')
const findings = ref([])
const summary = ref({})
const summaryByCloud = ref({})
const findingsByCloud = ref({})
const selectedFinding = ref(null)

const cloudLabel = computed(() => CLOUDS.find(c => c.id === selectedCloud.value)?.label || selectedCloud.value)
const hasData = computed(() => Object.keys(summaryByCloud.value).includes(selectedCloud.value))

const allChecks = ALL_CHECKS
const checksOpen = ref(true)

const _storageKey = () => `cspm_ai_enabled_${selectedCloud.value}`
const enabledRules = ref(new Set(ALL_CHECKS.filter(c => c.cloud === 'aws').map(c => c.rule_id)))

function _loadEnabled(cloud) {
  try {
    const raw = localStorage.getItem(`cspm_ai_enabled_${cloud}`)
    if (raw) {
      const arr = JSON.parse(raw)
      return new Set(arr)
    }
  } catch (_) {}
  return new Set(ALL_CHECKS.filter(c => c.cloud === cloud).map(c => c.rule_id))
}

function _saveEnabled() {
  try {
    localStorage.setItem(_storageKey(), JSON.stringify([...enabledRules.value]))
  } catch (_) {}
}

function toggleRule(ruleId, checked) {
  const set = new Set(enabledRules.value)
  if (checked) set.add(ruleId); else set.delete(ruleId)
  enabledRules.value = set
  _saveEnabled()
}

function toggleCategory(catId, checked) {
  const rules = ALL_CHECKS.filter(c => c.cloud === catId).map(c => c.rule_id)
  const set = new Set(enabledRules.value)
  for (const r of rules) {
    if (checked) set.add(r); else set.delete(r)
  }
  enabledRules.value = set
  _saveEnabled()
}

function isCatAllSelected(catId) {
  const rules = ALL_CHECKS.filter(c => c.cloud === catId).map(c => c.rule_id)
  return rules.length > 0 && rules.every(r => enabledRules.value.has(r))
}

function isCatIndeterminate(catId) {
  const rules = ALL_CHECKS.filter(c => c.cloud === catId).map(c => c.rule_id)
  const n = rules.filter(r => enabledRules.value.has(r)).length
  return n > 0 && n < rules.length
}

function selectAllChecks(checked) {
  const rules = checksForCloud(selectedCloud.value).map(c => c.rule_id)
  const set = new Set(enabledRules.value)
  for (const r of rules) {
    if (checked) set.add(r); else set.delete(r)
  }
  enabledRules.value = set
  _saveEnabled()
}

function checksForCloud(cloud) {
  return ALL_CHECKS.filter(c => c.cloud === cloud)
}

const enabledCount = computed(() => checksForCloud(selectedCloud.value).filter(c => enabledRules.value.has(c.rule_id)).length)

watch(selectedCloud, (cloud) => {
  enabledRules.value = _loadEnabled(cloud)
})

async function runScan() {
  loading.value = true
  error.value = ''
  try {
    const base = import.meta.env.VITE_API_BASE || ''
    const skipRules = checksForCloud(selectedCloud.value)
      .filter(c => !enabledRules.value.has(c.rule_id))
      .map(c => c.rule_id)
    const body = { cloud: selectedCloud.value, skip_rules: skipRules }
    if (selectedCloud.value === 'aws') body.region = undefined
    if (selectedCloud.value === 'gcp') body.region = 'us-central1'
    const res = await fetch(base + '/api/ai-scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'AI scan failed')
    const cloud = selectedCloud.value
    const f = data.findings || []
    const s = data.summary || {}
    findings.value = f
    summary.value = s
    findingsByCloud.value = { ...findingsByCloud.value, [cloud]: f }
    summaryByCloud.value = { ...summaryByCloud.value, [cloud]: s }
    logAudit('ai_scan', { cloud: selectedCloud.value, findings: findings.value.length })
  } catch (e) {
    error.value = e.message || 'Failed to run AI scan'
  } finally {
    loading.value = false
  }
}

function selectCloud(id) {
  selectedCloud.value = id
  enabledRules.value = _loadEnabled(id)
  if (summaryByCloud.value[id]) {
    summary.value = summaryByCloud.value[id]
    findings.value = findingsByCloud.value[id] || []
  } else {
    summary.value = {}
    findings.value = []
  }
}

function exportCSV() {
  const headers = ['rule_id', 'resource_type', 'resource_id', 'resource_name', 'title', 'severity', 'detail', 'remediation', 'region']
  const rows = findings.value.map(f => headers.map(h => `"${String(f[h] || '').replace(/"/g, '""')}"`).join(','))
  const csv = [headers.join(','), ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `ai-security-${selectedCloud.value}-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}

onMounted(() => {
  selectCloud(selectedCloud.value)
})
</script>

<style scoped>
.ai-view { padding: 24px 28px; max-width: 1200px; margin: 0 auto; }
.ai-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }
.ai-header h1 { margin: 0 0 6px; font-size: 1.5rem; font-weight: 700; }
.ai-header-actions { display: flex; gap: 10px; flex-shrink: 0; }
.cloud-tabs { display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; }
.cloud-tab {
  display: inline-flex; align-items: center; gap: 8px; padding: 10px 18px; border-radius: 10px;
  background: var(--bg-el); border: 1px solid var(--border); color: var(--text-muted);
  font-size: 0.9rem; font-weight: 500; cursor: pointer; transition: all 0.15s;
}
.cloud-tab:hover { background: rgba(255,255,255,0.06); color: var(--text); }
.cloud-tab.active { color: var(--text); font-weight: 600; }
.cloud-tab-badge { margin-left: 4px; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; background: rgba(239,68,68,0.2); color: #f87171; }
.no-scan-card, .loading-card, .error-card { padding: 32px; }
.no-scan-inner { display: flex; align-items: center; gap: 24px; }
.no-scan-icon { font-size: 2.5rem; display: flex; align-items: center; flex-shrink: 0; }
.no-scan-icon :deep(svg) { width: 48px; height: 48px; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
.kpi-card { display: flex; align-items: center; gap: 16px; padding: 18px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; }
.kpi-icon-wrap { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.kpi-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); font-weight: 700; }
.kpi-value { font-size: 1.4rem; font-weight: 700; color: var(--text); line-height: 1.2; }
.kpi-sub { font-size: 0.72rem; color: var(--text-muted); }
.findings-card h2 { margin: 0 0 16px; font-size: 1.1rem; }
.cost-table { width: 100%; border-collapse: collapse; }
.cost-table th { padding: 9px 12px; text-align: left; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); background: var(--bg-el-lo); white-space: nowrap; }
.cost-table td { padding: 12px; border-bottom: 1px solid var(--border); font-size: 0.88rem; }
.finding-row { cursor: pointer; transition: background 0.12s; }
.finding-row:hover { background: rgba(255,255,255,0.03); }
.res-name { font-weight: 600; color: var(--text); }
.res-type { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }
.finding-title { color: var(--text-muted); }
.sev-badge { font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; text-transform: uppercase; }
.sev-badge.sev-critical { background: rgba(239,68,68,0.15); color: #f87171; }
.sev-badge.sev-high { background: rgba(249,115,22,0.15); color: #fb923c; }
.sev-badge.sev-medium { background: rgba(234,179,8,0.15); color: #fbbf24; }
.sev-badge.sev-low { background: rgba(59,130,246,0.15); color: #60a5fa; }
.finding-detail { margin-top: 16px; padding: 16px; background: var(--bg-el); border: 1px solid var(--border); border-radius: 10px; }
.detail-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.close-btn { margin-left: auto; background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 1rem; padding: 2px 6px; }
.detail-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); margin: 12px 0 4px; }
.detail-remediation { white-space: pre-wrap; }
.detail-meta { display: flex; gap: 18px; flex-wrap: wrap; font-size: 0.78rem; color: var(--text-muted); margin-top: 12px; }
.success-card { padding: 24px; }
.success-inner { display: flex; align-items: center; gap: 20px; }
.success-icon { width: 48px; height: 48px; border-radius: 50%; background: rgba(34,197,94,0.2); color: #22c55e; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 700; }
.skeleton-row { height: 48px; background: var(--bg-el); border-radius: 8px; margin-bottom: 8px; }
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-8px); }

/* Configure checks */
.checks-card { margin-bottom: 22px; padding: 0; overflow: hidden; }
.checks-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; cursor: pointer; user-select: none; transition: background 0.12s; }
.checks-header:hover { background: var(--bg-el-lo); }
.checks-header-left { display: flex; align-items: center; gap: 10px; }
.checks-header-right { display: flex; align-items: center; gap: 8px; }
.checks-title { font-size: 0.92rem; font-weight: 600; color: var(--text); }
.checks-summary-badge { padding: 2px 9px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; background: rgba(14,165,233,0.12); color: var(--accent); }
.checks-select-all { padding: 4px 10px; border-radius: 7px; font-size: 0.75rem; font-weight: 600; background: var(--bg-el); border: 1px solid var(--border); color: var(--text-muted); cursor: pointer; transition: all 0.12s; }
.checks-select-all:hover { background: var(--bg-el-hi); color: var(--text); }
.checks-arrow { transition: transform 0.2s; flex-shrink: 0; color: var(--text-muted); }
.checks-arrow.open { transform: rotate(180deg); }
.checks-body { padding: 0 18px 18px; border-top: 1px solid var(--border); }
.checks-hint { font-size: 0.82rem; margin: 12px 0 16px; }
.check-cat-block { margin-bottom: 18px; }
.check-cat-header { margin-bottom: 8px; }
.check-cat-toggle { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 600; color: var(--text); }
.check-cat-toggle input[type="checkbox"] { cursor: pointer; width: 15px; height: 15px; flex-shrink: 0; }
.check-cat-label { font-weight: 700; }
.check-cat-count { font-weight: 400; font-size: 0.78rem; }
.check-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 8px; padding-left: 24px; }
.check-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px; border-radius: 9px; border: 1px solid var(--border); background: var(--bg-el-xlo); cursor: pointer; transition: all 0.12s; }
.check-item:hover { background: var(--bg-el); border-color: rgba(14,165,233,0.2); }
.check-item-disabled { opacity: 0.45; }
.check-item input[type="checkbox"] { flex-shrink: 0; margin-top: 3px; cursor: pointer; width: 14px; height: 14px; }
.check-item-body { flex: 1; min-width: 0; }
.check-item-top { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 3px; }
.check-item-name { font-size: 0.83rem; font-weight: 600; color: var(--text); }
.check-item-desc { font-size: 0.76rem; color: var(--text-muted); line-height: 1.4; }
.panel-slide-enter-active, .panel-slide-leave-active { transition: all 0.2s ease; overflow: hidden; }
.panel-slide-enter-from, .panel-slide-leave-to { opacity: 0; max-height: 0; }
.panel-slide-enter-to, .panel-slide-leave-from { max-height: 1200px; }
</style>
