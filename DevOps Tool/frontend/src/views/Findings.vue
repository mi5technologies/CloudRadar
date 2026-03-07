<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Findings</h1>
        <p class="muted">Security findings from the last successful scan. Click a row for details and recommendations.</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="load" :disabled="loading">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
          Refresh
        </button>
        <button class="btn btn-secondary" @click="exportCsv" :disabled="!filteredFindings.length">Export CSV</button>
      </div>
    </div>

    <div v-if="summary" class="summary-strip">
      <span class="strip-item cloud-badge" :class="'cloud-badge-' + (summary.cloud || 'aws')">
        <span v-html="cloudIcon(summary.cloud)"></span>
        {{ (summary.cloud||'aws').toUpperCase() }}
      </span>
      <span class="strip-sep">·</span>
      <span class="strip-item">{{ summary.region || '—' }}</span>
      <span class="strip-sep">·</span>
      <span class="strip-item sev-count-critical">🔴 {{ sevCounts.critical }} critical</span>
      <span class="strip-item sev-count-high">🟠 {{ sevCounts.high }} high</span>
      <span class="strip-item sev-count-medium">🟡 {{ sevCounts.medium }} medium</span>
      <span class="strip-item sev-count-low">🟢 {{ sevCounts.low }} low</span>
      <span class="strip-sep">·</span>
      <span class="strip-item">Risk <strong>{{ summary.risk_score ?? '—' }}</strong></span>
    </div>

    <!-- Remediation progress bar -->
    <div v-if="findings.length" class="rem-strip">
      <div class="rem-strip-left">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        Remediation progress
        <span class="rem-pct" :style="{ color: remProgressColor }">{{ remProgress.percentage }}%</span>
        <span class="rem-detail">· {{ remProgress.resolved }} fixed / {{ remProgress.remaining }} open</span>
      </div>
      <div class="rem-bar-wrap">
        <div class="rem-bar" :style="{ width: remProgress.percentage + '%', background: remProgressColor }"></div>
      </div>
    </div>

    <!-- Cloud filter tabs (shown when findings from multiple clouds exist) -->
    <div v-if="cloudTabs.length > 1" class="cloud-tabs">
      <button
        v-for="tab in cloudTabs" :key="tab.id"
        class="cloud-tab" :class="{ active: filterCloud === tab.id, ['ct-' + tab.id]: true }"
        @click="filterCloud = tab.id"
      >
        <span v-html="tab.icon"></span>
        {{ tab.label }}
        <span class="tab-count">{{ tab.count }}</span>
      </button>
      <button v-if="filterCloud" class="cloud-tab ct-clear" @click="filterCloud = ''">
        All clouds ×
      </button>
    </div>

    <div class="card" style="margin-bottom: 20px;">
      <div class="filters-row">
        <div class="search-wrap">
          <svg class="search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input v-model="searchQ" class="search-input" placeholder="Filter by rule, resource, title…" />
        </div>
        <select v-model="filterSev" class="filter-select">
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select v-model="filterType" class="filter-select">
          <option value="">All types</option>
          <option v-for="t in resourceTypes" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>
    </div>

    <div class="card" style="padding: 0; overflow: hidden;">
      <div class="card-head" style="padding: 16px 20px; border-bottom: 1px solid var(--border);">
        <h2 style="margin:0;">Findings <span class="count-badge">{{ filteredFindings.length }}</span></h2>
        <span v-if="filteredFindings.length !== findings.length" class="filter-note">{{ findings.length - filteredFindings.length }} filtered</span>
      </div>
      <div v-if="loading" class="loading-row">
        <span class="spinner"></span> Loading findings…
      </div>
      <div v-else-if="!findings.length" class="empty-row">
        No findings. Run a Security Scan to see results.
      </div>
      <div v-else-if="!filteredFindings.length" class="empty-row">
        No findings match the current filters.
      </div>
      <div v-else class="findings-table-wrap">
        <table class="findings-table">
          <thead>
            <tr>
              <th style="width:90px;">Severity</th>
              <th style="width:70px;">Cloud</th>
              <th>Rule</th>
              <th>Resource type</th>
              <th>Resource ID</th>
              <th>Title</th>
              <th style="width:90px;">Status</th>
              <th style="width:80px;"></th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(f, i) in filteredFindings" :key="i">
              <tr
                :class="['sev-row-' + (f.severity || 'medium'), isFindingFixed(f) ? 'row-fixed' : '']"
                @click="openSlide(f)"
                style="cursor:pointer;"
              >
                <td><span class="badge" :class="'badge-' + (f.severity || 'medium')">{{ f.severity || 'medium' }}</span></td>
                <td>
                  <span class="cloud-chip" :class="'cc-' + (f.cloud || 'aws')" :title="(f.cloud||'aws').toUpperCase()">
                    <span v-html="cloudIcon(f.cloud || 'aws')"></span>
                    {{ (f.cloud || 'aws').toUpperCase() }}
                  </span>
                </td>
                <td><code>{{ f.rule_id || '—' }}</code></td>
                <td>{{ f.resource_type || '—' }}</td>
                <td><code class="resource-id">{{ f.resource_id || '—' }}</code></td>
                <td>{{ f.title || '—' }}</td>
                <td @click.stop>
                  <button
                    class="btn-mark-fixed"
                    :class="isFindingFixed(f) ? 'btn-fixed' : 'btn-open'"
                    @click="toggleFixed(f)"
                    :title="isFindingFixed(f) ? 'Click to re-open this finding' : 'Mark as fixed'"
                  >
                    <svg v-if="isFindingFixed(f)" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                    {{ isFindingFixed(f) ? 'Fixed' : 'Mark fixed' }}
                  </button>
                </td>
                <td @click.stop>
                  <button
                    v-if="isRemediable(f)"
                    class="btn-remediate"
                    @click="toggleRemediate(f, i)"
                  >{{ remediateOpen === i ? 'Close' : 'Remediate' }}</button>
                </td>
              </tr>
              <tr v-if="remediateOpen === i && isRemediable(f)" class="remediate-row" @click.stop>
                <td colspan="6">
                  <div class="remediate-panel">
                    <div class="remediate-options">
                      <label class="checkbox-label">
                        <input type="checkbox" v-model="remState.dry_run" /> Dry run first
                      </label>
                      <div class="inline-input-group">
                        <label>Region</label>
                        <input v-model="remState.region" type="text" placeholder="us-east-1" />
                      </div>
                      <button class="btn btn-primary btn-sm" :disabled="remState.loading" @click="applyRemediate(f)">
                        {{ remState.loading ? 'Applying…' : 'Apply fix' }}
                      </button>
                    </div>
                    <div v-if="remState.result" class="remediate-result" :class="remState.ok ? 'result-ok' : 'result-err'">{{ remState.result }}</div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Slide-over detail panel ── -->
    <transition name="slide-fade">
      <div v-if="slideOver" class="slideover-wrap" @click.self="slideOver = null">
        <div class="slideover">
          <div class="slideover-header">
            <div class="so-title">
              <span class="badge" :class="'badge-' + (slideOver.severity || 'medium')">{{ slideOver.severity || 'medium' }}</span>
              <span class="cloud-chip" :class="'cc-' + (slideOver.cloud || 'aws')">
                <span v-html="cloudIcon(slideOver.cloud || 'aws')"></span>
                {{ (slideOver.cloud || 'aws').toUpperCase() }}
              </span>
              <h3>{{ slideOver.title || slideOver.rule_id || 'Finding Detail' }}</h3>
            </div>
            <button class="close-btn" @click="slideOver = null">×</button>
          </div>
          <div class="slideover-body">
            <!-- Remediation status -->
            <div class="so-fix-status">
              <button
                class="btn-mark-fixed btn-mark-fixed-lg"
                :class="isFindingFixed(slideOver) ? 'btn-fixed' : 'btn-open'"
                @click="toggleFixed(slideOver)"
              >
                <svg v-if="isFindingFixed(slideOver)" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
                {{ isFindingFixed(slideOver) ? 'Mark as re-opened' : 'Mark as fixed' }}
              </button>
              <span v-if="isFindingFixed(slideOver)" class="so-fixed-hint">This finding is marked as fixed. Your risk score is adjusted.</span>
            </div>

            <!-- Metadata -->
            <div class="so-meta">
              <div v-if="slideOver.cloud" class="so-meta-item"><span class="so-meta-label">Cloud</span><span>{{ slideOver.cloud.toUpperCase() }}</span></div>
              <div v-if="slideOver.rule_id" class="so-meta-item"><span class="so-meta-label">Rule</span><code>{{ slideOver.rule_id }}</code></div>
              <div v-if="slideOver.resource_type" class="so-meta-item"><span class="so-meta-label">Resource type</span><span>{{ slideOver.resource_type }}</span></div>
              <div v-if="slideOver.resource_id" class="so-meta-item"><span class="so-meta-label">Resource ID</span><code class="so-resource-id">{{ slideOver.resource_id }}</code></div>
              <div v-if="slideOver.region" class="so-meta-item"><span class="so-meta-label">Region / Project</span><span>{{ slideOver.region }}</span></div>
            </div>

            <!-- Recommendation section -->
            <div v-if="slideRec" class="rec-card">
              <div class="rec-what">
                <div class="rec-section-title">What is this?</div>
                <p>{{ slideRec.what }}</p>
              </div>
              <div class="rec-why">
                <div class="rec-section-title">Why it matters</div>
                <p>{{ slideRec.why }}</p>
              </div>
              <div class="rec-fix">
                <div class="rec-section-title">How to fix it</div>
                <ol class="fix-list">
                  <li v-for="(step, i) in slideRec.fix" :key="i">{{ step }}</li>
                </ol>
              </div>
              <a v-if="slideRec.docs" :href="slideRec.docs" target="_blank" rel="noopener" class="docs-link">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                {{ cloudLabel(slideOver.cloud) }} Documentation →
              </a>
            </div>

            <!-- Raw data -->
            <div class="raw-section">
              <div class="raw-title" @click="showRaw = !showRaw">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :style="{ transform: showRaw ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }"><polyline points="9 18 15 12 9 6"/></svg>
                Raw finding data
              </div>
              <pre v-if="showRaw" class="raw-pre">{{ JSON.stringify(slideOver, null, 2) }}</pre>
            </div>

            <!-- Remediate inline -->
            <div v-if="isRemediable(slideOver)" class="so-remediate">
              <div class="rec-section-title">Auto-remediation</div>
              <div class="remediate-options">
                <label class="checkbox-label"><input type="checkbox" v-model="soRemState.dry_run" /> Dry run first</label>
                <div class="inline-input-group"><label>Region</label><input v-model="soRemState.region" type="text" placeholder="us-east-1" /></div>
                <button class="btn btn-primary btn-sm" :disabled="soRemState.loading" @click="applyRemediateSO">
                  {{ soRemState.loading ? 'Applying…' : 'Apply fix' }}
                </button>
              </div>
              <div v-if="soRemState.result" class="remediate-result" :class="soRemState.ok ? 'result-ok' : 'result-err'">{{ soRemState.result }}</div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '../api'
