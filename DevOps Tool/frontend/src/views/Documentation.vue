<template>
  <div class="doc-page">
    <h1>Documentation</h1>
    <p class="doc-intro">
      Complete reference for CloudRadar — from first-time setup to running every scan, report, and test.
      Use the table of contents to jump to a section.
    </p>

    <!-- TOC -->
    <nav class="doc-toc">
      <a href="#getting-started">Getting started</a>
      <a href="#cloud-selection">Cloud selection</a>
      <a href="#setup">Setup &amp; credentials</a>
      <a href="#security">Security — Full scan</a>
      <a href="#vulnerabilities">Security — Vulnerabilities</a>
      <a href="#audit">Audit</a>
      <a href="#compliance">Compliance</a>
      <a href="#governance">Governance</a>
      <a href="#pentest">Pentest</a>
      <a href="#tests">Tests</a>
      <a href="#hosting">Running locally &amp; on a server</a>
    </nav>

    <!-- Getting started -->
    <section class="doc-section" id="getting-started">
      <h2>Getting started</h2>
      <p>
        <strong>CloudRadar</strong> is a multi-cloud Security &amp; Cloud Security Posture Management (CSPM) tool.
        It discovers resources in AWS, Google Cloud, and Azure; runs security rules and compliance checks;
        and produces findings, reports, and pentest output — all from a browser UI.
      </p>
      <p>
        Click the <strong>CloudRadar logo</strong> in the top-left of the sidebar at any time to return to
        the cloud-selection screen.
      </p>
      <p>
        Every run button supports <strong>script selection</strong>: expand the checklist above the run button,
        tick or untick individual scripts, and click <strong>All / None</strong> to quickly change the selection.
        Only the ticked scripts will execute — giving you full control over what runs.
      </p>
    </section>

    <!-- Cloud selection -->
    <section class="doc-section" id="cloud-selection">
      <h2>Cloud selection</h2>
      <p>
        The first screen shows three cloud provider cards: <strong>AWS</strong>, <strong>Google Cloud</strong>,
        and <strong>Azure</strong>. Click the one that matches your environment. You are taken to the Setup
        page for that provider. You can change provider at any time from the sidebar Setup page.
      </p>
    </section>

    <!-- Setup -->
    <section class="doc-section" id="setup">
      <h2>Setup &amp; credentials</h2>
      <p>Credentials are stored in <code>config.yaml</code> in the project root. Restrict file permissions and never commit this file.</p>
      <table class="doc-table">
        <thead><tr><th>Cloud</th><th>Required fields</th><th>Notes</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>AWS</strong></td>
            <td>Region, Access Key ID, Secret Access Key</td>
            <td>Session Token optional (for temporary credentials). Or use an IAM role / AWS profile instead of keys.</td>
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
      <p>
        Click <strong>Save and continue</strong> to persist credentials and open the Dashboard, or
        <strong>Setup later</strong> to skip and configure via environment variables or cloud instance roles.
      </p>
    </section>

    <!-- Security — Full scan -->
    <section class="doc-section" id="security">
      <h2>Security — Full security scan</h2>
      <p>
        The <strong>Security Scan</strong> runs end-to-end discovery, enrichment, rule evaluation, risk scoring,
        and optionally saves a snapshot. Progress is shown step-by-step in real time. Reports can be downloaded
        as JSON or HTML.
      </p>
      <p>
        You can choose <strong>which services to scan</strong> using the script selector — deselect any service
        to skip it completely (faster scans, lower API call cost).
      </p>

      <h3>Services &amp; what is checked</h3>
      <table class="doc-table">
        <thead><tr><th>Service</th><th>Script ID</th><th>What is checked</th></tr></thead>
        <tbody>
          <tr><td><strong>EC2</strong></td><td><code>ec2</code></td><td>Public IPs on instances, vulnerable AMIs, instance types, missing required tags.</td></tr>
          <tr><td><strong>S3</strong></td><td><code>s3</code></td><td>Public-access-block disabled, missing server-side encryption, overly permissive bucket policies.</td></tr>
          <tr><td><strong>RDS</strong></td><td><code>rds</code></td><td>Publicly accessible flag, storage encryption at rest disabled.</td></tr>
          <tr><td><strong>Lambda</strong></td><td><code>lambda</code></td><td>Short or missing timeout, hardcoded secrets in env vars, missing tags.</td></tr>
          <tr><td><strong>IAM</strong></td><td><code>iam</code></td><td>Wildcard actions in policies, admin-policy attachments to users/roles, unused access keys.</td></tr>
          <tr><td><strong>Security Groups</strong></td><td><code>sg</code></td><td>Inbound rules open to 0.0.0.0/0 on ports 22 (SSH), 3389 (RDP), 3306, 5432, 1433, and others.</td></tr>
          <tr><td><strong>ALB / Load Balancers</strong></td><td><code>alb</code></td><td>Internet-facing ALBs missing WAF Web ACL, access logging disabled.</td></tr>
          <tr><td><strong>WAF</strong></td><td><code>waf</code></td><td>Web ACLs not associated with API Gateway or ALB resources.</td></tr>
          <tr><td><strong>CloudTrail</strong></td><td><code>cloudtrail</code></td><td>Multi-region not enabled, log file validation off, CloudWatch Logs integration missing.</td></tr>
          <tr><td><strong>VPC</strong></td><td><code>vpc</code></td><td>Default VPC still in use, VPC flow logs not enabled.</td></tr>
          <tr><td><strong>EBS Volumes</strong></td><td><code>ebs</code></td><td>Volumes without encryption at rest.</td></tr>
          <tr><td><strong>EKS</strong></td><td><code>eks</code></td><td>Public API server endpoint, control plane logging disabled, secrets encryption missing.</td></tr>
          <tr><td><strong>ECS</strong></td><td><code>ecs</code></td><td>Privileged containers, missing CloudWatch log config, containers running as root.</td></tr>
          <tr><td><strong>KMS</strong></td><td><code>kms</code></td><td>Customer-managed keys with automatic rotation disabled.</td></tr>
          <tr><td><strong>API Gateway</strong></td><td><code>apigateway</code></td><td>Access logging not enabled, WAF not attached to REST API stages.</td></tr>
          <tr><td><strong>SQS</strong></td><td><code>sqs</code></td><td>Queues without server-side encryption, public resource policy exposure.</td></tr>
          <tr><td><strong>DynamoDB</strong></td><td><code>dynamodb</code></td><td>Tables without encryption at rest, point-in-time recovery (PITR) disabled.</td></tr>
          <tr><td><strong>GuardDuty</strong></td><td><code>guardduty</code></td><td>Threat detection detector not enabled in the scanned region.</td></tr>
          <tr><td><strong>CloudWatch</strong></td><td><code>cloudwatch</code></td><td>Missing CIS metric filters for root login, IAM/CloudTrail/VPC/KMS/S3 changes.</td></tr>
          <tr><td><strong>ECR</strong></td><td><code>ecr</code></td><td>Container images with critical/high CVEs, scan-on-push not enabled.</td></tr>
        </tbody>
      </table>

      <h3>How to use script selection</h3>
      <ol>
        <li>On the <strong>Security Scan</strong> page, all 20 services are pre-selected.</li>
        <li>Click <strong>None</strong> then tick only the services you care about — or click <strong>All</strong> to reset.</li>
        <li>Individual services can be toggled by clicking their row.</li>
        <li>The run button shows how many services are selected. The scan will only call AWS APIs for those services.</li>
      </ol>
    </section>

    <!-- Vulnerabilities -->
    <section class="doc-section" id="vulnerabilities">
      <h2>Security — Vulnerabilities</h2>
      <p>
        A focused scan for known CVEs and AMI issues — without running the full CSPM rule engine.
        Useful for a quick container security check after a deployment.
      </p>
      <table class="doc-table">
        <thead><tr><th>Script</th><th>ID</th><th>What it does</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>ECR Image Scan</strong></td>
            <td><code>ecr</code></td>
            <td>Pulls all ECR repositories and checks each image tag for CVE findings reported by AWS ECR native scanning or Inspector. Reports critical and high severity CVEs with package name, version, and fix version where available.</td>
          </tr>
          <tr>
            <td><strong>AMI Vulnerability Check</strong></td>
            <td><code>ami</code></td>
            <td>Checks EC2 instances for deprecated AMIs (older than 180 days), public AMI usage, and AMI IDs on known-vulnerable lists. Flags instances that should be re-imaged.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Audit -->
    <section class="doc-section" id="audit">
      <h2>Audit</h2>
      <p>Audit scripts let you inspect and compare your asset catalog over time. They do not run security rules.</p>
      <table class="doc-table">
        <thead><tr><th>Script</th><th>What it does</th><th>Options</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>List assets</strong></td>
            <td>Exports the full asset catalog from the last scan (or a named snapshot) as JSON or CSV. Includes resource type, ID, region, tags, and a risk-score field.</td>
            <td>Output format (JSON / CSV); Snapshot ID (optional — leave blank for latest scan).</td>
          </tr>
          <tr>
            <td><strong>Changes</strong></td>
            <td>Compares the current cloud state with the last saved snapshot. Reports new resources (added), removed resources (deleted), and modified resources (config diff). Useful for change-control audits.</td>
            <td>Runs automatically from latest scan vs. previous snapshot.</td>
          </tr>
          <tr>
            <td><strong>Snapshot diff</strong></td>
            <td>Compares two named snapshots by ID. Shows the exact diff between any two points in time — good for reviewing what changed between a deployment and a rollback.</td>
            <td>Snapshot ID A and Snapshot ID B.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Compliance -->
    <section class="doc-section" id="compliance">
      <h2>Compliance</h2>
      <p>
        Maps security findings to framework controls and generates a pass/fail report.
        The compliance check uses findings from the latest scan (or triggers a scan first if no data exists).
        Output can be JSON or HTML.
      </p>
      <table class="doc-table">
        <thead><tr><th>Framework</th><th>Standard</th><th>Focus &amp; controls checked</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>CIS</strong></td>
            <td>CIS AWS Foundations Benchmark v1.5</td>
            <td>AWS-specific hardening: IAM password policy, MFA on root, CloudTrail enabled, VPC flow logs, S3 logging, CloudWatch alarms for key events.</td>
          </tr>
          <tr>
            <td><strong>SOC 2</strong></td>
            <td>AICPA SOC 2 Trust Services Criteria</td>
            <td>Logical access controls, encryption in transit and at rest, monitoring, incident response readiness, availability of key services.</td>
          </tr>
          <tr>
            <td><strong>HIPAA</strong></td>
            <td>HIPAA Security Rule (45 CFR Part 164)</td>
            <td>Access control (§164.312(a)), audit controls (§164.312(b)), integrity (§164.312(c)), transmission security (§164.312(e)), encryption of PHI at rest and in transit.</td>
          </tr>
          <tr>
            <td><strong>PCI DSS</strong></td>
            <td>PCI DSS v4.0</td>
            <td>Firewall rules (Req. 1), no default credentials (Req. 2), encryption of cardholder data (Req. 3–4), access control (Req. 7–8), monitoring &amp; logging (Req. 10).</td>
          </tr>
          <tr>
            <td><strong>ISO 27001</strong></td>
            <td>ISO/IEC 27001:2022 Annex A</td>
            <td>A.5 policies, A.6 people controls, A.8 asset management, A.8.20 network security, A.8.24 cryptography, A.8.15 logging, A.5.33 data protection, A.8.16 monitoring.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Governance -->
    <section class="doc-section" id="governance">
      <h2>Governance</h2>
      <p>
        Governance checks enforce your organisation's resource policies and tagging standards.
        Select only the checks relevant to your environment. Output as JSON or HTML.
      </p>
      <table class="doc-table">
        <thead><tr><th>Script</th><th>ID</th><th>What it does</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>Tag Compliance</strong></td>
            <td><code>tags</code></td>
            <td>Scans all resources for required tags (e.g. <code>Environment</code>, <code>Owner</code>, <code>CostCenter</code>). Reports resources with missing, empty, or non-standard tag values. Tag requirements are configurable in <code>config.yaml</code>.</td>
          </tr>
          <tr>
            <td><strong>Resource Policy Checks</strong></td>
            <td><code>policy</code></td>
            <td>Validates resources against defined policies: forbidden instance types in production environments, minimum backup retention periods, required encryption settings. Policy rules are defined in <code>config.yaml</code>.</td>
          </tr>
          <tr>
            <td><strong>Policy Violations</strong></td>
            <td><code>violations</code></td>
            <td>Detects resources that violate governance policies derived from security findings: publicly exposed resources, unencrypted storage volumes, over-privileged IAM roles (e.g. Administrator access attached to users).</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Pentest -->
    <section class="doc-section" id="pentest">
      <h2>Pentest</h2>
      <p>
        Pentest checks simulate an attacker's perspective — finding exposed entry points, leaked secrets,
        and exploitable chains. Results augment the full security scan with attacker-centric context.
        Select only the checks you want.
      </p>
      <table class="doc-table">
        <thead><tr><th>Script</th><th>ID</th><th>What it does</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>Exposed Services</strong></td>
            <td><code>exposed</code></td>
            <td>Checks all security groups and network ACLs for inbound rules that expose sensitive ports to the public internet (0.0.0.0/0 or ::/0): SSH (22), RDP (3389), MySQL (3306), PostgreSQL (5432), MSSQL (1433), MongoDB (27017), Redis (6379), Elasticsearch (9200), and others.</td>
          </tr>
          <tr>
            <td><strong>Secrets Scan</strong></td>
            <td><code>secrets</code></td>
            <td>Searches asset metadata (Lambda environment variables, EC2 user-data, ECS task definitions) and optionally a supplied local repository path for hardcoded secrets: AWS keys, API tokens, passwords, RSA private keys, and common secret patterns using regex matching.</td>
          </tr>
          <tr>
            <td><strong>Exploit Mapping</strong></td>
            <td><code>exploits</code></td>
            <td>Takes the current findings and maps them to known exploit scenarios using a graph-based attack path engine (built on networkx). Example chains: public-S3 + wildcard-IAM = data exfiltration; public-RDS + no-encryption = SQL injection + data exposure; exposed-EC2 + EKS-public-API = cluster takeover path.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Tests -->
    <section class="doc-section" id="tests">
      <h2>Tests</h2>
      <p>
        The <strong>Tests</strong> tab runs CloudRadar's built-in unit and integration test suite using
        <code>pytest</code>. Tests are completely <strong>isolated from cloud scans</strong> — they use
        mocked AWS services (<code>moto</code>) and never make real API calls. Run tests to validate that
        your local installation is working correctly or after making custom rule changes.
      </p>
      <p>
        Select any combination of test modules from the checklist, then click <strong>Run Tests</strong>.
        Output streams in real time. Each test is shown as passed (✓), failed (✗), error (⚠), or skipped (–).
        A summary banner shows the final result.
      </p>

      <h3>Test modules</h3>
      <table class="doc-table">
        <thead><tr><th>Module</th><th>What it tests</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>Rule Engine</strong></td>
            <td>
              Validates that security rules fire correctly and produce accurate findings.
              Covers: S3 public-access-block disabled → CRITICAL finding; RDS publicly accessible → HIGH;
              EC2 missing encryption → MEDIUM; IAM wildcard action → HIGH; missing tags → LOW.
              Also checks that finding fields (rule_id, severity, resource_id, description) are always populated.
            </td>
          </tr>
          <tr>
            <td><strong>S3 Scanner</strong></td>
            <td>
              Tests the S3-specific scanner module end-to-end (mocked with moto).
              Checks: public-access-block disabled is detected; encryption not set raises finding;
              permissive bucket policy (s3:GetObject for *) is flagged; clean bucket produces zero findings.
            </td>
          </tr>
          <tr>
            <td><strong>Compliance Frameworks</strong></td>
            <td>
              Verifies all five compliance frameworks (CIS, SOC 2, HIPAA, PCI DSS, ISO 27001).
              For each framework: finds are correctly mapped to controls; pass/fail status per control is
              accurate; report structure contains required fields (framework, controls, summary);
              a clean environment with no findings produces an all-pass report.
            </td>
          </tr>
          <tr>
            <td><strong>Remediation Engine</strong></td>
            <td>
              Checks that the remediation module generates correct auto-remediation actions for each finding type.
              Examples tested: S3 public-access-block → enable-public-access-block action generated;
              EBS unencrypted → create-encrypted-copy action; RDS publicly accessible → modify-db-instance action.
              Validates action schema (action_type, resource_id, parameters).
            </td>
          </tr>
          <tr>
            <td><strong>Attack Paths</strong></td>
            <td>
              Tests the attack path graph engine. Validates that the graph is built correctly from findings,
              that a public-EC2 → open-security-group → sensitive-RDS chain is detected and scores above
              the HIGH threshold, and that an isolated resource with no exposure produces no attack path.
            </td>
          </tr>
          <tr>
            <td><strong>All Scanners</strong></td>
            <td>
              Integration tests for every scanner module using mocked AWS services.
              Covers: EC2, RDS, IAM, Lambda, CloudTrail, VPC, EBS, EKS, ECS, KMS,
              API Gateway, SQS, DynamoDB, GuardDuty, and CloudWatch.
              Each test creates a deliberately misconfigured mocked resource, runs the scanner,
              and asserts the expected finding is raised with the correct severity.
            </td>
          </tr>
        </tbody>
      </table>

      <h3>How tests work</h3>
      <ul>
        <li>Tests are run in a <strong>separate subprocess</strong> — completely isolated from the web server and any ongoing scan.</li>
        <li>AWS calls are intercepted by <code>moto</code> — no real AWS credentials are needed.</li>
        <li>Tests only start when you click <strong>Run Tests</strong> from the Tests page.</li>
        <li>You can select a subset (e.g. only run Compliance tests after updating a compliance rule).</li>
        <li>Output streams line-by-line in real time via Server-Sent Events with a polling fallback.</li>
      </ul>
    </section>

    <!-- Hosting -->
    <section class="doc-section" id="hosting">
      <h2>Running locally &amp; on a server</h2>
      <h3>Local setup</h3>
      <ol>
        <li>Install Python deps: <code>pip install -e .</code></li>
        <li>Install and build frontend: <code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code></li>
        <li>Start the server: <code>python -m cspm.cli ui --host 127.0.0.1 --port 8000</code></li>
        <li>Open <code>http://127.0.0.1:8000</code>, select your cloud, and enter credentials in Setup.</li>
      </ol>

      <h3>Hosted on a server</h3>
      <ol>
        <li>Build the frontend on the server (or copy the <code>frontend/dist/</code> build).</li>
        <li>Run: <code>python -m cspm.cli ui --host 0.0.0.0 --port 8000</code></li>
        <li>Put Nginx or another reverse proxy in front with HTTPS.</li>
        <li>
          Add this to your Nginx location block for <code>/api/jobs/</code> and <code>/api/tests/</code>
          to prevent SSE buffering:
          <pre class="doc-code">proxy_buffering off;
