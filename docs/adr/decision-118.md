# Observe one API authority without replaying uncertain submissions

- Decision identity: 118.

- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-17.
Native Unix/public-prefix routing is amended by [decision 123](decision-123.md).


## Context, decision and rationale

A base reader needs only explicit endpoint/trust/API credential settings, not
archive TOML, a NAS mount, Hub source, service UID or optional server/MCP imports.
Use strict independent ClientConfig and maintained HTTPX/HTTPCore transport. Explicit
URL/socket overrides replace the endpoint group; selected protected file precedes
configured file/named credential. There is no ambient proxy/netrc/token, redirect,
IP fallback, local executor fallback or automatic daemon startup.

Validate finite bytes, exact wire versions/identity and complete cursor walks;
retain old receipt policy/run identity. Generate/validate a nonsecret key before
the sole POST; only bounded idempotent reads retry. Lost/malformed acknowledgement
preserves the original key/route as uncertainty, never a new-key replay. One finite
observation deadline covers every read/chunk/retry/sleep. Adaptive event limits and
final empty-page accounting retain configured bounds. The operational CLI is this
client, with named local help/version/bootstrap/foreground exceptions. Handwritten
HTTP or borrowing server internals would undermine reader isolation.

## Relationships and technical evidence

- [decision 120](decision-120.md)
- [decision 123](decision-123.md)
- [108](decision-108.md)
- [112](decision-112.md)
- [109](decision-109.md)
- [114](decision-114.md)
- [Client contract](../api-client.md)
- [API](../api.md)
- [CLI](../cli.md)
- [configuration](../configuration.md)
- [security](../security.md)
- [invariants](../invariants.md)
- [independent settings/source selection](../../src/hfcache/client_config.py)
- [strict wire models](../../src/hfcache/client_models.py)
- [synchronous client](../../src/hfcache/client.py)
- [reader example](../../packaging/client.example.toml)
- [core client tests](../../tests/unit/test_api_client.py)
- [configuration tests](../../tests/unit/test_client_config.py)
- [real Unix/TCP/TLS tests](../../tests/unit/test_api_client_sockets.py)
- [adversarial client tests](../../tests/unit/test_api_client_adversarial.py)
- [locked base/server import smoke](../../scripts/check-installations.py)
- [Decision 119](decision-119.md)
- [actual CLI socket integration](../../tests/unit/test_interface_integration.py)
- [observer budget tests](../../tests/unit/test_cli_operation_helpers.py)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).

- [Unix/custom transports](https://www.python-httpx.org/advanced/transports/)

- [timeouts](https://www.python-httpx.org/advanced/timeouts/)

- [environment discovery controls](https://www.python-httpx.org/environment_variables/)

- [streaming responses](https://www.python-httpx.org/quickstart/#streaming-responses)
