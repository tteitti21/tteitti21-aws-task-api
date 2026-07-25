import os

import boto3
from boto3.resources.base import ServiceResource


def create_dynamodb_resource() -> ServiceResource:
    """Create a DynamoDB resource connected to DynamoDB Local."""
    endpoint_url = os.getenv("DYNAMODB_ENDPOINT")

    if not endpoint_url:
        raise RuntimeError(
            "LOCAL_DYNAMODB_ENABLED is true, but DYNAMODB_ENDPOINT is not set"
        )

    return boto3.resource(
        "dynamodb",
        endpoint_url=endpoint_url,
        region_name=os.getenv("AWS_REGION", "eu-north-1"),
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )
