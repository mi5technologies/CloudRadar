<template>
  <aside class="sidebar" :class="{ collapsed }">
    <!-- Brand + Collapse toggle -->
    <div class="sidebar-brand">
      <router-link to="/" class="brand-link" :title="collapsed ? 'Back to cloud selection' : 'Select cloud provider'">
        <img src="/cloudradar-logo.png" alt="CloudRadar" class="brand-logo" />
        <span v-show="!collapsed" class="brand-name">CloudRadar</span>
      </router-link>
      <button class="collapse-btn" @click="toggleCollapse" :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline v-if="!collapsed" points="15 18 9 12 15 6" />
          <polyline v-else points="9 18 15 12 9 6" />
        </svg>
      </button>
    </div>

    <nav class="sidebar-nav">
      <!-- Dashboard (top-level, always visible) -->
      <router-link to="/dashboard" class="nav-item nav-item-dashboard" :title="collapsed ? 'Dashboard' : ''">
        <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
          <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
        </svg>
        <span class="nav-label" v-show="!collapsed">Dashboard</span>
      </router-link>

      <!-- ── Security ── -->
      <div class="nav-group nav-group-security" :class="{ 'group-closed': !groups.security && !collapsed }">
        <button class="nav-group-header nav-group-security-header" @click="!collapsed && toggleGroup('security')" :class="{ clickable: !collapsed }" v-show="!collapsed">
          <span class="nav-group-label-text">Security</span>
          <svg class="nav-group-arrow" :class="{ open: groups.security }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        <transition name="group-slide">
          <div class="nav-group-items" v-show="collapsed || groups.security">
            <router-link to="/security/scan" class="nav-item" :title="collapsed ? 'Scan Assets' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Scan assets</span>
            </router-link>
            <router-link to="/security/vulnerabilities" class="nav-item" :title="collapsed ? 'Vulnerabilities' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Vulnerabilities</span>
            </router-link>
            <router-link to="/findings" class="nav-item" :title="collapsed ? 'Findings' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Findings</span>
            </router-link>
            <router-link to="/security/attack-paths" class="nav-item" :title="collapsed ? 'Attack Paths' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Attack Paths</span>
            </router-link>
            <router-link to="/security/scheduled" class="nav-item" :title="collapsed ? 'Scheduled Scans' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Scheduled Scans</span>
            </router-link>
            <router-link to="/security/notifications" class="nav-item" :title="collapsed ? 'Notifications' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Notifications</span>
            </router-link>
          </div>
        </transition>
      </div>

      <!-- ── Audit ── -->
      <div class="nav-group nav-group-audit" :class="{ 'group-closed': !groups.audit && !collapsed }">
        <button class="nav-group-header nav-group-audit-header" @click="!collapsed && toggleGroup('audit')" :class="{ clickable: !collapsed }" v-show="!collapsed">
          <span class="nav-group-label-text">Audit</span>
          <svg class="nav-group-arrow" :class="{ open: groups.audit }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        <transition name="group-slide">
          <div class="nav-group-items" v-show="collapsed || groups.audit">
            <router-link to="/audit/assets" class="nav-item" :title="collapsed ? 'List Assets' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">List assets</span>
            </router-link>
            <router-link to="/audit/changes" class="nav-item" :title="collapsed ? 'Changes' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 014-4h14"/>
                <polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 01-4 4H3"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Changes</span>
            </router-link>
            <router-link to="/audit/diff" class="nav-item" :title="collapsed ? 'Snapshot Diff' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Snapshot diff</span>
            </router-link>
            <router-link to="/audit/logs" class="nav-item" :title="collapsed ? 'Audit Logs' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/><line x1="13" y1="17" x2="8" y2="17"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Audit Logs</span>
            </router-link>
            <router-link to="/scan-history" class="nav-item" :title="collapsed ? 'Scan History' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Scan History</span>
            </router-link>
          </div>
        </transition>
      </div>

      <!-- ── Compliance ── -->
      <div class="nav-group nav-group-compliance" :class="{ 'group-closed': !groups.compliance && !collapsed }">
        <button class="nav-group-header nav-group-compliance-header" @click="!collapsed && toggleGroup('compliance')" :class="{ clickable: !collapsed }" v-show="!collapsed">
          <span class="nav-group-label-text">Compliance</span>
          <svg class="nav-group-arrow" :class="{ open: groups.compliance }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        <transition name="group-slide">
          <div class="nav-group-items" v-show="collapsed || groups.compliance">
            <router-link to="/compliance" class="nav-item" :title="collapsed ? 'Compliance Report' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Compliance report</span>
            </router-link>
          </div>
        </transition>
      </div>

      <!-- ── Governance ── -->
      <div class="nav-group nav-group-governance" :class="{ 'group-closed': !groups.governance && !collapsed }">
        <button class="nav-group-header nav-group-governance-header" @click="!collapsed && toggleGroup('governance')" :class="{ clickable: !collapsed }" v-show="!collapsed">
          <span class="nav-group-label-text">Governance</span>
          <svg class="nav-group-arrow" :class="{ open: groups.governance }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        <transition name="group-slide">
          <div class="nav-group-items" v-show="collapsed || groups.governance">
            <router-link to="/governance" class="nav-item" :title="collapsed ? 'Governance Report' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Governance report</span>
            </router-link>
          </div>
        </transition>
      </div>

      <!-- ── Pentest ── -->
      <div class="nav-group nav-group-pentest" :class="{ 'group-closed': !groups.pentest && !collapsed }">
        <button class="nav-group-header nav-group-pentest-header" @click="!collapsed && toggleGroup('pentest')" :class="{ clickable: !collapsed }" v-show="!collapsed">
          <span class="nav-group-label-text">Pentest</span>
          <svg class="nav-group-arrow" :class="{ open: groups.pentest }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        <transition name="group-slide">
          <div class="nav-group-items" v-show="collapsed || groups.pentest">
            <router-link to="/pentest" class="nav-item" :title="collapsed ? 'Run Pentest' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Run pentest</span>
            </router-link>
          </div>
        </transition>
      </div>

      <!-- ── Cost ── -->
      <div class="nav-group nav-group-cost" :class="{ 'group-closed': !groups.cost && !collapsed }">
        <button class="nav-group-header nav-group-cost-header" @click="!collapsed && toggleGroup('cost')" :class="{ clickable: !collapsed }" v-show="!collapsed">
          <span class="nav-group-label-text">Cost</span>
          <svg class="nav-group-arrow" :class="{ open: groups.cost }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        <transition name="group-slide">
          <div class="nav-group-items" v-show="collapsed || groups.cost">
            <router-link to="/cost" class="nav-item nav-item-cost" :title="collapsed ? 'Cost Optimisation' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Cost optimisation</span>
            </router-link>
          </div>
        </transition>
      </div>

      <!-- ── Tests ── -->
      <div class="nav-group nav-group-tests" :class="{ 'group-closed': !groups.tests && !collapsed }">
        <button class="nav-group-header nav-group-tests-header" @click="!collapsed && toggleGroup('tests')" :class="{ clickable: !collapsed }" v-show="!collapsed">
          <span class="nav-group-label-text">Tests</span>
          <svg class="nav-group-arrow" :class="{ open: groups.tests }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        <transition name="group-slide">
          <div class="nav-group-items" v-show="collapsed || groups.tests">
            <router-link to="/tests" class="nav-item nav-item-tests" :title="collapsed ? 'Run Tests' : ''">
              <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v11m0 0l-3 3m3-3l3 3m4-14v11m0 0l-3 3m3-3l3 3"/>
              </svg>
              <span class="nav-label" v-show="!collapsed">Run Tests</span>
            </router-link>
          </div>
        </transition>
      </div>

      <!-- Bottom: Setup + Docs -->
      <div class="sidebar-bottom">
        <router-link :to="{ path: '/setup', query: { cloud: selectedCloud } }" class="nav-item nav-item-setup" :title="collapsed ? 'Setup – Configure ' + selectedCloudLabel : 'Configure ' + selectedCloudLabel">
          <svg class="nav-icon-gear" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
          </svg>
          <span class="nav-label" v-show="!collapsed">Setup</span>
        </router-link>
        <router-link to="/documentation" class="nav-item nav-item-docs" :title="collapsed ? 'Documentation' : ''">
          <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 19.5A2.5 2.5 0 016.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/>
          </svg>
          <span class="nav-label" v-show="!collapsed">Documentation</span>
        </router-link>
      </div>
    </nav>

    <!-- User profile -->
    <div class="sidebar-user" :class="{ 'sidebar-user-collapsed': collapsed }">
      <div class="user-avatar" :style="{ background: userColor }" :title="collapsed ? userName : ''">
        {{ userInitials }}
      </div>
      <template v-if="!collapsed">
        <div class="user-details">
          <div v-if="!editingName" class="user-name-row">
            <span class="user-name">{{ userName }}</span>
            <button class="user-edit-btn" @click="startEditName" title="Edit name">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
          </div>
          <input
            v-else
            class="user-name-input"
            v-model="userNameEdit"
            @keyup.enter="saveName"
            @keyup.escape="cancelEdit"
            @blur="saveName"
            ref="nameInput"
            maxlength="32"
          />
          <span class="user-role">Administrator</span>
        </div>
      </template>
    </div>

    <!-- Footer: theme + cloud status -->
    <div class="sidebar-footer">
      <div class="theme-row" v-show="!collapsed">
        <span class="theme-label">Theme</span>
        <button type="button" class="theme-toggle" :class="{ active: isLight }" @click="setTheme(true)" title="Light theme">☀️</button>
        <button type="button" class="theme-toggle" :class="{ active: !isLight }" @click="setTheme(false)" title="Dark theme">🌙</button>
      </div>
      <div class="theme-row-collapsed" v-show="collapsed">
        <button type="button" class="theme-toggle theme-toggle-sm" :class="{ active: isLight }" @click="setTheme(true)" title="Light theme">☀️</button>
        <button type="button" class="theme-toggle theme-toggle-sm" :class="{ active: !isLight }" @click="setTheme(false)" title="Dark theme">🌙</button>
      </div>
      <div v-if="(statusMap || selectedCloud) && !collapsed" class="status-compact">
        <span class="status-label">{{ selectedCloudLabel }}</span>
        <span v-if="cloudStatus">{{ cloudStatusText }}</span>
        <span v-else>Not configured</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '../api'

