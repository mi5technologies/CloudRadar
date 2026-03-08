<template>
  <div>
    <h1>Security Scan</h1>
    <p class="muted">
      Full discovery and scan of cloud assets with step-by-step progress.
      Select the services you want scanned below — deselect anything you want to skip.
    </p>

    <!-- Mode toggle -->
    <div class="mode-toggle-row" v-if="!jobId && !multiDone">
      <button
        class="mode-btn" :class="{ active: !multiMode }"
        @click="multiMode = false"
      >Single cloud scan</button>
      <button
        class="mode-btn" :class="{ active: multiMode }"
        @click="multiMode = true"
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 12H2M2 12l5-5M2 12l5 5"/><path d="M22 6H11M22 18H11"/></svg>
        Scan all clouds in parallel
      </button>
    </div>

    <!-- ── MULTI-CLOUD PARALLEL SCAN ── -->
    <div v-if="multiMode && !jobId && !multiDone" class="multi-scan-panel">
      <div class="card" style="max-width: 700px;">
        <h2>Parallel multi-cloud scan</h2>
        <p class="muted" style="margin-bottom: 18px;">
          Runs security scans on all configured clouds simultaneously. Each cloud shows its own progress stream.
          Only clouds with credentials saved on the server will be scanned.
        </p>

        <div class="multi-cloud-grid">
          <div
            v-for="c in CLOUDS" :key="c.id"
            class="multi-cloud-card" :class="['mc-' + c.id, multiTargets.has(c.id) ? 'mc-selected' : '']"
            @click="toggleMultiTarget(c.id)"
          >
            <div class="mc-check">
              <svg v-if="multiTargets.has(c.id)" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
            <span v-html="c.icon"></span>
            <span class="mc-label">{{ c.label }}</span>
            <span v-if="connectedClouds.has(c.id)" class="mc-status-ok">✓ creds set</span>
            <span v-else class="mc-status-none">no creds</span>
          </div>
        </div>

        <!-- Per-cloud config fields for selected targets -->
        <div v-if="multiTargets.has('aws')" class="input-group" style="max-width: 280px;">
          <label>AWS Region</label>
          <input v-model="region" placeholder="us-east-1" />
        </div>
        <div v-if="multiTargets.has('gcp')" class="input-group" style="max-width: 280px;">
          <label>GCP Project ID</label>
          <input v-model="projectId" placeholder="my-gcp-project-id" />
        </div>
        <div v-if="multiTargets.has('azure')" class="input-group" style="max-width: 340px;">
          <label>Azure Subscription ID</label>
          <input v-model="subscriptionId" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
        </div>

        <div class="input-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="saveSnapshot" /> Save snapshots after scan
          </label>
        </div>

        <div class="run-bar">
          <button
            class="btn btn-run"
            :disabled="multiLoading || multiTargets.size === 0"
            @click="startMulti"
          >
            <span v-if="multiLoading" class="btn-spinner"></span>
            <span v-else>▶</span>
            {{ multiLoading ? 'Starting scans…' : 'Run ' + multiTargets.size + ' cloud scan' + (multiTargets.size !== 1 ? 's' : '') + ' in parallel' }}
          </button>
          <span v-if="multiTargets.size === 0" class="run-hint warn">Select at least one cloud</span>
        </div>
        <p v-if="multiError" class="muted" style="color: var(--error); margin-top: 8px;">{{ multiError }}</p>
      </div>
    </div>

    <!-- ── MULTI-CLOUD PARALLEL PROGRESS ── -->
    <div v-if="multiMode && (multiJobs.length > 0 || multiDone)" class="multi-progress-grid">
      <div
        v-for="job in multiJobs" :key="job.cloud"
        class="multi-progress-card" :class="'mpc-' + job.cloud"
      >
        <div class="mpc-header">
          <span v-html="CLOUDS.find(c => c.id === job.cloud)?.icon || ''"></span>
          <strong>{{ CLOUDS.find(c => c.id === job.cloud)?.label }}</strong>
          <span class="mpc-status" :class="'mpc-' + (job.done ? (job.error ? 'fail' : 'ok') : 'running')">
            {{ job.done ? (job.error ? 'Failed' : 'Complete') : 'Running…' }}
          </span>
        </div>
        <StepProgress
          :title="''"
          :steps="job.steps"
          :error="job.error"
          :done="job.done"
          :summary="job.summary"
          :downloads="job.downloads"
          compact
        />
      </div>
    </div>
    <div v-if="multiDone" class="multi-done-bar">
      <span>All cloud scans complete.</span>
      <button class="btn btn-secondary" @click="resetMulti">Run new scans</button>
    </div>

    <!-- ── SINGLE CLOUD SCAN ── -->
    <div v-if="!multiMode && !jobId">
      <!-- Cloud & options -->
      <div class="card" style="max-width: 560px;">
        <h2>Scan options</h2>
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
              <span v-html="c.icon"></span>
              {{ c.label }}
            </button>
          </div>
        </div>

        <!-- AWS: region -->
        <div class="input-group" v-if="selectedCloud === 'aws'">
          <label>Region</label>
          <input v-model="region" placeholder="us-east-1" />
        </div>

        <!-- GCP: project ID -->
        <div class="input-group" v-if="selectedCloud === 'gcp'">
          <label>Project ID</label>
          <input v-model="projectId" placeholder="my-gcp-project-id" />
        </div>

        <!-- Azure: subscription -->
        <div class="input-group" v-if="selectedCloud === 'azure'">
          <label>Subscription ID</label>
          <input v-model="subscriptionId" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
        </div>

        <div class="input-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="saveSnapshot" /> Save snapshot after scan
          </label>
        </div>

        <!-- Cloud info banner -->
        <div class="cloud-info-banner" :class="'banner-' + selectedCloud">
          <span class="banner-icon" v-html="currentCloud.icon"></span>
          <div>
            <strong>{{ currentCloud.label }} scan</strong> — scanning
            {{ serviceScripts.length }} services using {{ currentCloud.apiLabel }}
          </div>
        </div>
      </div>

      <!-- Service selector -->
      <div class="card">
        <ScriptSelector
          :title="'Services to scan — ' + currentCloud.label"
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
            {{ loading ? 'Starting scan…' : 'Run ' + currentCloud.label + ' security scan' }}
          </button>
          <span v-if="selectedServices.length === 0" class="run-hint warn">Select at least one service</span>
          <span v-else class="run-hint">{{ selectedServices.length }} of {{ serviceScripts.length }} services selected</span>
        </div>
        <p v-if="startError" class="muted" style="color: var(--error); margin-top: 8px;">{{ startError }}</p>
      </div>
    </div>

    <div v-if="!multiMode && jobId">
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import StepProgress from '../components/StepProgress.vue'
import ScriptSelector from '../components/ScriptSelector.vue'
import api from '../api'

