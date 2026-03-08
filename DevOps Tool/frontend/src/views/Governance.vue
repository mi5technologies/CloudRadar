<template>
  <div>
    <h1>Governance report</h1>
    <p class="muted">Check tagging, resource policies, and governance rules for your cloud environment.</p>

    <div class="card">
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
        <span>Running <strong>{{ govScripts.length }} governance checks</strong> against <strong>{{ currentCloud.label }}</strong></span>
      </div>

      <div class="input-group" style="max-width: 240px; margin-top: 14px;">
        <label>Output format</label>
        <select v-model="output">
          <option value="json">JSON</option>
          <option value="html">HTML (view in browser)</option>
          <option value="pdf">PDF (print / save)</option>
        </select>
      </div>
      <div v-if="output === 'pdf'" class="output-hint">
        <span>ℹ</span> The report will open in a new tab — use your browser's <strong>Print → Save as PDF</strong>.
      </div>

      <ScriptSelector
        :title="'Governance checks — ' + currentCloud.label"
        :scripts="govScripts"
        v-model="selectedChecks"
        :disabled="loading"
      />

      <div class="run-bar">
        <button
          class="btn btn-run"
          :disabled="loading || selectedChecks.length === 0"
          @click="run"
        >
          <span v-if="loading" class="btn-spinner"></span>
          <span v-else>▶</span>
          {{ loading ? 'Running report…' : 'Run ' + currentCloud.label + ' governance report' }}
        </button>
        <span v-if="selectedChecks.length === 0" class="run-hint warn">Select at least one check</span>
        <span v-else class="run-hint">{{ selectedChecks.length }} of {{ govScripts.length }} checks selected</span>
      </div>

      <p v-if="error" class="muted" style="color: var(--error); margin-top: 8px;">{{ error }}</p>
    </div>

    <div v-if="result && output === 'json'" class="card">
      <h2>Result</h2>
      <pre>{{ typeof result === 'string' ? result.slice(0, 4000) : JSON.stringify(result, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '../api'
import ScriptSelector from '../components/ScriptSelector.vue'
import { openPrintWindow } from '../utils/pdf'

const CLOUDS = [
  { id: 'aws',   label: 'AWS',          icon: `<svg width="14" height="9" viewBox="0 0 80 48" fill="none"><path d="M22.9 32.2c-4.5 2.4-9.4 3.7-14.5 3.7C3.8 35.9 0 32.1 0 27.3c0-5.3 4.5-9.6 10.7-10.2-.3-1.1-.5-2.3-.5-3.6C10.2 6.1 15.9 1 22.9 1c3.4 0 6.5 1.2 8.9 3.2 2.2-4.3 6.7-7.2 11.7-7.2 4.3 0 8.2 1.9 10.8 5 1.9-.7 3.9-1.1 6-1.1C68 1 75 8 75 16.8c0 1.8-.3 3.5-.8 5.1C77.4 23.5 80 27 80 31.1 80 36.8 75.3 41 69.2 41H22.9z" fill="#FF9900"/></svg>` },
  { id: 'gcp',   label: 'Google Cloud', icon: `<svg width="14" height="14" viewBox="0 0 48 48"><path fill="#4285F4" d="M30.2 17.8H24v4.2h6.9c-.7 3.7-4 6.5-7.9 6.5-4.5 0-8.2-3.7-8.2-8.2s3.7-8.2 8.2-8.2c2.1 0 4 .8 5.5 2.1l3-3C29 8.6 26.7 7.5 24 7.5c-7.5 0-13.5 6-13.5 13.5S16.5 34.5 24 34.5c7.2 0 12.8-5 12.8-13.5 0-.8-.1-1.5-.2-2.2l-6.4-1z"/></svg>` },
  { id: 'azure', label: 'Azure',        icon: `<svg width="14" height="14" viewBox="0 0 48 48"><path fill="#0078D4" d="M27 4L13 28l9 5-7 7h16l7-36z"/><path fill="#50E6FF" d="M27 4L4 34l9-1 7-7-3-5z"/></svg>` },
]

const GOV_SCRIPTS = {
  aws: [
    { id: 'tags',         name: 'Tag Compliance',               description: 'Checks all AWS resources for required tags (Environment, Owner, CostCenter, Project). Reports missing, incorrect, or inconsistently named tags.' },
    { id: 'policy',       name: 'Resource Policy Checks',       description: 'Validates AWS resource policies: forbidden instance types in production, minimum backup retention, required encryption on EBS/RDS/S3.' },
    { id: 'violations',   name: 'Policy Violations',            description: 'Detects AWS resources violating governance policies: publicly exposed resources, unencrypted storage, over-privileged IAM roles.' },
    { id: 'cost_govern',  name: 'Cost Governance',              description: 'Identifies cost governance issues: oversized EC2 instances, unattached EBS volumes, unused Elastic IPs, old EBS snapshots.' },
    { id: 'service_scp',  name: 'Service Control Policies',     description: 'Verifies AWS Organizations SCPs are in place to restrict high-risk actions (e.g. disabling CloudTrail, deleting GuardDuty detector).' },
  ],
  gcp: [
    { id: 'labels',       name: 'Label Compliance',             description: 'Checks all GCP resources (VMs, buckets, SQL instances) for required labels (environment, owner, cost-centre, team). Reports missing or incorrect labels.' },
    { id: 'policy',       name: 'Org Policy Checks',            description: 'Verifies GCP Organization Policies: constraints/compute.disableSerialPortAccess, constraints/storage.uniformBucketLevelAccess, constraints/iam.allowedPolicyMemberDomains.' },
    { id: 'violations',   name: 'Policy Violations',            description: 'Detects GCP resources violating governance policies: public Cloud Storage buckets, Compute instances without OS Login, default service accounts with editor role.' },
    { id: 'cost_govern',  name: 'Cost Governance',              description: 'Identifies GCP cost governance issues: idle Compute Engine VMs, oversized instance types, unattached Persistent Disks, old Snapshots.' },
    { id: 'project_iam',  name: 'Project IAM Governance',       description: 'Checks for project-level IAM bindings that violate governance: primitive roles (Owner/Editor), external users with access, too many project owners.' },
  ],
  azure: [
    { id: 'tags',         name: 'Tag Compliance',               description: 'Checks all Azure resources and resource groups for required tags (Environment, Owner, CostCenter, Department). Reports resources missing required tags.' },
    { id: 'policy',       name: 'Azure Policy Compliance',      description: 'Evaluates Azure Policy assignments and reports non-compliant resources. Covers built-in policies for encryption, HTTPS-only, network access, and tagging.' },
    { id: 'violations',   name: 'Policy Violations',            description: 'Detects Azure resources violating governance policies: public storage accounts, VMs without disk encryption, NSGs with dangerous open rules.' },
    { id: 'cost_govern',  name: 'Cost Governance',              description: 'Identifies Azure cost governance issues: oversized VMs, unattached Managed Disks, unused Public IPs, old snapshots, underutilised App Service plans.' },
    { id: 'rbac_govern',  name: 'RBAC Governance',              description: 'Checks Azure RBAC for governance violations: too many subscription Owners, direct user assignments (should use groups), classic co-administrator roles still active.' },
  ],
}

const selectedCloud  = ref('aws')
const output         = ref('json')
const loading        = ref(false)
const error          = ref('')
const result         = ref(null)

const currentCloud = computed(() => CLOUDS.find(c => c.id === selectedCloud.value) || CLOUDS[0])
const govScripts   = computed(() => GOV_SCRIPTS[selectedCloud.value] || GOV_SCRIPTS.aws)
const selectedChecks = ref(GOV_SCRIPTS.aws.map(s => s.id))

function switchCloud(id) {
  selectedCloud.value = id
  selectedChecks.value = GOV_SCRIPTS[id].map(s => s.id)
  result.value = null
  try { localStorage.setItem('cspm_cloud', id) } catch (_) {}
}

watch(govScripts, (list) => { selectedChecks.value = list.map(s => s.id) })

onMounted(() => {
  try {
    const saved = localStorage.getItem('cspm_cloud') || 'aws'
    selectedCloud.value = saved
    selectedChecks.value = GOV_SCRIPTS[saved]?.map(s => s.id) || GOV_SCRIPTS.aws.map(s => s.id)
  } catch (_) {}
})

async function run() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const reqOutput = output.value === 'pdf' ? 'html' : output.value
    const data = await api.runGovernance(reqOutput, selectedChecks.value, selectedCloud.value)
    if (output.value === 'pdf' || output.value === 'html') {
      const html = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
      openPrintWindow(html, `${currentCloud.value.label} Governance Report`)
    } else {
      result.value = data
    }
  } catch (e) {
    error.value = e.message || 'Failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.cloud-picker { display: flex; gap: 8px; flex-wrap: wrap; }
.cloud-pick-btn {
  display: inline-flex; align-items: center; gap: 7px; padding: 7px 14px;
  border-radius: 9px; border: 1px solid var(--border); background: var(--bg-el);
  color: var(--text-muted); font-size: 0.87rem; font-weight: 500; cursor: pointer; transition: all 0.15s;
}
.cloud-pick-btn:hover { color: var(--text); background: rgba(255,255,255,0.05); }
.cpb-aws.active    { background: rgba(255,153,0,0.15);  border-color: rgba(255,153,0,0.4);  color: #fb923c; font-weight: 700; }
.cpb-gcp.active    { background: rgba(66,133,244,0.15); border-color: rgba(66,133,244,0.4); color: #60a5fa; font-weight: 700; }
.cpb-azure.active  { background: rgba(0,120,212,0.15);  border-color: rgba(0,120,212,0.4);  color: #93c5fd; font-weight: 700; }

.cloud-info-banner {
  display: flex; align-items: center; gap: 9px; padding: 8px 12px;
  border-radius: 8px; font-size: 0.84rem; color: var(--text-muted);
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
.run-bar {
  display: flex; align-items: center; gap: 14px; padding-top: 14px; border-top: 1px solid var(--border); margin-top: 6px;
}
.btn-run {
  display: inline-flex; align-items: center; gap: 8px; padding: 10px 24px;
  background: linear-gradient(135deg, #0ea5e9, #6366f1); color: #fff; border: none;
  border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; transition: opacity 0.2s;
}
.btn-run:disabled { opacity: 0.45; cursor: not-allowed; }
.btn-run:not(:disabled):hover { opacity: 0.88; }
.btn-spinner {
  width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.run-hint { font-size: 0.82rem; color: var(--text-muted); }
.run-hint.warn { color: #f97316; }
</style>
