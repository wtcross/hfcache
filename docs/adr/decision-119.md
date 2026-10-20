# Preserve server read identity and separate candidate validity from authority

- Decision identity: 119.

- Status: Amended; see decisions 133/134 and the amendments referenced below.
- Date: 2026-10-18.
API-backed Cockpit mechanisms are amended by [decision 122](decision-122.md).


## Context, decision and rationale

The operational metadata CLI preserves exact server Envelope identity/status/
times/exit in JSON and classified human rendering. Complete bounded page assembly
and inventory/revision joins retain empty/unmanaged rows, current/exact publication
identity, counts, generation order and archive/policy consistency. Inconsistent or
exhausted walks fail, rather than silently omitting rows. Local bootstrap validation
is explicit; remote inspection compares installed target identity without accessing
client archive paths. Legacy operational archive-config/Hub overrides refuse.

Candidate text is bounded local input uploaded only for writer-authorized candidate
validation/planning. Syntax validity, installed compatibility and credential/Hub
proof are separate. Compatible planning rechecks all six authority fields and uses
installed credentials after queue waiting. Missing installed policy can yield unknown
compatibility, never permission to plan. Absent candidate preserves installed key
digests; explicit null refuses. The guarded Cockpit installer retains exact base/
candidate bytes, backups and installed fingerprint confirmation outside the API.

Promote already-locked HTTPCore to explicit base use for its public Unix transport
interfaces, with owned-socket cleanup on failure. TCP/TLS stays on HTTPX. Private
pool mutation, IP fallback, warning suppression and dependency/version churn were
rejected; resource-safe maintained framing is the correctness benefit.

## Relationships and technical evidence

- [decision 120](decision-120.md)
- [decision 122](decision-122.md)
- [118](decision-118.md)
- [116](decision-116.md)
- [AD-21](ad-21.md)
- [087](decision-087.md)
- [FW-01–FW-04](fw-01.md)
- [108](decision-108.md)
- [112](decision-112.md)
- [CLI](../cli.md)
- [client](../api-client.md)
- [API](../api.md)
- [configuration](../configuration.md)
- [security](../security.md)
- [consumer setup](../consumers.md)
- [invariants](../invariants.md)
- [CLI transport/reconstruction](../../src/hfcache/cli_client.py)
- [CLI modes](../../src/hfcache/cli.py)
- [candidate services](../../src/hfcache/services/candidates.py)
- [typed route adapters](../../src/hfcache/api/commands.py)
- [Unix resource ownership](../../src/hfcache/unix_http.py)
- [HTTP construction](../../src/hfcache/http_transport.py)
- [socket/stream failure regressions](../../tests/unit/test_unix_http.py)
- [real Unix/TCP/TLS coverage](../../tests/unit/test_api_client_sockets.py)
- [authenticated CLI fixture](../../tests/api_cli.py)
- [reader CLI integration](../../tests/unit/test_cli_api_reads.py)
- [legacy read shapes](../../tests/unit/test_readonly_commands.py)
- [candidate HTTP tests](../../tests/unit/test_api_candidates.py)
- [candidate/reader adversarial cases](../../tests/unit/test_api_candidates_adversarial.py)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).

- [HTTPX custom transports](https://www.python-httpx.org/advanced/transports/)

- [HTTPCore public network backends](https://www.encode.io/httpcore/network-backends/)

- [connection pools](https://www.encode.io/httpcore/connection-pools/)

- [affected locked implementation](https://github.com/encode/httpcore/blob/1.0.9/httpcore/_backends/sync.py)

## Supplemental discovery amendment (2026-10-19)

[Decision 133](decision-133.md) defines proposed tag/curation identities, the narrow
independent-atomic adjunct exception and protected read capabilities. Existing
archive, candidate-byte, whole-archive authorization and registered MCP boundaries
remain in force until corresponding additive implementation is accepted. Tags do
not change operational policy identity or grant installation/write authority.

## Empty Unix writes amendment (2026-10-20)

Repeated actual Unix-socket tests exposed an empty h11 end-of-message write after
the peer had sent and closed its response. `sendall(b'')` could raise BrokenPipe;
the owned adapter closed the descriptor before HTTPCore's deliberate response
read after a write error, yielding EBADF/ReadError instead of the received response.
The locked upstream synchronous backend explicitly makes empty writes a no-op.
The owned adapter now follows that contract, preserving cleanup for nonempty
I/O errors. A deterministic real socket regression and repeated existing truncated
response tests establish the repair; no framing/pool internals, dependency update,
fallback or request replay is added. [Decision134](decision-134.md) records the
Cockpit integration scope. This observed client defect does not identify the
original installed bridge/session trigger.
