<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Scan History</h1>
        <p class="muted">All past security scans saved in this browser session.</p>
      </div>
      <button class="btn btn-danger-sm" @click="showConfirm = true" :disabled="!history.length">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/></svg>
        Clear history
      </button>
    </div>

    <div v-if="!history.length" class="card empty-card">
      <div class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        <p>No scan history yet. Run a Security Scan to see results recorded here.</p>
        <router-link to="/security/scan" class="btn btn-primary">Run Security Scan</router-link>
      </div>
    </div>

    <div v-else class="card" style="padding: 0; overflow: hidden;">
      <table class="history-table">
        <thead>
          <tr>
            <th>Date &amp; Time</th>
            <th>Cloud</th>
            <th>Region</th>
            <th>Findings</th>
            <th>Risk Score</th>
            <th>Critical</th>
            <th>High</th>
            <th>Duration</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(scan, i) in history" :key="i" @click="viewScan(scan)" class="history-row">
            <td class="td-time">
              <span class="time-date">{{ formatDate(scan.timestamp) }}</span>
              <span class="time-clock">{{ formatTime(scan.timestamp) }}</span>
            </td>
            <td><span class="cloud-badge" :class="'cloud-' + scan.cloud">{{ (scan.cloud || 'aws').toUpperCase() }}</span></td>
            <td class="td-mono">{{ scan.region || '—' }}</td>
            <td class="td-num">{{ scan.findings_count ?? '—' }}</td>
            <td class="td-risk">
              <span class="risk-pill" :class="riskClass(scan.risk_score)">{{ scan.risk_score ?? '—' }}</span>
            </td>
            <td><span class="sev-count critical">{{ scan.critical ?? 0 }}</span></td>
            <td><span class="sev-count high">{{ scan.high ?? 0 }}</span></td>
            <td class="td-muted">{{ scan.duration ? scan.duration + 's' : '—' }}</td>
            <td><span class="status-pill" :class="'status-' + (scan.status || 'completed')">{{ scan.status || 'completed' }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detail slide-over -->
    <transition name="slideover">
      <div v-if="selected" class="slideover-wrap" @click.self="selected = null">
        <div class="slideover">
          <div class="slideover-header">
            <h3>Scan Details</h3>
            <button class="close-btn" @click="selected = null">×</button>
          </div>
          <div class="slideover-body">
            <div class="detail-grid">
              <div class="detail-item"><span class="detail-label">Cloud</span><span>{{ (selected.cloud || 'aws').toUpperCase() }}</span></div>
              <div class="detail-item"><span class="detail-label">Region</span><span class="td-mono">{{ selected.region || '—' }}</span></div>
              <div class="detail-item"><span class="detail-label">Date</span><span>{{ formatDate(selected.timestamp) }} {{ formatTime(selected.timestamp) }}</span></div>
              <div class="detail-item"><span class="detail-label">Status</span><span class="status-pill" :class="'status-' + (selected.status||'completed')">{{ selected.status || 'completed' }}</span></div>
              <div class="detail-item"><span class="detail-label">Total Findings</span><span class="big-num">{{ selected.findings_count ?? '—' }}</span></div>
              <div class="detail-item"><span class="detail-label">Risk Score</span><span class="risk-pill" :class="riskClass(selected.risk_score)">{{ selected.risk_score ?? '—' }}</span></div>
            </div>
            <div class="sev-breakdown">
              <div class="sev-bar-item"><span class="sev-label critical">Critical</span><div class="sev-bar"><div class="sev-fill critical" :style="{ width: sevPct(selected, 'critical') }"></div></div><span class="sev-num">{{ selected.critical ?? 0 }}</span></div>
              <div class="sev-bar-item"><span class="sev-label high">High</span><div class="sev-bar"><div class="sev-fill high" :style="{ width: sevPct(selected, 'high') }"></div></div><span class="sev-num">{{ selected.high ?? 0 }}</span></div>
              <div class="sev-bar-item"><span class="sev-label medium">Medium</span><div class="sev-bar"><div class="sev-fill medium" :style="{ width: sevPct(selected, 'medium') }"></div></div><span class="sev-num">{{ selected.medium ?? 0 }}</span></div>
              <div class="sev-bar-item"><span class="sev-label low">Low</span><div class="sev-bar"><div class="sev-fill low" :style="{ width: sevPct(selected, 'low') }"></div></div><span class="sev-num">{{ selected.low ?? 0 }}</span></div>
            </div>
            <router-link to="/findings" class="btn btn-primary" style="margin-top: 16px; display: inline-flex;">View Findings →</router-link>
          </div>
        </div>
      </div>
    </transition>

    <!-- Clear confirmation -->
    <div class="modal-overlay" v-if="showConfirm" @click.self="showConfirm = false">
      <div class="modal">
        <h3>Clear scan history?</h3>
        <p class="muted">This will remove all {{ history.length }} saved scan records.</p>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showConfirm = false">Cancel</button>
          <button class="btn btn-danger-sm" @click="clearHistory">Yes, clear</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const history = ref([])
const selected = ref(null)
const showConfirm = ref(false)

onMounted(loadHistory)

function loadHistory() {
  try {
    history.value = JSON.parse(localStorage.getItem('cspm_scan_history') || '[]')
  } catch (_) { history.value = [] }
}
function clearHistory() {
  localStorage.removeItem('cspm_scan_history')
  history.value = []
  showConfirm.value = false
}
function viewScan(scan) { selected.value = scan }

function formatDate(iso) { return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) }
function formatTime(iso) { return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) }

