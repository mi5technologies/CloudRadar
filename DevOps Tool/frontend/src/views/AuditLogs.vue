<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Audit Logs</h1>
        <p class="muted">Activity history — who ran what and when.</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="exportCsv" :disabled="!logs.length">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Export CSV
        </button>
        <button class="btn btn-danger" @click="confirmClear" :disabled="!logs.length">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/></svg>
          Clear Logs
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="card filters-card">
      <div class="filters-row">
        <div class="filter-group">
          <label>Search</label>
          <input v-model="search" placeholder="Filter by action, user, detail…" class="filter-input" />
        </div>
        <div class="filter-group">
          <label>Status</label>
          <select v-model="filterStatus" class="filter-select">
            <option value="">All</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
            <option value="info">Info</option>
          </select>
        </div>
        <div class="filter-group">
          <label>User</label>
          <select v-model="filterUser" class="filter-select">
            <option value="">All users</option>
            <option v-for="u in uniqueUsers" :key="u" :value="u">{{ u }}</option>
          </select>
        </div>
        <div class="filter-stats">
          <span class="stat-badge">{{ filteredLogs.length }} entries</span>
        </div>
      </div>
    </div>

    <!-- Logs table -->
    <div class="card logs-card" v-if="filteredLogs.length">
      <div class="logs-table-wrap">
        <table class="logs-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>User</th>
              <th>Action</th>
              <th>Detail</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in pagedLogs" :key="log.id" :class="'row-' + log.status">
              <td class="td-time">
                <span class="time-date">{{ formatDate(log.timestamp) }}</span>
                <span class="time-clock">{{ formatTime(log.timestamp) }}</span>
              </td>
              <td class="td-user">
                <span class="user-chip" :style="{ background: avatarColor(log.user) }">
                  {{ initials(log.user) }}
                </span>
                <span class="user-name">{{ log.user }}</span>
              </td>
              <td class="td-action">
                <span class="action-tag">{{ log.action }}</span>
              </td>
              <td class="td-detail">{{ log.detail || '—' }}</td>
              <td class="td-status">
                <span class="status-pill" :class="'status-' + log.status">{{ log.status }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Pagination -->
      <div class="pagination" v-if="totalPages > 1">
        <button class="page-btn" :disabled="page <= 1" @click="page--">‹ Prev</button>
        <span class="page-info">Page {{ page }} of {{ totalPages }}</span>
        <button class="page-btn" :disabled="page >= totalPages" @click="page++">Next ›</button>
      </div>
    </div>

    <div class="card empty-card" v-else>
      <div class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
        <p>No audit logs yet. Activity will be recorded here as you use the app.</p>
      </div>
    </div>

    <!-- Clear confirmation modal -->
    <div class="modal-overlay" v-if="showConfirm" @click.self="showConfirm = false">
      <div class="modal">
        <h3>Clear all logs?</h3>
        <p class="muted">This will permanently delete all {{ logs.length }} audit log entries. This cannot be undone.</p>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showConfirm = false">Cancel</button>
          <button class="btn btn-danger" @click="doClear">Yes, clear</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getAuditLogs, clearAuditLogs } from '../utils/auditLog'

const logs = ref([])
const search = ref('')
const filterStatus = ref('')
const filterUser = ref('')
const page = ref(1)
const PAGE_SIZE = 25
const showConfirm = ref(false)

onMounted(() => {
  logs.value = getAuditLogs()
})

const uniqueUsers = computed(() => [...new Set(logs.value.map(l => l.user))])

const filteredLogs = computed(() => {
  const s = search.value.toLowerCase()
  return logs.value.filter(l => {
    if (filterStatus.value && l.status !== filterStatus.value) return false
    if (filterUser.value && l.user !== filterUser.value) return false
    if (s && !l.action.toLowerCase().includes(s) && !l.user.toLowerCase().includes(s) && !(l.detail || '').toLowerCase().includes(s)) return false
    return true
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredLogs.value.length / PAGE_SIZE)))

const pagedLogs = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filteredLogs.value.slice(start, start + PAGE_SIZE)
})

function formatDate(iso) {
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}
function formatTime(iso) {
  const d = new Date(iso)
  return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
function initials(name) {
  return (name || 'U').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
}
const AVATAR_COLORS = ['#0ea5e9','#8b5cf6','#14b8a6','#f59e0b','#ef4444','#22c55e','#ec4899','#f97316']
function avatarColor(name) {
  let hash = 0
  for (const c of (name || '')) hash = (hash * 31 + c.charCodeAt(0)) & 0xffffffff
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length]
}

