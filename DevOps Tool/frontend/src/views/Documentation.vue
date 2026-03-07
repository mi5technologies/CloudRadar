<template>
  <div class="doc-page">
    <div class="doc-masthead">
      <h1>CloudRadar Documentation</h1>
      <p class="doc-intro">
        Complete reference for CloudRadar — from first-time setup to every scan, report, and new feature.
        Use the table of contents to jump to any section.
      </p>
      <div class="version-badge">v2.0 — Updated with all latest features</div>
    </div>

    <!-- TOC -->
    <nav class="doc-toc">
      <div class="toc-group">
        <span class="toc-group-label">Getting started</span>
        <a href="#getting-started">Overview</a>
        <a href="#cloud-selection">Cloud selection</a>
        <a href="#setup">Credentials setup</a>
      </div>
      <div class="toc-group">
        <span class="toc-group-label">New features</span>
        <a href="#dashboard">Dashboard &amp; charts</a>
        <a href="#command-palette">Command palette (Ctrl+K)</a>
        <a href="#findings-slideover">Findings slide-over panel</a>
        <a href="#recommendations">Per-finding recommendations</a>
        <a href="#scan-history">Scan history</a>
        <a href="#post-scan-summary">Post-scan summary card</a>
        <a href="#compliance-gaps">Compliance gap analysis</a>
        <a href="#toast">Toast notifications</a>
        <a href="#sidebar-features">Sidebar features</a>
        <a href="#mobile">Mobile support</a>
      </div>
      <div class="toc-group">
        <span class="toc-group-label">Scans &amp; reports</span>
        <a href="#security">Security scan</a>
        <a href="#vulnerabilities">Vulnerabilities</a>
        <a href="#audit">Audit</a>
        <a href="#compliance">Compliance</a>
        <a href="#governance">Governance</a>
        <a href="#pentest">Pentest</a>
        <a href="#tests">Tests</a>
        <a href="#hosting">Running CloudRadar</a>
      </div>
    </nav>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- GETTING STARTED -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="getting-started">
      <h2>Overview</h2>
      <p>
        <strong>CloudRadar</strong> is a multi-cloud Security Posture Management (CSPM) platform. It discovers
        resources in <strong>AWS, Google Cloud, and Azure</strong>; evaluates security rules; checks compliance
        against CIS / SOC 2 / HIPAA / PCI DSS / ISO 27001; and produces findings, charts, recommendations,
        and pentest output — all from a single browser UI.
      </p>
      <div class="tip-box">
        <span class="tip-icon">💡</span>
        <span>Click the <strong>CloudRadar logo</strong> in the top-left of the sidebar at any time to return to the cloud-selection screen.</span>
      </div>
      <div class="feature-grid">
        <div class="feature-card">
          <span class="feat-emoji">📊</span>
          <strong>Dashboard with charts</strong>
          <span>Real-time risk score, severity donut chart, trend line, and scan history bar chart — per cloud provider.</span>
        </div>
        <div class="feature-card">
          <span class="feat-emoji">⌨️</span>
          <strong>Command palette</strong>
          <span>Press Ctrl+K anywhere to instantly navigate to any page or action.</span>
        </div>
        <div class="feature-card">
          <span class="feat-emoji">📋</span>
          <strong>Findings slide-over</strong>
          <span>Click any finding for a detailed panel with what/why/how-to-fix and AWS docs link.</span>
        </div>
        <div class="feature-card">
          <span class="feat-emoji">📅</span>
          <strong>Scan history</strong>
          <span>Every completed scan is saved automatically — browse, filter and compare past runs.</span>
        </div>
        <div class="feature-card">
          <span class="feat-emoji">✅</span>
          <strong>Compliance gap analysis</strong>
          <span>Failed compliance controls now include specific remediation steps, not just a pass/fail status.</span>
        </div>
        <div class="feature-card">
          <span class="feat-emoji">📱</span>
          <strong>Mobile support</strong>
          <span>Hamburger menu and responsive layout work on phones and tablets.</span>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- CLOUD SELECTION -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="cloud-selection">
      <h2>Cloud selection</h2>
      <p>
        The first screen shows three cloud provider cards: <strong>AWS</strong>, <strong>Google Cloud</strong>,
        and <strong>Azure</strong>. Click the one that matches your environment to be taken to the Setup page.
        You can switch cloud provider at any time from the sidebar Setup link.
      </p>
      <div class="tip-box">
        <span class="tip-icon">ℹ️</span>
        <span>CloudRadar stores your selected cloud in browser storage so the Dashboard will remember it on your next visit.</span>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- SETUP -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="setup">
      <h2>Setup &amp; credentials</h2>
      <p>Credentials are stored in <code>config.yaml</code> in the project root. Restrict file permissions and never commit this file to version control.</p>
      <table class="doc-table">
        <thead><tr><th>Cloud</th><th>Required fields</th><th>Notes</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>AWS</strong></td>
            <td>Region, Access Key ID, Secret Access Key</td>
            <td>Session Token optional (for temporary credentials). Prefer IAM roles or AWS profiles over long-lived keys.</td>
          </tr>
          <tr>
            <td><strong>GCP</strong></td>
            <td>Project ID</td>
            <td>Service account JSON path optional — leave blank to use <code>gcloud auth application-default login</code>.</td>
          </tr>
          <tr>
            <td><strong>Azure</strong></td>
            <td>Subscription ID, Tenant ID, Client ID, Client secret</td>
            <td>Create a service principal with Reader + Security Reader roles on the subscription.</td>
          </tr>
        </tbody>
      </table>
      <p>Click <strong>Save and continue</strong> to persist credentials or <strong>Setup later</strong> to skip and use environment variables.</p>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- DASHBOARD (NEW) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="dashboard">
      <h2>🆕 Dashboard with charts &amp; cloud tabs</h2>
      <p>
        The Dashboard has been completely redesigned. It now shows live data per cloud provider and
        includes interactive Chart.js charts.
      </p>

      <h3>Cloud tabs (AWS / Google Cloud / Azure)</h3>
      <p>
        Three tabs sit at the top of the Dashboard — one for each cloud provider. Clicking a tab
        switches <em>all</em> data on the page (KPI cards, charts, and recommendations) to that
        cloud's scan history. The tab badge shows how many scans have been recorded for that provider.
      </p>

      <h3>KPI cards</h3>
      <table class="doc-table">
        <thead><tr><th>Card</th><th>What it shows</th></tr></thead>
        <tbody>
          <tr><td><strong>Last scan</strong></td><td>How long ago the most recent scan for the selected cloud ran, with cloud name and region.</td></tr>
          <tr><td><strong>Total findings</strong></td><td>Number of security findings from the latest scan of the selected cloud.</td></tr>
          <tr><td><strong>Risk score</strong></td><td>Numeric risk score colour-coded: green (low) → yellow (medium) → orange (high) → red (critical).</td></tr>
          <tr><td><strong>Critical</strong></td><td>Count of critical-severity findings that need immediate remediation.</td></tr>
        </tbody>
      </table>

      <h3>Charts</h3>
      <table class="doc-table">
        <thead><tr><th>Chart</th><th>Type</th><th>What it shows</th></tr></thead>
        <tbody>
          <tr><td><strong>Findings by severity</strong></td><td>Donut chart</td><td>Distribution of Critical / High / Medium / Low findings from the latest scan. Total finding count shown in the centre.</td></tr>
          <tr><td><strong>Risk score over time</strong></td><td>Line chart</td><td>Risk score trend across the last 10 scans for the selected cloud. Requires at least 2 recorded scans.</td></tr>
          <tr><td><strong>Findings per scan</strong></td><td>Stacked bar chart</td><td>Breakdown of severity counts per scan run for the last 8 scans. Each bar is stacked Critical / High / Medium / Low.</td></tr>
        </tbody>
      </table>

      <h3>Top recommendations panel</h3>
      <p>
        Immediately below the charts, the Dashboard shows the <strong>5 highest-priority recommendations</strong>
        for the current cloud provider, derived from the severity profile of the latest scan.
        Each recommendation shows:
      </p>
      <ul>
        <li>A <strong>title</strong> and <strong>severity badge</strong></li>
        <li>A plain-English <em>"What is this?"</em> description</li>
        <li>The first (most important) fix step</li>
        <li>A direct link to the cloud provider's official documentation</li>
      </ul>
      <p>
        Recommendations are <strong>cloud-specific</strong>:
      </p>
      <ul>
        <li><strong>AWS</strong> — e.g. "SSH port 22 open to the world", "S3 bucket publicly accessible", "IAM wildcard action"</li>
        <li><strong>Google Cloud</strong> — e.g. "Firewall rule allows SSH from 0.0.0.0/0", "GCS bucket public", "IAM primitive roles in use"</li>
        <li><strong>Azure</strong> — e.g. "NSG allows RDP from any IP", "Storage account allows public blob access", "Azure AD users without MFA"</li>
      </ul>
      <p>If no scans have been run for a cloud yet, an empty state with a "Run Scan" button is shown instead.</p>

      <h3>Quick actions &amp; connection status</h3>
      <p>
        The bottom of the Dashboard shows 8 quick-action tiles for the most common tasks, plus a
        <strong>cloud connection status card</strong> showing whether credentials are configured for
        the selected provider (region for AWS, project ID for GCP, subscription ID for Azure).
      </p>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- COMMAND PALETTE (NEW) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="command-palette">
      <h2>🆕 Command palette (Ctrl+K)</h2>
      <p>
        The command palette lets you navigate anywhere in CloudRadar instantly — without touching
        the sidebar or mouse.
      </p>
      <h3>How to use it</h3>
      <ol>
        <li>Press <kbd>Ctrl+K</kbd> (Windows/Linux) or <kbd>Cmd+K</kbd> (Mac) from <em>any page</em>.</li>
        <li>Start typing — the palette instantly filters by page name or section.</li>
        <li>Use <kbd>↑</kbd> / <kbd>↓</kbd> arrow keys to move through results.</li>
        <li>Press <kbd>Enter</kbd> to navigate to the highlighted item.</li>
        <li>Press <kbd>Esc</kbd> or click outside to close without navigating.</li>
      </ol>
      <p>The palette covers all 18 pages: Dashboard, Security Scan, Vulnerabilities, Findings, Attack Paths, Scheduled Scans, Notifications, List Assets, Changes, Snapshot Diff, Audit Logs, Scan History, Compliance, Governance, Pentest, Tests, Setup, and Documentation.</p>
      <div class="tip-box">
        <span class="tip-icon">💡</span>
        <span>The hint <kbd>Ctrl+K</kbd> is also displayed at the bottom of the Quick actions section on the Dashboard.</span>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- FINDINGS SLIDE-OVER (NEW) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="findings-slideover">
      <h2>🆕 Findings detail slide-over panel</h2>
      <p>
        The Findings page now has a <strong>right-side slide-over panel</strong>. Click any row in the
        findings table to open it without leaving the page.
      </p>
      <h3>What the panel shows</h3>
      <table class="doc-table">
        <thead><tr><th>Section</th><th>Content</th></tr></thead>
        <tbody>
          <tr><td><strong>Metadata</strong></td><td>Rule ID, resource type, resource ID, region — in a clean grid layout.</td></tr>
          <tr><td><strong>What is this?</strong></td><td>Plain-English explanation of the security issue.</td></tr>
          <tr><td><strong>Why it matters</strong></td><td>Explanation of the real-world risk and how attackers exploit it.</td></tr>
          <tr><td><strong>How to fix it</strong></td><td>Step-by-step numbered remediation instructions specific to the finding type.</td></tr>
          <tr><td><strong>AWS Docs link</strong></td><td>Direct link to the relevant official documentation page.</td></tr>
          <tr><td><strong>Raw JSON</strong></td><td>Collapsible section showing the full raw finding object for debugging.</td></tr>
          <tr><td><strong>Auto-remediation</strong></td><td>For supported resource types (S3, IAM roles, security groups) — dry-run or apply fix directly from the panel.</td></tr>
        </tbody>
      </table>
      <h3>Filtering the findings table</h3>
      <p>Before clicking a row, you can narrow the list with three filters:</p>
      <ul>
        <li><strong>Search box</strong> — filters by rule ID, resource type, resource ID, or title</li>
        <li><strong>Severity dropdown</strong> — show only Critical / High / Medium / Low</li>
        <li><strong>Resource type dropdown</strong> — filter to a specific service (e.g. <code>s3</code>, <code>security_group</code>)</li>
      </ul>
      <p>The <strong>Export CSV</strong> button exports the currently filtered list.</p>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- PER-FINDING RECOMMENDATIONS (NEW) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="recommendations">
      <h2>🆕 Per-finding recommendation library</h2>
      <p>
        CloudRadar now includes a built-in recommendation library with <strong>60+ rule mappings</strong>
        covering all three cloud providers. Every finding is matched to a recommendation that includes:
        what the issue is, why it is dangerous, how to fix it (step by step), and a link to official docs.
      </p>
      <h3>AWS rules covered</h3>
      <p>EC2 (public IP, vulnerable AMI, missing tags) · S3 (public access, no encryption, no versioning) · IAM (wildcard actions, admin policy, unused keys) · Security Groups (SSH open, RDP open, all traffic) · RDS (public, no encryption) · Lambda (hardcoded secrets) · CloudTrail (disabled) · EBS (unencrypted) · EKS (public endpoint) · GuardDuty (disabled) · KMS (no rotation) · VPC (default VPC, no flow logs) · ALB (no WAF, no access logs) · DynamoDB (no PITR) · ECR (critical CVEs, no scan-on-push)</p>
      <h3>Google Cloud rules covered</h3>
      <p>Compute Engine (public IP, serial port, OS patching) · Cloud Storage (public bucket, no CMEK, no versioning) · IAM (service account keys, primitive roles, no MFA) · Firewall (SSH open, RDP open) · VPC (no flow logs) · Cloud SQL (public IP, no backup) · GKE (public endpoint, legacy ABAC) · Cloud Audit Logging (disabled) · Cloud Monitoring (no alerts) · Cloud KMS (no rotation)</p>
      <h3>Azure rules covered</h3>
      <p>Virtual Machines (public IP, no disk encryption, no Defender for Endpoint) · Storage Accounts (public blob, no HTTPS, no CMK) · Azure AD (no MFA, excessive permissions, no PIM) · NSG (SSH open, RDP open) · Azure SQL (public access, no TDE, no auditing) · Key Vault (no expiry, no soft delete) · Azure Monitor (activity log not retained) · Defender for Cloud (not enabled) · AKS (public endpoint, RBAC disabled)</p>
      <div class="tip-box">
        <span class="tip-icon">ℹ️</span>
        <span>Recommendations are matched automatically — first by exact <code>rule_id</code>, then by <code>resource_type</code> prefix. Unrecognised findings fall back to a generic cloud-appropriate recommendation.</span>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- SCAN HISTORY (NEW) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="scan-history">
      <h2>🆕 Scan history</h2>
      <p>
        Every completed scan is automatically saved to browser storage. The <strong>Scan History</strong>
        page (accessible from the Audit group in the sidebar or via Ctrl+K → "Scan History") shows a
        full table of all recorded scans.
      </p>
      <h3>Table columns</h3>
      <table class="doc-table">
        <thead><tr><th>Column</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td><strong>Date &amp; Time</strong></td><td>When the scan ran.</td></tr>
          <tr><td><strong>Cloud</strong></td><td>AWS / GCP / Azure badge.</td></tr>
          <tr><td><strong>Region / Project</strong></td><td>The region or project ID scanned.</td></tr>
          <tr><td><strong>Findings</strong></td><td>Total number of security findings.</td></tr>
          <tr><td><strong>Risk score</strong></td><td>Colour-coded risk score badge.</td></tr>
          <tr><td><strong>Critical / High</strong></td><td>Count of the two most urgent severity levels.</td></tr>
          <tr><td><strong>Duration</strong></td><td>Scan duration in seconds.</td></tr>
          <tr><td><strong>Status</strong></td><td>Completed / Failed / Running.</td></tr>
        </tbody>
      </table>
      <h3>Slide-over detail view</h3>
      <p>Click any row to open a detail panel showing a severity breakdown bar chart for that scan, plus a link to view the current findings.</p>
      <h3>Storage and limits</h3>
      <ul>
        <li>Up to <strong>100 scan records</strong> are stored in <code>localStorage</code>. Oldest records are automatically removed when the limit is reached.</li>
        <li>Data is stored in the browser — clearing browser storage or using a different browser will start fresh.</li>
        <li>Use the <strong>Clear history</strong> button (with confirmation) to wipe all records.</li>
      </ul>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- POST-SCAN SUMMARY (NEW) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="post-scan-summary">
      <h2>🆕 Post-scan summary card</h2>
      <p>
        After a Security Scan completes, instead of raw JSON output, a structured
        <strong>summary card</strong> is displayed at the bottom of the progress log.
      </p>
      <h3>The summary card includes</h3>
      <ul>
        <li><strong>Severity pills</strong> — 🔴 N Critical · 🟠 N High · 🟡 N Medium · 🟢 N Low (or "✅ No findings" if clean)</li>
        <li><strong>Risk score badge</strong> — colour-coded and labelled (critical / high risk / medium risk / low risk)</li>
        <li><strong>Scan metadata</strong> — cloud provider, region, total findings count</li>
        <li><strong>Top 3 recommended actions</strong> — cloud-specific recommendations ranked by severity, each showing the title, first fix step, and severity badge</li>
        <li><strong>Action buttons</strong> — "View All Findings →" and any download links returned by the scan</li>
      </ul>
      <div class="tip-box">
        <span class="tip-icon">💡</span>
        <span>The recommendations shown in the summary card are <strong>cloud-aware</strong>. A GCP scan shows GCP-specific recommendations; an Azure scan shows Azure-specific ones.</span>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- COMPLIANCE GAPS (NEW) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="compliance-gaps">
      <h2>🆕 Compliance gap analysis</h2>
      <p>
        The Compliance page has been upgraded. When you run a check with <strong>JSON + Suggestions</strong>
        output selected, the result is now a structured report with gap analysis — not just raw JSON.
      </p>
      <h3>Compliance summary strip</h3>
      <p>Four cards show: <strong>Passed</strong> count, <strong>Failed</strong> count, overall <strong>Compliance %</strong> (colour-coded), and the selected <strong>Framework</strong>. A progress bar visualises the compliance percentage.</p>

      <h3>Failed controls — gap analysis</h3>
      <p>
        Each failed control appears in an expandable row. Click the row to see:
      </p>
      <ul>
        <li>The control description / reason for failure</li>
        <li>A <strong>gap recommendation</strong> automatically matched to the control — includes what to do, step-by-step fix instructions, and a link to official documentation</li>
      </ul>
      <p>Controls are matched to recommendations using keyword mapping against the control ID and name (e.g. a control mentioning "CloudTrail" maps to the CloudTrail disabled recommendation; a control mentioning "S3 encrypt" maps to the S3 encryption recommendation).</p>

      <h3>Passed controls</h3>
      <p>All passing controls are shown in a collapsible section beneath the failed ones.</p>

      <h3>Raw JSON toggle</h3>
      <p>The full raw API response is always available via a collapsible "Raw JSON response" section at the bottom.</p>

      <h3>How to use</h3>
      <ol>
        <li>Go to <strong>Compliance</strong> in the sidebar.</li>
        <li>Select a framework (CIS, SOC 2, HIPAA, PCI DSS, or ISO 27001).</li>
        <li>Select <strong>JSON + Suggestions</strong> as the output format.</li>
        <li>Click <strong>Run compliance check</strong>.</li>
        <li>Review the summary, then expand any failed control for specific remediation guidance.</li>
      </ol>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- TOAST NOTIFICATIONS (NEW) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="toast">
      <h2>🆕 Toast notification system</h2>
      <p>
        A global toast notification layer is now active across the application. Toasts appear in the
        <strong>bottom-right corner</strong> of the screen and automatically dismiss after a few seconds.
      </p>
      <table class="doc-table">
        <thead><tr><th>Type</th><th>Colour</th><th>Used for</th><th>Auto-dismiss</th></tr></thead>
        <tbody>
          <tr><td><strong>Success</strong></td><td>Green</td><td>Completed actions (scan started, CSV exported, etc.)</td><td>4 seconds</td></tr>
          <tr><td><strong>Error</strong></td><td>Red</td><td>Failed operations, API errors</td><td>6 seconds</td></tr>
          <tr><td><strong>Warning</strong></td><td>Amber</td><td>Non-critical issues requiring attention</td><td>4 seconds</td></tr>
          <tr><td><strong>Info</strong></td><td>Blue</td><td>Informational messages</td><td>4 seconds</td></tr>
        </tbody>
      </table>
      <p>Multiple toasts can stack. Click any toast to dismiss it immediately.</p>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- SIDEBAR FEATURES (NEW) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="sidebar-features">
      <h2>🆕 Sidebar features</h2>

      <h3>Collapse / expand</h3>
      <p>Click the <strong>arrow button</strong> in the top-right of the sidebar to collapse it to icon-only mode. Click again to expand. The state is remembered across browser sessions. The main content area smoothly adjusts its margin.</p>

      <h3>Collapsible navigation groups</h3>
      <p>Each navigation section (Security, Audit, Compliance, Governance, Pentest, Tests) has a <strong>▾ arrow toggle</strong> on the right. Click the group header to collapse or expand its links. Group states are saved in browser storage — your preferred layout is remembered between visits.</p>

      <h3>User profile</h3>
      <p>The bottom of the sidebar shows a user avatar with auto-generated initials and a colour derived from your name. Click the edit icon to change your display name. The name is saved in browser storage.</p>

      <h3>Audit Logs</h3>
      <p>The <strong>Audit Logs</strong> page (under the Audit group) records who ran what and when. Logs are stored in browser storage and can be filtered by user, status, and keyword, then exported to CSV or cleared.</p>

      <h3>Scan History in sidebar</h3>
      <p>The <strong>Scan History</strong> link now appears in the Audit group, giving quick access to the full scan history table from anywhere.</p>

      <h3>Theme toggle</h3>
      <p>The sun ☀ / moon 🌙 buttons at the bottom of the sidebar toggle between dark and light mode. The choice is saved in browser storage.</p>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- MOBILE SUPPORT (NEW) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="mobile">
      <h2>🆕 Mobile &amp; responsive support</h2>
      <p>
        CloudRadar now works on mobile phones and tablets.
      </p>
      <ul>
        <li>On screens narrower than <strong>768 px</strong>, the sidebar is hidden by default.</li>
        <li>A <strong>hamburger button ☰</strong> appears in the top-left corner to open the sidebar as an overlay.</li>
        <li>A <strong>dark backdrop</strong> covers the main content while the sidebar is open — tap it to close.</li>
        <li>The main content padding and layout adjust automatically for small screens.</li>
      </ul>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- SECURITY SCAN (EXISTING) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="security">
      <h2>Security — Full security scan</h2>
      <p>
        The <strong>Security Scan</strong> runs end-to-end discovery, enrichment, rule evaluation, risk scoring,
        and optionally saves a snapshot. Progress is shown step-by-step in real time. After completion, a
        <strong>structured summary card</strong> replaces the raw JSON output (see <a href="#post-scan-summary">Post-scan summary card</a>).
      </p>
      <p>Select which services to scan using the script selector. Deselecting a service skips all its API calls — useful for faster, cheaper targeted scans.</p>

      <h3>Services &amp; what is checked</h3>
      <table class="doc-table">
        <thead><tr><th>Service</th><th>Script ID</th><th>What is checked</th></tr></thead>
        <tbody>
          <tr><td><strong>EC2</strong></td><td><code>ec2</code></td><td>Public IPs, vulnerable AMIs, instance types, missing required tags.</td></tr>
          <tr><td><strong>S3</strong></td><td><code>s3</code></td><td>Public-access-block disabled, missing server-side encryption, overly permissive bucket policies.</td></tr>
          <tr><td><strong>RDS</strong></td><td><code>rds</code></td><td>Publicly accessible flag, storage encryption at rest disabled.</td></tr>
          <tr><td><strong>Lambda</strong></td><td><code>lambda</code></td><td>Short or missing timeout, hardcoded secrets in env vars, missing tags.</td></tr>
          <tr><td><strong>IAM</strong></td><td><code>iam</code></td><td>Wildcard actions in policies, admin-policy attachments, unused access keys.</td></tr>
          <tr><td><strong>Security Groups</strong></td><td><code>sg</code></td><td>Inbound rules open to 0.0.0.0/0 on ports 22, 3389, 3306, 5432, 1433, and others.</td></tr>
          <tr><td><strong>ALB</strong></td><td><code>alb</code></td><td>Internet-facing ALBs missing WAF Web ACL, access logging disabled.</td></tr>
          <tr><td><strong>WAF</strong></td><td><code>waf</code></td><td>Web ACLs not associated with API Gateway or ALB resources.</td></tr>
          <tr><td><strong>CloudTrail</strong></td><td><code>cloudtrail</code></td><td>Multi-region not enabled, log file validation off, CloudWatch integration missing.</td></tr>
          <tr><td><strong>VPC</strong></td><td><code>vpc</code></td><td>Default VPC still in use, VPC flow logs not enabled.</td></tr>
          <tr><td><strong>EBS Volumes</strong></td><td><code>ebs</code></td><td>Volumes without encryption at rest.</td></tr>
          <tr><td><strong>EKS</strong></td><td><code>eks</code></td><td>Public API server endpoint, control plane logging disabled, secrets encryption missing.</td></tr>
          <tr><td><strong>ECS</strong></td><td><code>ecs</code></td><td>Privileged containers, missing CloudWatch log config, containers running as root.</td></tr>
          <tr><td><strong>KMS</strong></td><td><code>kms</code></td><td>Customer-managed keys with automatic rotation disabled.</td></tr>
          <tr><td><strong>API Gateway</strong></td><td><code>apigateway</code></td><td>Access logging not enabled, WAF not attached to REST API stages.</td></tr>
          <tr><td><strong>SQS</strong></td><td><code>sqs</code></td><td>Queues without server-side encryption, public resource policy exposure.</td></tr>
          <tr><td><strong>DynamoDB</strong></td><td><code>dynamodb</code></td><td>Tables without encryption at rest, PITR disabled.</td></tr>
          <tr><td><strong>GuardDuty</strong></td><td><code>guardduty</code></td><td>Threat detection detector not enabled in the scanned region.</td></tr>
          <tr><td><strong>CloudWatch</strong></td><td><code>cloudwatch</code></td><td>Missing CIS metric filters for root login, IAM/CloudTrail/VPC/KMS/S3 changes.</td></tr>
          <tr><td><strong>ECR</strong></td><td><code>ecr</code></td><td>Container images with critical/high CVEs, scan-on-push not enabled.</td></tr>
        </tbody>
      </table>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- VULNERABILITIES -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="vulnerabilities">
      <h2>Security — Vulnerabilities</h2>
      <p>A focused scan for known CVEs and AMI issues without running the full CSPM rule engine.</p>
      <table class="doc-table">
        <thead><tr><th>Script</th><th>ID</th><th>What it does</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>ECR Image Scan</strong></td>
            <td><code>ecr</code></td>
            <td>Pulls all ECR repositories and checks each image tag for CVE findings. Reports critical and high severity CVEs with package name, version, and fix version where available.</td>
          </tr>
          <tr>
            <td><strong>AMI Vulnerability Check</strong></td>
            <td><code>ami</code></td>
            <td>Checks EC2 instances for deprecated AMIs (older than 180 days), public AMI usage, and known-vulnerable AMI IDs.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- AUDIT -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="audit">
      <h2>Audit</h2>
      <p>Audit scripts let you inspect and compare your asset catalog over time. They do not run security rules.</p>
      <table class="doc-table">
        <thead><tr><th>Page</th><th>What it does</th><th>Options</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>List assets</strong></td>
            <td>Exports the full asset catalog from the last scan (or a named snapshot) as JSON or CSV. Includes resource type, ID, region, tags, and risk-score field.</td>
            <td>Output format (JSON / CSV); Snapshot ID (optional).</td>
          </tr>
          <tr>
            <td><strong>Changes</strong></td>
            <td>Compares the current cloud state with the last saved snapshot. Reports added, removed, and modified resources.</td>
            <td>Runs automatically from latest scan vs. previous snapshot.</td>
          </tr>
          <tr>
            <td><strong>Snapshot diff</strong></td>
            <td>Compares two named snapshots by ID. Shows the exact diff between any two points in time.</td>
            <td>Snapshot ID A and Snapshot ID B.</td>
          </tr>
          <tr>
            <td><strong>Audit Logs</strong></td>
            <td>Browser-local log of who ran what action and when. Searchable, filterable, and exportable.</td>
            <td>Filter by user, status, or text. Export CSV. Clear all logs.</td>
          </tr>
          <tr>
            <td><strong>Scan History</strong></td>
            <td>All completed scans recorded in browser storage with severity breakdown and risk scores.</td>
            <td>Click any row for a detail slide-over. Clear history button.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- COMPLIANCE -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="compliance">
      <h2>Compliance</h2>
      <p>Maps security findings to framework controls and generates a pass/fail report with remediation guidance. The check uses findings from the latest scan (or triggers a new scan if no data exists).</p>
      <table class="doc-table">
        <thead><tr><th>Framework</th><th>Standard</th><th>Focus</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>CIS</strong></td>
            <td>CIS AWS Foundations Benchmark v1.5</td>
            <td>IAM password policy, MFA on root, CloudTrail enabled, VPC flow logs, S3 logging, CloudWatch alarms.</td>
          </tr>
          <tr>
            <td><strong>SOC 2</strong></td>
            <td>AICPA SOC 2 Trust Services Criteria</td>
            <td>Logical access controls, encryption in transit and at rest, monitoring, incident response readiness.</td>
          </tr>
          <tr>
            <td><strong>HIPAA</strong></td>
            <td>HIPAA Security Rule (45 CFR Part 164)</td>
            <td>Access control, audit controls, integrity, transmission security, encryption of PHI at rest and in transit.</td>
          </tr>
          <tr>
            <td><strong>PCI DSS</strong></td>
            <td>PCI DSS v4.0</td>
            <td>Firewall rules, no default credentials, encryption of cardholder data, access control, monitoring &amp; logging.</td>
          </tr>
          <tr>
            <td><strong>ISO 27001</strong></td>
            <td>ISO/IEC 27001:2022 Annex A</td>
            <td>A.5 policies, A.6 people controls, A.8 asset management, A.8.20 network security, A.8.24 cryptography, A.8.15 logging.</td>
          </tr>
        </tbody>
      </table>
      <div class="tip-box">
        <span class="tip-icon">🆕</span>
        <span>Select <strong>JSON + Suggestions</strong> as the output format to get per-control gap analysis with specific remediation steps. See <a href="#compliance-gaps">Compliance gap analysis</a> for full details.</span>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- GOVERNANCE -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="governance">
      <h2>Governance</h2>
      <p>Governance checks enforce your organisation's resource policies and tagging standards.</p>
      <table class="doc-table">
        <thead><tr><th>Script</th><th>ID</th><th>What it does</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>Tag Compliance</strong></td>
            <td><code>tags</code></td>
            <td>Scans all resources for required tags (e.g. <code>Environment</code>, <code>Owner</code>, <code>CostCenter</code>). Reports missing or empty tag values. Configurable in <code>config.yaml</code>.</td>
          </tr>
          <tr>
            <td><strong>Resource Policy Checks</strong></td>
            <td><code>policy</code></td>
            <td>Validates resources against defined policies: forbidden instance types in production, minimum backup retention, required encryption settings.</td>
          </tr>
          <tr>
            <td><strong>Policy Violations</strong></td>
            <td><code>violations</code></td>
            <td>Detects resources violating governance policies: publicly exposed resources, unencrypted storage, over-privileged IAM roles.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- PENTEST -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="pentest">
      <h2>Pentest</h2>
      <p>Pentest checks simulate an attacker's perspective — finding exposed entry points, leaked secrets, and exploitable chains.</p>
      <table class="doc-table">
        <thead><tr><th>Script</th><th>ID</th><th>What it does</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>Exposed Services</strong></td>
            <td><code>exposed</code></td>
            <td>Checks security groups and NACLs for inbound rules exposing sensitive ports (22, 3389, 3306, 5432, 1433, 27017, 6379, 9200, etc.) to the public internet.</td>
          </tr>
          <tr>
            <td><strong>Secrets Scan</strong></td>
            <td><code>secrets</code></td>
            <td>Searches asset metadata (Lambda env vars, EC2 user-data, ECS task definitions) and optionally a local repo path for hardcoded secrets using regex patterns.</td>
          </tr>
          <tr>
            <td><strong>Exploit Mapping</strong></td>
            <td><code>exploits</code></td>
            <td>Maps findings to known exploit chains using a graph engine. Example: public-S3 + wildcard-IAM = data exfiltration path; exposed-EC2 + EKS-public-API = cluster takeover path.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- TESTS -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="tests">
      <h2>Tests</h2>
      <p>Runs CloudRadar's built-in unit and integration test suite using <code>pytest</code> with mocked AWS services. Tests never make real API calls.</p>
      <table class="doc-table">
        <thead><tr><th>Module</th><th>What it tests</th></tr></thead>
        <tbody>
          <tr><td><strong>Rule Engine</strong></td><td>Security rules fire correctly and produce accurate findings with correct fields.</td></tr>
          <tr><td><strong>S3 Scanner</strong></td><td>S3-specific scanner end-to-end with moto: public bucket, no encryption, permissive policy, clean bucket.</td></tr>
          <tr><td><strong>Compliance Frameworks</strong></td><td>All five frameworks map findings to controls correctly; pass/fail is accurate; clean environment produces all-pass report.</td></tr>
          <tr><td><strong>Remediation Engine</strong></td><td>Auto-remediation actions are generated correctly for each finding type.</td></tr>
          <tr><td><strong>Attack Paths</strong></td><td>Attack path graph builds correctly; high-severity chains are detected; isolated resources produce no path.</td></tr>
          <tr><td><strong>All Scanners</strong></td><td>Integration tests for every scanner module: EC2, RDS, IAM, Lambda, CloudTrail, VPC, EBS, EKS, ECS, KMS, API Gateway, SQS, DynamoDB, GuardDuty, CloudWatch.</td></tr>
        </tbody>
      </table>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- HOSTING -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <section class="doc-section" id="hosting">
      <h2>Running CloudRadar</h2>
      <h3>Local setup</h3>
      <ol>
        <li>Install Python deps: <code>pip install -e .</code></li>
        <li>Install and build frontend: <code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code></li>
        <li>Start the server: <code>python -m cspm.cli ui --host 127.0.0.1 --port 8000</code></li>
        <li>Open <code>http://127.0.0.1:8000</code>, select your cloud, and enter credentials in Setup.</li>
      </ol>

      <h3>Hosted on a server</h3>
      <ol>
        <li>Build the frontend on the server (or copy the <code>frontend/dist/</code> folder).</li>
        <li>Run: <code>python -m cspm.cli ui --host 0.0.0.0 --port 8000</code></li>
        <li>Put Nginx or another reverse proxy in front with HTTPS.</li>
        <li>Add this to your Nginx config to prevent SSE buffering:<pre class="doc-code">proxy_buffering off;
