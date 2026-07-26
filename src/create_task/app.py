import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .local import is_request_authorized
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



def get_http_method(event: dict[str, Any]) -> str:
    return event.get("requestContext", {}).get("http", {}).get(
        "method",
        event.get("httpMethod", "POST"),
    )


def get_path_parameter(event: dict[str, Any], name: str) -> str | None:
    return (event.get("pathParameters") or {}).get(name)


def is_single_task_request(event: dict[str, Any]) -> bool:
    route_key = event.get("routeKey")
    path_parameters = event.get("pathParameters") or {}

    return route_key == "GET /tasks/{id}" or "id" in path_parameters


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


def get_task(event: dict[str, Any]) -> dict[str, Any]:
    task_id = get_path_parameter(event, "id")

    if not isinstance(task_id, str) or not task_id.strip():
        return make_response(400, {"error": "Task id is required"})

    table = get_tasks_table()
    response = table.get_item(Key={"id": task_id.strip()})
    task = response.get("Item")

    if task is None:
        return make_response(404, {"error": "Task not found"})

    return make_response(200, task)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Route task API requests."""
    if not is_request_authorized(event):
        return make_response(401, {"error": "Unauthorized"})

    method = get_http_method(event)

    if method == "POST":
        return create_task(event)

    if method == "GET":
        if is_single_task_request(event):
            return get_task(event)

        return list_tasks()

    return make_response(405, {"error": f"Method {method} is not allowed"})