import { getRecommendation } from '../utils/recommendations'
import { markFixed, unmarkFixed, isFixed, computeRemediationScore } from '../utils/remediationStore'

const CLOUD_META = {
  aws:   { label: 'AWS',          icon: `<svg width="12" height="8" viewBox="0 0 80 48" fill="none"><path d="M22.9 32.2c-4.5 2.4-9.4 3.7-14.5 3.7C3.8 35.9 0 32.1 0 27.3c0-5.3 4.5-9.6 10.7-10.2-.3-1.1-.5-2.3-.5-3.6C10.2 6.1 15.9 1 22.9 1c3.4 0 6.5 1.2 8.9 3.2 2.2-4.3 6.7-7.2 11.7-7.2 4.3 0 8.2 1.9 10.8 5 1.9-.7 3.9-1.1 6-1.1C68 1 75 8 75 16.8c0 1.8-.3 3.5-.8 5.1C77.4 23.5 80 27 80 31.1 80 36.8 75.3 41 69.2 41H22.9z" fill="#FF9900"/></svg>` },
  gcp:   { label: 'Google Cloud', icon: `<svg width="12" height="12" viewBox="0 0 48 48"><path fill="#4285F4" d="M30.2 17.8H24v4.2h6.9c-.7 3.7-4 6.5-7.9 6.5-4.5 0-8.2-3.7-8.2-8.2s3.7-8.2 8.2-8.2c2.1 0 4 .8 5.5 2.1l3-3C29 8.6 26.7 7.5 24 7.5c-7.5 0-13.5 6-13.5 13.5S16.5 34.5 24 34.5c7.2 0 12.8-5 12.8-13.5 0-.8-.1-1.5-.2-2.2l-6.4-1z"/></svg>` },
  azure: { label: 'Azure',        icon: `<svg width="12" height="12" viewBox="0 0 48 48"><path fill="#0078D4" d="M27 4L13 28l9 5-7 7h16l7-36z"/><path fill="#50E6FF" d="M27 4L4 34l9-1 7-7-3-5z"/></svg>` },
}
function cloudIcon(id) { return CLOUD_META[id]?.icon || CLOUD_META.aws.icon }
function cloudLabel(id) { return CLOUD_META[id]?.label || 'Cloud' }

