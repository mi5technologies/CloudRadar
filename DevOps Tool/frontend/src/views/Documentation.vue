<template>
  <div class="docs-root">
    <!-- Floating back to contents button -->
    <transition name="fab-fade">
      <button v-if="showFab" class="fab-contents" @click="scrollToTop" title="Back to contents">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>
        Contents
      </button>
    </transition>

    <div class="docs-layout">
      <!-- Sidebar TOC -->
      <aside class="docs-toc">
        <div class="toc-title">Contents</div>
        <nav>
          <a v-for="item in toc" :key="item.id" :href="'#' + item.id"
            class="toc-link" :class="{ 'toc-sub': item.sub }">
            {{ item.label }}
          </a>
        </nav>
      </aside>

      <!-- Main content -->
      <main class="docs-content">
        <!-- ───── Overview ───── -->
        <section id="overview">
          <h1>CloudRadar CSPM — Documentation</h1>
          <p class="lead">
            CloudRadar is a multi-cloud Cloud Security Posture Management (CSPM) platform that
            continuously scans AWS, Google Cloud, and Azure environments for misconfigurations,
            vulnerabilities, compliance gaps, and attack paths — and provides actionable remediation
            guidance for every finding.
          </p>
          <div class="info-box">
            <strong>Quick start:</strong> Go to <strong>Welcome</strong> → select your cloud → configure credentials → run a <strong>Security Scan</strong>.
            Press <kbd>Ctrl+K</kbd> (or <kbd>⌘K</kbd>) anywhere to open the command palette for fast navigation.
          </div>
        </section>

        <!-- ───── Getting Started ───── -->
        <section id="getting-started">
          <h2>Getting started</h2>

          <h3 id="cloud-setup">1. Cloud credentials setup</h3>
          <p>Before running any scan, configure credentials for the cloud you want to audit:</p>

          <div class="tabs-wrap">
            <div class="tab-block">
              <div class="tab-head aws">AWS</div>
              <div class="tab-body">
                <ol>
                  <li>Create an IAM user or role with the <code>SecurityAudit</code> + <code>ReadOnlyAccess</code> managed policies.</li>
                  <li>Generate an Access Key + Secret Key for the IAM user.</li>
                  <li>Run <code>aws configure</code> on the server running CloudRadar, or set the
                    <code>AWS_ACCESS_KEY_ID</code> / <code>AWS_SECRET_ACCESS_KEY</code> environment variables.</li>
                  <li>Optional: add the <code>arn:aws:iam::aws:policy/AmazonGuardDutyReadOnlyAccess</code> policy for GuardDuty checks.</li>
                </ol>
              </div>
            </div>
            <div class="tab-block">
              <div class="tab-head gcp">Google Cloud</div>
              <div class="tab-body">
                <ol>
                  <li>Create a Service Account in your GCP project with the following roles:
                    <code>Viewer</code>, <code>Security Reviewer</code>, <code>Cloud Asset Viewer</code>.</li>
                  <li>Download the JSON key file for the service account.</li>
                  <li>Set the environment variable: <code>GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json</code>.</li>
                  <li>Pass your <strong>Project ID</strong> when starting a scan.</li>
                </ol>
              </div>
            </div>
            <div class="tab-block">
              <div class="tab-head azure">Azure</div>
              <div class="tab-body">
                <ol>
                  <li>Register an App in Azure AD (App registrations → New registration).</li>
                  <li>Assign the app the <strong>Reader</strong> + <strong>Security Reader</strong> roles at the subscription scope.</li>
                  <li>Create a client secret and set the environment variables:
                    <code>AZURE_TENANT_ID</code>, <code>AZURE_CLIENT_ID</code>, <code>AZURE_CLIENT_SECRET</code>.</li>
                  <li>Pass your <strong>Subscription ID</strong> when starting a scan.</li>
                </ol>
              </div>
            </div>
          </div>

          <h3 id="first-scan">2. Running your first scan</h3>
          <ol>
            <li>Click <strong>Security</strong> → <strong>Security Scan</strong> in the sidebar.</li>
            <li>Select the cloud provider (AWS, Google Cloud, or Azure).</li>
            <li>Enter the Region / Project ID / Subscription ID as appropriate.</li>
            <li>Select the services you want to scan — or leave all checked for a full scan.</li>
            <li>Click <strong>Run security scan</strong> and watch real-time progress steps.</li>
            <li>After the scan completes, review the structured <strong>Post-scan summary card</strong>.</li>
            <li>Go to <strong>Findings</strong> for detailed, filterable results with per-finding remediation.</li>
          </ol>
        </section>

        <!-- ───── Dashboard ───── -->
        <section id="dashboard">
          <h2>Dashboard</h2>
          <p>
            The Dashboard provides a high-level security posture overview across all three clouds.
            It is accessible at any time from the sidebar.
          </p>
          <h3 id="dashboard-clouds">Multi-cloud tabs</h3>
          <p>
            Three cloud tabs appear at the top of the Dashboard (AWS, Google Cloud, Azure). Click any tab
            to switch the entire Dashboard — all KPI cards, charts, and recommendations update to show
            data only for that cloud. The selected cloud is persisted in <code>localStorage</code> and
            remembered between sessions.
          </p>
          <h3 id="dashboard-charts">Charts</h3>
          <ul>
            <li><strong>Findings by severity</strong> — Donut chart showing the Critical / High / Medium / Low split for the most recent scan of the selected cloud.</li>
            <li><strong>Risk score over time</strong> — Line chart showing risk score trend across the last 10 scans of the selected cloud.</li>
            <li><strong>Findings per scan</strong> — Bar chart showing total findings per scan over time for the selected cloud.</li>
          </ul>
          <p>Charts are powered by Chart.js and update automatically when the cloud tab is switched.</p>
          <h3 id="dashboard-recs">Top recommendations panel (findings-aware)</h3>
          <p>
            The Dashboard shows up to 5 prioritised recommendations for the selected cloud.
            When scan history contains findings, recommendations are <strong>ranked by actual data</strong> —
            sorted by severity weight × number of affected resources. A finding type that affects 5 resources
            ranks higher than one affecting only 1. The label "ranked by your scan data" appears when live
            findings are used. If no scan history exists, the panel falls back to the static priority table.
          </p>
          <h3 id="dashboard-quickwins">Quick Wins panel</h3>
          <p>
            Below the top recommendations, a <strong>⚡ Quick Wins</strong> panel highlights medium/low
            severity findings marked as easy to fix (single console action). These are surfaced separately so
            you can improve your posture quickly without tackling critical issues first.
          </p>
          <h3 id="dashboard-remediation">Remediation Progress panel</h3>
          <p>
            When a scan has been run, a progress bar shows what percentage of your findings have been
            marked as fixed. The score updates immediately as you mark findings on the Findings page.
            The panel also shows a <strong>risk score</strong> (0–100) that reflects only your remaining
            unfixed findings — watch it improve as you remediate.
          </p>
          <h3 id="dashboard-kpis">KPI cards</h3>
          <p>
            Four KPI cards show: last scan time, total findings, risk score, and critical count.
            A "No scans yet" empty state is shown if no scan history exists for the selected cloud.
          </p>
        </section>

        <!-- ───── Security Scan ───── -->
        <section id="security-scan">
          <h2>Security Scan</h2>
          <p>
            The Security Scan page performs a comprehensive, service-by-service audit of your cloud environment.
            Every service list is cloud-specific — the correct service names are shown for each cloud.
          </p>
          <h3 id="scan-aws">AWS services scanned (31)</h3>
          <div class="service-grid">
            <span class="svc-chip" v-for="s in awsServices" :key="s">{{ s }}</span>
          </div>
          <h3 id="scan-gcp">Google Cloud services scanned (23)</h3>
          <div class="service-grid">
            <span class="svc-chip gcp" v-for="s in gcpServices" :key="s">{{ s }}</span>
          </div>
          <h3 id="scan-azure">Azure services scanned (23)</h3>
          <div class="service-grid">
            <span class="svc-chip azure" v-for="s in azureServices" :key="s">{{ s }}</span>
          </div>
          <h3 id="scan-options">Scan options</h3>
          <ul>
            <li><strong>Cloud provider</strong> — switch between AWS, Google Cloud, and Azure. The service list updates automatically.</li>
            <li><strong>Region / Project ID / Subscription ID</strong> — the label and input change based on the selected cloud.</li>
            <li><strong>Save snapshot</strong> — saves a JSON snapshot of findings to disk for later comparison.</li>
            <li><strong>Service selection</strong> — deselect individual services to skip them. The "Run" button shows how many services are selected.</li>
          </ul>
          <h3 id="scan-progress">Real-time progress</h3>
          <p>
            Each scan step is streamed in real time via Server-Sent Events (SSE). Steps show a running,
            success, or failed status. After completion, the post-scan summary card is displayed.
          </p>
          <h3 id="scan-summary">Post-scan summary card</h3>
          <p>The summary card shows:</p>
          <ul>
            <li>Severity pill counts (Critical, High, Medium, Low)</li>
            <li>Overall risk score (0–100)</li>
            <li>Cloud, region/project, and total findings count</li>
            <li><strong>Prioritised actions</strong> — top 3 recommendations ranked by severity × affected resources from this scan (labelled "ranked by your findings" when findings are available)</li>
            <li><strong>⚡ Quick wins</strong> — up to 3 low-effort, high-impact fixes pulled from the scan's medium/low findings</li>
            <li>Download links for JSON and CSV reports</li>
          </ul>
        </section>

        <!-- ───── Findings ───── -->
        <section id="findings">
          <h2>Findings</h2>
          <p>
            The Findings page lists all security findings from the most recent scan with powerful filtering
            and a slide-over detail panel.
          </p>
          <h3 id="findings-filter">Filters</h3>
          <ul>
            <li><strong>Search</strong> — free-text search across rule ID, resource ID, resource type, and title.</li>
            <li><strong>Severity</strong> — filter by Critical, High, Medium, or Low.</li>
            <li><strong>Resource type</strong> — filter by the affected resource type (e.g. ec2, gcp.firewall, azure.nsg).</li>
          </ul>
          <h3 id="findings-slideover">Slide-over detail panel</h3>
          <p>Click any finding row to open the slide-over panel, which shows:</p>
          <ul>
            <li>Finding title, severity badge, cloud badge, rule ID, resource ID, resource type</li>
            <li><strong>What is this?</strong> — plain-English explanation of the issue</li>
            <li><strong>Why it matters</strong> — business and security impact</li>
            <li><strong>How to fix it</strong> — numbered remediation steps</li>
            <li><strong>Documentation link</strong> — direct link to the cloud provider's official docs</li>
            <li><strong>Raw JSON</strong> — collapsible raw finding data</li>
            <li><strong>Auto-remediation</strong> — inline remediation script (where available)</li>
          </ul>
          <h3 id="findings-remediation">Remediation progress tracking</h3>
          <p>
            Each finding row has a <strong>Mark fixed</strong> button. Clicking it marks the finding as
            resolved and turns the row semi-transparent. The <strong>Remediation Progress</strong> bar at
            the top of the page updates immediately, showing:
          </p>
          <ul>
            <li>Percentage of findings fixed</li>
            <li>Count of fixed vs. open findings</li>
            <li>A colour-coded bar (red → amber → green as you make progress)</li>
          </ul>
          <p>
            The same status is reflected on the <strong>Dashboard's Remediation Progress panel</strong>.
            Fixed status is stored in <code>localStorage</code> and persists across page refreshes.
            Click a fixed finding's button again to re-open it.
          </p>
          <h3 id="findings-export">Export CSV</h3>
          <p>Click <strong>Export CSV</strong> to download the currently filtered findings as a CSV file.</p>
        </section>

        <!-- ───── Vulnerabilities ───── -->
        <section id="vulnerabilities">
          <h2>Vulnerabilities</h2>
          <p>
            The Vulnerabilities page scans container registries, virtual machines, and native security
            tools for known CVEs and vulnerability assessment findings.
            The check list is fully cloud-specific:
          </p>
          <div class="tabs-wrap">
            <div class="tab-block">
              <div class="tab-head aws">AWS</div>
              <div class="tab-body">
                <ul>
                  <li><strong>ECR Image Scan</strong> — critical/high CVEs in container images via AWS Inspector / ECR scanning.</li>
                  <li><strong>AMI Vulnerability Check</strong> — deprecated AMIs, public AMIs, known-vulnerable image IDs.</li>
                  <li><strong>Amazon Inspector</strong> — Inspector v2 enablement check, EC2 + Lambda + container findings.</li>
                  <li><strong>SSM Patch Compliance</strong> — patch compliance status for SSM-managed EC2 instances.</li>
                </ul>
              </div>
            </div>
            <div class="tab-block">
              <div class="tab-head gcp">Google Cloud</div>
              <div class="tab-body">
                <ul>
                  <li><strong>Artifact Registry Image Scan</strong> — CVEs via Container Analysis.</li>
                  <li><strong>Container Registry CVE Scan</strong> — legacy gcr.io registry vulnerability scan.</li>
                  <li><strong>VM Manager OS Vulnerability Report</strong> — OS-level CVEs on Compute Engine VMs.</li>
                  <li><strong>Security Command Center Findings</strong> — MEDIUM+ vulnerability findings from SCC.</li>
                </ul>
              </div>
            </div>
            <div class="tab-block">
              <div class="tab-head azure">Azure</div>
              <div class="tab-body">
                <ul>
                  <li><strong>Container Registry Image Scan</strong> — CVEs via Defender for Containers.</li>
                  <li><strong>AKS Cluster Node Vulnerabilities</strong> — node OS patches and container CVEs.</li>
                  <li><strong>VM Vulnerability Assessment</strong> — Defender for Cloud VM findings.</li>
                  <li><strong>Defender for Cloud Alerts</strong> — active security alerts at subscription level.</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        <!-- ───── Pentest ───── -->
        <section id="pentest">
          <h2>Pentest</h2>
          <p>
            The Pentest page simulates real-world attack scenarios using your cloud environment's own
            configuration. All check names and descriptions match the selected cloud's terminology.
          </p>
          <div class="tabs-wrap">
            <div class="tab-block">
              <div class="tab-head aws">AWS</div>
              <div class="tab-body">
                <ul>
                  <li><strong>Exposed Services</strong> — Security Groups open on SSH, RDP, database ports to 0.0.0.0/0.</li>
                  <li><strong>Secrets Scan</strong> — hardcoded secrets in Lambda, CodeBuild, EC2 user-data, and local repos.</li>
                  <li><strong>Exploit Mapping</strong> — attack chains: public S3 + IAM wildcard → data exfiltration, SSRF → credential theft.</li>
                  <li><strong>IAM Privilege Escalation</strong> — iam:PassRole, lambda:CreateFunction, sts:AssumeRole on * vectors.</li>
                  <li><strong>Lateral Movement Paths</strong> — shared VPCs, overly permissive egress, cross-account trusts, SSM chains.</li>
                </ul>
              </div>
            </div>
            <div class="tab-block">
              <div class="tab-head gcp">Google Cloud</div>
              <div class="tab-body">
                <ul>
                  <li><strong>Exposed Services</strong> — VPC Firewall Rules with SSH/RDP/DB ports open from 0.0.0.0/0.</li>
                  <li><strong>Secrets Scan</strong> — Cloud Functions/Run env vars, Compute metadata, local repos.</li>
                  <li><strong>Exploit Mapping</strong> — public GCS + service account key, public Cloud SQL, GCE metadata SSRF.</li>
                  <li><strong>IAM Privilege Escalation</strong> — iam.serviceAccounts.actAs, serviceusage.services.enable vectors.</li>
                  <li><strong>GKE Attack Paths</strong> — public API endpoint, legacy ABAC, insecure Workload Identity, privileged pods.</li>
                </ul>
              </div>
            </div>
            <div class="tab-block">
              <div class="tab-head azure">Azure</div>
              <div class="tab-body">
                <ul>
                  <li><strong>Exposed Services</strong> — NSG rules with SSH/RDP/DB ports open from Internet on VMs and AKS nodes.</li>
                  <li><strong>Secrets Scan</strong> — Azure Functions app settings, VM extensions, App Service env vars, local repos.</li>
                  <li><strong>Exploit Mapping</strong> — public blob + Managed Identity, public Azure SQL, Azure AD token via IMDS SSRF.</li>
                  <li><strong>RBAC Privilege Escalation</strong> — Owner/Contributor at subscription scope, no PIM, roleAssignments/write.</li>
                  <li><strong>AKS Attack Paths</strong> — public API, no Azure AD RBAC, pod identity misconfig, no network policy.</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        <!-- ───── Security Checks Reference ───── -->
        <section id="security-checks">
          <h2>Security checks reference</h2>
          <p>
            All checks map to entries in <code>recommendations.js</code> which provides detailed
            remediation guidance for each rule. Below is the full reference grouped by cloud and service.
          </p>

          <h3 id="checks-aws">AWS checks</h3>
          <div class="checks-table">
            <div class="checks-header">
              <span>Rule ID</span><span>Title</span><span>Severity</span>
            </div>
            <div class="checks-row" v-for="r in awsChecks" :key="r.id">
              <code>{{ r.id }}</code><span>{{ r.title }}</span>
              <span class="sev-badge" :class="r.sev">{{ r.sev }}</span>
            </div>
          </div>

          <h3 id="checks-gcp">Google Cloud checks</h3>
          <div class="checks-table">
            <div class="checks-header">
              <span>Rule ID</span><span>Title</span><span>Severity</span>
            </div>
            <div class="checks-row" v-for="r in gcpChecks" :key="r.id">
              <code>{{ r.id }}</code><span>{{ r.title }}</span>
              <span class="sev-badge" :class="r.sev">{{ r.sev }}</span>
            </div>
          </div>

          <h3 id="checks-azure">Azure checks</h3>
          <div class="checks-table">
            <div class="checks-header">
              <span>Rule ID</span><span>Title</span><span>Severity</span>
            </div>
            <div class="checks-row" v-for="r in azureChecks" :key="r.id">
              <code>{{ r.id }}</code><span>{{ r.title }}</span>
              <span class="sev-badge" :class="r.sev">{{ r.sev }}</span>
            </div>
          </div>
        </section>

        <!-- ───── Compliance ───── -->
        <section id="compliance">
          <h2>Compliance</h2>
          <p>
            The Compliance page runs framework-specific checks (CIS Benchmarks, NIST 800-53, ISO 27001, SOC 2, GDPR, PCI-DSS) and optionally produces gap analysis.
          </p>
          <h3 id="compliance-gap">Gap analysis (JSON + Suggestions)</h3>
          <p>
            Select <strong>JSON + Suggestions</strong> as the output format. After the check completes:
          </p>
          <ul>
            <li>A compliance summary strip shows Pass / Fail counts and overall compliance %.</li>
            <li>A <strong>Failed controls — Gap analysis</strong> section lists each failed control with a specific "What to do" recommendation, fix steps, and a docs link.</li>
            <li>A collapsible <strong>Passed controls</strong> section shows what is already compliant.</li>
            <li>A collapsible <strong>Raw JSON response</strong> section is available for integration with other tools.</li>
          </ul>
        </section>

        <!-- ───── Attack Paths ───── -->
        <section id="attack-paths">
          <h2>Attack Paths</h2>
          <p>
            The Attack Paths page visualises chains of weaknesses that could be exploited together for
            maximum impact. Each path shows the entry point, traversal steps, and blast radius.
          </p>
          <p>Example paths that are automatically detected:</p>
          <ul>
            <li><strong>AWS:</strong> Public EC2 with SSRF vulnerability → IMDSv1 enabled → IAM role credentials stolen → S3 buckets exfiltrated.</li>
            <li><strong>GCP:</strong> Public Cloud Function with wildcard service account → Google Cloud Storage bucket read → BigQuery dataset queried.</li>
            <li><strong>Azure:</strong> Public blob container with SAS token → Storage account key exposed → subscription-wide data access.</li>
          </ul>
        </section>

        <!-- ───── Governance ───── -->
        <section id="governance">
          <h2>Governance</h2>
          <p>
            The Governance page runs policy checks for organisational standards such as tagging compliance,
            service enablement, and cost governance best practices. Policy checks are defined in YAML rule files.
          </p>
        </section>

        <!-- ───── Scan History ───── -->
        <section id="scan-history">
          <h2>Scan History</h2>
          <p>
            Every time a Security Scan completes, the result is automatically saved to
            <code>localStorage</code> (up to 100 entries). Access scan history from <strong>Audit → Scan History</strong>.
          </p>
          <ul>
            <li>The table shows: date, cloud, region/project, findings count, risk score, severity breakdown, and status.</li>
            <li>Click any row to open a slide-over with a severity bar chart and full details.</li>
            <li>Use <strong>Clear history</strong> to remove all saved entries (requires confirmation).</li>
          </ul>
        </section>

        <!-- ───── Notifications ───── -->
        <section id="notifications">
          <h2>Notifications</h2>
          <p>
            The Notifications page shows scan completion alerts, finding threshold breaches, and system messages.
            The bell icon in the sidebar header also shows an unread badge when new notifications arrive.
          </p>
        </section>

        <!-- ───── Scheduled Scans ───── -->
        <section id="scheduled-scans">
          <h2>Scheduled Scans</h2>
          <p>
            Create cron-based scan schedules on the Scheduled Scans page. Each schedule specifies a cloud provider,
            region/project, service selection, and cron expression. The scheduler runs scans in the background
            and stores results in scan history automatically.
          </p>
        </section>

        <!-- ───── UI Features ───── -->
        <section id="ui-features">
          <h2>UI features</h2>

          <h3 id="command-palette">Command palette (Ctrl+K)</h3>
          <p>
            Press <kbd>Ctrl+K</kbd> (Windows/Linux) or <kbd>⌘K</kbd> (Mac) anywhere in the app to open the
            global command palette. Type to search all pages and features by name. Use <kbd>↑</kbd> / <kbd>↓</kbd>
            to navigate and <kbd>Enter</kbd> to jump to the selected page.
          </p>

          <h3 id="sidebar">Sidebar</h3>
          <ul>
            <li><strong>Collapse/expand</strong> — click the ‹ / › button to collapse the sidebar to icon-only mode. State is persisted.</li>
            <li><strong>Navigation groups</strong> — click any group header (Security, Audit, etc.) to expand or collapse it. State is persisted.</li>
            <li><strong>Brand logo</strong> — clicking the CloudRadar logo navigates to the Welcome (cloud selection) page.</li>
            <li><strong>User panel</strong> — click the avatar to see the logged-in user name and access the audit log.</li>
          </ul>

          <h3 id="theme">Dark / Light mode</h3>
          <p>
            Click the theme toggle button at the top of the sidebar to switch between dark and light mode.
            The preference is stored in <code>localStorage</code> and applied immediately.
          </p>

          <h3 id="toast">Toast notifications</h3>
          <p>
            Transient toast messages appear in the top-right corner for key events (scan complete, error, etc.).
            Toasts auto-dismiss after 4 seconds. Four variants are available: success (green), error (red),
            warning (amber), and info (blue).
          </p>

          <h3 id="mobile">Mobile support</h3>
          <p>
            On small screens (below 768 px), the sidebar hides and a hamburger menu button (☰) appears
            in the top-left. Tap to open the sidebar as a full-height overlay. Tap the backdrop to close it.
          </p>
        </section>

        <!-- ───── Recommendations Engine ───── -->
        <section id="recommendations-engine">
          <h2>Recommendations engine</h2>
          <p>
            All per-finding recommendations come from <code>src/utils/recommendations.js</code> — a
            centralised lookup table with over <strong>90 rules</strong> covering AWS, Google Cloud, Azure, and CloudFront.
            Each rule includes:
          </p>
          <ul>
            <li><strong>cloud</strong> — the cloud provider (aws / gcp / azure)</li>
            <li><strong>title</strong> — short title of the issue</li>
            <li><strong>what</strong> — plain-English explanation of what the issue is</li>
            <li><strong>why</strong> — security and business impact</li>
            <li><strong>fix</strong> — ordered list of specific remediation steps</li>
            <li><strong>docs</strong> — direct link to official documentation</li>
            <li><strong>severity</strong> — critical / high / medium / low</li>
          </ul>
          <p>
            The engine matches by: (1) exact <code>rule_id</code>, (2) <code>resource_type</code> prefix,
            (3) cloud-prefix wildcard, (4) generic cloud-specific fallback. This means recommendations are
            shown even for custom or unknown rule IDs.
          </p>
          <p>
            The <code>TOP_RECS_BY_CLOUD</code> export provides prioritised rule keys for the Dashboard
            recommendations panel, organised by cloud and severity tier.
          </p>
          <h3 id="recs-quickwin">Quick win flag</h3>
          <p>
            Rules in the lookup table can be marked <code>quickWin: true</code> to indicate they are fast,
            single-step fixes. The Dashboard and post-scan summary card surface these separately in the
            <strong>⚡ Quick Wins</strong> panel. Currently marked as quick wins: CloudFront HTTP allowed,
            CloudFront security headers, CloudFront HSTS, CloudFront logging, CloudFront TLS version,
            and CloudFront geo-restriction.
          </p>
          <h3 id="recs-prioritisation">Prioritised recommendations</h3>
          <p>
            The <code>getPrioritisedRecs()</code> function in <code>remediationStore.js</code> groups
            unfixed findings by <code>rule_id</code> and sorts them by <strong>severity weight × occurrence count</strong>.
            A rule affecting 5 resources ranks above a rule affecting 1 resource of the same severity.
            This ensures the most impactful actions appear at the top of both the Dashboard and post-scan summary.
          </p>
        </section>

        <!-- ───── Built-in Tests ───── -->
        <section id="tests">
          <h2>Built-in tests</h2>
          <p>
            CloudRadar ships with a full built-in test suite you can run directly from the UI — no terminal required.
            Navigate to <strong>Tests</strong> in the sidebar. Tests validate the application's own logic
            using synthetic data and mocked AWS APIs, so <strong>no real cloud credentials are needed</strong>.
            They are completely independent of any running scan.
          </p>
          <div class="info-box">
            <strong>Before going to production:</strong> run all 9 test suites and confirm you see a
            green "✓ All tests passed" banner. If any test fails, check the terminal output for the exact failure before deploying.
          </div>

          <h3 id="tests-how">How to run tests</h3>
          <ol>
            <li>Click <strong>Tests</strong> in the sidebar (under Audit).</li>
            <li>All 9 suites are pre-selected. Deselect individual suites if you only want to test a subset.</li>
            <li>Click <strong>Run Tests</strong>.</li>
            <li>Watch the live terminal output stream in real time — green ✓ for passed, red ✗ for failed.</li>
            <li>A summary badge bar shows total passed / failed / errors / skipped counts.</li>
            <li>A result banner at the bottom confirms the final outcome.</li>
          </ol>

          <h3 id="tests-suites">Test suites (9 total)</h3>
          <div class="checks-table">
            <div class="checks-header"><span>Suite</span><span>What it validates</span><span>Method</span></div>
            <div class="checks-row" v-for="t in testSuites" :key="t.name">
              <code>{{ t.name }}</code>
              <span>{{ t.desc }}</span>
              <span class="sev-badge medium">{{ t.method }}</span>
            </div>
          </div>

          <h3 id="tests-technical">How it works (technical detail)</h3>
          <p>When you click Run Tests, the frontend sends:</p>
          <ol>
            <li><code>POST /api/tests/run</code> with the list of selected test modules → backend returns a <code>job_id</code>.</li>
            <li>The backend spawns a background thread that runs <code>pytest -v --tb=short</code> as a subprocess.</li>
            <li>Before running, dummy AWS credentials (<code>AWS_ACCESS_KEY_ID=testing</code> etc.) are injected into the subprocess environment so moto-based tests work without real keys.</li>
            <li>stdout is streamed line by line and each line is parsed: <code>PASSED</code> / <code>FAILED</code> / <code>ERROR</code> / <code>SKIPPED</code> lines become structured events.</li>
            <li>Events are pushed via Server-Sent Events (<code>GET /api/tests/&lt;job_id&gt;/events</code>) to the frontend in real time. A polling fallback (<code>GET /api/tests/&lt;job_id&gt;</code> every 1.5s) handles environments where SSE is blocked by a proxy.</li>
          </ol>

          <h3 id="tests-isolation">Test isolation</h3>
          <ul>
            <li>Tests use their own separate job store and SSE queues — they share no state with scan jobs.</li>
            <li>Running tests while a scan is in progress is safe.</li>
            <li>Tests that interact with AWS (S3 scanner, Remediation Engine) use <strong>moto</strong> to mock all AWS API calls — nothing touches real infrastructure.</li>
            <li>API endpoint tests use FastAPI's built-in <code>TestClient</code> (backed by httpx) — no running server needed.</li>
          </ul>

          <h3 id="tests-new-suite">Adding a new test suite</h3>
          <ol>
            <li>Create <code>tests/test_my_feature.py</code> with standard <code>pytest</code> functions.</li>
            <li>Register it in <code>cspm/ui/test_runner.py</code> under <code>_ALL_TEST_FILES</code>:<br/>
              <code>"test_my_feature": "My Feature Name"</code>
            </li>
            <li>Add its description to the <code>FALLBACK_TESTS</code> array in <code>Tests.vue</code> — it will appear in the UI automatically.</li>
          </ol>
        </section>

        <!-- ───── API / Backend ───── -->
        <section id="api">
          <h2>Backend API</h2>
          <p>The Python backend exposes a REST API consumed by the Vue.js frontend:</p>
          <div class="api-table">
            <div class="api-row header"><span>Method</span><span>Path</span><span>Description</span></div>
            <div class="api-row" v-for="ep in apiEndpoints" :key="ep.path">
              <span class="method-badge" :class="ep.method.toLowerCase()">{{ ep.method }}</span>
              <code>{{ ep.path }}</code>
              <span>{{ ep.desc }}</span>
            </div>
          </div>
          <h3 id="api-scan-flow">Scan job flow</h3>
          <ol>
            <li><code>POST /api/scan</code> → returns <code>{ job_id }</code></li>
            <li>Frontend subscribes to <code>GET /api/scan/&lt;job_id&gt;/stream</code> (SSE) for real-time step events.</li>
            <li>As fallback, frontend polls <code>GET /api/scan/&lt;job_id&gt;</code> every 1.5 seconds.</li>
            <li>On completion, the scan result includes <code>summary</code> and <code>downloads</code>.</li>
          </ol>
        </section>

        <!-- ───── Changelog ───── -->
        <section id="changelog">
          <h2>Changelog</h2>
          <div class="changelog-entry">
            <div class="cl-version">v2.4</div>
            <ul>
              <li>CloudFront security scanner — 8 new checks: HTTP allowed, no WAF, outdated TLS, missing security headers, HSTS, S3 origin without OAC, logging disabled, geo-restriction</li>
              <li>8 CloudFront recommendations added to recommendations.js with full what/why/fix/docs</li>
              <li>3 new test suites: <code>test_cloudfront_scanner</code> (no AWS credentials needed), <code>test_risk_engine</code>, <code>test_api_endpoints</code></li>
              <li>Total test suites: 6 → 9; registered in test runner UI automatically</li>
              <li>Prioritised recommendations: Dashboard and post-scan summary now rank recs by severity × number of affected resources from actual scan findings</li>
              <li>⚡ Quick Wins panel on Dashboard and post-scan summary card — low-effort, high-impact fixes surfaced separately</li>
              <li>Remediation Progress Tracker: mark any finding as fixed, watch progress bar and risk score update on Findings page and Dashboard</li>
              <li>remediationStore.js utility: markFixed, unmarkFixed, isFixed, computeRemediationScore, getPrioritisedRecs, getQuickWins — all persisted to localStorage</li>
              <li>CloudFront added to AWS services list (31 total), checks reference table, and documentation</li>
              <li>Documentation: new Tests section with full suite reference, how-to, technical detail, and "adding a new suite" guide</li>
            </ul>
          </div>
          <div class="changelog-entry">
            <div class="cl-version">v2.3</div>
            <ul>
              <li>Cloud-aware service lists on Security Scan (AWS 30, GCP 23, Azure 23 services)</li>
              <li>Cloud-aware vulnerability checks on Vulnerabilities page (AWS / GCP / Azure)</li>
              <li>Cloud-aware pentest checks on Pentest page with correct cloud terminology</li>
              <li>Added 30+ new security checks: Cognito, AWS Config, Backup, Redshift, ElastiCache, OpenSearch, Route 53, Secrets Manager, CodeBuild, CloudFormation, BigQuery, Cloud DNS, Secret Manager, Cloud Run, App Service, Redis Cache, Log Analytics, Cosmos DB, Service Bus, ACR</li>
              <li>Expanded TOP_RECS_BY_CLOUD with new rules for all three clouds</li>
              <li>Updated documentation to cover all new features</li>
            </ul>
          </div>
          <div class="changelog-entry">
            <div class="cl-version">v2.2</div>
            <ul>
              <li>Multi-cloud Dashboard with Chart.js charts (donut, line, bar)</li>
              <li>Dashboard cloud tabs for AWS, Google Cloud, Azure</li>
              <li>Top 5 recommendations panel on Dashboard (per-cloud)</li>
              <li>Documentation fully updated for all features</li>
            </ul>
          </div>
          <div class="changelog-entry">
            <div class="cl-version">v2.1</div>
            <ul>
              <li>Scan History page with slide-over details and severity bar chart</li>
              <li>Findings detail slide-over panel with per-finding recommendations</li>
              <li>Global Ctrl+K command palette</li>
              <li>Toast notification system</li>
              <li>Post-scan structured summary card</li>
              <li>Compliance gap analysis (JSON + Suggestions mode)</li>
              <li>Mobile sidebar hamburger menu</li>
              <li>Per-finding recommendation engine (80+ rules for AWS / GCP / Azure)</li>
            </ul>
          </div>
          <div class="changelog-entry">
            <div class="cl-version">v2.0</div>
            <ul>
              <li>Persistent Dashboard tab in sidebar navigation</li>
              <li>Collapsible/expandable sidebar navigation groups</li>
              <li>Sidebar collapse/expand to icon-only mode</li>
              <li>User login details, avatar, and audit log</li>
              <li>Brand logo navigates to Welcome (cloud selection) page</li>
              <li>Glassmorphism applied to service cards</li>
              <li>Dark / light mode theme toggle</li>
            </ul>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const showFab = ref(false)

