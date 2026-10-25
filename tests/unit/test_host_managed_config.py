"""Decision153 closed bootstrap parity, exact reconstruction and real Unix preparation."""

import ast
import asyncio
import copy
import hashlib
import json
import threading
import tomllib
from pathlib import Path

import pytest

from hfcache import host_policy as policy
from hfcache import host_protocol as protocol
from hfcache.config import RepositoryConfig, validate_config_mapping
from hfcache.config_models import EDITABLE_FIELDS, PROTECTED_FIELDS, ConfigPrepared, ConfigRead
from hfcache.errors import HfcacheError
from hfcache.host_helper_client import HostHelperClient
from tests.unit.test_host_daemon import inspector as inspector  # noqa: PLC0414 - shared fixture
from tests.unit.test_host_daemon import run_exchange
from tests.unit.test_host_helper_client import DEPLOYMENT, UnixTestBinding, unix_service
from tests.unit.test_host_policy import ARCHIVE_ID
from tests.unit.test_host_policy import native as native  # noqa: PLC0414 - shared fixture


def config_bytes(repositories=""):
    return (
        'schema_version=1\n[storage]\narchive_root="/srv/hfcache"\n'
        f'archive_id="{ARCHIVE_ID}"\n' + repositories
    ).encode()


def managed(snapshot, edits):
    return {"base_revision": snapshot.base_revision, "edits": edits}


def upsert(identifier="org/new", **fields):
    return {
        "kind": "repository-upsert",
        "repository": {"type": "model", "id": identifier, **fields},
    }


def test_closed_renderer_defaults_metadata_and_independent_application_roundtrip():
    document = policy.parse_configuration(config_bytes())
    rendered = policy.render_configuration(document)
    actual = validate_config_mapping(tomllib.loads(rendered.decode()))
    original = validate_config_mapping(tomllib.loads(config_bytes().decode()))
    assert actual == original
    assert document == actual.model_dump(mode="json")
    assert policy.EDITABLE_FIELDS == EDITABLE_FIELDS
    assert policy.PROTECTED_FIELDS == PROTECTED_FIELDS
    assert rendered.endswith(b"\n")
    assert policy.render_configuration(policy.parse_configuration(rendered)) == rendered


