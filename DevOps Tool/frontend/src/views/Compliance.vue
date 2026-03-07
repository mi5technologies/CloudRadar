<template>
  <div>
    <h1>Compliance report</h1>
    <p class="muted">Check if your cloud config meets a compliance framework. Maps findings to framework controls and reports pass/fail per control.</p>
    <div class="card card-what">
      <h3>What this script does</h3>
      <p>Runs a <strong>compliance report</strong> against your current findings. It maps security findings to controls for the selected framework and reports pass/fail — for example: whether API Gateway has a WAF, whether encryption is enabled, whether audit logging is active. Supports <strong>CIS, SOC2, HIPAA, PCI DSS, and ISO 27001</strong>. Uses the latest scan data (or runs a scan if needed).</p>
    </div>
    <div class="card" style="max-width: 520px;">
      <div class="input-group">
        <label>Framework</label>
        <select v-model="framework">
          <option value="cis">CIS AWS Foundations</option>
          <option value="soc2">SOC 2</option>
          <option value="hipaa">HIPAA</option>
          <option value="pci">PCI DSS</option>
          <option value="iso27001">ISO/IEC 27001:2022</option>
        </select>
      </div>
      <div class="input-group">
        <label>Output format</label>
        <select v-model="output">
          <option value="json">JSON + Suggestions</option>
          <option value="html">HTML (view in browser)</option>
          <option value="pdf">PDF (print / save)</option>
        </select>
      </div>
      <div v-if="output === 'pdf'" class="output-hint">
        <span>ℹ</span> The report will open in a new tab — use your browser's <strong>Print → Save as PDF</strong> to save it.
      </div>
      <button class="btn btn-primary" :disabled="loading" @click="run">Run compliance check</button>
      <RunProgress :running="loading" message="Running compliance check (may run scan first)…" />
      <p v-if="error" class="muted" style="color: var(--error); margin-top: 8px;">{{ error }}</p>
    </div>

    <!-- ── Structured result with gap suggestions ── -->
    <div v-if="parsedResult && output === 'json'" class="results-section">
      <!-- Summary strip -->
      <div class="compliance-summary">
        <div class="cs-item cs-pass">
          <span class="cs-num">{{ passCount }}</span>
          <span class="cs-label">Passed</span>
        </div>
        <div class="cs-item cs-fail">
          <span class="cs-num">{{ failCount }}</span>
          <span class="cs-label">Failed</span>
        </div>
        <div class="cs-item cs-score">
          <span class="cs-num" :style="{ color: scoreColor }">{{ scorePercent }}%</span>
          <span class="cs-label">Compliance</span>
        </div>
        <div class="cs-item">
          <span class="cs-num cs-framework">{{ framework.toUpperCase() }}</span>
          <span class="cs-label">Framework</span>
        </div>
      </div>

      <!-- Progress bar -->
      <div class="compliance-bar-wrap">
        <div class="compliance-bar">
          <div class="compliance-bar-fill" :style="{ width: scorePercent + '%', background: scoreColor }"></div>
        </div>
        <span class="compliance-bar-label" :style="{ color: scoreColor }">{{ scorePercent }}% compliant</span>
      </div>

      <!-- Failed controls with gap suggestions -->
      <div v-if="failedControls.length" class="card gaps-card">
        <div class="gaps-header">
          <h2>🔴 Failed controls — Gap analysis</h2>
          <span class="gaps-count">{{ failedControls.length }} gap{{ failedControls.length !== 1 ? 's' : '' }}</span>
        </div>
        <p class="muted" style="margin-bottom:16px;">Each failed control includes a specific remediation recommendation.</p>
        <div v-for="(ctrl, i) in failedControls" :key="i" class="gap-item">
          <div class="gap-header" @click="toggleGap(i)">
            <div class="gap-left">
              <span class="gap-dot"></span>
              <div class="gap-title-wrap">
                <span class="gap-id">{{ ctrl.control_id || ctrl.id || `Control ${i+1}` }}</span>
                <span class="gap-name">{{ ctrl.control_name || ctrl.name || ctrl.title || 'Unnamed control' }}</span>
              </div>
            </div>
            <svg class="gap-arrow" :class="{ open: openGaps.has(i) }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
          <div v-if="openGaps.has(i)" class="gap-body">
            <p v-if="ctrl.description || ctrl.reason" class="gap-desc">{{ ctrl.description || ctrl.reason }}</p>
            <div class="gap-rec" v-if="getGapRec(ctrl)">
              <div class="gap-rec-title">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                What to do
              </div>
              <p class="gap-rec-what">{{ getGapRec(ctrl).what }}</p>
              <ol class="gap-fix-list">
                <li v-for="(step, j) in getGapRec(ctrl).fix" :key="j">{{ step }}</li>
              </ol>
              <a v-if="getGapRec(ctrl).docs" :href="getGapRec(ctrl).docs" target="_blank" rel="noopener" class="gap-docs-link">
                AWS Documentation →
              </a>
            </div>
            <div v-else class="gap-rec gap-rec-generic">
              <div class="gap-rec-title">Remediation guidance</div>
              <p class="gap-rec-what">Review this control against CIS/{{ framework.toUpperCase() }} documentation and ensure the corresponding AWS service configuration meets the requirement. Consider enabling AWS Config rules to continuously monitor compliance.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Passed controls (collapsed) -->
      <div v-if="passedControls.length" class="card" style="padding: 0; overflow: hidden;">
        <div class="pass-header" @click="showPassed = !showPassed">
          <div style="display:flex;align-items:center;gap:10px;">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
            <span style="font-weight:600;color:var(--text);">✅ Passed controls</span>
            <span class="gaps-count" style="background:rgba(34,197,94,0.12);color:#86efac;">{{ passedControls.length }}</span>
          </div>
          <svg :class="['pass-arrow', showPassed && 'open']" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
        <div v-if="showPassed" class="passed-list">
          <div v-for="(ctrl, i) in passedControls" :key="i" class="passed-item">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>
            <span class="passed-id">{{ ctrl.control_id || ctrl.id }}</span>
            <span class="passed-name">{{ ctrl.control_name || ctrl.name || ctrl.title }}</span>
          </div>
        </div>
      </div>

      <!-- Raw JSON toggle -->
      <div class="card" style="padding:0;overflow:hidden;">
        <div class="raw-toggle" @click="showRaw = !showRaw">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" :style="{ transform: showRaw ? 'rotate(90deg)':'rotate(0)', transition:'transform 0.2s' }"><polyline points="9 18 15 12 9 6"/></svg>
          Raw JSON response
        </div>
        <pre v-if="showRaw" class="raw-pre">{{ JSON.stringify(parsedResult, null, 2).slice(0, 6000) }}</pre>
      </div>
    </div>

    <!-- Non-json result (legacy) -->
    <div v-else-if="result && output === 'json'" class="card">
      <h2>Result</h2>
      <pre>{{ typeof result === 'string' ? result.slice(0, 4000) : JSON.stringify(result, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '../api'
import RunProgress from '../components/RunProgress.vue'
import { openPrintWindow } from '../utils/pdf'
import { RECOMMENDATIONS } from '../utils/recommendations'

const framework = ref('cis')
const output = ref('json')
const loading = ref(false)
const error = ref('')
const result = ref(null)
const parsedResult = ref(null)
const showRaw = ref(false)
const showPassed = ref(false)
const openGaps = ref(new Set())

// Mapping of framework control keywords → recommendation keys
const CONTROL_MAP = [
  { keywords: ['ssh', 'port 22', 'rdp', '3389'],       key: 'sg.ssh_open' },
  { keywords: ['s3', 'public', 'bucket'],               key: 's3.public_access' },
  { keywords: ['s3', 'encrypt'],                        key: 's3.no_encryption' },
  { keywords: ['iam', 'wildcard', 'admin', 'privilege'],key: 'iam.wildcard_action' },
  { keywords: ['cloudtrail', 'logging', 'trail'],       key: 'cloudtrail.disabled' },
  { keywords: ['guardduty', 'threat'],                  key: 'guardduty.disabled' },
  { keywords: ['kms', 'rotation', 'key'],               key: 'kms.no_rotation' },
  { keywords: ['rds', 'database', 'public'],            key: 'rds.publicly_accessible' },
  { keywords: ['rds', 'encrypt'],                       key: 'rds.no_encryption' },
  { keywords: ['ebs', 'volume', 'encrypt'],             key: 'ebs.unencrypted' },
  { keywords: ['vpc', 'flow'],                          key: 'vpc.no_flow_logs' },
  { keywords: ['vpc', 'default'],                       key: 'vpc.default_in_use' },
  { keywords: ['waf', 'alb', 'load balancer'],          key: 'alb.no_waf' },
  { keywords: ['access log', 'alb'],                    key: 'alb.no_access_logs' },
  { keywords: ['ecr', 'container', 'cve'],              key: 'ecr.critical_cve' },
  { keywords: ['eks', 'endpoint', 'kubernetes'],        key: 'eks.public_endpoint' },
]

function getGapRec(ctrl) {
  const text = ((ctrl.control_id || '') + ' ' + (ctrl.control_name || ctrl.name || ctrl.title || '') + ' ' + (ctrl.description || ctrl.reason || '')).toLowerCase()
  for (const { keywords, key } of CONTROL_MAP) {
    if (keywords.every(kw => text.includes(kw)) || keywords.some(kw => text.includes(kw))) {
      if (RECOMMENDATIONS[key]) return RECOMMENDATIONS[key]
    }
  }
  return null
}

function toggleGap(i) {
  const s = new Set(openGaps.value)
  s.has(i) ? s.delete(i) : s.add(i)
  openGaps.value = s
}

// Parse JSON result into structured controls list
const controls = computed(() => {
  if (!parsedResult.value) return []
  const r = parsedResult.value
  // Various possible shapes from the backend
  if (Array.isArray(r.controls)) return r.controls
  if (Array.isArray(r.results))  return r.results
  if (Array.isArray(r.checks))   return r.checks
  if (typeof r === 'object') {
    const vals = Object.values(r)
    if (vals.length && typeof vals[0] === 'object') return vals
  }
  return []
})

const passedControls = computed(() => controls.value.filter(c => c.status === 'pass' || c.passed === true || c.result === 'pass'))
const failedControls = computed(() => controls.value.filter(c => c.status === 'fail' || c.passed === false || c.result === 'fail' || c.status === 'failed'))

const passCount = computed(() => passedControls.value.length)
const failCount = computed(() => failedControls.value.length)
const scorePercent = computed(() => {
  const total = passCount.value + failCount.value
  if (!total) return 0
  return Math.round((passCount.value / total) * 100)
})
const scoreColor = computed(() => {
  const s = scorePercent.value
  if (s >= 80) return '#22c55e'
  if (s >= 60) return '#eab308'
  if (s >= 40) return '#f97316'
  return '#ef4444'
})

async function run() {
  loading.value = true
  error.value = ''
  result.value = null
  parsedResult.value = null
  openGaps.value = new Set()
  showPassed.value = false
  showRaw.value = false
  try {
    const reqOutput = output.value === 'pdf' ? 'html' : output.value
    const data = await api.runCompliance(framework.value, reqOutput)
    if (output.value === 'pdf' || output.value === 'html') {
      const html = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
      openPrintWindow(html, `Compliance Report — ${framework.value.toUpperCase()}`)
    } else {
      result.value = data
      // Try to parse structured result
      try {
        parsedResult.value = typeof data === 'string' ? JSON.parse(data) : data
      } catch (_) {
        parsedResult.value = null
      }
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
  display: flex; align-items: flex-start; gap: 8px; font-size: 0.82rem; color: var(--text-muted);
  background: rgba(14,165,233,0.07); border: 1px solid rgba(14,165,233,0.18); border-radius: 7px;
  padding: 8px 12px; margin-bottom: 14px; line-height: 1.5;
}
.output-hint span { flex-shrink: 0; color: var(--accent); font-weight: 700; }

/* Summary strip */
.results-section { display: flex; flex-direction: column; gap: 18px; }
.compliance-summary { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 14px; }
.cs-item { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.cs-num { font-size: 1.6rem; font-weight: 700; color: var(--text); line-height: 1; }
.cs-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); font-weight: 700; }
.cs-item.cs-pass .cs-num { color: #22c55e; }
.cs-item.cs-fail .cs-num { color: #ef4444; }
.cs-framework { font-size: 1rem; }

/* Progress bar */
.compliance-bar-wrap { display: flex; align-items: center; gap: 14px; }
.compliance-bar { flex: 1; height: 10px; background: rgba(148,163,184,0.12); border-radius: 20px; overflow: hidden; }
.compliance-bar-fill { height: 100%; border-radius: 20px; transition: width 0.5s ease; }
.compliance-bar-label { font-size: 0.88rem; font-weight: 700; white-space: nowrap; }

/* Gaps */
.gaps-card { padding: 20px; }
.gaps-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; flex-wrap: wrap; gap: 8px; }
.gaps-header h2 { margin: 0; font-size: 1rem; }
.gaps-count { padding: 3px 10px; border-radius: 20px; font-size: 0.74rem; font-weight: 700; background: rgba(239,68,68,0.12); color: #fca5a5; }

.gap-item { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; margin-bottom: 8px; }
.gap-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; cursor: pointer; transition: background 0.12s; }
.gap-header:hover { background: rgba(239,68,68,0.05); }
.gap-left { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; }
.gap-dot { width: 8px; height: 8px; border-radius: 50%; background: #ef4444; flex-shrink: 0; }
.gap-title-wrap { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.gap-id   { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }
.gap-name { font-size: 0.88rem; font-weight: 600; color: var(--text); }
.gap-arrow { color: var(--text-muted); transition: transform 0.2s; flex-shrink: 0; }
.gap-arrow.open { transform: rotate(180deg); }
.gap-body { padding: 14px 16px 16px; background: rgba(15,23,42,0.3); border-top: 1px solid var(--border); }
.gap-desc { font-size: 0.84rem; color: var(--text-muted); margin: 0 0 12px; line-height: 1.5; }

/* Gap recommendation */
.gap-rec { background: rgba(14,165,233,0.05); border: 1px solid rgba(14,165,233,0.15); border-radius: 10px; padding: 14px; }
.gap-rec-generic { background: rgba(245,158,11,0.05); border-color: rgba(245,158,11,0.15); }
.gap-rec-title { display: flex; align-items: center; gap: 7px; font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); margin-bottom: 8px; }
.gap-rec-what { font-size: 0.84rem; color: var(--text-muted); margin: 0 0 10px; line-height: 1.5; }
.gap-fix-list { margin: 0 0 10px; padding-left: 18px; display: flex; flex-direction: column; gap: 5px; }
.gap-fix-list li { font-size: 0.82rem; color: var(--text-muted); line-height: 1.45; }
.gap-fix-list li::marker { color: var(--accent); }
.gap-docs-link { font-size: 0.8rem; color: var(--accent); text-decoration: none; }
.gap-docs-link:hover { text-decoration: underline; }

/* Passed controls */
.pass-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; cursor: pointer; transition: background 0.12s; }
.pass-header:hover { background: rgba(34,197,94,0.04); }
.pass-arrow { color: var(--text-muted); transition: transform 0.2s; }
.pass-arrow.open { transform: rotate(180deg); }
.passed-list { padding: 4px 20px 14px; display: flex; flex-direction: column; gap: 8px; border-top: 1px solid var(--border); }
.passed-item { display: flex; align-items: center; gap: 10px; font-size: 0.84rem; }
.passed-id   { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); width: 90px; flex-shrink: 0; }
.passed-name { color: var(--text-muted); }

/* Raw JSON */
.raw-toggle { display: flex; align-items: center; gap: 8px; padding: 10px 14px; cursor: pointer; font-size: 0.82rem; font-weight: 600; color: var(--text-muted); background: rgba(15,23,42,0.5); user-select: none; }
.raw-toggle:hover { color: var(--text); }
.raw-pre { margin: 0; padding: 14px; font-size: 0.75rem; background: rgba(0,0,0,0.3); color: var(--text-muted); overflow-x: auto; max-height: 400px; }
</style>
