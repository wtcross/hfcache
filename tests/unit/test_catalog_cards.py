"""ADR142: exact bounded source provenance and inert, secret-free presentation."""

import hashlib
import json
import os

import pytest

from hfcache.catalog_cards import capture_repository_card, validate_card_presentation
from hfcache.catalog_extractors import ExtractionBudget, SourceStream
from hfcache.catalog_models import MAXIMUM_CARD_PRESENTATION_BYTES, MAXIMUM_CARD_SOURCE_BYTES
from hfcache.catalog_parsing import ExtractionError
from hfcache.models import dump
from hfcache.redaction import clear_registered_secrets, contains_secret, register_secret
from tests.fixtures import examples
from tests.unit.test_catalog_extractors import publication

MANIFEST_DIGEST = "a" * 64


def capture(access):
    return capture_repository_card(access, MANIFEST_DIGEST, archive_id=examples.ARCHIVE_ID)


@pytest.mark.parametrize("repository_type", ["model", "dataset"])
def test_exact_card_provenance_safe_links_and_immutable_evidence(tmp_path, repository_type):
    raw = (
        b"---\nlanguage: en\n---\n# A card\n"
        b"[relative](docs/use.md#start) [fragment](#heading) "
        b'[web](https://example.invalid/read?q=1&n=2 "title")\n'
        b"[reference][guide]\n[guide]: ../guide.md\n"
        b"Bare https://example.invalid is inert source.\n"
        b"![remote](https://example.invalid/image.svg) next words\n"
        b"`<script> inert </script>`\n```python\nprint('<script>')\n```\n"
        b"| A | B |\n|---|---|\n| 1 | 2 |\n"
    )
    access = publication(tmp_path, {"README.md": raw}, repository_type=repository_type)
    original = access.manifest.to_payload()
    path = access.tree / "README.md"
    before = path.stat()
    card = capture(access)
    assert card.state == "present"
    assert card.source_path == "README.md"
    assert card.repository_type == repository_type
    assert card.manifest_digest == MANIFEST_DIGEST
    assert card.manifest_path.endswith(f"/{examples.SHA}/{examples.PUBLICATION}.json")
    assert card.expected_source_sha256 == hashlib.sha256(raw).hexdigest()
    assert card.markdown == raw.decode().split("---\n", 2)[2].replace(
        "![remote](https://example.invalid/image.svg)", r"\[image omitted\]"
    )
    assert card.markdown is not None
    assert card.presentation_sha256 == hashlib.sha256(card.markdown.encode()).hexdigest()
    assert card.diagnostics == ()
    assert access.budget.read_bytes == len(raw)
    assert access.budget.candidates == 1
    assert path.read_bytes() == raw
    after = path.stat()
    assert (before.st_ino, before.st_mtime_ns, before.st_ctime_ns) == (
        after.st_ino,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    assert access.manifest.to_payload() == original


def test_only_exact_manifest_root_readme_is_selected_and_missing_is_normal(tmp_path, monkeypatch):
    access = publication(tmp_path, {"nested/README.md": b"not root", "loader.py": b"raise"})

    def forbidden(*_args, **_kwargs):
        pytest.fail("absent root card opened a different source")

    monkeypatch.setattr(access.reader, "open", forbidden)
    card = capture(access)
    assert card.state == "absent"
    assert card.diagnostics == ("readme_absent",)
    assert card.source_path is card.expected_source_sha256 is None
    assert card.markdown is card.presentation_sha256 is None
    assert access.budget.read_bytes == access.budget.candidates == 0


@pytest.mark.parametrize(
    "raw",
    [
        b"hf_12345678",
        b"---\nsecret: Bearer opaque-secret\n---\npublic",
        b"![omit](https://example.invalid/?X-Amz-Signature=opaque)",
        b"```\nBasic opaque-credential\n```\n",
        b"Registered-Card-Credential",
        b"registered-card-credential",
    ],
)
def test_credentials_anywhere_withhold_whole_body_before_omissions(tmp_path, raw):
    register_secret("Registered-Card-Credential")
    try:
        access = publication(tmp_path, {"README.md": raw})
        card = capture(access)
        assert card.state == "unsafe"
        assert card.diagnostics == ("secret_suppressed",)
        assert card.markdown is card.presentation_sha256 is None
        assert raw not in dump(card)
        assert (access.tree / "README.md").read_bytes() == raw
    finally:
        clear_registered_secrets()


@pytest.mark.parametrize(
    ("raw", "state", "diagnostic"),
    [
        (b"\xff", "unsupported", "invalid_utf8"),
        (b"<details>ordinary HTML</details>", "unsupported", "unsupported_markdown"),
        (b"{dangerousMdx()}", "unsupported", "unsupported_markdown"),
        (b"import Card from './card'", "unsupported", "unsupported_markdown"),
        (b"```{handler}\nbody\n```\n", "unsupported", "unsupported_markdown"),
        (b"```python\nunclosed", "unsupported", "unsupported_markdown"),
        (b"---\nunclosed: metadata", "unsupported", "unsupported_markdown"),
        (b"unclosed `code", "unsupported", "unsupported_markdown"),
        (b"[x](javascript:alert)", "unsafe", "unsafe_content"),
        (b"[x](data:text/html,body)", "unsafe", "unsafe_content"),
        (b"[x](jav&#x61;script:alert)", "unsupported", "unsupported_markdown"),
        (b"[x](//example.invalid)", "unsupported", "unsupported_markdown"),
        (b"[x](https://name:password@example.invalid)", "unsupported", "unsupported_markdown"),
        (b"[x](../nested/(uncertain).md)", "unsupported", "unsupported_markdown"),
        (b"[<script>](https://example.invalid)", "unsupported", "unsupported_markdown"),
        (b"[<script>]: https://example.invalid", "unsupported", "unsupported_markdown"),
        (b"[x](https://[invalid)", "unsupported", "unsupported_markdown"),
        (b"[nested[label]](safe.md)", "unsupported", "unsupported_markdown"),
        (b"<not-an-autolink>", "unsupported", "unsupported_markdown"),
        (b"[unclosed", "unsupported", "unsupported_markdown"),
        (b"unmatched ]", "unsupported", "unsupported_markdown"),
        (b"bad\x00control", "unsafe", "unsafe_content"),
    ],
)
def test_nonpresent_classifications_never_retain_source(tmp_path, raw, state, diagnostic):
    access = publication(tmp_path, {"README.md": raw})
    card = capture(access)
    assert card.state == state
    assert card.diagnostics == (diagnostic,)
    assert card.markdown is card.presentation_sha256 is None
    assert card.expected_source_sha256 == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("raw", [b"", b"---\nlanguage: en\n---\n", "# café 😺\n".encode()])
def test_empty_and_unicode_presentations_are_real_present_cards(tmp_path, raw):
    card = capture(publication(tmp_path, {"README.md": raw}))
    assert card.state == "present"
    assert card.markdown is not None
    assert card.presentation_sha256 == hashlib.sha256(card.markdown.encode()).hexdigest()


def test_source_limit_refuses_before_read_and_charges_attempt(tmp_path):
    access = publication(tmp_path, {"README.md": b"a" * (MAXIMUM_CARD_SOURCE_BYTES + 1)})
    card = capture(access)
    assert card.state == "oversize"
    assert card.diagnostics == ("source_oversize",)
    assert access.budget.candidates == 1
    assert access.budget.read_bytes == 0


def test_image_placeholder_expansion_is_bounded_before_join(tmp_path):
    access = publication(tmp_path, {"README.md": b"![x]" * 100000})
    card = capture(access)
    assert card.state == "oversize"
    assert card.diagnostics == ("presentation_oversize",)
    assert card.markdown is None
    assert access.budget.read_bytes == 400000


def test_only_matching_maximal_inline_fences_hide_raw_html(tmp_path):
    raw = b"`` one ` tick <script> `` and `two `` ticks`\n\\`<script>"
    card = capture(publication(tmp_path, {"README.md": raw}))
    assert card.state == "unsupported"
    assert card.diagnostics == ("unsupported_markdown",)
    assert card.markdown is None
    safe = b"`` one ` tick <script> `` and `two `` ticks`\n"
    safe_card = capture(publication(tmp_path / "safe", {"README.md": safe}))
    assert safe_card.state == "present"
    assert safe_card.markdown == safe.decode()


def test_simple_autolinks_reference_images_and_escaped_punctuation(tmp_path):
    raw = b"<https://example.invalid> ![x][ref] ![x]\n[ref]: ./a.md\n\\*literal\\*\n"
    card = capture(publication(tmp_path, {"README.md": raw}))
    assert card.state == "present"
    assert card.markdown == (
        "<https://example.invalid> \\[image omitted\\] \\[image omitted\\]\n"
        "[ref]: ./a.md\n\\*literal\\*\n"
    )


@pytest.mark.parametrize(
    ("raw", "present"),
    [
        (b"a" * (MAXIMUM_CARD_PRESENTATION_BYTES - 2), True),
        (b"a" * (MAXIMUM_CARD_PRESENTATION_BYTES - 1), False),
        (b'"' * (MAXIMUM_CARD_PRESENTATION_BYTES // 2 - 1), True),
        (b'"' * (MAXIMUM_CARD_PRESENTATION_BYTES // 2), False),
        ("😺".encode() * (MAXIMUM_CARD_PRESENTATION_BYTES // 4 - 1), True),
        ("😺".encode() * (MAXIMUM_CARD_PRESENTATION_BYTES // 4), False),
    ],
)
def test_utf8_and_json_string_independent_exact_bounds(tmp_path, raw, present):
    access = publication(tmp_path, {"README.md": raw})
    card = capture(access)
    assert card.state == ("present" if present else "oversize")
    assert access.budget.read_bytes == len(raw)
    if present:
        assert card.markdown is not None
        assert len(card.markdown.encode()) <= MAXIMUM_CARD_PRESENTATION_BYTES
        assert len(json.dumps(card.markdown, ensure_ascii=False).encode()) <= (
            MAXIMUM_CARD_PRESENTATION_BYTES
        )
    else:
        assert card.diagnostics == ("presentation_oversize",)
        assert card.markdown is None


@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory", "ancestor", "missing"])
def test_no_follow_regular_sources_only_without_target_reads(tmp_path, kind):
    access = publication(tmp_path, {"README.md": b"expected"})
    path = access.tree / "README.md"
    if kind == "ancestor":
        moved = access.tree.with_name("original-tree")
        access.tree.rename(moved)
        access.tree.symlink_to(moved, target_is_directory=True)
    else:
        path.unlink()
        if kind == "symlink":
            path.symlink_to(tmp_path / "never-open")
        elif kind == "fifo":
            os.mkfifo(path)
        elif kind == "directory":
            path.mkdir()
    card = capture(access)
    assert card.state == "failed"
    assert card.diagnostics == ("read_failed",)
    assert card.markdown is None
    assert access.budget.read_bytes == 0
    assert access.budget.candidates == 1


def test_fresh_source_digest_is_distinct_from_old_ordinary_declaration_read(tmp_path):
    access = publication(tmp_path, {"README.md": b"original"})
    (access.tree / "README.md").write_bytes(b"modified")
    assert access.read("README.md") == b"modified"  # old ordinary read behavior is unchanged
    card = capture(access)
    assert card.state == "failed"
    assert card.diagnostics == ("source_digest_mismatch",)
    assert card.markdown is None
    assert access.budget.read_bytes == 16


@pytest.mark.parametrize("change", ["replace", "mode", "bytes"])
def test_descriptor_and_nofollow_path_rejoin_after_actual_read(tmp_path, monkeypatch, change):
    access = publication(tmp_path, {"README.md": b"original"})
    path = access.tree / "README.md"
    original = SourceStream.read

    def changed(source, count):
        raw = original(source, count)
        if change == "replace":
            path.rename(path.with_name("original-readme"))
            path.write_bytes(raw)
        elif change == "mode":
            path.chmod(0o600)
        else:
            path.write_bytes(b"modified")
        return raw

    monkeypatch.setattr(SourceStream, "read", changed)
    card = capture(access)
    assert card.state == "failed"
    assert card.diagnostics == ("source_changed",)
    assert card.markdown is None
    assert access.budget.read_bytes == 8


def test_shared_read_and_work_budget_refusals_never_reset_for_cards(tmp_path):
    access = publication(
        tmp_path, {"README.md": b"12345"}, budget=ExtractionBudget(maximum_bytes=7)
    )
    assert access.read("README.md") == b"12345"
    assert capture(access).diagnostics == ("work_limit",)
    assert access.budget.read_bytes == 5
    assert access.budget.candidates == 2
    access.budget.maximum_bytes = 100
    access.budget.maximum_work = access.budget.work + 1
    assert capture(access).diagnostics == ("work_limit",)
    assert access.budget.read_bytes == 5


def test_failed_read_charges_actual_consumption_before_classification(tmp_path, monkeypatch):
    access = publication(tmp_path, {"README.md": b"12345"})
    original = SourceStream.read

    def truncated(source, count):
        (access.tree / "README.md").write_bytes(b"12")
        return original(source, count)

    monkeypatch.setattr(SourceStream, "read", truncated)
    card = capture(access)
    assert card.diagnostics == ("source_changed",)
    assert card.markdown is None
    assert access.budget.read_bytes == 2


def test_suppression_budget_precedes_registry_scan_and_leaves_registry_intact():
    register_secret("registered-secret")
    try:
        budget = ExtractionBudget(maximum_work=2)
        with pytest.raises(ExtractionError, match="work_limit"):
            contains_secret("long safe source", charge=budget.step)
        assert contains_secret("REGISTERED-SECRET", charge=lambda _count: None)
        assert not contains_secret("https://x/" * 10000, charge=lambda _count: None)
        assert contains_secret("https://x/?signature=abc", charge=lambda _count: None)
    finally:
        clear_registered_secrets()


def test_captured_presentation_revalidates_without_removing_leading_horizontal_rule(tmp_path):
    raw = b"---\nlanguage: en\n---\n---\n# Body\n![x](image.png)\n[guide]: ./guide.md\n"
    access = publication(tmp_path, {"README.md": raw})
    card = capture(access)
    assert card.markdown == "---\n# Body\n\\[image omitted\\]\n[guide]: ./guide.md\n"
    assert card.markdown is not None
    before = card.to_payload()
    validate_card_presentation(card.markdown, access.budget)
    assert card.to_payload() == before
    assert (access.tree / "README.md").read_bytes() == raw


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        ("<details>raw HTML</details>", "unsupported_markdown"),
        ("{mdx()}", "unsupported_markdown"),
        ("![raw asset](https://example.invalid)", "unsafe_content"),
        ("[bad](javascript:alert)", "unsafe_content"),
        ("[guide]: //example.invalid", "unsupported_markdown"),
        ("hf_12345678", "secret_suppressed"),
        ("```\nBearer opaque-secret\n```", "secret_suppressed"),
    ],
)
def test_present_card_validator_refuses_content_without_repair(body, reason):
    with pytest.raises(ExtractionError, match=reason):
        validate_card_presentation(body, ExtractionBudget())


def test_present_card_validator_uses_caller_budget_and_current_secret_registry():
    budget = ExtractionBudget(maximum_work=30)
    validate_card_presentation("safe", budget)
    spent = budget.work
    with pytest.raises(ExtractionError, match="work_limit"):
        validate_card_presentation("safe", budget)
    assert budget.work > spent
    register_secret("newly-registered")
    try:
        with pytest.raises(ExtractionError, match="secret_suppressed"):
            validate_card_presentation("NEWLY-REGISTERED", ExtractionBudget())
    finally:
        clear_registered_secrets()


@pytest.mark.parametrize("following", ["(javascript:alert)", "[target]"])
def test_asset_placeholder_cannot_activate_adjacent_link_syntax(tmp_path, following):
    raw = ("![alt][image]" + following + "\n[target]: ./safe.md\n").encode()
    access = publication(tmp_path, {"README.md": raw})
    card = capture(access)
    assert card.state == "present"
    assert card.markdown == "\\[image omitted\\]" + following + "\n[target]: ./safe.md\n"
    assert card.markdown is not None
    validate_card_presentation(card.markdown, access.budget)
