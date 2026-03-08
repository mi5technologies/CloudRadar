<template>
  <div class="cost-view">
    <!-- Header -->
    <div class="cost-header">
      <div>
        <h1>Cost Optimisation</h1>
        <p class="muted">Detect idle resources, tagging gaps, and over-provisioned assets across all cloud providers.</p>
      </div>
      <div class="cost-header-actions">
        <button class="btn btn-primary" @click="runAnalysis" :disabled="loading">
          <svg v-if="!loading" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
            <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="spin">
            <path d="M21 12a9 9 0 11-9-9"/>
          </svg>
          {{ loading ? 'Analysing…' : 'Run analysis' }}
        </button>
        <button v-if="findings.length" class="btn btn-secondary" @click="exportCSV">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Export CSV
        </button>
      </div>
    </div>

    <!-- Cloud tabs -->
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

    <!-- ── Check Selector ── -->
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
            Deselect any check you want to deliberately skip (e.g. you know a stopped instance is intentional).
            Your selection is remembered per cloud.
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
                    <span v-if="chk.quickWin" class="qw-tag">⚡ quick win</span>
                    <span v-if="chk.est_usd > 0" class="est-usd">~${{ chk.est_usd }}/mo</span>
                  </div>
                  <div class="check-item-desc muted">{{ chk.desc }}</div>
                </div>
              </label>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- Error -->
    <div v-if="error" class="card error-card">
      <p style="color: var(--error); margin:0">{{ error }}</p>
    </div>

    <!-- No scan state -->
    <div v-else-if="!hasData && !loading" class="card no-scan-card">
      <div class="no-scan-inner">
        <div class="no-scan-icon" v-html="CLOUDS.find(c => c.id === selectedCloud)?.svg"></div>
        <div>
          <h3>No {{ cloudLabel }} cost analysis yet</h3>
          <p>Run the analysis above to identify idle resources, tagging gaps, and potential savings for your {{ cloudLabel }} environment.</p>
          <button class="btn btn-primary" style="margin-top:12px" @click="runAnalysis" :disabled="loading">
            Analyse {{ cloudLabel }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-else-if="loading" class="card loading-card">
      <div class="skeleton-row" v-for="i in 4" :key="i"></div>
    </div>

    <!-- Results -->
    <template v-else-if="hasData">
      <!-- KPI cards -->
      <div class="kpi-grid">
        <div class="kpi-card kpi-waste">
          <div class="kpi-icon-wrap" style="background: rgba(239,68,68,0.12)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
              <path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
            </svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">Idle Resources</div>
            <div class="kpi-value">{{ summary.by_category?.idle || 0 }}</div>
            <div class="kpi-sub">wasting money now</div>
          </div>
        </div>
        <div class="kpi-card kpi-savings">
          <div class="kpi-icon-wrap" style="background: rgba(34,197,94,0.12)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>
            </svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">Est. Monthly Waste</div>
            <div class="kpi-value">${{ summary.estimated_monthly_waste_usd?.toFixed(0) || '0' }}</div>
            <div class="kpi-sub">potential savings / month</div>
          </div>
        </div>
        <div class="kpi-card kpi-tagging">
          <div class="kpi-icon-wrap" style="background: rgba(234,179,8,0.12)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#eab308" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/>
              <line x1="7" y1="7" x2="7.01" y2="7"/>
            </svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">Tagging Score</div>
            <div class="kpi-value" :style="{ color: tagScoreColor }">{{ summary.tagging_score }}%</div>
            <div class="kpi-sub">cost-allocation coverage</div>
          </div>
        </div>
        <div class="kpi-card kpi-rightsizing">
          <div class="kpi-icon-wrap" style="background: rgba(99,102,241,0.12)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">Rightsizing / Reserved</div>
            <div class="kpi-value">{{ (summary.by_category?.rightsizing || 0) + (summary.by_category?.reservation || 0) }}</div>
            <div class="kpi-sub">instances to review</div>
          </div>
        </div>
      </div>

      <!-- Category breakdown bar -->
      <div class="card category-card">
        <div class="card-head">
          <h2>Findings by category</h2>
          <span class="total-badge">{{ summary.total_findings }} total</span>
        </div>
        <div class="cat-bars">
          <template v-for="cat in CATEGORIES" :key="cat.id">
            <div v-if="(summary.by_category?.[cat.id] || 0) > 0" class="cat-row">
              <div class="cat-label-row">
                <span class="cat-dot" :style="{ background: cat.color }"></span>
                <span class="cat-name">{{ cat.label }}</span>
                <span class="cat-count">{{ summary.by_category?.[cat.id] || 0 }}</span>
              </div>
              <div class="cat-bar-wrap">
                <div class="cat-bar" :style="{ width: catPct(cat.id) + '%', background: cat.color }"></div>
              </div>
            </div>
          </template>
          <div v-if="!summary.total_findings" class="empty-cat">No findings — great job!</div>
        </div>
      </div>

      <!-- Findings table -->
      <div class="card findings-card" v-if="filteredFindings.length">
        <div class="card-head">
          <h2>Waste & optimisation findings</h2>
          <div class="filter-row">
            <select v-model="filterCat" class="filter-select">
              <option value="">All categories</option>
              <option v-for="c in CATEGORIES" :key="c.id" :value="c.id">{{ c.label }}</option>
            </select>
            <select v-model="filterSev" class="filter-select">
              <option value="">All severities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
        <table class="cost-table">
          <thead>
            <tr>
              <th>Resource</th>
              <th>Category</th>
              <th>Severity</th>
              <th>Est. Waste / mo</th>
              <th>Finding</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="f in filteredFindings" :key="f.rule_id + f.resource_id"
              class="finding-row" :class="'sev-row-' + f.severity"
              @click="selectedFinding = selectedFinding === f ? null : f">
              <td>
                <div class="res-name">{{ f.resource_name }}</div>
                <div class="res-type">{{ f.resource_type }} · {{ f.region }}</div>
              </td>
              <td>
                <span class="cat-pill" :class="'cat-' + f.category">
                  {{ CATEGORY_LABEL[f.category] || f.category }}
                </span>
              </td>
              <td>
                <span class="sev-badge" :class="'sev-' + f.severity">{{ f.severity }}</span>
              </td>
              <td class="waste-usd">
                <span v-if="f.estimated_monthly_usd > 0">${{ f.estimated_monthly_usd.toFixed(0) }}</span>
                <span v-else class="muted">—</span>
              </td>
              <td class="finding-title">{{ f.title }}</td>
            </tr>
          </tbody>
        </table>

        <!-- Detail panel (slide-down on row click) -->
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

      <!-- Tagging report -->
      <div class="card tagging-card" v-if="Object.keys(taggingReport).length">
        <h2>Tagging compliance by resource type</h2>
        <p class="muted" style="margin-bottom:16px">Resources missing cost-allocation tags cannot be attributed to a team or project in billing dashboards.</p>
        <div class="tag-table-wrap">
          <table class="cost-table">
            <thead>
              <tr>
                <th>Resource type</th>
                <th>Total</th>
                <th>Missing tags</th>
                <th>Compliance</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, rt) in taggingReport" :key="rt">
                <td class="rt-cell">{{ rt }}</td>
                <td>{{ row.total }}</td>
                <td>
                  <span v-if="row.missing_tags > 0" style="color: var(--error); font-weight:600">{{ row.missing_tags }}</span>
                  <span v-else style="color: var(--success)">0</span>
                </td>
                <td>
                  <div class="tag-bar-wrap">
                    <div class="tag-bar" :style="{ width: tagCompliance(row) + '%', background: tagComplianceColor(row) }"></div>
                  </div>
                  <span class="tag-pct">{{ tagCompliance(row) }}%</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Estimated annual savings callout -->
      <div class="card savings-callout" v-if="summary.estimated_monthly_waste_usd > 0">
        <div class="savings-inner">
          <div class="savings-icon">💰</div>
          <div>
            <h3>Potential annual savings: ${{ (summary.estimated_monthly_waste_usd * 12).toFixed(0) }}</h3>
            <p>Based on {{ summary.total_waste_items }} idle resource{{ summary.total_waste_items !== 1 ? 's' : '' }} detected. Actual savings will vary based on usage patterns and reserved pricing.</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { logAudit } from '../utils/auditLog.js'

