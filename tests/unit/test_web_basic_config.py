"""Strict restart-only Basic origin/source policy without credential or DNS I/O."""

import copy
import json
import secrets
import socket
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest
from pydantic import ValidationError

from hfcache.api import credential_sources
from hfcache.errors import ConfigurationError
from hfcache.server_config import BasicConfig, validate_server_config_mapping


def mapping(origin="https://archive.example") -> dict[str, Any]:
    hostname = urlsplit(origin).hostname or "archive.example"
    host = f"[{hostname}]" if ":" in hostname else hostname
    return {
        "schema_version": 1,
        "credentials": {"writer": {"systemd_name": "rest-writer"}},
        "basic": {"origin": origin, "administrator": {"systemd_name": "ui-admin"}},
        "listener": {"allowed_hosts": [host], "allowed_origins": [origin]},
    }


@pytest.mark.parametrize(
    "origin",
    [
        "https://archive.example",
        "https://archive.example:8443",
        "https://localhost",
        "https://localhost:444",
        "https://127.0.0.1",
        "https://192.0.2.1:65535",
        "https://[::1]",
        "https://[::1]:8443",
        "https://[2001:db8::1]",
        "https://[2001:db8::1]:9443",
        "https://xn--bcher-kva.example",
    ],
)
def test_canonical_https_dns_ip_and_nondefault_ports_remain_exact(origin):
    settings = validate_server_config_mapping(mapping(origin))
    assert settings.basic is not None
    assert settings.basic.origin == origin
    assert settings.basic.administrator.systemd_name == "ui-admin"


@pytest.mark.parametrize(
    "origin",
    [
        "http://archive.example",
        "HTTPS://archive.example",
        "https://ARCHIVE.example",
        "https://archive.example/",
        "https://archive.example/path",
        "https://archive.example?query",
        "https://archive.example#fragment",
        "https://archive.example?",
        "https://archive.example#",
        "https://user@archive.example",
        "https://user:private@archive.example",
        "https://archive.example:443",
        "https://archive.example:08443",
        "https://archive.example:0",
        "https://archive.example:65536",
        "https://archive.example:",
        "https://127.000.000.001",
        "https://2130706433",
        "https://0x7f000001",
        "https://[2001:0db8:0:0:0:0:0:1]",
        "https://[2001:DB8::1]",
        "https://[::ffff:192.0.2.1]",
        "https://[fe80::1%25eth0]",
        "https://b\u00fccher.example",
        "https://%61rchive.example",
        "https://archive.example\\@other.example",
        " https://archive.example",
        "https://archive.example ",
        "https://archive.example\t",
        "https://archive.example\n",
        "https://archive.example\x00",
        "https://archive.example\x7f",
        "https:///archive.example",
        "https:archive.example",
        "//archive.example",
        "null",
        "*",
    ],
)
def test_noncanonical_unsafe_or_normalized_origin_is_refused(origin):
    data = mapping()
    data["basic"]["origin"] = origin
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(data)


@pytest.mark.parametrize("value", [None, True, 1, 1.0, b"https://archive.example", [], {}])
def test_origin_does_not_coerce_non_strings(value):
    data = mapping()
    data["basic"]["origin"] = value
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(data)


@pytest.mark.parametrize(
    "source",
    [
        {},
        {"file": "/owned/record", "systemd_name": "ui-admin"},
        {"file": "relative"},
        {"file": "/owned/../record"},
        {"file": "/owned/record\x00"},
        {"file": "/owned/record\n"},
        {"file": True},
        {"systemd_name": ""},
        {"systemd_name": ".."},
        {"systemd_name": "a/b"},
        {"systemd_name": "a" * 65},
        {"systemd_name": 1},
        {"password": "untrusted-input"},
        {"password_hash": "untrusted-input"},
    ],
)
def test_administrator_has_one_explicit_protected_source(source):
    data = mapping()
    data["basic"]["administrator"] = source
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(data)


@pytest.mark.parametrize(
    "change",
    [
        {"allowed_hosts": ["other.example"]},
        {"allowed_origins": ["https://other.example"]},
        {"allowed_origins": []},
        {"allowed_origins": ["https://archive.example:8443"]},
    ],
)
def test_origin_must_match_both_independent_listener_policies(change):
    data = mapping()
    data["listener"].update(change)
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(data)


def test_optional_basic_and_both_source_types_validate_without_io(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("server configuration validation accessed filesystem or network")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(credential_sources.os, "open", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    original = mapping()
    snapshot = copy.deepcopy(original)
    named = validate_server_config_mapping(original)
    assert original == snapshot
    assert named.basic is not None
    explicit = mapping()
    explicit["basic"]["administrator"] = {"file": "/not-accessed/administrator.json"}
    assert validate_server_config_mapping(explicit).basic is not None
    del original["basic"]
    assert validate_server_config_mapping(original).basic is None
    original["basic"] = None
    assert validate_server_config_mapping(original).basic is None


def test_basic_configuration_is_frozen_and_diagnostics_omit_unknown_names_and_values():
    settings = BasicConfig.model_validate(mapping()["basic"])
    with pytest.raises(ValidationError):
        settings.origin = "https://other.example"  # pyrefly: ignore[read-only]
    marker = secrets.token_hex(24)
    for change in (
        {marker: marker},
        {"origin": "https://" + marker + ".example/path"},
        {"administrator": {marker: marker}},
        {"administrator": {"file": marker}},
    ):
        data = mapping()
        data["basic"].update(change)
        with pytest.raises(ConfigurationError) as failure:
            validate_server_config_mapping(data)
        diagnostics = json.dumps(
            [problem.as_envelope_entry() for problem in failure.value.problems]
        )
        assert marker not in diagnostics
        assert marker not in str(failure.value)
        assert marker not in repr(failure.value)
        assert all(problem.code in {"HFCFG003", "HFCFG005"} for problem in failure.value.problems)


@pytest.mark.parametrize(
    "value", [True, "enabled", [], {"administrator": {"systemd_name": "ui-admin"}}]
)
def test_basic_object_is_strict_and_cannot_replace_required_writer(value):
    data = mapping()
    data["basic"] = value
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(data)
    data = mapping()
    data["credentials"] = {}
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(data)