@pytest.mark.parametrize(
    ("table", "field", "literal"),
    [
        ("hub", "endpoint", '"https://example.invalid"'),
        ("hub", "endpoint", '"http://example.invalid"'),
        ("hub", "endpoint", '"https://example.invalid/path"'),
        ("hub", "expected_account", '"valid-account"'),
        ("hub", "expected_account", '"wrong account"'),
        ("hub", "token_mode", '"required"'),
        ("hub", "token_mode", '"wrong"'),
        ("hub", "credential_name", '"other-source"'),
        ("hub", "credential_name", '".."'),
        ("storage", "publication_mode", '"copy"'),
        ("storage", "publication_mode", '"wrong"'),
        ("storage", "minimum_free_space_gib", "0"),
        ("storage", "minimum_free_space_gib", "1048576"),
        ("storage", "minimum_free_space_gib", "1048577"),
        ("storage", "minimum_free_space_gib", "true"),
        ("storage", "minimum_free_space_percent", "100"),
        ("storage", "minimum_free_space_percent", "101"),
        ("storage", "maximum_revisions", "5"),
        ("storage", "maximum_revisions", "4"),
        ("storage", "maximum_revisions", '"3"'),
        ("sync", "max_workers", "32"),
        ("sync", "max_workers", "33"),
        ("sync", "lock_wait_seconds", "86400"),
        ("sync", "lock_wait_seconds", "-1"),
        ("sync", "continue_on_repository_error", "false"),
        ("sync", "continue_on_repository_error", "0"),
        ("sync", "dependency_policy", '"warn"'),
        ("sync", "dependency_policy", '"error"'),
        ("sync", "stale_staging_age_hours", "8760"),
        ("sync", "stale_staging_age_hours", "0"),
        ("verification", "algorithm", '"sha256"'),
        ("verification", "algorithm", '"md5"'),
        ("verification", "hash_new_content", "true"),
        ("verification", "hash_new_content", "false"),
        ("verification", "lock_wait_seconds", "604800"),
        ("verification", "lock_wait_seconds", "604801"),
        ("repair", "retired_instance_grace_hours", "168"),
        ("repair", "retired_instance_grace_hours", "167"),
        ("repair", "retired_instance_grace_hours", "8760"),
        ("repair", "retired_instance_grace_hours", "8761"),
        ("sync", "unknown_field", "1"),
        ("hub", "token", '"never-export-this"'),
    ],
)
def test_full_table_grammar_matches_application_constraints(table, field, literal):
    suffix = ("" if table == "storage" else f"\n[{table}]\n") + field + "=" + literal + "\n"
    body = config_bytes() + suffix.encode()
    mapping = tomllib.loads(body.decode())
    try:
        expected = validate_config_mapping(mapping).model_dump(mode="json")
    except ValueError, HfcacheError:
        with pytest.raises(policy.InspectionError):
            policy.parse_configuration(body)
    else:
        assert policy.parse_configuration(body) == expected


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "a/b"),
        ("id", "a" * 96 + "/" + "b" * 96),
        ("id", "a" * 97 + "/b"),
        ("id", "../b"),
        ("id", "a/b\n"),
        ("id", "a//b"),
        ("id", 1),
        ("type", "dataset"),
        ("type", True),
        ("enabled", 1),
        ("revision", "main"),
        ("revision", "v1.0"),
        ("revision", "a" * 40),
        ("revision", "A" * 40),
        ("revision", "deadbeef"),
        ("revision", "a..b"),
        ("revision", "a.lock"),
        ("revision", "a/"),
        ("revision", "a\n"),
        ("tags", [" Fine/Tag ", "fine/tag"]),
        ("tags", ["İ"]),
        ("tags", [" tag\t"]),
        ("tags", ["a"] * 65),
        ("tags", [" " * 129]),
        ("tags", [1]),
        ("declared_dependencies", ["a/b", "c/d"]),
        ("declared_dependencies", ["a/b", "a/b"]),
        ("declared_dependencies", ["invalid"]),
    ],
)
def test_repository_grammar_matches_existing_application_model(field, value):
    repository = {"type": "model", "id": "org/repo", field: value}
    try:
        expected = RepositoryConfig.model_validate(repository).model_dump(mode="json")
    except ValueError, HfcacheError:
        with pytest.raises(policy.InspectionError):
            policy._configuration_repository(repository)
    else:
        assert policy._configuration_repository(repository) == expected


def test_hidden_fields_and_unicode_control_quoting_roundtrip_without_placeholders():
    document = policy.parse_configuration(config_bytes())
    hidden = 'https://hidden-"\\\t\r\n\x00\x7f-😀'
    document["hub"]["endpoint"] = hidden
    document["hub"]["credential_name"] = "private-source"
    rendered = policy.render_configuration(document)
    mapping = tomllib.loads(rendered.decode())
    assert validate_config_mapping(mapping).hub.endpoint == hidden
    assert mapping["hub"]["credential_name"] == "private-source"
    assert b"\x00" not in rendered
    assert b"\x7f" not in rendered
    assert b"\\u0000" in rendered
    assert b"\\u007f" in rendered
    projection = policy.editable_configuration(document)
    assert "hidden" not in json.dumps(projection)
    assert "private-source" not in json.dumps(projection)


def test_prepare_preserves_hidden_fields_exact_base_and_creates_no_files(native):
    before = {str(path): policy._identity(path.lstat()) for path in native.config.parent.rglob("*")}
    snapshot = policy.inspect_authority()
    read = ConfigRead.model_validate(policy.read_config_base(snapshot))
    body = managed(snapshot, [upsert(tags=[" GPU ", "gpu"], declared_dependencies=["org/base"])])
    result = policy.prepare_configuration(snapshot, body)
    assert policy.prepare_configuration(snapshot, body) == result
    prepared = ConfigPrepared.model_validate(result)
    actual = validate_config_mapping(tomllib.loads(prepared.candidate))
    assert actual.hub.credential_name == "unit-hidden-source"
    assert actual.storage.archive_id == read.archive_id
    assert actual.repositories[0].tags == ("gpu",)
    assert prepared.required_selectors == ("model:org/new",)
    assert prepared.base_revision == read.base_revision
    assert prepared.candidate_revision not in {
        read.base_revision,
        hashlib.sha256(prepared.candidate.encode()).hexdigest(),
    }
    assert {
        str(path): policy._identity(path.lstat()) for path in native.config.parent.rglob("*")
    } == before
    assert not (native.config.parent / ".configuration.lock").exists()
    assert not (native.config.parent / ".candidate.toml").exists()


