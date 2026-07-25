import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .config import get_boolean_env
from .storage import get_tasks_table


def make_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Create an API Gateway-compatible HTTP response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }


def auth_enabled() -> bool:
    return get_boolean_env("AUTH_ENABLED")


def get_http_method(event: dict[str, Any]) -> str:
    return event.get("requestContext", {}).get("http", {}).get(
        "method",
        event.get("httpMethod", "POST"),
    )


def get_header(event: dict[str, Any], name: str) -> str | None:
    headers = event.get("headers") or {}

    for header_name, header_value in headers.items():
        if header_name.lower() == name.lower():
            return header_value

    return None


def is_authorized(event: dict[str, Any]) -> bool:
    if not auth_enabled():
        return True

    expected_token = os.getenv("AUTH_TOKEN")

    if not expected_token:
        raise RuntimeError("AUTH_ENABLED is true, but AUTH_TOKEN is not set")

    authorization = get_header(event, "Authorization")

    return authorization == f"Bearer {expected_token}"


def create_task(event: dict[str, Any]) -> dict[str, Any]:
    try:
        request_body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return make_response(
            400,
            {"error": "Request body must contain valid JSON"},
        )

    title = request_body.get("title")

    if not isinstance(title, str) or not title.strip():
        return make_response(
            400,
            {"error": "title is required and must be a non-empty string"},
        )

    task = {
        **request_body,
        "id": str(uuid4()),
        "title": title.strip(),
        "completed": False,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    table = get_tasks_table()

    table.put_item(
        Item=task,
        ConditionExpression="attribute_not_exists(id)",
    )

    return make_response(201, task)


def list_tasks() -> dict[str, Any]:
    table = get_tasks_table()
    response = table.scan()

    return make_response(200, {"tasks": response.get("Items", [])})


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Route task API requests."""
    if not is_authorized(event):
        return make_response(401, {"error": "Unauthorized"})

    method = get_http_method(event)

    if method == "POST":
        return create_task(event)

    if method == "GET":
        return list_tasks()

    return make_response(405, {"error": f"Method {method} is not allowed"})
