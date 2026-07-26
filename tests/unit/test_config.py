"""Strict configuration validation (`docs/configuration.md`).

Every `HFCFG###` code in the contract has a test that provokes it, so the
taxonomy cannot drift away from the implementation.
"""

import copy
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from hfcache.config import (
    MAXIMUM_REVISIONS,
    REPAIR_GRACE_FLOOR_HOURS,
    SCHEMA_VERSION,
    load_config,
    parse_repository_id,
    parse_revision,
    validate_config_mapping,
)
from hfcache.errors import ConfigurationError, ExitCode

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
FULL_SHA = "0123456789abcdef0123456789abcdef01234567"


def base_mapping() -> dict[str, Any]:
    """A minimal valid configuration."""
    return {
        "schema_version": SCHEMA_VERSION,
        "storage": {"archive_root": "/srv/hfcache", "archive_id": ARCHIVE_ID},
        "repositories": [{"id": "organization/model-name", "type": "model"}],
    }


def mutate(**changes: Any) -> dict[str, Any]:
    mapping = base_mapping()
    for key, value in changes.items():
        mapping[key] = value
    return mapping


def codes_for(mapping: dict[str, Any]) -> list[str]:
    with pytest.raises(ConfigurationError) as raised:
        validate_config_mapping(mapping)
    return [problem.code for problem in raised.value.problems]


# --------------------------------------------------------------------------- #
# Accepting a valid configuration
# --------------------------------------------------------------------------- #


def test_minimal_configuration_loads_with_documented_defaults():
    config = validate_config_mapping(base_mapping())

    assert config.hub.endpoint == "https://huggingface.co"
    assert config.hub.expected_account == ""
    assert config.hub.token_mode == "optional"
    assert config.storage.archive_root == Path("/srv/hfcache")
    assert config.storage.publication_mode == "hardlink"
    assert config.storage.maximum_revisions == MAXIMUM_REVISIONS
    assert config.storage.minimum_free_space_gib == 100
    assert config.storage.minimum_free_space_percent == 10
    assert config.sync.max_workers == 4
    assert config.sync.lock_wait_seconds == 3600
    assert config.sync.continue_on_repository_error is True
    assert config.sync.stale_staging_age_hours == 24
    assert config.verification.algorithm == "sha256"
    assert config.verification.lock_wait_seconds == 86_400
    assert config.repair.retired_instance_grace_hours == REPAIR_GRACE_FLOOR_HOURS


def test_empty_repository_list_is_valid():
    # How an operator disables all synchronization without discarding the file.
    config = validate_config_mapping(mutate(repositories=[]))
    assert config.repositories == ()
    assert config.enabled_repositories == ()


def test_disabled_repositories_are_excluded_from_runs_but_retained():
    config = validate_config_mapping(
        mutate(
            repositories=[
                {"id": "org/a", "type": "model"},
                {"id": "org/b", "type": "dataset", "enabled": False},
            ]
        )
    )
    assert len(config.repositories) == 2
    assert [r.selector for r in config.enabled_repositories] == ["model:org/a"]


def test_a_full_commit_sha_is_an_acceptable_revision():
    config = validate_config_mapping(
        mutate(repositories=[{"id": "org/a", "type": "model", "revision": FULL_SHA}])
    )
    assert config.repositories[0].revision == FULL_SHA


def test_configuration_is_frozen_after_loading():
    config = validate_config_mapping(base_mapping())
    with pytest.raises(ValidationError):
        # pyrefly: ignore[read-only]
        # Assigning to a frozen field is the behaviour under test; the type
        # checker correctly rejects it, which is itself part of the guarantee.
        config.storage.maximum_revisions = 6


def test_collections_are_immutable():
    config = validate_config_mapping(base_mapping())
    assert isinstance(config.repositories, tuple)
    assert isinstance(config.repositories[0].declared_dependencies, tuple)


# --------------------------------------------------------------------------- #
# Rejecting an invalid configuration: one test per contract code
# --------------------------------------------------------------------------- #


def test_hfcfg001_missing_file(tmp_path: Path):
    with pytest.raises(ConfigurationError) as raised:
        load_config(tmp_path / "absent.toml")
    assert [p.code for p in raised.value.problems] == ["HFCFG001"]


def test_hfcfg001_directory_instead_of_file(tmp_path: Path):
    with pytest.raises(ConfigurationError) as raised:
        load_config(tmp_path)
    assert [p.code for p in raised.value.problems] == ["HFCFG001"]


def test_hfcfg001_unreadable_file(tmp_path: Path):
    """The deployed case, and the reason `--config` disables typer's own access
    check (decision 57): `/etc/hfcache/config.toml` is `0640` root:hfcache, so
    every identity but root and the service account gets exactly this — a
    configuration problem at exit `10`, not a usage error at exit `2`."""
    path = tmp_path / "config.toml"
    path.write_text("schema_version = 1\n", encoding="utf-8")
    path.chmod(0o000)

    with pytest.raises(ConfigurationError) as raised:
        load_config(path)

    assert [p.code for p in raised.value.problems] == ["HFCFG001"]
    assert "unreadable" in raised.value.problems[0].message


