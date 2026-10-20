"""Independent malformed/CSRF requests cross real TLS sockets and the actual verifier."""

import asyncio
import base64
import secrets

import pytest

from hfcache.redaction import redact_text
from tests.unit.test_web_basic_sockets import (
    client_for,
    running,
)
from tests.unit.test_web_basic_sockets import (
    memory_credentials as memory_credentials,  # noqa: PLC0414 - register shared fixture
)
from tests.unit.test_web_basic_sockets import (
    tls_identity as tls_identity,  # noqa: PLC0414 - register shared fixture
)


async def raw_request(
    harness, *, method="POST", path="/api/v1/not-a-route", headers=(), body_length=100
):
    """Leave the declared body unsent: refusal must precede body consumption."""
    port = harness["settings"].listener.tcp_port
    reader, writer = await asyncio.open_connection(
        "127.0.0.1", port, ssl=harness["tls"], server_hostname="localhost"
    )
    try:
        raw = f"{method} {path} HTTP/1.1\r\nHost: localhost:{port}\r\n".encode()
        raw += b"".join(key + b": " + value + b"\r\n" for key, value in headers)
        raw += f"Content-Length: {body_length}\r\nConnection: close\r\n\r\n".encode()
        writer.write(raw)
        await writer.drain()
        response = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=5)
        return int(response.split(b" ", 2)[1]), response
    finally:
        writer.close()
        await writer.wait_closed()


@pytest.mark.parametrize(
    "invalid",
    [
        "missing",
        "duplicate",
        "malformed-base64",
        "missing-colon",
        "invalid-utf8",
        "oversized-username",
        "oversized-password",
        "oversized-header",
    ],
)
def test_malformed_auth_refuses_without_body_or_hash_work(
    tmp_path_factory, memory_credentials, tls_identity, invalid
):
    profile = tmp_path_factory.mktemp("basic-bad") / "owned"

    async def exercise():
        async with running(profile, memory_credentials, tls_identity) as harness:
            authorization = memory_credentials.basic().encode()
            headers = [(b"Authorization", authorization)]
            if invalid == "missing":
                headers = []
            elif invalid == "duplicate":
                headers.append((b"Authorization", authorization))
            else:
                choices = {
                    "malformed-base64": b"Basic %%%",
                    "missing-colon": b"Basic " + base64.b64encode(b"invalid-no-colon"),
                    "invalid-utf8": b"Basic "
                    + base64.b64encode(b"\xff:" + memory_credentials.password),
                    "oversized-username": b"Basic "
                    + base64.b64encode(b"a" * 129 + b":" + memory_credentials.password),
                    "oversized-password": b"Basic "
                    + base64.b64encode(memory_credentials.username.encode() + b":" + b"a" * 1025),
                    "oversized-header": b"Basic " + b"a" * 8193,
                }
                headers = [(b"Authorization", choices[invalid])]
            status, _ = await raw_request(harness, headers=headers)
            assert status in {401, 413}
            assert harness["provider"].stats.active == 0
            assert harness["provider"].stats.waiting == 0
            assert harness["provider"].stats.failures == 0

    asyncio.run(exercise())


def test_body_length_preflight_refuses_before_actual_password_work(
    tmp_path_factory, memory_credentials, tls_identity
):
    profile = tmp_path_factory.mktemp("basic-body") / "owned"

    async def exercise():
        async with running(profile, memory_credentials, tls_identity) as harness:
            status, _ = await raw_request(
                harness,
                headers=[(b"Authorization", memory_credentials.basic().encode())],
                body_length=1024 * 1024 + 1,
            )
            assert status == 413
            assert harness["provider"].stats.active == 0
            assert harness["provider"].stats.waiting == 0
            assert harness["provider"].stats.failures == 0

    asyncio.run(exercise())


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize(
    "invalid",
    [
        "missing-origin",
        "null-origin",
        "foreign-origin",
        "duplicate-origin",
        "missing-marker",
        "duplicate-marker",
        "wrong-marker",
        "text",
        "multipart",
        "form",
    ],
)
def test_every_unsafe_basic_method_refuses_csrf_before_body_read(
    tmp_path_factory, memory_credentials, tls_identity, method, invalid
):
    profile = tmp_path_factory.mktemp("basic-csrf") / "owned"

    async def exercise():
        async with running(profile, memory_credentials, tls_identity) as harness:
            headers = [
                (b"Authorization", memory_credentials.basic().encode()),
                (b"Origin", harness["origin"].encode()),
                (b"Content-Type", b"application/json"),
                (b"X-Hfcache-Request", b"1"),
            ]
            if invalid == "missing-origin":
                headers = [row for row in headers if row[0] != b"Origin"]
            elif invalid == "null-origin":
                headers[1] = (b"Origin", b"null")
            elif invalid == "foreign-origin":
                headers[1] = (b"Origin", b"https://foreign.invalid")
            elif invalid == "duplicate-origin":
                headers.append(headers[1])
            elif invalid == "missing-marker":
                headers = [row for row in headers if row[0] != b"X-Hfcache-Request"]
            elif invalid == "duplicate-marker":
                headers.append(headers[3])
            elif invalid == "wrong-marker":
                headers[3] = (b"X-Hfcache-Request", b"true")
            else:
                headers[2] = (
                    b"Content-Type",
                    {
                        "text": b"text/plain",
                        "multipart": b"multipart/form-data; boundary=owned",
                        "form": b"application/x-www-form-urlencoded",
                    }[invalid],
                )
            status, _ = await raw_request(harness, method=method, headers=headers)
            assert status == 403
            assert harness["provider"].stats.failures == 0
            assert not (profile / "absent-archive").exists()

    asyncio.run(exercise())


