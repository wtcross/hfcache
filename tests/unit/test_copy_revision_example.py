"""Consumer publication identity and full verification use owned temporary trees."""

import hashlib
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]


@pytest.fixture
def publication(tmp_path):
    mount = tmp_path / "published"
    tree_relative = "repos/models/org/model/revisions/" + "a" * 40 + "/" + "b" * 32
    tree = mount / tree_relative
    tree.mkdir(parents=True)
    content = b"fixture model\n"
    (tree / "model.bin").write_bytes(content)
    manifest_path = mount / "manifests/model.json"
    manifest_path.parent.mkdir()
    reference = {
        "commit_sha": "a" * 40,
        "publication_id": "b" * 32,
        "publication_generation": 7,
        "tree": tree_relative,
        "manifest": "manifests/model.json",
    }
    manifest = {
        "commit_sha": reference["commit_sha"],
        "publication_id": reference["publication_id"],
        "tree": "published/" + tree_relative,
        "files": [
            {
                "path": "model.bin",
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        ],
    }
    manifest_path.write_text(json.dumps(manifest))
    ref_path = mount / "repos/models/org/model/refs/current.json"
    ref_path.parent.mkdir()
    ref_path.write_text(json.dumps(reference))
    destination = tmp_path / "revisions/new-model"
    namespace = runpy.run_path(str(ROOT / "examples/copy-revision.py"))
    arguments = [
        "--mount",
        str(mount),
        "--type",
        "model",
        "--repository",
        "org/model",
        "--destination",
        str(destination),
        "--attempts",
        "1",
        "--json",
    ]
    return namespace, arguments, tree, manifest_path, ref_path, destination


def test_documented_consumer_copy_reports_exact_identity_and_verified_bytes(publication, capsys):
    helper, arguments, tree, manifest, reference, destination = publication
    before = (manifest.read_bytes(), reference.read_bytes(), (tree / "model.bin").read_bytes())
    assert helper["main"](arguments) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["verified"] is True
    assert result["commit_sha"] == "a" * 40
    assert result["publication_id"] == "b" * 32
    assert result["publication_generation"] == 7
    assert result["attempts"] == 1
    assert result["file_count"] == 1
    assert (destination / "model.bin").read_bytes() == before[2]
    assert (
        manifest.read_bytes(),
        reference.read_bytes(),
        (tree / "model.bin").read_bytes(),
    ) == before


@pytest.mark.parametrize("corruption", ["digest", "size", "missing", "extra"])
def test_failed_full_verification_preserves_existing_destination(publication, capsys, corruption):
    helper, arguments, tree, _, _, destination = publication
    destination.mkdir(parents=True)
    (destination / "serving.marker").write_text("preserve")
    if corruption == "digest":
        (tree / "model.bin").write_bytes(b"changed bytes\n")
    elif corruption == "size":
        (tree / "model.bin").write_bytes(b"short")
    elif corruption == "missing":
        (tree / "model.bin").unlink()
    else:
        (tree / "extra").write_text("unexpected")
    assert helper["main"](arguments) == 1
    assert corruption + ":" in capsys.readouterr().err
    assert list(destination.iterdir()) == [destination / "serving.marker"]
    assert (destination / "serving.marker").read_text() == "preserve"
    assert list(destination.parent.iterdir()) == [destination]


def test_mismatched_publication_refuses_before_creating_destination(publication, capsys):
    helper, arguments, _, manifest_path, _, destination = publication
    manifest = json.loads(manifest_path.read_text())
    manifest["publication_id"] = "c" * 32
    manifest_path.write_text(json.dumps(manifest))
    assert helper["main"](arguments) == 2
    assert "different instance" in capsys.readouterr().err
    assert not destination.parent.exists()


def test_vanished_instance_retry_rereads_one_new_reference(publication, monkeypatch, capsys):
    helper, arguments, _, _, reference_path, destination = publication
    original_copy = helper["copy_tree"]
    calls = []

    def retire_then_copy(source, target):
        calls.append(source)
        if len(calls) == 1:
            new_tree = source.with_name("c" * 32)
            new_tree.mkdir()
            (new_tree / "model.bin").write_bytes((source / "model.bin").read_bytes())
            reference = json.loads(reference_path.read_text())
            mount = reference_path.parents[5]
            old_manifest = json.loads((mount / reference["manifest"]).read_text())
            old_manifest["publication_id"] = "c" * 32
            reference["publication_id"] = "c" * 32
            reference["publication_generation"] = 7
            reference["tree"] = str(new_tree.relative_to(mount))
            reference["manifest"] = "manifests/replacement.json"
            old_manifest["tree"] = "published/" + reference["tree"]
            (mount / reference["manifest"]).write_text(json.dumps(old_manifest))
            reference_path.write_text(json.dumps(reference))
            message = "original tree vanished"
            raise helper["RetryableError"](message)
        original_copy(source, target)

    monkeypatch.setitem(helper["attempt"].__globals__, "copy_tree", retire_then_copy)
    arguments[arguments.index("--attempts") + 1] = "2"
    assert helper["main"](arguments) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["attempts"] == 2
    assert result["publication_id"] == "c" * 32
    assert result["publication_generation"] == 7
    assert calls[0] != calls[1]
    assert (destination / "model.bin").is_file()
