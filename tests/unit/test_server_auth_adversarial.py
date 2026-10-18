"""API bearer authority survives hostile credential paths and inputs (INV-002/013)."""

import os
import socket
import stat
from contextlib import suppress
from types import SimpleNamespace

import pytest

from hfcache.api import auth
from hfcache.errors import ConfigurationError
from hfcache.server_config import validate_server_config_mapping

WRITER = "writer_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
READER = "reader_9876543210zyxwvutsrqponmlkjihgfedcbaZYXWVU"
MCP = "mcp_reader_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabc"


def _token(path, value=WRITER, *, mode=0o600):
    path.write_text(value + "\n", encoding="ascii")
    path.chmod(mode)
    return path


def _config(writer, reader=None, mcp=None):
    credentials = {"writer": {"file": str(writer)}}
    if reader is not None:
        credentials["reader"] = {"file": str(reader)}
    if mcp is not None:
        credentials["mcp_reader"] = {"file": str(mcp)}
    return validate_server_config_mapping(
        {"schema_version": 1, "credentials": credentials, "mcp_enabled": mcp is not None}
    )


@pytest.fixture
def registry(tmp_path):
    writer = _token(tmp_path / "writer", WRITER)
    reader = _token(tmp_path / "reader", READER)
    mcp = _token(tmp_path / "mcp", MCP)
    return auth.load_credentials(_config(writer, reader, mcp))


@pytest.mark.parametrize("mode", [0o400, 0o440, 0o600, 0o640])
def test_protected_regular_file_modes_read_one_exact_token(tmp_path, mode):
    path = _token(tmp_path / "writer", mode=mode)

    assert auth.read_protected_token(path) == WRITER


@pytest.mark.parametrize("mode", [0o000, 0o200, 0o420, 0o604, 0o620, 0o644, 0o660, 0o700])
def test_unprotected_or_unexpected_modes_fail_closed_without_token_echo(tmp_path, mode):
    path = _token(tmp_path / "writer", mode=mode)

    with pytest.raises(ConfigurationError) as failure:
        auth.read_protected_token(path)

    assert WRITER not in str(failure.value)
    assert WRITER not in repr(failure.value)


@pytest.mark.parametrize("shape", ["directory", "fifo", "socket", "symlink", "hardlink"])
def test_credential_sources_must_be_unlinked_regular_inodes(tmp_path, shape):
    path = tmp_path / "credential"
    listener = None
    if shape == "directory":
        path.mkdir()
    elif shape == "fifo":
        os.mkfifo(path, mode=0o600)
    elif shape == "socket":
        listener = socket.socket(socket.AF_UNIX)
        listener.bind(str(path))
    elif shape == "symlink":
        path.symlink_to(_token(tmp_path / "target"))
    else:
        path.hardlink_to(_token(tmp_path / "target"))
    try:
        with pytest.raises(ConfigurationError):
            auth.read_protected_token(path)
    finally:
        if listener is not None:
            listener.close()


def test_a_symlink_parent_cannot_redirect_credential_loading(tmp_path):
    directory = tmp_path / "actual"
    directory.mkdir()
    _token(directory / "writer")
    parent = tmp_path / "redirect"
    parent.symlink_to(directory, target_is_directory=True)

    with pytest.raises(ConfigurationError):
        auth.read_protected_token(parent / "writer")


@pytest.mark.parametrize("field", ["st_uid", "st_gid"])
def test_credential_owner_and_readable_group_must_be_trusted(tmp_path, monkeypatch, field):
    path = _token(tmp_path / "writer", mode=0o640)
    original = auth.os.fstat
    untrusted_id = max(os.geteuid(), os.getegid(), *os.getgroups()) + 100000

    def wrong_owner(descriptor):
        actual = original(descriptor)
        values = {
            name: getattr(actual, name)
            for name in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_uid",
                "st_gid",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        }
        values[field] = untrusted_id
        return SimpleNamespace(**values)

    monkeypatch.setattr(auth.os, "fstat", wrong_owner)
    with pytest.raises(ConfigurationError):
        auth.read_protected_token(path)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"\n",
        b"a" * 31,
        b"a" * 4098,
        b"\xff" * 40,
        b"a" * 40 + b"\r\n",
        b"a" * 40 + b"\n\n",
        b"a" * 20 + b" " + b"b" * 20,
        b"hf_" + b"a" * 40,
    ],
    ids=[
        "empty",
        "linefeed-only",
        "too-short",
        "too-large",
        "non-ascii",
        "crlf",
        "double-lf",
        "space",
        "hub-token",
    ],
)
def test_malformed_or_recognizable_hub_credentials_are_classified_refusals(tmp_path, raw):
    path = tmp_path / "writer"
    path.write_bytes(raw)
    path.chmod(0o600)

    with pytest.raises(ConfigurationError) as failure:
        auth.read_protected_token(path)

    assert failure.value.problems[0].code == "HFAPI003"


