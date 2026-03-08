<template>
  <div class="setup-page">
    <div class="setup-inner">
      <div class="setup-header">
        <h1>Cloud Credentials Setup</h1>
        <p class="muted">Configure one or more cloud providers. Each panel saves independently — configure only the clouds you use.</p>
      </div>

      <!-- Overall connection status bar -->
      <div class="status-bar">
        <div
          v-for="c in CLOUDS" :key="c.id"
          class="status-pill"
          :class="connectionStatus[c.id] === 'connected' ? 'pill-ok' : connectionStatus[c.id] === 'saving' ? 'pill-saving' : 'pill-none'"
        >
          <span v-html="c.icon"></span>
          <span>{{ c.label }}</span>
          <span class="pill-dot" :class="connectionStatus[c.id]"></span>
          <span class="pill-label">{{ connectionStatus[c.id] === 'connected' ? 'Connected' : connectionStatus[c.id] === 'saving' ? 'Saving…' : 'Not set' }}</span>
        </div>
      </div>

      <!-- ── AWS ── -->
      <div class="cloud-card" :class="{ 'card-connected': connectionStatus.aws === 'connected' }">
        <div class="cloud-card-header" @click="togglePanel('aws')">
          <div class="cloud-card-title">
            <span class="cloud-icon aws-icon" v-html="CLOUDS[0].icon"></span>
            <span>Amazon Web Services (AWS)</span>
            <span v-if="connectionStatus.aws === 'connected'" class="conn-badge badge-ok">✓ Connected</span>
            <span v-else class="conn-badge badge-none">Not configured</span>
          </div>
          <svg class="panel-arrow" :class="{ open: openPanels.has('aws') }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
        <div v-if="openPanels.has('aws')" class="cloud-card-body">
          <form @submit.prevent="submitAws">
            <div class="fields-grid">
              <div class="input-group">
                <label>Region</label>
                <input v-model="awsForm.region" placeholder="us-east-1" />
              </div>
              <div class="input-group">
                <label>Access Key ID</label>
                <input v-model="awsForm.access_key_id" type="text" placeholder="AKIA…" autocomplete="off" />
              </div>
              <div class="input-group">
                <label>Secret Access Key</label>
                <input v-model="awsForm.secret_access_key" type="password" placeholder="••••••••" autocomplete="new-password" />
              </div>
              <div class="input-group multi-account-section">
                <label>Role assumption template <span class="opt-label">(multi-account)</span></label>
                <input v-model="awsForm.role_assumption_template" type="text" placeholder="arn:aws:iam::{account_id}:role/CloudRadarScanner" />
                <p class="field-hint">Use <code>{account_id}</code> placeholder. Scans all org accounts via assume-role.</p>
              </div>
              <div class="input-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="awsForm.persist" /> Save to server config
                </label>
              </div>
            </div>
            <div class="card-actions">
              <button type="submit" class="btn btn-primary" :disabled="connectionStatus.aws === 'saving'">
                {{ connectionStatus.aws === 'saving' ? 'Saving…' : 'Save AWS credentials' }}
              </button>
              <p v-if="messages.aws" class="inline-msg" :class="{ 'msg-err': errors.aws }">{{ messages.aws }}</p>
            </div>
          </form>
          <div class="creds-hint">
            <strong>Minimum IAM permissions:</strong> <code>SecurityAudit</code> + <code>ReadOnlyAccess</code> managed policies.
            For GuardDuty checks also attach <code>AmazonGuardDutyReadOnlyAccess</code>.
          </div>
        </div>
      </div>

      <!-- ── GCP ── -->
      <div class="cloud-card" :class="{ 'card-connected': connectionStatus.gcp === 'connected' }">
        <div class="cloud-card-header" @click="togglePanel('gcp')">
          <div class="cloud-card-title">
            <span class="cloud-icon gcp-icon" v-html="CLOUDS[1].icon"></span>
            <span>Google Cloud Platform (GCP)</span>
            <span v-if="connectionStatus.gcp === 'connected'" class="conn-badge badge-ok">✓ Connected</span>
            <span v-else class="conn-badge badge-none">Not configured</span>
          </div>
          <svg class="panel-arrow" :class="{ open: openPanels.has('gcp') }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
        <div v-if="openPanels.has('gcp')" class="cloud-card-body">
          <form @submit.prevent="submitGcp">
            <div class="fields-grid">
              <div class="input-group">
                <label>Project ID</label>
                <input v-model="gcpForm.project_id" type="text" placeholder="my-gcp-project-id" />
              </div>
              <div class="input-group">
                <label>Service account JSON path <span class="opt-label">(optional)</span></label>
                <input v-model="gcpForm.credentials_path" type="text" placeholder="/path/to/service-account.json" />
                <p class="field-hint">Leave blank to use Application Default Credentials (<code>gcloud auth application-default login</code>).</p>
              </div>
              <div class="input-group">
                <label>Organization ID <span class="opt-label">(multi-project)</span></label>
                <input v-model="gcpForm.organization_id" type="text" placeholder="123456789012" />
              </div>
              <div class="input-group">
                <label>Folder ID <span class="opt-label">(multi-project, alt to org)</span></label>
                <input v-model="gcpForm.folder_id" type="text" placeholder="123456789012" />
              </div>
              <div class="input-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="gcpForm.persist" /> Save to server config
                </label>
              </div>
            </div>
            <div class="card-actions">
              <button type="submit" class="btn btn-primary" :disabled="connectionStatus.gcp === 'saving'">
                {{ connectionStatus.gcp === 'saving' ? 'Saving…' : 'Save GCP credentials' }}
              </button>
              <p v-if="messages.gcp" class="inline-msg" :class="{ 'msg-err': errors.gcp }">{{ messages.gcp }}</p>
            </div>
          </form>
          <div class="creds-hint">
            <strong>Minimum IAM roles:</strong> <code>Viewer</code> + <code>Security Reviewer</code> + <code>Cloud Asset Viewer</code> on the project.
          </div>
        </div>
      </div>

      <!-- ── Azure ── -->
      <div class="cloud-card" :class="{ 'card-connected': connectionStatus.azure === 'connected' }">
        <div class="cloud-card-header" @click="togglePanel('azure')">
          <div class="cloud-card-title">
            <span class="cloud-icon azure-icon" v-html="CLOUDS[2].icon"></span>
            <span>Microsoft Azure</span>
            <span v-if="connectionStatus.azure === 'connected'" class="conn-badge badge-ok">✓ Connected</span>
            <span v-else class="conn-badge badge-none">Not configured</span>
          </div>
          <svg class="panel-arrow" :class="{ open: openPanels.has('azure') }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
        <div v-if="openPanels.has('azure')" class="cloud-card-body">
          <form @submit.prevent="submitAzure">
            <div class="fields-grid">
              <div class="input-group">
                <label>Subscription ID</label>
                <input v-model="azureForm.subscription_id" type="text" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
              </div>
              <div class="input-group">
                <label>Tenant ID</label>
                <input v-model="azureForm.tenant_id" type="text" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
              </div>
              <div class="input-group">
                <label>Client (application) ID</label>
                <input v-model="azureForm.client_id" type="text" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
              </div>
              <div class="input-group">
                <label>Client secret</label>
                <input v-model="azureForm.client_secret" type="password" placeholder="••••••••" autocomplete="new-password" />
              </div>
              <div class="input-group">
                <label>Management group ID <span class="opt-label">(multi-subscription)</span></label>
                <input v-model="azureForm.management_group_id" type="text" placeholder="e.g. myMgmtGroup" />
              </div>
              <div class="input-group">
                <label>Subscription IDs <span class="opt-label">(multi, comma-separated)</span></label>
                <input v-model="azureForm.subscription_ids_str" type="text" placeholder="id1, id2, id3" />
              </div>
              <div class="input-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="azureForm.persist" /> Save to server config
                </label>
              </div>
            </div>
            <div class="card-actions">
              <button type="submit" class="btn btn-primary" :disabled="connectionStatus.azure === 'saving'">
                {{ connectionStatus.azure === 'saving' ? 'Saving…' : 'Save Azure credentials' }}
              </button>
              <p v-if="messages.azure" class="inline-msg" :class="{ 'msg-err': errors.azure }">{{ messages.azure }}</p>
            </div>
          </form>
          <div class="creds-hint">
            <strong>Minimum RBAC roles:</strong> <code>Reader</code> + <code>Security Reader</code> at subscription scope.
            Register the app in Azure AD → App registrations.
          </div>
        </div>
      </div>

      <div class="setup-footer">
        <router-link to="/dashboard" class="btn btn-secondary">← Go to Dashboard</router-link>
        <router-link to="/" class="setup-later-link">Choose a different cloud</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'