// ── Cloud definitions ────────────────────────────────────────────────────────
const CLOUDS = [
  {
    id: 'aws', label: 'AWS', apiLabel: 'AWS APIs',
    icon: `<svg width="16" height="10" viewBox="0 0 80 48" fill="none"><path d="M22.9 32.2c-4.5 2.4-9.4 3.7-14.5 3.7C3.8 35.9 0 32.1 0 27.3c0-5.3 4.5-9.6 10.7-10.2-.3-1.1-.5-2.3-.5-3.6C10.2 6.1 15.9 1 22.9 1c3.4 0 6.5 1.2 8.9 3.2 2.2-4.3 6.7-7.2 11.7-7.2 4.3 0 8.2 1.9 10.8 5 1.9-.7 3.9-1.1 6-1.1C68 1 75 8 75 16.8c0 1.8-.3 3.5-.8 5.1C77.4 23.5 80 27 80 31.1 80 36.8 75.3 41 69.2 41H22.9z" fill="#FF9900"/></svg>`,
  },
  {
    id: 'gcp', label: 'Google Cloud', apiLabel: 'Google Cloud APIs',
    icon: `<svg width="16" height="16" viewBox="0 0 48 48"><path fill="#4285F4" d="M30.2 17.8H24v4.2h6.9c-.7 3.7-4 6.5-7.9 6.5-4.5 0-8.2-3.7-8.2-8.2s3.7-8.2 8.2-8.2c2.1 0 4 .8 5.5 2.1l3-3C29 8.6 26.7 7.5 24 7.5c-7.5 0-13.5 6-13.5 13.5S16.5 34.5 24 34.5c7.2 0 12.8-5 12.8-13.5 0-.8-.1-1.5-.2-2.2l-6.4-1z"/></svg>`,
  },
  {
    id: 'azure', label: 'Azure', apiLabel: 'Azure Resource Manager APIs',
    icon: `<svg width="16" height="16" viewBox="0 0 48 48"><path fill="#0078D4" d="M27 4L13 28l9 5-7 7h16l7-36z"/><path fill="#50E6FF" d="M27 4L4 34l9-1 7-7-3-5z"/></svg>`,
  },
]

