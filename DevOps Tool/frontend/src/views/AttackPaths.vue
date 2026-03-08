<template>
  <div>
    <h1>Attack Paths</h1>
    <p class="muted">
      Discover chained security weaknesses — combinations of misconfigurations that an attacker
      could exploit in sequence to move through your infrastructure.
    </p>

    <!-- Explanation card -->
    <div class="card card-what">
      <h3>How attack path analysis works</h3>
      <p>
        An <strong>attack path</strong> is a series of connected security weaknesses that, when
        chained together, let an attacker escalate privileges, move laterally, or reach sensitive data.
        Each "hop" is a resource that is vulnerable or misconfigured. <strong>Fixing any single hop
        breaks the entire chain.</strong>
      </p>
      <p style="margin-top: 8px;">
        The analysis builds a <strong>directed graph</strong> of your cloud resources and their
        security relationships, then walks the graph to find exploitable chains. The risk score for
        each path is determined by the severity of its weakest link and the value of its target.
      </p>
      <p style="margin-top: 8px; color: var(--text-muted); font-size: 0.85rem;">
        <strong>Requires:</strong> at least one Security Scan to have been run first — attack path
        analysis operates on the findings from your latest scan.
      </p>
    </div>

    <!-- Script selector + Run -->
    <div class="card">
      <ScriptSelector
        title="Analysis modules"
        :scripts="analysisModules"
        v-model="selectedModules"
        :disabled="loading"
      />

      <div class="run-bar">
        <button
          class="btn btn-run"
          :disabled="loading || selectedModules.length === 0"
          @click="runAnalysis"
        >
          <span v-if="loading" class="btn-spinner"></span>
          <span v-else>▶</span>
          {{ loading ? 'Analysing…' : 'Run attack path analysis' }}
        </button>
        <button
          class="btn btn-secondary"
          style="margin-left: 4px;"
          :disabled="loading"
          @click="loadExisting"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="15" height="15"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
          Load last results
        </button>
        <span v-if="selectedModules.length === 0" class="run-hint warn">Select at least one module</span>
        <span v-else-if="!loading" class="run-hint">{{ selectedModules.length }} of {{ analysisModules.length }} modules selected</span>
      </div>
      <p v-if="runError" class="muted" style="color: var(--error); margin-top: 8px;">{{ runError }}</p>
    </div>

    <!-- Results -->
    <div v-if="hasResults" class="card">
      <div class="result-header">
        <h2>Detected paths ({{ paths.length }})</h2>
        <div class="result-meta" v-if="paths.length">
          <span class="badge-count badge-count-critical">{{ countBySev('critical') }} critical</span>
          <span class="badge-count badge-count-high">{{ countBySev('high') }} high</span>
          <span class="badge-count badge-count-medium">{{ countBySev('medium') }} medium</span>
        </div>
      </div>

      <div v-if="loading" class="loading-row">
        <span class="spinner"></span>
        <span class="muted">Running attack path analysis…</span>
      </div>
      <div v-else-if="!paths.length" class="muted empty-state">
        No attack paths detected. Either your environment is clean or run a Security Scan first.
      </div>
      <div v-else class="paths-list">
        <div
          v-for="(path, i) in paths"
          :key="i"
          class="attack-path-card"
          :class="'sev-border-' + (path.severity || 'medium')"
        >
          <div class="path-header">
            <span class="badge" :class="'badge-' + (path.severity || 'medium')">
              {{ path.severity || 'medium' }}
            </span>
            <span class="path-title">{{ path.description || 'Unnamed path' }}</span>
          </div>

          <!-- Chain hops -->
          <div v-if="path.hops && path.hops.length" class="path-chain">
            <template v-for="(hop, hi) in path.hops" :key="hi">
              <div class="path-hop">
                <span class="hop-type">{{ hop.resource_type || '?' }}</span>
                <span class="hop-id">{{ hop.resource_id || '?' }}</span>
                <span v-if="hop.issue" class="hop-issue">{{ hop.issue }}</span>
              </div>
              <span v-if="hi < path.hops.length - 1" class="path-arrow">→</span>
            </template>
          </div>

          <!-- Detail + remediation hint -->
          <div v-if="path.detail || path.remediation" class="path-footer">
            <p v-if="path.detail" class="path-detail">{{ path.detail }}</p>
            <p v-if="path.remediation" class="path-remediation">
              <strong>Fix:</strong> {{ path.remediation }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import ScriptSelector from '../components/ScriptSelector.vue'
import api from '../api'

const analysisModules = [
  {
    id: 'network_chains',
    name: 'Network Exposure Chains',
    description: 'Finds paths where a publicly accessible resource (EC2, ALB) connects through open security groups to sensitive backends (RDS, ElasticSearch, Redis). An attacker with access to the public resource can pivot to the database.',
  },
  {
    id: 'iam_escalation',
    name: 'IAM Privilege Escalation',
    description: 'Identifies IAM users or roles with wildcard actions or admin-policy attachments that could let an attacker escalate from a low-privilege account to full Administrator access.',
  },
  {
    id: 'data_exfiltration',
    name: 'Data Exfiltration Paths',
    description: 'Detects chains combining public S3 access, weak IAM policies, and unencrypted RDS/DynamoDB that an attacker could exploit to exfiltrate sensitive data without detection.',
  },
  {
    id: 'container_escape',
    name: 'Container Escape',
    description: 'Scans for privileged ECS containers or EKS pods that could allow a container breakout, giving an attacker access to the underlying EC2 host and from there to the entire VPC.',
  },
  {
    id: 'lateral_movement',
    name: 'Lateral Movement',
    description: 'Maps how an attacker could move between services using exposed ports, over-permissive security groups, and shared credentials — e.g. compromised Lambda → SQS → RDS chain.',
  },
]

const selectedModules = ref(analysisModules.map(m => m.id))
const paths = ref([])
const loading = ref(false)
const runError = ref('')
const hasResults = ref(false)

const countBySev = (sev) => paths.value.filter(p => (p.severity || 'medium') === sev).length

async function runAnalysis() {
  loading.value = true
  runError.value = ''
  hasResults.value = true
  paths.value = []
  try {
    const data = await api.runAttackPaths({ modules: selectedModules.value })
    paths.value = Array.isArray(data) ? data : (data.paths || [])
  } catch (e) {
    runError.value = e.message || 'Failed to run analysis. Make sure a Security Scan has been run first.'
  } finally {
    loading.value = false
  }
}

async function loadExisting() {
  loading.value = true
  runError.value = ''
  hasResults.value = true
  paths.value = []
  try {
    const data = await api.getAttackPaths()
    paths.value = Array.isArray(data) ? data : (data.paths || [])
  } catch (e) {
    runError.value = e.message || 'No previous results found. Run a Security Scan first, then click Run attack path analysis.'
  } finally {
    loading.value = false
  }
}

onMounted(loadExisting)
</script>

<style scoped>
/* Run bar */
.run-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  margin-top: 6px;
}
.btn-run {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 22px;
  background: linear-gradient(135deg, #0ea5e9, #6366f1);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-run:disabled { opacity: 0.45; cursor: not-allowed; }
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

/* Result header */
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}
.result-header h2 { margin: 0; }
.result-meta { display: flex; gap: 8px; flex-wrap: wrap; }
.badge-count {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
}
.badge-count-critical { background: rgba(239,68,68,0.15); color: #ef4444; }
.badge-count-high     { background: rgba(249,115,22,0.15); color: #f97316; }
.badge-count-medium   { background: rgba(234,179,8,0.15);  color: #ca8a04; }

/* Loading */
.loading-row { display: flex; align-items: center; gap: 12px; padding: 20px 0; }
.spinner {
  display: inline-block;
  width: 20px; height: 20px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.empty-state { padding: 32px 0; text-align: center; }

/* Path cards */
.paths-list { display: flex; flex-direction: column; gap: 16px; }
.path-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}
.path-title { font-size: 0.95rem; font-weight: 600; flex: 1; line-height: 1.4; }

.badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  white-space: nowrap;
  flex-shrink: 0;
  margin-top: 1px;
}
.badge-critical { background: var(--error);   color: #fff; }
.badge-high     { background: #f97316;         color: #fff; }
.badge-medium   { background: var(--running);  color: #1a1a1a; }
.badge-low      { background: var(--success);  color: #0f172a; }

/* Chain */
.path-chain {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 6px;
  margin: 4px 0 10px;
}
.path-hop {
  display: inline-flex;
  flex-direction: column;
  gap: 2px;
  background: rgba(148,163,184,0.1);
  border: 1px solid var(--border);
  border-radius: 7px;
  padding: 5px 10px;
  max-width: 180px;
}
.hop-type {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.hop-id {
  font-size: 0.78rem;
  font-family: monospace;
  color: var(--text);
  word-break: break-all;
}
.hop-issue {
  font-size: 0.72rem;
  color: #f97316;
  margin-top: 1px;
}
.path-arrow {
  color: var(--text-muted);
  font-size: 1.1rem;
  font-weight: 700;
  align-self: center;
  padding: 0 2px;
}

/* Footer */
.path-footer { margin-top: 6px; }
.path-detail {
  font-size: 0.83rem;
  color: var(--text-muted);
  margin: 0 0 4px;
  line-height: 1.4;
}
.path-remediation {
  font-size: 0.83rem;
  color: #4ade80;
  margin: 0;
  line-height: 1.4;
}
</style>
