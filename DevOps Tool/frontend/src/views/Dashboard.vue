<template>
  <div>
    <div class="dash-header">
      <div>
        <h1>Dashboard</h1>
        <p class="muted">Overview of your cloud security posture.</p>
      </div>
      <div class="dash-header-actions">
        <router-link to="/security/scan" class="btn btn-primary">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          Run Scan
        </router-link>
        <router-link to="/findings" class="btn btn-secondary">View Findings</router-link>
      </div>
    </div>

    <!-- Cloud tabs -->
    <div class="cloud-tabs">
      <button
        v-for="c in CLOUDS"
        :key="c.id"
        class="cloud-tab"
        :class="{ active: selectedCloud === c.id, ['cloud-tab-' + c.id]: true }"
        @click="switchCloud(c.id)"
      >
        <span class="cloud-tab-icon" v-html="c.icon"></span>
        <span class="cloud-tab-label">{{ c.label }}</span>
        <span class="cloud-tab-badge" v-if="cloudHistoryCount(c.id) > 0">{{ cloudHistoryCount(c.id) }}</span>
      </button>
    </div>

    <!-- KPI cards -->
    <div class="metric-grid">
      <div class="metric-card metric-scan">
        <div class="metric-icon-wrap" style="background:rgba(14,165,233,0.12);">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </div>
        <div class="metric-info">
          <span class="metric-label">Last scan</span>
          <span class="metric-value">{{ lastScan ? formatRelative(lastScan.timestamp) : '—' }}</span>
          <span class="metric-sub" v-if="lastScan">{{ (lastScan.cloud||'').toUpperCase() }} · {{ lastScan.region || '' }}</span>
          <span class="metric-sub" v-else>No scans for {{ cloudLabel }}</span>
        </div>
      </div>
      <div class="metric-card metric-findings">
        <div class="metric-icon-wrap" style="background:rgba(99,102,241,0.12);">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        </div>
        <div class="metric-info">
          <span class="metric-label">Total findings</span>
          <span class="metric-value">{{ lastScan?.findings_count ?? (summaryCloud ? summaryData?.findings_count : null) ?? '—' }}</span>
          <span class="metric-sub">from latest {{ cloudLabel }} scan</span>
        </div>
      </div>
      <div class="metric-card metric-risk">
        <div class="metric-icon-wrap" :style="{ background: riskIconBg }">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" :stroke="riskIconColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        <div class="metric-info">
          <span class="metric-label">Risk score</span>
          <span class="metric-value" :style="{ color: riskIconColor }">{{ riskScore ?? '—' }}</span>
          <span class="metric-sub">{{ riskLabel }}</span>
        </div>
      </div>
      <div class="metric-card metric-critical">
        <div class="metric-icon-wrap" style="background:rgba(239,68,68,0.12);">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        </div>
        <div class="metric-info">
          <span class="metric-label">Critical</span>
          <span class="metric-value" style="color:#f87171;">{{ lastScan?.critical ?? '—' }}</span>
          <span class="metric-sub">needs immediate action</span>
        </div>
      </div>
    </div>

    <!-- Charts row -->
    <div class="charts-grid">
      <div class="card chart-card">
        <h2>Findings by severity</h2>
        <div class="chart-wrap donut-wrap">
          <canvas ref="donutCanvas" width="200" height="200"></canvas>
          <div class="donut-center" v-if="lastScan">
            <span class="donut-num">{{ lastScan.findings_count || 0 }}</span>
            <span class="donut-lbl">total</span>
          </div>
          <div class="donut-center" v-else>
            <span class="donut-num" style="color:var(--text-muted);font-size:1rem;">No data</span>
          </div>
        </div>
        <div class="legend">
          <div class="legend-item"><span class="legend-dot" style="background:#ef4444;"></span>Critical <strong>{{ lastScan?.critical ?? 0 }}</strong></div>
          <div class="legend-item"><span class="legend-dot" style="background:#f97316;"></span>High <strong>{{ lastScan?.high ?? 0 }}</strong></div>
          <div class="legend-item"><span class="legend-dot" style="background:#eab308;"></span>Medium <strong>{{ lastScan?.medium ?? 0 }}</strong></div>
          <div class="legend-item"><span class="legend-dot" style="background:#22c55e;"></span>Low <strong>{{ lastScan?.low ?? 0 }}</strong></div>
        </div>
      </div>

      <div class="card chart-card">
        <h2>Risk score over time</h2>
        <div class="chart-wrap">
          <canvas ref="lineCanvas"></canvas>
        </div>
        <p v-if="cloudHistory.length < 2" class="chart-hint muted">
          {{ cloudHistory.length === 0 ? 'No ' + cloudLabel + ' scans recorded yet.' : 'Run more scans to see the trend.' }}
        </p>
      </div>

      <div class="card chart-card">
        <h2>Findings per scan</h2>
        <div class="chart-wrap">
          <canvas ref="barCanvas"></canvas>
        </div>
        <p v-if="!cloudHistory.length" class="chart-hint muted">No {{ cloudLabel }} history yet.</p>
      </div>
    </div>

    <!-- Remediation Progress Panel -->
    <div class="card remediation-panel" v-if="lastScan">
      <div class="card-head">
        <h2>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline;vertical-align:-2px;margin-right:6px;"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          Remediation Progress
        </h2>
        <router-link to="/findings" class="btn btn-secondary btn-sm-text">Manage fixes →</router-link>
      </div>
      <div class="rem-progress-row">
        <div class="rem-progress-bar-wrap">
          <div class="rem-progress-bar" :style="{ width: remediationScore.percentage + '%', background: remProgressColor }"></div>
        </div>
        <span class="rem-progress-pct" :style="{ color: remProgressColor }">{{ remediationScore.percentage }}%</span>
      </div>
      <div class="rem-stats">
        <span class="rem-stat rem-stat-fixed">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          {{ remediationScore.resolved }} fixed
        </span>
        <span class="rem-stat rem-stat-open">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          {{ remediationScore.remaining }} remaining
        </span>
        <span class="rem-stat-score" :style="{ color: remProgressColor }">Score: {{ remediationScore.score }}/100</span>
      </div>
      <p class="muted" style="font-size:0.78rem;margin-top:6px;">Mark findings as fixed in the <router-link to="/findings" style="color:var(--accent);text-decoration:none;">Findings page</router-link> to watch your risk score drop.</p>
    </div>

    <!-- Top recommendations — prioritised by actual findings -->
    <div class="card" v-if="topRecs.length">
      <div class="card-head">
        <h2>
          <span class="cloud-badge-inline" :class="'cloud-' + selectedCloud">{{ cloudLabel }}</span>
          Top recommendations
          <span class="rec-source-label" v-if="hasActualFindings">· ranked by your scan data</span>
        </h2>
        <router-link to="/findings" class="btn btn-secondary btn-sm-text">View all findings →</router-link>
      </div>
      <p class="muted" style="margin-bottom:14px;">
        <template v-if="hasActualFindings">Sorted by severity × number of affected resources from your latest scan.</template>
        <template v-else>Highest-priority actions for your {{ cloudLabel }} environment.</template>
      </p>
      <div class="recs-list">
        <div v-for="(rec, i) in topRecs" :key="i" class="rec-item" :class="'rec-sev-' + (rec.severity || rec.recommendation?.severity)">
          <div class="rec-num">{{ i + 1 }}</div>
          <div class="rec-content">
            <div class="rec-top">
              <span class="rec-title">{{ rec.title }}</span>
              <span v-if="rec.count > 1" class="rec-count-badge">{{ rec.count }} resources</span>
              <span class="rec-badge" :class="'badge-' + (rec.severity || rec.recommendation?.severity)">{{ rec.severity || rec.recommendation?.severity }}</span>
            </div>
            <p class="rec-what">{{ rec.recommendation?.what || rec.what }}</p>
            <p class="rec-fix-first">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
              {{ (rec.recommendation?.fix || rec.fix || [])[0] }}
            </p>
          </div>
          <a v-if="rec.recommendation?.docs || rec.docs" :href="rec.recommendation?.docs || rec.docs" target="_blank" rel="noopener" class="rec-docs-btn" title="Docs">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
          </a>
        </div>
      </div>
    </div>

    <!-- Quick Wins panel -->
    <div class="card quick-wins-card" v-if="quickWins.length">
      <div class="card-head">
        <h2>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline;vertical-align:-2px;margin-right:6px;"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
          Quick Wins
        </h2>
        <span class="quick-wins-badge">Low effort · High impact</span>
      </div>
      <p class="muted" style="margin-bottom:14px;">These medium/low severity issues are fast to fix and meaningfully improve your security posture.</p>
      <div class="recs-list">
        <div v-for="(rec, i) in quickWins" :key="i" class="rec-item rec-item-qw" :class="'rec-sev-' + rec.severity">
          <div class="qw-icon">⚡</div>
          <div class="rec-content">
            <div class="rec-top">
              <span class="rec-title">{{ rec.title }}</span>
              <span v-if="rec.count > 1" class="rec-count-badge">{{ rec.count }} resources</span>
              <span class="rec-badge" :class="'badge-' + rec.severity">{{ rec.severity }}</span>
            </div>
            <p class="rec-fix-first">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
              {{ (rec.recommendation?.fix || [])[0] || 'See finding for details.' }}
            </p>
          </div>
          <a v-if="rec.recommendation?.docs" :href="rec.recommendation.docs" target="_blank" rel="noopener" class="rec-docs-btn" title="Docs">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
          </a>
        </div>
      </div>
    </div>

    <!-- No-scan state for this cloud -->
    <div v-else-if="!cloudHistory.length" class="card no-scan-card">
      <div class="no-scan-inner">
        <span class="no-scan-icon" v-html="currentCloudObj.icon"></span>
        <div>
          <h3>No {{ cloudLabel }} scans yet</h3>
          <p class="muted">Run a security scan for {{ cloudLabel }} to see recommendations, charts, and findings here.</p>
          <router-link to="/security/scan" class="btn btn-primary" style="margin-top:10px;">Run {{ cloudLabel }} Scan</router-link>
        </div>
      </div>
    </div>

    <!-- Quick actions + Status -->
    <div class="bottom-grid">
      <div class="card">
        <h2>Quick actions</h2>
        <div class="quick-actions">
          <router-link to="/security/scan"            class="qa-btn"><span class="qa-icon">🔍</span><span>Security Scan</span></router-link>
          <router-link to="/findings"                 class="qa-btn"><span class="qa-icon">📋</span><span>Findings</span></router-link>
          <router-link to="/compliance"               class="qa-btn"><span class="qa-icon">✅</span><span>Compliance</span></router-link>
          <router-link to="/security/vulnerabilities" class="qa-btn"><span class="qa-icon">🛡️</span><span>Vulnerabilities</span></router-link>
          <router-link to="/audit/assets"             class="qa-btn"><span class="qa-icon">📦</span><span>Assets</span></router-link>
          <router-link to="/scan-history"             class="qa-btn"><span class="qa-icon">📅</span><span>Scan History</span></router-link>
          <router-link to="/security/attack-paths"    class="qa-btn"><span class="qa-icon">⛓</span><span>Attack Paths</span></router-link>
          <router-link :to="{ path: '/setup', query: { cloud: selectedCloud } }" class="qa-btn"><span class="qa-icon">⚙️</span><span>Setup</span></router-link>
        </div>
        <p class="palette-hint muted">Tip: press <kbd>Ctrl+K</kbd> to open the command palette.</p>
      </div>
      <div class="card" v-if="cloudStatus">
        <h2>{{ cloudLabel }} connection</h2>
        <div class="status-block">
          <span class="status-cloud">{{ cloudLabel }}</span>
          <span class="status-mode" :class="cloudStatus.mode !== 'none' ? 'status-ok' : 'status-none'">
            {{ cloudStatus.mode === 'none' ? 'Not configured' : cloudStatus.mode }}
          </span>
        </div>
        <p class="muted" style="font-size:0.82rem;" v-if="cloudStatus.region">Region: <strong>{{ cloudStatus.region }}</strong></p>
        <p class="muted" style="font-size:0.82rem;" v-if="cloudStatus.project_id">Project: <strong>{{ cloudStatus.project_id }}</strong></p>
        <p class="muted" style="font-size:0.82rem;" v-if="cloudStatus.subscription_id">Subscription: <strong>{{ cloudStatus.subscription_id }}</strong></p>
        <router-link :to="{ path: '/setup', query: { cloud: selectedCloud } }" class="btn btn-secondary" style="margin-top:10px;font-size:0.82rem;padding:6px 12px;">
          {{ cloudStatus.mode === 'none' ? 'Configure ' + cloudLabel : 'Update credentials' }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { Chart, ArcElement, DoughnutController, LineElement, LineController, PointElement, LinearScale, CategoryScale, BarElement, BarController, Tooltip, Legend, Filler } from 'chart.js'
import api from '../api'
import { getTopRecsForCloud, RECOMMENDATIONS } from '../utils/recommendations'
import { getPrioritisedRecs, getQuickWins, computeRemediationScore } from '../utils/remediationStore'

Chart.register(ArcElement, DoughnutController, LineElement, LineController, PointElement, LinearScale, CategoryScale, BarElement, BarController, Tooltip, Legend, Filler)

const CLOUDS = [
  {
    id: 'aws', label: 'AWS',
    icon: `<svg width="20" height="20" viewBox="0 0 80 48" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M22.9 32.2c-4.5 2.4-9.4 3.7-14.5 3.7C3.8 35.9 0 32.1 0 27.3c0-5.3 4.5-9.6 10.7-10.2-.3-1.1-.5-2.3-.5-3.6C10.2 6.1 15.9 1 22.9 1c3.4 0 6.5 1.2 8.9 3.2 2.2-4.3 6.7-7.2 11.7-7.2 4.3 0 8.2 1.9 10.8 5 1.9-.7 3.9-1.1 6-1.1C68 1 75 8 75 16.8c0 1.8-.3 3.5-.8 5.1C77.4 23.5 80 27 80 31.1 80 36.8 75.3 41 69.2 41H22.9z" fill="#FF9900"/></svg>`,
    accentColor: '#FF9900',
    tabBg: 'rgba(255,153,0,0.08)',
    tabActiveBg: 'rgba(255,153,0,0.18)',
    tabBorder: 'rgba(255,153,0,0.3)',
  },
  {
    id: 'gcp', label: 'Google Cloud',
    icon: `<svg width="20" height="20" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><path fill="#4285F4" d="M30.2 17.8H24v4.2h6.9c-.7 3.7-4 6.5-7.9 6.5-4.5 0-8.2-3.7-8.2-8.2s3.7-8.2 8.2-8.2c2.1 0 4 .8 5.5 2.1l3-3C29 8.6 26.7 7.5 24 7.5c-7.5 0-13.5 6-13.5 13.5S16.5 34.5 24 34.5c7.2 0 12.8-5 12.8-13.5 0-.8-.1-1.5-.2-2.2l-6.4-1z"/><path fill="#EA4335" d="M12.8 30.6l-3 3C12 35.8 14.7 37 17.8 37c.8 0 1.5-.1 2.2-.2l-1-3.9c-.5.1-1 .2-1.5.2-1.7 0-3.3-.5-4.7-1.4l-1 -1.1z"/><circle fill="#FBBC05" cx="24" cy="21" r="3"/></svg>`,
    accentColor: '#4285F4',
    tabBg: 'rgba(66,133,244,0.08)',
    tabActiveBg: 'rgba(66,133,244,0.18)',
    tabBorder: 'rgba(66,133,244,0.3)',
  },
  {
    id: 'azure', label: 'Azure',
    icon: `<svg width="20" height="20" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><path fill="#0078D4" d="M27 4L13 28l9 5-7 7h16l7-36z"/><path fill="#50E6FF" d="M27 4L4 34l9-1 7-7-3-5z"/></svg>`,
    accentColor: '#0078D4',
    tabBg: 'rgba(0,120,212,0.08)',
    tabActiveBg: 'rgba(0,120,212,0.18)',
    tabBorder: 'rgba(0,120,212,0.3)',
  },
]

const statusMap    = ref(null)
const summaryData  = ref(null)
const selectedCloud = ref('aws')
const allHistory   = ref([])

const donutCanvas  = ref(null)
const lineCanvas   = ref(null)
const barCanvas    = ref(null)

let donutChart = null
let lineChart  = null
let barChart   = null

const currentCloudObj = computed(() => CLOUDS.find(c => c.id === selectedCloud.value) || CLOUDS[0])
const cloudLabel      = computed(() => currentCloudObj.value.label)
const cloudStatus     = computed(() => statusMap.value ? (statusMap.value[selectedCloud.value] || null) : null)
const summaryCloud    = computed(() => (summaryData.value?.cloud || '').toLowerCase() === selectedCloud.value)

// History filtered to selected cloud
const cloudHistory = computed(() =>
  allHistory.value.filter(s => (s.cloud || 'aws').toLowerCase() === selectedCloud.value)
)
const lastScan = computed(() => cloudHistory.value[0] || null)

function cloudHistoryCount(id) {
  return allHistory.value.filter(s => (s.cloud || 'aws').toLowerCase() === id).length
}

const riskScore = computed(() => {
  const s = (summaryCloud.value ? summaryData.value?.summary?.risk_score : null) ?? lastScan.value?.risk_score
  return s != null ? parseFloat(s) : null
})
const riskIconColor = computed(() => {
  const n = riskScore.value
  if (n == null) return '#94a3b8'
  if (n >= 80) return '#ef4444'
  if (n >= 60) return '#f97316'
  if (n >= 40) return '#eab308'
  return '#22c55e'
})
const riskIconBg = computed(() => {
  const n = riskScore.value
  if (n == null) return 'rgba(148,163,184,0.1)'
  if (n >= 80) return 'rgba(239,68,68,0.12)'
  if (n >= 60) return 'rgba(249,115,22,0.12)'
  if (n >= 40) return 'rgba(234,179,8,0.12)'
  return 'rgba(34,197,94,0.12)'
})
const riskLabel = computed(() => {
  const n = riskScore.value
  if (n == null) return 'no data'
  if (n >= 80) return 'critical'
  if (n >= 60) return 'high risk'
  if (n >= 40) return 'medium risk'
  return 'low risk'
})

function formatRelative(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

// Collect all findings across history for the selected cloud
const allCloudFindings = computed(() => {
  const findings = []
  for (const scan of cloudHistory.value) {
    if (Array.isArray(scan.findings)) {
      for (const f of scan.findings) {
        findings.push({ ...f, cloud: scan.cloud || selectedCloud.value })
      }
    }
  }
  return findings
})

const hasActualFindings = computed(() => allCloudFindings.value.length > 0)

// Top recommendations — prioritised by actual finding frequency × severity
const topRecs = computed(() => {
  if (hasActualFindings.value) {
    return getPrioritisedRecs(allCloudFindings.value, RECOMMENDATIONS, selectedCloud.value, 5)
  }
  // Fallback: use static lookup ranked by last scan severity counts
  return getTopRecsForCloud(selectedCloud.value, {
    critical: lastScan.value?.critical || 0,
    high:     lastScan.value?.high || 0,
    medium:   lastScan.value?.medium || 0,
  }, 5).map(rec => ({ title: rec?.title, severity: rec?.severity, recommendation: rec, count: 0 }))
})

// Quick wins — medium/low unfixed findings
const quickWins = computed(() =>
  hasActualFindings.value
    ? getQuickWins(allCloudFindings.value, RECOMMENDATIONS, selectedCloud.value, 4)
    : []
)

// Remediation progress
const remediationScore = computed(() =>
  computeRemediationScore(allCloudFindings.value)
)
const remProgressColor = computed(() => {
  const pct = remediationScore.value.percentage
  if (pct >= 75) return '#22c55e'
  if (pct >= 40) return '#eab308'
  return '#f97316'
})

function switchCloud(id) {
  selectedCloud.value = id
  try { localStorage.setItem('cspm_cloud', id) } catch (_) {}
}

// ── Chart builders ───────────────────────────────────────────────────────────
function buildDonut() {
  if (!donutCanvas.value) return
  const scan = lastScan.value
  const data = scan ? [scan.critical||0, scan.high||0, scan.medium||0, scan.low||0] : [1,1,1,1]
  const isEmpty = !scan
  if (donutChart) donutChart.destroy()
  donutChart = new Chart(donutCanvas.value, {
    type: 'doughnut',
    data: {
      labels: ['Critical', 'High', 'Medium', 'Low'],
      datasets: [{
        data,
        backgroundColor: isEmpty
          ? ['rgba(148,163,184,0.12)','rgba(148,163,184,0.08)','rgba(148,163,184,0.06)','rgba(148,163,184,0.04)']
          : ['#ef4444','#f97316','#eab308','#22c55e'],
        borderColor: 'transparent',
        hoverOffset: 4,
      }],
    },
    options: {
      cutout: '68%',
      plugins: { legend: { display: false }, tooltip: { enabled: !isEmpty } },
      animation: { duration: 500 },
    },
  })
}

function buildLine() {
  if (!lineCanvas.value) return
  if (lineChart) { lineChart.destroy(); lineChart = null }
  if (cloudHistory.value.length < 2) return
  const sliced = [...cloudHistory.value].reverse().slice(-10)
  const labels = sliced.map(s => {
    const d = new Date(s.timestamp)
    return `${d.getMonth()+1}/${d.getDate()}`
  })
  const accentColor = currentCloudObj.value.accentColor
  lineChart = new Chart(lineCanvas.value, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Risk score',
        data: sliced.map(s => parseFloat(s.risk_score) || 0),
        borderColor: accentColor,
        backgroundColor: accentColor + '18',
        pointBackgroundColor: accentColor,
        tension: 0.35,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 6,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(148,163,184,0.08)' }, ticks: { color: '#64748b', font: { size: 11 } } },
        y: { grid: { color: 'rgba(148,163,184,0.08)' }, ticks: { color: '#64748b', font: { size: 11 } }, min: 0, max: 100 },
      },
      animation: { duration: 400 },
    },
  })
}

