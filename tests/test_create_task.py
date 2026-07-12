import json
import os
from unittest.mock import MagicMock, patch

import pytest


os.environ["TASKS_TABLE"] = "test-tasks-table"

from src.create_task import app


@pytest.fixture
def mock_table() -> MagicMock:
    table = MagicMock()

    with patch.object(app.dynamodb, "Table", return_value=table):
        yield table


def test_create_task_returns_201(mock_table: MagicMock) -> None:
    event = {
        "body": json.dumps(
            {
                "title": "Learn AWS Lambda",
            }
        )
    }

    response = app.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 201
    assert body["title"] == "Learn AWS Lambda"
    assert body["completed"] is False
    assert isinstance(body["id"], str)
    assert "createdAt" in body

    mock_table.put_item.assert_called_once()

    saved_item = mock_table.put_item.call_args.kwargs["Item"]

    assert saved_item == body


def test_create_task_rejects_missing_title(mock_table: MagicMock) -> None:
    event = {
        "body": json.dumps({}),
    }

    response = app.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert body["error"] == (
        "title is required and must be a non-empty string"
    )

    mock_table.put_item.assert_not_called()


def test_create_task_rejects_invalid_json(mock_table: MagicMock) -> None:
    event = {
        "body": "{invalid-json",
    }

    response = app.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert body["error"] == "Request body must contain valid JSON"

    mock_table.put_item.assert_not_called()