// ── Per-cloud service lists ──────────────────────────────────────────────────
const AWS_SERVICES = [
  { id: 'ec2',        name: 'EC2',                   description: 'Instances: public IPs, vulnerable AMIs, instance types, required tags.' },
  { id: 's3',         name: 'S3',                    description: 'Buckets: public-access-block, server-side encryption, bucket policies.' },
  { id: 'rds',        name: 'RDS',                   description: 'Databases: publicly accessible flag, storage encryption at rest.' },
  { id: 'lambda',     name: 'Lambda',                description: 'Functions: timeout configuration, hardcoded secret detection, tags.' },
  { id: 'iam',        name: 'IAM',                   description: 'Users & roles: MFA, wildcard actions, admin-policy attachments, unused keys, password policy, root usage.' },
  { id: 'sg',         name: 'Security Groups',       description: 'Inbound rules: 0.0.0.0/0 open on SSH (22), RDP (3389), and other sensitive ports.' },
  { id: 'alb',        name: 'Load Balancers (ALB)',  description: 'Internet-facing ALBs: WAF Web ACL association, access logging enabled.' },
  { id: 'waf',        name: 'WAF',                   description: 'Web ACLs: association to API Gateway and ALB resources.' },
  { id: 'cloudtrail', name: 'CloudTrail',            description: 'Trails: multi-region enabled, log file validation, CloudWatch integration.' },
  { id: 'vpc',        name: 'VPC',                   description: 'Default VPC in use, VPC flow logs, Network ACLs.' },
  { id: 'ebs',        name: 'EBS Volumes',           description: 'Volumes: encryption at rest, snapshots publicly shared.' },
  { id: 'eks',        name: 'EKS',                   description: 'Clusters: public API endpoint, control plane logging, secrets encryption.' },
  { id: 'ecs',        name: 'ECS',                   description: 'Task definitions: privileged containers, missing log config, running as root.' },
  { id: 'kms',        name: 'KMS',                   description: 'Customer-managed keys: automatic key rotation enabled.' },
  { id: 'apigateway', name: 'API Gateway',           description: 'REST & HTTP APIs: access logging enabled, WAF attached to REST APIs.' },
  { id: 'sqs',        name: 'SQS',                   description: 'Queues: server-side encryption, public resource policy exposure.' },
  { id: 'dynamodb',   name: 'DynamoDB',              description: 'Tables: encryption at rest, point-in-time recovery (PITR) enabled.' },
  { id: 'guardduty',  name: 'GuardDuty',             description: 'Threat detection: detector enabled in the scanned region.' },
  { id: 'cloudwatch', name: 'CloudWatch',            description: 'CIS metric filters: root usage, IAM/CloudTrail/VPC/KMS/S3 change alarms.' },
  { id: 'ecr',        name: 'ECR',                   description: 'Container images: critical and high CVE scan, image scan-on-push enabled.' },
  { id: 'cognito',    name: 'Cognito',               description: 'User pools: MFA not required, no advanced security mode, weak password policy.' },
  { id: 'config',     name: 'AWS Config',            description: 'Config recorder: not enabled in region, delivery channel missing.' },
  { id: 'backup',     name: 'AWS Backup',            description: 'Backup plans: RDS/DynamoDB/EFS not covered, no vault lock policy.' },
  { id: 'redshift',   name: 'Redshift',              description: 'Clusters: publicly accessible, no encryption, audit logging disabled.' },
  { id: 'elasticache',name: 'ElastiCache',           description: 'Redis clusters: no AUTH token, no in-transit encryption, no encryption at rest.' },
  { id: 'opensearch', name: 'OpenSearch',            description: 'Domains: public endpoint access, no encryption at rest, no node-to-node encryption.' },
  { id: 'route53',    name: 'Route 53',              description: 'Hosted zones: zone transfer allowed, dangling DNS records pointing to deleted resources.' },
  { id: 'secretsmanager', name: 'Secrets Manager',  description: 'Secrets: rotation disabled, not accessed in 180+ days, no resource policy.' },
  { id: 'codebuild',  name: 'CodeBuild',             description: 'Projects: logging to CloudWatch disabled, privileged mode containers enabled.' },
  { id: 'cloudformation', name: 'CloudFormation',   description: 'Stacks: termination protection disabled, admin IAM roles used, drift detected.' },
  { id: 'stepfunctions',  name: 'Step Functions',   description: 'State machines: IAM PassRole, logging, X-Ray tracing for serverless workflows.' },
]