const CLOUDS = [
  { id: 'aws', label: 'AWS',
    svg: `<svg width="22" height="14" viewBox="0 0 80 48" fill="none"><path d="M22.9 32.2c-4.5 2.4-9.4 3.7-14.5 3.7C3.8 35.9 0 32.1 0 27.3c0-5.3 4.5-9.6 10.7-10.2-.3-1.1-.5-2.3-.5-3.6C10.2 6.1 15.9 1 22.9 1c3.4 0 6.5 1.2 8.9 3.2 2.2-4.3 6.7-7.2 11.7-7.2 4.3 0 8.2 1.9 10.8 5 1.9-.7 3.9-1.1 6-1.1C68 1 75 8 75 16.8c0 1.8-.3 3.5-.8 5.1C77.4 23.5 80 27 80 31.1 80 36.8 75.3 41 69.2 41H22.9z" fill="#FF9900"/></svg>` },
  { id: 'gcp', label: 'Google Cloud',
    svg: `<svg width="22" height="22" viewBox="0 0 48 48"><path fill="#4285F4" d="M30.2 17.8H24v4.2h6.9c-.7 3.7-4 6.5-7.9 6.5-4.5 0-8.2-3.7-8.2-8.2s3.7-8.2 8.2-8.2c2.1 0 4 .8 5.5 2.1l3-3C29 8.6 26.7 7.5 24 7.5c-7.5 0-13.5 6-13.5 13.5S16.5 34.5 24 34.5c7.2 0 12.8-5 12.8-13.5 0-.8-.1-1.5-.2-2.2l-6.4-1z"/></svg>` },
  { id: 'azure', label: 'Azure',
    svg: `<svg width="22" height="22" viewBox="0 0 48 48"><path fill="#0078D4" d="M27 4L13 28l9 5-7 7h16l7-36z"/><path fill="#50E6FF" d="M27 4L4 34l9-1 7-7-3-5z"/></svg>` },
]

