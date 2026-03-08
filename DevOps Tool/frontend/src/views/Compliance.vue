<template>
  <div>
    <h1>Compliance report</h1>
    <p class="muted">Check if your cloud config meets a compliance framework. Select cloud, framework, and output format.</p>

    <div class="card" style="max-width: 580px;">
      <!-- Cloud picker -->
      <div class="input-group">
        <label>Cloud provider</label>
        <div class="cloud-picker">
          <button
            v-for="c in CLOUDS" :key="c.id"
            class="cloud-pick-btn" :class="{ active: selectedCloud === c.id, ['cpb-' + c.id]: true }"
            @click="switchCloud(c.id)"
          >
            <span v-html="c.icon"></span>{{ c.label }}
          </button>
        </div>
      </div>

      <!-- Cloud info banner -->
      <div class="cloud-info-banner" :class="'banner-' + selectedCloud">
        <span v-html="currentCloud.icon"></span>
        <span>Checking <strong>{{ currentCloud.label }}</strong> against <strong>{{ currentFramework.label }}</strong></span>
      </div>

      <div class="input-group">
        <label>Framework</label>
        <select v-model="framework">
          <option v-for="f in frameworks" :key="f.value" :value="f.value">{{ f.label }}</option>
        </select>
      </div>
      <div class="input-group">
        <label>Output format</label>
        <select v-model="output">
          <option value="json">JSON + Gap suggestions</option>
          <option value="html">HTML (view in browser)</option>
          <option value="pdf">PDF (print / save)</option>
        </select>
      </div>
      <div v-if="output === 'pdf'" class="output-hint">
        <span>ℹ</span> The report will open in a new tab — use your browser's <strong>Print → Save as PDF</strong>.
      </div>
      <button class="btn btn-primary" :disabled="loading" @click="run">
        Run {{ currentCloud.label }} compliance check
      </button>
      <RunProgress :running="loading" :message="'Running ' + currentCloud.label + ' compliance check…'" />
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
        <div class="cs-item">
          <span class="cs-num" style="font-size:0.95rem;" v-html="currentCloud.icon"></span>
          <span class="cs-label">{{ currentCloud.label }}</span>
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
        <p class="muted" style="margin-bottom:16px;">Each failed control includes a specific {{ currentCloud.label }} remediation recommendation.</p>
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
                {{ currentCloud.label }} Documentation →
              </a>
            </div>
            <div v-else class="gap-rec gap-rec-generic">
              <div class="gap-rec-title">Remediation guidance</div>
              <p class="gap-rec-what">Review this control against {{ framework.toUpperCase() }} documentation and ensure the {{ currentCloud.label }} service configuration meets the requirement.</p>
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
import { ref, computed, watch, onMounted } from 'vue'
import api from '../api'
import RunProgress from '../components/RunProgress.vue'
import { openPrintWindow } from '../utils/pdf'
import { RECOMMENDATIONS } from '../utils/recommendations'

// ── Cloud definitions ────────────────────────────────────────────────────────
const CLOUDS = [
  { id: 'aws',   label: 'AWS',          icon: `<svg width="14" height="9" viewBox="0 0 80 48" fill="none"><path d="M22.9 32.2c-4.5 2.4-9.4 3.7-14.5 3.7C3.8 35.9 0 32.1 0 27.3c0-5.3 4.5-9.6 10.7-10.2-.3-1.1-.5-2.3-.5-3.6C10.2 6.1 15.9 1 22.9 1c3.4 0 6.5 1.2 8.9 3.2 2.2-4.3 6.7-7.2 11.7-7.2 4.3 0 8.2 1.9 10.8 5 1.9-.7 3.9-1.1 6-1.1C68 1 75 8 75 16.8c0 1.8-.3 3.5-.8 5.1C77.4 23.5 80 27 80 31.1 80 36.8 75.3 41 69.2 41H22.9z" fill="#FF9900"/></svg>` },
  { id: 'gcp',   label: 'Google Cloud', icon: `<svg width="14" height="14" viewBox="0 0 48 48"><path fill="#4285F4" d="M30.2 17.8H24v4.2h6.9c-.7 3.7-4 6.5-7.9 6.5-4.5 0-8.2-3.7-8.2-8.2s3.7-8.2 8.2-8.2c2.1 0 4 .8 5.5 2.1l3-3C29 8.6 26.7 7.5 24 7.5c-7.5 0-13.5 6-13.5 13.5S16.5 34.5 24 34.5c7.2 0 12.8-5 12.8-13.5 0-.8-.1-1.5-.2-2.2l-6.4-1z"/></svg>` },
  { id: 'azure', label: 'Azure',        icon: `<svg width="14" height="14" viewBox="0 0 48 48"><path fill="#0078D4" d="M27 4L13 28l9 5-7 7h16l7-36z"/><path fill="#50E6FF" d="M27 4L4 34l9-1 7-7-3-5z"/></svg>` },
]