function buildBar() {
  if (!barCanvas.value) return
  if (barChart) { barChart.destroy(); barChart = null }
  if (!cloudHistory.value.length) return
  const sliced = [...cloudHistory.value].reverse().slice(-8)
  const labels = sliced.map(s => {
    const d = new Date(s.timestamp)
    return `${d.getMonth()+1}/${d.getDate()}`
  })
  barChart = new Chart(barCanvas.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Critical', data: sliced.map(s => s.critical||0), backgroundColor: 'rgba(239,68,68,0.75)',  borderRadius: 3, stack: 'sev' },
        { label: 'High',     data: sliced.map(s => s.high||0),     backgroundColor: 'rgba(249,115,22,0.75)', borderRadius: 3, stack: 'sev' },
        { label: 'Medium',   data: sliced.map(s => s.medium||0),   backgroundColor: 'rgba(234,179,8,0.75)',  borderRadius: 3, stack: 'sev' },
        { label: 'Low',      data: sliced.map(s => s.low||0),      backgroundColor: 'rgba(34,197,94,0.75)',  borderRadius: 3, stack: 'sev' },
      ],
    },
    options: {
      plugins: {
        legend: { display: true, position: 'bottom', labels: { color: '#64748b', font: { size: 11 }, boxWidth: 12, padding: 10 } },
      },
      scales: {
        x: { stacked: true, grid: { color: 'rgba(148,163,184,0.08)' }, ticks: { color: '#64748b', font: { size: 11 } } },
        y: { stacked: true, grid: { color: 'rgba(148,163,184,0.08)' }, ticks: { color: '#64748b', font: { size: 11 } } },
      },
      animation: { duration: 400 },
    },
  })
}