function onScroll() {
  showFab.value = (document.documentElement.scrollTop || document.body.scrollTop) > 300
}
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))

const toc = [
  { id: 'overview',               label: 'Overview' },
  { id: 'getting-started',        label: 'Getting started' },
  { id: 'cloud-setup',            label: '  Cloud credentials setup', sub: true },
  { id: 'first-scan',             label: '  First scan', sub: true },
  { id: 'dashboard',              label: 'Dashboard' },
  { id: 'dashboard-clouds',       label: '  Multi-cloud tabs', sub: true },
  { id: 'dashboard-charts',       label: '  Charts', sub: true },
  { id: 'dashboard-recs',         label: '  Top recommendations', sub: true },
  { id: 'dashboard-quickwins',    label: '  Quick Wins panel', sub: true },
  { id: 'dashboard-remediation',  label: '  Remediation Progress', sub: true },
  { id: 'security-scan',          label: 'Security Scan' },
  { id: 'scan-aws',               label: '  AWS services (31)', sub: true },
  { id: 'scan-gcp',               label: '  Google Cloud services', sub: true },
  { id: 'scan-azure',             label: '  Azure services', sub: true },
  { id: 'scan-summary',           label: '  Post-scan summary card', sub: true },
  { id: 'findings',               label: 'Findings' },
  { id: 'findings-slideover',     label: '  Slide-over panel', sub: true },
  { id: 'findings-remediation',   label: '  Remediation tracking', sub: true },
  { id: 'vulnerabilities',        label: 'Vulnerabilities' },
  { id: 'pentest',                label: 'Pentest' },
  { id: 'security-checks',        label: 'Security checks reference' },
  { id: 'checks-aws',             label: '  AWS checks (incl. CloudFront)', sub: true },
  { id: 'checks-gcp',             label: '  Google Cloud checks', sub: true },
  { id: 'checks-azure',           label: '  Azure checks', sub: true },
  { id: 'compliance',             label: 'Compliance & gap analysis' },
  { id: 'attack-paths',           label: 'Attack Paths' },
  { id: 'governance',             label: 'Governance' },
  { id: 'scan-history',           label: 'Scan History' },
  { id: 'notifications',          label: 'Notifications' },
  { id: 'scheduled-scans',        label: 'Scheduled Scans' },
  { id: 'tests',                  label: 'Built-in tests' },
  { id: 'tests-how',              label: '  How to run tests', sub: true },
  { id: 'tests-suites',           label: '  Test suites (9)', sub: true },
  { id: 'tests-technical',        label: '  Technical detail', sub: true },
  { id: 'tests-new-suite',        label: '  Adding a new suite', sub: true },
  { id: 'ui-features',            label: 'UI features' },
  { id: 'command-palette',        label: '  Command palette (Ctrl+K)', sub: true },
  { id: 'sidebar',                label: '  Sidebar', sub: true },
  { id: 'toast',                  label: '  Toast notifications', sub: true },
  { id: 'mobile',                 label: '  Mobile support', sub: true },
  { id: 'recommendations-engine', label: 'Recommendations engine' },
  { id: 'recs-quickwin',          label: '  Quick win flag', sub: true },
  { id: 'recs-prioritisation',    label: '  Prioritised recommendations', sub: true },
  { id: 'api',                    label: 'Backend API' },
  { id: 'changelog',              label: 'Changelog' },
]

