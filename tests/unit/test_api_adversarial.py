"""Every HTTP surface authenticates and bounds hostile input (INV-013, API-006)."""

import re
import warnings

import pytest
from starlette.exceptions import StarletteDeprecationWarning

# Starlette 1.8 supports the selected HTTPX 0.28 transport while deprecating
# its TestClient preference; this known test-only compatibility warning is scoped.
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message=re.escape(
            "Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead."
        ),
        category=StarletteDeprecationWarning,
    )
    from fastapi.testclient import TestClient

from hfcache.api.app import create_app
from hfcache.archive import inspect_archive
from hfcache.logging import reset
from hfcache.metadata import MetadataReader, QueryBounds, QueryLimitError
from hfcache.paths import ArchiveLayout
from hfcache.server_config import validate_server_config_mapping
from hfcache.storage import parse_mount_table
from tests.fixtures.examples import sentinel

WRITER = "writer_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
READER = "reader_9876543210zyxwvutsrqponmlkjihgfedcbaZYXWVU"
MCP = "mcp_reader_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabc"
ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"


@pytest.fixture(autouse=True)
def _isolate_daemon_logging():
    reset()
    yield
    reset()


def _server_settings(tmp_path):
    archive = tmp_path / "archive"
    policy = tmp_path / "archive.toml"
    policy.write_text(
        f'schema_version=1\n[storage]\narchive_root="{archive}"\narchive_id="{ARCHIVE_ID}"\n'
    )
    credentials = {}
    for name, token in (("writer", WRITER), ("reader", READER), ("mcp_reader", MCP)):
        path = tmp_path / name
        path.write_text(token + "\n", encoding="ascii")
        path.chmod(0o600)
        credentials[name] = {"file": str(path)}
    server = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(policy),
            "state_directory": str(tmp_path / "api-state"),
            "credentials": credentials,
            "interactive_docs": True,
            "listener": {"allowed_hosts": ["testserver"]},
            "limits": {"max_request_bytes": 1024},
        }
    )
    return server, archive


@pytest.fixture
def http_archive(tmp_path):
    server, archive = _server_settings(tmp_path)
    app = create_app(server, instance_lock_path=tmp_path / "daemon.lock")
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, archive


@pytest.mark.parametrize(
    "route",
    [
        "/api/v1/version",
        "/api/v1/capabilities",
        "/api/v1/health",
        "/api/v1/status",
        "/api/v1/repositories",
        "/api/v1/repositories/revisions",
        "/api/v1/verification/estimate",
        "/api/v1/archive/inspection",
        "/api/v1/runs",
        "/api/v1/runs/" + "0" * 32,
        "/api/v1/not-a-resource",
        "/openapi.json",
        "/docs",
        "/redoc",
    ],
)
def test_all_get_surfaces_authenticate_before_route_or_archive_inspection(http_archive, route):
    client, archive = http_archive

    response = client.get(route)

    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Bearer")
    assert not archive.exists()


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def test_unknown_methods_and_paths_have_no_anonymous_error_surface(http_archive, method):
    client, archive = http_archive

    response = client.request(method, "/api/v1/not-a-resource")

    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Bearer")
    assert not archive.exists()


@pytest.mark.parametrize(
    "header",
    [
        "",
        "Basic unrelated",
        "Bearer unknown_" + "a" * 40,
        "Bearer " + MCP,
        "Bearer  " + READER,
        "Bearer " + READER + " ",
        "Bearer " + "a" * 5000,
    ],
    ids=["empty", "basic", "unknown", "mcp", "double-space", "trailing-space", "oversized"],
)
def test_malformed_or_wrong_interface_bearers_are_uniform_and_safe(http_archive, header):
    client, _ = http_archive

    response = client.get("/api/v1/version", headers={"Authorization": header})

    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Bearer")
    for token in (WRITER, READER, MCP):
        assert token not in response.text


def test_duplicate_authorization_cannot_select_the_writer(http_archive):
    client, _ = http_archive

    response = client.get(
        "/api/v1/version",
        headers=[("Authorization", f"Bearer {READER}"), ("Authorization", f"Bearer {WRITER}")],
    )

    assert response.status_code == 401


def test_authenticated_missing_resource_has_sanitized_error_and_authoritative_request_id(
    http_archive,
):
    client, _ = http_archive
    selected_id = "caller-cannot-select-the-authoritative-request"
    response = client.get(
        "/api/v1/not-a-resource",
        headers={"Authorization": f"Bearer {READER}", "X-Request-ID": selected_id},
    )

    assert response.status_code == 404
    assert selected_id not in response.text
    assert response.headers.get("x-request-id") != selected_id
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["x-request-id"])
    for token in (WRITER, READER, MCP):
        assert token not in response.text


