"""Decision154 actual local filesystem transitions; SID adapter makes no MAC claim."""

import ast
import hashlib
import json
import os
import stat
import tempfile
import tomllib
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from hfcache import host_configuration as configuration
from hfcache import host_policy
from hfcache.config import validate_config_mapping

ARCHIVE_ID = "6ce912b6-141f-4bd2-a871-c19625c86aa9"


def _file_writer(tmp_path, monkeypatch):  # noqa: PLR0915 - shared actual-filesystem fixture
    """Reusable real-file writer with only protected capture and kernel SID adapted.

    API/Unix integration can use policy, snapshot(), and request(); no writer
    operation or filesystem syscall is replaced. root0700 becomes the test UID.
    """
    directory = tmp_path / "etc"
    directory.mkdir(mode=0o750)
    monkeypatch.setattr(configuration, "OWNER", os.getuid())
    monkeypatch.setattr(configuration, "OWNER_GID", os.getgid())
    for name, basename in {
        "CONFIGURATION": "config.toml",
        "CANDIDATE": ".candidate.toml",
        "BACKUP": "config.toml.bak",
        "LOCK": ".configuration.lock",
        "PENDING": ".configuration.pending",
        "APPLICATIONS": ".configuration-applications",
    }.items():
        monkeypatch.setattr(configuration, name, directory / basename)
    original = (
        'schema_version=1\n[storage]\narchive_root="/srv/hfcache"\n'
        f'archive_id="{ARCHIVE_ID}"\n'
        '[hub]\ncredential_name="private-credential-name"\n'
        '[[repositories]]\ntype="model"\nid="owned/base"\nenabled=false\ntags=[]\n'
    ).encode()
    configuration.CONFIGURATION.write_bytes(original)
    configuration.CONFIGURATION.chmod(0o640)
    configuration.LOCK.touch(mode=0o600)
    contexts = {}

    def context(path):
        if type(path) is int:
            info = os.fstat(path)
            name = Path(f"/proc/self/fd/{path}").readlink()
        else:
            info = path.lstat()
            name = path
        identity = info.st_dev, info.st_ino
        if name in {configuration.LOCK, configuration.PENDING}:
            kind = configuration.GUARD_TYPE
        elif name.name in {"predecessor.toml", "previous-backup.toml"}:
            kind = configuration.APPLICATION_TYPE
        elif name.is_relative_to(configuration.APPLICATIONS):
            kind = configuration.STATE_TYPE
        elif stat.S_ISDIR(info.st_mode):
            kind = configuration.DIRECTORY_TYPE
        else:
            kind = configuration.APPLICATION_TYPE
        contexts[identity] = f"system_u:object_r:{kind}:s0"
        return contexts[identity]

    # Preserve the original label as its actual inode moves between names.
    context(configuration.CONFIGURATION)
    context(configuration.LOCK)
    monkeypatch.setattr(configuration, "_context", context)
    state = SimpleNamespace(
        key=b"k" * 32,
        permissions={"configuration": True, "hub": True},
        deployment=b"deployment-one",
        policy=b"policy-one",
    )

    def snapshot(*, budget=None):
        body = configuration.CONFIGURATION.read_bytes()
        inspection = SimpleNamespace(
            key=state.key,
            config_body=body,
            deployment_body=state.deployment,
            policy_body=state.policy,
            capture=SimpleNamespace(local=lambda path: path.is_relative_to(directory)),
        )
        inspection.revision = lambda domain, *parts: host_policy._Inspection.revision(
            cast("host_policy._Inspection", inspection), domain, *parts
        )
        return SimpleNamespace(
            _inspection=inspection,
            archive_id=ARCHIVE_ID,
            base_revision=inspection.revision(b"host-config-base-v1", body),
            deployment_sha256=hashlib.sha256(state.deployment).hexdigest(),
            policy_sha256=hashlib.sha256(state.policy).hexdigest(),
            api_principal=(os.getuid(), os.getgid()),
            budget=budget or host_policy.InspectionBudget(),
            status=lambda: {"permissions": dict(state.permissions)},
        )

    def revalidate(captured):
        if (
            captured._inspection.config_body != configuration.CONFIGURATION.read_bytes()
            or captured._inspection.deployment_body != state.deployment
            or captured._inspection.policy_body != state.policy
        ):
            reason = "config-conflict"
            raise host_policy.InspectionError(reason)

    def confirm_configuration(captured, candidate, identity, context_value):
        assert tuple(configuration._identity(configuration.CONFIGURATION.lstat())) == identity
        assert context(configuration.CONFIGURATION) == context_value
        assert configuration.CONFIGURATION.read_bytes() == candidate
        assert captured._inspection.key == state.key
        # This fixture models the protected capture; test_host_policy exercises
        # the actual _Capture transition and its unchanged nonconfig bindings.
        inspection = SimpleNamespace(**vars(captured._inspection))
        inspection.config_body = candidate
        transitioned = SimpleNamespace(**vars(captured))
        transitioned._inspection = inspection
        revalidate(transitioned)

    monkeypatch.setattr(host_policy, "revalidate", revalidate)
    policy = SimpleNamespace(
        InspectionError=host_policy.InspectionError,
        _json=host_policy._json,
        prepare_configuration=host_policy.prepare_configuration,
        _prepare_configuration=host_policy._prepare_configuration,
        parse_configuration=host_policy.parse_configuration,
        revalidate=revalidate,
        confirm_configuration=confirm_configuration,
    )

    def request(edits=None, *, operation_id="a" * 32):
        captured = snapshot()
        managed = {"base_revision": captured.base_revision, "edits": edits or []}
        result = host_policy.prepare_configuration(
            cast("host_policy.AuthoritySnapshot", captured), managed
        )
        return {
            "operation_id": operation_id,
            "request_digest": operation_id * 2,
            "managed": managed,
            "candidate_revision": result["candidate_revision"],
            "config_fingerprint": configuration.configuration_fingerprint(
                host_policy.parse_configuration(result["candidate"].encode())
            ),
            "preview_operation_id": "f" * 32,
            "required_selectors": result["required_selectors"],
        }

    return SimpleNamespace(
        root=directory,
        policy=policy,
        snapshot=snapshot,
        request=request,
        state=state,
        original=original,
        contexts=contexts,
        context=context,
        apply=lambda body: configuration.apply_configuration(policy, snapshot(), body),
        outcome=lambda body: configuration.read_configuration_outcome(
            policy, snapshot(), {key: body[key] for key in ("operation_id", "request_digest")}
        ),
    )


