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
        </div>
      </div>
      <div class="metric-card metric-findings">
        <div class="metric-icon-wrap" style="background:rgba(99,102,241,0.12);">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        </div>
        <div class="metric-info">
          <span class="metric-label">Total findings</span>
          <span class="metric-value">{{ summaryData?.findings_count ?? lastScan?.findings_count ?? '—' }}</span>
          <span class="metric-sub">from latest scan</span>
        </div>
      </div>
      <div class="metric-card metric-risk">
        <div class="metric-icon-wrap" :style="{ background: riskIconBg }">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" :stroke="riskIconColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        <div class="metric-info">
          <span class="metric-label">Risk score</span>
          <span class="metric-value" :style="{ color: riskIconColor }">{{ summaryData?.summary?.risk_score ?? lastScan?.risk_score ?? '—' }}</span>
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
            <span class="donut-num">{{ (lastScan.findings_count || 0) }}</span>
            <span class="donut-lbl">total</span>
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
        <p v-if="history.length < 2" class="chart-hint muted">Run more scans to see trend data.</p>
      </div>

      <div class="card chart-card">
        <h2>Scan history</h2>
        <div class="chart-wrap">
          <canvas ref="barCanvas"></canvas>
        </div>
        <p v-if="!history.length" class="chart-hint muted">No history yet.</p>
      </div>
    </div>

    <!-- Top recommendations -->
    <div class="card" v-if="topRecs.length">
      <div class="card-head">
        <h2>Top recommendations</h2>
        <router-link to="/findings" class="btn btn-secondary btn-sm-text">View all findings →</router-link>
      </div>
      <p class="muted" style="margin-bottom:14px;">Highest-priority actions based on the latest scan.</p>
      <div class="recs-list">
        <div v-for="(rec, i) in topRecs" :key="i" class="rec-item" :class="'rec-sev-' + rec.severity">
          <div class="rec-num">{{ i + 1 }}</div>
          <div class="rec-content">
            <div class="rec-top">
              <span class="rec-title">{{ rec.title }}</span>
              <span class="rec-badge" :class="'badge-' + rec.severity">{{ rec.severity }}</span>
            </div>
            <p class="rec-what">{{ rec.what }}</p>
            <p class="rec-fix-first">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
              {{ rec.fix[0] }}
            </p>
          </div>
          <a v-if="rec.docs" :href="rec.docs" target="_blank" rel="noopener" class="rec-docs-btn" title="AWS docs">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
          </a>
        </div>
      </div>
    </div>

    <!-- Quick actions + Status -->
    <div class="bottom-grid">
      <div class="card">
        <h2>Quick actions</h2>
        <div class="quick-actions">
          <router-link to="/security/scan"         class="qa-btn"><span class="qa-icon">🔍</span><span>Security Scan</span></router-link>
          <router-link to="/findings"              class="qa-btn"><span class="qa-icon">📋</span><span>Findings</span></router-link>
          <router-link to="/compliance"            class="qa-btn"><span class="qa-icon">✅</span><span>Compliance</span></router-link>
          <router-link to="/security/vulnerabilities" class="qa-btn"><span class="qa-icon">🛡️</span><span>Vulnerabilities</span></router-link>
          <router-link to="/audit/assets"          class="qa-btn"><span class="qa-icon">📦</span><span>Assets</span></router-link>
          <router-link to="/scan-history"          class="qa-btn"><span class="qa-icon">📅</span><span>Scan History</span></router-link>
          <router-link to="/security/attack-paths" class="qa-btn"><span class="qa-icon">⛓</span><span>Attack Paths</span></router-link>
          <router-link :to="{ path: '/setup', query: { cloud: selectedCloud } }" class="qa-btn"><span class="qa-icon">⚙️</span><span>Setup</span></router-link>
        </div>
        <p class="palette-hint muted">Tip: press <kbd>Ctrl+K</kbd> to open the command palette.</p>
      </div>
      <div class="card" v-if="cloudStatus">
        <h2>Cloud status</h2>
        <div class="status-block">
          <span class="status-cloud">{{ selectedCloudLabel }}</span>
          <span class="status-mode" :class="cloudStatus.mode !== 'none' ? 'status-ok' : 'status-none'">
            {{ cloudStatus.mode === 'none' ? 'Not configured' : cloudStatus.mode }}
          </span>
        </div>
        <p class="muted" style="font-size:0.82rem;" v-if="cloudStatus.region">Region: <strong>{{ cloudStatus.region }}</strong></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Chart, ArcElement, DoughnutController, LineElement, LineController, PointElement, LinearScale, CategoryScale, BarElement, BarController, Tooltip, Legend, Filler } from 'chart.js'
