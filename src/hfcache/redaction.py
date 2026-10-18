"""Shared output sanitization for known credentials and sensitive fields (INV-002).

Opaque bearer values have no recognizable grammar. Trusted credential loaders
register their exact values; this module does not claim to recognize unknown
arbitrary secrets. The registry is process-private and never serialized.
"""

import re
from collections.abc import Mapping
from threading import RLock
from typing import Final

REDACTED: Final = "[redacted]"
SECRET_KEYS: Final = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "cookie",
        "credential",
        "header",
        "headers",
        "password",
        "secret",
        "token",
    }
)
_SECRET_VALUE = re.compile(r"(?:hf_[A-Za-z0-9]{8,}|bearer\s+\S+)", re.IGNORECASE)
_SIGNED_URL = re.compile(
    r"https?://\S*[?&](?:x-amz-|x-goog-|sig=|signature=|token=)", re.IGNORECASE
)
_registered: set[str] = set()
_registry_lock = RLock()


def register_secret(value: str) -> None:
    """Register a resolved credential before any use or possible exception output."""
    if not value:
        message = "an empty value cannot be registered as a credential"
        raise ValueError(message)
    with _registry_lock:
        _registered.add(value)


def clear_registered_secrets() -> None:
    """Clear only at process teardown or between isolated tests, never per request."""
    with _registry_lock:
        _registered.clear()


def redact_text(value: str) -> str:
    """Remove known literals and legacy recognizable credential/URL shapes."""
    with _registry_lock:
        secrets = tuple(sorted(_registered, key=lambda item: (-len(item), item)))
    for secret in secrets:
        value = value.replace(secret, REDACTED)
    if _SECRET_VALUE.search(value) or _SIGNED_URL.search(value):
        return REDACTED
    return value


def sanitize(value: object, *, key: str | None = None) -> object:
    """Copy nested diagnostic data, removing sensitive keys, literals and exceptions."""
    if key is not None and (
        key.lower() in SECRET_KEYS or key.lower().endswith(("_token", "_password", "_secret"))
    ):
        return REDACTED
    if isinstance(value, Mapping):
        return {
            redact_text(str(name)): sanitize(item, key=str(name)) for name, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact_text(str(value))
