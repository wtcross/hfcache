"""Actual Argon2id and protected single-administrator source boundaries."""

import asyncio
import base64
import json
import secrets

import pytest
from pydantic import ValidationError

from hfcache import redaction
from hfcache.api import basic, credential_sources
from hfcache.api.auth import AdminCapability, AuthenticationMethod, Capability, CredentialClass
from hfcache.api.basic import (
    BasicProvider,
    ProtectedAdministratorRecord,
    create_administrator_record,
    load_basic_provider,
)
from hfcache.errors import AuthenticationError, ConfigurationError
from hfcache.server_config import BasicConfig


@pytest.fixture(scope="module")
def administrator():
    password = secrets.token_urlsafe(32).encode("utf-8")
    return create_administrator_record("human:fixture-1", "operator", password), password


def authorization(username, password):
    return "Basic " + base64.b64encode(username.encode("utf-8") + b":" + password).decode("ascii")


def config(path):
    return BasicConfig.model_validate(
        {"origin": "https://archive.example", "administrator": {"file": str(path)}}
    )


def write_record(path, record):
    path.write_text(record.model_dump_json() + "\n", encoding="utf-8")
    path.chmod(0o600)
    return path


def test_disabled_provider_accesses_no_source(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("disabled provider accessed a credential source")

    monkeypatch.setattr(basic, "read_protected_bytes", forbidden)
    assert load_basic_provider(None, environ={}) is None


def test_actual_hash_and_both_source_profiles_authenticate_without_legacy_grant_changes(
    tmp_path, administrator
):
    record, password = administrator
    path = write_record(tmp_path / "ui-admin", record)
    named = BasicConfig.model_validate(
        {"origin": "https://archive.example", "administrator": {"systemd_name": "ui-admin"}}
    )

    async def exercise():
        for settings, environ in (
            (config(path), {}),
            (named, {"CREDENTIALS_DIRECTORY": str(tmp_path)}),
        ):
            provider = load_basic_provider(settings, environ=environ)
            assert provider is not None
            try:
                principal = await provider.authenticate(authorization(record.username, password))
                assert principal.subject == record.subject
                assert principal.authentication_method is AuthenticationMethod.BASIC
                assert principal.credential_class is CredentialClass.REST_WRITER
                assert principal.capabilities == frozenset({Capability.READ, Capability.WRITE})
                assert principal.admin_capabilities == frozenset(AdminCapability)
                assert provider.stats.active == provider.stats.waiting == 0
            finally:
                await provider.aclose()

    asyncio.run(exercise())


def test_wrong_user_and_wrong_password_use_one_hash_and_uniform_failure(administrator):
    record, password = administrator
    supplied = []

    def verify(value):
        supplied.append(value)
        return value == password

    async def exercise():
        provider = BasicProvider(record, verify=verify)
        wrong = secrets.token_urlsafe(32).encode()
        try:
            for username, value in (("another-user", password), (record.username, wrong)):
                with pytest.raises(AuthenticationError) as failure:
                    await provider.authenticate(authorization(username, value))
                assert failure.value.status_code == 401
                assert value.decode() not in str(failure.value)
            assert supplied == [password, wrong]
            assert provider.stats.failures == 2
        finally:
            await provider.aclose()

    asyncio.run(exercise())


def test_actual_wrong_username_still_performs_actual_hash(administrator, monkeypatch):
    record, password = administrator
    original = basic.Argon2id
    calls = []

    class ObservedArgon:
        def __new__(cls, **kwargs):
            return original(**kwargs)

        @staticmethod
        def verify_phc_encoded(value, phc):
            calls.append(phc)
            return original.verify_phc_encoded(value, phc)

    monkeypatch.setattr(basic, "Argon2id", ObservedArgon)

    async def exercise():
        provider = BasicProvider(record)
        try:
            with pytest.raises(AuthenticationError):
                await provider.authenticate(authorization("wrong-user", password))
            with pytest.raises(AuthenticationError):
                await provider.authenticate(
                    authorization(record.username, secrets.token_urlsafe(32).encode())
                )
            assert calls == [record.password_hash, record.password_hash]
        finally:
            await provider.aclose()

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "change",
    [
        lambda _: {},
        lambda value: value | {"schema_version": True},
        lambda value: value | {"schema_version": 1.0},
        lambda value: value | {"schema_version": "1"},
        lambda value: value | {"unknown": "private-input"},
        lambda value: value | {"subject": ""},
        lambda value: value | {"subject": "\u00e9"},
        lambda value: value | {"subject": "a" * 129},
        lambda value: value | {"subject": ".leading"},
        lambda value: value | {"username": ""},
        lambda value: value | {"username": "user:name"},
        lambda value: value | {"username": "user\n"},
        lambda value: value | {"username": "\u00e9" * 65},
        lambda value: value | {"username": 1},
        lambda value: (
            value | {"password_hash": value["password_hash"].replace("argon2id", "argon2i")}
        ),
        lambda value: value | {"password_hash": value["password_hash"].replace("v=19", "v=16")},
        lambda value: value | {"password_hash": value["password_hash"].replace("65536", "655360")},
        lambda value: value | {"password_hash": value["password_hash"].replace("t=3", "t=4")},
        lambda value: value | {"password_hash": value["password_hash"].replace("p=1", "p=2")},
        lambda value: (
            value | {"password_hash": value["password_hash"].replace("m=65536,t=3", "t=3,m=65536")}
        ),
        lambda value: value | {"password_hash": value["password_hash"].replace("t=3", "t=3,t=3")},
        lambda value: value | {"password_hash": value["password_hash"] + "="},
        lambda value: value | {"password_hash": value["password_hash"] + "$extra"},
        lambda value: value | {"password_hash": value["password_hash"] + "\n"},
        lambda value: (
            value
            | {
                "password_hash": "$argon2id$v=19$m=65536,t=3,p=1$"
                + base64.b64encode(b"a" * 15).decode().rstrip("=")
                + "$"
                + value["password_hash"].split("$")[-1]
            }
        ),
        lambda value: (
            value
            | {
                "password_hash": value["password_hash"].rsplit("$", 1)[0]
                + "$"
                + base64.b64encode(b"a" * 31).decode().rstrip("=")
            }
        ),
        lambda value: (
            value
            | {
                "password_hash": "$argon2id$v=19$m=65536,t=3,p=1$"
                + "_" * 22
                + "$"
                + value["password_hash"].split("$")[-1]
            }
        ),
    ],
)
def test_record_refuses_schema_identity_and_unbounded_or_noncanonical_phc_before_backend(
    tmp_path, administrator, monkeypatch, change
):
    record, _ = administrator
    path = tmp_path / "ui-admin"
    path.write_text(json.dumps(change(record.model_dump())))
    path.chmod(0o600)

    def forbidden(*args, **kwargs):
        pytest.fail("invalid record reached Argon2")

    monkeypatch.setattr(basic, "Argon2id", forbidden)
    with pytest.raises(ConfigurationError) as failure:
        load_basic_provider(config(path))
    assert failure.value.problems[0].code == "HFAPI003"
    assert record.password_hash not in str(failure.value)