// ── Per-cloud framework options ───────────────────────────────────────────────
const FRAMEWORKS_BY_CLOUD = {
  aws: [
    { value: 'cis',     label: 'CIS AWS Foundations Benchmark' },
    { value: 'soc2',    label: 'SOC 2' },
    { value: 'hipaa',   label: 'HIPAA' },
    { value: 'pci',     label: 'PCI DSS' },
    { value: 'iso27001',label: 'ISO/IEC 27001:2022' },
    { value: 'nist',    label: 'NIST 800-53' },
  ],
  gcp: [
    { value: 'cis_gcp', label: 'CIS Google Cloud Platform Benchmark' },
    { value: 'soc2',    label: 'SOC 2' },
    { value: 'pci',     label: 'PCI DSS' },
    { value: 'iso27001',label: 'ISO/IEC 27001:2022' },
    { value: 'nist',    label: 'NIST 800-53' },
  ],
  azure: [
    { value: 'cis_azure',label: 'CIS Microsoft Azure Foundations Benchmark' },
    { value: 'soc2',     label: 'SOC 2' },
    { value: 'hipaa',    label: 'HIPAA' },
    { value: 'pci',      label: 'PCI DSS' },
    { value: 'iso27001', label: 'ISO/IEC 27001:2022' },
    { value: 'nist',     label: 'NIST 800-53' },
  ],
}

// ── Per-cloud control keyword → recommendation key mapping ───────────────────
const CONTROL_MAPS = {
  aws: [
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
    { keywords: ['waf', 'alb', 'load balancer'],          key: 'alb.no_waf' },
    { keywords: ['ecr', 'container', 'cve'],              key: 'ecr.critical_cve' },
    { keywords: ['eks', 'kubernetes'],                    key: 'eks.public_endpoint' },
    { keywords: ['mfa', 'multi-factor'],                  key: 'iam.no_mfa' },
    { keywords: ['password', 'policy'],                   key: 'iam.password_policy_weak' },
    { keywords: ['config', 'recorder'],                   key: 'config.recorder_disabled' },
    { keywords: ['backup'],                               key: 'backup.no_plan' },
    { keywords: ['redshift', 'public'],                   key: 'redshift.publicly_accessible' },
    { keywords: ['elasticache', 'redis', 'auth'],         key: 'elasticache.no_auth' },
    { keywords: ['opensearch', 'elasticsearch'],          key: 'opensearch.public_endpoint' },
    { keywords: ['secrets', 'rotation'],                  key: 'secretsmanager.no_rotation' },
  ],
  gcp: [
    { keywords: ['firewall', 'ssh', 'port 22'],           key: 'gcp.firewall.ssh_open' },
    { keywords: ['storage', 'bucket', 'public'],          key: 'gcp.storage.public_bucket' },
    { keywords: ['iam', 'service account', 'key'],        key: 'gcp.iam.service_account_key' },
    { keywords: ['audit', 'logging'],                     key: 'gcp.logging.disabled' },
    { keywords: ['sql', 'public', 'ip'],                  key: 'gcp.sql.public_ip' },
    { keywords: ['kms', 'rotation', 'key'],               key: 'gcp.kms.no_rotation' },
    { keywords: ['vpc', 'flow'],                          key: 'gcp.vpc.no_flow_logs' },
    { keywords: ['gke', 'kubernetes', 'endpoint'],        key: 'gcp.gke.public_endpoint' },
    { keywords: ['mfa', '2-step', 'verification'],        key: 'gcp.iam.no_mfa' },
    { keywords: ['primitive', 'role', 'owner', 'editor'], key: 'gcp.iam.primitive_roles' },
    { keywords: ['bigquery', 'dataset', 'public'],        key: 'gcp.bigquery.public_dataset' },
    { keywords: ['dns', 'dnssec'],                        key: 'gcp.dns.dnssec_disabled' },
    { keywords: ['monitoring', 'alert'],                  key: 'gcp.monitoring.no_alerts' },
    { keywords: ['cloud run', 'unauthenticated'],         key: 'gcp.cloudrun.public_access' },
    { keywords: ['secret', 'rotation'],                   key: 'gcp.secretmanager.no_rotation' },
  ],
  azure: [
    { keywords: ['nsg', 'ssh', 'rdp', 'port 22'],        key: 'azure.nsg.ssh_open' },
    { keywords: ['storage', 'blob', 'public'],            key: 'azure.storage.public_blob' },
    { keywords: ['mfa', 'multi-factor', 'azure ad'],      key: 'azure.iam.no_mfa' },
    { keywords: ['sql', 'public', 'network'],             key: 'azure.sql.public_access' },
    { keywords: ['key vault', 'expiry', 'expiration'],    key: 'azure.keyvault.no_expiry' },
    { keywords: ['monitor', 'activity log', 'diagnostic'],key: 'azure.monitor.no_logs' },
    { keywords: ['aks', 'kubernetes', 'endpoint'],        key: 'azure.aks.public_endpoint' },
    { keywords: ['disk', 'encryption', 'vm'],             key: 'azure.vm.no_disk_encryption' },
    { keywords: ['storage', 'https', 'tls'],              key: 'azure.storage.no_https' },
    { keywords: ['sql', 'audit'],                         key: 'azure.sql.no_auditing' },
    { keywords: ['rbac', 'role', 'subscription'],         key: 'azure.iam.excessive_permissions' },
    { keywords: ['defender', 'security center'],          key: 'azure.defender.not_enabled' },
    { keywords: ['app service', 'http'],                  key: 'azure.appservice.http_allowed' },
    { keywords: ['cosmosdb', 'cosmos', 'public'],         key: 'azure.cosmosdb.public_endpoint' },
    { keywords: ['container registry', 'admin'],          key: 'azure.acr.admin_enabled' },
    { keywords: ['redis', 'ssl', 'port'],                 key: 'azure.redis.non_ssl_port' },
    { keywords: ['log analytics', 'retention'],           key: 'azure.loganalytics.short_retention' },
  ],
}