@pytest.fixture
def writer(tmp_path, monkeypatch):
    return _file_writer(tmp_path, monkeypatch)


def test_fingerprint_matches_application_defaults_order_and_hidden_exclusions():
    mapping = {
        "schema_version": 1,
        "storage": {"archive_root": "/srv/hfcache", "archive_id": ARCHIVE_ID},
        "repositories": [
            {"id": "owned/z", "type": "dataset", "tags": ["one"]},
            {"id": "owned/a", "type": "model", "enabled": False},
        ],
    }
    application = validate_config_mapping(mapping)
    document = application.model_dump(mode="json")
    assert configuration.configuration_fingerprint(document) == application.fingerprint()
    document["repositories"][0]["tags"] = ["two"]
    document["hub"]["credential_name"] = "another-private-source"
    assert configuration.configuration_fingerprint(document) == application.fingerprint()
    document["repositories"].reverse()
    assert configuration.configuration_fingerprint(document) != application.fingerprint()


def test_apply_preserves_original_inode_and_lock_and_observes_without_replay(writer):
    body = writer.request([{"kind": "settings-replace", "settings": {"sync": {"max_workers": 3}}}])
    original = configuration.CONFIGURATION.lstat()
    lock = configuration.LOCK.lstat()
    result = writer.apply(body)
    assert result["state"] == "confirmed"
    assert result["pending"] is False
    operation = configuration.APPLICATIONS / body["operation_id"]
    predecessor = operation / "predecessor.toml"
    assert predecessor.read_bytes() == writer.original == configuration.BACKUP.read_bytes()
    assert predecessor.lstat().st_ino == original.st_ino
    assert stat.S_IMODE(predecessor.lstat().st_mode) == 0o640
    assert configuration.LOCK.lstat() == lock
    assert writer.context(predecessor) == writer.contexts[(original.st_dev, original.st_ino)]
    assert tomllib.loads(configuration.CONFIGURATION.read_text())["sync"]["max_workers"] == 3
    installed = configuration.CONFIGURATION.lstat()
    assert writer.apply(body) == result == writer.outcome(body)
    assert configuration.CONFIGURATION.lstat() == installed
    encoded = json.dumps(result)
    assert "private-credential-name" not in encoded
    assert "candidate" not in result