@pytest.mark.parametrize(
    "contents",
    [b"", b"\xff", b"[]", b"[" * 1200, b" " * 8193, b'{"schema_version":1,"schema_version":1}'],
)
def test_record_refuses_bad_bytes_duplicates_and_resource_ceiling(tmp_path, contents):
    path = tmp_path / "ui-admin"
    path.write_bytes(contents)
    path.chmod(0o600)
    with pytest.raises(ConfigurationError) as failure:
        load_basic_provider(config(path))
    assert failure.value.problems[0].code == "HFAPI003"


@pytest.mark.parametrize(
    "shape", ["symlink", "parent-symlink", "hardlink", "directory", "world-readable"]
)
def test_record_source_uses_protected_descriptor_policy(tmp_path, administrator, shape):
    record, _ = administrator
    actual = write_record(tmp_path / "actual", record)
    source = tmp_path / "ui-admin"
    if shape == "symlink":
        source.symlink_to(actual)
    elif shape == "parent-symlink":
        directory = tmp_path / "owned"
        directory.mkdir()
        write_record(directory / "ui-admin", record)
        source.symlink_to(directory, target_is_directory=True)
        source /= "ui-admin"
    elif shape == "hardlink":
        source.hardlink_to(actual)
    elif shape == "directory":
        source.mkdir()
    else:
        source = actual
        source.chmod(0o644)
    with pytest.raises(ConfigurationError):
        load_basic_provider(config(source))


def test_in_place_record_change_is_refused(tmp_path, administrator, monkeypatch):
    record, _ = administrator
    path = write_record(tmp_path / "ui-admin", record)
    original = credential_sources.os.read
    changed = False

    def read_and_change(descriptor, count):
        nonlocal changed
        result = original(descriptor, count)
        if not changed:
            changed = True
            path.write_bytes(path.read_bytes() + b" ")
        return result

    monkeypatch.setattr(credential_sources.os, "read", read_and_change)
    with pytest.raises(ConfigurationError):
        load_basic_provider(config(path))


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"user",
        b":",
        b"\xff:x",
        b"user:\xff",
        b"user\n:x",
        b"u" * 129 + b":x",
        b"u:" + b"x" * 1025,
    ],
)
def test_malformed_decoded_credentials_do_not_reach_verification(administrator, raw):
    record, _ = administrator

    def forbidden(value):
        pytest.fail("malformed credential reached Argon2")

    async def exercise():
        provider = BasicProvider(record, verify=forbidden)
        try:
            with pytest.raises(AuthenticationError):
                await provider.authenticate("Basic " + base64.b64encode(raw).decode())
            assert provider.stats.failures == 0
        finally:
            await provider.aclose()

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "header",
    [
        "",
        "Bearer opaque",
        "Basic",
        "Basic  !!!",
        "Basic !!!",
        "Basic \u00e9",
        "Basic " + "A" * 8192,
    ],
)
def test_malformed_or_oversized_header_is_refused(administrator, header):
    record, _ = administrator

    async def exercise():
        provider = BasicProvider(record, verify=lambda _: pytest.fail("bad header reached hash"))
        try:
            with pytest.raises(AuthenticationError):
                await provider.authenticate(header)
        finally:
            await provider.aclose()

    asyncio.run(exercise())


