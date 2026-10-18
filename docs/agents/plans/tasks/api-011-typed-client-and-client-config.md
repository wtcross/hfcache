# API-011: Build the typed API client and reader-only configuration

| Field | Value |
| --- | --- |
| Work package | `API-011` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-010](api-010-guarded-maintenance-api.md) |
| Phase | 3 — CLI and REST integration |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-011: add typed API client and reader configuration` |

## Scope and acceptance

1. Implement a typed synchronous client appropriate for Typer, with explicit HTTP/Unix-socket transport, connect/read timeouts, streaming, response/envelope validation, page iteration, server capability negotiation, and optional expected archive UUID. Keep it independent of ApplicationConfig, archive filesystem paths, and server/MCP imports.
2. Add strict client TOML and `--client-config`, `--api-url`, `--api-socket`, `--api-token-file` selection using plan §7 precedence. Resolve only the named API credential. Preserve local help/version and handle missing writer config on reader hosts without trying to load it.
3. Verify TLS; reject token-bearing URLs/userinfo and cross-origin redirect credential forwarding. Disable ambient proxy/credential behavior by default. Distinguish protocol/auth/config failures from absent API or uncertain execution using the new documented HFAPI codes.
4. Generate mutation idempotency keys before transmission and retain them across permitted retries. Support an explicit key for a deliberate retry and expose authenticated lookup without resubmission. Poll/read retries are bounded; a lost response never triggers a new-key mutation replay. Validate API/envelope versions and unknown server capabilities rather than guessing.

## Contracts, invariants, and ADRs

`INV-001`–`INV-003`, `INV-006`, `INV-008`; plan §§3–5, 7.

Use the [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Create `docs/api-client.md` with reader and writer setup, endpoint/credential precedence, TLS/CA behavior, compatibility/version errors, retry rules, and troubleshooting. Update configuration, README, and CLI global-option contracts.

## Validation

Completed mock transport and real temporary Unix/TCP/TLS checks, reader-only
configuration/source setup, auth/CA/UUID/proxy refusal, strict malformed/version/
identity/header/body/page/event handling, retained-key uncertainty and actual
base/server wheel imports. Exact focused/drill/full-gate evidence follows.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../workflow.md). Work only on
`feat/rest-api-and-mcp`. A task may include several related subtasks, but this
work package owns one implementation commit. Read the affected invariant and ADR
sections before editing; update their enforcement/decision links where behavior
changes. Include code, tests, documentation, task evidence, the current pointer,
and completed progress audit together. Do not run production operations or weaken
host controls. Do not push, merge, tag, or deploy.

Mark `in_progress` only when authorized and dependencies are complete. On a real
blocker, record the exact missing prerequisite and unblock condition. A skipped
required test is not passing evidence. Use `this commit` until a real commit exists.

## Execution notes and handoff

Implementation continues under Tyler's authorized active plan after API-010
completed in `66d85a3`; git, completed dependency and current selector were
reconciled before starting. API-011 is the sole task in progress. Collaborators
share client configuration/global-option storage, independent synchronous typed
client/models, adversarial client tests and all Markdown contracts/records.
Decision 118 records this boundary in the actual progress log and ADR index.

Contract-first review covers INV-001–003/006/008/012–014 and decisions
108/111–117. Separate strict client configuration and an explicit API credential
must work without archive TOML, archive paths/mounts, service UID or Hub credential.
Explicit CLI endpoint selection overrides the configured endpoint as one URL/socket
group. No ambient proxy/credential discovery, cross-origin redirects, silent
filesystem fallback or daemon startup. Finite request/response/page/retry/poll
budgets and strict wire/version/identity validation retain exact domain results.
A lost submission response preserves its original key and uncertainty; no new-key
replay. Operational CLI migration remains API-012/013; no MCP/dependency/production
operation, deployment, push, merge or tag. Actual completion evidence is pending.

Contract-first implementation choices are recorded in decision 118 and
`docs/api-client.md`: optional installed `/etc/hfcache/client.toml`, independent
required integer schema 1, atomic explicit URL/socket override, named API-only
`hfcache.api` fallback after selected token-file precedence, exact timing/byte/page
bounds and explicit capabilities negotiation. Global options are parsed/stored
without runtime migration. Full `/api/v1/...` paths receive the configured prefix;
returned operation links must match exact derived paths, never redirect authority.

Post-transmission acknowledgement trust is conservative: malformed/truncated/
wrong-identity 202 or untrusted error body may follow durable admission, so retain
key/route and HFAPI020; validated remote problem retains its taxonomy and original key/route. Old-operation
UUID/fingerprint/domain relations survive policy changes. Per-response byte limits,
page ceilings/cursor-cycle checks and finite read/poll observation confer no
cancellation or replay authority. Standalone result/events fetch exact receipt
metadata first when needed; result/domain identity, immutable old fingerprints,
contiguous event/gap semantics and duplicate primary row identity checks refuse
substitution. Digest tracking is bounded without aggregating result rows, and
poll deadlines are checked on each transport chunk.

`packaging/client.example.toml` is model-validated in the locked base environment
without loading a credential or contacting the API. Root's 40 config/real-socket
checks pass, including Unix/TCP/custom-CA TLS, untrusted CA/bearer/UUID refusal,
ignored proxy environment and no archive creation. Actual predecessor `66d85a3`
built/installed on Python 3.14.6 rejects the client option with exit 2; current local
version returns 0 without using it. The independent schema-1 file stays byte-for-
byte unchanged, no API/Hub is contacted and no archive is created, recorded in
`.scratch/api-011-compatibility/result.json`. An initial scratch environment chose
Python 3.12 and lacked its cached pydantic-core; a separate locked offline Python
3.14 environment completed the drill without code/dependency/network changes.
The environment date advanced to 2026-10-18 during this task; historical creation
and plan identities remain unchanged. Final core/adversarial selection passed
127 tests in 0.78 seconds (14 core, 113 adversarial), with whole-project format/
Ruff/types/whitespace clean; root's 40 config/socket checks are released. Selected
tokens also cannot occur in configured URL prefixes after credential resolution.
The first full gate then exited 0, without a gate-cycle correction or post-freeze
source change; completed evidence follows.

## Completion evidence

Completed 2026-10-18, this commit.

- Independent frozen client settings require explicit integer schema 1 and
  separate API-only endpoint/source/CA/expected UUID/budgets. Optional installed
  client TOML, strict bounded file/URL/path checks and atomic CLI URL/socket
  overrides follow the declared precedence. Only the selected protected API
  file/named systemd source resolves credentials; unusable sources fail rather
  than discovering Hub/ambient credentials or becoming anonymous. Global CLI
  options are stored only; runtime migration remains API-012/013.
- The synchronous context-managed base client uses verified TLS/Unix sockets,
  no redirects/ambient proxy/netrc/cookies, bounded streamed bytes/headers/JSON
  and explicit capabilities negotiation without constructor requests. Client
  wire/Envelope schemas require exact integer version 1. Unknown capabilities,
  unsafe links/queries, malformed/truncated/encoded/unversioned responses, UUID
  changes and inconsistent metadata fail safely without body/secret echo.
- Page iteration pins archive/fingerprint/command, refuses cursor cycles/duplicate
  primary identities and bounds digest tracking without aggregating rows. Valid
  failed domain pages retain their Envelope/exit; exact responses reject cursors.
  Standalone result/events obtains the exact receipt when needed, preserving old
  admitted fingerprint/domain-run identity and immutable provenance. Event gaps
  must match explicit retention metadata; polling uses one absolute deadline
  checked across retries/transport chunks and never cancels accepted work.
- Keys are generated/accepted and exposed before POST. Unusable post-transmission
  acknowledgement is HFAPI020 with original key/route; no automatic POST/new-key
  replay. Validated remote problems retain server taxonomy plus key/route,
  including HFAPI008/500 that may follow admission. HFAPI017/018 config/protocol
  exit 10 and HFAPI019/020 connectivity/uncertainty exit 20 preserve exact remote
  domain Envelopes and existing server classifications. No direct archive fallback
  or automatic daemon start.
- Focused command:
  `rtk uv run --locked --extra server pytest tests/unit/test_api_client.py tests/unit/test_api_client_adversarial.py -q`
  passed 127 tests in 0.78 seconds (14 core, 113 adversarial). The released
  adversarial file separately passed 113 in 0.73 seconds. Root's 40 configuration/
  real Unix/TCP/TLS checks passed in 2.55 seconds: custom CA success, untrusted CA,
  bearer/UUID refusal, ignored proxy environment and no archive creation.
  `packaging/client.example.toml` passed syntax/model validation in the locked
  base environment without loading a token or contacting the API.
- Actual built/installed predecessor `66d85a3` on Python 3.14.6 rejects
  `--client-config` with exit 2; current local version accepts the stored option
  and exits 0 without resolving it. The complete client file remains unchanged,
  no API/Hub is contacted and no archive is created. The result is recorded in
  `.scratch/api-011-compatibility/result.json`. A first scratch setup chose
  Python 3.12 and lacked its offline pydantic-core cache; preserved separately,
  then a fresh locked Python 3.14 setup completed the drill without code,
  dependency or network changes. No archive/receipt durable schema changed.
- Definitive command:
  `rtk proxy bash scripts/check.sh > .scratch/api-011-gate.log 2>&1`
  exited 0 on the first full attempt. Lock check/server-extra sync passed;
  337 files were formatted, Ruff passed, Pyrefly reported 0 errors (11 suppressed,
  54 hidden warnings); Python passed 2,852 tests, 40 deselected, in 163.45 seconds.
  Version 0.1.10 sdist/wheel built; actual locked isolated base/server wheel
  installation/import/help/version passed, now explicitly importing client modules
  without server/MCP dependencies in base. Cockpit eslint/stylelint/types, 45
  tests (0 failures/skips) and production build passed. No gate failure/correction
  or source change after final freeze.
- Reviewed INV-001–003/006/008/012–014, FS-12, AD-21 and decisions 108/111–117.
  Decision 118 and amendments 108/112/114 preserve explicit authority, whole-archive
  roles, exact output/domain identity and consumer copy/verification ownership.
  New client/API/configuration/security/CLI/architecture/invariant/recovery,
  README/router/example, plan and Unreleased records agree. No new dependency,
  durable archive shape, runtime CLI migration, MCP or writer authority.
- Final local-link/dependency/current/matrix, all 118 numbered decision/ADR,
  example and whitespace audits pass. Matrix stays 27 implemented / 2 candidate
  rows planned. The completed [progress audit](../../progress.md#rest-api-and-read-only-mcp-api-2026-10-17)
  records the package; current selects API-012 pending. Historical plan/decision
  creation dates remain 2026-10-17; completion/current date is 2026-10-18. Live/NFS/
  installed-host and extra build-marker checks did not run. No production archive/
  listener operation, deployment, push, merge or tag; no new operator action required.
