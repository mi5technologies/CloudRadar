<template>
  <div>
    <h1>List assets</h1>
    <p class="muted">Get a catalog of all discovered cloud resources (EC2, S3, RDS, Lambda, IAM, etc.) from your last scan or a specific snapshot.</p>
    <div class="card card-what">
      <h3>What this script does</h3>
      <p>Lists all assets in your asset catalog. You can export as <strong>JSON</strong>, <strong>CSV</strong>, or <strong>PDF</strong>. Optionally use a saved <strong>Snapshot ID</strong> to list assets from a previous scan. If no snapshot is given, it uses the latest scan data (or runs a scan if none exists). Use this when you only need the asset list without running full security rules or compliance checks.</p>
    </div>
    <div class="card" style="max-width: 520px;">
      <div class="input-group">
        <label>Output format</label>
        <select v-model="output">
          <option value="json">JSON</option>
          <option value="csv">CSV (spreadsheet)</option>
          <option value="pdf">PDF (print / save)</option>
        </select>
      </div>
      <div v-if="output === 'pdf'" class="output-hint">
        <span>ℹ</span> The asset list will open in a new tab — use your browser's <strong>Print → Save as PDF</strong> to save it.
      </div>
      <div class="input-group">
        <label>Snapshot ID (optional)</label>
        <input v-model="snapshotId" placeholder="Leave empty for latest scan" />
      </div>
      <button class="btn btn-primary" :disabled="loading" @click="run">Run list assets</button>
      <RunProgress :running="loading" message="Listing assets…" />
      <p v-if="error" class="muted" style="color: var(--error); margin-top: 8px;">{{ error }}</p>
    </div>
    <div v-if="result && output !== 'pdf'" class="card">
      <h2>Result</h2>
      <pre>{{ typeof result === 'string' ? result.slice(0, 4000) : JSON.stringify(result, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'
import RunProgress from '../components/RunProgress.vue'
import { openPrintWindow } from '../utils/pdf'

const output = ref('json')
const snapshotId = ref('')
const loading = ref(false)
const error = ref('')
const result = ref(null)

async function run() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const reqOutput = output.value === 'pdf' ? 'json' : output.value
    const data = await api.exportAssets({
      output: reqOutput,
      snapshot_id: snapshotId.value.trim() || null,
    })
    if (output.value === 'pdf') {
      const json = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
      const html = buildAssetPdfHtml(json)
      openPrintWindow(html, 'Asset Catalog')
    } else {
      result.value = data
    }
  } catch (e) {
    error.value = e.message || 'Failed'
  } finally {
    loading.value = false
  }
}

function buildAssetPdfHtml(jsonStr) {
  let assets = []
  try { assets = JSON.parse(jsonStr) } catch (_) { assets = [] }
  const rows = Array.isArray(assets)
    ? assets.map(a => `<tr><td>${a.resource_type || ''}</td><td>${a.resource_id || ''}</td><td>${a.region || ''}</td><td>${a.risk_score ?? ''}</td></tr>`).join('')
    : `<tr><td colspan="4"><pre style="font-size:12px;">${jsonStr.slice(0, 8000)}</pre></td></tr>`
  return `<!DOCTYPE html><html><head><title>Asset Catalog</title><style>
    body{font-family:sans-serif;font-size:13px;color:#111;padding:24px;}
    h1{font-size:20px;margin-bottom:16px;}
    table{width:100%;border-collapse:collapse;font-size:12px;}
    th{background:#f1f5f9;padding:8px 10px;text-align:left;border-bottom:2px solid #cbd5e1;}
    td{padding:7px 10px;border-bottom:1px solid #e2e8f0;vertical-align:top;}
    tr:nth-child(even){background:#f8fafc;}
    @media print{body{padding:0;}}
  </style></head><body>
    <h1>Asset Catalog</h1>
    <table><thead><tr><th>Type</th><th>Resource ID</th><th>Region</th><th>Risk Score</th></tr></thead>
    <tbody>${rows}</tbody></table>
  </body></html>`
}
</script>

<style scoped>
.output-hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.82rem;
  color: var(--text-muted);
  background: rgba(14,165,233,0.07);
  border: 1px solid rgba(14,165,233,0.18);
  border-radius: 7px;
  padding: 8px 12px;
  margin-bottom: 14px;
  line-height: 1.5;
}
.output-hint span { flex-shrink: 0; color: var(--accent); font-weight: 700; }
</style>