def test_noncanonical_basic_padding_and_padding_bits_are_refused(administrator):
    record, _ = administrator

    async def exercise():
        provider = BasicProvider(
            record, verify=lambda _: pytest.fail("noncanonical header reached hash")
        )
        try:
            for encoded in ("dTo===", "dTp=", "dTo", "dTo=\n"):
                with pytest.raises(AuthenticationError):
                    await provider.authenticate("Basic " + encoded)
        finally:
            await provider.aclose()

    asyncio.run(exercise())


def test_provisioning_fresh_salts_and_exact_unicode_and_empty_password_boundaries(administrator):
    record, password = administrator
    another = create_administrator_record(record.subject, record.username, password)
    assert record.password_hash != another.password_hash
    assert record.password_hash not in repr(record)
    assert set(record.model_dump()) == {"schema_version", "subject", "username", "password_hash"}

    async def exercise():
        for value in (
            b"",
            secrets.token_urlsafe(768).encode(),
            ("\u00e9" * 511).encode() + secrets.token_hex(1).encode(),
        ):
            current = create_administrator_record("a" * 128, "\u00e9" * 64, value)
            provider = BasicProvider(current)
            try:
                principal = await provider.authenticate(authorization(current.username, value))
                assert principal.subject == current.subject
            finally:
                await provider.aclose()

    asyncio.run(exercise())


def test_invalid_provisioning_inputs_fail_before_hash(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("invalid provisioning input reached Argon2")

    monkeypatch.setattr(basic, "Argon2id", forbidden)
    for subject, username, value in (
        ("", "operator", b""),
        ("subject", "", b""),
        ("subject", "operator", b"x" * 1025),
        ("subject", "operator", b"\xff"),
    ):
        with pytest.raises(ConfigurationError):
            create_administrator_record(subject, username, value)


def test_wrong_passwords_never_accumulate_in_global_redaction_registry(administrator):
    record, _ = administrator
    before = frozenset(redaction._registered)

    async def exercise():
        provider = BasicProvider(record, verify=lambda _: False)
        try:
            for _ in range(10):
                with pytest.raises(AuthenticationError):
                    await provider.authenticate(
                        authorization(record.username, secrets.token_urlsafe(32).encode())
                    )
        finally:
            await provider.aclose()

    asyncio.run(exercise())
    assert frozenset(redaction._registered) == before


def test_record_is_frozen_and_cannot_coerce_values(administrator):
    record, _ = administrator
    with pytest.raises(ValidationError):
        record.subject = "replacement"  # pyrefly: ignore[read-only]
    with pytest.raises(ValidationError):
        ProtectedAdministratorRecord.model_validate(record.model_dump() | {"schema_version": True})


def test_exact_record_byte_limit_and_named_source_has_no_ambient_fallback(tmp_path, administrator):
    record, _ = administrator
    path = write_record(tmp_path / "ui-admin", record)
    content = path.read_bytes()
    path.write_bytes(content + b" " * (8192 - len(content)))

    async def exercise():
        provider = load_basic_provider(config(path))
        assert provider is not None
        await provider.aclose()

    asyncio.run(exercise())
    named = BasicConfig.model_validate(
        {"origin": "https://archive.example", "administrator": {"systemd_name": "ui-admin"}}
    )
    for environ in ({}, {"CREDENTIALS_DIRECTORY": "relative"}):
        with pytest.raises(ConfigurationError):
            load_basic_provider(named, environ=environ)


def test_unsupported_backend_is_startup_refusal_without_verification(
    tmp_path, administrator, monkeypatch
):
    record, _ = administrator
    path = write_record(tmp_path / "ui-admin", record)

    def unsupported(*args, **kwargs):
        message = "fixture unsupported algorithm"
        raise basic.UnsupportedAlgorithm(message)

    monkeypatch.setattr(basic, "Argon2id", unsupported)
    with pytest.raises(ConfigurationError) as failure:
        load_basic_provider(config(path))
    assert failure.value.problems[0].code == "HFAPI003"