const GCP_SERVICES = [
  { id: 'compute',          name: 'Compute Engine',         description: 'VMs: public IPs, serial port access enabled, OS patch status, Shielded VM disabled.' },
  { id: 'storage',          name: 'Cloud Storage',          description: 'Buckets: allUsers/allAuthenticatedUsers IAM, no CMEK, versioning off, no uniform bucket-level access.' },
  { id: 'cloudsql',         name: 'Cloud SQL',              description: 'Instances: public IP enabled, no automated backup, no SSL enforcement, no CMEK.' },
  { id: 'functions',        name: 'Cloud Functions',        description: 'Functions: public invocation (allUsers invoker), hardcoded secrets in environment variables.' },
  { id: 'iam',              name: 'IAM & Admin',            description: 'Service accounts: user-managed keys, primitive roles (Owner/Editor), users without 2-Step Verification.' },
  { id: 'firewall',         name: 'VPC Firewall Rules',     description: 'Firewall rules: SSH (22) / RDP (3389) open from 0.0.0.0/0, all-traffic allow rules.' },
  { id: 'loadbalancing',    name: 'Cloud Load Balancing',   description: 'Backend services: no Cloud Armor security policy attached, logging disabled.' },
  { id: 'armor',            name: 'Cloud Armor',            description: 'Security policies: not associated with backend services or load balancers.' },
  { id: 'auditlogs',        name: 'Cloud Audit Logs',       description: 'Audit logging: Admin Activity / Data Access / System Event logs disabled for services.' },
  { id: 'vpc',              name: 'VPC Networks',           description: 'Networks: VPC flow logs disabled on subnets, default network in use, open firewall rules.' },
  { id: 'disks',            name: 'Persistent Disks',       description: 'Disks: no CMEK encryption, disk snapshots publicly shared.' },
  { id: 'gke',              name: 'GKE',                    description: 'Clusters: public API endpoint, legacy ABAC enabled, no Workload Identity, no Binary Authorization.' },
  { id: 'cloudrun',         name: 'Cloud Run',              description: 'Services: public unauthenticated access (allUsers invoker), no VPC connector.' },
  { id: 'kms',              name: 'Cloud KMS',              description: 'Keys: automatic rotation not configured, CMEK not used for storage services.' },
  { id: 'apigateway',       name: 'API Gateway',            description: 'APIs: no authentication configured, no Cloud Armor policy, no access logging.' },
  { id: 'pubsub',           name: 'Pub/Sub',                description: 'Topics and subscriptions: no CMEK, public topic resource policies (allUsers subscriber).' },
  { id: 'firestore',        name: 'Firestore / Datastore',  description: 'Databases: no CMEK, no backup policy configured, public access via app credentials.' },
  { id: 'scc',              name: 'Security Command Center',description: 'SCC: not enabled in Standard or Premium tier, no notification configs for findings.' },
  { id: 'monitoring',       name: 'Cloud Monitoring',       description: 'Alerting policies: no alerts for IAM changes, firewall rule edits, bucket ACL changes.' },
  { id: 'artifactregistry', name: 'Artifact Registry',      description: 'Repositories: images with critical CVEs, scan-on-push not enabled, public registry access.' },
  { id: 'bigquery',         name: 'BigQuery',               description: 'Datasets: public access (allUsers), no CMEK, no audit logging for data access.' },
  { id: 'dns',              name: 'Cloud DNS',              description: 'Managed zones: DNSSEC disabled, dangling DNS records pointing to deleted resources.' },
  { id: 'secretmanager',    name: 'Secret Manager',         description: 'Secrets: rotation disabled, accessed by service accounts with overly broad IAM bindings.' },
]

