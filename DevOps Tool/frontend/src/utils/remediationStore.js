/**
 * Remediation Progress Store
 *
 * Tracks which rule_ids + resource_ids have been marked as "fixed" by the user.
 * State is persisted in localStorage so it survives page refreshes.
 *
 * Schema stored in localStorage key "cspm_remediation":
 * {
 *   "rule_id::resource_id": { ruleId, resourceId, resourceName, fixedAt, cloud, severity },
 *   ...
 * }
 */

const STORAGE_KEY = 'cspm_remediation'

function _load() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

function _save(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch {
    // quota exceeded — silently fail
  }
}

function _key(ruleId, resourceId) {
  return `${ruleId || 'unknown'}::${resourceId || 'unknown'}`
}

/** Mark a finding as fixed */
export function markFixed(finding) {
  const store = _load()
  const k = _key(finding.rule_id, finding.resource_id)
  store[k] = {
    ruleId: finding.rule_id,
    resourceId: finding.resource_id,
    resourceName: finding.resource_name || finding.resource_id,
    severity: finding.severity,
    cloud: finding.cloud || 'aws',
    title: finding.title || finding.rule_id,
    fixedAt: new Date().toISOString(),
  }
  _save(store)
}

/** Unmark a finding as fixed (re-opens it) */
export function unmarkFixed(finding) {
  const store = _load()
  delete store[_key(finding.rule_id, finding.resource_id)]
  _save(store)
}

/** Returns true if this specific finding instance is marked fixed */
export function isFixed(finding) {
  const store = _load()
  return !!store[_key(finding.rule_id, finding.resource_id)]
}

/** Returns the full map of all fixed items */
export function getAllFixed() {
  return _load()
}

/** Returns count of fixed items */
export function getFixedCount() {
  return Object.keys(_load()).length
}

/** Clear all remediation data */
export function clearAll() {
  _save({})
}

/**
 * Compute a simple remediation risk score delta.
 * Each severity level subtracts a weighted amount from 100.
 */
const SEVERITY_WEIGHT = { critical: 25, high: 15, medium: 8, low: 3 }

export function computeRemediationScore(findings = []) {
  const fixed = _load()
  let remaining = 0
  let resolved = 0

  for (const f of findings) {
    const w = SEVERITY_WEIGHT[(f.severity || 'low').toLowerCase()] ?? 3
    const k = _key(f.rule_id, f.resource_id)
    if (fixed[k]) {
      resolved += w
    } else {
      remaining += w
    }
  }

  const total = remaining + resolved
  if (total === 0) return { score: 100, resolved, remaining, percentage: 100 }
  const percentage = Math.round((resolved / total) * 100)
  // Risk score = percentage of weight still unresolved, normalised to 0-100
  const riskScore = Math.round((remaining / total) * 100)
  return { score: 100 - riskScore, resolved, remaining, percentage }
}

/**
 * Returns prioritised recommendations based on actual finding data.
 * Findings are grouped by rule_id and ranked by:
 *   1. Severity weight (critical → low)
 *   2. Occurrence count (more affected resources = higher priority)
 * Quick wins: medium/low severity, quickWin=true in recommendation, single affected resource.
 */
export function getPrioritisedRecs(findings = [], recommendations = {}, cloud = 'aws', maxItems = 5) {
  const fixed = _load()

  // Group findings by rule_id, excluding already-fixed ones
  const groups = {}
  for (const f of findings) {
    if ((f.cloud || 'aws').toLowerCase() !== cloud.toLowerCase()) continue
    const k = _key(f.rule_id, f.resource_id)
    if (fixed[k]) continue  // already marked fixed
    const rid = f.rule_id || 'unknown'
    if (!groups[rid]) {
      groups[rid] = { rule_id: rid, severity: f.severity, count: 0, finding: f }
    }
    groups[rid].count++
  }

  const SWEIGHT = { critical: 1000, high: 100, medium: 10, low: 1 }

  // Sort by severity × occurrence count
  const sorted = Object.values(groups).sort((a, b) => {
    const wa = (SWEIGHT[(a.severity || 'low').toLowerCase()] ?? 1) * a.count
    const wb = (SWEIGHT[(b.severity || 'low').toLowerCase()] ?? 1) * b.count
    return wb - wa
  })

  return sorted.slice(0, maxItems).map(g => {
    const rec = recommendations[g.rule_id] || null
    return {
      rule_id: g.rule_id,
      severity: g.severity,
      count: g.count,
      recommendation: rec,
      title: rec?.title || g.finding?.title || g.rule_id,
    }
  })
}

/**
 * Quick wins: unfixed findings that are medium/low severity with quickWin=true
 * in their recommendation, or have count === 1 (single resource, easy fix).
 */
export function getQuickWins(findings = [], recommendations = {}, cloud = 'aws', maxItems = 5) {
  const fixed = _load()

  const groups = {}
  for (const f of findings) {
    if ((f.cloud || 'aws').toLowerCase() !== cloud.toLowerCase()) continue
    const k = _key(f.rule_id, f.resource_id)
    if (fixed[k]) continue
    const rid = f.rule_id || 'unknown'
    if (!groups[rid]) {
      groups[rid] = { rule_id: rid, severity: f.severity, count: 0, finding: f }
    }
    groups[rid].count++
  }

  const wins = []
  for (const g of Object.values(groups)) {
    const rec = recommendations[g.rule_id]
    const sev = (g.severity || 'low').toLowerCase()
    const isQuickWin = rec?.quickWin === true || sev === 'low' || sev === 'medium'
    if (isQuickWin) {
      wins.push({
        rule_id: g.rule_id,
        severity: g.severity,
        count: g.count,
        recommendation: rec,
        title: rec?.title || g.finding?.title || g.rule_id,
      })
    }
  }

  // Sort quick wins: medium before low, then by count
  const QWEIGHT = { medium: 10, low: 1 }
  wins.sort((a, b) => {
    const wa = (QWEIGHT[(a.severity || 'low').toLowerCase()] ?? 1) * a.count
    const wb = (QWEIGHT[(b.severity || 'low').toLowerCase()] ?? 1) * b.count
    return wb - wa
  })

  return wins.slice(0, maxItems)
}