// ── State ────────────────────────────────────────────────────────────────────
const selectedCloud = ref('aws')
const framework     = ref('cis')
const output        = ref('json')
const loading       = ref(false)
const error         = ref('')
const result        = ref(null)
const parsedResult  = ref(null)
const showRaw       = ref(false)
const showPassed    = ref(false)
const openGaps      = ref(new Set())

const currentCloud = computed(() => CLOUDS.find(c => c.id === selectedCloud.value) || CLOUDS[0])
const frameworks   = computed(() => FRAMEWORKS_BY_CLOUD[selectedCloud.value] || FRAMEWORKS_BY_CLOUD.aws)
const currentFramework = computed(() => frameworks.value.find(f => f.value === framework.value) || frameworks.value[0])

function switchCloud(id) {
  selectedCloud.value = id
  framework.value = FRAMEWORKS_BY_CLOUD[id][0].value
  result.value = null
  parsedResult.value = null
  try { localStorage.setItem('cspm_cloud', id) } catch (_) {}
}

watch(frameworks, (list) => {
  if (!list.find(f => f.value === framework.value)) {
    framework.value = list[0].value
  }
})

onMounted(() => {
  try {
    const saved = localStorage.getItem('cspm_cloud') || 'aws'
    selectedCloud.value = saved
    framework.value = FRAMEWORKS_BY_CLOUD[saved]?.[0]?.value || 'cis'
  } catch (_) {}
})