const testSuites = [
  { name: 'test_rule_engine',        desc: 'Security rule operators (true/false, equals, gt, in, not_in) fire correctly, finding fields are accurate, only non-compliant assets are flagged.', method: 'Unit' },
  { name: 'test_s3_scanner',         desc: 'S3 bucket scanner: encryption disabled, public-access-block, multiple mixed buckets. Uses moto to mock AWS S3 API calls.', method: 'moto (mock AWS)' },
  { name: 'test_compliance',         desc: 'All compliance frameworks (CIS, SOC2, HIPAA, PCI DSS, ISO 27001) map findings to controls correctly, detect failures, and produce valid JSON reports.', method: 'Unit' },
  { name: 'test_remediation',        desc: 'Auto-remediation: S3 encryption dry-run, live apply, idempotent re-apply, public-access-block, missing resource_id, unsupported resource type. Uses moto.', method: 'moto (mock AWS)' },
  { name: 'test_attack_paths',       desc: 'Attack path graph construction: empty graph returns no paths, future path chain tests as the graph engine grows.', method: 'Unit' },
  { name: 'test_scanners',           desc: 'Integration tests for rule engine, asset catalog build/filter, risk engine, snapshot manager, change detector, tag policy engine, pentest exposed services, and exploit mapping.', method: 'Unit' },
  { name: 'test_cloudfront_scanner', desc: 'All 8 CloudFront rules: HTTP allowed, no WAF, outdated TLS, missing security headers, HSTS missing, S3 origin without OAC, logging disabled, no geo-restriction. Edge cases: empty list, perfectly secure dist, multi-dist isolation, required fields.', method: 'Unit (no AWS needed)' },
  { name: 'test_risk_engine',        desc: 'Risk score computation: per-severity weights, multi-finding accumulation, case-insensitive severity, unknown/missing severity handling, large input sets. risk_summary() report helper output validation.', method: 'Unit' },
  { name: 'test_api_endpoints',      desc: 'FastAPI routes: /api/health, /api/status, /api/setup (AWS/GCP/Azure input validation), /api/tests/list, /api/tests/run, /api/tests/{job_id} (status polling + 404 for unknown jobs), /api/findings, /api/summary.', method: 'TestClient (httpx)' },
]