X-Accel-Buffering: no;</pre>
        </li>
        <li>Prefer IAM roles (AWS), workload identity (GCP), or managed identity (Azure) instead of storing plain-text keys in <code>config.yaml</code>.</li>
      </ol>

      <h3>Docker</h3>
      <p>A <code>docker-compose.yml</code> is included. Run <code>docker compose up --build</code> to start the full stack. Set credentials via environment variables or mount a <code>config.yaml</code> volume.</p>
    </section>
  </div>
</template>

<script setup>
</script>

<style scoped>
.doc-page {
  max-width: 820px;
}
.doc-intro {
  font-size: 1.05rem;
  color: var(--text-muted);
  margin-bottom: 20px;
}

/* Table of contents */
.doc-toc {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  padding: 14px 18px;
  background: rgba(14,165,233,0.06);
  border: 1px solid rgba(14,165,233,0.2);
  border-radius: 10px;
  margin-bottom: 32px;
}
.doc-toc a {
  font-size: 0.84rem;
  color: var(--accent);
  text-decoration: none;
  white-space: nowrap;
}
.doc-toc a:hover { text-decoration: underline; }

.doc-section {
  margin-bottom: 36px;
}
.doc-section h2 {
  font-size: 1.2rem;
  color: var(--text);
  margin: 0 0 14px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}