function getGapRec(ctrl) {
  const text = ((ctrl.control_id || '') + ' ' + (ctrl.control_name || ctrl.name || ctrl.title || '') + ' ' + (ctrl.description || ctrl.reason || '')).toLowerCase()
  const map = CONTROL_MAPS[selectedCloud.value] || CONTROL_MAPS.aws
  for (const { keywords, key } of map) {
    if (keywords.some(kw => text.includes(kw))) {
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

const controls = computed(() => {
  if (!parsedResult.value) return []
  const r = parsedResult.value
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
const passCount    = computed(() => passedControls.value.length)
const failCount    = computed(() => failedControls.value.length)
const scorePercent = computed(() => {
  const total = passCount.value + failCount.value
  return total ? Math.round((passCount.value / total) * 100) : 0
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
    const data = await api.runCompliance(framework.value, reqOutput, selectedCloud.value)
    if (output.value === 'pdf' || output.value === 'html') {
      const html = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
      openPrintWindow(html, `${currentCloud.value.label} Compliance — ${framework.value.toUpperCase()}`)
    } else {
      result.value = data
      try { parsedResult.value = typeof data === 'string' ? JSON.parse(data) : data } catch (_) { parsedResult.value = null }
    }
  } catch (e) {
    error.value = e.message || 'Failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Cloud picker */
.cloud-picker { display: flex; gap: 8px; flex-wrap: wrap; }
.cloud-pick-btn {
  display: inline-flex; align-items: center; gap: 7px; padding: 7px 14px;
  border-radius: 9px; border: 1px solid var(--border); background: rgba(15,23,42,0.5);
  color: var(--text-muted); font-size: 0.87rem; font-weight: 500; cursor: pointer; transition: all 0.15s;
}
.cloud-pick-btn:hover { color: var(--text); background: rgba(255,255,255,0.05); }
.cpb-aws.active    { background: rgba(255,153,0,0.15);  border-color: rgba(255,153,0,0.4);  color: #fb923c; font-weight: 700; }
.cpb-gcp.active    { background: rgba(66,133,244,0.15); border-color: rgba(66,133,244,0.4); color: #60a5fa; font-weight: 700; }
.cpb-azure.active  { background: rgba(0,120,212,0.15);  border-color: rgba(0,120,212,0.4);  color: #93c5fd; font-weight: 700; }

.cloud-info-banner {
  display: flex; align-items: center; gap: 9px; padding: 8px 12px;
  border-radius: 8px; font-size: 0.84rem; color: var(--text-muted); margin-bottom: 4px;
}
.banner-aws   { background: rgba(255,153,0,0.07);   border: 1px solid rgba(255,153,0,0.2); }
.banner-gcp   { background: rgba(66,133,244,0.07);  border: 1px solid rgba(66,133,244,0.2); }
.banner-azure { background: rgba(0,120,212,0.07);   border: 1px solid rgba(0,120,212,0.2); }
.cloud-info-banner strong { color: var(--text); }

.output-hint {
  display: flex; align-items: flex-start; gap: 8px; font-size: 0.82rem; color: var(--text-muted);
  background: rgba(14,165,233,0.07); border: 1px solid rgba(14,165,233,0.18); border-radius: 7px;
  padding: 8px 12px; margin-bottom: 14px; line-height: 1.5;
}
.output-hint span { flex-shrink: 0; color: var(--accent); font-weight: 700; }

.results-section { display: flex; flex-direction: column; gap: 18px; }
.compliance-summary { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 14px; }
.cs-item { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.cs-num { font-size: 1.5rem; font-weight: 700; color: var(--text); line-height: 1; }
.cs-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); font-weight: 700; }
.cs-item.cs-pass .cs-num { color: #22c55e; }
.cs-item.cs-fail .cs-num { color: #ef4444; }
.cs-framework { font-size: 0.95rem; }

.compliance-bar-wrap { display: flex; align-items: center; gap: 14px; }
.compliance-bar { flex: 1; height: 10px; background: rgba(148,163,184,0.12); border-radius: 20px; overflow: hidden; }
.compliance-bar-fill { height: 100%; border-radius: 20px; transition: width 0.5s ease; }
.compliance-bar-label { font-size: 0.88rem; font-weight: 700; white-space: nowrap; }

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

.gap-rec { background: rgba(14,165,233,0.05); border: 1px solid rgba(14,165,233,0.15); border-radius: 10px; padding: 14px; }
.gap-rec-generic { background: rgba(245,158,11,0.05); border-color: rgba(245,158,11,0.15); }
.gap-rec-title { display: flex; align-items: center; gap: 7px; font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); margin-bottom: 8px; }
.gap-rec-what { font-size: 0.84rem; color: var(--text-muted); margin: 0 0 10px; line-height: 1.5; }
.gap-fix-list { margin: 0 0 10px; padding-left: 18px; display: flex; flex-direction: column; gap: 5px; }
.gap-fix-list li { font-size: 0.82rem; color: var(--text-muted); line-height: 1.45; }
.gap-fix-list li::marker { color: var(--accent); }
.gap-docs-link { font-size: 0.8rem; color: var(--accent); text-decoration: none; }
.gap-docs-link:hover { text-decoration: underline; }

.pass-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; cursor: pointer; transition: background 0.12s; }
.pass-header:hover { background: rgba(34,197,94,0.04); }
.pass-arrow { color: var(--text-muted); transition: transform 0.2s; }
.pass-arrow.open { transform: rotate(180deg); }
.passed-list { padding: 4px 20px 14px; display: flex; flex-direction: column; gap: 8px; border-top: 1px solid var(--border); }
.passed-item { display: flex; align-items: center; gap: 10px; font-size: 0.84rem; }
.passed-id   { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); width: 90px; flex-shrink: 0; }
.passed-name { color: var(--text-muted); }

.raw-toggle { display: flex; align-items: center; gap: 8px; padding: 10px 14px; cursor: pointer; font-size: 0.82rem; font-weight: 600; color: var(--text-muted); background: rgba(15,23,42,0.5); user-select: none; }
.raw-toggle:hover { color: var(--text); }
.raw-pre { margin: 0; padding: 14px; font-size: 0.75rem; background: rgba(0,0,0,0.3); color: var(--text-muted); overflow-x: auto; max-height: 400px; }
</style>
