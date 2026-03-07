<template>
  <div class="step-progress">
    <div class="step-progress-title">{{ title }}</div>
    <div v-if="steps.length === 0 && !error" class="step-progress-waiting">Waiting for execution logs…</div>
    <div class="steps" :class="{ 'steps-scroll': steps.length > 4 }">
      <div
        v-for="(step, i) in steps"
        :key="i"
        class="step"
        :class="[step.status === 'running' ? 'step-running' : '', step.status === 'success' ? 'step-success' : '', step.status === 'failed' ? 'step-failed' : '']"
      >
        <div class="step-indicator">
          <span v-if="step.status === 'running'" class="step-spinner"></span>
          <span v-else-if="step.status === 'success'" class="step-check">✓</span>
          <span v-else-if="step.status === 'failed'" class="step-x">✕</span>
          <span v-else class="step-dot"></span>
        </div>
        <div class="step-content">
          <div class="step-label">{{ step.step }}</div>
          <div v-if="step.detail" class="step-detail">{{ step.detail }}</div>
        </div>
      </div>
    </div>
    <div v-if="error" class="step-error">{{ error }}</div>

    <!-- ── Structured summary card ── -->
    <div v-if="done && summary" class="summary-card card">
      <div class="summary-header">
        <div class="summary-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
          Scan Complete
        </div>
        <span v-if="summary.risk_score" class="risk-badge" :class="riskClass(summary.risk_score)">
          Risk {{ summary.risk_score }}
        </span>
      </div>

      <!-- Severity breakdown -->
      <div class="sev-pills">
        <span class="sev-pill sev-critical" v-if="criticalCount > 0">🔴 {{ criticalCount }} Critical</span>
        <span class="sev-pill sev-high"     v-if="highCount > 0">🟠 {{ highCount }} High</span>
        <span class="sev-pill sev-medium"   v-if="mediumCount > 0">🟡 {{ mediumCount }} Medium</span>
        <span class="sev-pill sev-low"      v-if="lowCount > 0">🟢 {{ lowCount }} Low</span>
        <span class="sev-pill sev-none" v-if="totalFindings === 0">✅ No findings — great job!</span>
      </div>

      <!-- Meta row -->
      <div class="summary-meta">
        <span v-if="summary.cloud"><strong>Cloud:</strong> {{ summary.cloud?.toUpperCase() }}</span>
        <span v-if="summary.region"><strong>Region:</strong> {{ summary.region }}</span>
        <span v-if="summary.findings_count !== undefined"><strong>Total findings:</strong> {{ summary.findings_count }}</span>
      </div>

      <!-- Top recommendations -->
      <div v-if="topRecs.length" class="recs-section">
        <div class="recs-title">📌 Recommended actions</div>
        <div v-for="(rec, i) in topRecs" :key="i" class="rec-item">
          <span class="rec-num">{{ i + 1 }}</span>
          <div class="rec-body">
            <span class="rec-label">{{ rec.title }}</span>
            <span class="rec-fix">{{ rec.fix[0] }}</span>
          </div>
          <span class="rec-sev-badge" :class="'sev-badge-' + rec.severity">{{ rec.severity }}</span>
        </div>
      </div>

      <!-- Downloads + navigation -->
      <div class="summary-actions">
        <router-link to="/findings" class="btn btn-accent">View All Findings →</router-link>
        <a v-for="d in (downloads || [])" :key="d.url" :href="d.url" class="btn btn-secondary" target="_blank" rel="noopener">{{ d.label }}</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getRecommendation, SEV_ORDER } from '../utils/recommendations'

const props = defineProps({
  title:     { type: String,  default: 'Execution' },
  steps:     { type: Array,   default: () => [] },
  error:     { type: String,  default: '' },
  done:      { type: Boolean, default: false },
  summary:   { type: Object,  default: null },
  downloads: { type: Array,   default: () => [] },
})

const criticalCount = computed(() => props.summary?.critical ?? 0)
const highCount     = computed(() => props.summary?.high ?? 0)
const mediumCount   = computed(() => props.summary?.medium ?? 0)
const lowCount      = computed(() => props.summary?.low ?? 0)
const totalFindings = computed(() => props.summary?.findings_count ?? 0)

function riskClass(score) {
  const n = typeof score === 'number' ? score : parseFloat(score)
  if (n >= 80) return 'risk-critical'
  if (n >= 60) return 'risk-high'
  if (n >= 40) return 'risk-medium'
  return 'risk-low'
}

