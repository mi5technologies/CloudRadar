<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <router-link to="/" class="brand-link">
        <img src="/cloudradar-logo.png" alt="CloudRadar" class="brand-logo" />
        <span class="brand-name">CloudRadar</span>
      </router-link>
    </div>
    <nav class="sidebar-nav">
      <div class="nav-group nav-group-security">
        <div class="nav-group-label">Security</div>
        <router-link to="/security/scan" class="nav-item">Scan assets</router-link>
        <router-link to="/security/vulnerabilities" class="nav-item">Vulnerabilities</router-link>
        <router-link to="/findings" class="nav-item">Findings</router-link>
        <router-link to="/security/attack-paths" class="nav-item">
          <span class="nav-icon">⛓</span>Attack Paths
        </router-link>
        <router-link to="/security/scheduled" class="nav-item">
          <span class="nav-icon">🕐</span>Scheduled Scans
        </router-link>
        <router-link to="/security/notifications" class="nav-item">
          <span class="nav-icon">🔔</span>Notifications
        </router-link>
      </div>
      <div class="nav-group nav-group-audit">
        <div class="nav-group-label">Audit</div>
        <router-link to="/audit/assets" class="nav-item">List assets</router-link>
        <router-link to="/audit/changes" class="nav-item">Changes</router-link>
        <router-link to="/audit/diff" class="nav-item">Snapshot diff</router-link>
      </div>
      <div class="nav-group nav-group-compliance">
        <div class="nav-group-label">Compliance</div>
        <router-link to="/compliance" class="nav-item">Compliance report</router-link>
      </div>
      <div class="nav-group nav-group-governance">
        <div class="nav-group-label">Governance</div>
        <router-link to="/governance" class="nav-item">Governance report</router-link>
      </div>
      <div class="nav-group nav-group-pentest">
        <div class="nav-group-label">Pentest</div>
        <router-link to="/pentest" class="nav-item">Run pentest</router-link>
      </div>
      <div class="nav-group nav-group-tests">
        <div class="nav-group-label">Tests</div>
        <router-link to="/tests" class="nav-item nav-item-tests">
          <span class="nav-icon" aria-hidden="true">🧪</span>
          <span>Run Tests</span>
        </router-link>
      </div>
      <div class="sidebar-bottom">
        <router-link :to="{ path: '/setup', query: { cloud: selectedCloud } }" class="nav-item nav-item-setup" :title="'Configure ' + selectedCloudLabel">
          <svg class="nav-icon-gear" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="3"/>
            <path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42M19.78 12a7.78 7.78 0 01-2.49 5.71M12 4.22a7.78 7.78 0 015.71-2.49M4.22 12a7.78 7.78 0 012.49-5.71M12 19.78a7.78 7.78 0 005.71 2.49"/>
          </svg>
          <span class="nav-item-label">Setup</span>
        </router-link>
        <router-link to="/documentation" class="nav-item nav-item-docs">
          <span class="nav-icon">📄</span>
          <span>Documentation</span>
        </router-link>
      </div>
    </nav>
    <div class="sidebar-footer">
      <div class="theme-row">
        <span class="theme-label">Theme</span>
        <button type="button" class="theme-toggle" :class="{ active: isLight }" @click="setTheme(true)" title="Light theme">☀️</button>
        <button type="button" class="theme-toggle" :class="{ active: !isLight }" @click="setTheme(false)" title="Dark theme">🌙</button>
      </div>
      <div v-if="statusMap || selectedCloud" class="status-compact">
        <span class="status-label">{{ selectedCloudLabel }}</span>
        <span v-if="cloudStatus">{{ cloudStatusText }}</span>
        <span v-else>Not configured</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const statusMap = ref(null)
const selectedCloud = ref('aws')
const isLight = ref(false)

function setTheme(light) {
  isLight.value = light
  if (light) {
    document.documentElement.classList.add('theme-light')
    try { localStorage.setItem('cspm_theme', 'light') } catch (_) {}
  } else {
    document.documentElement.classList.remove('theme-light')
    try { localStorage.setItem('cspm_theme', 'dark') } catch (_) {}
  }
}