def test_comments_and_tags_invalidate_base_without_changing_operational_fingerprint(native):
    original = policy.inspect_authority()
    before = native.config.read_bytes()
    original_config = validate_config_mapping(tomllib.loads(before.decode()))
    native.config.write_bytes(before + b"\n# private changed comment\n")
    commented = policy.inspect_authority()
    assert commented.base_revision != original.base_revision
    assert (
        validate_config_mapping(tomllib.loads(native.config.read_text())).fingerprint()
        == original_config.fingerprint()
    )
    with pytest.raises(policy.InspectionError) as caught:
        policy.prepare_configuration(commented, managed(original, []))
    assert caught.value.reason == "config-conflict"
    native.config.write_bytes(
        before + b'\n[[repositories]]\nid="org/repo"\ntype="model"\ntags=["one"]\n'
    )
    tagged = policy.inspect_authority()
    prior = validate_config_mapping(tomllib.loads(native.config.read_text())).fingerprint()
    native.config.write_bytes(native.config.read_bytes().replace(b'["one"]', b'["two"]'))
    current = policy.inspect_authority()
    assert current.base_revision != tagged.base_revision
    assert validate_config_mapping(tomllib.loads(native.config.read_text())).fingerprint() == prior
    with pytest.raises(policy.InspectionError) as caught:
        policy.prepare_configuration(current, managed(tagged, []))
    assert caught.value.reason == "config-conflict"


def test_scope_is_added_enabled_or_retargeted_only_and_repository_order_is_preserved():
    base = policy.parse_configuration(
        config_bytes("""
[[repositories]]
id="org/unchanged"
type="model"
[[repositories]]
id="org/disabled"
type="model"
enabled=false
[[repositories]]
id="org/retarget"
type="dataset"
[[repositories]]
id="org/removed"
type="model"
""")
    )
    request = {
        "base_revision": "a" * 64,
        "edits": [
            upsert("org/unchanged", tags=["one"]),
            upsert("org/disabled"),
            {
                "kind": "repository-upsert",
                "repository": {"type": "dataset", "id": "org/retarget", "revision": "v1"},
            },
            {
                "kind": "repository-remove",
                "repository_type": "model",
                "repository_id": "org/removed",
            },
            upsert("org/new-disabled", enabled=False),
            upsert("org/new"),
            {"kind": "settings-replace", "settings": {"storage": {"maximum_revisions": 5}}},
        ],
    }
    candidate, scope = policy._managed_edits(base, request)
    assert scope == ["dataset:org/retarget", "model:org/disabled", "model:org/new"]
    assert [row["id"] for row in candidate["repositories"]] == [
        "org/unchanged",
        "org/disabled",
        "org/retarget",
        "org/new-disabled",
        "org/new",
    ]
    assert candidate["storage"]["maximum_revisions"] == 5


@pytest.mark.parametrize(
    "edits",
    [
        [upsert(), upsert()],
        [{"kind": "repository-remove", "repository_type": "model", "repository_id": "org/absent"}],
        [{"kind": "settings-replace", "settings": {}}],
        [{"kind": "settings-replace", "settings": {"sync": {}}}],
        [{"kind": "settings-replace", "settings": {"hub": {"endpoint": "https://other"}}}],
        [{"kind": "settings-replace", "settings": {"storage": {"archive_root": "/elsewhere"}}}],
        [{"kind": "settings-replace", "settings": {"verification": {"algorithm": "sha256"}}}],
        [{"kind": "settings-replace", "settings": {"sync": {"max_workers": True}}}],
        [{"kind": "settings-replace", "settings": {"sync": {"max_workers": None}}}],
        [{"kind": "settings-replace", "settings": {"sync": {"max_workers": 1}}}] * 2,
        [
            {
                "kind": "settings-replace",
                "settings": {"repair": {"retired_instance_grace_hours": 167}},
            }
        ],
        [
            {
                "kind": "repository-upsert",
                "repository": {"type": "model", "id": "org/repo", "token": "secret"},
            }
        ],
        [upsert("org/repo", path="/etc/passwd")],
        [upsert()] * 257,
    ],
)
def test_closed_edits_reject_unknown_coercive_protected_and_duplicate_inputs(edits):
    document = policy.parse_configuration(config_bytes())
    with pytest.raises(policy.InspectionError):
        policy._managed_edits(document, {"base_revision": "a" * 64, "edits": edits})


