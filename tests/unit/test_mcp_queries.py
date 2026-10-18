"""Content-bound read pages never silently mix metadata or publication identity."""

import base64

import pytest

from hfcache.errors import Problem, RequestError
from hfcache.redaction import register_secret
from hfcache.services.context import ExecutionContext, ServiceResult
from hfcache.services.mcp_queries import MetadataReadQueries
from tests.fixtures import examples
from tests.unit.test_queries import _publication
from tests.unit.test_queries import queries as base_queries  # noqa: F401 - fixture


@pytest.fixture
def backend(request):
    queries = request.getfixturevalue("base_queries")
    _publication(queries)
    return MetadataReadQueries(queries, fingerprint="a" * 64, max_page_size=1)


def test_omitted_limit_walks_complete_configured_empty_and_unmanaged_metadata(backend):
    expected = backend.queries.archive_status().data
    rows, cursor = [], None
    while True:
        page = backend.get_archive_status(cursor=cursor)
        assert len(page.result.data["repositories"]) == 1
        assert page.result.data["archive"]["archive_id"] == expected["archive"]["archive_id"]
        rows.extend(page.result.data["repositories"])
        cursor = page.next_cursor
        if cursor is None:
            break
    assert rows == expected["repositories"]
    assert [row["managed"] for row in rows] == [True, True, False]
    assert rows[0]["current_commit_sha"] is None


@pytest.mark.parametrize("limit", [True, False, 0, -1, 2, 10001, 1.5, "1"])
def test_server_page_cap_rejects_coercions_and_explicit_excess(backend, limit):
    with pytest.raises(RequestError) as error:
        backend.get_archive_status(limit=limit)
    assert error.value.problems[0].code == "HFAPI006"


@pytest.mark.parametrize("cursor", ["", "?", "x" * 257, "é", b"not-text"])
def test_cursor_grammar_is_bounded_and_classified(backend, cursor):
    with pytest.raises(RequestError) as error:
        backend.get_archive_status(cursor=cursor)
    assert error.value.problems[0].code == "HFAPI006"


def test_cursor_cannot_cross_tool_scope_or_installed_policy(backend):
    cursor = backend.get_archive_status().next_cursor
    for changed in (
        lambda: backend.list_repositories(cursor=cursor),
        lambda: backend.get_archive_status(repository_type="model", cursor=cursor),
        lambda: MetadataReadQueries(
            backend.queries, fingerprint="b" * 64, max_page_size=1
        ).get_archive_status(cursor=cursor),
    ):
        with pytest.raises(RequestError) as error:
            changed()
        assert error.value.problems[0].code == "HFAPI007"
    assert cursor is not None
    scope = base64.urlsafe_b64decode(cursor).decode().split(":")[0]
    past_end = base64.urlsafe_b64encode(f"{scope}:999".encode()).decode()
    with pytest.raises(RequestError) as error:
        backend.get_archive_status(cursor=past_end)
    assert error.value.problems[0].code == "HFAPI007"


def test_selector_sha_order_and_duplicates_preserve_normalized_repository_scope(backend):
    selectors = ["model:zeta/configured-first", examples.reference().identity.selector]
    first = backend.get_archive_status(selectors=selectors)
    assert first.next_cursor is not None
    equivalent = [f"{selector}@{'b' * 40}" for selector in reversed(selectors)]
    equivalent.append(equivalent[0])
    following = backend.get_archive_status(selectors=equivalent, cursor=first.next_cursor)
    assert following.next_cursor is None
    assert first.result.data["repositories"][0]["managed"] is True
    assert following.result.data["repositories"][0]["managed"] is False


def test_manifest_cursor_binds_unreturned_header_and_other_collection(backend):
    manifest = examples.manifest()
    arguments = {
        "repository_type": manifest.repository_type,
        "repository_id": manifest.repository_id,
        "commit_sha": manifest.commit_sha,
        "publication_id": manifest.publication_id,
    }
    first = backend.get_revision_manifest(**arguments)
    assert first.next_cursor is not None
    header = first.result.data["manifest"]
    assert "files" not in header
    assert "dependencies" not in header
    assert header["file_count"] == manifest.file_count
    path = backend.queries.layout.repository(manifest.identity).manifest(
        manifest.commit_sha, manifest.publication_id
    )
    changed_header = manifest.model_copy(update={"hub_endpoint": "https://changed.example"})
    path.write_text(changed_header.to_json())
    with pytest.raises(RequestError) as error:
        backend.get_revision_manifest(**arguments, cursor=first.next_cursor)
    assert error.value.problems[0].code == "HFAPI007"
    changed_collection = manifest.model_copy(update={"dependencies": ()})
    path.write_text(changed_collection.to_json())
    with pytest.raises(RequestError) as error:
        backend.get_revision_manifest(**arguments, cursor=first.next_cursor)
    assert error.value.problems[0].code == "HFAPI007"


def test_live_status_headlines_do_not_break_rows_or_lose_nested_warnings(backend, monkeypatch):
    original = backend.queries.archive_status()
    warning = Problem(
        code="HFWRN001", message="preserved evidence", context={"nested": {"rows": ["one"]}}
    )
    observed = 0

    def reading(*_args):
        nonlocal observed
        observed += 1
        data = original.data
        data["archive"]["available_bytes"] = observed
        return ServiceResult(original.command, data, warnings=(warning,))

    monkeypatch.setattr(type(backend.queries), "archive_status", reading)
    first = backend.get_archive_status()
    following = backend.get_archive_status(cursor=first.next_cursor)
    assert first.result.data["archive"]["available_bytes"] == 1
    assert following.result.data["archive"]["available_bytes"] == 2
    for page in (first, following):
        rendered = page.result.envelope(ExecutionContext.create()).model_dump(mode="json")
        assert rendered["outcome"] == "success_with_warnings"
        assert rendered["warnings"][0]["context"] == {"nested": {"rows": ["one"]}}


def test_cursor_binds_visible_metadata_without_fingerprinting_registered_secrets(backend):
    manifest = examples.manifest()
    arguments = {
        "repository_type": manifest.repository_type,
        "repository_id": manifest.repository_id,
        "commit_sha": manifest.commit_sha,
        "publication_id": manifest.publication_id,
    }
    path = backend.queries.layout.repository(manifest.identity).manifest(
        manifest.commit_sha, manifest.publication_id
    )
    first_secret, second_secret = "private-" + "x" * 40, "private-" + "y" * 40
    for secret in (first_secret, second_secret):
        register_secret(secret)
    path.write_text(manifest.model_copy(update={"hub_endpoint": first_secret}).to_json())
    first = backend.get_revision_manifest(**arguments)
    path.write_text(manifest.model_copy(update={"hub_endpoint": second_secret}).to_json())
    following = backend.get_revision_manifest(**arguments, cursor=first.next_cursor)
    assert first.next_cursor is not None
    assert following.next_cursor is None