function rebuildCharts() {
  nextTick(() => {
    buildDonut()
    buildLine()
    buildBar()
  })
}

// Rebuild charts whenever the cloud tab changes
watch(selectedCloud, rebuildCharts)

onMounted(async () => {
  try { selectedCloud.value = localStorage.getItem('cspm_cloud') || 'aws' } catch (_) {}
  try { allHistory.value = JSON.parse(localStorage.getItem('cspm_scan_history') || '[]') } catch (_) {}
  try { statusMap.value = await api.getStatus() } catch { statusMap.value = { aws: { mode: 'none' }, gcp: { mode: 'none' }, azure: { mode: 'none' } } }
  try { summaryData.value = await api.getSummary() } catch { summaryData.value = null }
  rebuildCharts()
})
</script>

<style scoped>
.dash-header { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 20px; }
.dash-header-actions { display: flex; gap: 8px; }

/* ── Cloud tabs ── */
.cloud-tabs { display: flex; gap: 6px; margin-bottom: 22px; flex-wrap: wrap; }
.cloud-tab {
  display: flex; align-items: center; gap: 8px; padding: 9px 16px;
  border-radius: 10px; border: 1px solid var(--border); cursor: pointer;
  background: rgba(15,23,42,0.4); color: var(--text-muted);
  font-size: 0.88rem; font-weight: 500; transition: all 0.15s;
}
.cloud-tab:hover { background: rgba(255,255,255,0.06); color: var(--text); }
.cloud-tab.active { color: var(--text); font-weight: 600; }
.cloud-tab-aws.active    { background: rgba(255,153,0,0.14); border-color: rgba(255,153,0,0.35); }
.cloud-tab-gcp.active    { background: rgba(66,133,244,0.14); border-color: rgba(66,133,244,0.35); }
.cloud-tab-azure.active  { background: rgba(0,120,212,0.14);  border-color: rgba(0,120,212,0.35); }
.cloud-tab-icon { display: flex; align-items: center; flex-shrink: 0; }
.cloud-tab-label { white-space: nowrap; }
.cloud-tab-badge { padding: 1px 7px; border-radius: 20px; font-size: 0.68rem; font-weight: 700; background: rgba(14,165,233,0.15); color: var(--accent); }