function riskClass(score) {
  if (!score) return ''
  const n = typeof score === 'number' ? score : parseFloat(score)
  if (n >= 80) return 'risk-critical'
  if (n >= 60) return 'risk-high'
  if (n >= 40) return 'risk-medium'
  return 'risk-low'
}

function sevPct(scan, level) {
  const total = (scan.findings_count || 1)
  const count = scan[level] || 0
  return Math.round((count / total) * 100) + '%'
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.btn-danger-sm {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 14px; border-radius: 7px; font-size: 0.84rem; font-weight: 500;
  background: rgba(239,68,68,0.12); color: #fca5a5;
  border: 1px solid rgba(239,68,68,0.22); cursor: pointer; transition: background 0.15s;
}
.btn-danger-sm:hover:not(:disabled) { background: rgba(239,68,68,0.22); }
.btn-danger-sm:disabled { opacity: 0.35; cursor: not-allowed; }
.empty-card { text-align: center; }
.empty-state { padding: 40px 20px; display: flex; flex-direction: column; align-items: center; gap: 16px; }
.empty-state p { color: var(--text-muted); font-size: 0.9rem; max-width: 320px; }
.history-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.history-table th { padding: 10px 14px; text-align: left; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); border-bottom: 1px solid var(--border); background: var(--bg-el-lo); white-space: nowrap; }
.history-table td { padding: 11px 14px; border-bottom: 1px solid var(--border); vertical-align: middle; }
.history-row { cursor: pointer; transition: background 0.12s; }
.history-row:hover { background: rgba(14,165,233,0.05); }
.history-row:last-child td { border-bottom: none; }
.td-time { white-space: nowrap; }
.time-date { display: block; font-weight: 500; color: var(--text); font-size: 0.82rem; }
.time-clock { display: block; color: var(--text-muted); font-size: 0.76rem; }
.td-mono { font-family: monospace; font-size: 0.82rem; color: var(--text-muted); }
.td-num { font-weight: 600; font-size: 0.95rem; }
.td-muted { color: var(--text-muted); font-size: 0.82rem; }
.cloud-badge { display: inline-block; padding: 3px 9px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; }
.cloud-aws   { background: rgba(249,115,22,0.15); color: #fb923c; }
.cloud-gcp   { background: rgba(59,130,246,0.15);  color: #60a5fa; }
.cloud-azure { background: rgba(99,102,241,0.15);  color: #a5b4fc; }
.td-risk .risk-pill, .risk-pill { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 700; }
.risk-critical { background: rgba(239,68,68,0.15);   color: #fca5a5; }
.risk-high     { background: rgba(249,115,22,0.15);  color: #fdba74; }
.risk-medium   { background: rgba(245,158,11,0.15);  color: #fcd34d; }
.risk-low      { background: rgba(34,197,94,0.15);   color: #86efac; }
.sev-count { display: inline-block; font-weight: 700; font-size: 0.88rem; }
.sev-count.critical { color: #f87171; }
.sev-count.high     { color: #fb923c; }
.status-pill { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.74rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
.status-completed { background: rgba(34,197,94,0.12); color: #86efac; }
.status-failed    { background: rgba(239,68,68,0.12);  color: #fca5a5; }
.status-running   { background: rgba(14,165,233,0.12); color: #7dd3fc; }

/* Slide-over */
.slideover-wrap { position: fixed; inset: 0; z-index: 500; display: flex; justify-content: flex-end; background: rgba(0,0,0,0.4); }
.slideover { width: 400px; max-width: 95vw; background: #0f172a; border-left: 1px solid var(--border); height: 100%; display: flex; flex-direction: column; box-shadow: -8px 0 32px rgba(0,0,0,0.4); }
.slideover-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid var(--border); }
.slideover-header h3 { margin: 0; font-size: 1rem; }
.close-btn { background: none; border: none; color: var(--text-muted); font-size: 1.4rem; cursor: pointer; line-height: 1; padding: 0 4px; }
.close-btn:hover { color: var(--text); }
.slideover-body { flex: 1; overflow-y: auto; padding: 24px; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 24px; }
.detail-item { display: flex; flex-direction: column; gap: 4px; }
.detail-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); }
.big-num { font-size: 1.4rem; font-weight: 700; color: var(--text); }
.sev-breakdown { display: flex; flex-direction: column; gap: 10px; }
.sev-bar-item { display: flex; align-items: center; gap: 10px; }
.sev-label { width: 56px; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; flex-shrink: 0; }
.sev-label.critical { color: #f87171; }
.sev-label.high     { color: #fb923c; }
.sev-label.medium   { color: #fcd34d; }
.sev-label.low      { color: #86efac; }
.sev-bar { flex: 1; height: 7px; background: rgba(148,163,184,0.1); border-radius: 4px; overflow: hidden; }
.sev-fill { height: 100%; border-radius: 4px; transition: width 0.4s ease; }
.sev-fill.critical { background: #ef4444; }
.sev-fill.high     { background: #f97316; }
.sev-fill.medium   { background: #eab308; }
.sev-fill.low      { background: #22c55e; }
.sev-num { width: 28px; text-align: right; font-size: 0.82rem; font-weight: 600; color: var(--text); flex-shrink: 0; }

.slideover-enter-active { transition: transform 0.25s ease; }
.slideover-leave-active { transition: transform 0.2s ease; }
.slideover-enter-from, .slideover-leave-to { transform: translateX(100%); }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 28px 32px; max-width: 400px; width: 90%; }
.modal h3 { margin: 0 0 10px; font-size: 1.05rem; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
</style>
