# MCP-001: Mount optional authenticated FastMCP after REST acceptance

| Field | Value |
| --- | --- |
| Work package | `MCP-001` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-016](api-016-rest-acceptance-gate.md) |
| Phase | 4 — Read-only MCP |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `MCP-001: mount optional authenticated FastMCP transport` |

## Scope and acceptance

1. Confirm API-016 is completed with actual evidence before adding any MCP code or runtime dependency. Resolve standalone FastMCP for Python 3.14, record its material dependency decision, add the `mcp` extra, update lock/gate/wheel coverage, and preserve base/REST-only installs.
2. Add an optional server setting and mount FastMCP Streamable HTTP at `/mcp` in the same FastAPI process. Compose REST and MCP lifespans in the verified startup/shutdown order; no second Uvicorn process or nested event loop. Disabled MCP must require neither its credential nor importable package.
3. Implement a production token-verifier adapter over shared protected opaque-token validation, restricted to the distinct MCP reader credential. Missing credential when enabled fails closed; REST writer/read tokens do not grant MCP access and MCP credentials never grant REST write access.
4. Verify actual mounted-path auth/session behavior, supported Host/Origin controls, and path-prefix handling using the locked version. Document static bearer as a pre-provisioned internal-client model, not OAuth discovery. Do not use development-only StaticTokenVerifier in production.

## Contracts, invariants, and ADRs

`FW-03`/`FW-04`, `AD-21`, `INV-002`/`INV-003`, new MCP exposure invariants; plan §8.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Create `docs/mcp.md` for enablement, credential boundary, transport/path/lifespan, and client limitations. Update server/security/configuration docs, dependency ADR/index, README extras, and Unreleased notes as functionality lands.

## Validation

Planned checks, not execution evidence:

REST suite with MCP absent/disabled/enabled; combined lifespan order and teardown; mounted HTTP handshake with valid/missing/wrong-role bearer; session identity/path-prefix behavior; extra-specific wheel tests and import isolation. Use an actual streaming-capable HTTP test transport. Run `scripts/check.sh`.

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
completed API-016 committed as `07ff468`. Git/current/dependency evidence was
reconciled with a clean tree. The required fresh REST `--with-build` gate exited
0 with 3,324 default Python tests, four extra wheel smokes and 127 Cockpit tests;
MCP implementation begins only after that committed boundary. MCP-001 was the
sole task in progress at activation. Collaborators own optional dependency/install isolation,
transport/lifespan integration and actual streaming HTTP/auth tests; all Markdown
belongs to this package. Decision 124 follows the actual log.

Contract-first work preserves one FastAPI/Uvicorn app and the existing REST
lifespan, shared protected credentials and distinct MCP-reader authority. Disabled
MCP must neither import its package nor require its credential. Production auth
uses the supported verifier extension, never a development static verifier.
This package mounts the authenticated transport only; curated tools belong to
MCP-002. No archive/config/durable operation format, command execution, production
operation, deployment, push/merge/tag or installed-host acceptance is authorized.
Exact supported API/version, path/session/bounds and acceptance evidence are
recorded below.
Operator-only deployment checks remain explicit holds.

Resolved dependency profile: standalone FastMCP/fastmcp-slim 4.1.1, MCP/mcp-types
2.3.0, HTTPX2/HTTPCore2 2.13.1 on CPython 3.14.6. Optional `fastmcp>=4.1.1,<5`
adds 53 packages to the 94-package lock without changing existing versions.
Official mounting/token-verifier/HTTP docs and installed signatures were checked.
Root owns explicit build/stage-only installer `--with-mcp`, locked default gate
with both implemented extras and actual base/server/server+MCP install isolation.
Default units still import no MCP credential; named source delivery needs an
explicit API-service drop-in or protected-file source, never worker delivery.

Query's settled transport uses public `http_app(path="/", stateless_http=True)`
under normal `/mcp` Mount, canonical `/mcp/`, with an authenticated safe relative
307 only after shared transport/body/query checks. Stateless mode retains no
legacy sessions/resumption; SDK POST/DELETE and authenticated GET method refusal
remain protocol behavior, never job admission. Outer registry and production
supported verifier both enforce the MCP-reader class on every request. Exact
framing/resource limits and streaming/lifecycle evidence are recorded below.

Current source provides `hfcache.mcp.OpaqueTokenVerifier/create_mcp_app/
BoundedMCPTransport/mcp_diagnostics`, shared boundary `project_path` and explicit
nested lifespan composition. Stateless `json_response=True` replies are buffered,
registered-secret sanitized and capped before headers; deferred overflow refusal
preserves HTTP 413 outside SDK exception interception. MCP queries are forbidden,
POST uses shared strict bounded JSON, other methods require empty bodies, and a
separate in-flight ceiling equals metadata workers plus pending capacity, reserved
after authentication before body collection and released through response/
disconnect/failure. One
trusted projection handles public/native interface collisions for auth/writer/
body/root/links. SDK warning/error logs use new closed-vocabulary warning
`mcp.diagnostic` through ordinary emit/correlation, with `sdk_level`, bounded
sanitized `sdk_logger` and fixed text, never formatted SDK message/args/exception;
original handlers restore and lower levels are suppressed.
Decision 64 and original plan §24 carry dated amendments.