const AZURE_SERVICES = [
  { id: 'vm',               name: 'Virtual Machines',           description: 'VMs: public IP attached, no disk encryption, Defender for Endpoint not enabled, JIT access off.' },
  { id: 'storage',          name: 'Storage Accounts',           description: 'Accounts: public blob access, HTTP allowed (not HTTPS-only), no CMK, no soft delete.' },
  { id: 'sql',              name: 'Azure SQL',                  description: 'SQL Servers/Databases: public network access, no TDE with CMK, auditing disabled, no threat detection.' },
  { id: 'functions',        name: 'Azure Functions',            description: 'Functions: public access, no managed identity, app settings contain plaintext secrets.' },
  { id: 'iam',              name: 'Azure AD & RBAC',            description: 'Users: no MFA, Owner/Contributor at subscription scope, no PIM, legacy authentication allowed.' },
  { id: 'nsg',              name: 'Network Security Groups',    description: 'NSG rules: SSH (22) / RDP (3389) from Internet (0.0.0.0/0), any-source any-port rules.' },
  { id: 'appgateway',       name: 'Application Gateway',        description: 'Gateways: no WAF policy attached, diagnostic logging not enabled, HTTP listeners open.' },
  { id: 'waf',              name: 'Azure WAF',                  description: 'WAF policies: not associated with Application Gateway, Front Door, or CDN endpoints.' },
  { id: 'monitor',          name: 'Azure Monitor',              description: 'Activity Log: not exported, retained less than 1 year, no alert rules for critical operations.' },
  { id: 'vnet',             name: 'Virtual Networks',           description: 'VNets: no NSG on subnets, no Network Watcher flow logs, peering with unrestricted access.' },
  { id: 'disks',            name: 'Managed Disks',              description: 'Disks: not encrypted with CMK, network access set to allow-all, snapshots publicly accessible.' },
  { id: 'aks',              name: 'AKS',                        description: 'Clusters: public API endpoint, RBAC disabled, no Azure AD integration, no network policy.' },
  { id: 'containerinstances',name: 'Container Instances',       description: 'Container groups: privileged containers, public IP with open ports, plaintext env var secrets.' },
  { id: 'keyvault',         name: 'Key Vault',                  description: 'Vaults: keys/secrets without expiry, no soft delete / purge protection, public network access.' },
  { id: 'apim',             name: 'API Management',             description: 'APIM: no subscription key required on APIs, no WAF, diagnostic logging disabled.' },
  { id: 'servicebus',       name: 'Service Bus',                description: 'Namespaces: no CMK, public network access, SAS authentication only (no AAD).' },
  { id: 'cosmosdb',         name: 'Cosmos DB',                  description: 'Accounts: public endpoint, no CMK, no backup policy, local auth not disabled.' },
  { id: 'defender',         name: 'Defender for Cloud',         description: 'Defender plans: not enabled for Servers / Storage / SQL / Containers / App Service.' },
  { id: 'alerts',           name: 'Azure Alerts / Sentinel',    description: 'Alert rules: no alerts for role assignments, policy changes, NSG modifications, key deletions.' },
  { id: 'acr',              name: 'Container Registry',         description: 'Registries: admin account enabled, no vulnerability scanning, public network access.' },
  { id: 'appservice',       name: 'App Service',                description: 'Web apps: HTTP allowed, remote debugging on, managed identity not used, TLS 1.0/1.1 allowed.' },
  { id: 'loganalytics',     name: 'Log Analytics',              description: 'Workspaces: no diagnostic settings sending to workspace, short retention (< 90 days).' },
  { id: 'redis',            name: 'Azure Cache for Redis',      description: 'Caches: non-SSL port enabled, no AAD authentication, public network access.' },
]

// ── Multi-cloud parallel scan state ─────────────────────────────────────────
const multiMode    = ref(false)
const multiTargets = ref(new Set(['aws', 'gcp', 'azure']))
const multiJobs    = ref([])
const multiLoading = ref(false)
const multiError   = ref('')
const multiDone    = ref(false)
const connectedClouds = ref(new Set())