/* ── KPI cards ── */
.metric-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 14px; margin-bottom: 22px; }
.metric-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 16px; display: flex; align-items: center; gap: 14px; transition: box-shadow 0.15s; }
.metric-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
.metric-card.metric-scan     { border-left: 3px solid #0ea5e9; }
.metric-card.metric-findings { border-left: 3px solid #6366f1; }
.metric-card.metric-risk     { border-left: 3px solid #eab308; }
.metric-card.metric-critical { border-left: 3px solid #ef4444; }
.metric-icon-wrap { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.metric-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.metric-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); font-weight: 700; }
.metric-value { font-size: 1.35rem; font-weight: 700; color: var(--text); line-height: 1.2; }
.metric-sub   { font-size: 0.72rem; color: var(--text-muted); }

/* ── Charts ── */
.charts-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 18px; margin-bottom: 22px; }
.chart-card h2 { font-size: 0.9rem; margin: 0 0 14px; }
.chart-wrap { position: relative; height: 200px; display: flex; align-items: center; justify-content: center; }
.donut-wrap { position: relative; }
.donut-center { position: absolute; display: flex; flex-direction: column; align-items: center; justify-content: center; pointer-events: none; }
.donut-num { font-size: 1.6rem; font-weight: 700; color: var(--text); line-height: 1; }
.donut-lbl { font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.legend { display: flex; flex-wrap: wrap; gap: 8px 16px; margin-top: 12px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; color: var(--text-muted); }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.legend-item strong { color: var(--text); margin-left: 2px; }
.chart-hint { font-size: 0.78rem; margin-top: 8px; }

/* ── Top recommendations ── */
.card-head { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 4px; }
.btn-sm-text { font-size: 0.82rem; padding: 6px 12px; }
.cloud-badge-inline { display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; margin-right: 6px; }
.cloud-badge-inline.cloud-aws   { background: rgba(255,153,0,0.15); color: #fb923c; }
.cloud-badge-inline.cloud-gcp   { background: rgba(66,133,244,0.15); color: #60a5fa; }
.cloud-badge-inline.cloud-azure { background: rgba(0,120,212,0.15);  color: #93c5fd; }
.recs-list { display: flex; flex-direction: column; gap: 8px; }
.rec-item { display: flex; align-items: flex-start; gap: 14px; padding: 14px 16px; border-radius: 10px; background: rgba(15,23,42,0.4); border: 1px solid var(--border); transition: background 0.15s, border-color 0.15s; }
.rec-item:hover { background: rgba(14,165,233,0.05); border-color: rgba(14,165,233,0.2); }
.rec-item.rec-sev-critical { border-left: 3px solid #ef4444; }
.rec-item.rec-sev-high     { border-left: 3px solid #f97316; }
.rec-item.rec-sev-medium   { border-left: 3px solid #eab308; }
.rec-item.rec-sev-low      { border-left: 3px solid #22c55e; }
.rec-num { width: 26px; height: 26px; border-radius: 50%; background: rgba(14,165,233,0.15); color: var(--accent); font-size: 0.78rem; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px; }
.rec-content { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.rec-top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.rec-title { font-size: 0.9rem; font-weight: 600; color: var(--text); }
.rec-badge { padding: 2px 8px; border-radius: 10px; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; }
.badge-critical { background: rgba(239,68,68,0.15); color: #fca5a5; }
.badge-high     { background: rgba(249,115,22,0.15); color: #fdba74; }
.badge-medium   { background: rgba(245,158,11,0.15); color: #fcd34d; }
.badge-low      { background: rgba(34,197,94,0.15);  color: #86efac; }
.rec-what     { font-size: 0.8rem; color: var(--text-muted); margin: 0; line-height: 1.4; }
.rec-fix-first { font-size: 0.78rem; color: var(--accent); margin: 0; display: flex; align-items: flex-start; gap: 6px; line-height: 1.4; }
.rec-fix-first svg { flex-shrink: 0; margin-top: 2px; }
.rec-docs-btn { display: flex; align-items: center; justify-content: center; width: 30px; height: 30px; border-radius: 8px; background: rgba(148,163,184,0.08); color: var(--text-muted); transition: all 0.15s; flex-shrink: 0; margin-top: 2px; text-decoration: none; }
.rec-docs-btn:hover { background: rgba(14,165,233,0.12); color: var(--accent); }

/* ── No scan state ── */
.no-scan-card { text-align: left; }
.no-scan-inner { display: flex; align-items: flex-start; gap: 20px; padding: 10px 0; flex-wrap: wrap; }
.no-scan-icon { font-size: 2.5rem; display: flex; align-items: center; flex-shrink: 0; }
.no-scan-inner h3 { margin: 0 0 6px; font-size: 1.05rem; }
.no-scan-inner p  { margin: 0; font-size: 0.88rem; }

/* ── Bottom grid ── */
.bottom-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 18px; }
@media (max-width: 680px) { .bottom-grid { grid-template-columns: 1fr; } }
.quick-actions { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; margin-bottom: 14px; }
.qa-btn { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 12px 8px; border-radius: 10px; background: rgba(15,23,42,0.5); border: 1px solid var(--border); text-decoration: none; color: var(--text-muted); font-size: 0.78rem; font-weight: 500; transition: all 0.15s; text-align: center; }
.qa-btn:hover { background: rgba(14,165,233,0.1); color: var(--text); border-color: rgba(14,165,233,0.2); }
.qa-icon { font-size: 1.3rem; }
.palette-hint { font-size: 0.78rem; }
.palette-hint kbd { background: rgba(148,163,184,0.1); border: 1px solid rgba(148,163,184,0.2); border-radius: 4px; padding: 1px 6px; font-size: 0.75rem; font-family: inherit; }
.status-block { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.status-cloud { font-weight: 700; font-size: 0.95rem; }
.status-mode { padding: 4px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
.status-ok   { background: rgba(34,197,94,0.12); color: #86efac; }
.status-none { background: rgba(148,163,184,0.1); color: #94a3b8; }

/* ── Remediation Panel ── */
.remediation-panel { margin-bottom: 22px; }
.rem-progress-row { display: flex; align-items: center; gap: 12px; margin: 12px 0 8px; }
.rem-progress-bar-wrap { flex: 1; height: 10px; background: rgba(148,163,184,0.12); border-radius: 10px; overflow: hidden; }
.rem-progress-bar { height: 100%; border-radius: 10px; transition: width 0.4s ease, background 0.3s; }
.rem-progress-pct { font-size: 0.88rem; font-weight: 700; flex-shrink: 0; }
.rem-stats { display: flex; gap: 16px; flex-wrap: wrap; font-size: 0.8rem; }
.rem-stat { display: flex; align-items: center; gap: 5px; color: var(--text-muted); }
.rem-stat-fixed { color: #86efac; }
.rem-stat-open  { color: #fdba74; }
.rem-stat-score { font-weight: 700; }

/* ── Quick Wins ── */
.quick-wins-card { margin-bottom: 22px; }
.quick-wins-badge { padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; background: rgba(34,197,94,0.12); color: #86efac; }
.rec-item-qw { background: rgba(34,197,94,0.04); border-color: rgba(34,197,94,0.15); }
.rec-item-qw:hover { background: rgba(34,197,94,0.08); border-color: rgba(34,197,94,0.25); }
.qw-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 2px; }
.rec-count-badge { padding: 1px 7px; border-radius: 10px; font-size: 0.68rem; font-weight: 700; background: rgba(14,165,233,0.12); color: var(--accent); }
.rec-source-label { font-size: 0.72rem; font-weight: 400; color: var(--text-muted); margin-left: 4px; }
</style>
