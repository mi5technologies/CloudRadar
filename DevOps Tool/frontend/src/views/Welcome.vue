<template>
  <div class="welcome">
    <div class="welcome-inner">
      <img src="/cloudradar-logo.png" alt="CloudRadar" class="welcome-logo" />
      <h1 class="welcome-title">CloudRadar</h1>
      <p class="welcome-subtitle">Multi-Cloud Security Intelligence</p>
      <p class="welcome-instruction">Select your cloud provider to get started</p>
      <div class="cloud-grid">
        <button type="button" class="cloud-card" @click="select('aws')">
          <span class="cloud-logo cloud-logo-aws" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 11c0-2.2-1.8-4-4-4-.9 0-1.7.3-2.4.8C11.8 5.5 10.1 4 8 4 5.2 4 3 6.2 3 9c0 .4 0 .8.1 1.2C1.8 10.8 0 13.1 0 16c0 2.2 1.8 4 4 4h11c2.2 0 4-1.8 4-4 0-.4-.1-.8-.2-1.1.2-.7.2-1.4.2-2.1V11z" fill="#FF9900"/></svg>
          </span>
          <span class="cloud-name">Amazon Web Services</span>
          <span class="cloud-tag">AWS</span>
        </button>
        <button type="button" class="cloud-card" @click="select('gcp')">
          <span class="cloud-logo cloud-logo-gcp" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 4v6l4-2-4-4z" fill="#4285F4"/><path d="M18 8.5l-6 3v6l6-3v-6z" fill="#34A853"/><path d="M12 18.5v-6l-6 3 6 3z" fill="#FBBC05"/><path d="M6 11.5l6-3V2l-6 3v6.5z" fill="#EA4335"/></svg>
          </span>
          <span class="cloud-name">Google Cloud Platform</span>
          <span class="cloud-tag">GCP</span>
        </button>
        <button type="button" class="cloud-card" @click="select('azure')">
          <span class="cloud-logo cloud-logo-azure" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M11 4L3 20h4l2-5 4 5h4L13 4h-2zm-4 11l3-7 3 7H7z" fill="#0078D4"/></svg>
          </span>
          <span class="cloud-name">Microsoft Azure</span>
          <span class="cloud-tag">Azure</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function select(cloud) {
  try {
    localStorage.setItem('cspm_cloud', cloud)
  } catch (_) {}
  router.push({ path: '/setup', query: { cloud } })
}
</script>

<style scoped>
.welcome {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-body);
  padding: 24px;
}
.welcome-inner {
  text-align: center;
  max-width: 720px;
}
.welcome-logo {
  max-width: 280px;
  width: 100%;
  height: auto;
  margin-bottom: 16px;
  display: block;
  margin-left: auto;
  margin-right: auto;
}
.welcome-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 8px;
  color: var(--text);
}
.welcome-subtitle {
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--accent);
  margin: 0 0 4px;
}
.welcome-instruction {
  font-size: 1rem;
  color: var(--text-muted);
  margin: 0 0 40px;
}
.cloud-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
@media (max-width: 640px) {
  .cloud-grid {
    grid-template-columns: 1fr;
  }
}
.cloud-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 24px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s, transform 0.15s;
  color: var(--text);
  font-family: inherit;
}
.cloud-card:hover {
  border-color: var(--accent);
  background: rgba(14, 165, 233, 0.06);
  transform: translateY(-2px);
}
.cloud-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
}
.cloud-logo svg {
  width: 48px;
  height: 48px;
  object-fit: contain;
}
.cloud-name {
  font-size: 0.95rem;
  font-weight: 600;
}
.cloud-tag {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}
</style>