const awsServices = [
  'EC2', 'S3', 'RDS', 'Lambda', 'IAM', 'Security Groups', 'Load Balancers (ALB)',
  'WAF', 'CloudTrail', 'VPC', 'EBS Volumes', 'EKS', 'ECS', 'KMS', 'API Gateway',
  'SQS', 'DynamoDB', 'GuardDuty', 'CloudWatch', 'ECR', 'Cognito', 'AWS Config',
  'AWS Backup', 'Redshift', 'ElastiCache', 'OpenSearch', 'Route 53',
  'Secrets Manager', 'CodeBuild', 'CloudFormation', 'CloudFront',
]

const gcpServices = [
  'Compute Engine', 'Cloud Storage', 'Cloud SQL', 'Cloud Functions', 'IAM & Admin',
  'VPC Firewall Rules', 'Cloud Load Balancing', 'Cloud Armor', 'Cloud Audit Logs',
  'VPC Networks', 'Persistent Disks', 'GKE', 'Cloud Run', 'Cloud KMS', 'API Gateway',
  'Pub/Sub', 'Firestore / Datastore', 'Security Command Center', 'Cloud Monitoring',
  'Artifact Registry', 'BigQuery', 'Cloud DNS', 'Secret Manager',
]

const azureServices = [
  'Virtual Machines', 'Storage Accounts', 'Azure SQL', 'Azure Functions',
  'Azure AD & RBAC', 'Network Security Groups', 'Application Gateway', 'Azure WAF',
  'Azure Monitor', 'Virtual Networks', 'Managed Disks', 'AKS', 'Container Instances',
  'Key Vault', 'API Management', 'Service Bus', 'Cosmos DB', 'Defender for Cloud',
  'Azure Alerts / Sentinel', 'Container Registry', 'App Service', 'Log Analytics',
  'Azure Cache for Redis',
]

