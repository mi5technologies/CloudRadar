<template>
  <div>
    <h1>Security Scan</h1>
    <p class="muted">
      Full discovery and scan of cloud assets with step-by-step progress.
      Select the services you want scanned below — deselect anything you want to skip.
    </p>

    <div v-if="!jobId">
      <!-- Cloud & options -->
      <div class="card" style="max-width: 520px;">
        <h2>Scan options</h2>
        <div class="input-group">
          <label>Cloud</label>
          <select v-model="selectedCloud">
            <option value="aws">AWS</option>
            <option value="gcp">Google Cloud</option>
            <option value="azure">Azure</option>
          </select>
        </div>
        <div class="input-group" v-if="selectedCloud === 'aws'">
          <label>Region</label>
          <input v-model="region" placeholder="us-east-1" />
        </div>
        <div class="input-group">
          <label>
            <input type="checkbox" v-model="saveSnapshot" /> Save snapshot after scan
          </label>
        </div>
      </div>

      <!-- Service selector -->
      <div class="card">
        <ScriptSelector
          title="Services to scan"
          :scripts="serviceScripts"
          v-model="selectedServices"
          :disabled="loading"
        />
        <div class="run-bar">
          <button
            class="btn btn-run"
            :disabled="loading || selectedServices.length === 0"
            @click="start"
          >
            <span v-if="loading" class="btn-spinner"></span>
            <span v-else>▶</span>
            {{ loading ? 'Starting scan…' : 'Run full security scan' }}
          </button>
          <span v-if="selectedServices.length === 0" class="run-hint warn">Select at least one service</span>
          <span v-else class="run-hint">{{ selectedServices.length }} of {{ serviceScripts.length }} services selected</span>
        </div>
        <p v-if="startError" class="muted" style="color: var(--error); margin-top: 8px;">{{ startError }}</p>
      </div>
    </div>

    <div v-else>
      <StepProgress
        title="Security scan"
        :steps="steps"
        :error="finalError"
        :done="done"
        :summary="summary"
        :downloads="downloads"
      />
      <button v-if="done" class="btn btn-secondary" @click="reset">Run another scan</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import StepProgress from '../components/StepProgress.vue'
import ScriptSelector from '../components/ScriptSelector.vue'
import api from '../api'

const serviceScripts = [
  { id: 'ec2',          name: 'EC2',                  description: 'Instances: public IPs, vulnerable AMIs, instance types, required tags.' },
  { id: 's3',           name: 'S3',                   description: 'Buckets: public-access-block, server-side encryption, bucket policies.' },
  { id: 'rds',          name: 'RDS',                  description: 'Databases: publicly accessible flag, storage encryption at rest.' },
  { id: 'lambda',       name: 'Lambda',               description: 'Functions: timeout configuration, hardcoded secret detection, tags.' },
  { id: 'iam',          name: 'IAM',                  description: 'Users & roles: wildcard actions, admin-policy attachments, unused access keys.' },
  { id: 'sg',           name: 'Security Groups',      description: 'Inbound rules: 0.0.0.0/0 open on SSH (22), RDP (3389), and other sensitive ports.' },
  { id: 'alb',          name: 'Load Balancers (ALB)', description: 'Internet-facing ALBs: WAF Web ACL association, access logging enabled.' },
  { id: 'waf',          name: 'WAF',                  description: 'Web ACLs: association to API Gateway and ALB resources.' },
  { id: 'cloudtrail',   name: 'CloudTrail',           description: 'Trails: multi-region enabled, log file validation, CloudWatch integration.' },
  { id: 'vpc',          name: 'VPC',                  description: 'Default VPC in use, VPC flow logs enabled.' },
  { id: 'ebs',          name: 'EBS Volumes',          description: 'Volumes: encryption at rest enabled.' },
  { id: 'eks',          name: 'EKS',                  description: 'Clusters: public API endpoint, control plane logging, secrets encryption.' },
  { id: 'ecs',          name: 'ECS',                  description: 'Clusters and task definitions: privileged containers, missing log config, running as root.' },
  { id: 'kms',          name: 'KMS',                  description: 'Customer-managed keys: automatic key rotation enabled.' },
  { id: 'apigateway',   name: 'API Gateway',          description: 'REST & HTTP APIs: access logging enabled, WAF attached to REST APIs.' },
  { id: 'sqs',          name: 'SQS',                  description: 'Queues: server-side encryption, public resource policy exposure.' },
  { id: 'dynamodb',     name: 'DynamoDB',             description: 'Tables: encryption at rest, point-in-time recovery (PITR) enabled.' },
  { id: 'guardduty',    name: 'GuardDuty',            description: 'Threat detection: detector enabled in the scanned region.' },
  { id: 'cloudwatch',   name: 'CloudWatch',           description: 'CIS metric filters: root usage, IAM/CloudTrail/VPC/KMS/S3 change alarms.' },
  { id: 'ecr',          name: 'ECR',                  description: 'Container images: critical and high CVE scan, image scan-on-push enabled.' },
]

