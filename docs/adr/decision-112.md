# Separate server authority and verified bearer capabilities

- Decision identity: 112.

- MCP transport amendment: [decision 124](decision-124.md).
- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-17.


## Context, decision and rationale

Archive TOML expresses storage/repository intent; daemon listeners, trust,
credential classes and resource budgets need a separate restart-only strict frozen
schema-1 ServerConfig. Fresh InstalledPolicy snapshots pin startup archive root/
UUID while reloading allowed archive policy. Silent authority changes fail closed.
Combining these domains would make reader setup depend on writer internals.

Protected explicit files or named systemd credentials supply distinct REST writer,
optional REST reader and optional MCP-reader capabilities. Missing required writer
or invalid configured sources fail startup; disabled optional sources stay inert.
No ambient discovery, token literals, duplicate active values or cross-interface
reuse is accepted. Descriptor-pinned no-follow ownership/mode/link/byte checks and
constant-time class matching protect loaded sources; rotation requires restart.

The explicit server-local Hub file is trusted startup input, never request input.
Candidate validation is bounded writer-only pure syntax/compatibility assessment;
candidate planning compares all six installed authority fields and uses installed
credentials. The independent base client has its own verified endpoint/source
settings. Optional MCP authenticates each request and exposes only its curated
read registry; native named delivery and rootless file-mounted delivery are distinct.

## Relationships and technical evidence

- [decision 124](decision-124.md)
- [decision 113](decision-113.md)
- [decision 116](decision-116.md)
- [decision 119](decision-119.md)
- [decision 108](decision-108.md)
- [FW-01–FW-04](fw-01.md)
- [AD-21](ad-21.md)
- [decision 111](decision-111.md)
- [server configuration/authentication](../server.md)
- [API capabilities](../api.md)
- [configuration domains](../configuration.md)
- [security](../security.md)
- [invariants](../invariants.md)
- [server policy](../../src/hfcache/server_config.py)
- [credential/capability core](../../src/hfcache/api/auth.py)
- [optional FastAPI dependencies](../../src/hfcache/api/security.py)
- [HTTPX factory](../../src/hfcache/http_transport.py)
- [locked isolated-install checks](../../scripts/check-installations.py)
- [strict configuration/reload/property tests](../../tests/unit/test_server_config.py)
- [adversarial credential/class tests](../../tests/unit/test_server_auth_adversarial.py)
- [FastAPI adapter tests](../../tests/unit/test_api_security.py)
- [transport defaults](../../tests/unit/test_http_transport.py)
- [Decision 118](decision-118.md)
- [MCP](../mcp.md)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).

- [HTTPX SSL verification](https://www.python-httpx.org/advanced/ssl/)

- [transport interfaces, including Unix sockets](https://www.python-httpx.org/advanced/transports/)

- [FastAPI security tools and HTTPBearer](https://fastapi.tiangolo.com/reference/security/)

- [application lifespan](https://fastapi.tiangolo.com/advanced/events/)

- [release notes](https://fastapi.tiangolo.com/release-notes/)

- [locked release metadata](https://pypi.org/pypi/fastapi/0.143.3/json)

- [Uvicorn socket, TLS, worker and resource settings](https://uvicorn.dev/settings/)

- [Uvicorn release notes](https://www.uvicorn.org/release-notes/)

- [locked release metadata](https://pypi.org/pypi/uvicorn/0.54.0/json)

- [HTTPX bounded timeouts](https://www.python-httpx.org/advanced/timeouts/)

- [client API](https://www.python-httpx.org/api/)

- [uv project dependencies and extras](https://docs.astral.sh/uv/concepts/projects/dependencies/)

- [Python 3.14 descriptor operations](https://docs.python.org/3.14/library/os.html)

- [constant-time comparison](https://docs.python.org/3.14/library/hmac.html)

- [RFC 6750 bearer token alphabet and header use](https://www.rfc-editor.org/rfc/rfc6750#section-2.1)