X-Accel-Buffering: no;</pre></li>
        <li>Prefer IAM roles (AWS), Workload Identity (GCP), or Managed Identity (Azure) instead of storing keys in <code>config.yaml</code>.</li>
      </ol>

      <h3>Docker</h3>
      <p>A <code>docker-compose.yml</code> is included. Run <code>docker compose up --build</code> to start the full stack. Set credentials via environment variables or mount a <code>config.yaml</code> volume.</p>
    </section>
  </div>
</template>

<script setup>
</script>

<style scoped>
.doc-page { max-width: 860px; }

/* Masthead */
.doc-masthead { margin-bottom: 24px; }
.doc-intro { font-size: 1.05rem; color: var(--text-muted); margin: 8px 0 12px; line-height: 1.6; }
.version-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; background: rgba(14,165,233,0.15); color: var(--accent); border: 1px solid rgba(14,165,233,0.25); }

/* TOC */
.doc-toc {
  display: flex; flex-wrap: wrap; gap: 16px 32px;
  padding: 16px 20px;
  background: rgba(14,165,233,0.05);
  border: 1px solid rgba(14,165,233,0.2);
  border-radius: 12px;
  margin-bottom: 36px;
}
.toc-group { display: flex; flex-direction: column; gap: 4px; }
.toc-group-label { font-size: 0.68rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); margin-bottom: 2px; }
.doc-toc a { font-size: 0.84rem; color: var(--accent); text-decoration: none; white-space: nowrap; }
.doc-toc a:hover { text-decoration: underline; }