def test_confirmed_history_and_backup_handover_survive_policy_change(writer):
    first = writer.request()
    writer.apply(first)
    backup = configuration.BACKUP.lstat()
    writer.state.deployment = b"legitimate-next-deployment"
    writer.state.policy = b"legitimate-next-policy"
    writer.state.permissions = {"configuration": False, "hub": False}
    assert writer.outcome(first)["state"] == "confirmed"
    assert writer.apply(first)["state"] == "confirmed"
    changed_principal = writer.snapshot()
    changed_principal.api_principal = (os.getuid(), os.getgid() + 1)
    historical = configuration.read_configuration_outcome(
        writer.policy,
        changed_principal,
        {key: first[key] for key in ("operation_id", "request_digest")},
    )
    assert historical["state"] == "confirmed"
    writer.state.permissions = {"configuration": True, "hub": True}
    second = writer.request(operation_id="b" * 32)
    writer.apply(second)
    archived = configuration.APPLICATIONS / second["operation_id"] / "previous-backup.toml"
    assert archived.lstat().st_ino == backup.st_ino
    assert archived.read_bytes() == writer.original
    assert writer.outcome(first)["state"] == "confirmed"


@pytest.mark.parametrize("drift", ["policy", "configuration"])
def test_captured_reconstruction_drift_refuses_before_first_pending_write(
    writer, monkeypatch, drift
):
    """Decision154: pure reconstruction never makes stale authority writable."""
    body = writer.request()
    captured = writer.snapshot()
    # Match AuthoritySnapshot: only full revalidation can see later revocation.
    captured_permissions = captured.status()["permissions"]
    captured.status = lambda: {"permissions": dict(captured_permissions)}
    reconstruct = writer.policy._prepare_configuration

    def changed(snapshot, managed):
        result = reconstruct(snapshot, managed)
        if drift == "policy":
            writer.state.policy = b"revoked-policy"
            writer.state.permissions["configuration"] = False
        else:
            with configuration.CONFIGURATION.open("ab") as output:
                output.write(b"# concurrent editor\n")
        return result

    monkeypatch.setattr(writer.policy, "_prepare_configuration", changed)
    with pytest.raises(host_policy.InspectionError if drift == "policy" else ValueError):
        configuration.apply_configuration(writer.policy, captured, body)
    assert configuration.CONFIGURATION.read_bytes() == (
        writer.original + (b"# concurrent editor\n" if drift == "configuration" else b"")
    )
    for path in (
        configuration.PENDING,
        configuration.APPLICATIONS,
        configuration.CANDIDATE,
        configuration.BACKUP,
    ):
        assert not path.exists()


def test_policy_revocation_after_backup_refuses_exchange_and_preserves_original(
    writer, monkeypatch
):
    """Decision154: staged evidence and the original inode survive a lost grant."""
    body = writer.request()
    original = configuration.CONFIGURATION.lstat()
    fired = False

    def revoke(name):
        nonlocal fired
        if name == "backup_ready:target:after_directory_fsync":
            fired = True
            writer.state.policy = b"revoked-policy"
            writer.state.permissions["configuration"] = False

    monkeypatch.setattr(configuration, "checkpoint", revoke)
    with pytest.raises(host_policy.InspectionError):
        writer.apply(body)
    assert fired
    assert configuration.CONFIGURATION.lstat() == original
    assert configuration.CONFIGURATION.read_bytes() == writer.original
    assert configuration.PENDING.is_file()
    assert configuration.CANDIDATE.is_file()
    assert configuration.BACKUP.read_bytes() == writer.original
    operation = configuration.APPLICATIONS / body["operation_id"]
    assert (
        json.loads((operation / "outcome.json").read_bytes())["record"]["phase"] == "backup_ready"
    )
    retained = {
        str(path): (configuration._identity(path.lstat()), path.read_bytes())
        for path in writer.root.rglob("*")
        if path.is_file()
    }
    # Same original ID is observation only; it cannot finish or clear the stage.
    observed = writer.outcome(body)
    assert observed["state"] == "staged"
    assert observed["pending"] is True
    assert writer.apply(body) == observed
    assert {
        str(path): (configuration._identity(path.lstat()), path.read_bytes())
        for path in writer.root.rglob("*")
        if path.is_file()
    } == retained


