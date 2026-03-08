"""AWS provider: auth and discovery orchestration."""
from typing import Any, Callable, Optional

from cspm.providers.base_provider import BaseProvider
from cspm.utils.aws_helpers import get_caller_identity
from cspm.discovery import (
    ec2_discovery,
    s3_discovery,
    rds_discovery,
    lambda_discovery,
    iam_discovery,
    network_discovery,
    waf_discovery,
    cloudtrail_discovery,
    vpc_discovery,
    eks_discovery,
    ecs_discovery,
    kms_discovery,
    apigateway_discovery,
    sqs_discovery,
    dynamodb_discovery,
    guardduty_discovery,
    cloudwatch_discovery,
    secretsmanager_discovery,
    sns_discovery,
    cloudfront_discovery,
)


class AWSProvider(BaseProvider):
    def __init__(self, region: str | None = None):
        self.region = region or "us-east-1"
        self._account_id: str | None = None

    def authenticate(self) -> bool:
        try:
            identity = get_caller_identity(self.region)
            self._account_id = identity.get("Account", "unknown")
            return True
        except Exception:
            return False

    def get_account_id(self) -> str:
        if self._account_id is None:
            self.authenticate()
        return self._account_id or "unknown"

    def get_regions(self) -> list[str]:
        try:
            from cspm.utils.aws_helpers import get_client
            ec2 = get_client("ec2", self.region)
            out = ec2.describe_regions()
            return [r["RegionName"] for r in out.get("Regions", [])]
        except Exception:
            return [self.region]

    def discover_assets(
        self, asset_types: list[str] | None = None, on_progress: Optional[Callable[[str, str, Optional[str]], None]] = None
    ) -> dict[str, list[dict[str, Any]]]:
        def report(step: str, status: str = "running", detail: str | None = None):
            if on_progress:
                on_progress(step, status, detail)

        all_types = {
            "ec2", "s3", "rds", "lambda", "iam_user", "iam_role",
            "security_group", "alb", "waf",
            "cloudtrail", "vpc", "ebs", "eks", "ecs_cluster", "ecs_task_def",
            "kms", "api_gateway", "sqs", "dynamodb", "guardduty", "cloudwatch_alarm",
            "secretsmanager", "sns", "cloudfront",
        }
        types = set(asset_types) if asset_types else all_types
        result: dict[str, list[dict]] = {}

        # --- existing services ---
        if "ec2" in types:
            report("Discovering EC2 instances", "running")
            result["ec2"] = ec2_discovery.discover(self.region)
            report("Discovering EC2 instances", "success")
        if "s3" in types:
            report("Discovering S3 buckets", "running")
            result["s3"] = s3_discovery.discover(self.region)
            report("Discovering S3 buckets", "success")
        if "rds" in types:
            report("Discovering RDS instances", "running")
            result["rds"] = rds_discovery.discover(self.region)
            report("Discovering RDS instances", "success")
        if "lambda" in types:
            report("Discovering Lambda functions", "running")
            result["lambda"] = lambda_discovery.discover(self.region)
            report("Discovering Lambda functions", "success")
        if "iam_user" in types or "iam_role" in types:
            report("Discovering IAM users and roles", "running")
            iam = iam_discovery.discover(self.region)
            result["iam_user"] = iam.get("users", [])
            result["iam_role"] = iam.get("roles", [])
            report("Discovering IAM users and roles", "success")
        if "security_group" in types or "alb" in types:
            report("Discovering security groups and ALBs", "running")
            net = network_discovery.discover(self.region)
            result["security_group"] = net.get("security_groups", [])
            result["alb"] = net.get("albs", [])
            report("Discovering security groups and ALBs", "success")
        if "waf" in types:
            report("Discovering WAF", "running")
            result["waf"] = waf_discovery.discover(self.region)
            report("Discovering WAF", "success")

        # --- new services ---
        if "cloudtrail" in types:
            report("Discovering CloudTrail trails", "running")
            result["cloudtrail"] = cloudtrail_discovery.discover(self.region)
            report("Discovering CloudTrail trails", "success")
        if "vpc" in types or "ebs" in types:
            report("Discovering VPCs and EBS volumes", "running")
            vpc_data = vpc_discovery.discover(self.region)
            result["vpc"] = vpc_data.get("vpc", [])
            result["ebs"] = vpc_data.get("ebs", [])
            report("Discovering VPCs and EBS volumes", "success")
        if "eks" in types:
            report("Discovering EKS clusters", "running")
            result["eks"] = eks_discovery.discover(self.region)
            report("Discovering EKS clusters", "success")
        if "ecs_cluster" in types or "ecs_task_def" in types:
            report("Discovering ECS clusters and task definitions", "running")
            ecs_data = ecs_discovery.discover(self.region)
            result["ecs_cluster"] = ecs_data.get("ecs_cluster", [])
            result["ecs_task_def"] = ecs_data.get("ecs_task_def", [])
            report("Discovering ECS clusters and task definitions", "success")
        if "kms" in types:
            report("Discovering KMS keys", "running")
            result["kms"] = kms_discovery.discover(self.region)
            report("Discovering KMS keys", "success")
        if "api_gateway" in types:
            report("Discovering API Gateway APIs", "running")
            result["api_gateway"] = apigateway_discovery.discover(self.region)
            report("Discovering API Gateway APIs", "success")
        if "sqs" in types:
            report("Discovering SQS queues", "running")
            result["sqs"] = sqs_discovery.discover(self.region)
            report("Discovering SQS queues", "success")
        if "dynamodb" in types:
            report("Discovering DynamoDB tables", "running")
            result["dynamodb"] = dynamodb_discovery.discover(self.region)
            report("Discovering DynamoDB tables", "success")
        if "guardduty" in types:
            report("Checking GuardDuty status", "running")
            result["guardduty"] = guardduty_discovery.discover(self.region)
            report("Checking GuardDuty status", "success")
        if "cloudwatch_alarm" in types:
            report("Checking CloudWatch security alarms", "running")
            result["cloudwatch_alarm"] = cloudwatch_discovery.discover(self.region)
            report("Checking CloudWatch security alarms", "success")
        if "secretsmanager" in types:
            report("Discovering Secrets Manager secrets", "running")
            result["secretsmanager"] = secretsmanager_discovery.discover(self.region)
            report("Discovering Secrets Manager secrets", "success")
        if "sns" in types:
            report("Discovering SNS topics", "running")
            result["sns"] = sns_discovery.discover(self.region)
            report("Discovering SNS topics", "success")
        if "cloudfront" in types:
            report("Discovering CloudFront distributions", "running")
            result["cloudfront"] = cloudfront_discovery.discover(self.region)
            report("Discovering CloudFront distributions", "success")

        return result