const statusMap = ref(null)
const selectedCloud = ref('aws')
const isLight = ref(false)
const collapsed = ref(false)

// Collapsible groups — all open by default
const groups = ref({
  security: true,
  audit: true,
  compliance: true,
  governance: true,
  pentest: true,
  cost: true,
  tests: true,
})

function toggleGroup(name) {
  groups.value[name] = !groups.value[name]
  try { localStorage.setItem('cspm_groups', JSON.stringify(groups.value)) } catch (_) {}
}

// User profile
const userName = ref('Admin')
const userNameEdit = ref('')
const editingName = ref(false)
const nameInput = ref(null)

const AVATAR_COLORS = ['#0ea5e9','#8b5cf6','#14b8a6','#f59e0b','#ef4444','#22c55e','#ec4899','#f97316']
const userColor = computed(() => {
  let hash = 0
  for (const c of userName.value) hash = (hash * 31 + c.charCodeAt(0)) & 0xffffffff
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length]
})
const userInitials = computed(() =>
  userName.value.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
)

function startEditName() {
  userNameEdit.value = userName.value
  editingName.value = true
  nextTick(() => nameInput.value?.focus())
}
function saveName() {
  const name = userNameEdit.value.trim()
  if (name) {
    userName.value = name
    try { localStorage.setItem('cspm_user_name', name) } catch (_) {}
  }
  editingName.value = false
}
function cancelEdit() {
  editingName.value = false
}

