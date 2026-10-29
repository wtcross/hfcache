"""Catalog authority and descriptor containment remain mandatory (AD-12, FS-09/FS-15)."""

import json
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest

from hfcache.errors import HfcacheError
from hfcache.identity import CommitSha, PublicationId
from hfcache.metadata import MetadataReader
from hfcache.paths import ArchiveLayout
from tests.unit import test_catalog_queries as fixtures

config = fixtures.config
layout = fixtures.layout


@pytest.mark.parametrize("observation_present", [True, False])
@pytest.mark.parametrize("damage", ["corrupt_manifest", "manifest_generation", "symlink_manifest"])
def test_selected_authority_is_required_with_present_or_missing_observation(
    config, layout, tmp_path, observation_present, damage
):
    record = fixtures.publish(layout)
    repository = layout.repository(fixtures.MODEL)
    sha, publication = CommitSha(record.commit_sha), PublicationId(record.publication_id)
    if not observation_present:
        repository.observation(sha, publication).unlink()
    manifest = repository.manifest(sha, publication)
    if damage == "corrupt_manifest":
        manifest.write_bytes(b"corrupt")
    elif damage == "manifest_generation":
        value = json.loads(manifest.read_bytes())
        value["publication_generation"] += 1
        manifest.write_text(json.dumps(value))
    else:
        outside = tmp_path / "external-valid-manifest.json"
        outside.write_bytes(manifest.read_bytes())
        manifest.unlink()
        manifest.symlink_to(outside)
    with pytest.raises(HfcacheError) as refusal:
        fixtures.search(config, scope="all", limit=1)
    assert any(problem.code == "HFVER007" for problem in refusal.value.problems)


@pytest.mark.parametrize(
    ("path", "root"),
    [
        ("/srv/a", "/srv"),
        ("/srv", "/srv"),
        ("/", "/"),
        ("//a/b", "//a"),
        ("//a/b", "/a"),
        ("/a/b", "//a"),
        ("/srv-other/a", "/srv"),
        ("/srv/a/../b", "/srv"),
        ("a/../b", "."),
        ("a", "a"),
        ("a/b", "/a"),
        ("/a/b", "a"),
        (".", "."),
        ("/資料/λ", "/資料"),
    ],
)
def test_lexical_containment_matches_public_posix_path_semantics(path, root):
    path, root = Path(path), Path(root)
    try:
        expected = PurePosixPath(path.relative_to(root))
    except ValueError:
        with pytest.raises(ValueError, match="not inside the test root"):
            ArchiveLayout._relative(path, root, "test root")
    else:
        assert ArchiveLayout._relative(path, root, "test root") == expected


@pytest.mark.parametrize(
    ("path", "root"),
    [
        ("C:/Archive/a", "c:/archive"),
        ("C:/Archive/a", "C:/Archive"),
        ("D:/Archive/a", "C:/Archive"),
    ],
)
def test_lexical_fallback_retains_other_path_flavour_rules(path, root):
    path, root = PureWindowsPath(path), PureWindowsPath(root)
    try:
        expected = PurePosixPath(path.relative_to(root))
    except ValueError:
        with pytest.raises(ValueError, match="not inside the test root"):
            ArchiveLayout._relative(path, root, "test root")
    else:
        assert ArchiveLayout._relative(path, root, "test root") == expected


@pytest.mark.parametrize("suffix", ["sibling", "../escape", "nested/../../escape"])
def test_metadata_escape_refuses_before_opening_any_descriptor(tmp_path, monkeypatch, suffix):
    root = tmp_path / "archive"
    candidate = root.with_name("archive-sibling") if suffix == "sibling" else root / suffix

    def forbidden(*args, **kwargs):
        pytest.fail("a lexical escape reached the descriptor walk")

    monkeypatch.setattr("hfcache.metadata.os.open", forbidden)
    with pytest.raises(ValueError, match=r"not contained|is not in"):
        MetadataReader(root).open(candidate)
