<template>
  <div class="serverless-usage-view">
    <div class="view-header">
      <div>
        <h1>Serverless &amp; Usage</h1>
        <p class="muted">Serverless security checks (Lambda, Step Functions, API Gateway, SQS, DynamoDB) and usage-based findings (idle Lambdas, errors, throttles).</p>
      </div>
    </div>

    <div class="cloud-tabs">
      <button v-for="c in CLOUDS" :key="c.id"
        class="cloud-tab" :class="[`cloud-tab-${c.id}`, { active: selectedCloud === c.id }]"
        @click="selectCloud(c.id)">
        <span class="cloud-tab-icon" v-html="c.svg"></span>
        <span class="cloud-tab-label">{{ c.label }}</span>
      </button>
    </div>

    <div class="scan-tabs">
      <button class="scan-tab" :class="{ active: activeTab === 'serverless' }" @click="activeTab = 'serverless'">
        Serverless Security
      </button>
      <button class="scan-tab" :class="{ active: activeTab === 'usage' }" @click="activeTab = 'usage'">
        Usage Scan
      </button>
    </div>

    <!-- Serverless tab -->
    <div v-show="activeTab === 'serverless'" class="tab-panel">
      <div class="panel-actions">
        <button class="btn btn-primary" @click="runServerlessScan" :disabled="loadingServerless">
          <span v-if="!loadingServerless">Run serverless scan</span>
          <span v-else>Scanning…</span>
        </button>
        <button v-if="serverlessFindings.length" class="btn btn-secondary" @click="exportServerlessCSV">
          Export CSV
        </button>
      </div>
      <div v-if="errorServerless" class="card error-card">
        <p style="color: var(--error); margin:0">{{ errorServerless }}</p>
      </div>
      <div v-else-if="!hasServerlessData && !loadingServerless" class="card no-scan-card">
        <p>Run the serverless scan to check Lambda, Step Functions, API Gateway, SQS, and DynamoDB for DLQ, logging, usage plans, and more.</p>
        <button class="btn btn-primary" style="margin-top:12px" @click="runServerlessScan" :disabled="loadingServerless">
          Run serverless scan
        </button>
      </div>
      <template v-else-if="hasServerlessData">
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">Total findings</div>
            <div class="kpi-value">{{ serverlessSummary.total_findings }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">High</div>
            <div class="kpi-value">{{ serverlessSummary.high || 0 }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Medium</div>
            <div class="kpi-value">{{ serverlessSummary.medium || 0 }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Low</div>
            <div class="kpi-value">{{ serverlessSummary.low || 0 }}</div>
          </div>
        </div>
        <div class="card findings-card" v-if="serverlessFindings.length">
          <h2>Serverless findings</h2>
          <table class="findings-table">
            <thead>
              <tr>
                <th>Resource</th>
                <th>Severity</th>
                <th>Finding</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in serverlessFindings" :key="f.rule_id + f.resource_id"
                class="finding-row" :class="'sev-row-' + f.severity"
                @click="selectedServerless = selectedServerless === f ? null : f">
                <td>
                  <div class="res-name">{{ f.resource_name }}</div>
                  <div class="res-type">{{ f.resource_type }} · {{ f.region }}</div>
                </td>
                <td><span class="sev-badge" :class="'sev-' + f.severity">{{ f.severity }}</span></td>
                <td class="finding-title">{{ f.title }}</td>
              </tr>
            </tbody>
          </table>
          <transition name="slide-down">
            <div v-if="selectedServerless" class="finding-detail">
              <div class="detail-header">
                <span class="sev-badge" :class="'sev-' + selectedServerless.severity">{{ selectedServerless.severity }}</span>
                <strong>{{ selectedServerless.title }}</strong>
                <button class="close-btn" @click="selectedServerless = null">✕</button>
              </div>
              <div class="detail-body">
                <p class="detail-label">Detail</p>
                <p>{{ selectedServerless.detail }}</p>
                <p class="detail-label">Remediation</p>
                <p class="detail-remediation">{{ selectedServerless.remediation }}</p>
                <div class="detail-meta">
                  <span><strong>Rule:</strong> {{ selectedServerless.rule_id }}</span>
                  <span><strong>Resource:</strong> {{ selectedServerless.resource_id }}</span>
                  <span><strong>Region:</strong> {{ selectedServerless.region }}</span>
                </div>
              </div>
            </div>
          </transition>
        </div>
        <div v-else class="card success-card">
          <p>No serverless security findings.</p>
        </div>
      </template>
    </div>

    <!-- Usage tab -->
    <div v-show="activeTab === 'usage'" class="tab-panel">
      <div class="panel-actions">
        <button class="btn btn-primary" @click="runUsageScan" :disabled="loadingUsage">
          <span v-if="!loadingUsage">Run usage scan</span>
          <span v-else>Scanning…</span>
        </button>
        <button v-if="usageFindings.length" class="btn btn-secondary" @click="exportUsageCSV">
          Export CSV
        </button>
        <label class="days-label">
          <span class="muted">Days of metrics:</span>
          <select v-model.number="daysLookback" class="days-select">
            <option :value="7">7</option>
            <option :value="14">14</option>
            <option :value="30">30</option>
          </select>
        </label>
      </div>
      <div v-if="errorUsage" class="card error-card">
        <p style="color: var(--error); margin:0">{{ errorUsage }}</p>
      </div>
      <div v-else-if="!hasUsageData && !loadingUsage" class="card no-scan-card">
        <p>Run the usage scan to detect idle Lambdas, high error rates, and throttles from CloudWatch metrics.</p>
        <button class="btn btn-primary" style="margin-top:12px" @click="runUsageScan" :disabled="loadingUsage">
          Run usage scan
        </button>
      </div>
      <template v-else-if="hasUsageData">
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">Total findings</div>
            <div class="kpi-value">{{ usageSummary.total_findings }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Medium</div>
            <div class="kpi-value">{{ usageSummary.medium || 0 }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Low</div>
            <div class="kpi-value">{{ usageSummary.low || 0 }}</div>
          </div>
        </div>
        <div class="card findings-card" v-if="usageFindings.length">
          <h2>Usage findings (last {{ usageSummary.days_lookback || 14 }} days)</h2>
          <table class="findings-table">
            <thead>
              <tr>
                <th>Resource</th>
                <th>Severity</th>
                <th>Finding</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in usageFindings" :key="f.rule_id + f.resource_id"
                class="finding-row" :class="'sev-row-' + f.severity"
                @click="selectedUsage = selectedUsage === f ? null : f">
                <td>
                  <div class="res-name">{{ f.resource_name }}</div>
                  <div class="res-type">{{ f.resource_type }} · {{ f.region }}</div>
                </td>
                <td><span class="sev-badge" :class="'sev-' + f.severity">{{ f.severity }}</span></td>
                <td class="finding-title">{{ f.title }}</td>
              </tr>
            </tbody>
          </table>
          <transition name="slide-down">
            <div v-if="selectedUsage" class="finding-detail">
              <div class="detail-header">
                <span class="sev-badge" :class="'sev-' + selectedUsage.severity">{{ selectedUsage.severity }}</span>
                <strong>{{ selectedUsage.title }}</strong>
                <button class="close-btn" @click="selectedUsage = null">✕</button>
              </div>
              <div class="detail-body">
                <p class="detail-label">Detail</p>
                <p>{{ selectedUsage.detail }}</p>
                <p class="detail-label">Remediation</p>
                <p class="detail-remediation">{{ selectedUsage.remediation }}</p>
                <div class="detail-meta">
                  <span><strong>Rule:</strong> {{ selectedUsage.rule_id }}</span>
                  <span><strong>Resource:</strong> {{ selectedUsage.resource_id }}</span>
                  <span><strong>Region:</strong> {{ selectedUsage.region }}</span>
                </div>
              </div>
            </div>
          </transition>
        </div>
        <div v-else class="card success-card">
          <p>No usage findings (no idle Lambdas, high errors, or throttles in the period).</p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const CLOUDS = [
  { id: 'aws', label: 'AWS',
    svg: `<svg width="22" height="14" viewBox="0 0 80 48" fill="none"><path d="M22.9 32.2c-4.5 2.4-9.4 3.7-14.5 3.7C3.8 35.9 0 32.1 0 27.3c0-5.3 4.5-9.6 10.7-10.2-.3-1.1-.5-2.3-.5-3.6C10.2 6.1 15.9 1 22.9 1c3.4 0 6.5 1.2 8.9 3.2 2.2-4.3 6.7-7.2 11.7-7.2 4.3 0 8.2 1.9 10.8 5 1.9-.7 3.9-1.1 6-1.1C68 1 75 8 75 16.8c0 1.8-.3 3.5-.8 5.1C77.4 23.5 80 27 80 31.1 80 36.8 75.3 41 69.2 41H22.9z" fill="#FF9900"/></svg>` },
  { id: 'gcp', label: 'Google Cloud',
    svg: `<svg width="22" height="22" viewBox="0 0 48 48"><path fill="#4285F4" d="M30.2 17.8H24v4.2h6.9c-.7 3.7-4 6.5-7.9 6.5-4.5 0-8.2-3.7-8.2-8.2s3.7-8.2 8.2-8.2c2.1 0 4 .8 5.5 2.1l3-3C29 8.6 26.7 7.5 24 7.5c-7.5 0-13.5 6-13.5 13.5S16.5 34.5 24 34.5c7.2 0 12.8-5 12.8-13.5 0-.8-.1-1.5-.2-2.2l-6.4-1z"/></svg>` },
  { id: 'azure', label: 'Azure',
    svg: `<svg width="22" height="22" viewBox="0 0 48 48"><path fill="#0078D4" d="M27 4L13 28l9 5-7 7h16l7-36z"/><path fill="#50E6FF" d="M27 4L4 34l9-1 7-7-3-5z"/></svg>` },
]

const selectedCloud = ref('aws')
const activeTab = ref('serverless')
const loadingServerless = ref(false)
const loadingUsage = ref(false)
const errorServerless = ref('')
const errorUsage = ref('')
const serverlessFindings = ref([])
const serverlessSummary = ref({})
const usageFindings = ref([])
const usageSummary = ref({})
const selectedServerless = ref(null)
const selectedUsage = ref(null)
const daysLookback = ref(14)

const hasServerlessData = computed(() => serverlessSummary.value.total_findings !== undefined)
const hasUsageData = computed(() => usageSummary.value.total_findings !== undefined)

function selectCloud(id) {
  selectedCloud.value = id
}

async function runServerlessScan() {
  loadingServerless.value = true
  errorServerless.value = ''
  try {
    const base = import.meta.env.VITE_API_BASE || ''
    const res = await fetch(base + '/api/serverless-scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cloud: selectedCloud.value,
        region: undefined,
      }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Serverless scan failed')
    serverlessFindings.value = data.findings || []
    serverlessSummary.value = data.summary || {}
  } catch (e) {
    errorServerless.value = e.message || 'Serverless scan failed'
  } finally {
    loadingServerless.value = false
  }
}

async function runUsageScan() {
  loadingUsage.value = true
  errorUsage.value = ''
  try {
    const base = import.meta.env.VITE_API_BASE || ''
    const res = await fetch(base + '/api/usage-scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cloud: selectedCloud.value,
        region: undefined,
        days_lookback: daysLookback.value,
      }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Usage scan failed')
    usageFindings.value = data.findings || []
    usageSummary.value = data.summary || {}
  } catch (e) {
    errorUsage.value = e.message || 'Usage scan failed'
  } finally {
    loadingUsage.value = false
  }
}

function exportServerlessCSV() {
  exportCSV(serverlessFindings.value, 'serverless')
}

function exportUsageCSV() {
  exportCSV(usageFindings.value, 'usage')
}

function exportCSV(findings, prefix) {
  const headers = ['rule_id', 'resource_type', 'resource_id', 'resource_name', 'title', 'severity', 'detail', 'remediation', 'region']
  const rows = findings.map(f => headers.map(h => `"${String(f[h] || '').replace(/"/g, '""')}"`).join(','))
  const csv = [headers.join(','), ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${prefix}-scan-${selectedCloud.value}-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}
</script>

<style scoped>
.serverless-usage-view { padding: 24px 28px; max-width: 1200px; margin: 0 auto; }
.view-header { margin-bottom: 24px; }
.view-header h1 { margin: 0 0 6px; font-size: 1.5rem; font-weight: 700; }
.cloud-tabs { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.cloud-tab {
  display: inline-flex; align-items: center; gap: 8px; padding: 10px 18px; border-radius: 10px;
  background: var(--bg-el); border: 1px solid var(--border); color: var(--text-muted);
  font-size: 0.9rem; font-weight: 500; cursor: pointer; transition: all 0.15s;
}
.cloud-tab:hover { background: rgba(255,255,255,0.06); color: var(--text); }
.cloud-tab.active { color: var(--text); font-weight: 600; }
.scan-tabs { display: flex; gap: 8px; margin-bottom: 24px; }
.scan-tab {
  padding: 10px 20px; border-radius: 10px; background: var(--bg-el); border: 1px solid var(--border);
  color: var(--text-muted); font-weight: 500; cursor: pointer; transition: all 0.15s;
}
.scan-tab:hover { color: var(--text); }
.scan-tab.active { background: rgba(14,165,233,0.12); color: var(--accent); border-color: var(--accent); }
.tab-panel { min-height: 200px; }
.panel-actions { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.days-label { display: flex; align-items: center; gap: 8px; font-size: 0.9rem; }
.days-select { padding: 6px 10px; border-radius: 8px; background: var(--bg-el); border: 1px solid var(--border); color: var(--text); }
.error-card, .no-scan-card { padding: 24px; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-bottom: 24px; }
.kpi-card { padding: 16px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; }
.kpi-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); font-weight: 700; }
.kpi-value { font-size: 1.4rem; font-weight: 700; color: var(--text); }
.findings-card { padding: 20px; }
.findings-card h2 { margin: 0 0 16px; font-size: 1.1rem; }
.findings-table { width: 100%; border-collapse: collapse; }
.findings-table th { padding: 9px 12px; text-align: left; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); background: var(--bg-el-lo); }
.findings-table td { padding: 12px; border-bottom: 1px solid var(--border); font-size: 0.88rem; }
.finding-row { cursor: pointer; transition: background 0.12s; }
.finding-row:hover { background: rgba(255,255,255,0.03); }
.res-name { font-weight: 600; color: var(--text); }
.res-type { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }
.finding-title { color: var(--text-muted); }
.sev-badge { font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; text-transform: uppercase; }
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
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