def test_wrong_user_and_wrong_password_have_uniform_private_failures(
    tmp_path_factory, memory_credentials, tls_identity
):
    profile = tmp_path_factory.mktemp("basic-uniform") / "owned"

    async def exercise():
        async with (
            running(profile, memory_credentials, tls_identity) as harness,
            client_for(harness, "tls") as client,
        ):
            wrong_password = secrets.token_urlsafe(32).encode()
            responses = []
            for authorization in (
                memory_credentials.basic(username="different-operator"),
                memory_credentials.basic(password=wrong_password),
            ):
                response = await client.get(
                    "/api/v1/version", headers={"Authorization": authorization}
                )
                assert response.status_code == 401
                payload = response.json()
                responses.append(
                    {key: value for key, value in payload.items() if key != "request_id"}
                )
                values = (
                    authorization,
                    memory_credentials.password.decode(),
                    wrong_password.decode(),
                )
                if any(value in response.text for value in values):
                    pytest.fail("authentication response disclosed a supplied credential")
                if redact_text(authorization) != "[redacted]":
                    pytest.fail("Basic Authorization was not unconditionally scrubbed")
            assert responses[0] == responses[1]
            assert harness["provider"].stats.failures == 2

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "target", ["/api/v1/not-real", "/api/v1/openapi.json", "/api/v1/health", "/api/v1/docs"]
)
@pytest.mark.parametrize("prefix", ["", "/management"])
@pytest.mark.parametrize("transport", ["tls", "unix"])
def test_authentication_precedes_route_schema_and_error_disclosure(  # noqa: PLR0913, PLR0917 - explicit real transport/prefix/route matrix
    tmp_path_factory, memory_credentials, tls_identity, target, prefix, transport
):
    profile = tmp_path_factory.mktemp("basic-routes") / "owned"

    async def exercise():
        async with (
            running(profile, memory_credentials, tls_identity, prefix=prefix) as harness,
            client_for(harness, transport) as client,
        ):
            response = await client.get(prefix + target)
            assert response.status_code == 401
            assert response.headers["content-type"].startswith("application/json")
            assert response.json()["code"] == "HFAPI001"
            assert response.headers["cache-control"] == "no-store"

    asyncio.run(exercise())


@pytest.mark.parametrize("prefix", ["", "/management"])
@pytest.mark.parametrize("transport", ["tls", "unix"])
def test_basic_exact_same_origin_post_and_legacy_no_origin_bearer_post_both_work(
    tmp_path_factory, memory_credentials, tls_identity, prefix, transport
):
    profile = tmp_path_factory.mktemp("basic-post") / "owned"

    async def exercise():
        async with (
            running(profile, memory_credentials, tls_identity, prefix=prefix) as harness,
            client_for(harness, transport) as client,
        ):
            response = await client.post(
                prefix + "/api/v1/config/validate",
                json={},
                headers={
                    "Authorization": memory_credentials.basic(),
                    "Origin": harness["origin"],
                    "X-Hfcache-Request": "1",
                },
            )
            assert response.status_code == 200
            assert response.json()["envelope"]["exit_code"] == 0
            bearer = await client.post(
                prefix + "/api/v1/config/validate",
                json={},
                headers={"Authorization": "Bearer " + memory_credentials.tokens["reader"]},
            )
            assert bearer.status_code == 200
            assert bearer.json()["envelope"]["exit_code"] == 0

    asyncio.run(exercise())