@pytest.mark.parametrize(
    "extra", [{"Host": "attacker.invalid"}, {"Origin": "https://attacker.invalid"}]
)
def test_authenticated_host_and_browser_origin_cannot_expand_server_exposure(http_archive, extra):
    client, _ = http_archive

    response = client.get("/api/v1/version", headers={"Authorization": f"Bearer {READER}"} | extra)

    assert response.status_code in {400, 403, 422}
    assert "attacker.invalid" not in response.text


def test_untrusted_forwarded_host_and_prefix_do_not_rewrite_a_normal_request(http_archive):
    client, _ = http_archive

    response = client.get(
        "/api/v1/version",
        headers={
            "Authorization": f"Bearer {READER}",
            "X-Forwarded-Host": "attacker.invalid",
            "X-Forwarded-Prefix": "/attacker",
            "X-Forwarded-Proto": "https",
        },
    )

    assert response.status_code == 200
    assert "attacker" not in response.text


@pytest.mark.parametrize("parameter", ["token", "access_token", "unknown"])
def test_query_secrets_are_rejected_without_echoing_unregistered_input(http_archive, parameter):
    client, _ = http_archive
    value = "unregistered-opaque-input-that-must-not-reach-diagnostics"

    response = client.get(
        "/api/v1/version",
        params={parameter: value},
        headers={"Authorization": f"Bearer {READER}"},
    )

    assert response.status_code == 422
    assert value not in response.text


def test_noncanonical_route_cannot_reflect_query_secrets_in_a_redirect(http_archive):
    client, _ = http_archive
    secret = "opaque-unregistered-secret-in-a-forbidden-query"

    response = client.get(
        "/api/v1/version/",
        params={"token": secret},
        headers={"Authorization": f"Bearer {READER}"},
        follow_redirects=False,
    )

    assert response.status_code in {404, 422}
    assert secret not in response.text
    assert secret not in str(response.headers)


@pytest.mark.parametrize("chunked", [False, True])
def test_oversized_body_refuses_even_when_the_route_does_not_consume_it(http_archive, chunked):
    client, _ = http_archive
    content = iter([b"x" * 1024, b"y"]) if chunked else b"x" * 1025

    response = client.request(
        "GET", "/api/v1/version", content=content, headers={"Authorization": f"Bearer {READER}"}
    )

    assert response.status_code == 413
    if chunked:
        assert "content-length" not in response.request.headers


def test_authentication_precedes_body_validation_and_sensitive_error_details(http_archive):
    client, archive = http_archive

    response = client.request("GET", "/api/v1/version", content=b"x" * 1025)

    assert response.status_code == 401
    assert not archive.exists()


@pytest.mark.parametrize("host", ["testserver:", "testserver:not-a-port", "testserver:1:2"])
def test_malformed_host_port_is_a_safe_transport_refusal(http_archive, host):
    client, _ = http_archive

    response = client.get(
        "/api/v1/version", headers={"Authorization": f"Bearer {READER}", "Host": host}
    )

    assert response.status_code == 400
    assert host not in response.text


@pytest.mark.parametrize(
    "query",
    [
        "limit=0",
        "limit=-1",
        "limit=true",
        "limit=1.0",
        "limit=%2B1",
        "limit=10001",
        "limit=1&limit=2",
        "cursor=x&cursor=y",
        "cursor=%%%",
        "type=invalid",
        "type=model&type=dataset",
        "unknown=opaque-unregistered-input",
        "&".join(["selector=x"] * 101),
    ],
    ids=[
        "zero",
        "negative",
        "bool",
        "decimal",
        "plus",
        "excess-limit",
        "duplicate-limit",
        "duplicate-cursor",
        "bad-cursor",
        "bad-type",
        "duplicate-type",
        "unknown",
        "excess-selectors",
    ],
)
def test_page_query_has_explicit_strict_bounded_conversion(http_archive, query):
    client, archive = http_archive

    response = client.get(
        "/api/v1/repositories?" + query, headers={"Authorization": f"Bearer {READER}"}
    )

    assert response.status_code == 422
    assert "opaque-unregistered-input" not in response.text
    assert not archive.exists()


def test_repeated_origin_cannot_choose_its_authorized_value(tmp_path):
    server, _ = _server_settings(tmp_path)
    server = server.model_copy(
        update={
            "listener": server.listener.model_copy(
                update={"allowed_origins": ("https://allowed.invalid",)}
            )
        }
    )
    app = create_app(server, instance_lock_path=tmp_path / "daemon.lock")
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(
            "/api/v1/version",
            headers=[
                ("Authorization", f"Bearer {READER}"),
                ("Origin", "https://attacker.invalid"),
                ("Origin", "https://allowed.invalid"),
            ],
        )

    assert response.status_code == 403
    assert "attacker.invalid" not in response.text