const awsChecks = [
  { id: 'ec2.public_ip',                        title: 'EC2 Instance Has Public IP',                     sev: 'medium' },
  { id: 'ec2.vulnerable_ami',                   title: 'EC2 Using Vulnerable or Deprecated AMI',         sev: 'high' },
  { id: 's3.public_access',                     title: 'S3 Bucket Publicly Accessible',                  sev: 'critical' },
  { id: 's3.no_encryption',                     title: 'S3 Bucket Not Encrypted at Rest',                sev: 'high' },
  { id: 'rds.publicly_accessible',              title: 'RDS Publicly Accessible',                        sev: 'critical' },
  { id: 'rds.no_encryption',                    title: 'RDS Storage Not Encrypted',                      sev: 'high' },
  { id: 'lambda.hardcoded_secret',              title: 'Lambda — Hardcoded Secret in Env Var',           sev: 'critical' },
  { id: 'iam.wildcard_action',                  title: 'IAM Policy Allows Wildcard Action',              sev: 'critical' },
  { id: 'iam.unused_keys',                      title: 'IAM User Has Unused Access Keys',                sev: 'high' },
  { id: 'iam.no_mfa',                           title: 'IAM User Has No MFA',                            sev: 'high' },
  { id: 'iam.password_policy_weak',             title: 'IAM Password Policy Too Weak',                   sev: 'medium' },
  { id: 'sg.ssh_open',                          title: 'Security Group Allows SSH from 0.0.0.0/0',       sev: 'critical' },
  { id: 'sg.rdp_open',                          title: 'Security Group Allows RDP from 0.0.0.0/0',       sev: 'critical' },
  { id: 'cloudtrail.disabled',                  title: 'CloudTrail Not Enabled',                         sev: 'critical' },
  { id: 'cloudtrail.no_log_validation',         title: 'CloudTrail Log File Validation Disabled',        sev: 'high' },
  { id: 'vpc.no_flow_logs',                     title: 'VPC Flow Logs Not Enabled',                      sev: 'medium' },
  { id: 'ebs.no_encryption',                    title: 'EBS Volume Not Encrypted',                       sev: 'high' },
  { id: 'eks.public_endpoint',                  title: 'EKS API Server Has Public Endpoint',             sev: 'high' },
  { id: 'kms.no_rotation',                      title: 'KMS Key Rotation Not Enabled',                   sev: 'medium' },
  { id: 'alb.no_waf',                           title: 'ALB Has No WAF Web ACL',                         sev: 'medium' },
  { id: 'guardduty.disabled',                   title: 'GuardDuty Not Enabled',                          sev: 'high' },
  { id: 'ecr.critical_cve',                     title: 'ECR Image Has Critical CVE',                     sev: 'critical' },
  { id: 'cognito.no_mfa',                       title: 'Cognito User Pool — MFA Not Required',           sev: 'high' },
  { id: 'cognito.no_advanced_security',         title: 'Cognito Advanced Security Mode Disabled',        sev: 'medium' },
  { id: 'cognito.weak_password_policy',         title: 'Cognito User Pool Has Weak Password Policy',     sev: 'medium' },
  { id: 'config.recorder_disabled',             title: 'AWS Config Recorder Not Enabled',                sev: 'high' },
  { id: 'backup.no_plan',                       title: 'No AWS Backup Plan Configured',                  sev: 'high' },
  { id: 'redshift.publicly_accessible',         title: 'Redshift Cluster Publicly Accessible',           sev: 'critical' },
  { id: 'redshift.no_encryption',               title: 'Redshift Cluster Not Encrypted',                 sev: 'high' },
  { id: 'redshift.no_audit_logging',            title: 'Redshift Audit Logging Disabled',                sev: 'medium' },
  { id: 'elasticache.no_auth',                  title: 'ElastiCache Redis — No AUTH Token',              sev: 'critical' },
  { id: 'elasticache.no_tls',                   title: 'ElastiCache — In-Transit Encryption Disabled',   sev: 'high' },
  { id: 'opensearch.public_endpoint',           title: 'OpenSearch Domain Has Public Endpoint',          sev: 'critical' },
  { id: 'opensearch.no_encryption_at_rest',     title: 'OpenSearch Domain Not Encrypted at Rest',        sev: 'high' },
  { id: 'route53.dangling_dns',                 title: 'Route 53 — Dangling DNS Record',                 sev: 'high' },
  { id: 'route53.zone_transfer',                title: 'Route 53 Zone Transfer Allowed',                 sev: 'medium' },
  { id: 'secretsmanager.no_rotation',           title: 'Secrets Manager — Rotation Disabled',            sev: 'high' },
  { id: 'secretsmanager.stale_secret',          title: 'Secrets Manager — Secret Not Accessed 180d+',   sev: 'medium' },
  { id: 'codebuild.no_logging',                 title: 'CodeBuild Project — Logging Disabled',           sev: 'medium' },
  { id: 'codebuild.privileged_mode',            title: 'CodeBuild Project — Privileged Mode Enabled',   sev: 'high' },
  { id: 'cloudformation.no_termination_protection', title: 'CloudFormation — Termination Protection Off', sev: 'medium' },
  // CloudFront
  { id: 'cf.http_allowed',               title: 'CloudFront Distribution Allows Plain HTTP',              sev: 'high' },
  { id: 'cf.no_waf',                     title: 'CloudFront Distribution Has No WAF Web ACL',             sev: 'high' },
  { id: 'cf.outdated_tls',               title: 'CloudFront Distribution Uses Outdated TLS Protocol',     sev: 'high' },
  { id: 'cf.s3_origin_no_oac',           title: 'CloudFront S3 Origin Without Origin Access Control',     sev: 'high' },
  { id: 'cf.missing_security_headers',   title: 'CloudFront Distribution Missing Security Headers',       sev: 'medium' },
  { id: 'cf.no_hsts',                    title: 'CloudFront HSTS Header Not Configured',                  sev: 'medium' },
  { id: 'cf.logging_disabled',           title: 'CloudFront Access Logging Disabled',                     sev: 'medium' },
  { id: 'cf.no_geo_restriction',         title: 'CloudFront Distribution Has No Geo-Restriction',         sev: 'low' },
]

