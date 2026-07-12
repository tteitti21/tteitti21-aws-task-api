import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import boto3


dynamodb = boto3.resource("dynamodb")


def make_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Create an API Gateway-compatible HTTP response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Create and persist a new task."""
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
        "id": str(uuid4()),
        "title": title.strip(),
        "completed": False,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    table_name = os.environ["TASKS_TABLE"]
    table = dynamodb.Table(table_name)

    table.put_item(
        Item=task,
        ConditionExpression="attribute_not_exists(id)",
    )

    return make_response(201, task)