const route = useRoute()

const CLOUDS = [
  { id: 'aws',   label: 'AWS',          icon: `<svg width="18" height="12" viewBox="0 0 80 48" fill="none"><path d="M22.9 32.2c-4.5 2.4-9.4 3.7-14.5 3.7C3.8 35.9 0 32.1 0 27.3c0-5.3 4.5-9.6 10.7-10.2-.3-1.1-.5-2.3-.5-3.6C10.2 6.1 15.9 1 22.9 1c3.4 0 6.5 1.2 8.9 3.2 2.2-4.3 6.7-7.2 11.7-7.2 4.3 0 8.2 1.9 10.8 5 1.9-.7 3.9-1.1 6-1.1C68 1 75 8 75 16.8c0 1.8-.3 3.5-.8 5.1C77.4 23.5 80 27 80 31.1 80 36.8 75.3 41 69.2 41H22.9z" fill="#FF9900"/></svg>` },
  { id: 'gcp',   label: 'Google Cloud', icon: `<svg width="18" height="18" viewBox="0 0 48 48"><path fill="#4285F4" d="M30.2 17.8H24v4.2h6.9c-.7 3.7-4 6.5-7.9 6.5-4.5 0-8.2-3.7-8.2-8.2s3.7-8.2 8.2-8.2c2.1 0 4 .8 5.5 2.1l3-3C29 8.6 26.7 7.5 24 7.5c-7.5 0-13.5 6-13.5 13.5S16.5 34.5 24 34.5c7.2 0 12.8-5 12.8-13.5 0-.8-.1-1.5-.2-2.2l-6.4-1z"/></svg>` },
  { id: 'azure', label: 'Azure',        icon: `<svg width="18" height="18" viewBox="0 0 48 48"><path fill="#0078D4" d="M27 4L13 28l9 5-7 7h16l7-36z"/><path fill="#50E6FF" d="M27 4L4 34l9-1 7-7-3-5z"/></svg>` },
]

