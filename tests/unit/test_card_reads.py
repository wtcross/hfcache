"""CARD07-09: exact retained, bounded, authenticated metadata-only card reads."""

import asyncio
import base64
import errno
import fcntl
import hashlib
import json
import os
import socket

import httpx
import pytest
from pydantic import ValidationError

from hfcache.api.app import create_app
from hfcache.api.basic import create_administrator_record
from hfcache.card_models import RepositoryCardRead
from hfcache.catalog_capture import CatalogCapture
from hfcache.catalog_extractors import SourceAccess
from hfcache.catalog_models import MAXIMUM_CARD_PRESENTATION_BYTES, RepositoryCard
from hfcache.errors import IntegrityError, RequestError
from hfcache.hub import HubClient
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity
from hfcache.metadata import MetadataReader, QueryBounds, QueryLimitError
from hfcache.models import dump
from hfcache.redaction import clear_registered_secrets, register_secret
from hfcache.server_config import validate_server_config_mapping
from hfcache.services import card_queries
from hfcache.services.queries import LocalQueries, PublicationQuery
from tests.fixtures import examples
from tests.unit import test_api_reads as reads

configured = reads.configured
isolate_logging = reads.isolate_logging
STEM = "/api/v1/repositories/model/" + examples.REPOSITORY_ID
ROUTE = STEM + f"/publications/{examples.SHA}/{examples.PUBLICATION}/card"


def presentation(state="present", *, markdown="# A safe archived card\n"):
    payload = examples.repository_card().to_payload()
    if state == "not_captured":
        payload.update(state=state, captured_at=None, presentation_version=None, diagnostics=[])
    elif state != "absent":
        payload.update(
            state=state,
            source_path="README.md",
            expected_source_sha256=examples.DIGEST,
            diagnostics=[],
        )
        if state == "present":
            payload.update(
                markdown=markdown,
                presentation_sha256=hashlib.sha256(markdown.encode()).hexdigest(),
            )
    return payload


def published(policy, *, state="present", markdown="# A safe archived card\n", readme=True):
    queries = reads.publish(policy)
    reads.write_model(queries.layout.sentinel, examples.sentinel())
    request = PublicationQuery(
        RepositoryIdentity.of("model", examples.REPOSITORY_ID),
        CommitSha(examples.SHA),
        PublicationId(examples.PUBLICATION),
    )
    repository = queries.layout.repository(request.identity)
    manifest = examples.manifest()
    if readme:
        raw = manifest.to_payload()
        source = dict(raw["files"][0], path="README.md")
        raw["files"] = [source, *raw["files"]]
        raw["file_count"] += 1
        raw["total_bytes"] += source["size"]
        manifest = type(manifest).model_validate(raw)
    reads.write_model(repository.manifest(request.commit_sha, request.publication_id), manifest)
    path = repository.card(request.commit_sha, request.publication_id)
    if state != "not_captured":
        payload = presentation(state, markdown=markdown)
        payload["manifest_digest"] = hashlib.sha256(dump(manifest)).hexdigest()
        reads.write_model(path, RepositoryCard.model_validate(payload))
    return queries, request, manifest, path


def snapshot(root):
    return {
        str(path.relative_to(root)): (
            path.read_bytes(),
            tuple(
                getattr(path.stat(), field)
                for field in (
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
            ),
        )
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize(
    "state", ["present", "absent", "unsupported", "oversize", "unsafe", "failed", "not_captured"]
)
def test_read_projection_has_independent_coherent_states(state):
    model = RepositoryCardRead.model_validate(presentation(state))
    assert model.state == state
    assert RepositoryCardRead.model_validate_json(dump(model)) == model


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": True},
        {"schema_version": 2},
        {"kind": "repository_card_read"},
        {"captured_at": None},
        {"presentation_version": None},
        {"markdown": None},
        {"presentation_sha256": None},
        {"source_path": None},
        {"expected_source_sha256": None},
        {"source_path": "nested/README.md"},
        {"diagnostics": ["work_limit", "work_limit"]},
        {"diagnostics": ["work_limit", "read_failed"]},
        {"raw_source": "forbidden"},
    ],
)
def test_read_projection_refuses_unknown_coercive_or_mixed_fields(change):
    with pytest.raises(ValidationError):
        RepositoryCardRead.model_validate(presentation() | change)