// Build top 3 recommendations from summary findings if available
const topRecs = computed(() => {
  const findings = props.summary?.top_findings || props.summary?.findings || []
  if (!findings.length) {
    // If no findings array, synthesise from severity counts
    const recs = []
    if (criticalCount.value > 0) recs.push(getRecommendation({ severity: 'critical', rule_id: 'sg.ssh_open' }))
    if (highCount.value > 0)     recs.push(getRecommendation({ severity: 'high',     rule_id: 's3.no_encryption' }))
    return recs.slice(0, 3)
  }
  const sorted = [...findings].sort((a, b) =>
    (SEV_ORDER[(a.severity||'medium').toLowerCase()] ?? 4) - (SEV_ORDER[(b.severity||'medium').toLowerCase()] ?? 4)
  )
  return sorted.slice(0, 3).map(f => getRecommendation(f)).filter(Boolean)
})
</script>

<style scoped>
.step-progress { margin: 20px 0; }
.step-progress-title { font-size: 1rem; font-weight: 600; margin-bottom: 16px; color: var(--text); }
.step-progress-waiting { padding: 16px; color: var(--text-muted); font-size: 0.9rem; background: rgba(15,23,42,0.4); border-radius: 8px; margin-bottom: 12px; }
.steps { display: flex; flex-direction: column; gap: 0; }
.steps-scroll { max-height: 420px; overflow-y: auto; overflow-x: hidden; }
.step { display: flex; align-items: flex-start; gap: 14px; padding: 12px 16px; border-radius: 8px; margin-bottom: 2px; background: rgba(15,23,42,0.4); border: 1px solid transparent; transition: background 0.15s, border-color 0.15s; }
.step-running { background: rgba(14,165,233,0.08); border-color: rgba(14,165,233,0.25); }
.step-success { background: rgba(34,197,94,0.06);  border-color: rgba(34,197,94,0.15); }
.step-failed  { background: rgba(239,68,68,0.08);  border-color: rgba(239,68,68,0.25); }
.step-indicator { flex-shrink: 0; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; }
.step-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--text-muted); opacity: 0.5; }
.step-spinner { width: 18px; height: 18px; border: 2px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.step-check { color: var(--success); font-weight: 700; }
.step-x { color: var(--error); font-weight: 700; }
.step-content { flex: 1; min-width: 0; }
.step-label { font-size: 0.9rem; font-weight: 500; color: var(--text); }
.step-detail { font-size: 0.8rem; color: var(--text-muted); margin-top: 2px; }
.step-error { margin-top: 16px; padding: 12px 16px; background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; color: #fca5a5; font-size: 0.9rem; }

/* ── Summary card ── */
.summary-card { margin-top: 24px; }
.summary-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }
.summary-title { display: flex; align-items: center; gap: 8px; font-size: 1rem; font-weight: 700; color: var(--text); }
.risk-badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; }
.risk-critical { background: rgba(239,68,68,0.15); color: #fca5a5; }
.risk-high     { background: rgba(249,115,22,0.15); color: #fdba74; }
.risk-medium   { background: rgba(245,158,11,0.15); color: #fcd34d; }
.risk-low      { background: rgba(34,197,94,0.15);  color: #86efac; }
.sev-pills { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
.sev-pill { padding: 5px 13px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; }
.sev-critical { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.2); }
.sev-high     { background: rgba(249,115,22,0.15); color: #fdba74; border: 1px solid rgba(249,115,22,0.2); }
.sev-medium   { background: rgba(245,158,11,0.15); color: #fcd34d; border: 1px solid rgba(245,158,11,0.2); }
.sev-low      { background: rgba(34,197,94,0.15);  color: #86efac; border: 1px solid rgba(34,197,94,0.2); }
.sev-none     { background: rgba(34,197,94,0.1);   color: #86efac; }
.summary-meta { display: flex; gap: 20px; flex-wrap: wrap; font-size: 0.84rem; color: var(--text-muted); margin-bottom: 18px; }
.summary-meta strong { color: var(--text); }

/* Recommendations */
.recs-section { margin-bottom: 18px; }
.recs-title { font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); margin-bottom: 10px; }
.rec-item { display: flex; align-items: flex-start; gap: 12px; padding: 10px 14px; background: rgba(14,165,233,0.05); border: 1px solid rgba(14,165,233,0.12); border-radius: 8px; margin-bottom: 6px; }
.rec-num { width: 22px; height: 22px; border-radius: 50%; background: rgba(14,165,233,0.2); color: var(--accent); font-size: 0.75rem; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px; }
.rec-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.rec-label { font-size: 0.87rem; font-weight: 600; color: var(--text); }
.rec-fix { font-size: 0.78rem; color: var(--text-muted); line-height: 1.4; }
.rec-sev-badge { flex-shrink: 0; padding: 2px 8px; border-radius: 10px; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; margin-top: 2px; }
.sev-badge-critical { background: rgba(239,68,68,0.15); color: #fca5a5; }
.sev-badge-high     { background: rgba(249,115,22,0.15); color: #fdba74; }
.sev-badge-medium   { background: rgba(245,158,11,0.15); color: #fcd34d; }
.sev-badge-low      { background: rgba(34,197,94,0.15);  color: #86efac; }

.summary-actions { display: flex; gap: 10px; flex-wrap: wrap; }
</style>