function toggleMultiTarget(id) {
  const s = new Set(multiTargets.value)
  s.has(id) ? s.delete(id) : s.add(id)
  multiTargets.value = s
}

async function startMulti() {
  multiLoading.value = true
  multiError.value = ''
  multiJobs.value = []
  multiDone.value = false

  const targets = [...multiTargets.value]
  const normalize = (ev) => ({
    step: ev.step || ev.message || 'Step',
    status: ev.status === 'success' ? 'success' : ev.status === 'failed' ? 'failed' : ev.status || 'running',
    detail: ev.detail || null,
  })

  // Start all jobs in parallel
  const jobMap = {}
  for (const cloud of targets) {
    const payload = { cloud, save_snapshot: saveSnapshot.value }
    if (cloud === 'aws')   payload.region = region.value.trim() || 'us-east-1'
    if (cloud === 'gcp')   payload.project_id = projectId.value.trim() || null
    if (cloud === 'azure') payload.subscription_id = subscriptionId.value.trim() || null
    try {
      const { job_id } = await api.startScan(payload)
      jobMap[cloud] = job_id
      multiJobs.value.push({ cloud, jobId: job_id, steps: [], done: false, error: '', summary: null, downloads: [] })
    } catch (e) {
      multiJobs.value.push({ cloud, jobId: null, steps: [{ step: 'Failed to start', status: 'failed', detail: e.message }], done: true, error: e.message, summary: null, downloads: [] })
    }
  }

  multiLoading.value = false

  // Poll all jobs until all done
  const pending = new Set(targets.filter(c => jobMap[c]))
  const pollInterval = setInterval(async () => {
    if (pending.size === 0) {
      clearInterval(pollInterval)
      multiDone.value = true
      return
    }
    for (const cloud of [...pending]) {
      const jid = jobMap[cloud]
      if (!jid) { pending.delete(cloud); continue }
      try {
        const data = await api.getJob(jid)
        const serverSteps = (data.steps || []).filter(ev => ev.type === 'step')
        const job = multiJobs.value.find(j => j.cloud === cloud)
        if (job) {
          if (serverSteps.length > 0) job.steps = serverSteps.map(normalize)
          if (data.status === 'completed' || data.status === 'failed') {
            job.done = true
            if (data.error) job.error = data.error
            if (data.result?.summary) { job.summary = data.result.summary; saveScanHistory(data.result.summary, data.status) }
            if (data.result?.downloads) job.downloads = data.result.downloads || []
            pending.delete(cloud)
          }
        }
      } catch (_) {}
    }
    if (pending.size === 0) {
      clearInterval(pollInterval)
      multiDone.value = true
    }
  }, 2000)
}

function resetMulti() {
  multiJobs.value = []
  multiDone.value = false
  multiError.value = ''
}

// ── Reactive state ──────────────────────────────────────────────────────────
const selectedCloud  = ref('aws')
const region         = ref('us-east-1')
const projectId      = ref('')
const subscriptionId = ref('')
const saveSnapshot   = ref(true)

const currentCloud = computed(() => CLOUDS.find(c => c.id === selectedCloud.value) || CLOUDS[0])

const serviceScripts = computed(() => {
  if (selectedCloud.value === 'gcp')   return GCP_SERVICES
  if (selectedCloud.value === 'azure') return AZURE_SERVICES
  return AWS_SERVICES
})

const selectedServices = ref(AWS_SERVICES.map(s => s.id))

// Reset service selection when cloud changes
watch(selectedCloud, (cloud) => {
  const list = cloud === 'gcp' ? GCP_SERVICES : cloud === 'azure' ? AZURE_SERVICES : AWS_SERVICES
  selectedServices.value = list.map(s => s.id)
  try { localStorage.setItem('cspm_cloud', cloud) } catch (_) {}
})

function switchCloud(id) { selectedCloud.value = id }