const findings   = ref([])
const summary    = ref(null)
const loading    = ref(false)
const searchQ    = ref('')
const filterSev  = ref('')
const filterType = ref('')
const filterCloud = ref('')

const remediateOpen = ref(null)
const remState = ref({ dry_run: true, region: 'us-east-1', loading: false, result: '', ok: false })
const REMEDIABLE_TYPES = ['s3', 'iam_role', 'security_group']

const slideOver = ref(null)
const showRaw   = ref(false)
const soRemState = ref({ dry_run: true, region: 'us-east-1', loading: false, result: '', ok: false })

const slideRec = computed(() => slideOver.value ? getRecommendation(slideOver.value) : null)

watch(slideOver, () => {
  showRaw.value = false
  soRemState.value = { dry_run: true, region: 'us-east-1', loading: false, result: '', ok: false }
})

// Remediation progress tracking
const fixedVersion = ref(0)  // bump to force recompute after toggle

function isFindingFixed(f) {
  // eslint-disable-next-line no-unused-expressions
  fixedVersion.value  // track reactively
  return isFixed(f)
}

function toggleFixed(f) {
  if (isFixed(f)) {
    unmarkFixed(f)
  } else {
    markFixed(f)
  }
  fixedVersion.value++
}

const remProgress = computed(() => {
  // eslint-disable-next-line no-unused-expressions
  fixedVersion.value
  return computeRemediationScore(findings.value)
})

