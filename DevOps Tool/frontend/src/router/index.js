import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Welcome', component: () => import('../views/Welcome.vue'), meta: { title: 'Welcome', noSidebar: true } },
  { path: '/setup', name: 'Setup', component: () => import('../views/Setup.vue'), meta: { title: 'Setup', noSidebar: true } },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: 'Dashboard' } },
  { path: '/security/scan', name: 'SecurityScan', component: () => import('../views/SecurityScan.vue'), meta: { title: 'Security Scan' } },
  { path: '/security/vulnerabilities', name: 'Vulnerabilities', component: () => import('../views/Vulnerabilities.vue'), meta: { title: 'Vulnerabilities' } },
  { path: '/audit/assets', name: 'Assets', component: () => import('../views/Assets.vue'), meta: { title: 'Assets' } },
  { path: '/audit/changes', name: 'Changes', component: () => import('../views/Changes.vue'), meta: { title: 'Changes' } },
  { path: '/audit/diff', name: 'Diff', component: () => import('../views/Diff.vue'), meta: { title: 'Snapshot Diff' } },
  { path: '/compliance', name: 'Compliance', component: () => import('../views/Compliance.vue'), meta: { title: 'Compliance' } },
  { path: '/governance', name: 'Governance', component: () => import('../views/Governance.vue'), meta: { title: 'Governance' } },
  { path: '/pentest', name: 'Pentest', component: () => import('../views/Pentest.vue'), meta: { title: 'Pentest' } },
  { path: '/documentation', name: 'Documentation', component: () => import('../views/Documentation.vue'), meta: { title: 'Documentation' } },
  { path: '/findings', name: 'Findings', component: () => import('../views/Findings.vue'), meta: { title: 'Findings' } },
  { path: '/security/attack-paths', name: 'AttackPaths', component: () => import('../views/AttackPaths.vue'), meta: { title: 'Attack Paths' } },
  { path: '/security/notifications', name: 'Notifications', component: () => import('../views/Notifications.vue'), meta: { title: 'Notifications' } },
  { path: '/security/scheduled', name: 'ScheduledScans', component: () => import('../views/ScheduledScans.vue'), meta: { title: 'Scheduled Scans' } },
  { path: '/tests', name: 'Tests', component: () => import('../views/Tests.vue'), meta: { title: 'Tests' } },
  { path: '/audit/logs', name: 'AuditLogs', component: () => import('../views/AuditLogs.vue'), meta: { title: 'Audit Logs' } },
  { path: '/scan-history', name: 'ScanHistory', component: () => import('../views/ScanHistory.vue'), meta: { title: 'Scan History' } },
]

const router = createRouter({
  history: createWebHistory('/'),
  routes,
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} – CloudRadar` : 'CloudRadar'
})

export default router
