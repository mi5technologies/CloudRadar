const MAX_LOGS = 500

export function logAudit(action, detail = '', status = 'success') {
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