def test_renderer_checks_utf8_and_escape_expansion_before_joining():
    document = policy.parse_configuration(config_bytes())
    document["hub"]["endpoint"] = "https://" + "\t" * (policy.MAX_CONFIGURATION_BYTES // 5)
    with pytest.raises(policy.InspectionError):
        policy.render_configuration(document)
    document["hub"]["endpoint"] = "https://" + "😀" * (policy.MAX_CONFIGURATION_BYTES // 3)
    with pytest.raises(policy.InspectionError):
        policy.render_configuration(document)
    with pytest.raises(policy.InspectionError):
        policy._configuration_reply_limit(
            {"candidate": "x" * (protocol.MAX_FRAME_BYTES - 1)}, "config-prepare"
        )


def test_real_unix_prepare_dispatch_and_stale_conflict_are_typed(native, inspector):
    instance, _calls, _authority = inspector
    snapshot = policy.inspect_authority()
    instance.policy.prepare_configuration = lambda _value, body: policy.prepare_configuration(
        snapshot, body
    )
    request = protocol.HostRequest("a" * 32, "config-prepare", managed(snapshot, [upsert()]))
    raw = run_exchange(instance, request.wire())
    reply = protocol.reply_body(protocol.decode_object(raw[4:]), request)
    assert ConfigPrepared.model_validate(reply).required_selectors == ("model:org/new",)
    stale = protocol.HostRequest(
        "b" * 32, "config-prepare", {"base_revision": "0" * 64, "edits": []}
    )
    raw = run_exchange(instance, stale.wire())
    value = protocol.decode_object(raw[4:])
    assert value["outcome"] == "denied"
    assert value["reason"] == "config-conflict"
    assert value["body"] == {}
    with pytest.raises(protocol.HostProtocolError, match="config-conflict"):
        protocol.reply_body(value, stale)


def test_sync_async_client_prepare_and_request_copy_use_real_unix(tmp_path):
    repository = {"type": "model", "id": "org/new"}
    body: dict[str, object] = {
        "base_revision": "a" * 64,
        "edits": [{"kind": "repository-upsert", "repository": repository}],
    }
    received = []
    with unix_service(tmp_path, reply={"prepared": True}, received=received) as (
        path,
        accepted,
        _errors,
    ):
        binding = UnixTestBinding(path)
        client = HostHelperClient(binding, deployment_sha256=DEPLOYMENT)
        assert client.config_prepare(body) == {"prepared": True}
        assert asyncio.run(client.async_config_prepare(body)) == {"prepared": True}
        expected = copy.deepcopy(body)
        binding.entered.clear()
        release = threading.Event()
        binding.stall = release

        async def mutate_after_queueing():
            task = asyncio.create_task(client.async_config_prepare(body))
            while not binding.entered.is_set():
                await asyncio.sleep(0.001)
            repository["id"] = "changed/after-freeze"
            release.set()
            assert await task == {"prepared": True}

        asyncio.run(mutate_after_queueing())
        assert len(accepted) == 3
        assert all(
            request.operation == "config-prepare" and request.body == expected
            for request in received
        )
        assert client.close(timeout=2)


def test_bootstrap_remains_standard_library_python312():
    root = Path(__file__).parents[2]
    for filename in (
        "src/hfcache/host_policy.py",
        "src/hfcache/host_protocol.py",
        "src/hfcache/host_helper_client.py",
        "scripts/host-helper.py",
    ):
        ast.parse((root / filename).read_text(), feature_version=(3, 12))
