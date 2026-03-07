<template>
  <div class="setup-page">
    <div class="setup-inner">
      <div class="setup-header">
        <h1>{{ cloudLabel }} Setup</h1>
        <p class="muted">Configure credentials for {{ cloudLabel }}. You can also skip and set up later from the dashboard.</p>
      </div>

      <!-- AWS -->
      <div v-if="cloud === 'aws'" class="card setup-card">
        <h2>Credentials</h2>
        <form @submit.prevent="submit">
          <div class="input-group">
            <label>Region</label>
            <input v-model="form.region" placeholder="us-east-1" />
          </div>
          <div class="input-group">
            <label>Access Key ID</label>
            <input v-model="form.access_key_id" type="text" placeholder="AKIA..." />
          </div>
          <div class="input-group">
            <label>Secret Access Key</label>
            <input v-model="form.secret_access_key" type="password" placeholder="..." />
          </div>
          <div class="input-group">
            <label>
              <input type="checkbox" v-model="form.persist" /> Save to config
            </label>
          </div>
          <button type="submit" class="btn btn-primary">Save and continue</button>
        </form>
        <p v-if="message" class="message" :class="{ error: isError }">{{ message }}</p>
      </div>

      <!-- GCP -->
      <div v-else-if="cloud === 'gcp'" class="card setup-card">
        <h2>Credentials</h2>
        <form @submit.prevent="submitGcp">
          <div class="input-group">
            <label>Project ID</label>
            <input v-model="gcpForm.project_id" type="text" placeholder="my-gcp-project" />
          </div>
          <div class="input-group">
            <label>Service account JSON path (optional)</label>
            <input v-model="gcpForm.credentials_path" type="text" placeholder="/path/to/service-account.json" />
          </div>
          <p class="muted" style="font-size: 0.85rem; margin-top: -8px;">Leave blank to use default credentials (gcloud auth application-default login).</p>
          <div class="input-group">
            <label>
              <input type="checkbox" v-model="gcpForm.persist" /> Save to config
            </label>
          </div>
          <button type="submit" class="btn btn-primary">Save and continue</button>
        </form>
        <p v-if="message" class="message" :class="{ error: isError }">{{ message }}</p>
      </div>

      <!-- Azure -->
      <div v-else-if="cloud === 'azure'" class="card setup-card">
        <h2>Service principal credentials</h2>
        <form @submit.prevent="submitAzure">
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
            <input v-model="azureForm.client_secret" type="password" placeholder="..." />
          </div>
          <div class="input-group">
            <label>
              <input type="checkbox" v-model="azureForm.persist" /> Save to config
            </label>
          </div>
          <button type="submit" class="btn btn-primary">Save and continue</button>
        </form>
        <p v-if="message" class="message" :class="{ error: isError }">{{ message }}</p>
      </div>

      <div class="setup-later">
        <router-link to="/dashboard" class="setup-later-link">Setup later</router-link>
        <span class="muted">— go to dashboard without saving credentials</span>
      </div>

      <div class="setup-back">
        <router-link to="/" class="btn btn-secondary">← Choose another cloud</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'

const route = useRoute()
const router = useRouter()
const cloud = computed(() => (route.query.cloud || 'aws').toLowerCase())
const cloudLabel = computed(() => {
  const labels = { aws: 'AWS', gcp: 'Google Cloud', azure: 'Azure' }
  return labels[cloud.value] || 'Cloud'
})

const form = reactive({
  region: 'us-east-1',
  access_key_id: '',
  secret_access_key: '',
  persist: true,
})
const gcpForm = reactive({
  project_id: '',
  credentials_path: '',
  persist: true,
})
const azureForm = reactive({
  subscription_id: '',
  tenant_id: '',
  client_id: '',
  client_secret: '',
  persist: true,
})
const message = ref('')
const isError = ref(false)

async function submit() {
  if (cloud.value !== 'aws') return
  message.value = ''
  isError.value = false
  if (!form.access_key_id?.trim() || !form.secret_access_key?.trim()) {
    message.value = 'Access Key ID and Secret Access Key are required.'
    isError.value = true
    return
  }
  try {
    await api.setupAws(form)
    message.value = 'Credentials saved. Going to dashboard…'
    isError.value = false
    setTimeout(() => router.push('/dashboard'), 800)
  } catch (e) {
    message.value = e.message || 'Failed to save.'
    isError.value = true
  }
}

async function submitGcp() {
  if (cloud.value !== 'gcp') return
  message.value = ''
  isError.value = false
  if (!gcpForm.project_id?.trim()) {
    message.value = 'Project ID is required.'
    isError.value = true
    return
  }
  try {
    await api.setupGcp({
      project_id: gcpForm.project_id,
      credentials_path: gcpForm.credentials_path?.trim() || null,
      persist: gcpForm.persist,
    })
    message.value = 'Credentials saved. Going to dashboard…'
    isError.value = false
    setTimeout(() => router.push('/dashboard'), 800)
  } catch (e) {
    message.value = e.message || 'Failed to save.'
    isError.value = true
  }
}

async function submitAzure() {
  if (cloud.value !== 'azure') return
  message.value = ''
  isError.value = false
  if (!azureForm.subscription_id?.trim() || !azureForm.client_id?.trim() || !azureForm.client_secret?.trim()) {
    message.value = 'Subscription ID, Client ID, and Client secret are required.'
    isError.value = true
    return
  }
  try {
    await api.setupAzure({
      subscription_id: azureForm.subscription_id,
      tenant_id: azureForm.tenant_id,
      client_id: azureForm.client_id,
      client_secret: azureForm.client_secret,
      persist: azureForm.persist,
    })
    message.value = 'Credentials saved. Going to dashboard…'
    isError.value = false
    setTimeout(() => router.push('/dashboard'), 800)
  } catch (e) {
    message.value = e.message || 'Failed to save.'
    isError.value = true
  }
}
</script>

<style scoped>
.setup-page {
  min-height: 100vh;
  background: var(--bg-body);
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.setup-inner {
  width: 100%;
  max-width: 480px;
}
.setup-header {
  margin-bottom: 24px;
  text-align: center;
}
.setup-header h1 {
  font-size: 1.5rem;
  margin: 0 0 8px;
}
.setup-card {
  margin-bottom: 24px;
}
.message {
  margin-top: 12px;
  font-size: 0.9rem;
}
.message.error {
  color: var(--error);
}
.setup-later {
  text-align: center;
  padding: 16px 0;
  border-top: 1px solid var(--border);
}
.setup-later-link {
  font-weight: 600;
  color: var(--accent);
  margin-right: 6px;
}
.setup-later-link:hover {
  text-decoration: underline;
}
.setup-back {
  margin-top: 16px;
  text-align: center;
}
</style>