def test_hfcfg002_malformed_toml(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text("schema_version = = 1\n", encoding="utf-8")
    with pytest.raises(ConfigurationError) as raised:
        load_config(path)
    assert [p.code for p in raised.value.problems] == ["HFCFG002"]


def test_hfcfg002_non_utf8(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_bytes(b"schema_version = 1\n# \xff\xfe invalid\n")
    with pytest.raises(ConfigurationError) as raised:
        load_config(path)
    assert [p.code for p in raised.value.problems] == ["HFCFG002"]


def test_hfcfg003_unknown_top_level_key():
    assert "HFCFG003" in codes_for(mutate(unexpected="value"))


def test_hfcfg003_unknown_nested_key():
    assert "HFCFG003" in codes_for(mutate(sync={"maxworkers": 4}))


def test_hfcfg004_missing_schema_version():
    mapping = base_mapping()
    del mapping["schema_version"]
    assert "HFCFG004" in codes_for(mapping)


def test_hfcfg004_unsupported_schema_version():
    assert "HFCFG004" in codes_for(mutate(schema_version=2))


@pytest.mark.parametrize(
    ("table", "key", "value"),
    [
        ("sync", "max_workers", "4"),
        ("sync", "continue_on_repository_error", 1),
        ("storage", "minimum_free_space_gib", 100.0),
        ("verification", "hash_new_content", "true"),
    ],
)
def test_hfcfg005_strict_types_reject_coercible_values(table: str, key: str, value: Any):
    mapping = base_mapping()
    mapping.setdefault(table, {})[key] = value
    assert "HFCFG005" in codes_for(mapping)


@pytest.mark.parametrize("archive_root", ["srv/hfcache", "/srv/hfcache/", "/srv/../srv/hfcache"])
def test_hfcfg006_paths_must_be_absolute_and_normalized(archive_root: str):
    mapping = base_mapping()
    mapping["storage"]["archive_root"] = archive_root
    assert "HFCFG006" in codes_for(mapping)


def test_hfcfg007_duplicate_repository_entry():
    mapping = base_mapping()
    mapping["repositories"].append({"id": "organization/model-name", "type": "model"})
    assert "HFCFG007" in codes_for(mapping)


def test_same_id_with_different_types_is_not_a_duplicate():
    config = validate_config_mapping(
        mutate(
            repositories=[
                {"id": "org/same", "type": "model"},
                {"id": "org/same", "type": "dataset"},
            ]
        )
    )
    assert len(config.repositories) == 2


@pytest.mark.parametrize(
    "repository_id",
    ["gpt2", "org/repo/extra", "/org/repo", "org/", "/repo", ".././etc", "org/..", "-bad/repo"],
)
def test_hfcfg008_invalid_repository_identifiers(repository_id: str):
    mapping = base_mapping()
    mapping["repositories"][0]["id"] = repository_id
    assert "HFCFG008" in codes_for(mapping)


@pytest.mark.parametrize(
    "revision",
    [
        "0123abc",
        "0123456789ABCDEF0123456789abcdef01234567",
        "-dash",
        "a//b",
        "a..b",
        "ref.lock",
        "",
    ],
)
def test_hfcfg009_invalid_revisions(revision: str):
    mapping = base_mapping()
    mapping["repositories"][0]["revision"] = revision
    assert "HFCFG009" in codes_for(mapping)


@pytest.mark.parametrize("key", ["token", "hf_token", "api_token", "secret", "password"])
def test_hfcfg010_literal_secrets_are_refused(key: str):
    mapping = base_mapping()
    mapping["hub"] = {key: "hf_averysecretvalue"}
    with pytest.raises(ConfigurationError) as raised:
        validate_config_mapping(mapping)
    problems = raised.value.problems
    assert [p.code for p in problems] == ["HFCFG010"]
    # The value is never echoed back (docs/cli.md §6).
    assert "hf_averysecretvalue" not in problems[0].message
    assert "hf_averysecretvalue" not in str(raised.value)


def test_hfcfg011_maximum_revisions_is_fixed_at_five():
    mapping = base_mapping()
    mapping["storage"]["maximum_revisions"] = 3
    assert "HFCFG011" in codes_for(mapping)


@pytest.mark.parametrize("archive_id", ["not-a-uuid", "3F2A1C88-7B40-4A2E-9C1D-0E5B6A7F8D90", ""])
def test_hfcfg012_archive_id_must_be_a_canonical_uuid(archive_id: str):
    mapping = base_mapping()
    mapping["storage"]["archive_id"] = archive_id
    assert "HFCFG012" in codes_for(mapping)


def test_hfcfg013_invalid_credential_name():
    assert "HFCFG013" in codes_for(mutate(hub={"credential_name": "bad name!"}))


@pytest.mark.parametrize(
    "endpoint",
    ["http://huggingface.co", "https://huggingface.co/", "https://huggingface.co/api", "ftp://x"],
)
def test_hfcfg014_endpoint_must_be_https_host_only(endpoint: str):
    assert "HFCFG014" in codes_for(mutate(hub={"endpoint": endpoint}))


def test_hfcfg015_required_token_mode_is_reserved():
    assert "HFCFG015" in codes_for(mutate(hub={"token_mode": "required"}))


def test_hfcfg016_repair_grace_has_a_seven_day_floor():
    assert "HFCFG016" in codes_for(mutate(repair={"retired_instance_grace_hours": 167}))


def test_repair_grace_at_the_floor_is_accepted():
    config = validate_config_mapping(
        mutate(repair={"retired_instance_grace_hours": REPAIR_GRACE_FLOOR_HOURS})
    )
    assert config.repair.retired_instance_grace_hours == REPAIR_GRACE_FLOOR_HOURS


def test_all_problems_are_reported_at_once():
    # An operator should fix one file once, not one key per run.
    mapping = mutate(unexpected=1, hub={"endpoint": "http://x"})
    mapping["storage"]["maximum_revisions"] = 2
    codes = set(codes_for(mapping))
    assert {"HFCFG003", "HFCFG011", "HFCFG014"} <= codes


def test_configuration_errors_exit_ten():
    assert ConfigurationError.exit_code == ExitCode.CONFIGURATION


def test_problem_location_names_the_key_path():
    with pytest.raises(ConfigurationError) as raised:
        validate_config_mapping(mutate(sync={"max_workers": 999}))
    assert raised.value.problems[0].location == "sync.max_workers"


# --------------------------------------------------------------------------- #
# Fingerprint
# --------------------------------------------------------------------------- #


def test_fingerprint_is_stable_for_identical_intent():
    first = validate_config_mapping(base_mapping())
    second = validate_config_mapping(base_mapping())
    assert first.fingerprint() == second.fingerprint()
    assert len(first.fingerprint()) == 64


def test_fingerprint_changes_when_archived_content_changes():
    baseline = validate_config_mapping(base_mapping()).fingerprint()
    changed = validate_config_mapping(
        mutate(repositories=[{"id": "organization/other", "type": "model"}])
    ).fingerprint()
    assert baseline != changed


def test_fingerprint_changes_when_a_repository_is_disabled():
    baseline = validate_config_mapping(base_mapping()).fingerprint()
    mapping = base_mapping()
    mapping["repositories"][0]["enabled"] = False
    assert validate_config_mapping(mapping).fingerprint() != baseline


def test_fingerprint_excludes_the_credential_name():
    baseline = validate_config_mapping(base_mapping()).fingerprint()
    changed = validate_config_mapping(mutate(hub={"credential_name": "other-name"}))
    assert changed.fingerprint() == baseline


# --------------------------------------------------------------------------- #
# Round trip through a real file
# --------------------------------------------------------------------------- #


def test_load_config_reads_a_real_file(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text(
        f"""
schema_version = 1

[storage]
archive_root = "/srv/hfcache"
archive_id = "{ARCHIVE_ID}"

[[repositories]]
id = "organization/model-name"
type = "model"
revision = "main"
""",
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.repositories[0].selector == "model:organization/model-name"


# --------------------------------------------------------------------------- #
# Property-based grammar checks
# --------------------------------------------------------------------------- #

_SEGMENT_CHARS = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"),
    min_size=0,
    max_size=8,
)
_VALID_SEGMENT = st.builds(
    lambda head, tail: head + tail,
    st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
    _SEGMENT_CHARS,
)


@given(namespace=_VALID_SEGMENT, name=_VALID_SEGMENT)
def test_valid_two_segment_identifiers_round_trip(namespace: str, name: str):
    identifier = f"{namespace}/{name}"
    assert parse_repository_id(identifier) == identifier


@given(value=st.text(min_size=0, max_size=40))
def test_repository_id_never_admits_a_path_escape(value: str):
    try:
        accepted = parse_repository_id(value)
    except ValueError:
        return
    # Anything accepted must be exactly two safe segments, so joining it onto an
    # archive root can never escape (docs/architecture.md FS-09).
    namespace, _, name = accepted.partition("/")
    for segment in (namespace, name):
        assert segment not in {"", ".", ".."}
        assert "/" not in segment
        assert not segment.startswith((".", "-")) or segment[0].isalnum()


@given(value=st.text(min_size=0, max_size=50))
def test_revision_never_admits_a_traversal_or_abbreviated_sha(value: str):
    try:
        accepted = parse_revision(value)
    except ValueError:
        return
    assert ".." not in accepted
    assert "//" not in accepted
    assert not accepted.startswith(("-", "/"))
    assert not accepted.endswith(("/", ".lock"))


def test_deep_copy_of_base_mapping_is_independent():
    # Guards the test helpers themselves: a shared nested dict would make the
    # parametrized cases above contaminate one another.
    first = base_mapping()
    second = copy.deepcopy(first)
    first["storage"]["archive_root"] = "/elsewhere"
    assert second["storage"]["archive_root"] == "/srv/hfcache"
