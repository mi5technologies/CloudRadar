<template>
  <div>
    <h1>Scheduled Scans</h1>

    <div class="card card-what">
      <h3>What this does</h3>
      <p>Schedule automatic cloud security scans using cron expressions. Jobs run on the server and save snapshots automatically. You can add, view, and remove schedules at any time.</p>
    </div>

    <div class="card" style="max-width: 560px;">
      <h2>Add Schedule</h2>
      <div class="add-form">
        <div class="form-row">
          <div class="form-group form-group-fixed">
            <label for="sched_cloud">Cloud</label>
            <select id="sched_cloud" v-model="newJob.cloud">
              <option value="aws">AWS</option>
              <option value="gcp">GCP</option>
              <option value="azure">Azure</option>
            </select>
          </div>
          <div class="form-group form-group-grow">
            <label for="sched_region">Region</label>
            <input id="sched_region" v-model="newJob.region" type="text" placeholder="us-east-1" />
          </div>
        </div>
        <div class="form-group">
          <label for="sched_cron">
            Cron expression
            <span class="cron-hint muted">— Standard cron: minute hour day month weekday</span>
          </label>
          <input id="sched_cron" v-model="newJob.cron_expr" type="text" placeholder="0 2 * * *" />
        </div>
        <button class="btn btn-primary" :disabled="adding || !newJob.cron_expr" @click="addJob">
          {{ adding ? 'Adding…' : 'Add' }}
        </button>
        <div v-if="addError" class="inline-msg msg-error">{{ addError }}</div>
        <div v-if="addSuccess" class="inline-msg msg-success">Schedule added.</div>
      </div>
    </div>

    <div class="card">
      <div class="card-head">
        <h2>Schedules ({{ jobs.length }})</h2>
        <button class="btn btn-secondary" @click="loadJobs" :disabled="loading">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" aria-hidden="true"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
          Refresh
        </button>
      </div>
      <div v-if="loading" class="loading-row">
        <span class="spinner" aria-label="Loading"></span>
        <span class="muted">Loading schedules…</span>
      </div>
      <div v-else-if="loadError" class="muted" style="color: var(--error);">{{ loadError }}</div>
      <div v-else-if="!jobs.length" class="muted empty-state">No scheduled scans. Add one above.</div>
      <div v-else class="table-wrap">
        <table class="sched-table">
          <thead>
            <tr>
              <th>Cloud</th>
              <th>Region</th>
              <th>Cron</th>
              <th>Status</th>
              <th>Last run</th>
              <th>Next run</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="job in jobs" :key="job.id">
              <td><span class="cloud-badge">{{ job.cloud?.toUpperCase() || '—' }}</span></td>
              <td>{{ job.region || '—' }}</td>
              <td><code>{{ job.cron_expr || '—' }}</code></td>
              <td>
                <span class="status-badge" :class="job.enabled === false ? 'status-disabled' : 'status-enabled'">
                  {{ job.enabled === false ? 'disabled' : 'enabled' }}
                </span>
              </td>
              <td class="muted">{{ job.last_run ? formatDate(job.last_run) : '—' }}</td>
              <td class="muted">{{ job.next_run ? formatDate(job.next_run) : '—' }}</td>
              <td>
                <button class="btn btn-danger-sm" :disabled="deletingId === job.id" @click="deleteJob(job.id)">
                  {{ deletingId === job.id ? '…' : 'Delete' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const jobs = ref([])
const loading = ref(false)
const loadError = ref('')
const adding = ref(false)
const addError = ref('')
const addSuccess = ref(false)
const deletingId = ref(null)

const newJob = ref({ cloud: 'aws', region: '', cron_expr: '' })

function formatDate(ts) {
  if (!ts) return '—'
  try { return new Date(ts).toLocaleString() } catch { return ts }
}

async function loadJobs() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await api.getSchedulerJobs()
    jobs.value = Array.isArray(data) ? data : (data.jobs || [])
  } catch (e) {
    loadError.value = e.message || 'Failed to load jobs.'
    jobs.value = []
  } finally {
    loading.value = false
  }
}

async function addJob() {
  if (!newJob.value.cron_expr) return
  adding.value = true
  addError.value = ''
  addSuccess.value = false
  try {
    await api.addSchedulerJob(newJob.value.cloud, newJob.value.region, newJob.value.cron_expr)
    addSuccess.value = true
    newJob.value = { cloud: 'aws', region: '', cron_expr: '' }
    setTimeout(() => { addSuccess.value = false }, 3000)
    await loadJobs()
  } catch (e) {
    addError.value = e.message || 'Failed to add schedule.'
  } finally {
    adding.value = false
  }
}

async function deleteJob(id) {
  deletingId.value = id
  try {
    await api.deleteSchedulerJob(id)
    await loadJobs()
  } catch (e) {
    loadError.value = e.message || 'Failed to delete job.'
  } finally {
    deletingId.value = null
  }
}

onMounted(loadJobs)
</script>

<style scoped>
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}
.card-head h2 { margin: 0; }
.add-form { display: flex; flex-direction: column; gap: 0; }

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}
.form-group label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-muted);
}
.form-group input,
.form-group select {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: rgba(15, 23, 42, 0.8);
  color: var(--text);
  font-size: 0.9rem;
  width: 100%;
}
.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2);
}
.form-row { display: flex; gap: 16px; flex-wrap: wrap; }
.form-group-grow { flex: 1; min-width: 120px; }
.form-group-fixed { flex: 0 0 100px; }
.cron-hint { font-size: 0.78rem; font-weight: 400; }

.loading-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
}
.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.empty-state { padding: 24px 0; text-align: center; }

.table-wrap { overflow-x: auto; margin-top: 4px; }
.sched-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}
.sched-table th,
.sched-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
.sched-table th {
  color: var(--text-muted);
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.cloud-badge {
  font-size: 0.78rem;
  font-weight: 700;
  background: rgba(14, 165, 233, 0.15);
  color: var(--accent);
  padding: 3px 7px;
  border-radius: 5px;
}
.status-badge {
  font-size: 0.78rem;
  font-weight: 600;
  padding: 3px 7px;
  border-radius: 5px;
}
.status-enabled {
  background: rgba(34, 197, 94, 0.15);
  color: var(--success);
}
.status-disabled {
  background: rgba(148, 163, 184, 0.15);
  color: var(--text-muted);
}

.btn-danger-sm {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  border: none;
  cursor: pointer;
  background: rgba(239, 68, 68, 0.12);
  color: #f87171;
  transition: background 0.15s;
}
.btn-danger-sm:hover { background: rgba(239, 68, 68, 0.22); }
.btn-danger-sm:disabled { opacity: 0.5; cursor: not-allowed; }

.inline-msg {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 500;
}
.msg-success {
  background: rgba(34, 197, 94, 0.12);
  color: var(--success);
  border: 1px solid rgba(34, 197, 94, 0.25);
}
.msg-error {
  background: rgba(239, 68, 68, 0.1);
  color: var(--error);
  border: 1px solid rgba(239, 68, 68, 0.2);
}
</style>
