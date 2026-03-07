/**
 * Per-finding recommendation lookup table.
 * Keys match on rule_id (exact) or resource_type prefix (fallback).
 * Covers AWS, GCP, and Azure findings.
 */

// ═══════════════════════════════════════════════════════════════════════════
// AWS RECOMMENDATIONS
// ═══════════════════════════════════════════════════════════════════════════
export const RECOMMENDATIONS = {
  // ── EC2 ─────────────────────────────────────────────────────────────────
  'ec2.public_ip': {
    cloud: 'aws',
    title: 'EC2 Instance Has Public IP',
    what: 'One or more EC2 instances have a public IP address directly assigned.',
    why: 'Publicly reachable instances expand your attack surface. Any open port becomes externally accessible.',
    fix: [
      'Place instances behind an Application Load Balancer (ALB) or NAT Gateway.',
      'Remove the public IP by disabling "Auto-assign public IP" in the subnet settings.',
      'Restrict Security Group inbound rules to known IP ranges only.',
    ],
    docs: 'https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-instance-addressing.html',
    severity: 'medium',
  },
  'ec2.vulnerable_ami': {
    cloud: 'aws',
    title: 'EC2 Using Vulnerable or Deprecated AMI',
    what: 'Instances are running on AMIs that are outdated, deprecated, or have known CVEs.',
    why: 'Unpatched AMIs are a common initial access vector in cloud breaches.',
    fix: [
      'Build a new AMI from the latest Amazon Linux 2023 / Ubuntu 22.04 LTS base.',
      'Enable EC2 Image Builder to auto-refresh AMIs on a schedule.',
      'Replace running instances with new ones using the updated AMI.',
    ],
    docs: 'https://docs.aws.amazon.com/imagebuilder/latest/userguide/what-is-image-builder.html',
    severity: 'high',
  },
  'ec2.missing_tags': {
    cloud: 'aws',
    title: 'EC2 Instance Missing Required Tags',
    what: 'Instances are missing required tags (e.g. Owner, Environment, CostCenter).',
    why: 'Missing tags make cost attribution, incident response, and compliance auditing difficult.',
    fix: [
      'Define a tagging policy using AWS Organizations Tag Policies.',
      'Use AWS Config rule "required-tags" to enforce tagging compliance.',
      'Apply tags via IaC (Terraform/CloudFormation) to all new resources.',
    ],
    docs: 'https://docs.aws.amazon.com/tag-editor/latest/userguide/tagging.html',
    severity: 'low',
  },

  // ── S3 ──────────────────────────────────────────────────────────────────
  's3.public_access': {
    cloud: 'aws',
    title: 'S3 Bucket Publicly Accessible',
    what: 'S3 bucket has public access enabled — either via ACL, bucket policy, or missing Block Public Access settings.',
    why: 'Public S3 buckets are responsible for some of the largest data breaches. Sensitive data can be read or overwritten by anyone.',
    fix: [
      'Enable "Block all public access" on the bucket in the AWS Console or via CLI.',
      'Remove any ACL grants to "Everyone" or "Any authenticated AWS user".',
      'Review bucket policy for `"Principal": "*"` statements and restrict them.',
      'Use AWS Macie to scan for sensitive data in at-risk buckets.',
    ],
    docs: 'https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html',
    severity: 'critical',
  },
  's3.no_encryption': {
    cloud: 'aws',
    title: 'S3 Bucket Not Encrypted at Rest',
    what: 'Server-side encryption (SSE) is not enabled on this bucket.',
    why: 'Without encryption at rest, bucket data is readable if storage is physically compromised.',
    fix: [
      'Enable SSE-S3 (AES-256) or SSE-KMS on the bucket.',
      'Use a bucket policy to deny `s3:PutObject` requests without `x-amz-server-side-encryption`.',
      'Prefer SSE-KMS with a customer-managed key for additional access control.',
    ],
    docs: 'https://docs.aws.amazon.com/AmazonS3/latest/userguide/serv-side-encryption.html',
    severity: 'high',
  },
  's3.no_versioning': {
    cloud: 'aws',
    title: 'S3 Bucket Versioning Disabled',
    what: 'Object versioning is not enabled, so deleted or overwritten objects cannot be recovered.',
    why: 'Without versioning, ransomware or accidental deletion permanently destroys data.',
    fix: [
      'Enable versioning on the bucket.',
      'Configure lifecycle rules to expire old versions and control storage costs.',
      'Enable MFA Delete for buckets containing critical data.',
    ],
    docs: 'https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html',
    severity: 'medium',
  },

  // ── IAM ─────────────────────────────────────────────────────────────────
  'iam.wildcard_action': {
    cloud: 'aws',
    title: 'IAM Policy Grants Wildcard Actions (*)',
    what: 'An IAM policy contains `"Action": "*"` granting unrestricted permissions.',
    why: 'Wildcard actions violate least-privilege principle and allow privilege escalation.',
    fix: [
      'Replace `"Action": "*"` with only the specific actions the role needs.',
      'Use AWS IAM Access Analyzer to generate least-privilege policies from CloudTrail.',
      'Regularly review and prune unused permissions with IAM Access Advisor.',
    ],
    docs: 'https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege',
    severity: 'critical',
  },
  'iam.admin_policy': {
    cloud: 'aws',
    title: 'IAM User or Role Has Admin Policy Attached',
    what: 'AdministratorAccess or a similar all-encompassing policy is attached.',
    why: 'Admin accounts are high-value targets. Compromise leads to full account takeover.',
    fix: [
      'Remove AdministratorAccess and replace with scoped policies.',
      'Use IAM roles with short-lived credentials (STS) instead of long-term admin keys.',
      'Enable MFA on all admin accounts.',
      'Use AWS Organizations SCPs to restrict admin actions at the org level.',
    ],
    docs: 'https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_job-functions.html',
    severity: 'critical',
  },
  'iam.unused_keys': {
    cloud: 'aws',
    title: 'IAM Access Key Unused for 90+ Days',
    what: 'Long-lived access keys that have not been used in over 90 days still exist.',
    why: 'Unused credentials are a dormant risk — if leaked, attackers can use them unnoticed.',
    fix: [
      'Rotate or delete access keys unused for more than 90 days.',
      'Use IAM roles instead of long-term access keys wherever possible.',
      'Enable AWS Credential Reports to regularly audit key usage.',
    ],
    docs: 'https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html',
    severity: 'high',
  },

  // ── Security Groups ──────────────────────────────────────────────────────
  'sg.ssh_open': {
    cloud: 'aws',
    title: 'SSH Port 22 Open to the World (0.0.0.0/0)',
    what: 'Security group allows inbound SSH (port 22) from any IP address.',
    why: 'Open SSH is constantly scanned and brute-forced by automated bots across the internet.',
    fix: [
      'Restrict SSH to your office/VPN IP ranges only.',
      'Remove direct SSH access entirely — use AWS Systems Manager Session Manager instead.',
      'If SSH is needed, place it behind a bastion host with strict security group rules.',
    ],
    docs: 'https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html',
    severity: 'critical',
  },
  'sg.rdp_open': {
    cloud: 'aws',
    title: 'RDP Port 3389 Open to the World (0.0.0.0/0)',
    what: 'Security group allows inbound RDP (port 3389) from any IP address.',
    why: 'Open RDP is one of the most common ransomware entry points.',
    fix: [
      'Restrict RDP to VPN or specific IP ranges only.',
      'Use AWS Systems Manager Fleet Manager for remote desktop instead of direct RDP.',
      'Enable Network Access Control Lists (NACLs) as a secondary layer.',
    ],
    docs: 'https://docs.aws.amazon.com/systems-manager/latest/userguide/fleet-rdp.html',
    severity: 'critical',
  },
  'sg.all_traffic': {
    cloud: 'aws',
    title: 'Security Group Allows All Inbound Traffic',
    what: 'A security group rule allows all ports and protocols from any source.',
    why: 'This effectively disables the firewall, exposing every running service to the internet.',
    fix: [
      'Replace the open rule with specific port/protocol rules for only what is needed.',
      'Audit each running service and only allow its specific port.',
      'Use VPC Flow Logs to understand actual traffic before tightening rules.',
    ],
    docs: 'https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html',
    severity: 'critical',
  },

  // ── RDS ─────────────────────────────────────────────────────────────────
  'rds.publicly_accessible': {
    cloud: 'aws',
    title: 'RDS Database Publicly Accessible',
    what: 'The RDS instance has the "Publicly Accessible" flag set to true.',
    why: 'A publicly accessible database can be discovered and attacked from the internet.',
    fix: [
      'Set "Publicly Accessible" to false — databases should only be in private subnets.',
      'Use a bastion host or AWS Systems Manager for administrative access.',
      'Ensure the DB is in a private VPC subnet with no internet gateway route.',
    ],
    docs: 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html',
    severity: 'critical',
  },
  'rds.no_encryption': {
    cloud: 'aws',
    title: 'RDS Database Storage Not Encrypted',
    what: 'The RDS instance does not have storage encryption enabled.',
    why: 'Unencrypted database storage can expose sensitive data if snapshots or storage are compromised.',
    fix: [
      'Enable encryption by creating a new encrypted snapshot and restoring to a new instance.',
      'Note: encryption cannot be enabled on a running instance — a snapshot restore is required.',
      'Use a KMS customer-managed key for additional control over key rotation.',
    ],
    docs: 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html',
    severity: 'high',
  },

  // ── Lambda ──────────────────────────────────────────────────────────────
  'lambda.hardcoded_secret': {
    cloud: 'aws',
    title: 'Hardcoded Secret Detected in Lambda Function',
    what: 'Environment variables or function code contains what appears to be a hardcoded secret, API key, or password.',
    why: 'Hardcoded credentials are exposed to anyone with Lambda describe/list access and are difficult to rotate.',
    fix: [
      'Move secrets to AWS Secrets Manager or Parameter Store (SecureString).',
      'Update the Lambda function to fetch secrets at runtime using the AWS SDK.',
      'Revoke and rotate any exposed credentials immediately.',
      'Use AWS Macie to scan for additional exposed secrets.',
    ],
    docs: 'https://docs.aws.amazon.com/secretsmanager/latest/userguide/lambda-functions.html',
    severity: 'critical',
  },

  // ── CloudTrail ──────────────────────────────────────────────────────────
  'cloudtrail.disabled': {
    cloud: 'aws',
    title: 'CloudTrail Not Enabled or Not Multi-Region',
    what: 'CloudTrail is either disabled or only logging in a single region.',
    why: 'Without CloudTrail you have no audit log of API calls — impossible to detect breaches or do forensics.',
    fix: [
      'Enable CloudTrail with multi-region logging.',
      'Enable CloudTrail log file validation to detect tampering.',
      'Deliver logs to a separate S3 bucket in a dedicated security account.',
      'Set up CloudWatch Alarms for suspicious CloudTrail events.',
    ],
    docs: 'https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-create-and-update-a-trail.html',
    severity: 'critical',
  },

  // ── EBS ─────────────────────────────────────────────────────────────────
  'ebs.unencrypted': {
    cloud: 'aws',
    title: 'EBS Volume Not Encrypted',
    what: 'One or more EBS volumes do not have encryption at rest enabled.',
    why: 'Unencrypted EBS volumes can expose data if snapshots are shared or volumes are detached.',
    fix: [
      'Enable EBS default encryption at the account level so all new volumes are encrypted.',
      'For existing volumes: create an encrypted snapshot and restore to a new encrypted volume.',
      'Use KMS customer-managed keys for stricter access control.',
    ],
    docs: 'https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSEncryption.html',
    severity: 'high',
  },

  // ── EKS ─────────────────────────────────────────────────────────────────
  'eks.public_endpoint': {
    cloud: 'aws',
    title: 'EKS API Server Endpoint is Publicly Accessible',
    what: 'The EKS cluster API server endpoint is accessible from the public internet.',
    why: 'A public Kubernetes API server is a prime target for credential theft and cluster takeover.',
    fix: [
      'Restrict API server access to specific CIDR blocks (your office/VPN).',
      'Enable the private endpoint and disable the public endpoint entirely.',
      'Ensure RBAC is configured with least-privilege roles.',
    ],
    docs: 'https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html',
    severity: 'high',
  },

  // ── GuardDuty ───────────────────────────────────────────────────────────
  'guardduty.disabled': {
    cloud: 'aws',
    title: 'AWS GuardDuty Not Enabled',
    what: 'GuardDuty threat detection is not enabled in this region.',
    why: 'Without GuardDuty, malicious activity (crypto mining, credential exfiltration, port scanning) goes undetected.',
    fix: [
      'Enable GuardDuty in all active regions.',
      'Enable GuardDuty at the AWS Organizations level to cover all accounts.',
      'Configure SNS notifications or EventBridge rules for high-severity findings.',
    ],
    docs: 'https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_settingup.html',
    severity: 'high',
  },

  // ── KMS ─────────────────────────────────────────────────────────────────
  'kms.no_rotation': {
    cloud: 'aws',
    title: 'KMS Key Auto-Rotation Disabled',
    what: 'Customer-managed KMS keys do not have automatic key rotation enabled.',
    why: 'Without rotation, a compromised key provides indefinite access to encrypted data.',
    fix: [
      'Enable automatic annual key rotation in KMS key settings.',
      'AWS rotates only the key material — the key ID remains the same, no re-encryption needed.',
    ],
    docs: 'https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html',
    severity: 'medium',
  },

  // ── VPC ─────────────────────────────────────────────────────────────────
  'vpc.default_in_use': {
    cloud: 'aws',
    title: 'Default VPC Is In Use',
    what: 'Resources are deployed in the default VPC which has permissive settings.',
    why: 'Default VPCs allow all instances to have public IPs and have open inter-instance communication.',
    fix: [
      'Create a custom VPC with private subnets and a NAT Gateway.',
      'Migrate workloads from the default VPC to the custom VPC.',
      'Delete the default VPC from all regions once workloads are migrated.',
    ],
    docs: 'https://docs.aws.amazon.com/vpc/latest/userguide/default-vpc.html',
    severity: 'medium',
  },
  'vpc.no_flow_logs': {
    cloud: 'aws',
    title: 'VPC Flow Logs Not Enabled',
    what: 'VPC Flow Logs are not configured for network traffic monitoring.',
    why: 'Without flow logs, you cannot detect anomalous traffic, data exfiltration, or port scanning.',
    fix: [
      'Enable VPC Flow Logs and deliver to CloudWatch Logs or S3.',
      'Set up CloudWatch Metric Filters to alert on suspicious traffic patterns.',
    ],
    docs: 'https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html',
    severity: 'medium',
  },

  // ── ALB ─────────────────────────────────────────────────────────────────
  'alb.no_waf': {
    cloud: 'aws',
    title: 'Load Balancer Has No WAF Web ACL',
    what: 'The Application Load Balancer does not have a WAF Web ACL attached.',
    why: 'Without WAF, common web attacks (SQL injection, XSS, DDoS) reach your application directly.',
    fix: [
      'Create a WAF Web ACL with AWS Managed Rule Groups (Core Rule Set, Known Bad Inputs).',
      'Associate the Web ACL with the ALB.',
      'Enable AWS Shield Advanced for DDoS protection on critical ALBs.',
    ],
    docs: 'https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html',
    severity: 'high',
  },
  'alb.no_access_logs': {
    cloud: 'aws',
    title: 'ALB Access Logging Disabled',
    what: 'Access logs are not enabled for the Application Load Balancer.',
    why: 'Without access logs, you cannot investigate request patterns, attacks, or performance issues.',
    fix: [
      'Enable access logging on the ALB and point it to an S3 bucket.',
      'Set a lifecycle policy on the S3 bucket to retain logs for at least 90 days.',
    ],
    docs: 'https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html',
    severity: 'medium',
  },

  // ── DynamoDB ─────────────────────────────────────────────────────────────
  'dynamodb.no_pitr': {
    cloud: 'aws',
    title: 'DynamoDB Point-in-Time Recovery (PITR) Disabled',
    what: 'PITR is not enabled, meaning accidental data loss cannot be recovered.',
    why: 'Without PITR, accidental deletes or table corruption result in permanent data loss.',
    fix: [
      'Enable PITR on all DynamoDB tables holding important data.',
      'Test recovery procedures at least quarterly.',
    ],
    docs: 'https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery.html',
    severity: 'medium',
  },

  // ── ECR ──────────────────────────────────────────────────────────────────
  'ecr.critical_cve': {
    cloud: 'aws',
    title: 'Container Image Has Critical CVEs',
    what: 'ECR image scan found critical or high severity CVEs in container images.',
    why: 'Container vulnerabilities can be exploited for container escape, privilege escalation, or data theft.',
    fix: [
      'Update the base image to the latest version.',
      'Rebuild and push a patched image immediately.',
      'Enable scan-on-push to catch vulnerabilities before they reach production.',
      'Use Amazon Inspector for continuous container vulnerability monitoring.',
    ],
    docs: 'https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html',
    severity: 'critical',
  },
  'ecr.no_scan_on_push': {
    cloud: 'aws',
    title: 'ECR Repository Has Scan-on-Push Disabled',
    what: 'Container images are pushed to ECR without being automatically scanned for vulnerabilities.',
    why: 'Unscanned images may contain known CVEs that could have been caught at build time.',
    fix: [
      'Enable scan-on-push for all ECR repositories.',
      'Configure EventBridge rules to alert on critical scan findings.',
    ],
    docs: 'https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html',
    severity: 'high',
  },

  // ═══════════════════════════════════════════════════════════════════════
  // GCP RECOMMENDATIONS
  // ═══════════════════════════════════════════════════════════════════════

  // ── Compute Engine ──────────────────────────────────────────────────────
  'gcp.compute.public_ip': {
    cloud: 'gcp',
    title: 'Compute VM Has External (Public) IP',
    what: 'A Compute Engine VM instance has an external IP address directly attached.',
    why: 'VMs with external IPs are directly reachable from the internet, increasing the attack surface.',
    fix: [
      'Remove the external IP from the VM network interface.',
      'Use Cloud NAT to give VMs internet egress without a public ingress IP.',
      'Route external traffic through a Cloud Load Balancer instead.',
    ],
    docs: 'https://cloud.google.com/compute/docs/ip-addresses/reserve-static-external-ip-address',
    severity: 'medium',
  },
  'gcp.compute.serial_port_enabled': {
    cloud: 'gcp',
    title: 'Serial Port Access Enabled on VM',
    what: 'Interactive serial port access is enabled on a Compute Engine instance.',
    why: 'Serial port access bypasses normal network controls and can be used by attackers with IAM access.',
    fix: [
      'Disable serial port access in the VM metadata: set `serial-port-enable` to `false`.',
      'Use OS Login or SSH keys for legitimate administrative access.',
      'Enforce this with an Organisation Policy: `compute.disableSerialPortAccess`.',
    ],
    docs: 'https://cloud.google.com/compute/docs/troubleshooting/troubleshooting-using-serial-console',
    severity: 'medium',
  },
  'gcp.compute.os_not_patched': {
    cloud: 'gcp',
    title: 'Compute VM OS Not Patched',
    what: 'The VM is running an OS version with known unpatched vulnerabilities.',
    why: 'Unpatched systems are the primary entry vector for both automated and targeted attacks.',
    fix: [
      'Enable OS patch management using VM Manager patch jobs.',
      'Schedule recurring patch deployments across your VM fleet.',
      'Use Container-Optimized OS or Shielded VMs for increased security baseline.',
    ],
    docs: 'https://cloud.google.com/compute/docs/os-patch-management',
    severity: 'high',
  },

  // ── Cloud Storage ────────────────────────────────────────────────────────
  'gcp.storage.public_bucket': {
    cloud: 'gcp',
    title: 'Cloud Storage Bucket is Publicly Accessible',
    what: 'The GCS bucket has `allUsers` or `allAuthenticatedUsers` in its IAM policy.',
    why: 'Public buckets expose all stored objects to anyone on the internet, risking data leakage.',
    fix: [
      'Remove `allUsers` and `allAuthenticatedUsers` from all bucket IAM bindings.',
      'Enable Uniform Bucket-Level Access to disable legacy ACLs.',
      'Use Signed URLs or Identity-Aware Proxy for controlled public access.',
      'Enable GCS audit logs and use Security Command Center to alert on public buckets.',
    ],
    docs: 'https://cloud.google.com/storage/docs/access-control/making-data-public',
    severity: 'critical',
  },
  'gcp.storage.no_encryption': {
    cloud: 'gcp',
    title: 'Cloud Storage Not Using Customer-Managed Encryption Keys (CMEK)',
    what: 'Buckets are using Google-managed encryption keys instead of customer-managed keys.',
    why: 'Without CMEK, you have no control over key rotation, revocation, or access auditing for encrypted data.',
    fix: [
      'Create a Cloud KMS key ring and key for each sensitive bucket.',
      'Set the default encryption key on the bucket to your CMEK.',
      'Rotate CMEK keys at least annually.',
    ],
    docs: 'https://cloud.google.com/storage/docs/encryption/customer-managed-keys',
    severity: 'medium',
  },
  'gcp.storage.no_versioning': {
    cloud: 'gcp',
    title: 'Cloud Storage Versioning Disabled',
    what: 'Object versioning is not enabled on the bucket.',
    why: 'Without versioning, deleted or overwritten objects cannot be recovered.',
    fix: [
      'Enable versioning on the bucket via `gsutil versioning set on gs://BUCKET_NAME`.',
      'Set Object Lifecycle Management rules to expire old versions after N days.',
    ],
    docs: 'https://cloud.google.com/storage/docs/object-versioning',
    severity: 'medium',
  },

  // ── IAM ─────────────────────────────────────────────────────────────────
  'gcp.iam.service_account_key': {
    cloud: 'gcp',
    title: 'Service Account Has User-Managed Keys',
    what: 'A service account has one or more user-created and managed keys.',
    why: 'User-managed keys are long-lived credentials that are easily leaked and hard to rotate.',
    fix: [
      'Delete all user-managed service account keys.',
      'Use Workload Identity for GKE workloads, or the metadata server for Compute Engine.',
      'If keys are unavoidable, store them in Secret Manager and rotate every 90 days.',
    ],
    docs: 'https://cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys',
    severity: 'high',
  },
  'gcp.iam.primitive_roles': {
    cloud: 'gcp',
    title: 'Primitive IAM Roles (Owner/Editor/Viewer) in Use',
    what: 'Project-level primitive roles (roles/owner, roles/editor) are assigned.',
    why: 'Primitive roles grant overly broad permissions and violate least-privilege principle.',
    fix: [
      'Replace roles/owner and roles/editor with predefined or custom roles.',
      'Use IAM Recommender to get least-privilege role suggestions.',
      'Enable Policy Analyzer to audit who has access to what.',
    ],
    docs: 'https://cloud.google.com/iam/docs/understanding-roles#primitive_roles',
    severity: 'high',
  },
  'gcp.iam.no_mfa': {
    cloud: 'gcp',
    title: 'Users Without Multi-Factor Authentication (MFA)',
    what: 'Some Google accounts in your organisation do not have MFA/2-Step Verification enabled.',
    why: 'Without MFA, a stolen password is sufficient to compromise an account.',
    fix: [
      'Enforce 2-Step Verification for all users via Google Workspace Admin.',
      'Require hardware security keys (FIDO2) for privileged accounts.',
      'Use Context-Aware Access to require MFA for sensitive resource access.',
    ],
    docs: 'https://support.google.com/a/answer/9176657',
    severity: 'critical',
  },

  // ── Firewall / VPC ───────────────────────────────────────────────────────
  'gcp.firewall.ssh_open': {
    cloud: 'gcp',
    title: 'Firewall Rule Allows SSH from 0.0.0.0/0',
    what: 'A VPC firewall rule allows inbound SSH (TCP 22) from any source IP.',
    why: 'Open SSH ports are continuously scanned and attacked by automated tools globally.',
    fix: [
      'Delete or restrict the firewall rule to specific known IP ranges.',
      'Use Identity-Aware Proxy (IAP) for TCP tunnelling — it provides SSH access without open firewall rules.',
      'Enable OS Login for centrally managed, short-lived SSH access.',
    ],
    docs: 'https://cloud.google.com/iap/docs/using-tcp-forwarding',
    severity: 'critical',
  },
  'gcp.firewall.rdp_open': {
    cloud: 'gcp',
    title: 'Firewall Rule Allows RDP from 0.0.0.0/0',
    what: 'A VPC firewall rule allows inbound RDP (TCP 3389) from any source IP.',
    why: 'Publicly exposed RDP is a top ransomware entry point.',
    fix: [
      'Restrict the firewall rule to only your corporate/VPN IP ranges.',
      'Use IAP for TCP tunnelling to remove the need for any open RDP firewall rule.',
      'Enable Cloud Armor to protect internet-facing endpoints.',
    ],
    docs: 'https://cloud.google.com/iap/docs/using-tcp-forwarding',
    severity: 'critical',
  },
  'gcp.vpc.no_flow_logs': {
    cloud: 'gcp',
    title: 'VPC Flow Logs Not Enabled',
    what: 'VPC flow logging is disabled for one or more subnets.',
    why: 'Without flow logs, you cannot investigate network anomalies, lateral movement, or data exfiltration.',
    fix: [
      'Enable VPC Flow Logs on all subnets via the Cloud Console or gcloud.',
      'Export flow logs to Cloud Logging and set up Log-Based Alerts for anomalous patterns.',
    ],
    docs: 'https://cloud.google.com/vpc/docs/using-flow-logs',
    severity: 'medium',
  },

  // ── Cloud SQL ────────────────────────────────────────────────────────────
  'gcp.sql.public_ip': {
    cloud: 'gcp',
    title: 'Cloud SQL Instance Has Public IP',
    what: 'The Cloud SQL instance has a public IP address and is reachable from the internet.',
    why: 'A publicly accessible database is a high-value target for brute-force and injection attacks.',
    fix: [
      'Switch the instance to Private IP only — remove the public IP.',
      'Use Cloud SQL Auth Proxy for all connection from applications and admin tools.',
      'Place the instance in a VPC with restricted IP authorisation.',
    ],
    docs: 'https://cloud.google.com/sql/docs/mysql/configure-private-ip',
    severity: 'critical',
  },
  'gcp.sql.no_backup': {
    cloud: 'gcp',
    title: 'Cloud SQL Automated Backups Disabled',
    what: 'Automated backups are not enabled for the Cloud SQL instance.',
    why: 'Without backups, data loss from corruption or accidental deletion is unrecoverable.',
    fix: [
      'Enable automated backups in the Cloud SQL instance settings.',
      'Configure a backup retention window of at least 7 days.',
      'Enable point-in-time recovery (PITR) for additional granularity.',
    ],
    docs: 'https://cloud.google.com/sql/docs/mysql/backup-recovery/backups',
    severity: 'high',
  },

  // ── GKE ─────────────────────────────────────────────────────────────────
  'gcp.gke.public_endpoint': {
    cloud: 'gcp',
    title: 'GKE Cluster Has Public API Server Endpoint',
    what: 'The GKE cluster control plane is accessible from the public internet.',
    why: 'A public Kubernetes API server is a prime target for credential theft and cluster takeover.',
    fix: [
      'Enable Private Cluster mode to remove the public endpoint.',
      'If a public endpoint is required, use Master Authorised Networks to restrict access to known IPs.',
      'Ensure RBAC and Workload Identity are configured.',
    ],
    docs: 'https://cloud.google.com/kubernetes-engine/docs/how-to/private-clusters',
    severity: 'high',
  },
  'gcp.gke.legacy_abac': {
    cloud: 'gcp',
    title: 'GKE Legacy ABAC (Attribute-Based Access Control) Enabled',
    what: 'The GKE cluster is using the legacy ABAC authorisation system.',
    why: 'Legacy ABAC is coarse-grained and bypasses Kubernetes RBAC policies.',
    fix: [
      'Disable Legacy ABAC on the cluster.',
      'Use Kubernetes RBAC exclusively for fine-grained access control.',
      'Review and update all service account bindings to use RBAC roles.',
    ],
    docs: 'https://cloud.google.com/kubernetes-engine/docs/how-to/role-based-access-control',
    severity: 'high',
  },

  // ── Logging / Monitoring ─────────────────────────────────────────────────
  'gcp.logging.disabled': {
    cloud: 'gcp',
    title: 'Cloud Audit Logging Not Fully Enabled',
    what: 'Admin Activity, Data Access, or System Event audit logs are not enabled for one or more services.',
    why: 'Without audit logs, you cannot detect unauthorised access or reconstruct incident timelines.',
    fix: [
      'Enable all audit log types (Admin Activity, Data Access, System Event) at the project level.',
      'Export logs to Cloud Storage or BigQuery for long-term retention.',
      'Set up Log-Based Alerts for critical events (IAM changes, key deletions, etc.).',
    ],
    docs: 'https://cloud.google.com/logging/docs/audit',
    severity: 'critical',
  },
  'gcp.monitoring.no_alerts': {
    cloud: 'gcp',
    title: 'No Security Monitoring Alerts Configured',
    what: 'No alerting policies exist for critical security events in Cloud Monitoring.',
    why: 'Without alerts, security incidents go undetected until they cause visible damage.',
    fix: [
      'Create alerting policies for: IAM policy changes, firewall rule modifications, bucket ACL changes.',
      'Integrate Cloud Monitoring with PagerDuty, Slack, or email for timely notification.',
      'Use Security Command Center Premium for automated threat detection.',
    ],
    docs: 'https://cloud.google.com/monitoring/alerts',
    severity: 'high',
  },

  // ── Cloud KMS ────────────────────────────────────────────────────────────
  'gcp.kms.no_rotation': {
    cloud: 'gcp',
    title: 'Cloud KMS Key Rotation Not Configured',
    what: 'Customer-managed encryption keys (CMEK) do not have automatic rotation enabled.',
    why: 'Without rotation, a compromised key gives indefinite access to all data encrypted with it.',
    fix: [
      'Enable automatic rotation on Cloud KMS keys (recommended: 90 days).',
      'Rotation creates a new key version; old versions remain for decryption until destroyed.',
      'Use separate key rings per environment (dev/staging/prod).',
    ],
    docs: 'https://cloud.google.com/kms/docs/key-rotation',
    severity: 'medium',
  },

  // ═══════════════════════════════════════════════════════════════════════
  // AZURE RECOMMENDATIONS
  // ═══════════════════════════════════════════════════════════════════════

  // ── Virtual Machines ─────────────────────────────────────────────────────
  'azure.vm.public_ip': {
    cloud: 'azure',
    title: 'Azure VM Has Public IP Address',
    what: 'A Virtual Machine has a public IP directly attached to its NIC.',
    why: 'Internet-facing VMs are continuously scanned for vulnerabilities and open ports.',
    fix: [
      'Dissociate the public IP from the VM NIC.',
      'Place the VM behind an Azure Load Balancer or Application Gateway.',
      'Use Azure Bastion for secure administrative access instead of direct RDP/SSH.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/bastion/bastion-overview',
    severity: 'medium',
  },
  'azure.vm.no_disk_encryption': {
    cloud: 'azure',
    title: 'Azure VM Disk Not Encrypted',
    what: 'The VM OS or data disks are not encrypted with Azure Disk Encryption (ADE).',
    why: 'Unencrypted disks expose data at rest if the underlying hardware is compromised.',
    fix: [
      'Enable Azure Disk Encryption (ADE) using Azure Key Vault for key management.',
      'Use Server-Side Encryption (SSE) with Customer-Managed Keys (CMK) as a minimum.',
      'Apply Azure Policy to enforce disk encryption across all VMs in the subscription.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/virtual-machines/disk-encryption-overview',
    severity: 'high',
  },
  'azure.vm.no_mde': {
    cloud: 'azure',
    title: 'Microsoft Defender for Endpoint Not Enabled on VM',
    what: 'Microsoft Defender for Endpoint (MDE) is not deployed on the Virtual Machine.',
    why: 'Without EDR coverage, malware, lateral movement, and ransomware can run undetected on the VM.',
    fix: [
      'Enable Microsoft Defender for Servers in Defender for Cloud.',
      'Deploy the MDE extension to all VMs via Azure Policy.',
      'Review Defender for Cloud security score to identify other unprotected resources.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/defender-for-cloud/integration-defender-for-endpoint',
    severity: 'high',
  },

  // ── Storage Accounts ──────────────────────────────────────────────────────
  'azure.storage.public_blob': {
    cloud: 'azure',
    title: 'Azure Storage Account Allows Public Blob Access',
    what: 'The storage account has public blob access enabled, allowing anonymous reads.',
    why: 'Publicly accessible blobs expose sensitive files to anyone who knows (or guesses) the URL.',
    fix: [
      'Set `allowBlobPublicAccess` to `false` on the storage account.',
      'Use Shared Access Signatures (SAS) or Azure AD authentication for controlled access.',
      'Enable Azure Defender for Storage to detect anomalous access patterns.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/storage/blobs/anonymous-read-access-prevent',
    severity: 'critical',
  },
  'azure.storage.no_https': {
    cloud: 'azure',
    title: 'Azure Storage Account Allows HTTP (Non-HTTPS) Traffic',
    what: 'The storage account does not enforce HTTPS-only connections.',
    why: 'HTTP traffic is unencrypted; credentials and data can be intercepted in transit.',
    fix: [
      'Enable "Secure transfer required" on the storage account.',
      'Apply Azure Policy `Secure transfer to storage accounts should be enabled` to enforce this.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/storage/common/storage-require-secure-transfer',
    severity: 'high',
  },
  'azure.storage.no_cmk': {
    cloud: 'azure',
    title: 'Azure Storage Not Using Customer-Managed Keys (CMK)',
    what: 'The storage account uses Microsoft-managed keys instead of customer-managed keys.',
    why: 'Without CMK, you cannot control key rotation, revocation, or access auditing.',
    fix: [
      'Create an Azure Key Vault and add a key.',
      'Configure the storage account to use the Key Vault key via managed identity.',
      'Enable automatic key rotation in Key Vault.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/storage/common/customer-managed-keys-overview',
    severity: 'medium',
  },

  // ── Azure AD / IAM ───────────────────────────────────────────────────────
  'azure.iam.no_mfa': {
    cloud: 'azure',
    title: 'Azure AD Users Without MFA',
    what: 'One or more Azure AD user accounts do not have multi-factor authentication enabled.',
    why: 'MFA prevents account takeover even when credentials are compromised.',
    fix: [
      'Enable Conditional Access policies requiring MFA for all users.',
      'Use Microsoft Authenticator app or FIDO2 hardware keys.',
      'Enable Microsoft Entra ID Protection to detect risky sign-ins automatically.',
    ],
    docs: 'https://learn.microsoft.com/en-us/entra/identity/authentication/tutorial-enable-azure-mfa',
    severity: 'critical',
  },
  'azure.iam.excessive_permissions': {
    cloud: 'azure',
    title: 'Over-Privileged Role Assignment (Owner/Contributor)',
    what: 'Users or service principals have been assigned Owner or Contributor roles at subscription scope.',
    why: 'Overly broad roles allow full resource modification or deletion, risking account-wide damage.',
    fix: [
      'Replace subscription-scope Owner/Contributor with resource-group or resource-scoped roles.',
      'Use Azure AD Privileged Identity Management (PIM) for just-in-time elevation.',
      'Review role assignments regularly with Azure Access Reviews.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/role-based-access-control/best-practices',
    severity: 'critical',
  },
  'azure.iam.no_privileged_identity_mgmt': {
    cloud: 'azure',
    title: 'Azure AD Privileged Identity Management (PIM) Not Configured',
    what: 'Privileged roles are permanently assigned rather than using just-in-time elevation via PIM.',
    why: 'Permanent privileged assignments mean an attacker who compromises the account has constant admin access.',
    fix: [
      'Enable Microsoft Entra Privileged Identity Management.',
      'Convert all permanent privileged assignments to eligible assignments with approval workflows.',
      'Set maximum activation duration of 4-8 hours for privileged roles.',
    ],
    docs: 'https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-configure',
    severity: 'high',
  },

  // ── Network Security Groups ───────────────────────────────────────────────
  'azure.nsg.ssh_open': {
    cloud: 'azure',
    title: 'NSG Allows Inbound SSH from Any IP (0.0.0.0/0)',
    what: 'A Network Security Group rule allows TCP port 22 from the Internet.',
    why: 'Open SSH on the internet is constantly brute-forced by automated scanners.',
    fix: [
      'Remove the any-source SSH rule from the NSG.',
      'Use Azure Bastion for SSH/RDP access — no open ports required.',
      'If SSH is required, restrict the source IP to your corporate/VPN range.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/bastion/bastion-overview',
    severity: 'critical',
  },
  'azure.nsg.rdp_open': {
    cloud: 'azure',
    title: 'NSG Allows Inbound RDP from Any IP (0.0.0.0/0)',
    what: 'A Network Security Group rule allows TCP port 3389 from the Internet.',
    why: 'Exposed RDP is the #1 ransomware entry point in Azure environments.',
    fix: [
      'Delete the open RDP NSG rule immediately.',
      'Use Azure Bastion for browser-based RDP without any open firewall rules.',
      'Enable Just-in-Time VM Access via Defender for Cloud for temporary access.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/defender-for-cloud/just-in-time-access-usage',
    severity: 'critical',
  },

  // ── Azure SQL / Database ──────────────────────────────────────────────────
  'azure.sql.public_access': {
    cloud: 'azure',
    title: 'Azure SQL Server Allows Public Network Access',
    what: 'The SQL Server firewall allows connections from public internet IPs.',
    why: 'Publicly reachable SQL servers are targeted for brute-force, injection, and credential stuffing.',
    fix: [
      'Set "Deny public network access" to Yes on the SQL Server.',
      'Use Private Link or VNet Service Endpoints for all connectivity.',
      'Audit and restrict firewall rules to specific known IPs.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/azure-sql/database/private-endpoint-overview',
    severity: 'critical',
  },
  'azure.sql.no_tde': {
    cloud: 'azure',
    title: 'Transparent Data Encryption (TDE) Not Using CMK',
    what: 'Azure SQL TDE is using a service-managed key instead of a customer-managed key.',
    why: 'Without CMK-based TDE, you lack control over encryption key lifecycle.',
    fix: [
      'Enable TDE with a customer-managed key stored in Azure Key Vault.',
      'Assign a managed identity to the SQL Server for Key Vault access.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-byok-overview',
    severity: 'medium',
  },
  'azure.sql.no_auditing': {
    cloud: 'azure',
    title: 'Azure SQL Server Auditing Disabled',
    what: 'Database auditing is not enabled, so queries and logins are not logged.',
    why: 'Without auditing, detecting SQL injection, data exfiltration, or privilege abuse is impossible.',
    fix: [
      'Enable SQL Server Auditing and send logs to a Storage Account, Log Analytics, or Event Hub.',
      'Retain audit logs for at least 90 days.',
      'Enable Microsoft Defender for SQL for advanced threat detection.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/azure-sql/database/auditing-overview',
    severity: 'high',
  },

  // ── Azure Key Vault ───────────────────────────────────────────────────────
  'azure.keyvault.no_expiry': {
    cloud: 'azure',
    title: 'Key Vault Secrets or Keys Have No Expiry Date',
    what: 'Secrets, keys, or certificates in Azure Key Vault have no expiration configured.',
    why: 'Non-expiring credentials are a persistent risk — if leaked, they remain valid indefinitely.',
    fix: [
      'Set expiry dates on all Key Vault secrets, keys, and certificates.',
      'Use Azure Key Vault Managed Identities to eliminate the need for long-lived secrets.',
      'Enable Key Vault diagnostic logging and monitor for expiring items.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/key-vault/general/best-practices',
    severity: 'high',
  },
  'azure.keyvault.no_soft_delete': {
    cloud: 'azure',
    title: 'Key Vault Soft Delete and Purge Protection Not Enabled',
    what: 'Soft Delete and/or Purge Protection are not enabled on the Key Vault.',
    why: 'Without these protections, a Key Vault or its contents can be permanently deleted instantly.',
    fix: [
      'Enable Soft Delete and set retention to at least 90 days.',
      'Enable Purge Protection to prevent permanent deletion during the retention period.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/key-vault/general/soft-delete-overview',
    severity: 'high',
  },

  // ── Azure Monitor / Defender ──────────────────────────────────────────────
  'azure.monitor.no_logs': {
    cloud: 'azure',
    title: 'Azure Activity Log Not Retained or Exported',
    what: 'Activity Log entries are not being exported or retained beyond the default 90-day period.',
    why: 'Without long-term logs, forensic investigation after a breach is impossible.',
    fix: [
      'Create a Diagnostic Setting to export Activity Logs to Log Analytics, Storage, or Event Hub.',
      'Set retention to at least 1 year for compliance requirements.',
      'Enable Azure Monitor Alerts for critical activity (role assignments, policy changes, etc.).',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/activity-log',
    severity: 'high',
  },
  'azure.defender.not_enabled': {
    cloud: 'azure',
    title: 'Microsoft Defender for Cloud Not Fully Enabled',
    what: 'Defender for Cloud plans (Servers, Storage, SQL, etc.) are not enabled for all resource types.',
    why: 'Without Defender, threat detection, vulnerability assessment, and compliance monitoring are absent.',
    fix: [
      'Enable Defender for Cloud plans for: Servers, Storage, SQL, Containers, and App Service.',
      'Review the Secure Score dashboard and remediate high-impact recommendations.',
      'Enable continuous export to SIEM for advanced correlation.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/defender-for-cloud/enable-enhanced-security',
    severity: 'high',
  },

  // ── Azure AKS ────────────────────────────────────────────────────────────
  'azure.aks.public_endpoint': {
    cloud: 'azure',
    title: 'AKS API Server Has Public Endpoint',
    what: 'The Azure Kubernetes Service API server is accessible from the public internet.',
    why: 'A public Kubernetes API server is a prime target for credential theft and cluster takeover.',
    fix: [
      'Enable Private Cluster to restrict API server to private network only.',
      'If public endpoint is required, configure Authorised IP Ranges to restrict access.',
      'Enable Azure AD integration and RBAC for fine-grained access control.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/aks/private-cluster',
    severity: 'high',
  },
  'azure.aks.rbac_disabled': {
    cloud: 'azure',
    title: 'RBAC Disabled on AKS Cluster',
    what: 'Kubernetes RBAC is not enabled on the AKS cluster.',
    why: 'Without RBAC, all authenticated users have unrestricted access to all cluster resources.',
    fix: [
      'Enable Azure AD integration with RBAC on the cluster.',
      'Create namespace-scoped roles for application teams.',
      'Use Azure AD groups to manage cluster access centrally.',
    ],
    docs: 'https://learn.microsoft.com/en-us/azure/aks/manage-azure-rbac',
    severity: 'high',
  },
}

// ─── Per-cloud top recommendations used on Dashboard ────────────────────────
export const TOP_RECS_BY_CLOUD = {
  aws: {
    critical: ['sg.ssh_open', 's3.public_access', 'iam.wildcard_action', 'cloudtrail.disabled', 'lambda.hardcoded_secret'],
    high:     ['s3.no_encryption', 'rds.publicly_accessible', 'iam.unused_keys', 'guardduty.disabled', 'eks.public_endpoint'],
    medium:   ['kms.no_rotation', 'vpc.no_flow_logs', 's3.no_versioning', 'alb.no_waf'],
  },
  gcp: {
    critical: ['gcp.firewall.ssh_open', 'gcp.storage.public_bucket', 'gcp.iam.no_mfa', 'gcp.logging.disabled', 'gcp.sql.public_ip'],
    high:     ['gcp.iam.service_account_key', 'gcp.iam.primitive_roles', 'gcp.gke.public_endpoint', 'gcp.compute.os_not_patched', 'gcp.monitoring.no_alerts'],
    medium:   ['gcp.kms.no_rotation', 'gcp.vpc.no_flow_logs', 'gcp.storage.no_versioning'],
  },
  azure: {
    critical: ['azure.nsg.ssh_open', 'azure.storage.public_blob', 'azure.iam.no_mfa', 'azure.iam.excessive_permissions', 'azure.sql.public_access'],
    high:     ['azure.vm.no_disk_encryption', 'azure.vm.no_mde', 'azure.storage.no_https', 'azure.sql.no_auditing', 'azure.keyvault.no_expiry'],
    medium:   ['azure.storage.no_cmk', 'azure.sql.no_tde', 'azure.monitor.no_logs'],
  },
}

/**
 * Get recommendation for a finding.
 * Tries exact rule_id match first, then resource_type prefix match, then cloud-prefix match.
 */
export function getRecommendation(finding) {
  if (!finding) return null
  const ruleId      = (finding.rule_id || '').toLowerCase()
  const resourceType = (finding.resource_type || '').toLowerCase()
  const cloud       = (finding.cloud || '').toLowerCase()

  // 1. Exact match on rule_id
  if (ruleId && RECOMMENDATIONS[ruleId]) return RECOMMENDATIONS[ruleId]

  // 2. Prefix match by resource_type (aws: 'sg', gcp: 'gcp.firewall', azure: 'azure.nsg')
  for (const key of Object.keys(RECOMMENDATIONS)) {
    const [prefix] = key.split('.')
    if (resourceType && resourceType.startsWith(prefix)) {
      return RECOMMENDATIONS[key]
    }
  }

  // 3. Any key starting with cloud prefix
  if (cloud && cloud !== 'aws') {
    const prefix = cloud + '.'
    for (const key of Object.keys(RECOMMENDATIONS)) {
      if (key.startsWith(prefix)) return RECOMMENDATIONS[key]
    }
  }

  // 4. Generic fallback
  const sev = (finding.severity || 'medium').toLowerCase()
  return {
    cloud: cloud || 'aws',
    title: finding.title || 'Security Finding',
    what: finding.title || 'A security issue was detected in your cloud environment.',
    why: 'This finding may indicate a misconfiguration or security gap that could be exploited.',
    fix: [
      'Review the affected resource and apply the principle of least privilege.',
      'Consult the cloud provider security best practices documentation for this service.',
      'Consider enabling native security monitoring (GuardDuty / Security Command Center / Defender for Cloud) to continuously detect and alert on this issue.',
    ],
    docs: cloud === 'gcp'
      ? 'https://cloud.google.com/security/best-practices'
      : cloud === 'azure'
        ? 'https://learn.microsoft.com/en-us/azure/security/fundamentals/best-practices-and-patterns'
        : 'https://docs.aws.amazon.com/security/',
    severity: sev,
  }
}

export const SEV_ORDER = { critical: 0, high: 1, medium: 2, low: 3, info: 4 }

export function sortBySeverity(findings) {
  return [...findings].sort((a, b) => {
    const sa = SEV_ORDER[(a.severity || 'medium').toLowerCase()] ?? 4
    const sb = SEV_ORDER[(b.severity || 'medium').toLowerCase()] ?? 4
    return sa - sb
  })
}

/**
 * Get top N recommendations for a given cloud + severity profile.
 */
export function getTopRecsForCloud(cloud, scanCounts, maxItems = 5) {
  const cloudKey = (cloud || 'aws').toLowerCase()
  const buckets  = TOP_RECS_BY_CLOUD[cloudKey] || TOP_RECS_BY_CLOUD.aws
  const keys     = []
  if ((scanCounts.critical || 0) > 0) keys.push(...(buckets.critical || []))
  if ((scanCounts.high     || 0) > 0) keys.push(...(buckets.high     || []))
  if ((scanCounts.medium   || 0) > 0) keys.push(...(buckets.medium   || []))
  if (!keys.length) keys.push(...(buckets.critical || []), ...(buckets.high || []))
  const seen = new Set()
  return keys
    .filter(k => { if (seen.has(k)) return false; seen.add(k); return true })
    .slice(0, maxItems)
    .map(k => RECOMMENDATIONS[k])
    .filter(Boolean)
}