const CATEGORIES = [
  { id: 'idle',        label: 'Idle resources',   color: '#ef4444' },
  { id: 'tagging',    label: 'Tagging gaps',      color: '#eab308' },
  { id: 'rightsizing',label: 'Rightsizing',       color: '#6366f1' },
  { id: 'reservation',label: 'Reserved pricing', color: '#0ea5e9' },
]

const CHECK_CATEGORIES = CATEGORIES

const CATEGORY_LABEL = {
  idle: 'Idle', tagging: 'Tagging', rightsizing: 'Rightsizing', reservation: 'Reserved',
}

// Full check catalogue — one entry per rule_id
const ALL_CHECKS = [
  // ── AWS ──────────────────────────────────────────────────────────────────
  { rule_id: 'cost.ebs_unattached',     cloud: 'aws', cat: 'idle',        severity: 'medium', quickWin: true,  est_usd: 8,
    title: 'Unattached EBS Volumes',
    desc:  'EBS volumes in "available" state — not attached to any instance — still incur ~$0.10/GB/month in storage charges.' },
  { rule_id: 'cost.ec2_stopped',        cloud: 'aws', cat: 'idle',        severity: 'medium', quickWin: true,  est_usd: 30,
    title: 'Stopped EC2 Instances',
    desc:  'Stopped instances continue to bill for EBS storage and any attached Elastic IPs. They do not incur compute charges.' },
  { rule_id: 'cost.rds_stopped',        cloud: 'aws', cat: 'idle',        severity: 'medium', quickWin: true,  est_usd: 60,
    title: 'Stopped RDS Instances',
    desc:  'Stopped RDS instances still bill for storage and IOPS. AWS auto-restarts them after 7 days.' },
  { rule_id: 'cost.ec2_on_demand_large',cloud: 'aws', cat: 'reservation', severity: 'low',    quickWin: false, est_usd: 200,
    title: 'Large On-Demand Instances (Savings Plan opportunity)',
    desc:  'Large instance families (M5/R5/C5 4xl+) running 24/7 on-demand cost 30–60 % more than a 1-year Reserved Instance or Savings Plan.' },
  { rule_id: 'cost.lambda_oversized',   cloud: 'aws', cat: 'rightsizing', severity: 'low',    quickWin: true,  est_usd: 5,
    title: 'Oversized Lambda Functions (≥ 8 GB memory)',
    desc:  'Lambda is billed per GB-second. Functions with 8 GB+ configured are likely over-provisioned unless processing very large payloads.' },
  { rule_id: 'cost.ec2_missing_tags',   cloud: 'aws', cat: 'tagging',     severity: 'low',    quickWin: true,  est_usd: 0,
    title: 'EC2 Instances Missing Cost-Allocation Tags',
    desc:  'Missing Owner, CostCenter, Environment, or Project tags prevents per-team cost attribution in AWS Cost Explorer.' },
  { rule_id: 'cost.rds_missing_tags',   cloud: 'aws', cat: 'tagging',     severity: 'low',    quickWin: true,  est_usd: 0,
    title: 'RDS Instances Missing Cost-Allocation Tags',
    desc:  'RDS is often a top-3 AWS cost driver. Missing tags make it impossible to attribute database costs to an application or team.' },
  { rule_id: 'cost.s3_missing_tags',    cloud: 'aws', cat: 'tagging',     severity: 'low',    quickWin: true,  est_usd: 0,
    title: 'S3 Buckets Missing Cost-Allocation Tags',
    desc:  'S3 storage costs are impossible to split across teams without bucket-level cost-allocation tags.' },

  // ── GCP ──────────────────────────────────────────────────────────────────
  { rule_id: 'cost.gce_terminated',     cloud: 'gcp', cat: 'idle',    severity: 'medium', quickWin: true,  est_usd: 25,
    title: 'Terminated GCE Instances (disks still billing)',
    desc:  'TERMINATED GCE instances keep their persistent disks attached, costing $0.04–$0.17/GB/month.' },
  { rule_id: 'cost.gce_missing_labels', cloud: 'gcp', cat: 'tagging', severity: 'low',    quickWin: true,  est_usd: 0,
    title: 'GCE Instances Missing Cost Labels',
    desc:  'GCP uses labels (owner, environment, cost-center) for billing export attribution in BigQuery. Missing labels break cost reporting.' },
  { rule_id: 'cost.gcs_missing_labels', cloud: 'gcp', cat: 'tagging', severity: 'low',    quickWin: true,  est_usd: 0,
    title: 'GCS Buckets Missing Cost Labels',
    desc:  'Cloud Storage costs are tracked by labels in GCP Billing Export. Buckets without labels cannot be attributed to teams.' },

  // ── Azure ─────────────────────────────────────────────────────────────────
  { rule_id: 'cost.azure_vm_deallocated', cloud: 'azure', cat: 'idle',    severity: 'medium', quickWin: true,  est_usd: 20,
    title: 'Deallocated Azure VMs (managed disks still billing)',
    desc:  'Deallocated VMs stop compute charges but managed disks ($5–$20+/disk/month) continue to bill.' },
  { rule_id: 'cost.azure_missing_tags',   cloud: 'azure', cat: 'tagging', severity: 'low',    quickWin: true,  est_usd: 0,
    title: 'Azure Resources Missing Cost-Allocation Tags',
    desc:  'Azure Cost Management relies on tags (Owner, CostCenter, Environment, Project) to break down subscription costs by team.' },
]

