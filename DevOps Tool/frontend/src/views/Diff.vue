<template>
  <div>
    <h1>Snapshot diff</h1>
    <p class="muted">Compare two saved snapshots by ID. See differences between two points in time.</p>
    <div class="card card-what">
      <h3>What this script does</h3>
      <p>Compares <strong>two snapshots</strong> (before and after) by their snapshot IDs. Shows what changed between those two saved states—new, removed, and modified resources and findings. Use this when you only need a diff between two historical snapshots without running a new scan or compliance.</p>
    </div>
    <div class="card" style="max-width: 480px;">
      <div class="input-group">
        <label>Snapshot before</label>
        <input v-model="before" placeholder="Snapshot ID" list="snapshots" />
      </div>
      <div class="input-group">
        <label>Snapshot after</label>
        <input v-model="after" placeholder="Snapshot ID" list="snapshots" />
      </div>
      <datalist id="snapshots">
        <option v-for="s in snapshots" :key="s" :value="s" />
      </datalist>
      <button class="btn btn-primary" :disabled="loading" @click="run">Run snapshot diff</button>
      <RunProgress :running="loading" message="Comparing snapshots…" />
      <p v-if="error" class="muted" style="color: var(--error); margin-top: 8px;">{{ error }}</p>
    </div>
    <div v-if="result" class="card">
      <h2>Result</h2>
      <pre>{{ typeof result === 'string' ? result.slice(0, 4000) : JSON.stringify(result, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import RunProgress from '../components/RunProgress.vue'

const before = ref('')
const after = ref('')
const snapshots = ref([])
const loading = ref(false)
const error = ref('')
const result = ref(null)

onMounted(async () => {
  try {
    snapshots.value = await api.listSnapshots()
  } catch {
    snapshots.value = []
  }
})

async function run() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await api.runDiff(before.value.trim(), after.value.trim())
  } catch (e) {
    error.value = e.message || 'Failed'
  } finally {
    loading.value = false
  }
}
</script>
