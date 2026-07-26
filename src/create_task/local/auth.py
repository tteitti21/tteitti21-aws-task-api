import os
from typing import Any

from ..config import get_boolean_env


def get_header(event: dict[str, Any], name: str) -> str | None:
    headers = event.get("headers") or {}

    for header_name, header_value in headers.items():
        if header_name.lower() == name.lower():
            return header_value

    return None


def is_request_authorized(event: dict[str, Any]) -> bool:
    """Apply the shared-token check only when local auth is enabled."""
    if not get_boolean_env("LOCAL_AUTH_ENABLED"):
        return True

    expected_token = os.getenv("LOCAL_AUTH_TOKEN")

    if not expected_token:
        raise RuntimeError(
            "LOCAL_AUTH_ENABLED is true, but LOCAL_AUTH_TOKEN is not set"
        )

    authorization = get_header(event, "Authorization")
    return authorization == f"Bearer {expected_token}"