const allChecks = ALL_CHECKS

const CLOUD_LABEL = { aws: 'AWS', gcp: 'Google Cloud', azure: 'Azure' }

const selectedCloud = ref('aws')
const loading       = ref(false)
const error         = ref('')
const selectedFinding = ref(null)
const filterCat     = ref('')
const filterSev     = ref('')
const checksOpen    = ref(true)

// Per-cloud cached results
const resultsByCloud = ref({ aws: null, gcp: null, azure: null })
const summaryByCloud = ref({ aws: null, gcp: null, azure: null })

// Enabled rules — start with ALL enabled; persisted to localStorage
const _storageKey = () => `cspm_cost_enabled_${selectedCloud.value}`
const enabledRules = ref(new Set(ALL_CHECKS.map(c => c.rule_id)))

function _loadEnabled(cloud) {
  try {
    const raw = localStorage.getItem(`cspm_cost_enabled_${cloud}`)
    if (raw) {
      const arr = JSON.parse(raw)
      return new Set(arr)
    }
  } catch (_) {}
  // Default: all checks for this cloud enabled
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
  const set = new Set(enabledRules.value)
  checksForCloud(catId).forEach(c => {
    if (checked) set.add(c.rule_id); else set.delete(c.rule_id)
  })
  enabledRules.value = set
  _saveEnabled()
}