function confirmClear() {
  showConfirm.value = true
}
function doClear() {
  clearAuditLogs()
  logs.value = []
  showConfirm.value = false
  page.value = 1
}
function exportCsv() {
  const headers = ['Timestamp', 'User', 'Action', 'Detail', 'Status']
  const rows = filteredLogs.value.map(l => [l.timestamp, l.user, l.action, l.detail || '', l.status])
  const csv = [headers, ...rows].map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 16px;
  flex-wrap: wrap;
}
.header-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
  margin-top: 4px;
}
.filters-card { margin-bottom: 16px; }
.filters-row {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex: 1;
  min-width: 140px;
}
.filter-group label {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}
.filter-input, .filter-select {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: rgba(15, 23, 42, 0.8);
  color: var(--text);
  font-size: 0.88rem;
  font-family: inherit;
}
.filter-input:focus, .filter-select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(14,165,233,0.15);
}
.filter-stats { display: flex; align-items: flex-end; padding-bottom: 2px; }
.stat-badge {
  font-size: 0.8rem;
  color: var(--text-muted);
  background: rgba(148,163,184,0.1);
  padding: 4px 10px;
  border-radius: 20px;
  border: 1px solid var(--border);
  white-space: nowrap;
}
.logs-card { padding: 0; overflow: hidden; }
.logs-table-wrap { overflow-x: auto; }
.logs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
.logs-table th {
  padding: 11px 14px;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
  background: rgba(15,23,42,0.5);
  white-space: nowrap;
}
.logs-table td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}
.logs-table tbody tr:last-child td { border-bottom: none; }
.logs-table tbody tr:hover { background: rgba(148,163,184,0.04); }
.row-error { background: rgba(239,68,68,0.03); }
.td-time { white-space: nowrap; }
.time-date { display: block; font-weight: 500; color: var(--text); font-size: 0.82rem; }
.time-clock { display: block; color: var(--text-muted); font-size: 0.78rem; font-family: monospace; }
.td-user { white-space: nowrap; }
.user-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
  vertical-align: middle;
  margin-right: 7px;
  flex-shrink: 0;
}
.user-name { vertical-align: middle; font-weight: 500; color: var(--text); }
.td-action { white-space: nowrap; }
.action-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 6px;
  background: rgba(14,165,233,0.12);
  color: #7dd3fc;
  font-size: 0.8rem;
  font-weight: 600;
}
.td-detail { color: var(--text-muted); font-size: 0.82rem; max-width: 280px; word-break: break-word; }
.status-pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.status-success { background: rgba(34,197,94,0.15); color: #86efac; }
.status-error { background: rgba(239,68,68,0.15); color: #fca5a5; }
.status-info { background: rgba(148,163,184,0.15); color: #cbd5e1; }
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 14px;
  border-top: 1px solid var(--border);
}
.page-btn {
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: rgba(148,163,184,0.1);
  color: var(--text);
  cursor: pointer;
  font-size: 0.85rem;
  font-family: inherit;
  transition: background 0.15s;
}
.page-btn:hover:not(:disabled) { background: rgba(148,163,184,0.2); }
.page-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.page-info { font-size: 0.85rem; color: var(--text-muted); }
.empty-card { text-align: center; }
.empty-state { padding: 40px 20px; display: flex; flex-direction: column; align-items: center; gap: 16px; }
.empty-state p { color: var(--text-muted); font-size: 0.9rem; max-width: 340px; }
.btn-danger {
  background: rgba(239,68,68,0.15);
  color: #fca5a5;
  border: 1px solid rgba(239,68,68,0.25);
}
.btn-danger:hover:not(:disabled) {
  background: rgba(239,68,68,0.25);
  color: #f87171;
}
.btn-danger:disabled { opacity: 0.4; cursor: not-allowed; }
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 28px 32px;
  max-width: 420px;
  width: 90%;
}
.modal h3 { margin: 0 0 10px; font-size: 1.1rem; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }

/* Light theme overrides */
:global(.theme-light) .filter-input,
:global(.theme-light) .filter-select {
  background: #fff;
  color: #0f172a;
  border-color: rgba(71,85,105,0.25);
}
:global(.theme-light) .logs-table th { background: rgba(241,245,249,0.8); }
:global(.theme-light) .action-tag { background: rgba(2,132,199,0.1); color: #0369a1; }
:global(.theme-light) .status-success { background: rgba(34,197,94,0.1); color: #15803d; }
:global(.theme-light) .status-error { background: rgba(239,68,68,0.1); color: #b91c1c; }
:global(.theme-light) .modal { background: #fff; }
</style>
