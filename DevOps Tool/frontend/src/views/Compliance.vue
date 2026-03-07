<template>
  <div>
    <h1>Compliance report</h1>
    <p class="muted">Check if your cloud config meets a compliance framework. Maps findings to framework controls and reports pass/fail per control.</p>
    <div class="card card-what">
      <h3>What this script does</h3>
      <p>Runs a <strong>compliance report</strong> against your current findings. It maps security findings to controls for the selected framework and reports pass/fail — for example: whether API Gateway has a WAF, whether encryption is enabled, whether audit logging is active. Supports <strong>CIS, SOC2, HIPAA, PCI DSS, and ISO 27001</strong>. Uses the latest scan data (or runs a scan if needed).</p>
    </div>
    <div class="card" style="max-width: 520px;">
      <div class="input-group">
        <label>Framework</label>
        <select v-model="framework">
          <option value="cis">CIS AWS Foundations</option>
          <option value="soc2">SOC 2</option>
          <option value="hipaa">HIPAA</option>
          <option value="pci">PCI DSS</option>
          <option value="iso27001">ISO/IEC 27001:2022</option>
        </select>
      </div>
      <div class="input-group">
        <label>Output format</label>
        <select v-model="output">
          <option value="json">JSON</option>
          <option value="html">HTML (view in browser)</option>
          <option value="pdf">PDF (print / save)</option>
        </select>
      </div>
      <div v-if="output === 'pdf'" class="output-hint">
        <span>ℹ</span> The report will open in a new tab — use your browser's <strong>Print → Save as PDF</strong> to save it.
      </div>
      <button class="btn btn-primary" :disabled="loading" @click="run">Run compliance check</button>
      <RunProgress :running="loading" message="Running compliance check (may run scan first)…" />
      <p v-if="error" class="muted" style="color: var(--error); margin-top: 8px;">{{ error }}</p>
    </div>
    <div v-if="result && output === 'json'" class="card">
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

const framework = ref('cis')
const output = ref('json')
const loading = ref(false)
const error = ref('')
const result = ref(null)

async function run() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const reqOutput = output.value === 'pdf' ? 'html' : output.value
    const data = await api.runCompliance(framework.value, reqOutput)
    if (output.value === 'pdf' || output.value === 'html') {
      const html = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
      openPrintWindow(html, `Compliance Report — ${framework.value.toUpperCase()}`)
    } else {
      result.value = data
    }
  } catch (e) {
    error.value = e.message || 'Failed'
  } finally {
    loading.value = false
  }
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