const selectedCloudLabel = computed(() => {
  const labels = { aws: 'AWS', gcp: 'GCP', azure: 'Azure' }
  return labels[selectedCloud.value] || 'Cloud'
})

const cloudStatus = computed(() => {
  if (!statusMap.value) return null
  return statusMap.value[selectedCloud.value] || statusMap.value.aws
})

const cloudStatusText = computed(() => {
  const s = cloudStatus.value
  if (!s || s.mode === 'none') return 'Not configured'
  if (s.region) return `${s.mode} · ${s.region}`
  if (s.project_id) return `${s.mode} · ${s.project_id}`
  if (s.subscription_id) return `${s.mode} · ${s.subscription_id}`
  return s.mode || 'Configured'
})

onMounted(async () => {
  try {
    selectedCloud.value = localStorage.getItem('cspm_cloud') || 'aws'
  } catch (_) {}
  try {
    const theme = localStorage.getItem('cspm_theme')
    isLight.value = theme === 'light'
    if (isLight.value) document.documentElement.classList.add('theme-light')
    else document.documentElement.classList.remove('theme-light')
  } catch (_) {}
  try {
    statusMap.value = await api.getStatus()
  } catch {
    statusMap.value = { aws: { mode: 'none' }, gcp: { mode: 'none' }, azure: { mode: 'none' } }
  }
})
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
}
.sidebar-brand {
  padding: 20px 20px 16px;
  border-bottom: 1px solid var(--border);
}
.sidebar-brand a {
  font-weight: 700;
  font-size: 1.15rem;
  color: var(--text);
}
.brand-link {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
}
.brand-logo {
  height: 32px;
  width: auto;
  max-width: 140px;
  object-fit: contain;
  display: block;
}
.brand-name {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--text);
}
.sidebar-brand a:hover {
  color: var(--text);
}
.sidebar-nav {
  flex: 1;
  padding: 12px 10px;
  overflow-y: auto;
}

/* Setup: at bottom, distinct style, gear icon same size as other nav icons */
.sidebar-bottom {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-icon-gear {
  width: 1.15rem;
  height: 1.15rem;
  flex-shrink: 0;
  opacity: 0.9;
}
.nav-item-setup {
  background: rgba(100, 116, 139, 0.12);
  border-left: 3px solid #94a3b8;
  font-weight: 600;
  color: #cbd5e1;
}
.nav-item-setup:hover {
  background: rgba(100, 116, 139, 0.2);
  color: #e2e8f0;
}
.nav-item-setup.router-link-active {
  background: rgba(100, 116, 139, 0.22);
  color: #f1f5f9;
  border-left-color: #e2e8f0;
}
.sidebar-bottom .nav-item-docs {
  margin-left: 0;
  padding: 9px 12px;
  font-size: 0.88rem;
}
.nav-item-setup {
  margin-left: 0;
  padding: 9px 12px;
  font-size: 0.88rem;
}
.nav-group-docs {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}
.nav-group-docs .nav-group-label { display: none; }
.nav-item-docs {
  color: #a5b4fc;
  font-weight: 500;
}
.nav-item-docs:hover {
  background: rgba(99, 102, 241, 0.15);
  color: #c7d2fe;
}
.nav-item-docs.router-link-active {
  background: rgba(99, 102, 241, 0.2);
  color: #a5b4fc;
}

/* Group labels: bold, uppercase, colored left border */
.nav-group {
  margin-bottom: 20px;
}
.nav-group-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 10px 12px 6px;
  margin-bottom: 4px;
  border-radius: 4px;
  font-family: inherit;
}
.nav-group-security .nav-group-label {
  color: #7dd3fc;
  background: rgba(14, 165, 233, 0.12);
  border-left: 3px solid #0ea5e9;
}
.nav-group-audit .nav-group-label {
  color: #fcd34d;
  background: rgba(234, 179, 8, 0.1);
  border-left: 3px solid #eab308;
}
.nav-group-compliance .nav-group-label {
  color: #86efac;
  background: rgba(34, 197, 94, 0.1);
  border-left: 3px solid #22c55e;
}
.nav-group-governance .nav-group-label {
  color: #c4b5fd;
  background: rgba(139, 92, 246, 0.12);
  border-left: 3px solid #8b5cf6;
}
.nav-group-pentest .nav-group-label {
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.1);
  border-left: 3px solid #ef4444;
}

