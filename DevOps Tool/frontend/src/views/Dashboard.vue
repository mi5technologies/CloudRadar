<template>
  <div>
    <h1>Dashboard</h1>
    <p class="muted">Run security scans, audit assets, and check compliance from the sidebar.</p>
    <div v-if="summaryData" class="dashboard-cards">
      <div class="metric-card metric-scan">
        <span class="metric-label">Last scan</span>
        <span class="metric-value">{{ summaryData.cloud ? summaryData.cloud.toUpperCase() : '—' }} {{ summaryData.summary?.region || '' }}</span>
      </div>
      <div class="metric-card metric-findings">
        <span class="metric-label">Findings</span>
        <span class="metric-value">{{ summaryData.findings_count ?? 0 }}</span>
      </div>
      <div class="metric-card metric-risk">
        <span class="metric-label">Risk score</span>
        <span class="metric-value">{{ summaryData.summary?.risk_score ?? '—' }}</span>
      </div>
    </div>
    <div class="card">
      <h2>Quick actions</h2>
      <p class="muted" style="margin-bottom: 12px;">Run a Security Scan to see step-by-step execution, or use the sidebar for Audit, Compliance, Governance, and Pentest.</p>
      <router-link to="/security/scan" class="btn btn-primary">Run Security Scan</router-link>
      <router-link :to="{ path: '/setup', query: { cloud: selectedCloud } }" class="btn btn-secondary">Setup credentials</router-link>
      <router-link to="/findings" class="btn btn-accent">View Findings</router-link>
      <router-link to="/security/attack-paths" class="btn btn-purple">View Attack Paths</router-link>
    </div>
    <div v-if="cloudStatus" class="card">
      <h2>Status</h2>
      <p><strong>{{ selectedCloudLabel }}</strong>: {{ cloudStatus.mode === 'none' ? 'Not configured' : cloudStatus.mode }}{{ cloudStatus.region ? ' · ' + cloudStatus.region : '' }}{{ cloudStatus.project_id ? ' · ' + cloudStatus.project_id : '' }}{{ cloudStatus.subscription_id ? ' · ' + cloudStatus.subscription_id : '' }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const statusMap = ref(null)
const summaryData = ref(null)
const selectedCloud = ref('aws')
const selectedCloudLabel = computed(() => {
  const labels = { aws: 'AWS', gcp: 'GCP', azure: 'Azure' }
  return labels[selectedCloud.value] || 'Cloud'
})
const cloudStatus = computed(() => {
  if (!statusMap.value) return null
  return statusMap.value[selectedCloud.value] || statusMap.value.aws
})

onMounted(async () => {
  try {
    selectedCloud.value = localStorage.getItem('cspm_cloud') || 'aws'
  } catch (_) {}
  try {
    statusMap.value = await api.getStatus()
  } catch {
    statusMap.value = { aws: { mode: 'none' }, gcp: { mode: 'none' }, azure: { mode: 'none' } }
  }
  try {
    summaryData.value = await api.getSummary()
  } catch {
    summaryData.value = null
  }
})
</script>

<style scoped>
.dashboard-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.metric-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.metric-card.metric-scan { border-left: 4px solid var(--accent); }
.metric-card.metric-findings { border-left: 4px solid var(--accent-teal); }
.metric-card.metric-risk { border-left: 4px solid var(--accent-amber); }
.metric-label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.metric-value { font-size: 1.25rem; font-weight: 600; color: var(--text); }
</style>