@pytest.mark.parametrize("name", ["CANDIDATE", "BACKUP", "PENDING"])
def test_unknown_legacy_paths_refuse_without_overwrite(writer, name):
    path = getattr(configuration, name)
    path.write_bytes(b"unknown original evidence")
    path.chmod(0o640 if name != "PENDING" else 0o600)
    before = path.lstat()
    with pytest.raises(ValueError, match="protected configuration"):
        writer.apply(writer.request())
    assert path.read_bytes() == b"unknown original evidence"
    assert path.lstat() == before
    assert configuration.CONFIGURATION.read_bytes() == writer.original


def test_unknown_and_corrupt_history_block_and_reads_never_create(writer):
    body = writer.request()
    configuration.LOCK.unlink()
    before = sorted(writer.root.iterdir())
    assert writer.outcome(body)["state"] == "unknown"
    assert sorted(writer.root.iterdir()) == before
    configuration.LOCK.touch(mode=0o600)
    writer.apply(body)
    path = configuration.APPLICATIONS / body["operation_id"] / "outcome.json"
    path.write_bytes(path.read_bytes().replace(b'"confirmed"', b'"intent"'))
    assert writer.outcome(body)["state"] == "unknown"
    with pytest.raises(ValueError, match="protected configuration"):
        writer.apply(writer.request(operation_id="b" * 32))


@pytest.mark.parametrize(
    "field", ["candidate_revision", "config_fingerprint", "required_selectors"]
)
def test_identity_mismatch_refuses_before_private_or_fixed_mutation(writer, field):
    body = writer.request()
    body[field] = ["model:owned/wrong"] if field == "required_selectors" else "0" * 64
    with pytest.raises(ValueError, match="protected configuration"):
        writer.apply(body)
    assert not configuration.APPLICATIONS.exists()
    assert not configuration.PENDING.exists()
    assert configuration.CONFIGURATION.read_bytes() == writer.original


def test_permission_and_digest_conflicts_do_not_repeat_effect(writer):
    body = writer.request(
        [{"kind": "repository-upsert", "repository": {"type": "model", "id": "owned/new"}}]
    )
    writer.state.permissions["hub"] = False
    with pytest.raises(host_policy.InspectionError, match="protected host inspection refused"):
        writer.apply(body)
    assert not configuration.APPLICATIONS.exists()
    writer.state.permissions["hub"] = True
    writer.apply(body)
    body["request_digest"] = "0" * 64
    with pytest.raises(host_policy.InspectionError):
        writer.apply(body)
    with pytest.raises(host_policy.InspectionError):
        writer.outcome(body)


def test_missing_original_lock_is_never_recreated(writer):
    body = writer.request()
    configuration.LOCK.unlink()
    with pytest.raises(FileNotFoundError):
        writer.apply(body)
    assert not configuration.LOCK.exists()
    assert not configuration.APPLICATIONS.exists()
    assert configuration.CONFIGURATION.read_bytes() == writer.original


def test_authenticated_but_incompatible_private_schema_remains_unknown(writer):
    body = writer.request()
    writer.apply(body)
    path = configuration.APPLICATIONS / body["operation_id"] / "outcome.json"
    envelope = json.loads(path.read_bytes())
    envelope["record"]["schema_version"] = True
    envelope["authentication"] = configuration._seal(
        writer.state.key, envelope["record"], b"host-config-outcome-v1"
    )
    path.write_bytes(configuration._encoded(envelope))
    assert writer.outcome(body)["state"] == "unknown"
    with pytest.raises(ValueError, match="protected configuration"):
        writer.apply(writer.request(operation_id="b" * 32))