function selectAllChecks(checked) {
  const cloudChecks = ALL_CHECKS.filter(c => c.cloud === selectedCloud.value)
  const set = new Set(enabledRules.value)
  cloudChecks.forEach(c => {
    if (checked) set.add(c.rule_id); else set.delete(c.rule_id)
  })
  enabledRules.value = set
  _saveEnabled()
}

// checks relevant to selected cloud, filtered by category
function checksForCloud(catId) {
  return ALL_CHECKS.filter(c => c.cloud === selectedCloud.value && c.cat === catId)
}

function isCatAllSelected(catId) {
  return checksForCloud(catId).every(c => enabledRules.value.has(c.rule_id))
}

function isCatIndeterminate(catId) {
  const checks = checksForCloud(catId)
  const n = checks.filter(c => enabledRules.value.has(c.rule_id)).length
  return n > 0 && n < checks.length
}

const enabledCount = computed(() => {
  return ALL_CHECKS.filter(c => c.cloud === selectedCloud.value && enabledRules.value.has(c.rule_id)).length
})

const cloudLabel = computed(() => CLOUD_LABEL[selectedCloud.value])

const currentResult = computed(() => resultsByCloud.value[selectedCloud.value])
const summary = computed(() => currentResult.value?.summary || {})
const findings = computed(() => currentResult.value?.findings || [])
const taggingReport = computed(() => currentResult.value?.tagging_report || {})
const hasData = computed(() => !!currentResult.value)

const filteredFindings = computed(() => {
  return findings.value.filter(f => {
    if (filterCat.value && f.category !== filterCat.value) return false
    if (filterSev.value && f.severity !== filterSev.value) return false
    return true
  })
})

const tagScoreColor = computed(() => {
  const s = summary.value.tagging_score ?? 100
  if (s >= 80) return '#22c55e'
  if (s >= 50) return '#eab308'
  return '#ef4444'
})

function catPct(catId) {
  const total = summary.value.total_findings || 1
  return Math.round(((summary.value.by_category?.[catId] || 0) / total) * 100)
}

function tagCompliance(row) {
  if (!row.total) return 100
  return Math.round((1 - row.missing_tags / row.total) * 100)
}

function tagComplianceColor(row) {
  const p = tagCompliance(row)
  if (p >= 80) return '#22c55e'
  if (p >= 50) return '#eab308'
  return '#ef4444'
}

function selectCloud(id) {
  selectedCloud.value = id
  try { localStorage.setItem('cspm_cloud', id) } catch (_) {}
  enabledRules.value = _loadEnabled(id)
  selectedFinding.value = null
  filterCat.value = ''
  filterSev.value = ''
}

async function runAnalysis() {
  loading.value = true
  error.value = ''
  selectedFinding.value = null
  const cloud = selectedCloud.value

  try {
    const region = localStorage.getItem('cspm_region') || 'us-east-1'
    // Collect disabled rule IDs to send as skip_rules
    const cloudChecks = ALL_CHECKS.filter(c => c.cloud === cloud)
    const skipRules = cloudChecks.filter(c => !enabledRules.value.has(c.rule_id)).map(c => c.rule_id)

    const res = await fetch('/api/cost', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cloud, region, skip_rules: skipRules }),
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.error || `Server error ${res.status}`)
    }
    const data = await res.json()
    resultsByCloud.value[cloud] = data
    summaryByCloud.value[cloud] = data.summary
    logAudit('cost_analysis', `${CLOUD_LABEL[cloud]} cost analysis — ${data.summary?.total_findings || 0} findings`, 'success', cloud)
  } catch (e) {
    error.value = e.message || 'Analysis failed. Make sure the backend is running and credentials are configured.'
  } finally {
    loading.value = false
  }
}