import api from '../api'
import { RECOMMENDATIONS, SEV_ORDER } from '../utils/recommendations'

Chart.register(ArcElement, DoughnutController, LineElement, LineController, PointElement, LinearScale, CategoryScale, BarElement, BarController, Tooltip, Legend, Filler)

const statusMap    = ref(null)
const summaryData  = ref(null)
const selectedCloud = ref('aws')
const history      = ref([])

const donutCanvas  = ref(null)
const lineCanvas   = ref(null)
const barCanvas    = ref(null)

let donutChart = null
let lineChart  = null
let barChart   = null

const selectedCloudLabel = computed(() => ({ aws: 'AWS', gcp: 'GCP', azure: 'Azure' }[selectedCloud.value] || 'Cloud'))
const cloudStatus = computed(() => statusMap.value ? (statusMap.value[selectedCloud.value] || statusMap.value.aws) : null)

const lastScan = computed(() => history.value[0] || null)

const riskScore = computed(() => {
  const s = summaryData.value?.summary?.risk_score ?? lastScan.value?.risk_score
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

// Top 5 recommendations built from saved history critical/high findings
const topRecs = computed(() => {
  const scan = lastScan.value
  if (!scan) return []
  const candidates = []
  if ((scan.critical || 0) > 0) {
    candidates.push(RECOMMENDATIONS['sg.ssh_open'])
    candidates.push(RECOMMENDATIONS['s3.public_access'])
    candidates.push(RECOMMENDATIONS['iam.wildcard_action'])
  }
  if ((scan.high || 0) > 0) {
    candidates.push(RECOMMENDATIONS['s3.no_encryption'])
    candidates.push(RECOMMENDATIONS['rds.publicly_accessible'])
    candidates.push(RECOMMENDATIONS['iam.unused_keys'])
    candidates.push(RECOMMENDATIONS['guardduty.disabled'])
  }
  if ((scan.medium || 0) > 0) {
    candidates.push(RECOMMENDATIONS['kms.no_rotation'])
    candidates.push(RECOMMENDATIONS['vpc.no_flow_logs'])
  }
  const seen = new Set()
  return candidates.filter(r => {
    if (!r || seen.has(r.title)) return false
    seen.add(r.title)
    return true
  }).slice(0, 5)
})

function buildDonut() {
  if (!donutCanvas.value) return
  const scan = lastScan.value
  const data = scan
    ? [scan.critical||0, scan.high||0, scan.medium||0, scan.low||0]
    : [1, 1, 1, 1]
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
      animation: { duration: 600 },
    },
  })
}

function buildLine() {
  if (!lineCanvas.value || history.value.length < 2) return
  const sliced = [...history.value].reverse().slice(-10)
  const labels = sliced.map(s => {
    const d = new Date(s.timestamp)
    return `${d.getMonth()+1}/${d.getDate()}`
  })
  const scores = sliced.map(s => parseFloat(s.risk_score) || 0)
  if (lineChart) lineChart.destroy()
  lineChart = new Chart(lineCanvas.value, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Risk score',
        data: scores,
        borderColor: '#0ea5e9',
        backgroundColor: 'rgba(14,165,233,0.08)',
        pointBackgroundColor: '#0ea5e9',
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
      animation: { duration: 500 },
    },
  })
}