/* Sections */
.doc-section { margin-bottom: 40px; }
.doc-section h2 {
  font-size: 1.15rem; color: var(--text); margin: 0 0 14px;
  padding-bottom: 8px; border-bottom: 2px solid var(--border);
  display: flex; align-items: center; gap: 8px;
}
.doc-section h3 { font-size: 0.95rem; margin: 20px 0 8px; color: var(--text); font-weight: 600; }
.doc-section p, .doc-section ul, .doc-section ol { margin: 0 0 12px; line-height: 1.65; color: var(--text); }
.doc-section ul, .doc-section ol { padding-left: 24px; }
.doc-section li { margin-bottom: 4px; }
.doc-section a { color: var(--accent); }
.doc-section code {
  background: rgba(0,0,0,0.3); padding: 2px 6px;
  border-radius: 4px; font-size: 0.85em;
}
.doc-code {
  background: rgba(0,0,0,0.35); border-radius: 8px; padding: 10px 14px;
  font-family: monospace; font-size: 0.82rem; color: #d4d4d4;
  margin: 8px 0 12px; overflow-x: auto; display: block;
}
kbd {
  background: rgba(148,163,184,0.1); border: 1px solid rgba(148,163,184,0.25);
  border-radius: 5px; padding: 2px 7px; font-size: 0.8rem; font-family: inherit;
  color: var(--text);
}