Root's test-only public MockTransport-to-TestClient response bridge accommodates
Starlette selecting HTTPX2 when the MCP extra is installed; the runtime base
transport is unchanged. Final focused CLI read/write/verification regression:
154 passed in 60.20 seconds. All 40 release installer cases passed in 30.36 seconds,
including explicit profile, no-write dry-run, refused switch/list and real
import/synthetic-policy smoke. Fresh built wheel and all three actual locked
isolated profiles (base/server/server+MCP) pass presence, cold CLI imports,
help/version and supported auth/module imports. Optional imports with warnings as
errors pass; root scripts syntax/Ruff/whole Pyrefly are green. Integrated
mount/direct transport/logging/protected-auth selection passed 224 in 11.27
seconds before the final route-collision cases; these focused results do not
replace the full gate. Actual streaming/auth/lifecycle and final gate evidence follow below.

Final mounted malformed-protocol regression exposed SDK/Pydantic rejected-value
echoes before gate freeze. The fix projects JSON-RPC errors to integer code/fixed
message, drops raw SDK data/details and never formats raw SDK diagnostic messages,
args or exceptions. Success values retain registered-secret sanitization; unsafe
registered numeric identities refuse safely. Final direct+actual mounted selection
passed 63 tests in 10.25 seconds. Root added the new MCP page to the existing
15-interface anchor audit; example/docs/cold-disabled selection passed 7 in
1.34 seconds. These are pre-gate findings/corrections, not a failed full gate.

## Completion evidence

Completed 2026-10-18, this commit. After committed REST acceptance, optional
standalone FastMCP 4.1.1 mounts canonical `/mcp/` in the same app/lifespan with
shared protected production MCP-only verification. Disabled mode imports/resolves
neither package nor credential. Stateless finite JSON has no retained legacy
session/resumption store; every method authenticates and no tool/resources/prompts
or command/job path is registered. Trusted interface projection handles public/
native prefix collisions; safe alias redirect, strict body/query policy, pre-body
capacity reservation, bounded sanitized replies and fixed SDK error/diagnostic
projection preserve transport and secret boundaries. REST enters first, MCP exits
first, and startup failure unwinds ownership. Existing archive/config/durable
schemas and domain algorithms are unchanged.

Final actual mounted command
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_mcp_transport.py -q -x`
passed 51 cases in 10.78 seconds; repeated-slash refusal's narrow rerun passed in
2.06 seconds. Final direct+mounted selection passed 63 in 10.25 seconds, covering
production verifier, composed ownership, slow bodies, SDK overflow and rejected-
value containment. REST regression passed 113 in 17.97 seconds; root CLI selection
154 in 60.20 seconds and all 40 installer cases in 30.36 seconds. Strict examples/
15-interface anchors/cold-disabled selection passed 7 in 1.34 seconds; final
parsed matrix/anchor selection passed 63 in 1.02 seconds before the full gate.
Actual fresh locked wheel profiles prove base/server/server+MCP isolation, cold
CLI imports/help/version and supported production auth imports. Server-only
factory remains cold when disabled and refuses enabled missing optional runtime
with HFCFG005; server+MCP enabled factory mounts `/mcp` without credential/state
path creation before lifespan startup. No format migration/drill is needed for
this unchanged existing config slot; rollback must deliberately disable MCP.

First full `rtk proxy bash scripts/check.sh > .scratch/mcp-001-gate.log 2>&1`
exited 1 at Python: 9 failed, 3,385 passed, 40 deselected in 380.11 seconds.
These were test-only HTTPX/HTTPX2 private-transport borrowing in eight CLI observer
cases and scheduled observer restart. Root extracted/reused the existing public
ApiCli exchange; zero private borrowers remain. All 79 focused cases passed in
6.80 seconds while preserving signal/timeout/lost-ack/detach/key/restart and
no-second-POST assertions. No runtime/semantic change was needed; original failed
log remains intact. Build/install/Cockpit stages were not reached on that attempt.

Definitive full rerun
`rtk proxy bash scripts/check.sh > .scratch/mcp-001-gate-rerun.log 2>&1`
exited 0: 94-package lock and both-extra sync, 373 formatted files, Ruff clean,
Pyrefly 0 errors (11 suppressed, 59 warnings not shown); 3,394 Python tests passed,
40 deselected in 377.89 seconds. Source distribution/wheel 0.1.10 built; actual
locked isolated base/server/server+MCP installation/import/help/version checks
passed. Complete Cockpit ESLint/Stylelint/TypeScript, 127 tests in 2.152 seconds
and production build in 1,203 ms passed. No post-definitive-gate source change.

Reviewed FW-03/04, AD-21, INV-002/003/012–016, correlation/logging and previous
108/112/113/123 decisions. Decision 124 and 064/framework/AD-21/predecessor
amendments, original plan §24, active plan, MCP/server/API/config/security/CLI/
release guidance, README and Unreleased agree. The 53 optional package additions
preserve existing versions. Explicit installer `--with-mcp` selects build/stage
only, defaults server-only and never provisions/enables auth or changes services.
Named MCP credential delivery requires an explicit API-service drop-in or
protected-file source, never private worker delivery. No workflow/state authority
is introduced. Final local links/anchors, task/current/dependencies, unchanged
29 REST modes, 124 unique indexed decision/ADR records and whitespace pass;
see the completed [progress audit](../../progress.md).

Current selects MCP-002 pending after this package's commit. Actual tools and
their per-tool side-effect proof remain that task; no later-task implementation
has begun. Live Hub/NFS and extra build-marker suites were not run. Existing
systemd/cgroup/no-IP/credential masks/custom paths/browser/PAM/SELinux/drain/
rollback/verify-calendar acceptance and new MCP enablement checks remain operator
holds (handoff 16–18), not asserted passes. No production operation, installation,
deployment, push, merge or tag occurred.
