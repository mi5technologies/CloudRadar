<template>
  <div class="tests-page">
    <h1>Tests</h1>
    <p class="muted">
      Run the built-in unit and integration tests to validate CloudRadar's scanning rules,
      compliance mappings, and remediation logic. Tests are completely independent of any
      cloud scan and only run when you click <strong>Run Tests</strong>.
    </p>

    <!-- Test selector -->
    <div class="card">
      <div class="card-head">
        <h2>Select tests to run</h2>
        <div class="selector-actions">
          <button class="btn btn-secondary btn-sm" @click="selectAll">All</button>
          <button class="btn btn-secondary btn-sm" @click="selectNone">None</button>
        </div>
      </div>

      <div v-if="loadingList" class="muted">Loading test list…</div>
      <div v-else class="test-list">
        <label
          v-for="t in availableTests"
          :key="t.module"
          class="test-item"
          :class="{ 'test-disabled': !t.exists }"
        >
          <input
            type="checkbox"
            :value="t.module"
            v-model="selected"
            :disabled="!t.exists || running"
          />
          <div class="test-info">
            <span class="test-name">{{ t.display_name }}</span>
            <span class="test-desc">{{ t.description }}</span>
          </div>
          <span v-if="!t.exists" class="test-missing">file missing</span>
        </label>
      </div>

      <div class="run-bar">
        <button
          class="btn btn-run"
          :disabled="running"
          @click="runTests"
        >
          <span v-if="running" class="btn-spinner"></span>
          <span v-else>▶</span>
          {{ running ? 'Running tests…' : 'Run Tests' }}
        </button>
        <span v-if="running" class="run-hint">Tests are isolated — scans continue unaffected</span>
      </div>
    </div>

    <!-- Live output terminal -->
    <div v-if="jobId || lines.length" class="card card-terminal">
      <div class="terminal-head">
        <span class="terminal-title">
          <span class="dot dot-green"></span> Test Output
        </span>
        <div class="terminal-badges" v-if="summary">
          <span class="badge badge-pass">✓ {{ summary.passed }} passed</span>
          <span class="badge badge-fail" v-if="summary.failed > 0">✗ {{ summary.failed }} failed</span>
          <span class="badge badge-error" v-if="summary.errors > 0">⚠ {{ summary.errors }} errors</span>
          <span class="badge badge-skip" v-if="summary.skipped > 0">– {{ summary.skipped }} skipped</span>
        </div>
        <button class="btn btn-secondary btn-sm" @click="clearOutput">Clear</button>
      </div>

      <div class="terminal-body" ref="terminalEl">
        <div
          v-for="(line, i) in lines"
          :key="i"
          class="terminal-line"
          :class="lineClass(line)"
        >
          <span v-if="line.type === 'test'" class="line-icon">
            <span v-if="line.status === 'passed'" class="icon-pass">✓</span>
            <span v-else-if="line.status === 'failed'" class="icon-fail">✗</span>
            <span v-else-if="line.status === 'error'" class="icon-error">⚠</span>
            <span v-else class="icon-skip">–</span>
          </span>
          <span v-else class="line-icon line-icon-plain"> </span>
          <span class="line-text">{{ line.raw }}</span>
        </div>
        <div v-if="running" class="terminal-cursor">█</div>
      </div>
    </div>

    <!-- Final result banner -->
    <div v-if="done" class="result-banner" :class="allPassed ? 'banner-pass' : 'banner-fail'">
      <span class="banner-icon">{{ allPassed ? '✓' : '✗' }}</span>
      <span v-if="allPassed">All {{ summary.passed }} tests passed.</span>
      <span v-else>
        {{ summary.failed + summary.errors }} test(s) failed out of {{ summary.total }}.
        Check the output above for details.
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import api from '../api'