onMounted(() => {
  try {
    const saved = localStorage.getItem('cspm_cloud') || 'aws'
    selectedCloud.value = saved
    const list = saved === 'gcp' ? GCP_SERVICES : saved === 'azure' ? AZURE_SERVICES : AWS_SERVICES
    selectedServices.value = list.map(s => s.id)
    // Load connected clouds for multi-scan mode
    const conns = JSON.parse(localStorage.getItem('cspm_cloud_connections') || '{}')
    const connected = new Set(Object.entries(conns).filter(([, v]) => v).map(([k]) => k))
    connectedClouds.value = connected
    // Default multi targets to connected clouds only (or all if none configured)
    if (connected.size > 0) multiTargets.value = new Set([...connected])
  } catch (_) {}
})

// ── Scan execution ───────────────────────────────────────────────────────────
const loading    = ref(false)
const startError = ref('')
const jobId      = ref('')
const steps      = ref([])
const done       = ref(false)
const summary    = ref(null)
const downloads  = ref([])
const finalError = ref('')
let unsubscribe  = null

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
    const allIds = serviceScripts.value.map(s => s.id)
    const onlyStr = selectedServices.value.length < allIds.length
      ? selectedServices.value.join(',')
      : null

    const scanPayload = { cloud: selectedCloud.value, only: onlyStr, save_snapshot: saveSnapshot.value }
    if (selectedCloud.value === 'aws')   scanPayload.region = region.value.trim() || 'us-east-1'
    if (selectedCloud.value === 'gcp')   scanPayload.project_id = projectId.value.trim() || null
    if (selectedCloud.value === 'azure') scanPayload.subscription_id = subscriptionId.value.trim() || null

    const { job_id } = await api.startScan(scanPayload)
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
          if (data.result?.summary) { summary.value = data.result.summary; saveScanHistory(data.result.summary, data.status) }
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
        if (ev.summary) { summary.value = ev.summary; saveScanHistory(ev.summary, ev.error ? 'failed' : 'completed') }
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

