"""Optional FastAPI bearer extraction and stable failures, without an application."""

import asyncio

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from hfcache.api.auth import Capability, CredentialClass, load_credentials
from hfcache.api.security import BearerAuthentication, RequireCapability
from hfcache.server_config import validate_server_config_mapping


@pytest.fixture
def authentication(tmp_path):
    sources = {}
    for name, token in (
        ("writer", "writer-" + "a" * 48),
        ("reader", "reader-" + "b" * 48),
        ("mcp_reader", "mcp-" + "c" * 48),
    ):
        path = tmp_path / name
        path.write_text(token)
        path.chmod(0o600)
        sources[name] = {"file": str(path)}
    return BearerAuthentication(
        load_credentials(
            validate_server_config_mapping({"schema_version": 1, "credentials": sources})
        )
    )


def request(headers=(), *, query=b""):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": query,
            "headers": list(headers),
        }
    )


@pytest.mark.parametrize(
    "field",
    [
        None,
        b"",
        b"Basic opaque",
        b"Bearer wrong",
        b"Bearer " + b"x" * 5000,
        b"Bearer writer-" + b"a" * 48 + b" ",
        b"Bearer mcp-" + b"c" * 48,
    ],
)
def test_missing_malformed_wrong_and_other_interface_fields_share_401(authentication, field):
    headers = () if field is None else ((b"authorization", field),)
    with pytest.raises(HTTPException) as caught:
        asyncio.run(authentication(request(headers)))
    assert caught.value.status_code == 401
    assert caught.value.detail == "Not authenticated"
    assert caught.value.headers == {"WWW-Authenticate": 'Bearer realm="hfcache"'}
    assert "writer-" not in str(caught.value)
    assert "mcp-" not in str(caught.value)


def test_repeated_authorization_cannot_choose_a_stronger_principal(authentication):
    headers = (
        (b"authorization", b"Bearer reader-" + b"b" * 48),
        (b"authorization", b"Bearer writer-" + b"a" * 48),
    )
    with pytest.raises(HTTPException) as caught:
        asyncio.run(authentication(request(headers)))
    assert caught.value.status_code == 401


def test_query_and_cookie_bearers_do_not_authenticate(authentication):
    with pytest.raises(HTTPException) as caught:
        asyncio.run(
            authentication(
                request(
                    ((b"cookie", b"token=writer-" + b"a" * 48),), query=b"token=writer-" + b"a" * 48
                )
            )
        )
    assert caught.value.status_code == 401


def test_reader_can_read_but_write_has_stable_403(authentication):
    reader = request(((b"authorization", b"Bearer reader-" + b"b" * 48),))
    principal = asyncio.run(RequireCapability(authentication, Capability.READ)(reader))
    assert principal.credential_class is CredentialClass.REST_READER
    with pytest.raises(HTTPException) as caught:
        asyncio.run(RequireCapability(authentication, Capability.WRITE)(reader))
    assert caught.value.status_code == 403
    assert caught.value.detail == "Forbidden"
    assert caught.value.headers == {}


def test_writer_has_rest_capabilities_but_no_mcp_capability(authentication):
    writer = request(((b"authorization", b"Bearer writer-" + b"a" * 48),))
    assert (
        asyncio.run(RequireCapability(authentication, Capability.WRITE)(writer)).credential_class
        is CredentialClass.REST_WRITER
    )
    with pytest.raises(HTTPException) as caught:
        asyncio.run(RequireCapability(authentication, Capability.MCP_READ)(writer))
    assert caught.value.status_code == 403