// Hardcoded fallback — always shown even if backend is unreachable
const FALLBACK_TESTS = [
  { module: 'test_rule_engine',  display_name: 'Rule Engine',           description: 'Validates security rules fire correctly (e.g. open S3 bucket, public RDS, missing encryption) and that severity/finding fields are accurate.', exists: true },
  { module: 'test_s3_scanner',   display_name: 'S3 Scanner',            description: 'Tests S3 bucket scanner: public-access-block disabled, missing encryption, bucket policy exposure, and correct finding generation.', exists: true },
  { module: 'test_compliance',   display_name: 'Compliance Frameworks', description: 'Verifies all 5 compliance frameworks (CIS, SOC2, HIPAA, PCI DSS, ISO 27001) map findings to controls correctly and produce pass/fail reports.', exists: true },
  { module: 'test_remediation',  display_name: 'Remediation Engine',    description: 'Checks that auto-remediation actions (enable S3 encryption, enable EBS encryption, etc.) are generated correctly for each finding type.', exists: true },
  { module: 'test_attack_paths', display_name: 'Attack Paths',          description: 'Validates attack path graph construction: public EC2 → open security group → sensitive RDS chains are detected and scored.', exists: true },
  { module: 'test_scanners',     display_name: 'All Scanners',          description: 'Integration tests for EC2, RDS, IAM, Lambda, CloudTrail, VPC, EBS, EKS, ECS, KMS, API Gateway, SQS, DynamoDB, GuardDuty, and CloudWatch scanners.', exists: true },
]

const availableTests = ref(FALLBACK_TESTS)
const loadingList = ref(false)
// Pre-select ALL by default
const selected = ref(FALLBACK_TESTS.map(t => t.module))
const running = ref(false)
const done = ref(false)
const jobId = ref(null)
const lines = ref([])
const summary = ref(null)
const terminalEl = ref(null)

let unsubscribe = null
let pollTimer = null

const allPassed = computed(
  () => summary.value && summary.value.failed === 0 && summary.value.errors === 0
)

async function fetchList() {
  loadingList.value = true
  try {
    const data = await api.listTests()
    const tests = data.tests || []
    if (tests.length > 0) {
      availableTests.value = tests
      // Pre-select all existing files returned by backend
      selected.value = tests.filter(t => t.exists).map(t => t.module)
    }
    // If backend returns empty, keep the hardcoded fallback
  } catch {
    // Backend unreachable — keep FALLBACK_TESTS and all selected
  } finally {
    loadingList.value = false
  }
}

function selectAll() {
  selected.value = availableTests.value.filter(t => t.exists).map(t => t.module)
}
function selectNone() {
  selected.value = []
}

function clearOutput() {
  lines.value = []
  summary.value = null
  done.value = false
  jobId.value = null
}

function lineClass(line) {
  if (line.type !== 'test') return 'line-output'
  return {
    'line-passed': line.status === 'passed',
    'line-failed': line.status === 'failed',
    'line-error': line.status === 'error',
    'line-skipped': line.status === 'skipped',
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (terminalEl.value) {
      terminalEl.value.scrollTop = terminalEl.value.scrollHeight
    }
  })
}

function handleEvent(event) {
  if (event.type === 'output' || event.type === 'test') {
    lines.value = [...lines.value, event]
    scrollToBottom()
  } else if (event.type === 'done') {
    done.value = true
    running.value = false
    summary.value = event.summary || summary.value
    lines.value = [...lines.value, {
      type: 'output',
      raw: event.success
        ? `\n✓ All tests passed.`
        : `\n✗ Tests finished with failures.`,
    }]
    scrollToBottom()
    clearPoll()
  } else if (event.type === 'close') {
    running.value = false
    clearPoll()
  }
}

function clearPoll() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  if (unsubscribe) { unsubscribe(); unsubscribe = null }
}

async function startPolling(jId) {
  pollTimer = setInterval(async () => {
    try {
      const job = await api.getTestJob(jId)
      if (job.lines) {
        lines.value = job.lines
        scrollToBottom()
      }
      if (job.status !== 'running') {
        summary.value = job.summary
        done.value = true
        running.value = false
        clearPoll()
      }
    } catch { clearPoll() }
  }, 1500)
}

async function runTests() {
  clearPoll()
  lines.value = []
  summary.value = null
  done.value = false
  running.value = true

  // If nothing checked, run all available tests
  const toRun = selected.value.length > 0
    ? selected.value
    : availableTests.value.filter(t => t.exists).map(t => t.module)

  try {
    const resp = await api.startTests(toRun)
    jobId.value = resp.job_id

    // Small delay to let the job queue initialise
    await new Promise(r => setTimeout(r, 120))

    // Subscribe to SSE stream
    unsubscribe = api.subscribeTestProgress(resp.job_id, handleEvent)

    // Polling fallback in case SSE is buffered by a proxy
    startPolling(resp.job_id)
  } catch (e) {
    lines.value = [{ type: 'output', raw: `Error starting tests: ${e.message}` }]
    running.value = false
  }
}