def test_configured_path_prefix_is_required_and_preserved_in_authenticated_schema(tmp_path):
    server, _ = _server_settings(tmp_path)
    server = server.model_copy(
        update={"listener": server.listener.model_copy(update={"root_path": "/management"})}
    )
    app = create_app(server, instance_lock_path=tmp_path / "daemon.lock")
    with TestClient(app, raise_server_exceptions=False) as client:
        headers = {"Authorization": f"Bearer {READER}"}
        assert client.get("/api/v1/version", headers=headers).status_code == 404
        response = client.get("/management/api/v1/openapi.json", headers=headers)

    assert response.status_code == 200
    assert any(server["url"] == "/management" for server in response.json()["servers"])


def test_authenticated_docs_and_schema_advertise_a_nonpersistent_bearer_flow(http_archive):
    client, _ = http_archive
    headers = {"Authorization": f"Bearer {READER}"}

    response = client.get("/api/v1/openapi.json", headers=headers)
    docs = client.get("/api/v1/docs", headers=headers)

    assert response.status_code == 200
    assert docs.status_code == 200
    schema = response.json()
    schemes = schema["components"]["securitySchemes"]
    bearer_names = {
        name
        for name, scheme in schemes.items()
        if scheme.get("type") == "http" and scheme.get("scheme") == "bearer"
    }
    assert bearer_names
    for path in schema["paths"].values():
        for operation in path.values():
            assert any(set(requirement) & bearer_names for requirement in operation["security"])
    assert '"persistAuthorization": false' in docs.text
    for token in (WRITER, READER, MCP):
        assert token not in response.text
        assert token not in docs.text


def test_schema_cannot_bypass_the_configured_normal_response_limit(tmp_path):
    server, _ = _server_settings(tmp_path)
    server = server.model_copy(
        update={"limits": server.limits.model_copy(update={"max_response_bytes": 1024})}
    )
    app = create_app(server, instance_lock_path=tmp_path / "daemon.lock")
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/openapi.json", headers={"Authorization": f"Bearer {READER}"})

    assert response.status_code == 413
    assert len(response.content) <= 1024


