const BASE = '/api'

async function request(path, options = {}) {
  const url = path.startsWith('http') ? path : `${BASE}${path}`
  const headers = { ...options.headers }
  if (options.body != null && typeof options.body === 'string') {
    headers['Content-Type'] = 'application/json'
  }
  const res = await fetch(url, { ...options, headers })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) return res.json()
  return res.text()
}

export default {
  async getHealth() {
    return request('/health')
  },

  async getStatus() {
    return request('/status')
  },

  async getSummary() {
    return request('/summary')
  },

  async getFindings() {
    return request('/findings')
  },

  async setupAws(body) {
    return request('/setup/aws', { method: 'POST', body: JSON.stringify(body) })
  },

  async setupGcp(body) {
    return request('/setup/gcp', { method: 'POST', body: JSON.stringify(body) })
  },

  async setupAzure(body) {
    return request('/setup/azure', { method: 'POST', body: JSON.stringify(body) })
  },

  async startScan(params = {}) {
    return request('/jobs/scan', {
      method: 'POST',
      body: JSON.stringify({
        cloud: params.cloud || 'aws',
        region: params.region || null,
        only: params.only || null,
        save_snapshot: params.save_snapshot !== false,
      }),
    })
  },

  async getJob(jobId) {
    return request(`/jobs/${jobId}`)
  },

  subscribeScanProgress(jobId, onEvent) {
    const base = window.location.origin
    const url = `${base}${BASE}/jobs/${jobId}/events`
    const es = new EventSource(url)
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        onEvent(data)
        if (data.type === 'done' || data.type === 'close') es.close()
      } catch (err) {
        onEvent({ type: 'error', error: String(err) })
      }
    }
    es.onerror = () => {
      es.close()
      onEvent({ type: 'close' })
    }
    return () => es.close()
  },

  async runVulnerabilities(region = 'us-east-1', checks = []) {
    return request('/vulnerabilities', { method: 'POST', body: JSON.stringify({ region, checks }) })
  },

  async listSnapshots() {
    return request('/audit/snapshots')
  },

  async exportAssets(params) {
    return request('/audit/assets', { method: 'POST', body: JSON.stringify(params) })
  },

  async runChanges(output = 'json') {
    return request('/audit/changes', { method: 'POST', body: JSON.stringify({ output }) })
  },

  async runDiff(before, after) {
    return request('/audit/diff', { method: 'POST', body: JSON.stringify({ snapshot_before: before, snapshot_after: after }) })
  },

  async runCompliance(framework = 'cis', output = 'json') {
    return request('/compliance', { method: 'POST', body: JSON.stringify({ framework, output }) })
  },

  async runGovernance(output = 'json', checks = []) {
    return request('/governance', { method: 'POST', body: JSON.stringify({ output, checks }) })
  },

  async runPentest(options = {}) {
    return request('/pentest', { method: 'POST', body: JSON.stringify(options) })
  },

  async getAttackPaths() {
    return request('/attack-paths')
  },

  async runAttackPaths(options = {}) {
    return request('/attack-paths/run', { method: 'POST', body: JSON.stringify(options) })
  },

  async remediate(finding, dry_run, region) {
    return request('/remediate', { method: 'POST', body: JSON.stringify({ finding, dry_run, region }) })
  },

  async getSchedulerJobs() {
    return request('/scheduler/jobs')
  },

  async addSchedulerJob(cloud, region, cron_expr) {
    return request('/scheduler/jobs', { method: 'POST', body: JSON.stringify({ cloud, region, cron_expr }) })
  },

  async deleteSchedulerJob(job_id) {
    return request(`/scheduler/jobs/${job_id}`, { method: 'DELETE' })
  },

  async getNotificationsConfig() {
    return request('/notifications/config')
  },

  async saveNotificationsConfig(config) {
    return request('/notifications/config', { method: 'POST', body: JSON.stringify(config) })
  },

  async getScanRegions(cloud) {
    return request('/scan/regions', { method: 'POST', body: JSON.stringify({ cloud }) })
  },

  // ---------- Tests (independent of scans) ----------

  async listTests() {
    return request('/tests/list')
  },

  async startTests(testFiles = []) {
    return request('/tests/run', {
      method: 'POST',
      body: JSON.stringify({ test_files: testFiles }),
    })
  },

  async getTestJob(jobId) {
    return request(`/tests/${jobId}`)
  },

  subscribeTestProgress(jobId, onEvent) {
    const base = window.location.origin
    const url = `${base}${BASE}/tests/${jobId}/events`
    const es = new EventSource(url)
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        onEvent(data)
        if (data.type === 'done' || data.type === 'close') es.close()
      } catch (err) {
        onEvent({ type: 'error', error: String(err) })
      }
    }
    es.onerror = () => {
      es.close()
      onEvent({ type: 'close' })
    }
    return () => es.close()
  },
}
