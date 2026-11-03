"""Basic original keys are subject-scoped while old bearer bytes remain exact (146)."""

import json

import pytest

from hfcache.api import operations
from hfcache.api.auth import (
    AdminCapability,
    AuthenticationMethod,
    Capability,
    CredentialClass,
    Principal,
    require_admin_capability,
)
from hfcache.config import ApplicationConfig
from hfcache.errors import AuthorizationError, OperationError, RequestError
from hfcache.server_config import PolicySnapshot
from tests.fixtures import examples
from tests.intent_fixtures import OperationStore

KEY = "known-original-key"
LEGACY_DIGEST = "b5eb6d922ffe54c895f439b22b7b268cffc120dc816171d37b064fd307097ec3"
BASIC_DIGEST = "308abc26b0a93c5e95ab581c8b21cb9e0c050018cc5441cbf0a937a596cb225a"


def basic(subject="stable-admin-v1", *, grants=frozenset(AdminCapability)):
    return Principal(
        CredentialClass.REST_WRITER,
        authentication_method=AuthenticationMethod.BASIC,
        subject=subject,
        admin_capabilities=grants,
    )


@pytest.fixture
def snapshot(tmp_path):
    config = ApplicationConfig.model_validate(
        {
            "schema_version": 1,
            "storage": {
                "archive_root": str(tmp_path / "archive"),
                "archive_id": examples.ARCHIVE_ID,
            },
        }
    )
    return PolicySnapshot(config, config.fingerprint())


def admit(store, snapshot, principal, *, key=KEY):
    return store.admit(principal, key, "/api/v1/plans", {"selectors": []}, lambda: snapshot)


@pytest.mark.parametrize("credential_class", list(CredentialClass))
def test_legacy_principal_constructor_keeps_exact_legacy_capabilities(credential_class):
    principal = Principal(credential_class)
    assert principal.authentication_method is AuthenticationMethod.BEARER
    assert principal.subject == "credential-class:" + credential_class.value
    assert principal.admin_capabilities == frozenset()
    expected = {
        CredentialClass.REST_WRITER: {"read", "write"},
        CredentialClass.REST_READER: {"read"},
        CredentialClass.MCP_READER: {"mcp-read"},
    }
    assert {value.value for value in principal.capabilities} == expected[credential_class]
    for grant in AdminCapability:
        with pytest.raises(AuthorizationError):
            require_admin_capability(principal, grant)


def test_basic_admin_grants_are_separate_frozen_internal_permissions():
    principal = basic()
    assert principal.capabilities == frozenset({Capability.READ, Capability.WRITE})
    assert {value.value for value in principal.admin_capabilities} == {
        "config-read",
        "config-write",
        "host-read",
        "schedule-write",
        "observer-stop",
    }
    for grant in AdminCapability:
        assert require_admin_capability(principal, grant) is principal
    with pytest.raises(AuthorizationError):
        require_admin_capability(basic(grants=frozenset()), AdminCapability.HOST_READ)


@pytest.mark.parametrize("subject", [None, "", "wrong subject", "é", "x" * 129, "line\n"])
def test_basic_subject_is_explicit_bounded_ascii(subject):
    with pytest.raises(ValueError, match="Basic principals"):
        basic(subject)


def test_bearers_cannot_be_given_administrator_grants_or_person_identity():
    with pytest.raises(ValueError, match="bearer principals"):
        Principal(CredentialClass.REST_WRITER, admin_capabilities=frozenset(AdminCapability))
    with pytest.raises(ValueError, match="bearer principals"):
        Principal(CredentialClass.REST_WRITER, subject="stable-admin-v1")
    with pytest.raises(ValueError, match="Basic principals"):
        Principal(
            CredentialClass.MCP_READER,
            authentication_method=AuthenticationMethod.BASIC,
            subject="stable-admin-v1",
        )


def test_exact_versioned_basic_preimage_and_legacy_bearer_golden():
    assert operations._key_digest(KEY) == LEGACY_DIGEST
    assert operations._key_digest(KEY, Principal(CredentialClass.REST_WRITER)) == LEGACY_DIGEST
    assert operations._key_digest(KEY, Principal(CredentialClass.REST_READER)) == LEGACY_DIGEST
    assert operations._key_digest(KEY, basic()) == BASIC_DIGEST
    assert operations._key_digest(KEY, basic("stable-admin-v2")) != BASIC_DIGEST
    # A bearer cannot impersonate the private namespace by using a printable surrogate.
    assert (
        operations._key_digest(BASIC_DIGEST, Principal(CredentialClass.REST_WRITER)) != BASIC_DIGEST
    )


def test_same_original_key_is_independent_for_basic_subjects_and_legacy_classes(tmp_path, snapshot):
    subjects = [
        basic(),
        basic("stable-admin-v2"),
        Principal(CredentialClass.REST_WRITER),
        Principal(CredentialClass.REST_READER),
    ]
    root = tmp_path / "operations"
    with OperationStore(root) as store:
        receipts = [admit(store, snapshot, principal).receipt for principal in subjects]
        assert len({receipt.operation_id for receipt in receipts}) == 4
        for principal, receipt in zip(subjects, receipts, strict=True):
            assert store.lookup(principal, KEY).operation_id == receipt.operation_id
            assert not admit(store, snapshot, principal).created
    assert not snapshot.config.storage.archive_root.exists()
    for path in root.rglob("*"):
        if path.is_file():
            raw = path.read_bytes()
            assert KEY.encode() not in raw
            assert b"stable-admin-v1" not in raw
            assert b"stable-admin-v2" not in raw


def test_restart_rotation_with_the_same_subject_keeps_the_original_handle(tmp_path, snapshot):
    root = tmp_path / "operations"
    with OperationStore(root) as store:
        receipt = admit(store, snapshot, basic()).receipt
    # Username/hash/provider rotation has no input to this stable-subject binding.
    rotated = basic(grants=frozenset({AdminCapability.CONFIG_READ}))
    with OperationStore(root) as reopened:
        assert reopened.lookup(rotated, KEY).operation_id == receipt.operation_id
        retried = reopened.admit(
            rotated,
            KEY,
            "/api/v1/plans",
            {"selectors": []},
            lambda: pytest.fail("an exact old binding cannot consult new policy"),
        )
        assert not retried.created
        assert retried.receipt.operation_id == receipt.operation_id
        with pytest.raises(OperationError) as missing:
            reopened.lookup(Principal(CredentialClass.REST_WRITER), KEY)
        assert missing.value.problems[0].code == "HFAPI013"
    records = list(root.rglob(receipt.operation_id + ".json"))
    assert len(records) == 1
    payload = json.loads(records[0].read_bytes())
    assert payload["key_digest"] == BASIC_DIGEST
    assert "subject" not in payload
    assert "authentication_method" not in payload


@pytest.mark.parametrize("key", ["", "space key", "nul\0key", "é", "key\n", "x" * 129])
def test_malformed_keys_are_rejected_before_store_lock_or_policy(
    tmp_path, snapshot, monkeypatch, key
):
    with OperationStore(tmp_path / "operations") as store:
        monkeypatch.setattr(
            store, "_locked", lambda: pytest.fail("invalid key acquired the store lock")
        )
        with pytest.raises(RequestError):
            admit(store, snapshot, basic(), key=key)
        with pytest.raises(RequestError):
            store.lookup(basic(), key)