def test_credential_read_pins_the_open_inode_across_path_replacement(tmp_path, monkeypatch):
    path = _token(tmp_path / "writer", WRITER)
    original_open = auth.os.open
    changed = False

    def replace_after_open(name, flags, *, dir_fd=None):
        nonlocal changed
        descriptor = original_open(name, flags, dir_fd=dir_fd)
        if name == path.name and flags & os.O_NOFOLLOW and not flags & os.O_DIRECTORY:
            changed = True
            path.rename(tmp_path / "original-inode")
            _token(path, READER)
        return descriptor

    monkeypatch.setattr(auth.os, "open", replace_after_open)

    assert auth.read_protected_token(path) == WRITER
    assert changed
    assert path.read_text(encoding="ascii").strip() == READER


@pytest.mark.parametrize("mutation", ["same-size-rewrite", "growth"])
def test_descriptor_metadata_and_bounded_reads_refuse_concurrent_changes(
    tmp_path, monkeypatch, mutation
):
    path = _token(tmp_path / "writer", WRITER)
    original_read = auth.os.read
    changed = False
    requested = []

    def rewrite_before_read(descriptor, count):
        nonlocal changed
        requested.append(count)
        if not changed:
            changed = True
            before = os.fstat(descriptor)
            replacement = (
                "z" * len(WRITER) + "\n"
                if mutation == "same-size-rewrite"
                else "z" * (auth.MAXIMUM_TOKEN_FILE_BYTES + 100)
            )
            path.write_text(replacement, encoding="ascii")
            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
        return original_read(descriptor, count)

    monkeypatch.setattr(auth.os, "read", rewrite_before_read)
    with pytest.raises(ConfigurationError):
        auth.read_protected_token(path)

    assert changed
    assert all(0 < count <= auth.MAXIMUM_TOKEN_FILE_BYTES + 1 for count in requested)


@pytest.mark.parametrize("credential", [WRITER, READER, MCP])
def test_capabilities_and_interface_boundaries_are_explicit(registry, credential):
    expected = {
        WRITER: (auth.CredentialClass.REST_WRITER, {auth.Capability.READ, auth.Capability.WRITE}),
        READER: (auth.CredentialClass.REST_READER, {auth.Capability.READ}),
        MCP: (auth.CredentialClass.MCP_READER, {auth.Capability.MCP_READ}),
    }
    credential_class, capabilities = expected[credential]
    interface = "mcp" if credential == MCP else "rest"
    principal = auth.authenticate_bearer(registry, f"Bearer {credential}", interface=interface)

    assert principal.credential_class == credential_class
    assert principal.capabilities == frozenset(capabilities)
    for capability in auth.Capability:
        if capability in capabilities:
            assert auth.require_capability(principal, capability) is principal
        else:
            with pytest.raises(auth.AuthorizationError) as failure:
                auth.require_capability(principal, capability)
            assert failure.value.status_code == 403
            assert not failure.value.headers
    with pytest.raises(auth.AuthenticationError):
        auth.authenticate_bearer(
            registry, f"Bearer {credential}", interface="rest" if interface == "mcp" else "mcp"
        )


@pytest.mark.parametrize(
    "header",
    [
        None,
        "",
        WRITER,
        f"Basic {WRITER}",
        "Bearer",
        f"Bearer  {WRITER}",
        f"Bearer {WRITER} extra",
        f"Bearer {WRITER}\r\nInjected: value",
        "Bearer " + "z" * 5000,
        "Bearer " + "é" * 40,
        "Bearer " + "unknown_" * 6,
    ],
    ids=[
        "missing",
        "empty",
        "no-scheme",
        "basic",
        "missing-token",
        "extra-space",
        "suffix",
        "crlf",
        "too-large",
        "non-ascii",
        "unknown",
    ],
)
def test_every_missing_wrong_or_malformed_bearer_has_the_same_safe_challenge(registry, header):
    with pytest.raises(auth.AuthenticationError) as failure:
        auth.authenticate_bearer(registry, header)

    assert failure.value.status_code == 401
    assert failure.value.headers["WWW-Authenticate"].startswith("Bearer")
    assert failure.value.detail == "Not authenticated"
    assert failure.value.problems[0].code == "HFAPI001"
    assert WRITER not in repr(failure.value)


def test_all_fixed_slots_use_equal_length_constant_time_comparisons(registry, monkeypatch):
    original = auth.hmac.compare_digest
    calls = []

    def record(first, second):
        calls.append((len(first), len(second)))
        return original(first, second)

    monkeypatch.setattr(auth.hmac, "compare_digest", record)
    for credential in (WRITER, READER, MCP, "unknown_" * 6):
        calls.clear()
        with suppress(auth.AuthenticationError):
            auth.authenticate_bearer(registry, f"Bearer {credential}")
        assert calls == [(32, 32)] * 3