const gcpChecks = [
  { id: 'gcp.compute.public_ip',          title: 'Compute Engine — Public IP Assigned',               sev: 'medium' },
  { id: 'gcp.storage.public_bucket',      title: 'Cloud Storage Bucket Publicly Accessible',          sev: 'critical' },
  { id: 'gcp.storage.no_versioning',      title: 'Cloud Storage Bucket Versioning Disabled',          sev: 'medium' },
  { id: 'gcp.iam.service_account_key',    title: 'Service Account — User-Managed Key',                sev: 'high' },
  { id: 'gcp.iam.primitive_roles',        title: 'Primitive IAM Roles (Owner/Editor) In Use',         sev: 'high' },
  { id: 'gcp.iam.no_mfa',                 title: 'User Without 2-Step Verification',                  sev: 'critical' },
  { id: 'gcp.firewall.ssh_open',          title: 'Firewall Rule Allows SSH from 0.0.0.0/0',           sev: 'critical' },
  { id: 'gcp.firewall.rdp_open',          title: 'Firewall Rule Allows RDP from 0.0.0.0/0',           sev: 'critical' },
  { id: 'gcp.sql.public_ip',              title: 'Cloud SQL — Public IP Enabled',                     sev: 'high' },
  { id: 'gcp.gke.public_endpoint',        title: 'GKE API Server Has Public Endpoint',                sev: 'high' },
  { id: 'gcp.logging.disabled',           title: 'Cloud Audit Logging Disabled',                      sev: 'critical' },
  { id: 'gcp.kms.no_rotation',            title: 'Cloud KMS Key — No Auto-Rotation',                  sev: 'medium' },
  { id: 'gcp.vpc.no_flow_logs',           title: 'VPC Subnet — Flow Logs Disabled',                   sev: 'medium' },
  { id: 'gcp.monitoring.no_alerts',       title: 'Cloud Monitoring — No Alert Policies',              sev: 'high' },
  { id: 'gcp.compute.os_not_patched',     title: 'Compute Engine VM — OS Not Patched',                sev: 'high' },
  { id: 'gcp.bigquery.public_dataset',    title: 'BigQuery Dataset Publicly Accessible',              sev: 'critical' },
  { id: 'gcp.bigquery.no_cmek',           title: 'BigQuery Dataset Not Using CMEK',                   sev: 'medium' },
  { id: 'gcp.dns.dnssec_disabled',        title: 'Cloud DNS — DNSSEC Disabled',                      sev: 'medium' },
  { id: 'gcp.secretmanager.no_rotation',  title: 'Secret Manager — No Rotation Policy',               sev: 'medium' },
  { id: 'gcp.cloudrun.public_access',     title: 'Cloud Run — Unauthenticated Invocation Allowed',   sev: 'high' },
]