def test_unix_transport_remains_usable_alongside_a_trusted_tls_proxy(tmp_path):
    server, _ = _server_settings(tmp_path)
    server = server.model_copy(
        update={
            "listener": server.listener.model_copy(
                update={"proxy_tls": True, "trusted_proxies": ("127.0.0.1",)}
            )
        }
    )
    app = create_app(server, instance_lock_path=tmp_path / "daemon.lock")

    async def unix_scope(scope, receive, send):
        if scope["type"] == "http":
            scope = scope | {"client": None, "server": (str(server.listener.unix_socket), None)}
        await app(scope, receive, send)

    with TestClient(unix_scope, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/version", headers={"Authorization": f"Bearer {READER}"})

    assert response.status_code == 200


@pytest.mark.parametrize(
    "route",
    [
        "/api/v1/runs/invalid-run-id",
        "/api/v1/repositories/invalid/org/repo/references/current",
        "/api/v1/repositories/model/.invalid/repo/references/current",
        "/api/v1/repositories/model/org/.invalid/references/current",
        "/api/v1/repositories/model/org/repo/references/short-sha",
        "/api/v1/repositories/model/org/repo/manifests/short-sha/" + "0" * 32,
        "/api/v1/repositories/model/org/repo/manifests/" + "a" * 40 + "/invalid-publication-id",
        "/api/v1/repositories?selector=malformed-selector",
    ],
)
def test_invalid_structured_identifiers_are_request_errors_before_artifact_reads(
    http_archive, route
):
    client, archive = http_archive

    response = client.get(route, headers={"Authorization": f"Bearer {READER}"})

    assert response.status_code == 422
    assert not archive.exists()


def _nfs_table(root):
    return parse_mount_table(
        f"457 47 0:68 / {root} rw,nosuid,nodev,relatime shared:488 "
        "- nfs4 nas.invalid:/archive rw,vers=4.2\n"
    )


def test_inspection_scan_budget_is_visible_rather_than_a_truncated_success(tmp_path):
    root = tmp_path / "archive"
    root.mkdir()
    for index in range(11):
        (root / f"unknown-{index}").touch()
    layout = ArchiveLayout(root=root)

    with pytest.raises(QueryLimitError) as failure:
        inspect_archive(
            layout,
            archive_id=ARCHIVE_ID,
            table=_nfs_table(root),
            reader=MetadataReader(root, QueryBounds(maximum_entries=10)),
        )

    assert failure.value.problems[0].code == "HFAPI005"
    assert len(list(root.iterdir())) == 11


def test_http_inspection_budget_refusal_keeps_its_safety_classification(tmp_path, monkeypatch):
    server, root = _server_settings(tmp_path)
    root.mkdir()
    for index in range(11):
        (root / f"unknown-{index}").touch()
    server = server.model_copy(
        update={"limits": server.limits.model_copy(update={"max_scan_entries": 10})}
    )
    monkeypatch.setattr("hfcache.archive.read_mount_table", lambda: _nfs_table(root))
    app = create_app(server, instance_lock_path=tmp_path / "daemon.lock")
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(
            "/api/v1/archive/inspection", headers={"Authorization": f"Bearer {READER}"}
        )

    assert response.status_code == 503
    assert response.json()["code"] == "HFAPI005"
    assert response.json()["exit_code"] == 20
    assert len(list(root.iterdir())) == 11


def test_inspection_bounded_sentinel_read_refuses_an_oversized_artifact(tmp_path):
    root = tmp_path / "archive"
    root.mkdir()
    layout = ArchiveLayout(root=root)
    layout.sentinel.write_bytes(b"x" * 1025)

    with pytest.raises(QueryLimitError):
        inspect_archive(
            layout,
            archive_id=ARCHIVE_ID,
            table=_nfs_table(root),
            reader=MetadataReader(root, QueryBounds(maximum_artifact_bytes=1024)),
        )


def test_inspection_sentinel_swap_cannot_read_a_symlink_target(tmp_path):
    root = tmp_path / "archive"
    root.mkdir()
    layout = ArchiveLayout(root=root)
    layout.sentinel.write_text(sentinel().to_json(), encoding="utf-8")
    outside = tmp_path / "outside-sentinel"
    outside.write_text(sentinel().to_json(), encoding="utf-8")

    class SwapSentinel(MetadataReader):
        def read(self, path):
            assert path == layout.sentinel
            path.unlink()
            path.symlink_to(outside)
            return super().read(path)

    inspection = inspect_archive(
        layout, archive_id=ARCHIVE_ID, table=_nfs_table(root), reader=SwapSentinel(root)
    )

    assert inspection.state == "unusable"
    assert "HFMNT006" in {problem.code for problem in inspection.problems}
    assert layout.sentinel.is_symlink()


@pytest.mark.parametrize("mutation", ["malformed", "missing-after-scan"])
def test_inspection_diagnoses_corrupt_or_vanished_sentinel_without_repair(tmp_path, mutation):
    root = tmp_path / "archive"
    root.mkdir()
    layout = ArchiveLayout(root=root)
    layout.sentinel.write_text(sentinel().to_json(), encoding="utf-8")

    class ChangedSentinel(MetadataReader):
        def read(self, path):
            if mutation == "malformed":
                path.write_bytes(b"{malformed")
            else:
                path.unlink()
            return super().read(path)

    inspection = inspect_archive(
        layout, archive_id=ARCHIVE_ID, table=_nfs_table(root), reader=ChangedSentinel(root)
    )

    assert inspection.state == "unusable"
    assert inspection.sentinel is None
    assert "HFMNT006" in {problem.code for problem in inspection.problems}
    if mutation == "malformed":
        assert layout.sentinel.read_bytes() == b"{malformed"
    else:
        assert not layout.sentinel.exists()


def test_inspection_directory_swap_cannot_follow_a_new_symlink(tmp_path):
    root = tmp_path / "archive"
    root.mkdir()
    layout = ArchiveLayout(root=root)
    layout.published.mkdir(mode=0o2750)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "private-filename").touch()

    class SwapPublished(MetadataReader):
        def entries(self, path, *, missing_ok=True):
            entries = super().entries(path, missing_ok=missing_ok)
            if path == layout.published:
                path.rename(root / "retained-original")
                path.symlink_to(outside, target_is_directory=True)
            return entries

    inspection = inspect_archive(
        layout, archive_id=ARCHIVE_ID, table=_nfs_table(root), reader=SwapPublished(root)
    )

    assert inspection.state == "unusable"
    assert "HFMNT015" in {problem.code for problem in inspection.problems}
    assert "private-filename" not in str(inspection.as_payload())
    assert layout.published.is_symlink()


def test_inspection_rejects_symlinked_root_ancestors_before_mount_resolution(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    (actual / "archive").mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    layout = ArchiveLayout(root=alias / "archive")

    inspection = inspect_archive(
        layout,
        archive_id=ARCHIVE_ID,
        table=_nfs_table(actual / "archive"),
        reader=MetadataReader(layout.root),
    )

    assert inspection.state == "unusable"
    assert inspection.existing_directories == ()
