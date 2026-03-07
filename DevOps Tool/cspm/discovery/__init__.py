"""Discovery modules for cloud assets."""
from cspm.discovery import ec2_discovery
from cspm.discovery import s3_discovery
from cspm.discovery import rds_discovery
from cspm.discovery import lambda_discovery
from cspm.discovery import iam_discovery
from cspm.discovery import network_discovery
from cspm.discovery import waf_discovery
from cspm.discovery import cloudtrail_discovery
from cspm.discovery import vpc_discovery
from cspm.discovery import eks_discovery
from cspm.discovery import ecs_discovery
from cspm.discovery import kms_discovery
from cspm.discovery import apigateway_discovery
from cspm.discovery import sqs_discovery
from cspm.discovery import dynamodb_discovery
from cspm.discovery import guardduty_discovery
from cspm.discovery import cloudwatch_discovery
from cspm.discovery import secretsmanager_discovery
from cspm.discovery import sns_discovery

__all__ = [
    "ec2_discovery", "s3_discovery", "rds_discovery", "lambda_discovery",
    "iam_discovery", "network_discovery", "waf_discovery",
    "cloudtrail_discovery", "vpc_discovery", "eks_discovery", "ecs_discovery",
    "kms_discovery", "apigateway_discovery", "sqs_discovery", "dynamodb_discovery",
    "guardduty_discovery", "cloudwatch_discovery",
    "secretsmanager_discovery", "sns_discovery",
]