// Sidebar collapse
function toggleCollapse() {
  collapsed.value = !collapsed.value
  try { localStorage.setItem('cspm_sidebar_collapsed', String(collapsed.value)) } catch (_) {}
  updateSidebarWidth()
}
function updateSidebarWidth() {
  document.documentElement.style.setProperty('--sidebar-width', collapsed.value ? '64px' : '260px')
}

// Theme
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
  try { selectedCloud.value = localStorage.getItem('cspm_cloud') || 'aws' } catch (_) {}
  try {
    const theme = localStorage.getItem('cspm_theme')
    isLight.value = theme === 'light'
    if (isLight.value) document.documentElement.classList.add('theme-light')
    else document.documentElement.classList.remove('theme-light')
  } catch (_) {}
  try {
    const stored = localStorage.getItem('cspm_sidebar_collapsed')
    if (stored === 'true') { collapsed.value = true; updateSidebarWidth() }
  } catch (_) {}
  try {
    const name = localStorage.getItem('cspm_user_name')
    if (name) userName.value = name
  } catch (_) {}
  try {
    const savedGroups = JSON.parse(localStorage.getItem('cspm_groups') || '{}')
    Object.assign(groups.value, savedGroups)
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
  width: var(--sidebar-width, 260px);
  min-width: var(--sidebar-width, 260px);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  overflow: hidden;
  transition: width 0.22s ease, min-width 0.22s ease;
  z-index: 100;
}