/* Tip box */
.tip-box {
  display: flex; align-items: flex-start; gap: 10px; padding: 10px 14px;
  background: rgba(14,165,233,0.07); border: 1px solid rgba(14,165,233,0.18);
  border-radius: 9px; margin: 10px 0 14px; font-size: 0.86rem; line-height: 1.5;
  color: var(--text-muted);
}
.tip-icon { flex-shrink: 0; font-size: 1rem; margin-top: 1px; }
.tip-box a { color: var(--accent); }

/* Feature overview cards */
.feature-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; margin: 16px 0 20px; }
.feature-card {
  display: flex; flex-direction: column; gap: 4px; padding: 14px;
  background: rgba(15,23,42,0.5); border: 1px solid var(--border);
  border-radius: 12px;
}
.feat-emoji { font-size: 1.4rem; }
.feature-card strong { font-size: 0.88rem; color: var(--text); }
.feature-card span { font-size: 0.78rem; color: var(--text-muted); line-height: 1.5; }

/* Tables */
.doc-table { width: 100%; border-collapse: collapse; margin: 10px 0 18px; font-size: 0.85rem; }
.doc-table th, .doc-table td { text-align: left; padding: 9px 12px; border: 1px solid var(--border); color: var(--text); vertical-align: top; line-height: 1.5; }
.doc-table thead th { background: rgba(14,165,233,0.10); font-weight: 600; color: var(--accent); }
.doc-table tbody tr:nth-child(even) { background: rgba(255,255,255,0.03); }

/* Light theme */
:global(.theme-light) .doc-section code { background: rgba(0,0,0,0.07); }
:global(.theme-light) .doc-code { background: #1e1e2e; }
:global(.theme-light) .doc-table tbody tr:nth-child(even) { background: rgba(0,0,0,0.03); }
:global(.theme-light) .feature-card { background: rgba(255,255,255,0.7); }
:global(.theme-light) kbd { background: rgba(0,0,0,0.06); border-color: rgba(0,0,0,0.15); }
</style>