function buildBar() {
  if (!barCanvas.value || !history.value.length) return
  const sliced = [...history.value].reverse().slice(-8)
  const labels = sliced.map(s => {
    const d = new Date(s.timestamp)
    return `${d.getMonth()+1}/${d.getDate()}`
  })
  if (barChart) barChart.destroy()
  barChart = new Chart(barCanvas.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Critical', data: sliced.map(s => s.critical||0), backgroundColor: 'rgba(239,68,68,0.7)',  borderRadius: 4, stack: 'sev' },
        { label: 'High',     data: sliced.map(s => s.high||0),     backgroundColor: 'rgba(249,115,22,0.7)', borderRadius: 4, stack: 'sev' },
        { label: 'Medium',   data: sliced.map(s => s.medium||0),   backgroundColor: 'rgba(234,179,8,0.7)',  borderRadius: 4, stack: 'sev' },
        { label: 'Low',      data: sliced.map(s => s.low||0),      backgroundColor: 'rgba(34,197,94,0.7)',  borderRadius: 4, stack: 'sev' },
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
      animation: { duration: 500 },
    },
  })
}

onMounted(async () => {
  try { selectedCloud.value = localStorage.getItem('cspm_cloud') || 'aws' } catch (_) {}
  try { history.value = JSON.parse(localStorage.getItem('cspm_scan_history') || '[]') } catch (_) {}
  try { statusMap.value = await api.getStatus() } catch { statusMap.value = { aws: { mode: 'none' }, gcp: { mode: 'none' }, azure: { mode: 'none' } } }
  try { summaryData.value = await api.getSummary() } catch { summaryData.value = null }
  await nextTick()
  buildDonut()
  buildLine()
  buildBar()
})
</script>

<style scoped>
.dash-header { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 22px; }
.dash-header-actions { display: flex; gap: 8px; }
.btn svg { vertical-align: middle; }

/* KPI cards */
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

/* Charts */
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

/* Top recommendations */
.card-head { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 0; }
.btn-sm-text { font-size: 0.82rem; padding: 6px 12px; }
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
.rec-docs-btn { display: flex; align-items: center; justify-content: center; width: 30px; height: 30px; border-radius: 8px; background: rgba(148,163,184,0.08); color: var(--text-muted); transition: background 0.15s, color 0.15s; flex-shrink: 0; margin-top: 2px; text-decoration: none; }
.rec-docs-btn:hover { background: rgba(14,165,233,0.12); color: var(--accent); }

/* Bottom grid */
.bottom-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 18px; }
@media (max-width: 680px) { .bottom-grid { grid-template-columns: 1fr; } }
.quick-actions { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; margin-bottom: 14px; }
.qa-btn { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 12px 8px; border-radius: 10px; background: rgba(15,23,42,0.5); border: 1px solid var(--border); text-decoration: none; color: var(--text-muted); font-size: 0.78rem; font-weight: 500; transition: background 0.15s, color 0.15s; text-align: center; }
.qa-btn:hover { background: rgba(14,165,233,0.1); color: var(--text); border-color: rgba(14,165,233,0.2); }
.qa-icon { font-size: 1.3rem; }
.palette-hint { font-size: 0.78rem; }
.palette-hint kbd { background: rgba(148,163,184,0.1); border: 1px solid rgba(148,163,184,0.2); border-radius: 4px; padding: 1px 6px; font-size: 0.75rem; font-family: inherit; }
.status-block { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.status-cloud { font-weight: 700; font-size: 0.95rem; }
.status-mode { padding: 4px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
.status-ok   { background: rgba(34,197,94,0.12); color: #86efac; }
.status-none { background: rgba(148,163,184,0.1); color: #94a3b8; }
</style>