def test_maximum_valid_selection_fits_private_metadata_without_losing_scope(writer):
    edits = [
        {
            "kind": "repository-upsert",
            "repository": {"type": "model", "id": "o" * 96 + "/" + "r" * 91 + f"{index:05d}"},
        }
        for index in range(256)
    ]
    body = writer.request(edits)
    assert len(body["required_selectors"]) == 256
    assert writer.apply(body)["state"] == "confirmed"
    stored = configuration.APPLICATIONS / body["operation_id"] / "outcome.json"
    assert len(stored.read_bytes()) > 32768
    assert len(stored.read_bytes()) <= configuration.MAX_STATE


def test_private_paths_require_captured_local_filesystem_proof(writer):
    body = writer.request()
    captured = writer.snapshot()

    def refuse(_path):
        reason = "facts-unavailable"
        raise host_policy.InspectionError(reason)

    captured._inspection.capture.local = refuse
    with pytest.raises(host_policy.InspectionError):
        configuration.apply_configuration(writer.policy, captured, body)
    assert not configuration.APPLICATIONS.exists()


@pytest.mark.parametrize(
    ("point", "expected_state", "expected_pending"),
    [
        ("base:before_file_fsync", "unknown", True),
        ("intent:before_rename", "unknown", True),
        ("pending:after_file_fsync", "unknown", True),
        ("pending:after_directory_fsync", "unknown", True),
        ("stage:before_file_fsync", "unchanged", True),
        ("staged:after_rename", "staged", True),
        ("backup:after_file_fsync", "staged", True),
        ("backup_ready:after_rename", "staged", True),
        ("install_intent:after_directory_fsync", "unknown", True),
        ("exchange:before_rename", "staged", True),
        ("exchange:after_rename", "installed_unconfirmed", True),
        ("exchange:source:before_directory_fsync", "installed_unconfirmed", True),
        ("exchange:source:after_directory_fsync", "installed_unconfirmed", True),
        ("exchange:target:before_directory_fsync", "installed_unconfirmed", True),
        ("exchange:target:after_directory_fsync", "installed_unconfirmed", True),
        ("predecessor:after_rename", "installed_unconfirmed", True),
        ("installed:after_rename", "installed_unconfirmed", True),
        ("confirm:before_read", "installed_unconfirmed", True),
        ("confirmed:after_rename", "confirmed", True),
        ("pending:before_unlink", "confirmed", True),
        ("pending:after_unlink", "confirmed", False),
        ("pending-clear:after_directory_fsync", "confirmed", False),
    ],
)
def test_fault_boundaries_preserve_and_never_replay(
    writer, monkeypatch, point, expected_state, expected_pending
):
    body = writer.request()
    before_inode = configuration.CONFIGURATION.lstat().st_ino
    fired = False

    def fail(name):
        nonlocal fired
        if not fired and name == point:
            fired = True
            raise OSError(5, "injected storage boundary")

    monkeypatch.setattr(configuration, "checkpoint", fail)
    with pytest.raises(OSError, match="injected"):
        writer.apply(body)
    assert fired
    monkeypatch.setattr(configuration, "checkpoint", lambda _name: None)
    before = {
        str(path): (configuration._identity(path.lstat()), path.read_bytes())
        for path in writer.root.rglob("*")
        if path.is_file()
    }
    observed = writer.outcome(body)
    repeated = writer.apply(body)
    assert repeated == observed
    assert {
        str(path): (configuration._identity(path.lstat()), path.read_bytes())
        for path in writer.root.rglob("*")
        if path.is_file()
    } == before
    assert before_inode in {
        path.lstat().st_ino for path in writer.root.rglob("*") if path.is_file()
    }
    assert observed["state"] == expected_state
    assert observed["pending"] is expected_pending
    fresh = writer.request(operation_id="b" * 32)
    if point in {"pending:after_unlink", "pending-clear:after_directory_fsync"}:
        assert writer.apply(fresh)["state"] == "confirmed"
        assert writer.outcome(body)["state"] == "confirmed"
    else:
        with pytest.raises(ValueError, match="protected configuration"):
            writer.apply(fresh)