const awsForm = reactive({ region: 'us-east-1', access_key_id: '', secret_access_key: '', role_assumption_template: '', persist: true })
const gcpForm = reactive({ project_id: '', credentials_path: '', organization_id: '', folder_id: '', persist: true })
const azureForm = reactive({ subscription_id: '', tenant_id: '', client_id: '', client_secret: '', management_group_id: '', subscription_ids_str: '', persist: true })

const connectionStatus = reactive({ aws: 'none', gcp: 'none', azure: 'none' })
const messages = reactive({ aws: '', gcp: '', azure: '' })
const errors   = reactive({ aws: false, gcp: false, azure: false })
const openPanels = ref(new Set())

function togglePanel(id) {
  const s = new Set(openPanels.value)
  s.has(id) ? s.delete(id) : s.add(id)
  openPanels.value = s
}

onMounted(async () => {
  // Auto-open the panel corresponding to query param
  const q = (route.query.cloud || '').toLowerCase()
  if (q && ['aws', 'gcp', 'azure'].includes(q)) {
    openPanels.value = new Set([q])
  } else {
    openPanels.value = new Set(['aws'])
  }
  // Load saved connection states and multi-account config from API
  try {
    const status = await api.getStatus()
    if (status.aws?.mode !== 'none') {
      connectionStatus.aws = 'connected'
      awsForm.region = status.aws.region || 'us-east-1'
      awsForm.role_assumption_template = status.aws.role_assumption_template || status.aws.organization_role_arn || ''
    }
    if (status.gcp?.mode !== 'none') {
      connectionStatus.gcp = 'connected'
      gcpForm.project_id = status.gcp.project_id || ''
      gcpForm.organization_id = status.gcp.organization_id || ''
      gcpForm.folder_id = status.gcp.folder_id || ''
    }
    if (status.azure?.mode !== 'none') {
      connectionStatus.azure = 'connected'
      azureForm.subscription_id = status.azure.subscription_id || ''
      azureForm.tenant_id = status.azure.tenant_id || ''
      azureForm.management_group_id = status.azure.management_group_id || ''
      const subIds = status.azure.subscription_ids
      azureForm.subscription_ids_str = Array.isArray(subIds) ? subIds.join(', ') : ''
    }
  } catch (_) {
    try {
      const saved = JSON.parse(localStorage.getItem('cspm_cloud_connections') || '{}')
      if (saved.aws)   connectionStatus.aws   = 'connected'
      if (saved.gcp)   connectionStatus.gcp   = 'connected'
      if (saved.azure) connectionStatus.azure = 'connected'
    } catch (__) {}
  }
})