onMounted(fetchList)

// Auto-scroll whenever lines change
watch(lines, scrollToBottom)
</script>

<style scoped>
.tests-page {
  max-width: 900px;
}

/* ---- selector card ---- */
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.selector-actions {
  display: flex;
  gap: 6px;
}
.btn-sm {
  font-size: 0.78rem;
  padding: 4px 10px;
}

.test-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}
.test-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}
.test-item input[type="checkbox"] {
  margin-top: 3px;
  flex-shrink: 0;
}
.test-item:hover {
  background: rgba(14,165,233,0.07);
}
.test-disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.test-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}
.test-name {
  font-weight: 600;
  color: var(--text);
}
.test-desc {
  font-size: 0.82rem;
  color: var(--text-muted);
  flex: 1;
  line-height: 1.4;
}
.test-missing {
  font-size: 0.75rem;
  color: #f87171;
  margin-left: auto;
  background: rgba(248,113,113,0.12);
  padding: 2px 8px;
  border-radius: 4px;
}

/* ---- run bar ---- */
.run-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-top: 4px;
}
.btn-run {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: linear-gradient(135deg, #0ea5e9, #6366f1);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-run:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.btn-run:not(:disabled):hover {
  opacity: 0.88;
}
.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.run-hint {
  font-size: 0.8rem;
  color: var(--text-muted);
}

/* ---- terminal ---- */
.card-terminal {
  padding: 0;
  overflow: hidden;
}
.terminal-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: rgba(0,0,0,0.25);
  border-bottom: 1px solid var(--border);
}
.terminal-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot { width: 10px; height: 10px; border-radius: 50%; }
.dot-green { background: #22c55e; }
.terminal-badges {
  display: flex;
  gap: 6px;
  flex: 1;
  flex-wrap: wrap;
}
.badge {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}
.badge-pass { background: rgba(34,197,94,0.15); color: #22c55e; }
.badge-fail { background: rgba(239,68,68,0.15); color: #ef4444; }
.badge-error { background: rgba(249,115,22,0.15); color: #f97316; }
.badge-skip { background: rgba(156,163,175,0.15); color: #9ca3af; }

.terminal-body {
  background: #0a0e17;
  color: #d4d4d4;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 0.8rem;
  line-height: 1.55;
  padding: 14px 16px;
  min-height: 260px;
  max-height: 520px;
  overflow-y: auto;
}
.terminal-cursor {
  display: inline-block;
  animation: blink 1s step-end infinite;
  color: #6366f1;
}
@keyframes blink { 50% { opacity: 0; } }

.terminal-line {
  display: flex;
  gap: 8px;
  padding: 1px 0;
}
.line-icon {
  width: 18px;
  flex-shrink: 0;
  text-align: center;
}
.line-icon-plain { color: transparent; }
.icon-pass { color: #22c55e; }
.icon-fail { color: #ef4444; }
.icon-error { color: #f97316; }
.icon-skip { color: #6b7280; }

.line-passed .line-text { color: #86efac; }
.line-failed .line-text { color: #fca5a5; }
.line-error .line-text { color: #fdba74; }
.line-skipped .line-text { color: #6b7280; }
.line-output .line-text { color: #d4d4d4; }

/* ---- result banner ---- */
.result-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  margin-top: 8px;
}
.banner-pass {
  background: rgba(34,197,94,0.12);
  border: 1px solid rgba(34,197,94,0.3);
  color: #4ade80;
}
.banner-fail {
  background: rgba(239,68,68,0.10);
  border: 1px solid rgba(239,68,68,0.3);
  color: #f87171;
}
.banner-icon {
  font-size: 1.3rem;
}

/* light theme overrides */
.theme-light .terminal-body {
  background: #1e1e2e;
  color: #cdd6f4;
}
.theme-light .terminal-head {
  background: rgba(0,0,0,0.08);
}
.theme-light .test-item {
  background: rgba(0,0,0,0.03);
}
</style>