const selectedCloud = ref('aws')
const region = ref('us-east-1')
const saveSnapshot = ref(true)
const selectedServices = ref(serviceScripts.map(s => s.id))

onMounted(() => {
  try { selectedCloud.value = localStorage.getItem('cspm_cloud') || 'aws' } catch (_) {}
})

const loading = ref(false)
const startError = ref('')
const jobId = ref('')
const steps = ref([])
const done = ref(false)
const summary = ref(null)
const downloads = ref([])
const finalError = ref('')
let unsubscribe = null

function pushStep(ev) {
  const s = {
    step: ev.step || ev.message || 'Step',
    status: ev.status === 'success' ? 'success' : ev.status === 'failed' ? 'failed' : ev.status || 'running',
    detail: ev.detail || null,
  }
  const last = steps.value[steps.value.length - 1]
  if (last && last.step === s.step && last.status === 'running') {
    steps.value = steps.value.slice(0, -1).concat([s])
  } else {
    steps.value = steps.value.concat([s])
  }
}

async function start() {
  loading.value = true
  startError.value = ''
  try {
    // Pass selected services as the "only" filter
    const onlyStr = selectedServices.value.length < serviceScripts.length
      ? selectedServices.value.join(',')
      : null

    const { job_id } = await api.startScan({
      cloud: selectedCloud.value,
      region: selectedCloud.value === 'aws' ? (region.value.trim() || 'us-east-1') : null,
      only: onlyStr,
      save_snapshot: saveSnapshot.value,
    })
    jobId.value = job_id
    steps.value = []
    done.value = false
    summary.value = null
    downloads.value = []
    finalError.value = ''

    await new Promise(r => setTimeout(r, 150))

    let pollTimer = null
    const normalize = (ev) => ({
      step: ev.step || ev.message || 'Step',
      status: ev.status === 'success' ? 'success' : ev.status === 'failed' ? 'failed' : ev.status || 'running',
      detail: ev.detail || null,
    })
    const poll = async () => {
      if (done.value) return
      try {
        const data = await api.getJob(job_id)
        const serverSteps = (data.steps || []).filter(ev => ev.type === 'step')
        if (serverSteps.length > 0) steps.value = serverSteps.map(normalize)
        if (data.status === 'completed' || data.status === 'failed') {
          done.value = true
          if (data.error) finalError.value = data.error
          if (data.result?.summary) summary.value = data.result.summary
          if (data.result?.downloads) downloads.value = data.result.downloads || []
          if (pollTimer) clearInterval(pollTimer)
          pollTimer = null
        }
      } catch (_) {}
    }

    unsubscribe = api.subscribeScanProgress(job_id, (ev) => {
      if (ev.type === 'step') pushStep(ev)
      else if (ev.type === 'done') {
        done.value = true
        if (ev.error) finalError.value = ev.error
        if (ev.summary) summary.value = ev.summary
        if (ev.downloads) downloads.value = ev.downloads || []
      } else if (ev.type === 'close') {
        if (unsubscribe) unsubscribe()
      }
    })

    pollTimer = setInterval(poll, 1500)
    const origUnsub = unsubscribe
    unsubscribe = () => {
      if (pollTimer) clearInterval(pollTimer)
      pollTimer = null
      if (origUnsub) origUnsub()
    }
  } catch (e) {
    startError.value = e.message || 'Failed to start scan'
  } finally {
    loading.value = false
  }
}

function reset() {
  jobId.value = ''
  steps.value = []
  done.value = false
  summary.value = null
  downloads.value = []
  finalError.value = ''
}

onUnmounted(() => { if (unsubscribe) unsubscribe() })
</script>

<style scoped>
.run-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  margin-top: 6px;
}
.btn-run {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: linear-gradient(135deg, #0ea5e9, #6366f1);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-run:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.btn-run:not(:disabled):hover { opacity: 0.88; }
.btn-spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.run-hint { font-size: 0.82rem; color: var(--text-muted); }
.run-hint.warn { color: #f97316; }
</style>
