"""CSPM constants and risk scoring."""
# Risk severity scores (negative impact)
CRITICAL = -10
HIGH = -7
MEDIUM = -4
LOW = -1

SEVERITY_MAP = {
    "critical": CRITICAL,
    "high": HIGH,
    "medium": MEDIUM,
    "low": LOW,
}

# Rule categories
CATEGORY_STORAGE = "STORAGE"
CATEGORY_IDENTITY = "IDENTITY"
CATEGORY_NETWORK = "NETWORK"
CATEGORY_COMPUTE = "COMPUTE"
CATEGORY_SERVERLESS = "SERVERLESS"
CATEGORY_DATABASE = "DATABASE"
CATEGORY_WAF = "WAF"
CATEGORY_SECURITY_CONTROLS = "SECURITY_CONTROLS"
CATEGORY_GOVERNANCE = "GOVERNANCE"

# Asset types (normalized)
ASSET_EC2 = "ec2"
ASSET_S3 = "s3"
ASSET_RDS = "rds"
ASSET_LAMBDA = "lambda"
ASSET_IAM_USER = "iam_user"
ASSET_IAM_ROLE = "iam_role"
ASSET_SG = "security_group"
ASSET_ALB = "alb"
ASSET_WAF = "waf"
ASSET_ECR = "ecr"

# Sensitive ports for exposure checks
SENSITIVE_PORTS = [22, 3389, 5432, 3306, 6379, 27017, 5985, 5986]