function markConnected(cloud) {
  connectionStatus[cloud] = 'connected'
  try {
    const saved = JSON.parse(localStorage.getItem('cspm_cloud_connections') || '{}')
    saved[cloud] = true
    localStorage.setItem('cspm_cloud_connections', JSON.stringify(saved))
    localStorage.setItem('cspm_cloud', cloud)
  } catch (_) {}
}

async function submitAws() {
  messages.aws = ''
  errors.aws = false
  if (!awsForm.access_key_id?.trim() || !awsForm.secret_access_key?.trim()) {
    messages.aws = 'Access Key ID and Secret Access Key are required.'
    errors.aws = true
    return
  }
  connectionStatus.aws = 'saving'
  try {
    await api.setupAws({
      ...awsForm,
      role_assumption_template: awsForm.role_assumption_template?.trim() || null,
    })
    messages.aws = '✓ AWS credentials saved successfully.'
    markConnected('aws')
  } catch (e) {
    messages.aws = e.message || 'Failed to save AWS credentials.'
    errors.aws = true
    connectionStatus.aws = 'none'
  }
}

async function submitGcp() {
  messages.gcp = ''
  errors.gcp = false
  if (!gcpForm.project_id?.trim() && !gcpForm.organization_id?.trim() && !gcpForm.folder_id?.trim()) {
    messages.gcp = 'Project ID (single) or Organization ID / Folder ID (multi-project) is required.'
    errors.gcp = true
    return
  }
  connectionStatus.gcp = 'saving'
  try {
    await api.setupGcp({
      project_id: gcpForm.project_id,
      credentials_path: gcpForm.credentials_path?.trim() || null,
      organization_id: gcpForm.organization_id?.trim() || null,
      folder_id: gcpForm.folder_id?.trim() || null,
      persist: gcpForm.persist,
    })
    messages.gcp = '✓ Google Cloud credentials saved successfully.'
    markConnected('gcp')
  } catch (e) {
    messages.gcp = e.message || 'Failed to save GCP credentials.'
    errors.gcp = true
    connectionStatus.gcp = 'none'
  }
}

async function submitAzure() {
  messages.azure = ''
  errors.azure = false
  if (!azureForm.subscription_id?.trim() && !azureForm.management_group_id?.trim() && !azureForm.subscription_ids_str?.trim()) {
    messages.azure = 'Subscription ID (single) or Management group ID / Subscription IDs (multi) required.'
    errors.azure = true
    return
  }
  if (!azureForm.client_id?.trim() || !azureForm.client_secret?.trim()) {
    messages.azure = 'Client ID and Client secret are required.'
    errors.azure = true
    return
  }
  connectionStatus.azure = 'saving'
  try {
    const subIds = azureForm.subscription_ids_str
      ? azureForm.subscription_ids_str.split(',').map(s => s.trim()).filter(Boolean)
      : null
    await api.setupAzure({
      subscription_id: azureForm.subscription_id,
      tenant_id: azureForm.tenant_id,
      client_id: azureForm.client_id,
      client_secret: azureForm.client_secret,
      management_group_id: azureForm.management_group_id?.trim() || null,
      subscription_ids: subIds,
      persist: azureForm.persist,
    })
    messages.azure = '✓ Azure credentials saved successfully.'
    markConnected('azure')
  } catch (e) {
    messages.azure = e.message || 'Failed to save Azure credentials.'
    errors.azure = true
    connectionStatus.azure = 'none'
  }
}
</script>