/* ── Brand ── */
.sidebar-brand {
  padding: 16px 14px 14px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.brand-link {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
  min-width: 0;
  transition: opacity 0.15s;
}
.brand-link:hover { opacity: 0.8; }
.brand-logo {
  height: 28px;
  width: auto;
  max-width: 110px;
  object-fit: contain;
  display: block;
  flex-shrink: 0;
}
.brand-name {
  font-weight: 700;
  font-size: 1.05rem;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
}
.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: rgba(148,163,184,0.08);
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
}
.collapse-btn:hover { background: rgba(148,163,184,0.18); color: var(--text); }
.collapse-btn svg { width: 14px; height: 14px; }

/* ── Nav ── */
.sidebar-nav {
  flex: 1;
  padding: 10px 8px;
  overflow-y: auto;
  overflow-x: hidden;
}
.sidebar-nav::-webkit-scrollbar { width: 4px; }
.sidebar-nav::-webkit-scrollbar-track { background: transparent; }
.sidebar-nav::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.15); border-radius: 2px; }

/* Dashboard */
.nav-item-dashboard {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  margin-bottom: 10px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-muted);
  font-size: 0.9rem;
  font-weight: 600;
  transition: background 0.15s, color 0.15s;
  border: 1px solid transparent;
  white-space: nowrap;
}
.nav-item-dashboard:hover { background: rgba(14,165,233,0.12); color: var(--text); }
.nav-item-dashboard.router-link-active { background: rgba(14,165,233,0.18); color: #38bdf8; border-color: rgba(14,165,233,0.2); }

/* ── Group header (clickable label with arrow) ── */
.nav-group { margin-bottom: 4px; }
.nav-group.group-closed { margin-bottom: 2px; }

.nav-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 7px 12px 6px;
  margin-bottom: 2px;
  border-radius: 5px;
  border: none;
  background: transparent;
  font-family: inherit;
  text-align: left;
  cursor: default;
  user-select: none;
}
.nav-group-header.clickable { cursor: pointer; }
.nav-group-header.clickable:hover { background: rgba(148,163,184,0.07); }

