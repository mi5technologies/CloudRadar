<template>
  <div>
    <h1>Changes</h1>
    <p class="muted">Compare current cloud state with the last saved snapshot. See what was added, removed, or modified.</p>
    <div class="card card-what">
      <h3>What this script does</h3>
      <p>Compares <strong>current state</strong> (from a fresh discovery) with the <strong>last saved snapshot</strong>. It reports new resources, removed resources, and changes to assets and findings. You must have run a scan with “Save snapshot” at least once before. Use this when you only want change detection without running compliance, governance, or a full scan.</p>
    </div>
    <div class="card" style="max-width: 480px;">
      <div class="input-group">
        <label>Output</label>
        <select v-model="output">
          <option value="json">JSON</option>
          <option value="html">HTML</option>
        </select>
      </div>
      <button class="btn btn-primary" :disabled="loading" @click="run">Run changes</button>
      <RunProgress :running="loading" message="Comparing current state with last snapshot…" />
      <p v-if="error" class="muted" style="color: var(--error); margin-top: 8px;">{{ error }}</p>
    </div>
    <div v-if="result" class="card">
      <h2>Result</h2>
      <pre>{{ typeof result === 'string' ? result.slice(0, 4000) : JSON.stringify(result, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'
import RunProgress from '../components/RunProgress.vue'

const output = ref('json')
const loading = ref(false)
const error = ref('')
const result = ref(null)

async function run() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await api.runChanges(output.value)
  } catch (e) {
    error.value = e.message || 'Failed'
  } finally {
    loading.value = false
  }
}
</script>