@pytest.mark.parametrize(
    "field",
    ["captured_at", "presentation_version", "markdown", "presentation_sha256", "diagnostics"],
)
def test_not_captured_cannot_invent_capture_metadata(field):
    value = presentation("not_captured")
    present = presentation()
    value[field] = ["read_failed"] if field == "diagnostics" else present[field]
    with pytest.raises(ValidationError):
        RepositoryCardRead.model_validate(value)


def test_read_projection_bounds_utf8_and_json_expansion_separately():
    for text in (
        "x" * MAXIMUM_CARD_PRESENTATION_BYTES,
        "é" * (MAXIMUM_CARD_PRESENTATION_BYTES // 2),
    ):
        with pytest.raises(ValidationError):
            RepositoryCardRead.model_validate(presentation(markdown=text))
    assert RepositoryCardRead.model_validate(presentation(markdown="")).markdown == ""


@pytest.mark.parametrize(
    ("state", "change"),
    [
        ("present", {"source_path": None, "expected_source_sha256": None}),
        ("absent", {"source_path": "README.md", "expected_source_sha256": examples.DIGEST}),
        ("unsafe", {"markdown": "Withheld text"}),
        ("failed", {"presentation_sha256": examples.DIGEST}),
    ],
)
def test_stored_states_cannot_mix_source_or_withheld_presentation(state, change):
    with pytest.raises(ValidationError):
        RepositoryCardRead.model_validate(presentation(state) | change)


@pytest.mark.parametrize("readme", [False, True])
def test_missing_capture_keeps_only_authoritative_source_identity(configured, readme):
    _, policy, _, _ = configured
    queries, request, manifest, _ = published(policy, state="not_captured", readme=readme)
    before = snapshot(queries.layout.root)
    result = queries.read_card(request)
    assert result.state == "not_captured"
    assert result.source_path == ("README.md" if readme else None)
    assert result.expected_source_sha256 == (examples.DIGEST if readme else None)
    assert result.manifest_digest == hashlib.sha256(dump(manifest)).hexdigest()
    assert (
        result.captured_at
        is result.presentation_version
        is result.markdown
        is result.presentation_sha256
        is None
    )
    assert result.diagnostics == ()
    assert snapshot(queries.layout.root) == before


def test_exact_read_ignores_current_but_refuses_repaired_away_even_if_replacement_missing(
    configured,
):
    _, policy, _, _ = configured
    queries, request, _, path = published(policy)
    repository = queries.layout.repository(request.identity)
    repository.current_ref.unlink()
    assert queries.read_card(request).state == "present"
    changed = examples.reference().model_copy(
        update={
            "publication_id": examples.REPLACEMENT,
            "tree": str(
                repository.tree_reference(request.commit_sha, PublicationId(examples.REPLACEMENT))
            ),
            "manifest": str(
                repository.manifest_reference(
                    request.commit_sha, PublicationId(examples.REPLACEMENT)
                )
            ),
        }
    )
    reads.write_model(repository.revision_ref(request.commit_sha), changed)
    before = path.read_bytes()
    with pytest.raises(RequestError) as failure:
        queries.read_card(request)
    assert failure.value.status_code == 404
    assert path.read_bytes() == before


@pytest.mark.parametrize("missing", ["reference", "manifest", "tree"])
def test_retained_authorization_precedes_orphan_adjunct(configured, missing):
    _, policy, _, _ = configured
    queries, request, _, card_path = published(policy)
    repository = queries.layout.repository(request.identity)
    if missing == "reference":
        repository.revision_ref(request.commit_sha).unlink()
    elif missing == "manifest":
        repository.manifest(request.commit_sha, request.publication_id).unlink()
    else:
        repository.instance(request.commit_sha, request.publication_id).rmdir()
    original = card_path.read_bytes()
    with pytest.raises(RequestError) as failure:
        queries.read_card(request)
    assert failure.value.status_code == 404
    assert card_path.read_bytes() == original


@pytest.mark.parametrize("corrupt", ["repository", "locator", "generation", "tree-file"])
def test_corrupt_retention_authority_refuses_before_adjunct_read(configured, monkeypatch, corrupt):
    _, policy, _, _ = configured
    queries, request, manifest, _ = published(policy)
    repository = queries.layout.repository(request.identity)
    reference = examples.reference()
    if corrupt == "repository":
        reads.write_model(
            repository.revision_ref(request.commit_sha),
            reference.model_copy(update={"repository_id": "other/model"}),
        )
    elif corrupt == "locator":
        reads.write_model(
            repository.revision_ref(request.commit_sha),
            reference.model_copy(update={"tree": examples.REFERENCE_TREE + "-other"}),
        )
    elif corrupt == "generation":
        reads.write_model(
            repository.manifest(request.commit_sha, request.publication_id),
            manifest.model_copy(
                update={"publication_generation": manifest.publication_generation + 1}
            ),
        )
    else:
        tree = repository.instance(request.commit_sha, request.publication_id)
        tree.rmdir()
        tree.write_bytes(b"A regular file cannot authorize a publication tree")

    def forbidden(*args, **options):
        pytest.fail("Corrupt authority must refuse before reading an adjunct")

    monkeypatch.setattr(card_queries, "read_repository_card", forbidden)
    before = snapshot(queries.layout.root)
    with pytest.raises(IntegrityError) as failure:
        queries.read_card(request)
    assert failure.value.problems[0].code == (
        "HFVER008" if corrupt in {"repository", "locator"} else "HFVER007"
    )
    assert snapshot(queries.layout.root) == before


@pytest.mark.parametrize("change", ["prune", "repair", "manifest"])
def test_authority_rejoin_rejects_races_after_adjunct_read(configured, monkeypatch, change):
    _, policy, _, _ = configured
    queries, request, manifest, _ = published(policy)
    repository = queries.layout.repository(request.identity)
    original = card_queries.read_repository_card

    def raced(*args, **options):
        value = original(*args, **options)
        if change == "prune":
            repository.revision_ref(request.commit_sha).unlink()
        elif change == "repair":
            reads.write_model(
                repository.revision_ref(request.commit_sha),
                examples.reference().model_copy(
                    update={
                        "publication_id": examples.REPLACEMENT,
                        "tree": str(
                            repository.tree_reference(
                                request.commit_sha, PublicationId(examples.REPLACEMENT)
                            )
                        ),
                        "manifest": str(
                            repository.manifest_reference(
                                request.commit_sha, PublicationId(examples.REPLACEMENT)
                            )
                        ),
                    }
                ),
            )
        else:
            reads.write_model(
                repository.manifest(request.commit_sha, request.publication_id),
                manifest.model_copy(update={"application_version": "9.9.9"}),
            )
        return value

    monkeypatch.setattr(card_queries, "read_repository_card", raced)
    with pytest.raises(IntegrityError if change == "manifest" else RequestError) as failure:
        queries.read_card(request)
    if change != "manifest":
        assert isinstance(failure.value, RequestError)
        assert failure.value.status_code == 404


def test_tree_metadata_descriptor_has_no_directory_content_capability(configured):
    _, policy, _, _ = configured
    queries, request, _, _ = published(policy)
    path = queries.layout.repository(request.identity).instance(
        request.commit_sha, request.publication_id
    )
    descriptor = MetadataReader(queries.layout.root).open(path, directory=True, metadata_only=True)
    try:
        assert fcntl.fcntl(descriptor, fcntl.F_GETFL) & os.O_PATH
        with pytest.raises(OSError, match="Bad file descriptor") as failure:
            os.listdir(descriptor)  # noqa: PTH208 - exercise this exact metadata-only FD
        assert failure.value.errno == errno.EBADF
    finally:
        os.close(descriptor)


@pytest.mark.parametrize(
    "state", ["present", "absent", "unsupported", "oversize", "unsafe", "failed", "not_captured"]
)
def test_authenticated_get_returns_flat_projection_and_security_headers(configured, state):
    data, policy, _, lock = configured
    _, _, _, _ = published(policy, state=state, readme=state != "absent")
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def read(client):
        for token in (reads.READER, reads.WRITER):
            response = await client.get(ROUTE, headers={"authorization": "Bearer " + token})
            assert response.status_code == 200
            body = response.json()
            assert body["envelope"]["command"] == "card read"
            result = RepositoryCardRead.model_validate(body["envelope"]["data"])
            assert result.state == state
            assert result.archive_id == body["archive_id"] == examples.ARCHIVE_ID
            assert result.publication_id == examples.PUBLICATION
            assert response.headers["cache-control"] == "no-store"
            assert response.headers["x-content-type-options"] == "nosniff"
            assert app.state.pool.inflight == 0

    asyncio.run(reads.client_context(app, read))


@pytest.mark.parametrize("corrupt", ["version", "digest", "identity", "unsafe", "symlink"])
def test_invalid_adjunct_is_classified_without_fallback_or_private_values(configured, corrupt):
    data, policy, _, lock = configured
    _, _, _, path = published(policy)
    payload = json.loads(path.read_bytes())
    if corrupt == "version":
        payload["schema_version"] = 2
    elif corrupt == "digest":
        payload["presentation_sha256"] = "0" * 64
    elif corrupt == "identity":
        payload["publication_id"] = examples.REPLACEMENT
    elif corrupt == "unsafe":
        payload["markdown"] = "<script>private-rejected-content</script>"
        payload["presentation_sha256"] = hashlib.sha256(payload["markdown"].encode()).hexdigest()
    else:
        path.unlink()
        path.symlink_to(path.with_name("never-open"))
    if corrupt != "symlink":
        path.write_text(json.dumps(payload))
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def read(client):
        response = await client.get(ROUTE)
        assert response.status_code == 409
        assert response.json()["code"] == "HFVER007"
        assert "private-rejected-content" not in response.text
        assert app.state.pool.inflight == 0

    asyncio.run(reads.client_context(app, read))


def test_basic_allowed_and_mcp_credential_denied_before_metadata_work(configured, tmp_path):
    data, policy, _, lock = configured
    published(policy)
    password = b"owned-card-test-password-0123456789"
    record = create_administrator_record("owned-card", "administrator", password)
    account = tmp_path / "administrator.json"
    account.write_text(record.model_dump_json())
    account.chmod(0o600)
    mcp = tmp_path / "mcp"
    mcp.write_text("owned-card-mcp-" + "M" * 40)
    mcp.chmod(0o600)
    data["credentials"]["mcp_reader"] = {"file": str(mcp)}
    data["mcp_enabled"] = True
    data["basic"] = {"origin": "https://testserver", "administrator": {"file": str(account)}}
    data["listener"]["allowed_origins"] = ["https://testserver"]
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def read(client):
        basic = "Basic " + base64.b64encode(b"administrator:" + password).decode()
        response = await client.get(ROUTE, headers={"authorization": basic})
        assert response.status_code == 200
        denied = await client.get(ROUTE, headers={"authorization": "Bearer " + mcp.read_text()})
        assert denied.status_code == 401
        assert (
            app.state.credentials.authenticate(
                "Bearer " + mcp.read_text(), interface="mcp"
            ).credential_class.value
            == "mcp-reader"
        )
        assert app.state.pool.inflight == 0

    asyncio.run(reads.client_context(app, read))


def test_sanitization_race_refuses_changed_markdown_and_stale_digest(configured, monkeypatch):
    data, policy, _, lock = configured
    published(policy, markdown="Late-registered-owned-card-value")
    original = LocalQueries.read_card

    def changed(self, request):
        value = original(self, request)
        register_secret("Late-registered-owned-card-value")
        return value

    monkeypatch.setattr(LocalQueries, "read_card", changed)
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def read(client):
        response = await client.get(ROUTE)
        assert response.status_code == 409
        assert response.json()["code"] == "HFVER007"
        assert "Late-registered-owned-card-value" not in response.text

    try:
        asyncio.run(reads.client_context(app, read))
    finally:
        clear_registered_secrets()


def test_card_encoding_expansion_refuses_before_success_headers(configured):
    data, policy, _, lock = configured
    published(policy, markdown="\n" * (MAXIMUM_CARD_PRESENTATION_BYTES // 2 - 1))
    data["limits"] = {"max_response_bytes": MAXIMUM_CARD_PRESENTATION_BYTES}
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def read(client):
        response = await client.get(ROUTE)
        assert response.status_code == 413
        assert "envelope" not in response.json()
        assert app.state.pool.inflight == 0

    asyncio.run(reads.client_context(app, read))


def test_configured_metadata_budget_is_not_bypassed_by_card_read(configured):
    _, policy, _, _ = configured
    queries, request, _, _ = published(policy)
    bounded = LocalQueries(queries.config, bounds=QueryBounds(maximum_total_bytes=1))
    with pytest.raises(QueryLimitError):
        bounded.read_card(request)


@pytest.mark.parametrize(
    "suffix",
    ["?file=README.md", "?source=https://example.invalid", "?limit=1", "?state=present"],
)
def test_card_query_and_body_refuse_before_metadata_work(configured, monkeypatch, suffix):
    data, _, _, lock = configured

    def forbidden(*args, **options):
        pytest.fail("invalid read acquired a metadata capability")

    monkeypatch.setattr(LocalQueries, "read_card", forbidden)
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def read(client):
        assert (await client.get(ROUTE + suffix)).status_code == 422
        assert (await client.request("GET", ROUTE, content=b"{}")).status_code == 422
        assert app.state.pool.inflight == 0

    asyncio.run(reads.client_context(app, read))


@pytest.mark.parametrize(
    "route",
    [
        ROUTE.replace("/model/", "/models/", 1),
        ROUTE.replace(examples.SHA, examples.SHA.upper()),
        ROUTE.replace(examples.SHA, "f" * 39),
        ROUTE.replace(examples.PUBLICATION, "f" * 31),
        ROUTE.replace("/organization/", "/organization%2Fother/"),
    ],
)
def test_card_identity_grammar_never_opens_archive_on_refusal(configured, monkeypatch, route):
    data, _, _, lock = configured

    def forbidden(*args, **options):
        pytest.fail("malformed identity acquired archive metadata")

    monkeypatch.setattr(LocalQueries, "read_card", forbidden)
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def read(client):
        assert (await client.get(route)).status_code in {400, 404, 422}

    asyncio.run(reads.client_context(app, read))


def test_real_card_get_has_only_metadata_capability_and_no_capture_network_or_lock(
    configured, monkeypatch
):
    data, policy, _, lock = configured
    queries, request, _, path = published(policy)
    repository = queries.layout.repository(request.identity)
    tree = repository.instance(request.commit_sha, request.publication_id)
    (tree / "README.md").write_text("payload must not be opened by GET")
    allowed = {
        queries.layout.sentinel,
        repository.revision_ref(request.commit_sha),
        repository.manifest(request.commit_sha, request.publication_id),
        path,
        tree,
    }
    before = snapshot(queries.layout.root)
    original = MetadataReader.open
    opened = []

    def metadata_only(self, path, **options):
        assert path in allowed
        if path == tree:
            assert options == {"directory": True, "metadata_only": True}
        opened.append(path)
        return original(self, path, **options)

    def forbidden(*args, **options):
        pytest.fail("GET reached a writer, loader, network or archive lock")

    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def read(client):
        with monkeypatch.context() as patch:
            patch.setattr(MetadataReader, "open", metadata_only)
            patch.setattr(SourceAccess, "__init__", forbidden)
            patch.setattr(CatalogCapture, "__init__", forbidden)
            patch.setattr(HubClient, "of", forbidden)
            patch.setattr("hfcache.credentials.resolve_token", forbidden)
            patch.setattr("hfcache.locking.exclusive_lock", forbidden)
            patch.setattr(socket, "socket", forbidden)
            response = await client.get(ROUTE)
            assert response.status_code == 200
        assert set(opened) == allowed

    asyncio.run(reads.client_context(app, read))
    assert snapshot(queries.layout.root) == before


@pytest.mark.parametrize("disconnect", [False, True])
def test_card_metadata_lease_lives_through_slow_send_and_disconnect(configured, disconnect):
    data, policy, _, lock = configured
    published(policy)
    data["limits"] = {"metadata_workers": 1, "metadata_queue": 1}
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def exercise():
        async with app.router.lifespan_context(app):
            sending, release = asyncio.Event(), asyncio.Event()
            messages = []

            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}

            async def send(message):
                messages.append(message)
                if message["type"] == "http.response.body":
                    if sum(row["type"] == "http.response.body" for row in messages) == 2:
                        sending.set()
                    await release.wait()

            scope = {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": ROUTE,
                "raw_path": ROUTE.encode(),
                "root_path": "",
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 19000),
                "headers": [
                    (b"host", b"testserver"),
                    (b"authorization", ("Bearer " + reads.READER).encode()),
                ],
            }
            original_requests = [
                asyncio.create_task(app(dict(scope), receive, send)) for _ in range(2)
            ]
            try:
                await asyncio.wait_for(sending.wait(), 3)
                assert messages[0]["status"] == 200
                assert app.state.pool.inflight == 2
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app),
                    base_url="http://testserver",
                    headers=reads.HEADERS,
                ) as client:
                    assert (await client.get(ROUTE)).status_code == 503
                if disconnect:
                    for request in original_requests:
                        request.cancel()
                    for request in original_requests:
                        with pytest.raises(asyncio.CancelledError):
                            await request
                else:
                    release.set()
                    await asyncio.gather(*original_requests)
                assert app.state.pool.inflight == 0
            finally:
                release.set()
                for request in original_requests:
                    if not request.done():
                        request.cancel()
                await asyncio.gather(*original_requests, return_exceptions=True)

    asyncio.run(exercise())
    assert app.state.pool.closed