.nav-group-label-text {
  font-size: 0.67rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.09em;
}
.nav-group-security-header  { border-left: 3px solid #0ea5e9; }
.nav-group-audit-header     { border-left: 3px solid #eab308; }
.nav-group-compliance-header{ border-left: 3px solid #22c55e; }
.nav-group-governance-header{ border-left: 3px solid #8b5cf6; }
.nav-group-pentest-header   { border-left: 3px solid #ef4444; }
.nav-group-tests-header     { border-left: 3px solid #d946ef; }

.nav-group-security-header  .nav-group-label-text { color: #7dd3fc; }
.nav-group-audit-header     .nav-group-label-text { color: #fcd34d; }
.nav-group-compliance-header .nav-group-label-text{ color: #86efac; }
.nav-group-governance-header .nav-group-label-text{ color: #c4b5fd; }
.nav-group-pentest-header   .nav-group-label-text { color: #fca5a5; }
.nav-group-tests-header     .nav-group-label-text { color: #d946ef; }

.nav-group-arrow {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  opacity: 0.5;
  transform: rotate(-90deg);
  transition: transform 0.2s ease, opacity 0.15s;
}
.nav-group-arrow.open {
  transform: rotate(0deg);
  opacity: 0.8;
}
.nav-group-security-header  .nav-group-arrow { color: #7dd3fc; }
.nav-group-audit-header     .nav-group-arrow { color: #fcd34d; }
.nav-group-compliance-header .nav-group-arrow{ color: #86efac; }
.nav-group-governance-header .nav-group-arrow{ color: #c4b5fd; }
.nav-group-pentest-header   .nav-group-arrow { color: #fca5a5; }
.nav-group-tests-header     .nav-group-arrow { color: #d946ef; }

/* Group items container */
.nav-group-items { overflow: hidden; }

/* Slide transition for groups */
.group-slide-enter-active {
  transition: max-height 0.22s ease, opacity 0.18s ease;
  max-height: 400px;
  overflow: hidden;
}
.group-slide-leave-active {
  transition: max-height 0.18s ease, opacity 0.14s ease;
  max-height: 400px;
  overflow: hidden;
}
.group-slide-enter-from,
.group-slide-leave-to {
  max-height: 0 !important;
  opacity: 0;
}

/* Nav items */
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  margin-left: 4px;
  margin-bottom: 1px;
  border-radius: 6px;
  text-decoration: none;
  cursor: pointer;
  font-size: 0.87rem;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
  overflow: hidden;
}
.nav-svg {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
  opacity: 0.85;
}
.nav-label { overflow: hidden; }

.nav-group-security .nav-item { color: #bae6fd; }
.nav-group-security .nav-item:hover { background: rgba(14,165,233,0.14); color: #7dd3fc; }
.nav-group-security .nav-item.router-link-active { background: rgba(14,165,233,0.2); color: #38bdf8; }

.nav-group-audit .nav-item { color: #fde68a; }
.nav-group-audit .nav-item:hover { background: rgba(234,179,8,0.12); color: #fcd34d; }
.nav-group-audit .nav-item.router-link-active { background: rgba(234,179,8,0.18); color: #fbbf24; }

.nav-group-compliance .nav-item { color: #bbf7d0; }
.nav-group-compliance .nav-item:hover { background: rgba(34,197,94,0.12); color: #86efac; }
.nav-group-compliance .nav-item.router-link-active { background: rgba(34,197,94,0.18); color: #4ade80; }

.nav-group-governance .nav-item { color: #ddd6fe; }
.nav-group-governance .nav-item:hover { background: rgba(139,92,246,0.12); color: #c4b5fd; }
.nav-group-governance .nav-item.router-link-active { background: rgba(139,92,246,0.2); color: #a78bfa; }

.nav-group-pentest .nav-item { color: #fecaca; }
.nav-group-pentest .nav-item:hover { background: rgba(239,68,68,0.12); color: #fca5a5; }
.nav-group-pentest .nav-item.router-link-active { background: rgba(239,68,68,0.18); color: #f87171; }

.nav-item-tests { color: #d946ef !important; }
.nav-item-tests:hover { background: rgba(217,70,239,0.2) !important; color: #e879f9 !important; }
.nav-item-tests.router-link-active { background: rgba(217,70,239,0.28) !important; color: #f0abfc !important; }

/* Bottom: Setup + Docs */
.sidebar-bottom {
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-icon-gear { width: 15px; height: 15px; flex-shrink: 0; opacity: 0.85; }
.nav-item-setup {
  margin-left: 0;
  background: rgba(100,116,139,0.12);
  border-left: 3px solid #94a3b8;
  font-weight: 600;
  color: #cbd5e1;
}
.nav-item-setup:hover { background: rgba(100,116,139,0.2); color: #e2e8f0; }
.nav-item-setup.router-link-active { background: rgba(100,116,139,0.22); color: #f1f5f9; border-left-color: #e2e8f0; }
.nav-item-docs { margin-left: 0; color: #a5b4fc; }
.nav-item-docs:hover { background: rgba(99,102,241,0.15); color: #c7d2fe; }
.nav-item-docs.router-link-active { background: rgba(99,102,241,0.2); color: #a5b4fc; }

/* ── User profile ── */
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}
.sidebar-user-collapsed { justify-content: center; padding: 10px 8px; }
.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
  user-select: none;
}
.user-details { flex: 1; min-width: 0; }
.user-name-row { display: flex; align-items: center; gap: 6px; }
.user-name { font-size: 0.85rem; font-weight: 600; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-role { display: block; font-size: 0.72rem; color: var(--text-muted); margin-top: 1px; }
.user-edit-btn {
  background: none; border: none; padding: 3px; cursor: pointer;
  color: var(--text-muted); border-radius: 4px;
  display: flex; align-items: center;
  transition: color 0.15s, background 0.15s; flex-shrink: 0;
}
.user-edit-btn:hover { color: var(--text); background: rgba(148,163,184,0.15); }
.user-name-input {
  width: 100%; padding: 4px 8px; border-radius: 5px;
  border: 1px solid var(--accent); background: rgba(14,165,233,0.08);
  color: var(--text); font-size: 0.84rem; font-family: inherit; outline: none;
}

/* ── Footer ── */
.sidebar-footer {
  padding: 10px 14px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}
.theme-row { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.theme-row-collapsed { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.theme-label { font-size: 0.75rem; color: var(--text-muted); margin-right: 4px; }
.theme-toggle {
  padding: 5px 9px; border-radius: 6px; border: none;
  background: rgba(148,163,184,0.15); color: var(--text);
  cursor: pointer; font-size: 0.95rem; transition: background 0.15s;
}
.theme-toggle-sm { padding: 4px 7px; font-size: 0.85rem; }
.theme-toggle:hover { background: rgba(148,163,184,0.25); }
.theme-toggle.active { background: var(--accent); color: #fff; }
.theme-toggle.active:hover { background: var(--accent-hover); }
.status-compact { font-size: 0.78rem; color: var(--text-muted); overflow: hidden; }
.status-label { font-weight: 600; color: var(--text); margin-right: 5px; }

/* ── Mobile ── */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0; top: 0; bottom: 0;
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    box-shadow: none;
  }
  .sidebar.sidebar-mobile-open {
    transform: translateX(0);
    box-shadow: 8px 0 32px rgba(0,0,0,0.4);
  }
}

/* ── Collapsed overrides ── */
.sidebar.collapsed .nav-item { justify-content: center; margin-left: 0; padding: 9px 0; }
.sidebar.collapsed .nav-item-dashboard { justify-content: center; padding: 9px 0; }
.sidebar.collapsed .nav-item-setup { padding: 9px 0; }
.sidebar.collapsed .nav-group { margin-bottom: 4px; }
.sidebar.collapsed .sidebar-bottom { padding-top: 8px; }
.sidebar.collapsed .sidebar-brand { padding: 14px 0; justify-content: center; }
.sidebar.collapsed .sidebar-footer { padding: 8px 0; display: flex; flex-direction: column; align-items: center; gap: 4px; }

/* ── Light theme: group headers ── */
:global(.theme-light) .nav-group-header.clickable:hover { background: rgba(0,0,0,0.04); }

:global(.theme-light) .nav-group-security-header {
  background: rgba(2,132,199,0.08);
  border-left-color: #0284c7;
}
:global(.theme-light) .nav-group-security-header .nav-group-label-text { color: #0369a1; }
:global(.theme-light) .nav-group-security-header .nav-group-arrow { color: #0369a1; }

:global(.theme-light) .nav-group-audit-header {
  background: rgba(217,119,6,0.1);
  border-left-color: #d97706;
}
:global(.theme-light) .nav-group-audit-header .nav-group-label-text { color: #92400e; }
:global(.theme-light) .nav-group-audit-header .nav-group-arrow { color: #92400e; }

:global(.theme-light) .nav-group-compliance-header {
  background: rgba(22,163,74,0.08);
  border-left-color: #16a34a;
}
:global(.theme-light) .nav-group-compliance-header .nav-group-label-text { color: #15803d; }
:global(.theme-light) .nav-group-compliance-header .nav-group-arrow { color: #15803d; }

:global(.theme-light) .nav-group-governance-header {
  background: rgba(124,58,237,0.08);
  border-left-color: #7c3aed;
}
:global(.theme-light) .nav-group-governance-header .nav-group-label-text { color: #6d28d9; }
:global(.theme-light) .nav-group-governance-header .nav-group-arrow { color: #6d28d9; }

:global(.theme-light) .nav-group-pentest-header {
  background: rgba(220,38,38,0.08);
  border-left-color: #dc2626;
}
:global(.theme-light) .nav-group-pentest-header .nav-group-label-text { color: #b91c1c; }
:global(.theme-light) .nav-group-pentest-header .nav-group-arrow { color: #b91c1c; }

:global(.theme-light) .nav-group-tests-header {
  background: rgba(126,34,206,0.08);
  border-left-color: #9333ea;
}
:global(.theme-light) .nav-group-tests-header .nav-group-label-text { color: #7e22ce; }
:global(.theme-light) .nav-group-tests-header .nav-group-arrow { color: #7e22ce; }

/* Light theme: nav items refined */
:global(.theme-light) .nav-group-security .nav-item:hover { background: rgba(2,132,199,0.1); color: #0284c7; }
:global(.theme-light) .nav-group-security .nav-item.router-link-active { background: rgba(2,132,199,0.13); color: #0369a1; }
:global(.theme-light) .nav-group-audit .nav-item:hover { background: rgba(217,119,6,0.1); color: #b45309; }
:global(.theme-light) .nav-group-audit .nav-item.router-link-active { background: rgba(217,119,6,0.14); color: #92400e; }
:global(.theme-light) .nav-group-compliance .nav-item:hover { background: rgba(22,163,74,0.1); }
:global(.theme-light) .nav-group-governance .nav-item:hover { background: rgba(124,58,237,0.1); }
:global(.theme-light) .nav-group-pentest .nav-item:hover { background: rgba(220,38,38,0.1); }
:global(.theme-light) .nav-item-dashboard { color: #334155; }
:global(.theme-light) .nav-item-dashboard:hover { background: rgba(2,132,199,0.1); color: #0369a1; }
:global(.theme-light) .nav-item-dashboard.router-link-active { background: rgba(2,132,199,0.14); color: #0284c7; }
</style>
