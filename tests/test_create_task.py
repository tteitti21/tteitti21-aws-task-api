import json
import os
from unittest.mock import MagicMock, patch

import pytest


os.environ["TASKS_TABLE"] = "test-tasks-table"

from src.create_task import app


@pytest.fixture(autouse=True)
def disable_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.delenv("AUTH_TOKEN", raising=False)


@pytest.fixture
def mock_table() -> MagicMock:
    table = MagicMock()

    with patch.object(app, "get_tasks_table", return_value=table):
        yield table


def make_event(
    method: str,
    body: str | None = None,
    headers: dict[str, str] | None = None,
) -> dict:
    return {
        "requestContext": {
            "http": {
                "method": method,
            }
        },
        "headers": headers or {},
        "body": body,
    }


def test_auth_rejects_missing_token(
    monkeypatch: pytest.MonkeyPatch,
    mock_table: MagicMock,
) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_TOKEN", "secret-token")

    response = app.lambda_handler(make_event("GET"), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 401
    assert body == {"error": "Unauthorized"}
    mock_table.scan.assert_not_called()


def test_auth_rejects_wrong_token(
    monkeypatch: pytest.MonkeyPatch,
    mock_table: MagicMock,
) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_TOKEN", "secret-token")

    response = app.lambda_handler(
        make_event("GET", headers={"Authorization": "Bearer wrong-token"}),
        None,
    )
    body = json.loads(response["body"])

    assert response["statusCode"] == 401
    assert body == {"error": "Unauthorized"}
    mock_table.scan.assert_not_called()


def test_auth_allows_correct_token(
    monkeypatch: pytest.MonkeyPatch,
    mock_table: MagicMock,
) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_TOKEN", "secret-token")
    mock_table.scan.return_value = {"Items": []}

    response = app.lambda_handler(
        make_event("GET", headers={"Authorization": "Bearer secret-token"}),
        None,
    )

    assert response["statusCode"] == 200
    mock_table.scan.assert_called_once_with()


def test_auth_requires_configured_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.delenv("AUTH_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="AUTH_TOKEN is not set"):
        app.is_authorized(make_event("GET"))


def test_create_task_returns_201(mock_table: MagicMock) -> None:
    event = make_event(
        "POST",
        json.dumps(
            {
                "title": "Learn AWS Lambda",
            }
        ),
    )

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


def test_create_task_keeps_extra_request_fields(mock_table: MagicMock) -> None:
    event = make_event(
        "POST",
        json.dumps(
            {
                "title": "Learn AWS Lambda",
                "description": "Practice extra fields",
                "priority": "high",
                "tags": ["aws", "sam"],
            }
        ),
    )

    response = app.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 201
    assert body["description"] == "Practice extra fields"
    assert body["priority"] == "high"
    assert body["tags"] == ["aws", "sam"]

    saved_item = mock_table.put_item.call_args.kwargs["Item"]

    assert saved_item == body


def test_create_task_protects_server_controlled_fields(
    mock_table: MagicMock,
) -> None:
    event = make_event(
        "POST",
        json.dumps(
            {
                "id": "client-id",
                "title": "  Clean title  ",
                "completed": True,
                "createdAt": "client-time",
            }
        ),
    )

    response = app.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 201
    assert body["id"] != "client-id"
    assert body["title"] == "Clean title"
    assert body["completed"] is False
    assert body["createdAt"] != "client-time"

    saved_item = mock_table.put_item.call_args.kwargs["Item"]

    assert saved_item == body

def test_list_tasks_returns_200(mock_table: MagicMock) -> None:
    task = {
        "id": "task-1",
        "title": "Learn DynamoDB",
        "completed": False,
        "createdAt": "2026-07-12T00:00:00+00:00",
    }
    mock_table.scan.return_value = {"Items": [task]}

    response = app.lambda_handler(make_event("GET"), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body == {"tasks": [task]}
    mock_table.scan.assert_called_once_with()


def test_create_task_rejects_missing_title(mock_table: MagicMock) -> None:
    event = make_event("POST", json.dumps({}))

    response = app.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert body["error"] == (
        "title is required and must be a non-empty string"
    )

    mock_table.put_item.assert_not_called()


def test_create_task_rejects_invalid_json(mock_table: MagicMock) -> None:
    event = make_event("POST", "{invalid-json")

    response = app.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert body["error"] == "Request body must contain valid JSON"

    mock_table.put_item.assert_not_called()


def test_rejects_unsupported_method(mock_table: MagicMock) -> None:
    response = app.lambda_handler(make_event("DELETE"), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 405
    assert body == {"error": "Method DELETE is not allowed"}
    mock_table.put_item.assert_not_called()
    mock_table.scan.assert_not_called()
