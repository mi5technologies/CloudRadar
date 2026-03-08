<template>
  <div class="serverless-usage-view">
    <div class="view-header">
      <div>
        <h1>Serverless &amp; Usage</h1>
        <p class="muted">Serverless security checks (Lambda, Step Functions, API Gateway, SQS, DynamoDB) and usage-based findings (idle Lambdas, errors, throttles).</p>
      </div>
    </div>

    <div class="cloud-tabs">
      <button v-for="c in CLOUDS" :key="c.id"
        class="cloud-tab" :class="[`cloud-tab-${c.id}`, { active: selectedCloud === c.id }]"
        @click="selectCloud(c.id)">
        <span class="cloud-tab-icon" v-html="c.svg"></span>
        <span class="cloud-tab-label">{{ c.label }}</span>
      </button>
    </div>

    <div class="scan-tabs">
      <button class="scan-tab" :class="{ active: activeTab === 'serverless' }" @click="activeTab = 'serverless'">
        Serverless Security
      </button>
      <button class="scan-tab" :class="{ active: activeTab === 'usage' }" @click="activeTab = 'usage'">
        Usage Scan
      </button>
    </div>

    <!-- Configure checks: show checks for the active tab so user can select what to run -->
    <div class="card checks-card" v-if="!loadingServerless && !loadingUsage">
      <div class="checks-header" @click="checksOpen = !checksOpen">
        <div class="checks-header-left">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
          </svg>
          <span class="checks-title">Configure checks</span>
          <span class="checks-summary-badge">{{ enabledCount }} / {{ allChecksForTab.length }} enabled</span>
        </div>
        <div class="checks-header-right">
          <button class="checks-select-btn" @click.stop="selectAllChecks(true)">Select all</button>
          <button class="checks-select-btn" @click.stop="selectAllChecks(false)">Deselect all</button>
          <svg class="checks-arrow" :class="{ open: checksOpen }" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </div>
      <transition name="panel-slide">
        <div v-if="checksOpen" class="checks-body">
          <p class="checks-hint muted">Deselect any check you want to skip when running the {{ activeTab === 'serverless' ? 'serverless' : 'usage' }} scan. Your selection is remembered.</p>
          <!-- Serverless: by category -->
          <template v-if="activeTab === 'serverless'">
            <div v-for="cat in serverlessCategoriesForCloud" :key="cat.id" class="check-cat-block">
              <div class="check-cat-header">
                <label class="check-cat-toggle">
                  <input type="checkbox"
                    :checked="isCatAllSelected(cat.id)"
                    :indeterminate.prop="isCatIndeterminate(cat.id)"
                    @change="toggleCategory(cat.id, $event.target.checked)"
                  />
                  <span class="cat-dot" :style="{ background: cat.color }"></span>
                  <span class="check-cat-label">{{ cat.label }}</span>
                  <span class="check-cat-count muted">{{ checksForCategoryInCloud(cat.id).length }} check{{ checksForCategoryInCloud(cat.id).length !== 1 ? 's' : '' }}</span>
                </label>
              </div>
              <div class="check-grid">
                <label v-for="chk in checksForCategoryInCloud(cat.id)" :key="chk.rule_id" class="check-item"
                  :class="{ 'check-item-disabled': !enabledServerlessRules.has(chk.rule_id) }">
                  <input type="checkbox"
                    :checked="enabledServerlessRules.has(chk.rule_id)"
                    @change="toggleServerlessRule(chk.rule_id, $event.target.checked)"
                  />
                  <div class="check-item-body">
                    <div class="check-item-top">
                      <span class="check-item-name">{{ chk.title }}</span>
                      <span class="sev-badge" :class="'sev-' + chk.severity">{{ chk.severity }}</span>
                    </div>
                    <div class="check-item-desc muted">{{ chk.desc }}</div>
                  </div>
                </label>
              </div>
            </div>
          </template>
          <!-- Usage: flat list (AWS only) -->
          <template v-else>
            <p v-if="!usageChecksForCloud.length" class="checks-hint muted">Usage scan is currently available for AWS only (Lambda and CloudWatch metrics). Switch to AWS to run it.</p>
            <div v-else class="check-grid usage-checks">
              <label v-for="chk in usageChecksForCloud" :key="chk.rule_id" class="check-item"
                :class="{ 'check-item-disabled': !enabledUsageRules.has(chk.rule_id) }">
                <input type="checkbox"
                  :checked="enabledUsageRules.has(chk.rule_id)"
                  @change="toggleUsageRule(chk.rule_id, $event.target.checked)"
                />
                <div class="check-item-body">
                  <div class="check-item-top">
                    <span class="check-item-name">{{ chk.title }}</span>
                    <span class="sev-badge" :class="'sev-' + chk.severity">{{ chk.severity }}</span>
                  </div>
                  <div class="check-item-desc muted">{{ chk.desc }}</div>
                </div>
              </label>
            </div>
          </template>
        </div>
      </transition>
    </div>

    <!-- Serverless tab -->
    <div v-show="activeTab === 'serverless'" class="tab-panel">
      <div class="panel-actions">
        <button class="btn btn-primary" @click="runServerlessScan" :disabled="loadingServerless">
          <span v-if="!loadingServerless">Run serverless scan</span>
          <span v-else>Scanning…</span>
        </button>
        <button v-if="serverlessFindings.length" class="btn btn-secondary" @click="exportServerlessCSV">
          Export CSV
        </button>
      </div>
      <div v-if="errorServerless" class="card error-card">
        <p style="color: var(--error); margin:0">{{ errorServerless }}</p>
      </div>
      <div v-else-if="!hasServerlessData && !loadingServerless" class="card no-scan-card">
        <p>{{ serverlessEmptyMessage }}</p>
      </div>
      <template v-else-if="hasServerlessData">
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">Total findings</div>
            <div class="kpi-value">{{ serverlessSummary.total_findings }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">High</div>
            <div class="kpi-value">{{ serverlessSummary.high || 0 }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Medium</div>
            <div class="kpi-value">{{ serverlessSummary.medium || 0 }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Low</div>
            <div class="kpi-value">{{ serverlessSummary.low || 0 }}</div>
          </div>
        </div>
        <div class="card findings-card" v-if="serverlessFindings.length">
          <h2>Serverless findings</h2>
          <table class="findings-table">
            <thead>
              <tr>
                <th>Resource</th>
                <th>Severity</th>
                <th>Finding</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in serverlessFindings" :key="f.rule_id + f.resource_id"
                class="finding-row" :class="'sev-row-' + f.severity"
                @click="selectedServerless = selectedServerless === f ? null : f">
                <td>
                  <div class="res-name">{{ f.resource_name }}</div>
                  <div class="res-type">{{ f.resource_type }} · {{ f.region }}</div>
                </td>
                <td><span class="sev-badge" :class="'sev-' + f.severity">{{ f.severity }}</span></td>
                <td class="finding-title">{{ f.title }}</td>
              </tr>
            </tbody>
          </table>
          <transition name="slide-down">
            <div v-if="selectedServerless" class="finding-detail">
              <div class="detail-header">
                <span class="sev-badge" :class="'sev-' + selectedServerless.severity">{{ selectedServerless.severity }}</span>
                <strong>{{ selectedServerless.title }}</strong>
                <button class="close-btn" @click="selectedServerless = null">✕</button>
              </div>
              <div class="detail-body">
                <p class="detail-label">Detail</p>
                <p>{{ selectedServerless.detail }}</p>
                <p class="detail-label">Remediation</p>
                <p class="detail-remediation">{{ selectedServerless.remediation }}</p>
                <div class="detail-meta">
                  <span><strong>Rule:</strong> {{ selectedServerless.rule_id }}</span>
                  <span><strong>Resource:</strong> {{ selectedServerless.resource_id }}</span>
                  <span><strong>Region:</strong> {{ selectedServerless.region }}</span>
                </div>
              </div>
            </div>
          </transition>
        </div>
        <div v-else class="card success-card">
          <p>No serverless security findings.</p>
        </div>
      </template>
    </div>

    <!-- Usage tab -->
    <div v-show="activeTab === 'usage'" class="tab-panel">
      <div class="panel-actions">
        <button class="btn btn-primary" @click="runUsageScan" :disabled="loadingUsage || !usageScanAvailable"
          :title="usageScanAvailable ? '' : 'Usage scan is available for AWS only'">
          <span v-if="!loadingUsage">Run usage scan</span>
          <span v-else>Scanning…</span>
        </button>
        <button v-if="usageFindings.length" class="btn btn-secondary" @click="exportUsageCSV">
          Export CSV
        </button>
        <label class="days-label">
          <span class="muted">Days of metrics:</span>
          <select v-model.number="daysLookback" class="days-select">
            <option :value="7">7</option>
            <option :value="14">14</option>
            <option :value="30">30</option>
          </select>
        </label>
      </div>
      <div v-if="errorUsage" class="card error-card">
        <p style="color: var(--error); margin:0">{{ errorUsage }}</p>
      </div>
      <div v-else-if="!hasUsageData && !loadingUsage" class="card no-scan-card">
        <p>{{ usageEmptyMessage }}</p>
      </div>
      <template v-else-if="hasUsageData">
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">Total findings</div>
            <div class="kpi-value">{{ usageSummary.total_findings }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Medium</div>
            <div class="kpi-value">{{ usageSummary.medium || 0 }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Low</div>
            <div class="kpi-value">{{ usageSummary.low || 0 }}</div>
          </div>
        </div>
        <div class="card findings-card" v-if="usageFindings.length">
          <h2>Usage findings (last {{ usageSummary.days_lookback || 14 }} days)</h2>
          <table class="findings-table">
            <thead>
              <tr>
                <th>Resource</th>
                <th>Severity</th>
                <th>Finding</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in usageFindings" :key="f.rule_id + f.resource_id"
                class="finding-row" :class="'sev-row-' + f.severity"
                @click="selectedUsage = selectedUsage === f ? null : f">
                <td>
                  <div class="res-name">{{ f.resource_name }}</div>
                  <div class="res-type">{{ f.resource_type }} · {{ f.region }}</div>
                </td>
                <td><span class="sev-badge" :class="'sev-' + f.severity">{{ f.severity }}</span></td>
                <td class="finding-title">{{ f.title }}</td>
              </tr>
            </tbody>
          </table>
          <transition name="slide-down">
            <div v-if="selectedUsage" class="finding-detail">
              <div class="detail-header">
                <span class="sev-badge" :class="'sev-' + selectedUsage.severity">{{ selectedUsage.severity }}</span>
                <strong>{{ selectedUsage.title }}</strong>
                <button class="close-btn" @click="selectedUsage = null">✕</button>
              </div>
              <div class="detail-body">
                <p class="detail-label">Detail</p>
                <p>{{ selectedUsage.detail }}</p>
                <p class="detail-label">Remediation</p>
                <p class="detail-remediation">{{ selectedUsage.remediation }}</p>
                <div class="detail-meta">
                  <span><strong>Rule:</strong> {{ selectedUsage.rule_id }}</span>
                  <span><strong>Resource:</strong> {{ selectedUsage.resource_id }}</span>
                  <span><strong>Region:</strong> {{ selectedUsage.region }}</span>
                </div>
              </div>
            </div>
          </transition>
        </div>
        <div v-else class="card success-card">
          <p>No usage findings (no idle Lambdas, high errors, or throttles in the period).</p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const CLOUDS = [
  { id: 'aws', label: 'AWS',
    svg: `<svg width="22" height="14" viewBox="0 0 80 48" fill="none"><path d="M22.9 32.2c-4.5 2.4-9.4 3.7-14.5 3.7C3.8 35.9 0 32.1 0 27.3c0-5.3 4.5-9.6 10.7-10.2-.3-1.1-.5-2.3-.5-3.6C10.2 6.1 15.9 1 22.9 1c3.4 0 6.5 1.2 8.9 3.2 2.2-4.3 6.7-7.2 11.7-7.2 4.3 0 8.2 1.9 10.8 5 1.9-.7 3.9-1.1 6-1.1C68 1 75 8 75 16.8c0 1.8-.3 3.5-.8 5.1C77.4 23.5 80 27 80 31.1 80 36.8 75.3 41 69.2 41H22.9z" fill="#FF9900"/></svg>` },
  { id: 'gcp', label: 'Google Cloud',
    svg: `<svg width="22" height="22" viewBox="0 0 48 48"><path fill="#4285F4" d="M30.2 17.8H24v4.2h6.9c-.7 3.7-4 6.5-7.9 6.5-4.5 0-8.2-3.7-8.2-8.2s3.7-8.2 8.2-8.2c2.1 0 4 .8 5.5 2.1l3-3C29 8.6 26.7 7.5 24 7.5c-7.5 0-13.5 6-13.5 13.5S16.5 34.5 24 34.5c7.2 0 12.8-5 12.8-13.5 0-.8-.1-1.5-.2-2.2l-6.4-1z"/></svg>` },
  { id: 'azure', label: 'Azure',
    svg: `<svg width="22" height="22" viewBox="0 0 48 48"><path fill="#0078D4" d="M27 4L13 28l9 5-7 7h16l7-36z"/><path fill="#50E6FF" d="M27 4L4 34l9-1 7-7-3-5z"/></svg>` },
]

const SERVERLESS_CATEGORIES = [
  { id: 'lambda', label: 'Lambda', color: '#FF9900' },
  { id: 'stepfunctions', label: 'Step Functions', color: '#DD344C' },
  { id: 'api_gateway', label: 'API Gateway', color: '#FF4F8B' },
  { id: 'sqs', label: 'SQS', color: '#FF4F8B' },
  { id: 'dynamodb', label: 'DynamoDB', color: '#4053D6' },
  { id: 'cloud_run', label: 'Cloud Run', color: '#4285F4' },
  { id: 'gcp_cloud_functions', label: 'GCP Cloud Functions', color: '#4285F4' },
  { id: 'azure_functions', label: 'Azure Functions', color: '#0078D4' },
]

const CATEGORIES_BY_CLOUD = {
  aws: ['lambda', 'stepfunctions', 'api_gateway', 'sqs', 'dynamodb'],
  gcp: ['cloud_run', 'gcp_cloud_functions'],
  azure: ['azure_functions'],
}

const SERVERLESS_CHECKS = [
  { rule_id: 'serverless.lambda_no_dlq', category: 'lambda', severity: 'medium', title: 'Lambda has no failure destination (DLQ or OnFailure)', desc: 'Failed async invocations may be lost. Configure DeadLetterConfig or Event Invoke OnFailure.' },
  { rule_id: 'serverless.lambda_timeout_high', category: 'lambda', severity: 'low', title: 'Lambda timeout exceeds 5 minutes', desc: 'Long timeouts can mask hanging code and increase cost.' },
  { rule_id: 'serverless.lambda_env_secrets', category: 'lambda', severity: 'high', title: 'Lambda environment may contain secrets', desc: 'Use Secrets Manager or Parameter Store instead of env vars.' },
  { rule_id: 'serverless.lambda_reserved_concurrency_zero', category: 'lambda', severity: 'medium', title: 'Lambda reserved concurrency is 0', desc: 'All invocations are throttled; often unintentional.' },
  { rule_id: 'serverless.lambda_vpc_review', category: 'lambda', severity: 'low', title: 'Lambda in VPC: verify NAT/egress and failure handling', desc: 'VPC Lambdas need NAT or VPC endpoints; ensure DLQ for async.' },
  { rule_id: 'serverless.lambda_layers_review', category: 'lambda', severity: 'low', title: 'Lambda uses layers: review for updates and vulnerabilities', desc: 'Keep layers updated and audit for known vulnerabilities.' },
  { rule_id: 'serverless.lambda_extensions_review', category: 'lambda', severity: 'low', title: 'Review Lambda extensions for security and observability', desc: 'Consider extension layers for logging, metrics, and security.' },
  { rule_id: 'serverless.stepfunctions_no_logging', category: 'stepfunctions', severity: 'medium', title: 'Step Functions state machine has logging disabled', desc: 'Enable logging for execution history and debugging.' },
  { rule_id: 'serverless.stepfunctions_no_xray', category: 'stepfunctions', severity: 'low', title: 'Step Functions X-Ray tracing is disabled', desc: 'X-Ray helps diagnose failures and latency.' },
  { rule_id: 'serverless.apigw_no_usage_plan', category: 'api_gateway', severity: 'low', title: 'API Gateway has no usage plan (throttling/quota)', desc: 'Create a usage plan for rate limiting.' },
  { rule_id: 'serverless.apigw_logging_review', category: 'api_gateway', severity: 'low', title: 'API Gateway access logging not enabled', desc: 'Enable access logging for audit and debugging.' },
  { rule_id: 'serverless.sqs_no_dlq', category: 'sqs', severity: 'low', title: 'SQS queue has no dead-letter queue', desc: 'Use RedrivePolicy with deadLetterTargetArn and maxReceiveCount.' },
  { rule_id: 'serverless.sqs_visibility_short', category: 'sqs', severity: 'low', title: 'SQS visibility timeout may be too short for Lambda', desc: 'Set to at least 6× Lambda timeout to avoid duplicate processing.' },
  { rule_id: 'serverless.dynamodb_streams_review', category: 'dynamodb', severity: 'low', title: 'DynamoDB table has no streams (if used by Lambda)', desc: 'Enable streams if you need event-driven processing.' },
  { rule_id: 'serverless.cloudrun_public_invoker', category: 'cloud_run', severity: 'medium', title: 'Cloud Run allows public (allUsers) invoker', desc: 'Restrict invoker IAM to required identities.' },
  { rule_id: 'serverless.cloudrun_min_instances_review', category: 'cloud_run', severity: 'low', title: 'Cloud Run min instances > 0 (always-on cost)', desc: 'Consider 0 for dev or low-traffic to reduce cost.' },
  { rule_id: 'serverless.gcp_functions_public_invoker', category: 'gcp_cloud_functions', severity: 'medium', title: 'Cloud Function allows public (allUsers) invoker', desc: 'Remove allUsers from Cloud Functions Invoker role.' },
  { rule_id: 'serverless.gcp_functions_env_secrets_review', category: 'gcp_cloud_functions', severity: 'low', title: 'Cloud Function env vars; prefer Secret Manager', desc: 'Use secret_environment_variables / Secret Manager for secrets.' },
  { rule_id: 'serverless.azure_functions_public_access_review', category: 'azure_functions', severity: 'low', title: 'Azure Function App has public network access enabled', desc: 'Consider private endpoints for sensitive workloads.' },
  { rule_id: 'serverless.azure_functions_managed_identity_review', category: 'azure_functions', severity: 'low', title: 'Azure Function: consider using managed identity', desc: 'Managed identity avoids storing credentials in app settings.' },
  { rule_id: 'serverless.azure_functions_app_settings_secrets', category: 'azure_functions', severity: 'medium', title: 'Function App may store secrets in app settings', desc: 'Prefer Key Vault references in app settings.' },
]

const USAGE_CHECKS = [
  { rule_id: 'usage.lambda_idle', severity: 'low', title: 'Lambda has no invocations in the period', desc: 'Function appears unused; consider removing or verifying triggers.' },
  { rule_id: 'usage.lambda_errors_high', severity: 'medium', title: 'Lambda error rate is high (≥5%)', desc: 'Check CloudWatch Logs and fix code or add DLQ for async.' },
  { rule_id: 'usage.lambda_throttles', severity: 'low', title: 'Lambda has throttled invocations', desc: 'Increase reserved concurrency or optimize duration/memory.' },
]

const selectedCloud = ref('aws')
const activeTab = ref('serverless')
const loadingServerless = ref(false)
const loadingUsage = ref(false)
const errorServerless = ref('')
const errorUsage = ref('')
const serverlessFindings = ref([])
const serverlessSummary = ref({})
const usageFindings = ref([])
const usageSummary = ref({})
const selectedServerless = ref(null)
const selectedUsage = ref(null)
const daysLookback = ref(14)
const checksOpen = ref(true)

const enabledServerlessRules = ref(new Set(SERVERLESS_CHECKS.map(c => c.rule_id)))
const enabledUsageRules = ref(new Set(USAGE_CHECKS.map(c => c.rule_id)))

const serverlessCategoriesForCloud = computed(() => {
  const ids = CATEGORIES_BY_CLOUD[selectedCloud.value]
  if (!ids) return []
  return SERVERLESS_CATEGORIES.filter(cat => ids.includes(cat.id))
})

const serverlessChecksForCloud = computed(() => {
  const ids = CATEGORIES_BY_CLOUD[selectedCloud.value]
  if (!ids) return []
  return SERVERLESS_CHECKS.filter(c => ids.includes(c.category))
})

const usageChecksForCloud = computed(() => {
  return selectedCloud.value === 'aws' ? USAGE_CHECKS : []
})

const allChecksForTab = computed(() => activeTab.value === 'serverless' ? serverlessChecksForCloud.value : usageChecksForCloud.value)
const enabledCount = computed(() => {
  if (activeTab.value === 'serverless') {
    return serverlessChecksForCloud.value.filter(c => enabledServerlessRules.value.has(c.rule_id)).length
  }
  return usageChecksForCloud.value.filter(c => enabledUsageRules.value.has(c.rule_id)).length
})

const hasServerlessData = computed(() => serverlessSummary.value.total_findings !== undefined)
const hasUsageData = computed(() => usageSummary.value.total_findings !== undefined)

const serverlessEmptyMessage = computed(() => {
  const cloud = selectedCloud.value
  if (cloud === 'gcp') return 'Run the serverless scan to check Cloud Run and GCP Cloud Functions for public invoker, min instances, env/secrets, and more.'
  if (cloud === 'azure') return 'Run the serverless scan to check Azure Function Apps for public access, managed identity, and app settings secrets.'
  return 'Run the serverless scan to check Lambda, Step Functions, API Gateway, SQS, and DynamoDB for DLQ, logging, usage plans, and more.'
})

const usageEmptyMessage = computed(() => {
  if (selectedCloud.value === 'aws') {
    return 'Run the usage scan to detect idle Lambdas, high error rates, and throttles from CloudWatch metrics.'
  }
  return 'Usage scan is currently available for AWS only (Lambda and CloudWatch metrics). Switch to AWS to run it.'
})

const usageScanAvailable = computed(() => selectedCloud.value === 'aws')

function loadServerlessEnabled() {
  try {
    const raw = localStorage.getItem('cspm_serverless_checks_enabled')
    const allIds = new Set(SERVERLESS_CHECKS.map(c => c.rule_id))
    if (raw) {
      const arr = JSON.parse(raw)
      const saved = new Set(arr)
      const merged = new Set(saved)
      allIds.forEach(id => { if (!saved.has(id)) merged.add(id) })
      enabledServerlessRules.value = merged
    } else {
      enabledServerlessRules.value = allIds
    }
  } catch (_) {
    enabledServerlessRules.value = new Set(SERVERLESS_CHECKS.map(c => c.rule_id))
  }
}

function saveServerlessEnabled() {
  try {
    localStorage.setItem('cspm_serverless_checks_enabled', JSON.stringify([...enabledServerlessRules.value]))
  } catch (_) {}
}

function loadUsageEnabled() {
  try {
    const raw = localStorage.getItem('cspm_usage_checks_enabled')
    if (raw) {
      const arr = JSON.parse(raw)
      enabledUsageRules.value = new Set(arr)
    }
  } catch (_) {}
}

function saveUsageEnabled() {
  try {
    localStorage.setItem('cspm_usage_checks_enabled', JSON.stringify([...enabledUsageRules.value]))
  } catch (_) {}
}

function checksForCategory(catId) {
  return SERVERLESS_CHECKS.filter(c => c.category === catId)
}

function checksForCategoryInCloud(catId) {
  const ids = CATEGORIES_BY_CLOUD[selectedCloud.value]
  if (!ids || !ids.includes(catId)) return []
  return SERVERLESS_CHECKS.filter(c => c.category === catId)
}

function isCatAllSelected(catId) {
  const rules = checksForCategoryInCloud(catId).map(c => c.rule_id)
  return rules.length > 0 && rules.every(r => enabledServerlessRules.value.has(r))
}

function isCatIndeterminate(catId) {
  const rules = checksForCategoryInCloud(catId).map(c => c.rule_id)
  const n = rules.filter(r => enabledServerlessRules.value.has(r)).length
  return n > 0 && n < rules.length
}

function toggleCategory(catId, checked) {
  const rules = checksForCategoryInCloud(catId).map(c => c.rule_id)
  const set = new Set(enabledServerlessRules.value)
  rules.forEach(r => { if (checked) set.add(r); else set.delete(r) })
  enabledServerlessRules.value = set
  saveServerlessEnabled()
}

function toggleServerlessRule(ruleId, checked) {
  const set = new Set(enabledServerlessRules.value)
  if (checked) set.add(ruleId); else set.delete(ruleId)
  enabledServerlessRules.value = set
  saveServerlessEnabled()
}

function toggleUsageRule(ruleId, checked) {
  const set = new Set(enabledUsageRules.value)
  if (checked) set.add(ruleId); else set.delete(ruleId)
  enabledUsageRules.value = set
  saveUsageEnabled()
}

function selectAllChecks(checked) {
  if (activeTab.value === 'serverless') {
    const set = new Set(enabledServerlessRules.value)
    const checks = serverlessChecksForCloud.value
    if (checked) checks.forEach(c => set.add(c.rule_id))
    else checks.forEach(c => set.delete(c.rule_id))
    enabledServerlessRules.value = set
    saveServerlessEnabled()
  } else {
    const checks = usageChecksForCloud.value
    const set = new Set(checked ? checks.map(c => c.rule_id) : [])
    enabledUsageRules.value = set
    saveUsageEnabled()
  }
}

function selectCloud(id) {
  selectedCloud.value = id
}

onMounted(() => {
  loadServerlessEnabled()
  loadUsageEnabled()
})

async function runServerlessScan() {
  loadingServerless.value = true
  errorServerless.value = ''
  try {
    const base = import.meta.env.VITE_API_BASE || ''
    const skipRules = SERVERLESS_CHECKS.filter(c => !enabledServerlessRules.value.has(c.rule_id)).map(c => c.rule_id)
    const res = await fetch(base + '/api/serverless-scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cloud: selectedCloud.value,
        region: undefined,
        skip_rules: skipRules,
      }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Serverless scan failed')
    serverlessFindings.value = data.findings || []
    serverlessSummary.value = data.summary || {}
  } catch (e) {
    errorServerless.value = e.message || 'Serverless scan failed'
  } finally {
    loadingServerless.value = false
  }
}

async function runUsageScan() {
  loadingUsage.value = true
  errorUsage.value = ''
  try {
    const base = import.meta.env.VITE_API_BASE || ''
    const skipRules = USAGE_CHECKS.filter(c => !enabledUsageRules.value.has(c.rule_id)).map(c => c.rule_id)
    const res = await fetch(base + '/api/usage-scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cloud: selectedCloud.value,
        region: undefined,
        days_lookback: daysLookback.value,
        skip_rules: skipRules,
      }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Usage scan failed')
    usageFindings.value = data.findings || []
    usageSummary.value = data.summary || {}
  } catch (e) {
    errorUsage.value = e.message || 'Usage scan failed'
  } finally {
    loadingUsage.value = false
  }
}

function exportServerlessCSV() {
  exportCSV(serverlessFindings.value, 'serverless')
}

function exportUsageCSV() {
  exportCSV(usageFindings.value, 'usage')
}

function exportCSV(findings, prefix) {
  const headers = ['rule_id', 'resource_type', 'resource_id', 'resource_name', 'title', 'severity', 'detail', 'remediation', 'region']
  const rows = findings.map(f => headers.map(h => `"${String(f[h] || '').replace(/"/g, '""')}"`).join(','))
  const csv = [headers.join(','), ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${prefix}-scan-${selectedCloud.value}-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}
</script>

<style scoped>
.serverless-usage-view { padding: 24px 28px; max-width: 1200px; margin: 0 auto; }
.view-header { margin-bottom: 24px; }
.view-header h1 { margin: 0 0 6px; font-size: 1.5rem; font-weight: 700; }
.cloud-tabs { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.cloud-tab {
  display: inline-flex; align-items: center; gap: 8px; padding: 10px 18px; border-radius: 10px;
  background: var(--bg-el); border: 1px solid var(--border); color: var(--text-muted);
  font-size: 0.9rem; font-weight: 500; cursor: pointer; transition: all 0.15s;
}
.cloud-tab:hover { background: rgba(255,255,255,0.06); color: var(--text); }
.cloud-tab.active { color: var(--text); font-weight: 600; }
.scan-tabs { display: flex; gap: 8px; margin-bottom: 24px; }
.scan-tab {
  padding: 10px 20px; border-radius: 10px; background: var(--bg-el); border: 1px solid var(--border);
  color: var(--text-muted); font-weight: 500; cursor: pointer; transition: all 0.15s;
}
.scan-tab:hover { color: var(--text); }
.scan-tab.active { background: rgba(14,165,233,0.12); color: var(--accent); border-color: var(--accent); }
.checks-card { margin-bottom: 22px; padding: 0; overflow: hidden; }
.checks-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; cursor: pointer; user-select: none; transition: background 0.12s; }
.checks-header:hover { background: var(--bg-el-lo); }
.checks-header-left { display: flex; align-items: center; gap: 10px; }
.checks-header-right { display: flex; align-items: center; gap: 8px; }
.checks-title { font-size: 0.92rem; font-weight: 600; color: var(--text); }
.checks-summary-badge { padding: 2px 9px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; background: rgba(14,165,233,0.12); color: var(--accent); }
.checks-select-btn { padding: 4px 10px; border-radius: 7px; font-size: 0.75rem; font-weight: 600; background: var(--bg-el); border: 1px solid var(--border); color: var(--text-muted); cursor: pointer; transition: all 0.12s; }
.checks-select-btn:hover { background: var(--bg-el-hi); color: var(--text); }
.checks-arrow { transition: transform 0.2s; flex-shrink: 0; color: var(--text-muted); }
.checks-arrow.open { transform: rotate(180deg); }
.checks-body { padding: 0 18px 18px; border-top: 1px solid var(--border); }
.checks-hint { font-size: 0.82rem; margin: 12px 0 16px; }
.check-cat-block { margin-bottom: 18px; }
.check-cat-header { margin-bottom: 8px; }
.check-cat-toggle { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 600; color: var(--text); }
.check-cat-toggle input[type="checkbox"] { cursor: pointer; width: 15px; height: 15px; flex-shrink: 0; }
.cat-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.check-cat-label { font-weight: 700; }
.check-cat-count { font-weight: 400; font-size: 0.78rem; }
.check-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 8px; padding-left: 24px; }
.check-grid.usage-checks { padding-left: 0; }
.check-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px; border-radius: 9px; border: 1px solid var(--border); background: var(--bg-el-xlo); cursor: pointer; transition: all 0.12s; }
.check-item:hover { background: var(--bg-el); border-color: rgba(14,165,233,0.2); }
.check-item-disabled { opacity: 0.45; }
.check-item input[type="checkbox"] { flex-shrink: 0; margin-top: 3px; cursor: pointer; width: 14px; height: 14px; }
.check-item-body { flex: 1; min-width: 0; }
.check-item-top { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 3px; }
.check-item-name { font-size: 0.83rem; font-weight: 600; color: var(--text); }
.check-item-desc { font-size: 0.76rem; color: var(--text-muted); line-height: 1.4; }
.panel-slide-enter-active, .panel-slide-leave-active { transition: all 0.2s ease; overflow: hidden; }
.panel-slide-enter-from, .panel-slide-leave-to { opacity: 0; max-height: 0; }
.panel-slide-enter-to, .panel-slide-leave-from { max-height: 1200px; }
.tab-panel { min-height: 200px; }
.panel-actions { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.days-label { display: flex; align-items: center; gap: 8px; font-size: 0.9rem; }
.days-select { padding: 6px 10px; border-radius: 8px; background: var(--bg-el); border: 1px solid var(--border); color: var(--text); }
.error-card, .no-scan-card { padding: 24px; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-bottom: 24px; }
.kpi-card { padding: 16px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; }
.kpi-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); font-weight: 700; }
.kpi-value { font-size: 1.4rem; font-weight: 700; color: var(--text); }
.findings-card { padding: 20px; }
.findings-card h2 { margin: 0 0 16px; font-size: 1.1rem; }
.findings-table { width: 100%; border-collapse: collapse; }
.findings-table th { padding: 9px 12px; text-align: left; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); background: var(--bg-el-lo); }
.findings-table td { padding: 12px; border-bottom: 1px solid var(--border); font-size: 0.88rem; }
.finding-row { cursor: pointer; transition: background 0.12s; }
.finding-row:hover { background: rgba(255,255,255,0.03); }
.res-name { font-weight: 600; color: var(--text); }
.res-type { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }
.finding-title { color: var(--text-muted); }
.sev-badge { font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; text-transform: uppercase; }
.sev-badge.sev-high { background: rgba(249,115,22,0.15); color: #fb923c; }
.sev-badge.sev-medium { background: rgba(234,179,8,0.15); color: #fbbf24; }
.sev-badge.sev-low { background: rgba(59,130,246,0.15); color: #60a5fa; }
.finding-detail { margin-top: 16px; padding: 16px; background: var(--bg-el); border: 1px solid var(--border); border-radius: 10px; }
.detail-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.close-btn { margin-left: auto; background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 1rem; padding: 2px 6px; }
.detail-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); margin: 12px 0 4px; }
.detail-remediation { white-space: pre-wrap; }
.detail-meta { display: flex; gap: 18px; flex-wrap: wrap; font-size: 0.78rem; color: var(--text-muted); margin-top: 12px; }
.success-card { padding: 24px; }
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