def test_first_durable_marker_blocks_without_workspace_and_binds_original_digest(
    writer, monkeypatch
):
    body = writer.request()
    original = configuration.CONFIGURATION.lstat()
    lock = configuration.LOCK.lstat()

    def fail(name):
        if name == "pending:after_directory_fsync":
            raise OSError(5, "injected first durable intent")

    monkeypatch.setattr(configuration, "checkpoint", fail)
    with pytest.raises(OSError, match="injected"):
        writer.apply(body)
    assert configuration.PENDING.exists()
    assert not (configuration.APPLICATIONS / body["operation_id"]).exists()
    assert not configuration.CANDIDATE.exists()
    assert not configuration.BACKUP.exists()
    pending = configuration.PENDING.read_bytes()
    assert configuration.CONFIGURATION.lstat() == original
    assert configuration.LOCK.lstat() == lock
    monkeypatch.setattr(configuration, "checkpoint", lambda _name: None)
    expected = writer.outcome(body)
    assert expected["state"] == "unknown"
    assert expected["pending"] is True
    fresh = writer.request(operation_id="b" * 32)
    writer.state.permissions = {"configuration": False, "hub": False}
    assert writer.apply(body) == expected
    assert configuration.PENDING.read_bytes() == pending
    assert not (configuration.APPLICATIONS / body["operation_id"]).exists()
    conflicting = body | {"request_digest": "0" * 64}
    with pytest.raises(host_policy.InspectionError) as caught:
        writer.apply(conflicting)
    assert caught.value.reason == "config-conflict"
    with pytest.raises(host_policy.InspectionError):
        writer.outcome(conflicting)
    with pytest.raises(ValueError, match="protected configuration"):
        writer.apply(fresh)
    assert configuration.PENDING.read_bytes() == pending
    assert configuration.CONFIGURATION.lstat() == original


def test_confirmed_pending_crash_stays_blocked_and_quota_never_deletes(writer, monkeypatch):
    body = writer.request()

    def fail(name):
        if name == "pending:before_unlink":
            raise OSError(5, "injected ack loss")

    monkeypatch.setattr(configuration, "checkpoint", fail)
    with pytest.raises(OSError, match="injected"):
        writer.apply(body)
    assert writer.outcome(body)["state"] == "confirmed"
    assert writer.outcome(body)["pending"]
    with pytest.raises(ValueError, match="protected configuration"):
        writer.apply(writer.request(operation_id="b" * 32))
    # An operator action is explicit in this unit setup, never outcome-read repair.
    configuration.PENDING.unlink()
    monkeypatch.setattr(configuration, "checkpoint", lambda _name: None)
    monkeypatch.setattr(configuration, "MAX_RECORDS", 1)
    with pytest.raises(ValueError, match="protected configuration"):
        writer.apply(writer.request(operation_id="b" * 32))
    assert writer.outcome(body)["state"] == "confirmed"
    monkeypatch.setattr(configuration, "MAX_RECORDS", 64)
    monkeypatch.setattr(configuration, "MAX_PRIVATE_BYTES", 1)
    with pytest.raises(ValueError, match="protected configuration"):
        writer.apply(writer.request(operation_id="b" * 32))


def test_module_is_standard_library_and_python312():
    source = Path(configuration.__file__).read_text()
    tree = ast.parse(source, feature_version=(3, 12))
    imports = {
        node.names[0].name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
    }
    assert "hfcache" not in imports


def _successful_checkpoint_walk(prior_application):
    # Discover actual named durability boundaries using the real Store/syscalls.
    # Only the already documented protected-capture/SID fixture is substituted.
    with (
        tempfile.TemporaryDirectory(prefix="hfcache-config-walk-") as temporary,
        pytest.MonkeyPatch.context() as patch,
    ):
        instance = _file_writer(Path(temporary), patch)
        if prior_application:
            instance.apply(instance.request(operation_id="d" * 32))
        emitted = []
        patch.setattr(configuration, "checkpoint", emitted.append)
        instance.apply(instance.request())
        return tuple(dict.fromkeys(emitted))


