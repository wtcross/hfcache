"""URI headers preserve raw JSON identity and the admitted original operation."""

import json
from urllib.parse import unquote, urlsplit

import pytest
from starlette.requests import Request

from hfcache.api.auth import CredentialClass, Principal
from hfcache.api.commands import _accepted
from hfcache.api.operations import OperationStore
from hfcache.config import ApplicationConfig
from hfcache.server_config import PolicySnapshot, ServerConfig
from hfcache.services.context import ExecutionContext
from hfcache.url_paths import uri_path
from tests.fixtures import examples


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("/", "/"),
        ("/api/v1/operations/abcd", "/api/v1/operations/abcd"),
        ("/management/ui/", "/management/ui/"),
        ("/管理/ui/", "/%E7%AE%A1%E7%90%86/ui/"),
        ("/é/mcp/", "/%C3%A9/mcp/"),
        ("/café/😀/ui/", "/caf%C3%A9/%F0%9F%98%80/ui/"),
        ("/a:@/b!$&'()+,;=[]/mcp/", "/a:@/b!$&'()+,;=[]/mcp/"),
        ('/a"<>/ui/', "/a%22%3C%3E/ui/"),
        ("/a`{}|^/ui/", "/a%60%7B%7D%7C%5E/ui/"),
    ],
)
def test_uri_path_has_exact_utf8_spelling_without_origin_or_identity_change(raw, expected):
    encoded = uri_path(raw)
    assert encoded == expected
    assert encoded.isascii()
    assert unquote(encoded, encoding="utf-8", errors="strict") == raw
    target = urlsplit("https://archive.invalid" + encoded)
    assert (target.scheme, target.netloc, target.query, target.fragment) == (
        "https",
        "archive.invalid",
        "",
        "",
    )


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "relative",
        "//foreign.invalid/ui/",
        "///ui/",
        "/a//b",
        "/a/./b",
        "/a/../b",
        "/a//",
        "/a?b",
        "/a#b",
        "/a\\b",
        "/a%2Fb",
        "/a b",
        "/nul\0",
        "/line\n",
        "/tab\t",
        "/zero\u200b",
        "/surrogate\ud800",
    ],
)
def test_uri_path_refuses_ambiguous_or_already_encoded_input(raw):
    with pytest.raises(ValueError, match="normalized absolute raw path"):
        uri_path(raw)


@pytest.mark.parametrize(
    ("prefix", "encoded_prefix"),
    [
        ("", ""),
        ("/management", "/management"),
        ("/管理", "/%E7%AE%A1%E7%90%86"),
        ("/é", "/%C3%A9"),
        ('/a"<>', "/a%22%3C%3E"),
        ("/a:@/b!$&'()+,;=[]", "/a:@/b!$&'()+,;=[]"),
    ],
)
def test_admitted_response_quotes_only_location_and_retains_original_binding(
    tmp_path, prefix, encoded_prefix
):
    config = ApplicationConfig.model_validate(
        {
            "schema_version": 1,
            "storage": {
                "archive_root": str(tmp_path / "archive"),
                "archive_id": examples.ARCHIVE_ID,
            },
        }
    )
    snapshot = PolicySnapshot(config, config.fingerprint())
    server = ServerConfig.model_validate(
        {
            "schema_version": 1,
            "credentials": {"writer": {"file": str(tmp_path / "not-opened.token")}},
            "listener": {"root_path": prefix},
        }
    )
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": prefix + "/api/v1/plans",
            "root_path": prefix,
            "headers": [],
            "state": {"execution_context": ExecutionContext.new_request()},
        }
    )
    principal = Principal(CredentialClass.REST_WRITER)
    key = "retain-this-original-key"
    with OperationStore(tmp_path / "operations") as store:
        admission = store.admit(
            principal, key, "/api/v1/plans", {"selectors": []}, lambda: snapshot
        )
        response = _accepted(request, admission, server)
        payload = json.loads(bytes(response.body))
        suffix = "/api/v1/operations/" + admission.receipt.operation_id
        assert response.status_code == 202
        assert response.headers.getlist("location") == [encoded_prefix + suffix]
        assert payload["links"] == {
            "status": prefix + suffix,
            "result": prefix + suffix + "/result",
            "events": prefix + suffix + "/events",
        }
        assert payload["operation"]["operation_id"] == admission.receipt.operation_id
        assert store.lookup(principal, key).operation_id == admission.receipt.operation_id
        repeated = store.admit(
            principal,
            key,
            "/api/v1/plans",
            {"selectors": []},
            lambda: pytest.fail("header rendering cannot consult replacement policy"),
        )
        assert not repeated.created
        assert _accepted(request, repeated, server).headers["location"] == encoded_prefix + suffix
    assert not config.storage.archive_root.exists()
