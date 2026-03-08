<template>
  <div>
    <h1>Notifications</h1>
    <p class="muted">Configure alerts for critical findings and scan completions.</p>

    <div v-if="loadError" class="card" style="border-left: 4px solid var(--error);">
      <p class="muted" style="color: var(--error); margin: 0;">Failed to load config: {{ loadError }}</p>
    </div>

    <form class="card" @submit.prevent="save" style="max-width: 560px;">
      <div v-if="loadingConfig" class="muted" style="padding: 8px 0;">Loading config…</div>

      <div class="form-section">
        <h3 class="form-section-title">
          <span>💬</span> Slack
        </h3>
        <div class="form-group">
          <label for="slack_webhook">Webhook URL</label>
          <input id="slack_webhook" v-model="form.slack_webhook_url" type="url" placeholder="https://hooks.slack.com/services/…" />
        </div>
      </div>

      <div class="form-section">
        <h3 class="form-section-title">
          <span>✉️</span> Email (SMTP)
        </h3>
        <div class="form-row">
          <div class="form-group form-group-grow">
            <label for="smtp_host">SMTP Host</label>
            <input id="smtp_host" v-model="form.smtp_host" type="text" placeholder="smtp.example.com" />
          </div>
          <div class="form-group form-group-fixed">
            <label for="smtp_port">Port</label>
            <input id="smtp_port" v-model.number="form.smtp_port" type="number" min="1" max="65535" placeholder="587" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group form-group-grow">
            <label for="smtp_user">Username</label>
            <input id="smtp_user" v-model="form.smtp_username" type="text" placeholder="user@example.com" />
          </div>
          <div class="form-group form-group-grow">
            <label for="smtp_pass">Password</label>
            <input id="smtp_pass" v-model="form.smtp_password" type="password" placeholder="••••••••" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group form-group-grow">
            <label for="from_email">From</label>
            <input id="from_email" v-model="form.from_email" type="email" placeholder="alerts@example.com" />
          </div>
          <div class="form-group form-group-grow">
            <label for="to_email">To</label>
            <input id="to_email" v-model="form.to_email" type="email" placeholder="team@example.com" />
          </div>
        </div>
      </div>

      <div class="form-section form-section-last">
        <h3 class="form-section-title">
          <span>⚙️</span> Threshold
        </h3>
        <div class="form-group">
          <label for="min_severity">Minimum severity to alert</label>
          <select id="min_severity" v-model="form.min_severity">
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn btn-primary" :disabled="saving">
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
        <button type="button" class="btn btn-secondary" :disabled="saving || testSending" @click="sendTest">
          {{ testSending ? 'Sending…' : 'Send test alert' }}
        </button>
      </div>

      <div v-if="saveMsg" class="inline-msg" :class="saveMsg.type === 'success' ? 'msg-success' : 'msg-error'">
        {{ saveMsg.text }}
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const loadingConfig = ref(false)
const loadError = ref('')
const saving = ref(false)
const testSending = ref(false)
const saveMsg = ref(null)

const form = ref({
  slack_webhook_url: '',
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  from_email: '',
  to_email: '',
  min_severity: 'high',
})

function showMsg(type, text, durationMs = 4000) {
  saveMsg.value = { type, text }
  setTimeout(() => { saveMsg.value = null }, durationMs)
}

async function save() {
  saving.value = true
  saveMsg.value = null
  try {
    await api.saveNotificationsConfig({ ...form.value })
    showMsg('success', 'Configuration saved successfully.')
  } catch (e) {
    showMsg('error', e.message || 'Failed to save configuration.')
  } finally {
    saving.value = false
  }
}

async function sendTest() {
  testSending.value = true
  saveMsg.value = null
  try {
    await api.saveNotificationsConfig({ ...form.value })
    showMsg('success', 'Test alert sent (config saved).')
  } catch (e) {
    showMsg('error', e.message || 'Failed to send test alert.')
  } finally {
    testSending.value = false
  }
}

onMounted(async () => {
  loadingConfig.value = true
  loadError.value = ''
  try {
    const data = await api.getNotificationsConfig()
    if (data && typeof data === 'object') {
      Object.assign(form.value, data)
      if (!form.value.smtp_port) form.value.smtp_port = 587
      if (!form.value.min_severity) form.value.min_severity = 'high'
    }
  } catch (e) {
    loadError.value = e.message || 'Unknown error'
  } finally {
    loadingConfig.value = false
  }
})
</script>

<style scoped>
.form-section {
  padding-bottom: 20px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border);
}
.form-section-last {
  border-bottom: none;
  padding-bottom: 0;
  margin-bottom: 20px;
}
.form-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0 0 14px;
  color: var(--text);
}
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
.form-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.form-group-grow { flex: 1; min-width: 140px; }
.form-group-fixed { flex: 0 0 90px; }
.form-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 4px;
}
.inline-msg {
  margin-top: 14px;
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
