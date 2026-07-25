import os


def get_boolean_env(name: str, default: str = "false") -> bool:
    value = os.getenv(name, default).strip().lower()

    if value not in {"true", "false"}:
        raise RuntimeError(f"{name} must be either 'true' or 'false'")

    return value == "true"