/* Section items: indented, different weight */
.nav-group .nav-item {
  margin-left: 6px;
  padding: 9px 12px;
  font-size: 0.88rem;
  font-weight: 500;
}
.nav-group-security .nav-item {
  color: #bae6fd;
}
.nav-group-security .nav-item:hover {
  background: rgba(14, 165, 233, 0.15);
  color: #7dd3fc;
}
.nav-group-security .nav-item.router-link-active {
  background: rgba(14, 165, 233, 0.2);
  color: #38bdf8;
}
.nav-group-audit .nav-item {
  color: #fde68a;
}
.nav-group-audit .nav-item:hover {
  background: rgba(234, 179, 8, 0.12);
  color: #fcd34d;
}
.nav-group-audit .nav-item.router-link-active {
  background: rgba(234, 179, 8, 0.18);
  color: #fbbf24;
}
.nav-group-compliance .nav-item {
  color: #bbf7d0;
}
.nav-group-compliance .nav-item:hover {
  background: rgba(34, 197, 94, 0.12);
  color: #86efac;
}
.nav-group-compliance .nav-item.router-link-active {
  background: rgba(34, 197, 94, 0.18);
  color: #4ade80;
}
.nav-group-governance .nav-item {
  color: #ddd6fe;
}
.nav-group-governance .nav-item:hover {
  background: rgba(139, 92, 246, 0.12);
  color: #c4b5fd;
}
.nav-group-governance .nav-item.router-link-active {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}
.nav-group-pentest .nav-item {
  color: #fecaca;
}
.nav-group-pentest .nav-item:hover {
  background: rgba(239, 68, 68, 0.12);
  color: #fca5a5;
}
.nav-group-pentest .nav-item.router-link-active {
  background: rgba(239, 68, 68, 0.18);
  color: #f87171;
}
.nav-group-tests .nav-group-label {
  color: #d946ef;
  background: rgba(217, 70, 239, 0.16);
  border-left: 3px solid #d946ef;
}
.nav-item-tests {
  color: #d946ef !important;
  cursor: pointer !important;
  pointer-events: all !important;
}
.nav-item-tests * {
  pointer-events: none;
}
.nav-item-tests:hover {
  background: rgba(217, 70, 239, 0.22) !important;
  color: #e879f9 !important;
  cursor: pointer !important;
}
.nav-item-tests.router-link-active {
  background: rgba(217, 70, 239, 0.28) !important;
  color: #f0abfc !important;
  border-left: 3px solid #d946ef;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  border-radius: 6px;
  margin-bottom: 2px;
  text-decoration: none;
  cursor: pointer;
  pointer-events: all;
  transition: background 0.15s, color 0.15s;
}
.nav-icon {
  font-size: 0.95rem;
  opacity: 0.9;
  pointer-events: none;
}
.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--border);
}
.theme-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}
.theme-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-right: 4px;
}
.theme-toggle {
  padding: 6px 10px;
  border-radius: 6px;
  border: none;
  background: rgba(148, 163, 184, 0.15);
  color: var(--text);
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.15s;
}
.theme-toggle:hover {
  background: rgba(148, 163, 184, 0.25);
}
.theme-toggle.active {
  background: var(--accent);
  color: #fff;
}
.theme-toggle.active:hover {
  background: var(--accent-hover);
  color: #fff;
}
.status-compact {
  font-size: 0.8rem;
  color: var(--text-muted);
}
.status-label {
  font-weight: 600;
  color: var(--text);
  margin-right: 6px;
}
</style>
