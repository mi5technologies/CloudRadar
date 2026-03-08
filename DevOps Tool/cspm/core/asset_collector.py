"""Collect and enrich assets from a cloud provider."""
from typing import Any, Callable, Optional

from cspm.scanners import s3_scanner, iam_scanner, network_scanner, waf_scanner
from cspm.scanners import lambda_scanner, ec2_scanner, rds_scanner
from cspm.scanners import (
    cloudtrail_scanner,
    vpc_scanner,
    eks_scanner,
    ecs_scanner,
    kms_scanner,
    apigateway_scanner,
    sqs_scanner,
    dynamodb_scanner,
    guardduty_scanner,
    cloudwatch_scanner,
    secretsmanager_scanner,
    sns_scanner,
    cloudfront_scanner,
    stepfunctions_scanner,
)


def collect(
    raw_assets: dict[str, list[dict[str, Any]]],
    region: str,
    only_types: list[str] | None = None,
    on_progress: Optional[Callable[[str, str], None]] = None,
) -> dict[str, list[dict[str, Any]]]:
    def report(step: str, status: str = "running"):
        if on_progress:
            on_progress(step, status)

    result = {}
    type_set = set(only_types) if only_types else None

    def _include(t: str) -> bool:
        return type_set is None or t in type_set

    # --- existing services ---
    if raw_assets.get("s3") and _include("s3"):
        report("Scanning S3 buckets", "running")
        result["s3"] = s3_scanner.scan_s3(raw_assets["s3"], region)
        report("Scanning S3 buckets", "success")
    if raw_assets.get("ec2") and _include("ec2"):
        report("Scanning EC2 instances", "running")
        result["ec2"] = ec2_scanner.scan_ec2(raw_assets["ec2"])
        report("Scanning EC2 instances", "success")
    if raw_assets.get("rds") and _include("rds"):
        report("Scanning RDS instances", "running")
        result["rds"] = rds_scanner.scan_rds(raw_assets["rds"])
        report("Scanning RDS instances", "success")
    if raw_assets.get("lambda") and _include("lambda"):
        report("Scanning Lambda functions", "running")
        result["lambda"] = lambda_scanner.scan_lambda(raw_assets["lambda"])
        report("Scanning Lambda functions", "success")
    if (raw_assets.get("iam_user") or raw_assets.get("iam_role")) and (
        _include("iam_user") or _include("iam_role")
    ):
        report("Scanning IAM", "running")
        users, roles = iam_scanner.scan_iam(
            raw_assets.get("iam_user", []),
            raw_assets.get("iam_role", []),
            region,
        )
        result["iam_user"] = users
        result["iam_role"] = roles
        report("Scanning IAM", "success")
    if raw_assets.get("security_group") and _include("security_group"):
        report("Scanning security groups", "running")
        result["security_group"] = network_scanner.scan_network(
            raw_assets["security_group"], raw_assets.get("alb", [])
        )
        report("Scanning security groups", "success")
    if raw_assets.get("alb") and (_include("alb") or _include("waf")):
        report("Scanning WAF/ALB", "running")
        result["alb"] = waf_scanner.scan_waf(raw_assets["alb"], region)
        report("Scanning WAF/ALB", "success")
    if raw_assets.get("waf") and _include("waf"):
        result["waf"] = raw_assets["waf"]

    # --- new services ---
    if raw_assets.get("cloudtrail") and _include("cloudtrail"):
        report("Scanning CloudTrail trails", "running")
        result["cloudtrail"] = cloudtrail_scanner.scan_cloudtrail(raw_assets["cloudtrail"])
        report("Scanning CloudTrail trails", "success")
    if raw_assets.get("vpc") and _include("vpc"):
        report("Scanning VPCs", "running")
        result["vpc"] = vpc_scanner.scan_vpc(raw_assets["vpc"])
        report("Scanning VPCs", "success")
    if raw_assets.get("ebs") and _include("ebs"):
        report("Scanning EBS volumes", "running")
        result["ebs"] = vpc_scanner.scan_ebs(raw_assets["ebs"])
        report("Scanning EBS volumes", "success")
    if raw_assets.get("eks") and _include("eks"):
        report("Scanning EKS clusters", "running")
        result["eks"] = eks_scanner.scan_eks(raw_assets["eks"])
        report("Scanning EKS clusters", "success")
    if raw_assets.get("ecs_cluster") and _include("ecs_cluster"):
        report("Scanning ECS clusters", "running")
        result["ecs_cluster"] = ecs_scanner.scan_ecs_clusters(raw_assets["ecs_cluster"])
        report("Scanning ECS clusters", "success")
    if raw_assets.get("ecs_task_def") and _include("ecs_task_def"):
        report("Scanning ECS task definitions", "running")
        result["ecs_task_def"] = ecs_scanner.scan_ecs_task_defs(raw_assets["ecs_task_def"])
        report("Scanning ECS task definitions", "success")
    if raw_assets.get("kms") and _include("kms"):
        report("Scanning KMS keys", "running")
        result["kms"] = kms_scanner.scan_kms(raw_assets["kms"])
        report("Scanning KMS keys", "success")
    if raw_assets.get("api_gateway") and _include("api_gateway"):
        report("Scanning API Gateway", "running")
        result["api_gateway"] = apigateway_scanner.scan_apigateway(raw_assets["api_gateway"])
        report("Scanning API Gateway", "success")
    if raw_assets.get("sqs") and _include("sqs"):
        report("Scanning SQS queues", "running")
        result["sqs"] = sqs_scanner.scan_sqs(raw_assets["sqs"])
        report("Scanning SQS queues", "success")
    if raw_assets.get("dynamodb") and _include("dynamodb"):
        report("Scanning DynamoDB tables", "running")
        result["dynamodb"] = dynamodb_scanner.scan_dynamodb(raw_assets["dynamodb"])
        report("Scanning DynamoDB tables", "success")
    if raw_assets.get("guardduty") and _include("guardduty"):
        report("Scanning GuardDuty", "running")
        result["guardduty"] = guardduty_scanner.scan_guardduty(raw_assets["guardduty"])
        report("Scanning GuardDuty", "success")
    if raw_assets.get("cloudwatch_alarm") and _include("cloudwatch_alarm"):
        report("Scanning CloudWatch alarms", "running")
        result["cloudwatch_alarm"] = cloudwatch_scanner.scan_cloudwatch(raw_assets["cloudwatch_alarm"])
        report("Scanning CloudWatch alarms", "success")
    if raw_assets.get("secretsmanager") and _include("secretsmanager"):
        report("Scanning Secrets Manager secrets", "running")
        result["secretsmanager"] = secretsmanager_scanner.scan_secretsmanager(raw_assets["secretsmanager"])
        report("Scanning Secrets Manager secrets", "success")
    if raw_assets.get("sns") and _include("sns"):
        report("Scanning SNS topics", "running")
        result["sns"] = sns_scanner.scan_sns(raw_assets["sns"])
        report("Scanning SNS topics", "success")
    if raw_assets.get("cloudfront") and _include("cloudfront"):
        report("Scanning CloudFront distributions", "running")
        result["cloudfront"] = cloudfront_scanner.scan_cloudfront(raw_assets["cloudfront"])
        report("Scanning CloudFront distributions", "success")
    if raw_assets.get("stepfunctions") and _include("stepfunctions"):
        report("Scanning Step Functions state machines", "running")
        result["stepfunctions"] = stepfunctions_scanner.scan_stepfunctions(raw_assets["stepfunctions"])
        report("Scanning Step Functions state machines", "success")

    # --- GCP/Azure serverless (no dedicated scanner; pass through for serverless_scanner) ---
    if raw_assets.get("cloud_run") and _include("cloud_run"):
        result["cloud_run"] = raw_assets["cloud_run"]
    if raw_assets.get("gcp_cloud_functions") and _include("gcp_cloud_functions"):
        result["gcp_cloud_functions"] = raw_assets["gcp_cloud_functions"]
    if raw_assets.get("azure_functions") and _include("azure_functions"):
        result["azure_functions"] = raw_assets["azure_functions"]

    return result