function exportCSV() {
  if (!findings.value.length) return
  const cols = ['rule_id','resource_type','resource_id','resource_name','severity','category','estimated_monthly_usd','title','detail','region']
  const rows = findings.value.map(f => cols.map(c => JSON.stringify(f[c] ?? '')).join(','))
  const csv = [cols.join(','), ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `cost-analysis-${selectedCloud.value}-${new Date().toISOString().slice(0,10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  try { selectedCloud.value = localStorage.getItem('cspm_cloud') || 'aws' } catch (_) {}
  enabledRules.value = _loadEnabled(selectedCloud.value)
})
</script>

<style scoped>
.cost-view { max-width: 1100px; }
h1 { margin: 0 0 6px; font-size: 1.7rem; font-weight: 700; }
.cost-header { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 20px; }
.cost-header-actions { display: flex; gap: 8px; }

/* Cloud tabs */
.cloud-tabs { display: flex; gap: 6px; margin-bottom: 22px; flex-wrap: wrap; }
.cloud-tab {
  display: flex; align-items: center; gap: 8px; padding: 9px 16px;
  border-radius: 10px; border: 1px solid var(--border); cursor: pointer;
  background: var(--bg-el); color: var(--text-muted);
  font-size: 0.88rem; font-weight: 500; transition: all 0.15s;
}
.cloud-tab:hover { background: rgba(255,255,255,0.06); color: var(--text); }
.cloud-tab.active { color: var(--text); font-weight: 600; }
.cloud-tab-aws.active    { background: rgba(255,153,0,0.14);   border-color: rgba(255,153,0,0.35); }
.cloud-tab-gcp.active    { background: rgba(66,133,244,0.14);  border-color: rgba(66,133,244,0.35); }
.cloud-tab-azure.active  { background: rgba(0,120,212,0.14);   border-color: rgba(0,120,212,0.35); }
.cloud-tab-icon { display: flex; align-items: center; }
.cloud-tab-badge { padding: 1px 7px; border-radius: 20px; font-size: 0.68rem; font-weight: 700; background: rgba(14,165,233,0.15); color: var(--accent); }

/* No-scan / error */
.no-scan-card { text-align: left; }
.no-scan-inner { display: flex; align-items: flex-start; gap: 20px; padding: 10px 0; flex-wrap: wrap; }
.no-scan-icon { display: flex; align-items: center; flex-shrink: 0; }
.no-scan-icon :deep(svg) { width: 48px; height: 48px; }
.no-scan-inner h3 { margin: 0 0 6px; font-size: 1.05rem; }
.no-scan-inner p { margin: 0; font-size: 0.88rem; }
.error-card { border-color: rgba(239,68,68,0.3); }

/* Loading skeleton */
.loading-card { padding: 28px; }
.skeleton-row { height: 18px; border-radius: 8px; background: linear-gradient(90deg, var(--bg-el) 25%, var(--bg-el-hi) 50%, var(--bg-el) 75%); background-size: 400px; animation: shimmer 1.2s infinite; margin-bottom: 14px; }
@keyframes shimmer { 0%{background-position:-400px 0} 100%{background-position:400px 0} }

/* KPI grid */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px,1fr)); gap: 14px; margin-bottom: 22px; }
.kpi-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 16px; display: flex; align-items: center; gap: 14px; }
.kpi-waste    { border-left: 3px solid #ef4444; }
.kpi-savings  { border-left: 3px solid #22c55e; }
.kpi-tagging  { border-left: 3px solid #eab308; }
.kpi-rightsizing { border-left: 3px solid #6366f1; }
.kpi-icon-wrap { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.kpi-info { display: flex; flex-direction: column; gap: 2px; }
.kpi-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); font-weight: 700; }
.kpi-value { font-size: 1.4rem; font-weight: 700; color: var(--text); line-height: 1.2; }
.kpi-sub   { font-size: 0.72rem; color: var(--text-muted); }

/* Category breakdown */
.card-head { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
.total-badge { padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; background: rgba(14,165,233,0.12); color: var(--accent); }
.cat-bars { display: flex; flex-direction: column; gap: 10px; }
.cat-row { display: flex; align-items: center; gap: 12px; }
.cat-label-row { display: flex; align-items: center; gap: 7px; width: 180px; flex-shrink: 0; }
.cat-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.cat-name { font-size: 0.85rem; color: var(--text); flex: 1; }
.cat-count { font-size: 0.85rem; font-weight: 700; color: var(--text); }
.cat-bar-wrap { flex: 1; height: 10px; background: var(--bg-el); border-radius: 8px; overflow: hidden; }
.cat-bar { height: 100%; border-radius: 8px; transition: width 0.5s ease; }
.empty-cat { color: var(--text-muted); font-size: 0.88rem; }

/* Findings table */
.filter-row { display: flex; gap: 8px; flex-wrap: wrap; }
.filter-select { padding: 6px 10px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-el); color: var(--text); font-size: 0.84rem; outline: none; cursor: pointer; }
.cost-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.cost-table th { padding: 9px 12px; text-align: left; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); background: var(--bg-el-lo); white-space: nowrap; }
.cost-table td { padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
.finding-row { cursor: pointer; transition: background 0.12s; }
.finding-row:hover { background: var(--bg-el-lo); }
.sev-row-high   { border-left: 2px solid #ef4444; }
.sev-row-medium { border-left: 2px solid #eab308; }
.sev-row-low    { border-left: 2px solid #22c55e; }
.res-name { font-weight: 600; color: var(--text); }
.res-type { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }
.finding-title { max-width: 260px; }
.waste-usd { font-weight: 700; color: var(--text); white-space: nowrap; }

/* Category pills */
.cat-pill { padding: 2px 9px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; }
.cat-idle        { background: rgba(239,68,68,0.12);   color: #ef4444; }
.cat-tagging     { background: rgba(234,179,8,0.12);   color: #eab308; }
.cat-rightsizing { background: rgba(99,102,241,0.12);  color: #6366f1; }
.cat-reservation { background: rgba(14,165,233,0.12);  color: var(--accent); }

/* Severity badges */
.sev-badge { padding: 2px 8px; border-radius: 10px; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; }
.sev-high   { background: rgba(239,68,68,0.15);   color: #fca5a5; }
.sev-medium { background: rgba(234,179,8,0.15);   color: #fcd34d; }
.sev-low    { background: rgba(34,197,94,0.15);   color: #86efac; }

/* Finding detail */
.finding-detail { margin-top: 0; border-top: 1px solid var(--border); padding: 18px; background: var(--bg-el-xlo); border-radius: 0 0 12px 12px; }
.detail-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.close-btn { margin-left: auto; background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 1rem; padding: 2px 6px; }
.detail-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); margin: 12px 0 4px; }
.detail-remediation { background: var(--bg-el); border-left: 3px solid var(--accent); padding: 10px 14px; border-radius: 0 8px 8px 0; font-size: 0.85rem; line-height: 1.5; font-family: monospace; }
.detail-meta { display: flex; gap: 18px; flex-wrap: wrap; font-size: 0.78rem; color: var(--text-muted); margin-top: 12px; }
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-8px); }

/* Tagging report */
.tag-table-wrap { overflow-x: auto; }
.rt-cell { font-family: monospace; font-size: 0.82rem; }
.tag-bar-wrap { display: inline-block; width: 80px; height: 8px; background: var(--bg-el); border-radius: 8px; overflow: hidden; vertical-align: middle; margin-right: 8px; }
.tag-bar { height: 100%; border-radius: 8px; transition: width 0.4s ease; }
.tag-pct { font-weight: 700; font-size: 0.82rem; }

/* Savings callout */
.savings-callout { border-color: rgba(34,197,94,0.3); background: rgba(34,197,94,0.05); }
.savings-inner { display: flex; align-items: flex-start; gap: 16px; }
.savings-icon { font-size: 2rem; flex-shrink: 0; }
.savings-inner h3 { margin: 0 0 6px; font-size: 1.05rem; color: var(--text); }
.savings-inner p { margin: 0; font-size: 0.88rem; color: var(--text-muted); }

/* Spin animation */
@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }

/* ── Check Selector ── */
.checks-card { margin-bottom: 22px; padding: 0; overflow: hidden; }
.checks-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; cursor: pointer; user-select: none;
  transition: background 0.12s;
}
.checks-header:hover { background: var(--bg-el-lo); }
.checks-header-left { display: flex; align-items: center; gap: 10px; }
.checks-header-right { display: flex; align-items: center; gap: 8px; }
.checks-title { font-size: 0.92rem; font-weight: 600; color: var(--text); }
.checks-summary-badge { padding: 2px 9px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; background: rgba(14,165,233,0.12); color: var(--accent); }
.checks-select-all {
  padding: 4px 10px; border-radius: 7px; font-size: 0.75rem; font-weight: 600;
  background: var(--bg-el); border: 1px solid var(--border); color: var(--text-muted);
  cursor: pointer; transition: all 0.12s;
}
.checks-select-all:hover { background: var(--bg-el-hi); color: var(--text); }
.checks-arrow { transition: transform 0.2s; flex-shrink: 0; color: var(--text-muted); }
.checks-arrow.open { transform: rotate(180deg); }

.checks-body { padding: 0 18px 18px; border-top: 1px solid var(--border); }
.checks-hint { font-size: 0.82rem; margin: 12px 0 16px; }

/* Category block */
.check-cat-block { margin-bottom: 18px; }
.check-cat-header { margin-bottom: 8px; }
.check-cat-toggle {
  display: flex; align-items: center; gap: 8px; cursor: pointer;
  font-size: 0.85rem; font-weight: 600; color: var(--text);
}
.check-cat-toggle input[type="checkbox"] { cursor: pointer; width: 15px; height: 15px; flex-shrink: 0; }
.check-cat-label { font-weight: 700; }
.check-cat-count { font-weight: 400; font-size: 0.78rem; }

/* Check grid */
.check-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 8px; padding-left: 24px; }
.check-item {
  display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px;
  border-radius: 9px; border: 1px solid var(--border); background: var(--bg-el-xlo);
  cursor: pointer; transition: all 0.12s;
}
.check-item:hover { background: var(--bg-el); border-color: rgba(14,165,233,0.2); }
.check-item-disabled { opacity: 0.45; }
.check-item input[type="checkbox"] { flex-shrink: 0; margin-top: 3px; cursor: pointer; width: 14px; height: 14px; }
.check-item-body { flex: 1; min-width: 0; }
.check-item-top { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 3px; }
.check-item-name { font-size: 0.83rem; font-weight: 600; color: var(--text); }
.check-item-desc { font-size: 0.76rem; color: var(--text-muted); line-height: 1.4; }
.qw-tag { padding: 1px 6px; border-radius: 8px; font-size: 0.65rem; font-weight: 700; background: rgba(34,197,94,0.12); color: #22c55e; }
.est-usd { font-size: 0.7rem; font-weight: 700; color: var(--text-muted); }

.panel-slide-enter-active, .panel-slide-leave-active { transition: all 0.2s ease; overflow: hidden; }
.panel-slide-enter-from, .panel-slide-leave-to { opacity: 0; max-height: 0; }
.panel-slide-enter-to, .panel-slide-leave-from { max-height: 1200px; }

/* Light mode overrides */
:global(.theme-light) .cloud-tab { background: #fff !important; border-color: rgba(71,85,105,0.2) !important; color: #475569 !important; }
:global(.theme-light) .cloud-tab:hover { color: #0f172a !important; }
:global(.theme-light) .cloud-tab.active { color: #0f172a !important; }
:global(.theme-light) .kpi-card { background: #fff; border-color: rgba(71,85,105,0.18); }
:global(.theme-light) .sev-high   { background: rgba(239,68,68,0.12)  !important; color: #dc2626 !important; }
:global(.theme-light) .sev-medium { background: rgba(234,179,8,0.12)  !important; color: #b45309 !important; }
:global(.theme-light) .sev-low    { background: rgba(34,197,94,0.12)  !important; color: #15803d !important; }
:global(.theme-light) .cat-idle        { background: rgba(239,68,68,0.1)  !important; color: #dc2626 !important; }
:global(.theme-light) .cat-tagging     { background: rgba(234,179,8,0.1)  !important; color: #92400e !important; }
:global(.theme-light) .cat-rightsizing { background: rgba(99,102,241,0.1) !important; color: #4338ca !important; }
:global(.theme-light) .cat-reservation { background: rgba(2,132,199,0.1)  !important; color: #0369a1 !important; }
:global(.theme-light) .filter-select { background: #fff !important; color: #0f172a !important; border-color: rgba(71,85,105,0.25) !important; }
:global(.theme-light) .savings-callout { background: rgba(34,197,94,0.06) !important; border-color: rgba(22,163,74,0.3) !important; }
:global(.theme-light) .check-item { background: rgba(255,255,255,0.85) !important; border-color: rgba(71,85,105,0.15) !important; }
:global(.theme-light) .check-item:hover { background: #fff !important; border-color: rgba(2,132,199,0.25) !important; }
:global(.theme-light) .checks-select-all { background: #fff !important; border-color: rgba(71,85,105,0.2) !important; color: #475569 !important; }
:global(.theme-light) .checks-select-all:hover { background: rgba(2,132,199,0.06) !important; color: #0369a1 !important; }
:global(.theme-light) .qw-tag { background: rgba(34,197,94,0.12) !important; color: #15803d !important; }
</style>