_FIRST_CUTS = _successful_checkpoint_walk(prior_application=False)
_SECOND_CUTS = _successful_checkpoint_walk(prior_application=True)
_EXHAUSTIVE_CUTS = [(False, name) for name in _FIRST_CUTS] + [(True, name) for name in _SECOND_CUTS]


def _owned_tree(instance):
    result = {}
    for path in [instance.root, *sorted(instance.root.rglob("*"))]:
        assert not path.is_symlink()
        result[str(path.relative_to(instance.root))] = (
            configuration._identity(path.lstat()),
            instance.context(path),
            path.read_bytes() if path.is_file() else None,
        )
    return result


def test_exhaustive_walk_includes_all_current_first_and_previous_backup_boundaries():
    assert len(_FIRST_CUTS) == 114
    assert len(_SECOND_CUTS) == 120
    assert set(_FIRST_CUTS) <= set(_SECOND_CUTS)
    assert set(_SECOND_CUTS) - set(_FIRST_CUTS) == {
        "previous-backup:before_rename",
        "previous-backup:after_rename",
        "previous-backup:source:before_directory_fsync",
        "previous-backup:source:after_directory_fsync",
        "previous-backup:target:before_directory_fsync",
        "previous-backup:target:after_directory_fsync",
    }


@pytest.mark.parametrize(("prior_application", "point"), _EXHAUSTIVE_CUTS)
def test_every_emitted_durability_cut_preserves_inodes_and_observes_without_replay(
    writer, monkeypatch, prior_application, point
):
    previous = None
    if prior_application:
        previous = writer.request(operation_id="d" * 32)
        assert writer.apply(previous)["state"] == "confirmed"
    body = writer.request()
    prepared = host_policy.prepare_configuration(writer.snapshot(), body["managed"])
    base = configuration.CONFIGURATION.read_bytes()
    candidate = prepared["candidate"].encode("utf-8")
    original_inode = configuration.CONFIGURATION.lstat().st_ino
    backup_inode = configuration.BACKUP.lstat().st_ino if configuration.BACKUP.exists() else None
    lock = configuration._identity(configuration.LOCK.lstat())
    fired = []

    def interrupt(name):
        if name == point and not fired:
            fired.append(name)
            raise OSError(5, "injected exhaustive durability cut")

    monkeypatch.setattr(configuration, "checkpoint", interrupt)
    with pytest.raises(OSError, match="injected exhaustive durability cut"):
        writer.apply(body)
    assert fired == [point]
    monkeypatch.setattr(configuration, "checkpoint", lambda _name: None)
    preserved = _owned_tree(writer)
    observed = writer.outcome(body)
    assert _owned_tree(writer) == preserved
    assert configuration._identity(configuration.LOCK.lstat()) == lock
    assert configuration.CONFIGURATION.read_bytes() in (base, candidate)
    current_inodes = {path.lstat().st_ino for path in writer.root.rglob("*") if path.is_file()}
    assert original_inode in current_inodes
    if backup_inode is not None:
        assert backup_inode in current_inodes
    if previous is not None:
        assert writer.outcome(previous)["state"] == "confirmed"
        assert _owned_tree(writer) == preserved

    if point == "pending:before_write":
        # There is no private ledger/intent yet. Do not retransmit the effect to
        # test observation: the API's original admitted receipt owns no-replay.
        assert observed["state"] == "unknown"
        assert observed["pending"] is False
        assert not (configuration.APPLICATIONS / body["operation_id"]).exists()
        assert not configuration.PENDING.exists()
        assert not configuration.CANDIDATE.exists()
        assert configuration.CONFIGURATION.lstat().st_ino == original_inode
        assert configuration.CONFIGURATION.read_bytes() == base
        return

    assert writer.apply(body) == observed
    assert _owned_tree(writer) == preserved
    if observed["state"] != "confirmed" or observed["pending"]:
        with pytest.raises(ValueError, match="protected configuration"):
            writer.apply(writer.request(operation_id="b" * 32))
        assert _owned_tree(writer) == preserved
