import boto3
from boto3.resources.base import ServiceResource


def create_dynamodb_resource() -> ServiceResource:
    """Create a DynamoDB resource using the Lambda's AWS configuration."""
    return boto3.resource("dynamodb")