const azureChecks = [
  { id: 'azure.vm.public_ip',                   title: 'VM — Public IP Directly Assigned',                 sev: 'medium' },
  { id: 'azure.vm.no_disk_encryption',          title: 'VM — OS/Data Disk Not Encrypted',                  sev: 'high' },
  { id: 'azure.vm.no_mde',                      title: 'VM — Defender for Endpoint Not Deployed',          sev: 'high' },
  { id: 'azure.storage.public_blob',            title: 'Storage Account — Public Blob Access Enabled',     sev: 'critical' },
  { id: 'azure.storage.no_https',               title: 'Storage Account — HTTP Connections Allowed',       sev: 'high' },
  { id: 'azure.storage.no_cmk',                 title: 'Storage Account — Not Using CMK',                  sev: 'medium' },
  { id: 'azure.iam.no_mfa',                     title: 'Azure AD User — MFA Not Enabled',                  sev: 'critical' },
  { id: 'azure.iam.excessive_permissions',      title: 'User/SP Has Excessive RBAC Permissions',           sev: 'critical' },
  { id: 'azure.nsg.ssh_open',                   title: 'NSG — SSH Allowed from Internet',                  sev: 'critical' },
  { id: 'azure.nsg.rdp_open',                   title: 'NSG — RDP Allowed from Internet',                  sev: 'critical' },
  { id: 'azure.sql.public_access',              title: 'Azure SQL — Public Network Access Enabled',        sev: 'critical' },
  { id: 'azure.sql.no_auditing',                title: 'Azure SQL — Auditing Disabled',                    sev: 'high' },
  { id: 'azure.sql.no_tde',                     title: 'Azure SQL — TDE with CMK Not Configured',          sev: 'medium' },
  { id: 'azure.keyvault.no_expiry',             title: 'Key Vault — Key/Secret Without Expiry Date',       sev: 'high' },
  { id: 'azure.monitor.no_logs',                title: 'Azure Monitor — Activity Log Diagnostics Missing', sev: 'high' },
  { id: 'azure.aks.public_endpoint',            title: 'AKS API Server Has Public Endpoint',               sev: 'high' },
  { id: 'azure.aks.rbac_disabled',              title: 'RBAC Disabled on AKS Cluster',                     sev: 'high' },
  { id: 'azure.defender.not_enabled',           title: 'Defender for Cloud Plan Not Enabled',              sev: 'high' },
  { id: 'azure.appservice.http_allowed',        title: 'App Service — HTTP Not Redirected to HTTPS',       sev: 'high' },
  { id: 'azure.appservice.remote_debugging',    title: 'App Service — Remote Debugging Enabled',           sev: 'high' },
  { id: 'azure.appservice.no_managed_identity', title: 'App Service — No Managed Identity',                sev: 'medium' },
  { id: 'azure.redis.non_ssl_port',             title: 'Azure Cache for Redis — Non-SSL Port Enabled',     sev: 'high' },
  { id: 'azure.loganalytics.short_retention',   title: 'Log Analytics — Short Retention Period',           sev: 'medium' },
  { id: 'azure.cosmosdb.public_endpoint',       title: 'Cosmos DB — Public Network Access Enabled',        sev: 'high' },
  { id: 'azure.cosmosdb.local_auth',            title: 'Cosmos DB — Local Authentication Not Disabled',    sev: 'high' },
  { id: 'azure.servicebus.no_cmk',              title: 'Service Bus — No Customer-Managed Key',            sev: 'medium' },
  { id: 'azure.acr.admin_enabled',              title: 'Container Registry — Admin Account Enabled',       sev: 'high' },
]

