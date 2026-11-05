# Preserve server read identity and separate candidate validity from authority

- Decision identity: 119.

## 2026-10-21 protected-reader amendment

[Decision150](decision-150.md) binds protected host status to the configured
archive UUID and independent selected deployment. Status is neither archive
health nor candidate/install authority. New Basic admission proof does not
widen bearer/MCP behavior, alter installed/candidate policy semantics or replace
original operation observations with replay.

## Context, decision and rationale

The operational metadata CLI preserves exact server Envelope identity/status/
times/exit in JSON and classified human rendering. Complete bounded page assembly
and inventory/revision joins retain empty/unmanaged rows, current/exact publication
identity, counts, generation order and archive/policy consistency. Inconsistent or
exhausted walks fail, rather than silently omitting rows. Local bootstrap validation
is explicit; remote inspection compares installed target identity without accessing
client archive paths. Legacy operational archive-config/Hub overrides refuse.

Promote already-locked HTTPCore to explicit base use for its public Unix transport
interfaces, with owned-socket cleanup on failure. TCP/TLS stays on HTTPX. Private
pool mutation, IP fallback, warning suppression and dependency/version churn were
rejected; resource-safe maintained framing is the correctness benefit.

## Relationships and technical evidence

Deployment prerequisites are defined in the
[deployment guide](../deployment-centos-stream-10.md).

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

The Unix transport treats an empty write as a no-op. Closing the stream on an
empty end-of-message write could prematurely close a valid response; retaining
the connection preserves HTTP framing and response ownership.

## Replacement UI design amendment (2026-10-20)

[Decision 141](decision-141.md) amends this record for the accepted
replacement design. Managed-edit/helper design supports configuration administration while preserving exact candidate/base bytes, installed authority and original key canonicalization.
