> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 119 — Preserve server read identity and separate candidate validity from authority

- Status: Accepted; implemented by API-012 on 2026-10-18, with operational
  observation advanced by [decision 120](../../../../../adr/decision-120.md).
- Date: 2026-10-18.
- Work package: API-012, this commit.
- Source: [progress decision 119](../../../../progress.md#decisions),
  [active plan](../../../../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../../../../plans/tasks/api-012-migrate-read-cli-and-candidates.md).
API-backed Cockpit mechanisms are amended by [decision 122](../../../../../adr/decision-122.md).

## Context and decision

Migrate CLI metadata reads and read-only jobs to the typed API client. Preserve
exact server Envelope command/run identity, timestamps, status/warnings/errors,
application exit and payload through one terminal stdout rendering. Page walks
must reconstruct complete data, and list-with-revisions joins base inventory with
revision rows under explicit consistency checks; refuse inconsistent evidence
rather than dropping unmanaged repositories or silently splicing results.

Keep help/local version independent, add explicit server version, and retain only
explicit `config validate --local` as offline bootstrap validation. It is never an
API fallback. Reader commands need no archive TOML/mount/service UID/Hub credential.
Reject explicit legacy archive config on other API reads and reject Hub-token
options rather than forwarding them. Inspection uses the server's configured
target with canonical legacy command `archive init`; no client root path is
required. An optional root restatement checks the returned root and selects no
filesystem path on the server.

An explicit `--config` on validate/plan reads bounded TOML on the CLI host and
sends content, never a pathname for server interpretation. Candidate syntax/policy
validity and authority compatibility are separate. A syntactically valid proposal
with changed authority remains valid, reports compatibility=false and only fixed
mismatch names, and resolves no credential or Hub request. That validation proves
neither credential availability nor network/account identity.

Candidate planning requires installed root/UUID, Hub endpoint, token mode,
credential name and expected account to match before any credential-bearing work.
Recheck all six fields after queue waiting before Hub work, including the
credential name excluded from the policy fingerprint. Then apply candidate
repository/retention/worker policy while resolving only the installed authorized
credential. Authority changes need operator installation before planning;
startup-pinned root/UUID changes also require restart. Candidate bodies grant no installation or apply authority.
The receipt/key uses the installed admitted fingerprint, never a replacement
candidate fingerprint. Adding optional candidate support must preserve the previous
installed-plan canonical mapping/digest when candidate is absent; existing keys
must not conflict solely because a new optional field appeared. Explicit null
is refused rather than treated as installed intent.

Plan/read-only diagnostics remain keyed jobs with Hub/resource/control-state
effects; they wait for the exact terminal Envelope, not a receipt rendered as
success. Accepted work is not cancelled by lost observation, and the original key/
operation survives uncertainty. Mutation/operation UX migration remains API-013.

## Rationale and alternatives

Readers must report writer truth rather than probe their own unrelated machine.
Reconstructing a new CLI Envelope would replace server evidence with observer
metadata; partial page reconstruction would silently change existing results.
A local-filesystem fallback would create another execution authority when the
API is unavailable. Refuse those alternatives.

Treating compatibility as syntax failure would prevent reviewing legitimate
operator authority changes. Resolving candidate credentials or using its endpoint
would redirect installed privilege. Pure validation plus installed-authority planning
retains the existing Cockpit candidate → validate → preview → privileged atomic
install pipeline (CP-11), without adding a configuration-install REST endpoint.
An optional DTO extension must not change historical idempotency comparison input.

### UDS descriptor ownership and FW-04

The required missing-local-API test exposed a descriptor leak in locked
HTTPCore 1.0.9's synchronous Unix connect failure path. Promote the already-locked
`httpcore` package to an explicit base dependency, `>=1.0.9,<2`, retaining 1.0.9
and adding no package or version upgrade. Correct unavailable-API handling must
release every socket, including failed connections; warnings remain errors.

Use a narrow Unix-only HTTPX `BaseTransport` with HTTPCore's public
`ConnectionPool`, `NetworkBackend` and `NetworkStream` interfaces. The backend
owns and closes failed/timed-out sockets, and the response stream owns cleanup.
Keep HTTP parsing/pooling in maintained HTTPCore and TCP/TLS on HTTPX. Refuse IP
fallback, private pool mutation, global monkeypatches, warning suppression and a
hand-written HTTP parser. This direct dependency satisfies FW-04: standard-library
socket ownership fixes the leak while maintained HTTP framing/pooling supplies
protocol correctness. HTTPX's public transport does not expose backend injection;
a public adapter avoids depending on its private implementation.

Official references: [HTTPX custom transports](https://www.python-httpx.org/advanced/transports/),
[HTTPCore public network backends](https://www.encode.io/httpcore/network-backends/),
[connection pools](https://www.encode.io/httpcore/connection-pools/), and the
[affected locked implementation](https://github.com/encode/httpcore/blob/1.0.9/httpcore/_backends/sync.py).

## Consequences and relationships

Implements [118](../../../../../adr/decision-118.md)'s reader integration and
[116](../../../../../adr/decision-116.md)'s bounded candidate hooks; amends
[AD-21](../../../../../adr/ad-21.md) and [087](../../../../../adr/decision-087.md) for the reader/candidate boundary,
and [FW-01–FW-04](../../../../../adr/fw-01.md)/[108](../../../../../adr/decision-108.md)/[112](../../../../../adr/decision-112.md) for explicit HTTPCore use.
Preserves INV-001/002/006/008/
012–014, AD-21, CP-11, FS-12 and all shared domain/credential rules. Candidate
planning receipts never authorize later apply. The direct HTTPCore declaration
retains the already-locked package/version. No new durable shape, MCP,
production operation or filesystem installation authority is introduced.

[CLI](../../../../../cli.md), [client](../../../../../api-client.md), [API](../../../../../api.md),
[configuration](../../../../../configuration.md), [security](../../../../../security.md),
[consumer setup](../../../../../consumers.md) and [invariants](../../../../../invariants.md) define the
current boundaries. The task records actual acceptance and the full gate.

Enforcement: [CLI transport/reconstruction](../../../../../../src/hfcache/cli_client.py),
[CLI modes](../../../../../../src/hfcache/cli.py),
[candidate services](../../../../../../src/hfcache/services/candidates.py) and
[typed route adapters](../../../../../../src/hfcache/api/commands.py).
[Unix resource ownership](../../../../../../src/hfcache/unix_http.py) integrates through
[HTTP construction](../../../../../../src/hfcache/http_transport.py), with
[socket/stream failure regressions](../../../../../../tests/unit/test_unix_http.py) and
[real Unix/TCP/TLS coverage](../../../../../../tests/unit/test_api_client_sockets.py).
Evidence: [authenticated CLI fixture](../../../../../../tests/api_cli.py),
[reader CLI integration](../../../../../../tests/unit/test_cli_api_reads.py),
[legacy read shapes](../../../../../../tests/unit/test_readonly_commands.py),
[candidate HTTP tests](../../../../../../tests/unit/test_api_candidates.py) and
[candidate/reader adversarial cases](../../../../../../tests/unit/test_api_candidates_adversarial.py).

## API-013 operational observation amendment (2026-10-18)

[Decision 120](../../../../../adr/decision-120.md) extends the shared submission/wait helper to all
jobs, including planning/read-only diagnostics. Default exact terminal output is
unchanged; explicit detach is identified admission, while mandatory key/operation
handles survive quiet and interrupted observation. Candidate authority and
historical canonical key mappings are unchanged. Pure request extraction grants
no local mutation authority or configuration-install path.


## 2026-10-18 Cockpit API integration amendment (API-015)

Cockpit now applies the syntax/installed-authority distinction through its
API-only CLI boundary. Exact candidate/base checks under a retained root config
flock prevent stale assessment/preview reuse. Incompatible/unknown authority blocks
plugin installation with manual guidance; successful installed confirmation must
match the exact expected fingerprint. Planning remains installed-credential-only;
REST gains no install authority. See [decision 122](../../../../../adr/decision-122.md).