function saveScanHistory(sum, status = 'completed') {
  try {
    const history = JSON.parse(localStorage.getItem('cspm_scan_history') || '[]')
    const entry = {
      timestamp: new Date().toISOString(),
      cloud: sum.cloud || selectedCloud.value,
      region: sum.region || region.value || projectId.value || subscriptionId.value,
      findings_count: sum.findings_count ?? 0,
      risk_score: sum.risk_score ?? null,
      critical: sum.critical ?? 0,
      high: sum.high ?? 0,
      medium: sum.medium ?? 0,
      low: sum.low ?? 0,
      status,
    }
    history.unshift(entry)
    localStorage.setItem('cspm_scan_history', JSON.stringify(history.slice(0, 100)))
  } catch (_) {}
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
/* Mode toggle */
.mode-toggle-row { display: flex; gap: 6px; margin-bottom: 20px; }
.mode-btn {
  display: inline-flex; align-items: center; gap: 7px; padding: 7px 16px;
  border-radius: 8px; border: 1px solid var(--border); background: var(--bg-el);
  color: var(--text-muted); font-size: 0.85rem; font-weight: 500; cursor: pointer; transition: all 0.15s;
}
.mode-btn:hover { color: var(--text); border-color: rgba(99,102,241,0.4); }
.mode-btn.active { background: rgba(99,102,241,0.12); border-color: rgba(99,102,241,0.4); color: #a5b4fc; font-weight: 700; }

/* Multi-cloud grid */
.multi-cloud-grid { display: flex; gap: 10px; flex-wrap: wrap; margin: 0 0 18px; }
.multi-cloud-card {
  display: flex; align-items: center; gap: 9px; padding: 10px 16px;
  border-radius: 10px; border: 1px solid var(--border); background: var(--bg-el);
  cursor: pointer; transition: all 0.15s; user-select: none; flex: 1; min-width: 160px;
}
.multi-cloud-card:hover { border-color: rgba(99,102,241,0.35); }
.mc-check {
  width: 16px; height: 16px; border-radius: 4px; border: 1px solid var(--border);
  background: var(--bg-el-hi); display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all 0.13s;
}
.mc-aws.mc-selected    { border-color: rgba(255,153,0,0.4);   background: rgba(255,153,0,0.07); }
.mc-gcp.mc-selected    { border-color: rgba(66,133,244,0.4);  background: rgba(66,133,244,0.07); }
.mc-azure.mc-selected  { border-color: rgba(0,120,212,0.4);   background: rgba(0,120,212,0.07); }
.mc-aws.mc-selected    .mc-check { border-color: #fb923c; background: rgba(255,153,0,0.2); color: #fb923c; }
.mc-gcp.mc-selected    .mc-check { border-color: #60a5fa; background: rgba(66,133,244,0.2); color: #60a5fa; }
.mc-azure.mc-selected  .mc-check { border-color: #93c5fd; background: rgba(0,120,212,0.2); color: #93c5fd; }
.mc-label { font-weight: 600; font-size: 0.88rem; color: var(--text); flex: 1; }
.mc-status-ok   { font-size: 0.72rem; color: #4ade80; background: rgba(34,197,94,0.1); padding: 2px 7px; border-radius: 10px; }
.mc-status-none { font-size: 0.72rem; color: #94a3b8; background: rgba(100,116,139,0.1); padding: 2px 7px; border-radius: 10px; }

/* Multi-cloud progress grid */
.multi-progress-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 18px; margin-top: 20px; }
.multi-progress-card { border: 1px solid var(--border); border-radius: 14px; overflow: hidden; }
.mpc-aws   { border-color: rgba(255,153,0,0.25); }
.mpc-gcp   { border-color: rgba(66,133,244,0.25); }
.mpc-azure { border-color: rgba(0,120,212,0.25); }
.mpc-header {
  display: flex; align-items: center; gap: 10px; padding: 12px 18px;
  border-bottom: 1px solid var(--border); font-size: 0.9rem;
}
.mpc-aws   .mpc-header { background: rgba(255,153,0,0.05); }
.mpc-gcp   .mpc-header { background: rgba(66,133,244,0.05); }
.mpc-azure .mpc-header { background: rgba(0,120,212,0.05); }
.mpc-status { margin-left: auto; font-size: 0.74rem; font-weight: 700; padding: 2px 9px; border-radius: 20px; }
.mpc-running { background: rgba(234,179,8,0.12);  color: #fbbf24; }
.mpc-ok      { background: rgba(34,197,94,0.12);  color: #4ade80; }
.mpc-fail    { background: rgba(239,68,68,0.12);  color: #f87171; }

.multi-done-bar {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;
  margin-top: 18px; padding: 14px 20px; border-radius: 10px;
  background: rgba(34,197,94,0.07); border: 1px solid rgba(34,197,94,0.2); color: #4ade80; font-weight: 600;
}

/* Cloud picker */
.cloud-picker { display: flex; gap: 8px; flex-wrap: wrap; }
.cloud-pick-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 16px; border-radius: 9px;
  border: 1px solid var(--border); background: var(--bg-el);
  color: var(--text-muted); font-size: 0.88rem; font-weight: 500;
  cursor: pointer; transition: all 0.15s;
}
.cloud-pick-btn:hover { background: rgba(255,255,255,0.06); color: var(--text); }
.cpb-aws.active    { background: rgba(255,153,0,0.15);   border-color: rgba(255,153,0,0.4);   color: #fb923c; font-weight: 700; }
.cpb-gcp.active    { background: rgba(66,133,244,0.15);  border-color: rgba(66,133,244,0.4);  color: #60a5fa; font-weight: 700; }
.cpb-azure.active  { background: rgba(0,120,212,0.15);   border-color: rgba(0,120,212,0.4);   color: #93c5fd; font-weight: 700; }

/* Cloud info banner */
.cloud-info-banner {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 14px; border-radius: 9px;
  font-size: 0.84rem; margin-top: 6px;
  color: var(--text-muted); line-height: 1.4;
}
.banner-aws   { background: rgba(255,153,0,0.07);   border: 1px solid rgba(255,153,0,0.2); }
.banner-gcp   { background: rgba(66,133,244,0.07);  border: 1px solid rgba(66,133,244,0.2); }
.banner-azure { background: rgba(0,120,212,0.07);   border: 1px solid rgba(0,120,212,0.2); }
.banner-icon  { display: flex; align-items: center; flex-shrink: 0; }
.banner-icon svg { opacity: 0.85; }
.cloud-info-banner strong { color: var(--text); }

.checkbox-label { display: flex; align-items: center; gap: 7px; cursor: pointer; font-size: 0.9rem; }

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
