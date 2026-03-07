<template>
  <teleport to="body">
    <transition name="palette-fade">
      <div v-if="open" class="palette-overlay" @mousedown.self="close">
        <div class="palette-modal">
          <div class="palette-search-wrap">
            <svg class="palette-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              ref="inputRef"
              v-model="query"
              class="palette-input"
              placeholder="Search pages, actions…"
              @keydown.escape="close"
              @keydown.arrow-down.prevent="moveDown"
              @keydown.arrow-up.prevent="moveUp"
              @keydown.enter.prevent="confirm"
            />
            <kbd class="palette-esc">ESC</kbd>
          </div>
          <div class="palette-list" ref="listRef">
            <div
              v-for="(item, i) in filtered"
              :key="item.id"
              class="palette-item"
              :class="{ active: i === cursor }"
              @mouseenter="cursor = i"
              @click="pick(item)"
            >
              <span class="palette-item-icon">{{ item.icon }}</span>
              <span class="palette-item-label">{{ item.label }}</span>
              <span class="palette-item-group">{{ item.group }}</span>
            </div>
            <div v-if="!filtered.length" class="palette-empty">No results for "{{ query }}"</div>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const open   = ref(false)
const query  = ref('')
const cursor = ref(0)
const inputRef = ref(null)
const listRef  = ref(null)

const ALL_ITEMS = [
  { id: 'dashboard',     icon: '🏠', label: 'Dashboard',          group: 'Navigation', path: '/dashboard' },
  { id: 'scan',          icon: '🔍', label: 'Security Scan',       group: 'Security',   path: '/security/scan' },
  { id: 'vulns',         icon: '🛡️', label: 'Vulnerabilities',     group: 'Security',   path: '/security/vulnerabilities' },
  { id: 'findings',      icon: '📋', label: 'Findings',            group: 'Security',   path: '/findings' },
  { id: 'attack-paths',  icon: '⛓',  label: 'Attack Paths',        group: 'Security',   path: '/security/attack-paths' },
  { id: 'scheduled',     icon: '🕐', label: 'Scheduled Scans',     group: 'Security',   path: '/security/scheduled' },
  { id: 'notifications', icon: '🔔', label: 'Notifications',       group: 'Security',   path: '/security/notifications' },
  { id: 'assets',        icon: '📦', label: 'List Assets',         group: 'Audit',      path: '/audit/assets' },
  { id: 'changes',       icon: '🔄', label: 'Changes',             group: 'Audit',      path: '/audit/changes' },
  { id: 'diff',          icon: '📊', label: 'Snapshot Diff',       group: 'Audit',      path: '/audit/diff' },
  { id: 'audit-logs',    icon: '📝', label: 'Audit Logs',          group: 'Audit',      path: '/audit/logs' },
  { id: 'scan-history',  icon: '📅', label: 'Scan History',        group: 'Audit',      path: '/scan-history' },
  { id: 'compliance',    icon: '✅', label: 'Compliance Report',   group: 'Compliance', path: '/compliance' },
  { id: 'governance',    icon: '🏛️', label: 'Governance Report',   group: 'Governance', path: '/governance' },
  { id: 'pentest',       icon: '🔓', label: 'Run Pentest',         group: 'Pentest',    path: '/pentest' },
  { id: 'tests',         icon: '🧪', label: 'Run Tests',           group: 'Tests',      path: '/tests' },
  { id: 'setup',         icon: '⚙️', label: 'Setup Credentials',   group: 'Settings',   path: '/setup' },
  { id: 'docs',          icon: '📄', label: 'Documentation',       group: 'Help',       path: '/documentation' },
]

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return ALL_ITEMS
  return ALL_ITEMS.filter(i =>
    i.label.toLowerCase().includes(q) || i.group.toLowerCase().includes(q)
  )
})

watch(query, () => { cursor.value = 0 })

function moveDown() {
  cursor.value = Math.min(cursor.value + 1, filtered.value.length - 1)
  scrollActiveIntoView()
}
function moveUp() {
  cursor.value = Math.max(cursor.value - 1, 0)
  scrollActiveIntoView()
}
function scrollActiveIntoView() {
  nextTick(() => {
    const el = listRef.value?.querySelector('.active')
    el?.scrollIntoView({ block: 'nearest' })
  })
}
function confirm() {
  if (filtered.value[cursor.value]) pick(filtered.value[cursor.value])
}
function pick(item) {
  router.push(item.path)
  close()
}
function close() {
  open.value = false
  query.value = ''
  cursor.value = 0
}
function openPalette() {
  open.value = true
  nextTick(() => inputRef.value?.focus())
}

function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    open.value ? close() : openPalette()
  }
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.palette-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.55);
  display: flex; align-items: flex-start; justify-content: center;
  padding-top: 12vh;
  z-index: 8000;
  backdrop-filter: blur(4px);
}
.palette-modal {
  width: 100%;
  max-width: 560px;
  background: #0f172a;
  border: 1px solid rgba(148,163,184,0.18);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.6);
}
.palette-search-wrap {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(148,163,184,0.12);
}
.palette-icon { width: 18px; height: 18px; color: rgba(148,163,184,0.6); flex-shrink: 0; }
.palette-input {
  flex: 1; background: none; border: none; outline: none;
  font-size: 1rem; color: #e2e8f0; font-family: inherit;
}
.palette-input::placeholder { color: rgba(148,163,184,0.5); }
.palette-esc {
  font-size: 0.7rem; padding: 3px 7px; border-radius: 5px;
  background: rgba(148,163,184,0.12); color: #64748b;
  border: 1px solid rgba(148,163,184,0.15); font-family: inherit;
}
.palette-list { max-height: 380px; overflow-y: auto; padding: 6px; }
.palette-list::-webkit-scrollbar { width: 4px; }
.palette-list::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.15); border-radius: 2px; }
.palette-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: 9px; cursor: pointer;
  transition: background 0.1s;
}
.palette-item.active, .palette-item:hover { background: rgba(14,165,233,0.12); }
.palette-item-icon { font-size: 1.05rem; width: 22px; text-align: center; flex-shrink: 0; }
.palette-item-label { flex: 1; font-size: 0.92rem; font-weight: 500; color: #e2e8f0; }
.palette-item-group { font-size: 0.72rem; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
.palette-empty { padding: 24px; text-align: center; color: #64748b; font-size: 0.88rem; }

.palette-fade-enter-active { transition: opacity 0.15s, transform 0.15s; }
.palette-fade-leave-active { transition: opacity 0.12s, transform 0.12s; }
.palette-fade-enter-from, .palette-fade-leave-to { opacity: 0; transform: scale(0.97); }
</style>