<style scoped>
.setup-page { min-height: 100vh; background: var(--bg-body); padding: 32px 24px; }
.setup-inner { width: 100%; max-width: 700px; margin: 0 auto; }
.setup-header { margin-bottom: 24px; }
.setup-header h1 { font-size: 1.6rem; margin: 0 0 6px; }

/* Status bar */
.status-bar { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 24px; }
.status-pill {
  display: inline-flex; align-items: center; gap: 7px; padding: 6px 14px;
  border-radius: 20px; border: 1px solid var(--border); font-size: 0.82rem; font-weight: 600;
  background: var(--bg-card); color: var(--text-muted);
}
.pill-ok    { border-color: rgba(34,197,94,0.3);   background: rgba(34,197,94,0.07);  color: #4ade80; }
.pill-saving{ border-color: rgba(234,179,8,0.3);   background: rgba(234,179,8,0.07);  color: #fbbf24; }
.pill-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.pill-dot.connected { background: #22c55e; }
.pill-dot.saving    { background: #eab308; animation: pulse 1s infinite; }
.pill-dot.none      { background: #64748b; }
.pill-label { font-size: 0.75rem; font-weight: 500; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

/* Cloud cards */
.cloud-card {
  border: 1px solid var(--border); border-radius: 14px; overflow: hidden;
  margin-bottom: 16px; background: var(--bg-card);
  transition: border-color 0.2s;
}
.card-connected { border-color: rgba(34,197,94,0.35); }

.cloud-card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; cursor: pointer; user-select: none;
  transition: background 0.13s;
}
.cloud-card-header:hover { background: rgba(255,255,255,0.03); }

.cloud-card-title {
  display: flex; align-items: center; gap: 12px; font-weight: 600; font-size: 0.95rem;
}
.cloud-icon { display: flex; align-items: center; }

.conn-badge { font-size: 0.72rem; font-weight: 700; padding: 2px 9px; border-radius: 20px; }
.badge-ok   { background: rgba(34,197,94,0.12);  color: #4ade80; }
.badge-none { background: rgba(100,116,139,0.12); color: #94a3b8; }

.panel-arrow { color: var(--text-muted); transition: transform 0.2s; flex-shrink: 0; }
.panel-arrow.open { transform: rotate(180deg); }

.cloud-card-body { padding: 0 20px 20px; border-top: 1px solid var(--border); }

.fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px; margin-top: 16px; }
.fields-grid .input-group { grid-column: span 1; }
.fields-grid .input-group:first-child,
.fields-grid .input-group:last-child { grid-column: span 2; }

.opt-label { font-size: 0.75rem; color: var(--text-muted); font-weight: 400; }
.field-hint { font-size: 0.78rem; color: var(--text-muted); margin: 4px 0 0; line-height: 1.4; }
.field-hint code { font-size: 0.76rem; }
.checkbox-label { display: flex; align-items: center; gap: 7px; cursor: pointer; font-size: 0.88rem; padding-top: 4px; }

.card-actions { display: flex; align-items: center; gap: 14px; margin-top: 16px; flex-wrap: wrap; }
.inline-msg { font-size: 0.84rem; margin: 0; }
.msg-err { color: var(--error); }
.inline-msg:not(.msg-err) { color: #4ade80; }

.creds-hint {
  margin-top: 14px; padding: 10px 14px; border-radius: 8px; font-size: 0.8rem;
  color: var(--text-muted); line-height: 1.5;
  background: rgba(99,102,241,0.06); border: 1px solid rgba(99,102,241,0.14);
}
.creds-hint code { font-size: 0.78rem; }

.setup-footer {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
  gap: 12px; padding-top: 20px; border-top: 1px solid var(--border); margin-top: 8px;
}
.setup-later-link { font-size: 0.88rem; color: var(--accent); text-decoration: none; }
.setup-later-link:hover { text-decoration: underline; }

@media (max-width: 560px) {
  .fields-grid { grid-template-columns: 1fr; }
  .fields-grid .input-group { grid-column: span 1; }
}
</style>