const remProgressColor = computed(() => {
  const pct = remProgress.value.percentage
  if (pct >= 75) return '#22c55e'
  if (pct >= 40) return '#eab308'
  return '#f97316'
})

const sevCounts = computed(() => {
  const counts = { critical: 0, high: 0, medium: 0, low: 0 }
  for (const f of findings.value) {
    const k = (f.severity || 'medium').toLowerCase()
    if (k in counts) counts[k]++
  }
  return counts
})

const resourceTypes = computed(() => {
  return [...new Set(findings.value.map(f => f.resource_type).filter(Boolean))].sort()
})

// Cloud tabs — only shown if findings from multiple clouds exist
const cloudTabs = computed(() => {
  const counts = {}
  for (const f of findings.value) {
    const c = (f.cloud || 'aws').toLowerCase()
    counts[c] = (counts[c] || 0) + 1
  }
  return Object.entries(counts).map(([id, count]) => ({
    id, count, label: CLOUD_META[id]?.label || id.toUpperCase(),
    icon: CLOUD_META[id]?.icon || '',
  }))
})

const filteredFindings = computed(() => {
  let list = findings.value
  if (filterCloud.value) list = list.filter(f => (f.cloud || 'aws').toLowerCase() === filterCloud.value)
  if (filterSev.value)   list = list.filter(f => (f.severity||'').toLowerCase() === filterSev.value)
  if (filterType.value)  list = list.filter(f => f.resource_type === filterType.value)
  if (searchQ.value.trim()) {
    const q = searchQ.value.toLowerCase()
    list = list.filter(f =>
      (f.rule_id||'').toLowerCase().includes(q) ||
      (f.resource_type||'').toLowerCase().includes(q) ||
      (f.resource_id||'').toLowerCase().includes(q) ||
      (f.title||'').toLowerCase().includes(q)
    )
  }
  return list
})

function isRemediable(f) { return REMEDIABLE_TYPES.includes(f.resource_type) }

function openSlide(f) {
  slideOver.value = f
}

function toggleRemediate(f, i) {
  if (remediateOpen.value === i) {
    remediateOpen.value = null
  } else {
    remediateOpen.value = i
    remState.value = { dry_run: true, region: 'us-east-1', loading: false, result: '', ok: false }
  }
}

async function applyRemediate(finding) {
  remState.value.loading = true
  remState.value.result = ''
  try {
    const res = await api.remediate(finding, remState.value.dry_run, remState.value.region)
    remState.value.result = typeof res === 'string' ? res : JSON.stringify(res)
    remState.value.ok = true
  } catch (e) {
    remState.value.result = e.message || 'Remediation failed.'
    remState.value.ok = false
  } finally {
    remState.value.loading = false
  }
}

