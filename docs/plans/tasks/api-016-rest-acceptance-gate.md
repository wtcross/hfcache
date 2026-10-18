# API-016: Prove complete REST and CLI parity before beginning MCP

| Field | Value |
| --- | --- |
| Work package | `API-016` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-015](api-015-cockpit-api-client-compatibility.md) |
| Phase | 3 — CLI and REST integration |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-016: pass REST parity security and client acceptance gate` |

## Scope and acceptance

1. Audit every baseline command/mode against the API/service/role/effect/test matrix. Close missing routes, invalid-mode checks, selector coverage, legacy output mismatches, and candidate/systemd/Cockpit integration gaps with fresh task splits if needed; do not declare parity based only on sync/status tests.
2. Add/review a full adversarial suite covering credentials on every endpoint, read/write capability separation, traversal and unauthorized authority selection, stale destructive scopes, verification persistence races, queue saturation, API responsiveness, idempotency/crash boundaries, restart/no-replay, and client disconnect behavior.
3. Prove ordinary reader execution without archive config/mount/Hub token, writer-local Unix transport, base/server wheel isolation, large result streaming/page completeness, and stable API/envelope negotiation. Check legacy failure aggregation and report identity. No FastMCP dependency/import/route may yet be required.
4. Validate all current REST/server/client examples, OpenAPI determinism, documentation links, contracts, invariants, and ADR amendments. Separate implemented/tested repository behavior from pending operator installation/hardening/NFS acceptance. Record a deployment hold for any unperformed required host check.

## Contracts, invariants, and ADRs

All affected register sections; `INV-010`/`INV-011`; plan §12 REST gate.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Complete REST/CLI/server/consumer migration documentation and the traceability matrix. Record gate evidence in this task and progress. Update current selector to MCP-001 only after this package passes.

## Validation

Planned checks, not execution evidence:

`scripts/check.sh --with-build` with implemented server extras, complete Cockpit gate, full default Python suite, real throwaway Unix/TCP transport integration, documented compatibility drill, and docs/OpenAPI/example checks. Record actual versions/counts/outputs and any operator-only pending checks; no inherited prior test counts.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../agents/workflow.md). Work only on
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

Activated 2026-10-18 under Tyler's authorized REST-first implementation after
completed dependency API-015 committed as `9ba89cf`. Git/current/dependency were
reconciled with a clean tree; API-016 is the sole task in progress. Collaborators
share actual Unix/TCP prefix integration, complete parity/adversarial evidence,
strict examples/OpenAPI/docs checks and all Markdown. Decision 123 follows the
actual log. No MCP dependency/import/route or production operation, deployment,
push, merge or tag. At activation, completion awaited fresh repository acceptance, including
`scripts/check.sh --with-build`; the result is recorded below and installed-host
holds remain explicit.

Contract-first refinement: retain configured public root_path/TLS/proxy/Host/
Origin checks for TCP, while the actual supported Uvicorn AF_UNIX scope
(`client=None` plus corroborating `server=(absolute Unix socket pathname, None)`)
may use native unprefixed REST paths. Peer absence alone can be a socket error;
require that corroborated predicate for prefix and proxy-TLS exceptions, refusing
missing/malformed local evidence. Authentication/Host/Origin
and all resource bounds remain; no caller header may manufacture local transport
authority. Derive operation links and docs URLs from a trusted per-request
effective prefix, with no shared mutable prefix or forwarded-header authority.
Public OpenAPI remains deterministic. The local client/schema need no new
prefix setting or durable/config format. Verify the pinned Uvicorn implementation
and actual throwaway Unix/TCP sockets before accepting this distinction.


Fresh focused acceptance preceded the full `--with-build` gate. The final eight-file transport/read/command/client/bootstrap
sweep in `.scratch/api-016-transport-tests.log` passed 130 tests in 47.31 seconds;
the final `test_rest_transport_gate.py test_rest_pagination_gate.py` selection
passed all 14 new cases in 9.44 seconds. Locked Uvicorn 0.54.0 source and real
sockets corroborate both peer and local scope values; eleven negative cases
refuse missing/malformed/numeric local evidence for both prefix and proxy-TLS
exceptions. Real native/public Unix and TCP paths share one registry/lifespan;
schema views never mutate cached public OpenAPI.

The independent 29-mode parity manifest now names concrete CLI/API test functions
and selected parameter cases. The static citation gate plus six positive CLI
parity cases passed 68 tests in 6.68 seconds; the broader verification/read/write
CLI selection passed 154 in 61.20 seconds. Complete one-row page walks retain
empty/unmanaged repositories and exact publication/run identities. The independent
security/example selection passed 19 tests in 3.23 seconds, covering all 34
registered method/path pairs (33 with interactive docs disabled), bad bearers
before body receive, mixed roles without admission, five strict TOML loaders,
14 current interface documents/anchors, and a fresh disabled app process with no
MCP import or filesystem creation. Source owners report Ruff/format/Pyrefly and
whitespace clean. These focused checks do not replace the required full gate.

Fresh compatibility command
`rtk uv run --locked --extra server python .scratch/api-016-drill.py` exited 0.
Actual isolated installed predecessor `9ba89cf` and current working-tree base
wheels both report application 0.1.10, with distinct wheel hashes retained in
`.scratch/api-016-compatibility/result.json` and commands in `commands.log`.
Seven families (archive/server/client TOML, receipt/event/result-reference JSON,
scheduled ObservationFile), schema 1/future 2 and both binaries produce 28 cases:
schema 1 reads, future 2 refuses, all input bytes unchanged. Only disposable owned
state/lock fixtures were used; no daemon/listener/network/archive operation or
production installation. The predecessor is a feature commit, not a release cut.

Reviewed INV-003/006/010/011/012–014, framework/credential/FS/TX constraints and
ADRs 113/118/121/122. Decision 123 narrowly amends request-local transport
projection; operation/admitted policy/domain result identities and all durable
formats remain unchanged. Current availability, source enforcement links,
concrete matrix evidence and five example loaders are reconciled. Historical
operations/recovery aliases and captured results remain explicitly historical;
current reconnect examples quote keys after `--`. Actual installed systemd,
cgroup/no-IP/no-credential/custom-path masks, browser/PAM, SELinux/NFS and drain/
rollback probes remain operator deployment holds, not repository blockers.
No MCP dependency/import/research implementation begins before this gate commits.

## Completion evidence

Completed 2026-10-18, this commit. All 29 baseline semantic modes have concrete
CLI/API function evidence and static selected-parameter checks. Independent
security inventory covers all 34 actual method/path pairs (33 without interactive
docs), authentication before body receive and mixed read/write roles. Real
Unix/TCP fixtures and the locked Uvicorn implementation prove the corroborated
native transport predicate, request-local links and deterministic copied schema
views without weakening TCP prefix/proxy checks. Complete one-row page walks
retain empty/unmanaged entries and exact publication/run/operation identities.

Required first-attempt full command
`rtk proxy bash scripts/check.sh --with-build > .scratch/api-016-gate.log 2>&1`
exited 0: lock/sync, 368 formatted Python files, Ruff clean, Pyrefly 0 errors
(11 suppressed, 57 warnings not shown); 3,324 default Python tests passed,
40 deselected, in 358.69 seconds. Built source distribution and wheel 0.1.10;
actual locked isolated base/server installation/import/help/version checks passed.
Complete Cockpit ESLint/Stylelint/TypeScript, 127 tests in 2.134 seconds and
production build in 1,224 ms passed. Required extra wheel smoke passed 4 tests,
3,360 deselected, in 4.48 seconds. No full-gate correction, restart or post-gate
source change. Final parsed matrix/current-interface anchor selection additionally
passed 63 tests in 1.89 seconds before the full gate. Focused results and the
fresh 28-case actual installed old/current parser drill are recorded above.

Reviewed INV-003/006/010/011/012–014 and affected framework/authority/FS/TX rules;
decision 123 and amendments to 113/118/121/122 preserve shared domain algorithms,
credential separation, admitted policy/result identity and no-replay semantics.
Current availability, concrete enforcement references, five packaged examples,
README/Unreleased and historical/current runbook boundaries agree. No dependency,
configuration or durable schema change. Final local links/anchors, task/current/
dependency records, all 29 implemented parity rows, 123 unique indexed decision/
ADR records and whitespace pass; see the completed [progress audit](../../progress.md).

The REST repository acceptance boundary is complete. Current selects MCP-001
pending; no MCP dependency, import, endpoint, tool or research implementation was
added. MCP-001 cannot activate until this API-016 commit exists. Live Hub/NFS and
actual installed-host systemd/cgroup/no-IP/no-credential/custom-path/browser/PAM/
SELinux/drain/rollback/verify-calendar checks were not performed; Operator handoff
items 16/17 remain deployment prerequisites. No production operation, installation,
deployment, push, merge or tag occurred.