@pytest.mark.parametrize("state", ["present", "not_captured"])
@pytest.mark.parametrize("change", ["missing", "mismatch", "malformed"])
def test_archive_sentinel_must_authorize_even_a_missing_capture(configured, state, change):
    _, policy, _, _ = configured
    queries, request, _, _ = published(policy, state=state)
    if change == "missing":
        queries.layout.sentinel.unlink()
    elif change == "mismatch":
        reads.write_model(
            queries.layout.sentinel,
            examples.sentinel().model_copy(
                update={"archive_id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"}
            ),
        )
    else:
        queries.layout.sentinel.write_bytes(b"malformed sentinel")
    with pytest.raises(IntegrityError) as failure:
        queries.read_card(request)
    assert failure.value.problems[0].code == "HFVER007"


def test_archive_identity_is_rejoined_after_adjunct_read(configured, monkeypatch):
    _, policy, _, _ = configured
    queries, request, _, _ = published(policy)
    original = card_queries.read_repository_card

    def replaced(*args, **options):
        result = original(*args, **options)
        reads.write_model(
            queries.layout.sentinel,
            examples.sentinel().model_copy(
                update={"archive_id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"}
            ),
        )
        return result

    monkeypatch.setattr(card_queries, "read_repository_card", replaced)
    with pytest.raises(IntegrityError) as failure:
        queries.read_card(request)
    assert failure.value.problems[0].code == "HFVER007"
