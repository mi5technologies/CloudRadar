<template>
  <div>
    <h1>Vulnerabilities</h1>
    <p class="muted">
      Scan for known CVEs in container images, check host/OS vulnerability status, and detect exposed secrets.
      Select the cloud provider and checks you want to run below.
    </p>

    <div class="card" style="max-width: 600px;">
      <!-- Cloud picker -->
      <div class="input-group">
        <label>Cloud provider</label>
        <div class="cloud-picker">
          <button
            v-for="c in CLOUDS"
            :key="c.id"
            class="cloud-pick-btn"
            :class="{ active: selectedCloud === c.id, ['cpb-' + c.id]: true }"
            @click="switchCloud(c.id)"
          >
            <span v-html="c.icon"></span>{{ c.label }}
          </button>
        </div>
      </div>

      <!-- Region / Project / Subscription -->
      <div class="input-group" v-if="selectedCloud === 'aws'">
        <label>Region</label>
        <input v-model="region" placeholder="us-east-1" />
      </div>
      <div class="input-group" v-if="selectedCloud === 'gcp'">
        <label>Project ID</label>
        <input v-model="projectId" placeholder="my-gcp-project-id" />
      </div>
      <div class="input-group" v-if="selectedCloud === 'azure'">
        <label>Subscription ID</label>
        <input v-model="subscriptionId" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
      </div>

      <ScriptSelector
        :title="'Vulnerability checks — ' + currentCloud.label"
        :scripts="vulnScripts"
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
          {{ loading ? 'Scanning…' : 'Run ' + currentCloud.label + ' vulnerability scan' }}
        </button>
        <span v-if="selectedChecks.length === 0" class="run-hint warn">Select at least one check</span>
        <span v-else class="run-hint">{{ selectedChecks.length }} of {{ vulnScripts.length }} checks selected</span>
      </div>

      <p v-if="error" class="muted" style="color: var(--error); margin-top: 8px;">{{ error }}</p>
    </div>

    <div v-if="result" class="card">
      <h2>Result</h2>
      <pre>{{ JSON.stringify(result, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '../api'
import ScriptSelector from '../components/ScriptSelector.vue'

const CLOUDS = [
  { id: 'aws',   label: 'AWS',           icon: `<svg width="14" height="9" viewBox="0 0 80 48" fill="none"><path d="M22.9 32.2c-4.5 2.4-9.4 3.7-14.5 3.7C3.8 35.9 0 32.1 0 27.3c0-5.3 4.5-9.6 10.7-10.2-.3-1.1-.5-2.3-.5-3.6C10.2 6.1 15.9 1 22.9 1c3.4 0 6.5 1.2 8.9 3.2 2.2-4.3 6.7-7.2 11.7-7.2 4.3 0 8.2 1.9 10.8 5 1.9-.7 3.9-1.1 6-1.1C68 1 75 8 75 16.8c0 1.8-.3 3.5-.8 5.1C77.4 23.5 80 27 80 31.1 80 36.8 75.3 41 69.2 41H22.9z" fill="#FF9900"/></svg>` },
  { id: 'gcp',   label: 'Google Cloud',  icon: `<svg width="14" height="14" viewBox="0 0 48 48"><path fill="#4285F4" d="M30.2 17.8H24v4.2h6.9c-.7 3.7-4 6.5-7.9 6.5-4.5 0-8.2-3.7-8.2-8.2s3.7-8.2 8.2-8.2c2.1 0 4 .8 5.5 2.1l3-3C29 8.6 26.7 7.5 24 7.5c-7.5 0-13.5 6-13.5 13.5S16.5 34.5 24 34.5c7.2 0 12.8-5 12.8-13.5 0-.8-.1-1.5-.2-2.2l-6.4-1z"/></svg>` },
  { id: 'azure', label: 'Azure',         icon: `<svg width="14" height="14" viewBox="0 0 48 48"><path fill="#0078D4" d="M27 4L13 28l9 5-7 7h16l7-36z"/><path fill="#50E6FF" d="M27 4L4 34l9-1 7-7-3-5z"/></svg>` },
]

const AWS_VULN = [
  { id: 'ecr',      name: 'ECR Image Scan',              description: 'Scans all ECR container image repositories for critical and high CVEs using AWS Inspector / ECR native scanning.' },
  { id: 'ami',      name: 'AMI Vulnerability Check',     description: 'Checks EC2 instances for deprecated AMIs (>180 days), public AMI usage, and known-vulnerable image IDs.' },
  { id: 'inspector',name: 'Amazon Inspector',            description: 'Checks whether Amazon Inspector v2 is enabled and aggregates its findings for EC2, Lambda, and container workloads.' },
  { id: 'ssm_patch',name: 'Systems Manager Patch Compliance', description: 'Reports patch compliance status for EC2 instances managed by AWS Systems Manager.' },
]

const GCP_VULN = [
  { id: 'artifact_registry', name: 'Artifact Registry Image Scan',        description: 'Scans container images in Artifact Registry for critical and high CVEs using Container Analysis.' },
  { id: 'container_registry',name: 'Container Registry CVE Scan',         description: 'Scans images in legacy Container Registry (gcr.io) for known vulnerabilities.' },
  { id: 'os_inventory',      name: 'VM Manager OS Vulnerability Report',  description: 'Uses VM Manager to report installed packages with known CVEs on Compute Engine instances.' },
  { id: 'scc_vulns',         name: 'Security Command Center Findings',    description: 'Pulls vulnerability findings (MEDIUM+ severity) from Security Command Center for the project.' },
]

const AZURE_VULN = [
  { id: 'acr_scan',         name: 'Container Registry Image Scan',        description: 'Scans images in Azure Container Registry for critical and high CVEs using Microsoft Defender for Containers.' },
  { id: 'aks_vuln',         name: 'AKS Cluster Node Vulnerabilities',     description: 'Checks AKS node pool OS patch status and running container images for known CVEs via Defender for Containers.' },
  { id: 'vm_assess',        name: 'VM Vulnerability Assessment',          description: 'Aggregates vulnerability assessment findings from Defender for Cloud for all Virtual Machines.' },
  { id: 'defender_alerts',  name: 'Defender for Cloud Alerts',            description: 'Pulls active security alerts and recommendations from Microsoft Defender for Cloud at the subscription level.' },
]

const selectedCloud  = ref('aws')
const region         = ref('us-east-1')
const projectId      = ref('')
const subscriptionId = ref('')
const loading        = ref(false)
const error          = ref('')
const result         = ref(null)

const currentCloud = computed(() => CLOUDS.find(c => c.id === selectedCloud.value) || CLOUDS[0])

const vulnScripts = computed(() => {
  if (selectedCloud.value === 'gcp')   return GCP_VULN
  if (selectedCloud.value === 'azure') return AZURE_VULN
  return AWS_VULN
})

const selectedChecks = ref(AWS_VULN.map(s => s.id))

watch(selectedCloud, (cloud) => {
  const list = cloud === 'gcp' ? GCP_VULN : cloud === 'azure' ? AZURE_VULN : AWS_VULN
  selectedChecks.value = list.map(s => s.id)
  result.value = null
})

function switchCloud(id) { selectedCloud.value = id }

onMounted(() => {
  try {
    const saved = localStorage.getItem('cspm_cloud') || 'aws'
    selectedCloud.value = saved
    const list = saved === 'gcp' ? GCP_VULN : saved === 'azure' ? AZURE_VULN : AWS_VULN
    selectedChecks.value = list.map(s => s.id)
  } catch (_) {}
})

async function run() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const payload = {
      cloud: selectedCloud.value,
      checks: selectedChecks.value,
    }
    if (selectedCloud.value === 'aws')   payload.region = region.value.trim() || 'us-east-1'
    if (selectedCloud.value === 'gcp')   payload.project_id = projectId.value.trim() || null
    if (selectedCloud.value === 'azure') payload.subscription_id = subscriptionId.value.trim() || null
    result.value = await api.runVulnerabilities(payload.region || payload.project_id || '', selectedChecks.value)
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
  display: inline-flex; align-items: center; gap: 7px;
  padding: 7px 14px; border-radius: 9px; border: 1px solid var(--border);
  background: var(--bg-el); color: var(--text-muted);
  font-size: 0.87rem; font-weight: 500; cursor: pointer; transition: all 0.15s;
}
.cloud-pick-btn:hover { color: var(--text); background: rgba(255,255,255,0.05); }
.cpb-aws.active    { background: rgba(255,153,0,0.15);  border-color: rgba(255,153,0,0.4);  color: #fb923c; font-weight: 700; }
.cpb-gcp.active    { background: rgba(66,133,244,0.15); border-color: rgba(66,133,244,0.4); color: #60a5fa; font-weight: 700; }
.cpb-azure.active  { background: rgba(0,120,212,0.15);  border-color: rgba(0,120,212,0.4);  color: #93c5fd; font-weight: 700; }
.run-bar {
  display: flex; align-items: center; gap: 14px;
  padding-top: 14px; border-top: 1px solid var(--border); margin-top: 6px;
}
.btn-run {
  display: inline-flex; align-items: center; gap: 8px; padding: 10px 24px;
  background: linear-gradient(135deg, #0ea5e9, #6366f1);
  color: #fff; border: none; border-radius: 8px;
  font-size: 0.95rem; font-weight: 600; cursor: pointer; transition: opacity 0.2s;
}
.btn-run:disabled { opacity: 0.45; cursor: not-allowed; }
.btn-run:not(:disabled):hover { opacity: 0.88; }
.btn-spinner {
  width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff; border-radius: 50%;
  animation: spin 0.7s linear infinite; flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.run-hint { font-size: 0.82rem; color: var(--text-muted); }
.run-hint.warn { color: #f97316; }
</style>