.doc-section h3 {
  font-size: 1rem;
  margin: 18px 0 8px;
  color: var(--text-muted);
}
.doc-section p, .doc-section ul, .doc-section ol {
  margin: 0 0 12px;
  line-height: 1.65;
  color: var(--text);
}
.doc-section ul, .doc-section ol {
  padding-left: 24px;
}
.doc-section li {
  margin-bottom: 4px;
}
.doc-section code {
  background: rgba(0,0,0,0.3);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85em;
}
.doc-code {
  background: rgba(0,0,0,0.35);
  border-radius: 8px;
  padding: 10px 14px;
  font-family: monospace;
  font-size: 0.82rem;
  color: #d4d4d4;
  margin: 8px 0 12px;
  overflow-x: auto;
}

.doc-table {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0 18px;
  font-size: 0.85rem;
}
.doc-table th, .doc-table td {
  text-align: left;
  padding: 9px 12px;
  border: 1px solid var(--border);
  color: var(--text);
  vertical-align: top;
  line-height: 1.5;
}
.doc-table thead th {
  background: rgba(14,165,233,0.10);
  font-weight: 600;
  color: var(--accent);
}
.doc-table tbody tr:nth-child(even) {
  background: rgba(255,255,255,0.03);
}

/* Light theme overrides */
.theme-light .doc-section code {
  background: rgba(0,0,0,0.07);
}
.theme-light .doc-code {
  background: #1e1e2e;
}
.theme-light .doc-table tbody tr:nth-child(even) {
  background: rgba(0,0,0,0.03);
}
</style>