async function applyRemediateSO() {
  soRemState.value.loading = true
  soRemState.value.result = ''
  try {
    const res = await api.remediate(slideOver.value, soRemState.value.dry_run, soRemState.value.region)
    soRemState.value.result = typeof res === 'string' ? res : JSON.stringify(res)
    soRemState.value.ok = true
  } catch (e) {
    soRemState.value.result = e.message || 'Remediation failed.'
    soRemState.value.ok = false
  } finally {
    soRemState.value.loading = false
  }
}

function exportCsv() {
  const cols = ['severity','rule_id','resource_type','resource_id','title']
  const rows = [cols.join(',')]
  for (const f of filteredFindings.value) {
    rows.push(cols.map(c => `"${(f[c]||'').toString().replace(/"/g,'""')}"`).join(','))
  }
  const blob = new Blob([rows.join('\n')], { type: 'text/csv' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'findings.csv'
  a.click()
}

async function load() {
  loading.value = true
  try {
    const data = await api.getFindings()
    findings.value = data.findings || []
    summary.value = data.summary || null
    remediateOpen.value = null
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
.page-header { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 18px; }
.header-actions { display: flex; gap: 8px; flex-wrap: wrap; }

/* Summary strip */
.summary-strip { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 10px 18px; background: rgba(15,23,42,0.5); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 18px; font-size: 0.84rem; }
.strip-sep { color: var(--text-muted); }
.strip-item { color: var(--text-muted); }
.strip-item strong { color: var(--text); }
.sev-count-critical { color: #f87171; font-weight: 600; }
.sev-count-high     { color: #fb923c; font-weight: 600; }
.sev-count-medium   { color: #fbbf24; font-weight: 600; }
.sev-count-low      { color: #86efac; font-weight: 600; }

/* Cloud badge in summary strip */
.cloud-badge { display: inline-flex; align-items: center; gap: 5px; font-weight: 700; padding: 2px 9px; border-radius: 7px; }
.cloud-badge-aws   { background: rgba(255,153,0,0.12);  color: #fb923c; }
.cloud-badge-gcp   { background: rgba(66,133,244,0.12); color: #60a5fa; }
.cloud-badge-azure { background: rgba(0,120,212,0.12);  color: #93c5fd; }

/* Cloud filter tabs */
.cloud-tabs { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }
.cloud-tab {
  display: inline-flex; align-items: center; gap: 6px; padding: 6px 13px;
  border-radius: 20px; border: 1px solid var(--border); background: rgba(15,23,42,0.5);
  color: var(--text-muted); font-size: 0.82rem; font-weight: 500; cursor: pointer; transition: all 0.14s;
}
.cloud-tab:hover { color: var(--text); border-color: rgba(99,102,241,0.35); }
.ct-aws.active    { background: rgba(255,153,0,0.12);  border-color: rgba(255,153,0,0.35);  color: #fb923c; font-weight: 700; }
.ct-gcp.active    { background: rgba(66,133,244,0.12); border-color: rgba(66,133,244,0.35); color: #60a5fa; font-weight: 700; }
.ct-azure.active  { background: rgba(0,120,212,0.12);  border-color: rgba(0,120,212,0.35);  color: #93c5fd; font-weight: 700; }
.ct-clear { border-color: rgba(99,102,241,0.3); color: #a5b4fc; }
.tab-count { background: rgba(255,255,255,0.1); padding: 0 6px; border-radius: 20px; font-size: 0.72rem; }

/* Cloud chip in table rows */
.cloud-chip {
  display: inline-flex; align-items: center; gap: 4px; padding: 2px 7px;
  border-radius: 5px; font-size: 0.7rem; font-weight: 700; white-space: nowrap;
}
.cc-aws   { background: rgba(255,153,0,0.1);  color: #fb923c; }
.cc-gcp   { background: rgba(66,133,244,0.1); color: #60a5fa; }
.cc-azure { background: rgba(0,120,212,0.1);  color: #93c5fd; }

/* Filters */
.filters-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.search-wrap { position: relative; flex: 1; min-width: 180px; }
.search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.search-input { width: 100%; padding: 8px 12px 8px 34px; border-radius: 8px; border: 1px solid var(--border); background: rgba(15,23,42,0.6); color: var(--text); font-size: 0.88rem; outline: none; box-sizing: border-box; }
.search-input:focus { border-color: var(--accent); }
.filter-select { padding: 8px 10px; border-radius: 8px; border: 1px solid var(--border); background: rgba(15,23,42,0.6); color: var(--text); font-size: 0.85rem; outline: none; cursor: pointer; }
.filter-select:focus { border-color: var(--accent); }

/* Table */
.card-head { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.count-badge { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; background: rgba(14,165,233,0.15); color: var(--accent); font-weight: 700; margin-left: 6px; vertical-align: middle; }
.filter-note { font-size: 0.78rem; color: var(--text-muted); }
.loading-row, .empty-row { padding: 32px 20px; color: var(--text-muted); font-size: 0.9rem; display: flex; align-items: center; gap: 10px; justify-content: center; }
.spinner { width: 18px; height: 18px; border: 2px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }
.findings-table-wrap { overflow-x: auto; }
.findings-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.findings-table th { padding: 10px 14px; text-align: left; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); background: rgba(15,23,42,0.4); white-space: nowrap; }
.findings-table td { padding: 10px 14px; border-bottom: 1px solid var(--border); vertical-align: middle; }
.findings-table tbody tr:last-child td { border-bottom: none; }
.findings-table tbody tr:hover:not(.remediate-row) { background: rgba(14,165,233,0.04); }
.resource-id { max-width: 180px; overflow: hidden; text-overflow: ellipsis; display: inline-block; white-space: nowrap; }
.badge { display: inline-block; padding: 3px 9px; border-radius: 6px; font-size: 0.73rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
.badge-critical { background: rgba(239,68,68,0.18); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
.badge-high     { background: rgba(249,115,22,0.18); color: #fdba74; border: 1px solid rgba(249,115,22,0.3); }
.badge-medium   { background: rgba(245,158,11,0.18); color: #fcd34d; border: 1px solid rgba(245,158,11,0.3); }
.badge-low      { background: rgba(34,197,94,0.18);  color: #86efac; border: 1px solid rgba(34,197,94,0.3); }
.btn-remediate { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 500; border: none; cursor: pointer; background: rgba(14,165,233,0.12); color: var(--accent); transition: background 0.15s; white-space: nowrap; }
.btn-remediate:hover { background: rgba(14,165,233,0.22); }
.btn-sm { padding: 7px 14px; font-size: 0.85rem; }
.remediate-row td { background: rgba(14,165,233,0.04); border-bottom: 2px solid rgba(14,165,233,0.2); }
.remediate-panel { padding: 12px 4px; display: flex; flex-direction: column; gap: 10px; }
.remediate-options { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.checkbox-label { display: flex; align-items: center; gap: 6px; font-size: 0.88rem; cursor: pointer; }
.inline-input-group { display: flex; align-items: center; gap: 8px; font-size: 0.88rem; }
.inline-input-group label { color: var(--text-muted); white-space: nowrap; }
.inline-input-group input { padding: 6px 10px; border-radius: 6px; border: 1px solid var(--border); background: rgba(15,23,42,0.8); color: var(--text); font-size: 0.88rem; width: 130px; }
.inline-input-group input:focus { outline: none; border-color: var(--accent); }
.remediate-result { padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; font-family: monospace; white-space: pre-wrap; word-break: break-all; }
.result-ok { background: rgba(34,197,94,0.1);  color: var(--success); border: 1px solid rgba(34,197,94,0.2); }
.result-err{ background: rgba(239,68,68,0.1);  color: var(--error);   border: 1px solid rgba(239,68,68,0.2); }

/* ── Slide-over ── */
.slideover-wrap { position: fixed; inset: 0; z-index: 500; display: flex; justify-content: flex-end; background: rgba(0,0,0,0.45); }
.slideover { width: 480px; max-width: 96vw; background: #0d1b2e; border-left: 1px solid var(--border); height: 100%; display: flex; flex-direction: column; box-shadow: -12px 0 40px rgba(0,0,0,0.5); }
.slideover-header { display: flex; justify-content: space-between; align-items: flex-start; padding: 18px 22px; border-bottom: 1px solid var(--border); gap: 12px; }
.so-title { display: flex; align-items: flex-start; gap: 10px; flex: 1; min-width: 0; }
.so-title h3 { margin: 0; font-size: 0.95rem; font-weight: 600; line-height: 1.4; color: var(--text); }
.close-btn { background: none; border: none; color: var(--text-muted); font-size: 1.5rem; cursor: pointer; line-height: 1; padding: 0 2px; flex-shrink: 0; margin-top: -2px; }
.close-btn:hover { color: var(--text); }
.slideover-body { flex: 1; overflow-y: auto; padding: 20px 22px; display: flex; flex-direction: column; gap: 18px; }
.slideover-body::-webkit-scrollbar { width: 4px; }
.slideover-body::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.15); border-radius: 2px; }
.so-meta { display: flex; flex-direction: column; gap: 8px; background: rgba(15,23,42,0.5); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }
.so-meta-item { display: flex; align-items: baseline; gap: 10px; }
.so-meta-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); width: 90px; flex-shrink: 0; }
.so-resource-id { word-break: break-all; font-size: 0.82rem; }

/* Recommendation card */
.rec-card { background: rgba(14,165,233,0.05); border: 1px solid rgba(14,165,233,0.15); border-radius: 12px; padding: 18px; display: flex; flex-direction: column; gap: 14px; }
.rec-section-title { font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); margin-bottom: 6px; }
.rec-card p { margin: 0; font-size: 0.88rem; color: var(--text-muted); line-height: 1.55; }
.fix-list { margin: 0; padding-left: 18px; display: flex; flex-direction: column; gap: 6px; }
.fix-list li { font-size: 0.86rem; color: var(--text-muted); line-height: 1.5; }
.fix-list li::marker { color: var(--accent); }
.docs-link { display: inline-flex; align-items: center; gap: 6px; font-size: 0.82rem; color: var(--accent); text-decoration: none; padding: 6px 12px; border-radius: 7px; background: rgba(14,165,233,0.1); border: 1px solid rgba(14,165,233,0.2); transition: background 0.15s; }
.docs-link:hover { background: rgba(14,165,233,0.18); }

/* Raw data */
.raw-section { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.raw-title { display: flex; align-items: center; gap: 8px; padding: 10px 14px; cursor: pointer; font-size: 0.82rem; font-weight: 600; color: var(--text-muted); background: rgba(15,23,42,0.5); user-select: none; }
.raw-title:hover { color: var(--text); }
.raw-pre { margin: 0; padding: 14px; font-size: 0.75rem; background: rgba(0,0,0,0.3); color: var(--text-muted); overflow-x: auto; max-height: 260px; }

/* SO remediate */
.so-remediate { background: rgba(15,23,42,0.5); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; display: flex; flex-direction: column; gap: 10px; }

/* Transition */
.slide-fade-enter-active { transition: all 0.25s ease; }
.slide-fade-leave-active { transition: all 0.2s ease; }
.slide-fade-enter-from .slideover, .slide-fade-leave-to .slideover { transform: translateX(100%); }
.slide-fade-enter-from { opacity: 0; }
.slide-fade-leave-to   { opacity: 0; }

/* ── Remediation progress strip ── */
.rem-strip { display: flex; align-items: center; gap: 14px; padding: 10px 18px; background: rgba(15,23,42,0.5); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 14px; font-size: 0.82rem; flex-wrap: wrap; }
.rem-strip-left { display: flex; align-items: center; gap: 7px; color: var(--text-muted); flex-shrink: 0; }
.rem-pct { font-weight: 700; }
.rem-detail { color: var(--text-muted); }
.rem-bar-wrap { flex: 1; min-width: 100px; height: 7px; background: rgba(148,163,184,0.1); border-radius: 10px; overflow: hidden; }
.rem-bar { height: 100%; border-radius: 10px; transition: width 0.4s ease, background 0.3s; }

/* ── Mark fixed button ── */
.btn-mark-fixed { display: inline-flex; align-items: center; gap: 5px; padding: 4px 9px; border-radius: 6px; font-size: 0.74rem; font-weight: 600; border: none; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.btn-open  { background: rgba(148,163,184,0.1); color: var(--text-muted); }
.btn-open:hover  { background: rgba(34,197,94,0.14); color: #86efac; }
.btn-fixed { background: rgba(34,197,94,0.14); color: #86efac; }
.btn-fixed:hover { background: rgba(239,68,68,0.1); color: #fca5a5; }
.btn-mark-fixed-lg { padding: 8px 16px; font-size: 0.86rem; }

.row-fixed td { opacity: 0.5; }
.row-fixed:hover td { opacity: 0.75; }

/* SO fix status */
.so-fix-status { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.so-fixed-hint { font-size: 0.78rem; color: #86efac; }
</style>