def test_missing_optional_class_never_falls_back_to_ambient_credentials(tmp_path):
    path = _token(tmp_path / "writer")
    registry = auth.load_credentials(
        _config(path),
        environ={"HF_TOKEN": READER, "HUGGING_FACE_HUB_TOKEN": READER, "API_TOKEN": READER},
    )
    with pytest.raises(auth.AuthenticationError):
        registry.authenticate(f"Bearer {READER}")

    assert WRITER not in repr(registry)
    assert READER not in repr(registry)
    assert (
        registry.authenticate(f"Bearer {WRITER}").credential_class
        is auth.CredentialClass.REST_WRITER
    )


@pytest.mark.parametrize("reader", [None, "absent", "duplicate"])
def test_missing_writer_or_configured_unusable_and_duplicate_classes_refuse_startup(
    tmp_path, reader
):
    writer = tmp_path / "writer"
    if reader is None:
        server = _config(writer)
    elif reader == "absent":
        _token(writer)
        server = _config(writer, tmp_path / "missing-reader")
    else:
        _token(writer)
        server = _config(writer, _token(tmp_path / "reader", WRITER))

    with pytest.raises(ConfigurationError) as failure:
        auth.load_credentials(server, environ={"HF_TOKEN": WRITER})

    assert WRITER not in str(failure.value)
    assert WRITER not in repr(failure.value)


def test_named_systemd_sources_are_explicit_and_never_use_a_relative_directory(tmp_path):
    _token(tmp_path / "writer")
    server = validate_server_config_mapping(
        {"schema_version": 1, "credentials": {"writer": {"systemd_name": "writer"}}}
    )
    for environment in ({}, {"CREDENTIALS_DIRECTORY": "relative"}):
        with pytest.raises(ConfigurationError):
            auth.load_credentials(server, environ=environment)
    registry = auth.load_credentials(server, environ={"CREDENTIALS_DIRECTORY": str(tmp_path)})
    assert (
        registry.authenticate(f"Bearer {WRITER}").credential_class
        is auth.CredentialClass.REST_WRITER
    )


@pytest.mark.parametrize(
    "directory",
    [None, "", "relative-secret-directory", "/tmp/secret\x00directory", "/tmp/secret\ndirectory"],
    ids=["missing", "empty", "relative", "nul", "newline"],
)
def test_malformed_systemd_directory_is_a_safe_refusal_before_filesystem_access(
    monkeypatch, directory
):
    server = validate_server_config_mapping(
        {"schema_version": 1, "credentials": {"writer": {"systemd_name": "writer"}}}
    )

    def unexpected_open(*args, **kwargs):
        pytest.fail("malformed systemd credential directory reached filesystem access")

    monkeypatch.setattr(auth.os, "open", unexpected_open)
    environment = {} if directory is None else {"CREDENTIALS_DIRECTORY": directory}
    with pytest.raises(ConfigurationError) as failure:
        auth.load_credentials(server, environ=environment)

    assert failure.value.problems[0].code == "HFAPI003"
    if directory:
        assert directory not in str(failure.value)
        assert directory not in repr(failure.value)


def test_protected_token_helpers_never_change_a_checked_inode(tmp_path):
    path = _token(tmp_path / "writer")
    before = path.stat()
    content = path.read_bytes()
    auth.read_protected_token(path)

    assert path.read_bytes() == content
    assert stat.S_IMODE(path.stat().st_mode) == stat.S_IMODE(before.st_mode)


@pytest.mark.parametrize("control", ["\x00", "\x01", "\x1f", "\x7f", "\r", "\n"])
@pytest.mark.parametrize("setting", ["root_path", "allowed_hosts", "allowed_origins"])
def test_listener_text_rejects_controls_before_url_normalization(tmp_path, control, setting):
    writer = _token(tmp_path / "writer")
    value = {
        "root_path": f"/api{control}x",
        "allowed_hosts": [f"example{control}.invalid"],
        "allowed_origins": [f"https://example{control}.invalid"],
    }[setting]

    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(
            {
                "schema_version": 1,
                "credentials": {"writer": {"file": str(writer)}},
                "listener": {setting: value},
            }
        )


@pytest.mark.parametrize(
    "invalid", ["relative", "/tmp/../secret", "/tmp/secret\x00value", "/tmp/secret\nvalue"]
)
@pytest.mark.parametrize(
    "setting", ["archive_config", "unix_socket", "credential", "certificate", "private_key"]
)
def test_credential_tls_and_runtime_paths_refuse_invalid_values_before_io(
    tmp_path, invalid, setting
):
    writer = _token(tmp_path / "writer")
    mapping = {"schema_version": 1, "credentials": {"writer": {"file": str(writer)}}}
    if setting == "archive_config":
        mapping["archive_config"] = invalid
    elif setting == "credential":
        mapping["credentials"]["writer"]["file"] = invalid
    elif setting == "unix_socket":
        mapping["listener"] = {"unix_socket": invalid}
    else:
        mapping["listener"] = {
            "tls": {"certificate": "/tmp/certificate.pem", "private_key": "/tmp/key.pem"}
        }
        mapping["listener"]["tls"][setting] = invalid

    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(mapping)
