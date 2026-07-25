from unittest.mock import patch

import pytest

from src.create_task.storage import aws_dynamodb, local_dynamodb
from src.create_task.storage.tasks_table import get_dynamodb_resource


def test_aws_dynamodb_is_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOCAL_DYNAMODB_ENABLED", raising=False)
    monkeypatch.delenv("DYNAMODB_ENDPOINT", raising=False)

    with patch.object(aws_dynamodb.boto3, "resource") as resource:
        get_dynamodb_resource()

    resource.assert_called_once_with("dynamodb")


def test_dynamodb_mode_rejects_unclear_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOCAL_DYNAMODB_ENABLED", "yes")

    with pytest.raises(RuntimeError, match="must be either 'true' or 'false'"):
        get_dynamodb_resource()


def test_local_dynamodb_requires_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOCAL_DYNAMODB_ENABLED", "true")
    monkeypatch.delenv("DYNAMODB_ENDPOINT", raising=False)

    with pytest.raises(RuntimeError, match="DYNAMODB_ENDPOINT is not set"):
        get_dynamodb_resource()


def test_local_dynamodb_uses_explicit_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOCAL_DYNAMODB_ENABLED", "true")
    monkeypatch.setenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
    monkeypatch.setenv("AWS_REGION", "eu-north-1")

    with patch.object(local_dynamodb.boto3, "resource") as resource:
        get_dynamodb_resource()

    resource.assert_called_once_with(
        "dynamodb",
        endpoint_url="http://localhost:8000",
        region_name="eu-north-1",
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )
