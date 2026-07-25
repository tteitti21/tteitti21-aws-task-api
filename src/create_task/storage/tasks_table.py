import os
from typing import Any

from boto3.resources.base import ServiceResource

from ..config import get_boolean_env
from .aws_dynamodb import create_dynamodb_resource as create_aws_resource
from .local_dynamodb import create_dynamodb_resource as create_local_resource


def get_dynamodb_resource() -> ServiceResource:
    """Select the local or AWS DynamoDB implementation explicitly."""
    if get_boolean_env("LOCAL_DYNAMODB_ENABLED"):
        return create_local_resource()

    return create_aws_resource()


def get_tasks_table() -> Any:
    table_name = os.environ["TASKS_TABLE"]
    return get_dynamodb_resource().Table(table_name)
