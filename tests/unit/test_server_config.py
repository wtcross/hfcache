"""Strict independent server policy and restart-only authority (API-005)."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from hfcache.errors import ConfigurationError
from hfcache.server_config import (
    InstalledPolicy,
    load_server_config,
    validate_server_config_mapping,
)

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"


def mapping() -> dict[str, Any]:
    return {"schema_version": 1, "credentials": {"writer": {"systemd_name": "rest-writer"}}}


def test_defaults_are_private_immutable_and_separate_from_archive_policy():
    config = validate_server_config_mapping(mapping())
    assert config.listener.unix_socket == Path("/run/hfcache/api.sock")
    assert config.listener.tcp_host == "127.0.0.1"
    assert config.listener.socket_mode == 0o660
    assert config.listener.allowed_origins == ()
    assert config.listener.trusted_proxies == ()
    assert config.limits.max_queued_operations == 16
    assert config.maintenance_enabled is False
    assert config.interactive_docs is False
    assert config.mcp_enabled is False
    with pytest.raises(ValidationError, match="frozen"):
        config.listener.tcp_host = "0.0.0.0"  # pyrefly: ignore[read-only]


@pytest.mark.parametrize("version", [None, True, False, "1", 1.0, 0, 2])
def test_schema_version_requires_integer_one(version):
    data = mapping() | {"schema_version": version}
    with pytest.raises(ConfigurationError) as caught:
        validate_server_config_mapping(data)
    assert caught.value.problems[0].code == "HFCFG004"


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        (None, "maintenance_enabled", "true"),
        (None, "interactive_docs", 1),
        (None, "mcp_enabled", 0),
        (None, "log_level", "trace"),
        ("limits", "metadata_workers", "4"),
        ("limits", "metadata_queue", True),
        ("limits", "max_page_size", 0),
        ("limits", "max_queued_operations", -1),
        ("limits", "max_request_bytes", 100000000),
        ("listener", "tcp_port", "8787"),
        ("listener", "tcp_port", 0),
        ("listener", "socket_mode", 0o666),
        ("listener", "socket_mode", 432.0),
        ("listener", "allowed_hosts", ["*"]),
        ("listener", "allowed_hosts", []),
        ("listener", "allowed_hosts", ["a", "a"]),
        ("listener", "allowed_hosts", ["https://example.com"]),
        ("listener", "allowed_hosts", ["example.com:443"]),
        ("listener", "allowed_origins", ["*"]),
        ("listener", "allowed_origins", ["null"]),
        ("listener", "allowed_origins", ["https://example.com/path"]),
        ("listener", "allowed_origins", ["https://example.com?token=opaque"]),
        ("listener", "allowed_origins", ["https://user:password@example.com"]),
        ("listener", "allowed_origins", ["https://example.com:0"]),
        ("listener", "allowed_origins", ["https://example.com:99999"]),
        ("listener", "trusted_proxies", ["*"]),
        ("listener", "trusted_proxies", ["0.0.0.0/0"]),
        ("listener", "trusted_proxies", ["::/0"]),
        ("listener", "trusted_proxies", ["some-proxy"]),
        ("listener", "root_path", "/prefix/"),
        ("listener", "root_path", "/a/../b"),
        ("listener", "root_path", "/%2e%2e"),
        ("listener", "root_path", "/a?token=x"),
    ],
)
def test_types_and_security_constraints_reject_without_coercion(section, key, value):
    data = mapping()
    target = data if section is None else data.setdefault(section, {})
    target[key] = value
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(data)


@pytest.mark.parametrize(
    "value", ["relative", "/", "/tmp/../x", "/tmp//x", "/tmp/", "/tmp/x\x00", "/tmp/x\\y", 1]
)
def test_paths_are_absolute_normalized_and_non_control(value):
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(mapping() | {"archive_config": value})


@pytest.mark.parametrize(
    "source",
    [
        {},
        {"file": "/tmp/a", "systemd_name": "b"},
        {"systemd_name": ".."},
        {"systemd_name": "a/b"},
        {"systemd_name": ""},
    ],
)
def test_credential_sources_are_explicit_and_unambiguous(source):
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(mapping() | {"credentials": {"writer": source}})


def test_missing_writer_cannot_enable_anonymous_rest():
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping({"schema_version": 1, "credentials": {}})


def test_each_listener_can_be_disabled_explicitly_but_not_both():
    unix_only = validate_server_config_mapping(mapping() | {"listener": {"tcp_enabled": False}})
    assert unix_only.listener.unix_address == Path("/run/hfcache/api.sock")
    assert unix_only.listener.tcp_address is None
    tcp_only = validate_server_config_mapping(mapping() | {"listener": {"unix_enabled": False}})
    assert tcp_only.listener.unix_address is None
    assert tcp_only.listener.tcp_address == ("127.0.0.1", 8787)
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(
            mapping() | {"listener": {"unix_enabled": False, "tcp_enabled": False}}
        )


def test_mcp_setting_requires_separate_source_but_creates_no_endpoint():
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(mapping() | {"mcp_enabled": True})
    data = mapping()
    data["mcp_enabled"] = True
    data["credentials"]["mcp_reader"] = {"systemd_name": "mcp-reader"}
    assert validate_server_config_mapping(data).mcp_enabled is True


def test_off_host_tcp_requires_tls_and_proxy_tls_is_local_explicit():
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(mapping() | {"listener": {"tcp_host": "0.0.0.0"}})
    direct = {
        "tcp_host": "0.0.0.0",
        "tls": {"certificate": "/etc/hfcache/tls.crt", "private_key": "/etc/hfcache/tls.key"},
    }
    assert validate_server_config_mapping(mapping() | {"listener": direct}).listener.tls
    for bad in (
        {"tcp_host": "127.0.0.1", "proxy_tls": True},
        {"tcp_host": "0.0.0.0", "proxy_tls": True, "trusted_proxies": ["127.0.0.1"]},
    ):
        with pytest.raises(ConfigurationError):
            validate_server_config_mapping(mapping() | {"listener": bad})
    proxy = {
        "tcp_host": "127.0.0.1",
        "proxy_tls": True,
        "trusted_proxies": ["127.0.0.1"],
        "root_path": "/hfcache",
        "allowed_hosts": ["archive.example.com"],
        "allowed_origins": ["https://archive.example.com"],
    }
    assert validate_server_config_mapping(mapping() | {"listener": proxy}).listener.proxy_tls


@given(
    st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=32, max_size=64
    )
)
def test_unknown_keys_values_and_literal_tokens_never_enter_config_diagnostics(secret):
    original = mapping() | {secret: {"token": secret}, "log_level": secret}
    data = copy.deepcopy(original)
    with pytest.raises(ConfigurationError) as caught:
        validate_server_config_mapping(data)
    assert secret not in str(caught.value)
    assert secret not in repr(caught.value)
    assert secret not in json.dumps(
        [problem.as_envelope_entry() for problem in caught.value.problems]
    )
    assert original == data


def test_malformed_toml_never_echoes_source_or_unregistered_secret(tmp_path):
    path = tmp_path / "server.toml"
    secret = "opaque-value-must-never-appear-in-a-diagnostic"
    path.write_text(f'schema_version=1\nsecret="{secret}" invalid')
    with pytest.raises(ConfigurationError) as caught:
        load_server_config(path)
    assert caught.value.problems[0].code == "HFCFG002"
    assert secret not in str(caught.value)


def test_shipped_example_matches_schema():
    assert (
        load_server_config(Path("packaging/server.toml")).credentials.writer.systemd_name
        == "rest-writer"
    )


def write_archive(path, *, root="/srv/hfcache", archive_id=ARCHIVE_ID, workers=4):
    path.write_text(
        f'schema_version=1\n[storage]\narchive_root="{root}"\narchive_id="{archive_id}"\n[sync]\nmax_workers={workers}\n'
    )


def test_policy_reload_freezes_each_valid_snapshot_and_secret_free_fingerprint(tmp_path):
    archive = tmp_path / "config.toml"
    write_archive(archive)
    server = validate_server_config_mapping(mapping() | {"archive_config": str(archive)})
    provider = InstalledPolicy.open(server)
    first = provider.snapshot()
    write_archive(archive, workers=8)
    second = provider.snapshot()
    assert first.config.sync.max_workers == 4
    assert second.config.sync.max_workers == 8
    assert first.fingerprint != second.fingerprint
    assert "rest-writer" not in first.fingerprint
    assert first.config.storage.archive_root == second.config.storage.archive_root


@pytest.mark.parametrize("authority", ["root", "uuid"])
def test_policy_cannot_hot_switch_root_or_uuid(tmp_path, authority):
    archive = tmp_path / "config.toml"
    write_archive(archive)
    provider = InstalledPolicy.open(
        validate_server_config_mapping(mapping() | {"archive_config": str(archive)})
    )
    first = provider.snapshot()
    write_archive(
        archive,
        root="/srv/elsewhere" if authority == "root" else "/srv/hfcache",
        archive_id="00000000-0000-4000-8000-000000000000" if authority == "uuid" else ARCHIVE_ID,
    )
    with pytest.raises(ConfigurationError, match="restart"):
        provider.snapshot()
    assert first.config.storage.archive_id == ARCHIVE_ID


def test_invalid_installed_policy_fails_fresh_snapshot_without_changing_previous(tmp_path):
    archive = tmp_path / "config.toml"
    write_archive(archive)
    provider = InstalledPolicy.open(
        validate_server_config_mapping(mapping() | {"archive_config": str(archive)})
    )
    snapshot = provider.snapshot()
    archive.write_text("malformed = [")
    with pytest.raises(ConfigurationError):
        provider.snapshot()
    assert snapshot.config.sync.max_workers == 4
    write_archive(archive, workers=8)
    assert provider.snapshot().config.sync.max_workers == 8
