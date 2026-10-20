"""Narrow authenticated client-authority presentation for Cockpit recovery (CP-08)."""

import hashlib
import json
from typing import TYPE_CHECKING, Any

import httpx

from hfcache.client_config import DEFAULT_CLIENT_CONFIG
from hfcache.client_errors import ClientProtocolError
from hfcache.client_models import Capabilities
from hfcache.errors import ConfigurationError
from hfcache.redaction import redact_text

if TYPE_CHECKING:
    from pathlib import Path

    from hfcache.client import ApiClient
    from hfcache.client_config import ClientConfig
    from hfcache.reporting import Envelope


def _endpoint(config: ClientConfig) -> str:
    # ClientConfig has already refused userinfo, query, fragment, remote HTTP,
    # escaping paths and unsafe lengths. HTTPX canonicalizes its actual URL.
    try:
        endpoint = (
            "unix:" + str(config.socket)
            if config.socket is not None
            else str(httpx.URL(config.url)).rstrip("/")
        )
    except httpx.InvalidURL:
        message = "API client endpoint cannot be represented safely"
        raise ConfigurationError.single(message, code="HFAPI017") from None
    if redact_text(endpoint) != endpoint:
        message = "API endpoint contains credential material"
        raise ConfigurationError.single(message, code="HFAPI017")
    return endpoint


def describe_client(client: ApiClient, settings_path: Path | None) -> dict[str, Any] | Envelope:
    """Present allowlisted authority; failed server Envelopes remain exact (INV-006)."""
    endpoint = _endpoint(client.config)
    response = client.read("/api/v1/capabilities")
    if response.envelope.exit_code:
        return response.envelope
    try:
        capabilities = Capabilities.model_validate(response.envelope.data)
    except ValueError:
        raise ClientProtocolError from None
    if response.envelope.command != "capabilities" or not capabilities.reads:
        raise ClientProtocolError
    version = client.version()
    if version.envelope.exit_code:
        return version.envelope
    if version.envelope.command != "version":
        raise ClientProtocolError
    authority = {
        "metadata_schema_version": 1,
        "endpoint": endpoint,
        "selected_settings": str(settings_path or DEFAULT_CLIENT_CONFIG),
        "expected_archive_id": client.config.expected_archive_id,
        "credential_class": capabilities.credential_class,
        "ca_file": str(client.config.ca_file) if client.config.ca_file is not None else None,
    }
    fingerprint = hashlib.sha256(
        json.dumps(authority, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    metadata = {
        "metadata_schema_version": 1,
        "profile_fingerprint": fingerprint,
        "endpoint": endpoint,
        "credential_class": capabilities.credential_class,
        "archive_id": version.archive_id,
        "instance_id": capabilities.instance_id,
    }
    metadata["authority_fingerprint"] = hashlib.sha256(
        json.dumps(
            {key: value for key, value in metadata.items() if key != "instance_id"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    # Public hashes/identifiers can still equal a registered opaque credential.
    # Refuse the whole presentation instead of emitting a redacted authority pin.
    if any(isinstance(value, str) and redact_text(value) != value for value in metadata.values()):
        message = "API client authority metadata contains credential material"
        raise ConfigurationError.single(message, code="HFAPI017")
    return metadata
