const MAX_LOGS = 500

/**
 * Log an audit entry.
 * @param {string} action   - What happened (e.g. "Security Scan")
 * @param {string} detail   - Extra context (e.g. "AWS us-east-1 · 12 findings")
 * @param {string} status   - 'success' | 'error' | 'info'
 * @param {string} cloud    - 'aws' | 'gcp' | 'azure' | '' (optional)
 */
export function logAudit(action, detail = '', status = 'success', cloud = '') {
  try {
    const userName = localStorage.getItem('cspm_user_name') || 'Admin'
    const logs = getAuditLogs()
    logs.unshift({
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      timestamp: new Date().toISOString(),
      user: userName,
      action,
      detail,
      status,
      cloud: cloud || (localStorage.getItem('cspm_cloud') || ''),
    })
    if (logs.length > MAX_LOGS) logs.splice(MAX_LOGS)
    localStorage.setItem('cspm_audit_logs', JSON.stringify(logs))
  } catch (_) {}
}

export function getAuditLogs() {
  try {
    return JSON.parse(localStorage.getItem('cspm_audit_logs') || '[]')
  } catch (_) {
    return []
  }
}

export function clearAuditLogs() {
  try {
    localStorage.removeItem('cspm_audit_logs')
  } catch (_) {}
}