const apiEndpoints = [
  { method: 'POST', path: '/api/scan',                   desc: 'Start a new security scan job' },
  { method: 'GET',  path: '/api/scan/<job_id>',          desc: 'Poll scan job status and results' },
  { method: 'GET',  path: '/api/scan/<job_id>/stream',   desc: 'SSE stream of real-time scan step events' },
  { method: 'GET',  path: '/api/findings',               desc: 'Get latest findings (optionally filtered)' },
  { method: 'POST', path: '/api/compliance',             desc: 'Run compliance framework checks' },
  { method: 'GET',  path: '/api/attack-paths',           desc: 'Get detected attack paths' },
  { method: 'POST', path: '/api/vulnerabilities',        desc: 'Run vulnerability checks' },
  { method: 'POST', path: '/api/pentest',                desc: 'Run pentest / exploit mapping checks' },
  { method: 'GET',  path: '/api/notifications',          desc: 'Get recent notifications' },
  { method: 'GET',  path: '/api/scheduler',              desc: 'List scheduled scans' },
  { method: 'POST', path: '/api/scheduler',              desc: 'Create a scheduled scan' },
]
</script>

<style scoped>
.docs-root { padding: 0; }
.docs-layout { display: flex; gap: 0; align-items: flex-start; }

/* TOC sidebar */
.docs-toc {
  position: sticky; top: 0; width: 210px; min-width: 210px;
  height: 100vh; overflow-y: auto; padding: 28px 0 28px 4px;
  border-right: 1px solid var(--border); flex-shrink: 0;
}
.toc-title {
  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--text-muted); padding: 0 16px 10px;
}
.toc-link {
  display: block; padding: 4px 16px; font-size: 0.81rem;
  color: var(--text-muted); text-decoration: none; border-radius: 5px;
  transition: color 0.13s, background 0.13s; white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis; line-height: 1.6;
}
.toc-link:hover { color: var(--text); background: rgba(255,255,255,0.05); }
.toc-sub { padding-left: 26px; font-size: 0.78rem; }

/* Content area */
.docs-content { flex: 1; min-width: 0; padding: 32px 40px 60px; max-width: 900px; }
.docs-content section { margin-bottom: 48px; }
.docs-content h1 { font-size: 2rem; margin-bottom: 10px; }
.docs-content h2 { font-size: 1.35rem; margin: 36px 0 12px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
.docs-content h3 { font-size: 1.05rem; margin: 22px 0 8px; color: var(--text); }
.docs-content p { margin-bottom: 12px; line-height: 1.7; color: var(--text-muted); }
.docs-content p.lead { font-size: 1.05rem; color: var(--text); }
.docs-content ul, .docs-content ol { padding-left: 22px; margin-bottom: 12px; }
.docs-content li { line-height: 1.7; color: var(--text-muted); margin-bottom: 3px; }
.docs-content li strong { color: var(--text); }
.docs-content code {
  background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.2);
  padding: 1px 6px; border-radius: 4px; font-size: 0.85em; color: #a5b4fc;
}

kbd {
  background: rgba(255,255,255,0.08); border: 1px solid var(--border);
  padding: 2px 7px; border-radius: 4px; font-size: 0.82em;
  font-family: monospace; color: var(--text);
}

.info-box {
  background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.25);
  border-radius: 10px; padding: 12px 16px; margin: 14px 0;
  font-size: 0.9rem; color: var(--text-muted); line-height: 1.6;
}
.info-box strong { color: var(--text); }

/* Cloud tabs */
.tabs-wrap { display: flex; flex-direction: column; gap: 10px; margin: 12px 0; }
.tab-block { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.tab-head {
  padding: 8px 16px; font-size: 0.82rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.06em;
}
.tab-head.aws   { background: rgba(255,153,0,0.1);  color: #fb923c; }
.tab-head.gcp   { background: rgba(66,133,244,0.1); color: #60a5fa; }
.tab-head.azure { background: rgba(0,120,212,0.1);  color: #93c5fd; }
.tab-body { padding: 10px 16px; }
.tab-body ul, .tab-body ol { margin: 0; padding-left: 20px; }
.tab-body li { font-size: 0.88rem; }

/* Service chips */
.service-grid { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 16px; }
.svc-chip {
  background: rgba(255,153,0,0.1); border: 1px solid rgba(255,153,0,0.25);
  color: #fb923c; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 500;
}
.svc-chip.gcp   { background: rgba(66,133,244,0.1); border-color: rgba(66,133,244,0.3); color: #60a5fa; }
.svc-chip.azure { background: rgba(0,120,212,0.1);  border-color: rgba(0,120,212,0.3);  color: #93c5fd; }

/* Checks table */
.checks-table { margin: 8px 0 20px; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.checks-header, .checks-row {
  display: grid; grid-template-columns: 2fr 3fr 80px;
  padding: 7px 14px; gap: 12px; align-items: center; font-size: 0.83rem;
}
.checks-header { font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; background: rgba(255,255,255,0.03); color: var(--text-muted); }
.checks-row { border-top: 1px solid var(--border); }
.checks-row code { font-size: 0.78rem; }
.checks-row span:nth-child(2) { color: var(--text-muted); }

/* API table */
.api-table { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; margin: 10px 0 20px; }
.api-row { display: grid; grid-template-columns: 70px 2fr 3fr; gap: 12px; padding: 7px 14px; font-size: 0.83rem; align-items: center; }
.api-row.header { font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; background: rgba(255,255,255,0.03); color: var(--text-muted); }
.api-row + .api-row { border-top: 1px solid var(--border); }
.method-badge { font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; }
.method-badge.get  { background: rgba(16,185,129,0.15); color: #34d399; }
.method-badge.post { background: rgba(99,102,241,0.15); color: #a5b4fc; }
.api-row span:last-child { color: var(--text-muted); }

/* Severity badges */
.sev-badge { font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; text-transform: uppercase; display: inline-block; }
.sev-badge.critical { background: rgba(239,68,68,0.15); color: #f87171; }
.sev-badge.high     { background: rgba(249,115,22,0.15); color: #fb923c; }
.sev-badge.medium   { background: rgba(234,179,8,0.15);  color: #fbbf24; }
.sev-badge.low      { background: rgba(59,130,246,0.15); color: #60a5fa; }

/* Changelog */
.changelog-entry { margin-bottom: 24px; }
.cl-version {
  font-size: 0.82rem; font-weight: 700; letter-spacing: 0.05em;
  color: #a5b4fc; margin-bottom: 6px;
}

/* Floating back to contents button */
.fab-contents {
  position: fixed; bottom: 28px; right: 28px; z-index: 200;
  display: inline-flex; align-items: center; gap: 7px;
  padding: 10px 18px; border-radius: 30px;
  background: rgba(99,102,241,0.9); color: #fff;
  border: 1px solid rgba(99,102,241,0.6);
  font-size: 0.84rem; font-weight: 600; cursor: pointer;
  box-shadow: 0 4px 20px rgba(0,0,0,0.35);
  backdrop-filter: blur(8px);
  transition: opacity 0.18s, transform 0.18s;
}
.fab-contents:hover { opacity: 0.88; transform: translateY(-2px); }
.fab-fade-enter-active, .fab-fade-leave-active { transition: opacity 0.22s, transform 0.22s; }
.fab-fade-enter-from, .fab-fade-leave-to { opacity: 0; transform: translateY(12px); }

@media (max-width: 800px) {
  .docs-toc { display: none; }
  .docs-content { padding: 20px 16px; }
  .checks-header, .checks-row { grid-template-columns: 1fr 1fr 60px; }
  .api-row { grid-template-columns: 60px 1fr 1.5fr; }
  .fab-contents { bottom: 16px; right: 16px; padding: 9px 14px; font-size: 0.8rem; }
}
</style>
