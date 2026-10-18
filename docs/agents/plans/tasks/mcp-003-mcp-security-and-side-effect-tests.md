# MCP-003: Prove MCP cannot mutate through tools, auth, or transport bypasses

| Field | Value |
| --- | --- |
| Work package | `MCP-003` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [MCP-002](mcp-002-curated-read-only-tools.md) |
| Phase | 4 — Read-only MCP |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `MCP-003: prove mounted MCP authentication and read-only behavior` |

## Scope and acceptance

1. Test the mounted `/mcp` HTTP application through the parent FastAPI middleware/lifespan, not just direct tool calls. Cover supported streaming/session requests, missing/invalid credentials, cross-class credentials, replayed session identity, proxy-prefix/Host/Origin handling, malformed input, and shutdown during active reads.
2. Attempt writer command names and mutation-shaped arguments against every registered tool and any resource/prompt handlers. Assert the exact exposed registry, no hidden OpenAPI-generated write operations, no generic invocation capability, and no REST write access with an MCP bearer.
3. For each valid and invalid tool call, compare archive refs/manifests/content/catalogs/runs/transactions and API operation-state files before/after. Reads must create no reports, jobs, directories, locks, caches, or recovered artifacts; access logs are the documented exception. Inspect paths/content/modes rather than treating filesystem atime changes as application writes.
4. Exercise concurrent MCP reads during fake long REST sync/verification, large-page bounds, cancellation, and malformed upstream evidence. Verify no event-loop starvation, cross-request IDs, token leakage, or false verification confidence.

## Contracts, invariants, and ADRs

`INV-002`/`INV-003`/`INV-007`/`INV-010`, MCP allowlist/no-side-effect invariants; plan §§8, 12.

Use the [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Add a threat/control/test traceability section to MCP/security docs and record residual deployment assumptions. Update any incorrect transport/client examples found by mounted-boundary tests.

## Validation

Planned checks, not execution evidence:

Mounted streaming transport integration, route/registry authorization matrix, filesystem and service-state snapshots, adversarial tool arguments, secret scans over logs/errors/responses, concurrent mixed-interface tests, disabled-mode regression, and `scripts/check.sh`.

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

Activated 2026-10-18 under Tyler's authorized REST-first implementation after
MCP-002 committed clean as `35e5f51`. Git history, clean tree, current selector and
completed dependency agreed; MCP-003 was the sole task in progress. MCP-002's first
full gate passed 3,481 Python tests, all three locked wheel profiles and 127
Cockpit tests. Collaborators remain within this package: malformed original
evidence/secret projections, mounted transport/concurrency, adversarial exact
registry/arguments/state snapshots, and all Markdown traceability.

The existing nine-tool/auth/transport/read-only contracts govern these proofs.
No new decision is needed for tests of unchanged behavior; a concrete behavior
change must receive its own contract review before implementation. Tests and
threat/control mapping distinguish application-side no-write proof from real
installed-host enforcement. At activation, gate evidence/completion remained pending;
MCP-004/API-017 and production operations are not authorized by this activation.

The normative MCP/security threat/control map requires parent-lifespan mounted
HTTP proof, exact registry/closed arguments, complete post-startup path/content/
mode snapshots for each valid/invalid read, malformed evidence/confidence/secret
containment, finite mixed-interface work and cancellation/drain ownership.
Operational logs are the documented exception, atime is excluded, and authorized
concurrent REST mutations must not be misattributed to MCP. Existing 124/125,
AD-21 and INV-002/003/007/010/016 are reviewed; no policy or durable/dependency
change is selected. Root released test_mcp_security_evidence.py: 25 cases passed
in 6.50 seconds,
covering all three original report families against seven corruption classes,
numeric-secret cursor substitution, string/numeric mounted report containment
and unexpected reader masking. Initial focused collection lacked the explicit
socket_policy fixture import; that test-only setup correction preceded the actual
proof run. Ruff/format and scoped Pyrefly pass; no runtime source changed.
Mounted review found the locked SDK ignores legacy top-level params.task on a
valid allowlisted call and performs an ordinary finite synchronous read. The
proof records no task handle/retained task/job/admission/state effect, while
unsupported task RPCs and mutation-shaped tool arguments refuse. Existing
contracts require no background authority, not blanket rejection of every
optional SDK field; this is characterization, not a runtime change/new decision.
Final closed-authority test command
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_mcp_security.py -x -q`
passed 12 in 9.84 seconds, with 9 tools × 17 mutation field sets, writer/generic/
OpenAPI/hashed aliases, empty resource/template/prompt registries and unsupported
read/get/task/generic RPCs. Every call snapshots the whole fixture parent,
including archive/control/config/credential/runtime siblings, and has explicit
admission/writer/Hub/credential/probe/archive-byte-hash tripwires and output/log secret scans.

New concurrency tests passed 4 in 4.52 seconds: sync/verification modes use real
fake-Hub sync and the actual framed private VerificationWorker; five overlapping
MCP reads preserve archive/API/private-worker state while the REST domain is
paused, with distinct correlation and no additional authority. Cancellation and
shutdown preserve state. The supported streaming observer detaches while the
server conservatively retains both transport request slot and metadata-worker
lease until actual completion; composed shutdown may join at MCP before the
REST pool closes. Ordinary lifespan ownership is retained, not transferred to
an unrelated task. No runtime source changed. Actual gate evidence follows;
installed-host checks remain explicit residual assumptions.

## Completion evidence

Completed 2026-10-18, this commit. Parent-lifespan mounted tests prove the existing
nine-tool/read-only/authentication boundary rather than adding runtime behavior.
The normative MCP threat/control map resolves 27 concrete test functions, with
security cross-mapping, snapshot/concurrency method and residual assumptions.
Every valid/invalid read compares full post-startup fixture paths/content/modes,
including archive/API/private-worker state and config/credential/runtime siblings.
Operational logs are the documented exception; atime is not an application write.
Controlled concurrent REST mutations remain attributable to their command.

Root malformed-evidence selection passed 25 in 6.50 seconds: three report types
against JSON/version/run/archive/time/symlink/duplicate damage, numeric registered-
secret cursor binding, string/numeric mounted report containment and unexpected
reader masking. Malformed original evidence and all control state are preserved,
without repair/report/job/confidence creation. Initial focused collection needed
an explicit socket_policy fixture import; that test-only setup correction came
before the successful proof run and was not a failed full gate. String secrets
redact; unsafe numeric output safely refuses HFAPI008/HTTP 500. Neither wire nor
captured diagnostics exposes rejected private input or bearer values.

`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_mcp_security.py -x -q`
passed 12 in 9.84 seconds. All nine tools reject 17 mutation-shaped argument sets;
writer/generic/OpenAPI/hashed aliases, resource/template/prompt handlers and
unsupported task/generic RPCs grant no hidden authority. Explicit admission/
command/Hub/credential/probe/archive-byte-hash tripwires and whole-parent state
snapshots cover each call. The locked SDK's ignored optional legacy params.task
performs only the same finite synchronous approved read, returning no task handle,
retained task/job/admission or write. That is unchanged safe behavior, not a claim
that every optional SDK protocol field refuses. Archive-byte hash tripwires do
not prohibit cursor hashing of sanitized metadata or authentication digests.

`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_mcp_concurrency.py -q -x`
passed 4 in 4.52 seconds. Fake-Hub sync and actual framed private verification keep
the common lock while five parallel MCP reads preserve full three-root state,
remain responsive and retain distinct request/run/operation correlation with no
extra jobs/Hub/credential/verification calls or false confidence. Cancellation
and shutdown preserve state. A detached streaming observer can leave both the
transport slot and worker lease owned until actual completion; composed drain
may join at MCP before closing the REST pool. Lifespan ownership stays on its
normal task, and worker context restores without cross-request IDs.

Documentation anchor/parity command
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_rest_examples_gate.py::test_current_interface_documentation_has_resolvable_local_files_and_anchors tests/unit/test_rest_parity_gate.py -q`
passed 63 in 1.04 seconds before semantic freeze. Read-only AST validation resolves
all 27 mapped functions without importing their modules. Existing actual TCP/Unix/
streaming/session/class/prefix/Host/Origin/body/capacity/disabled/lifespan tests
also remain in the required full suite; ordinary direct SDK calls alone are not
the authentication proof.

First full
`rtk proxy bash scripts/check.sh > .scratch/mcp-003-gate.log 2>&1`
exited 0: 94-package lock/both-extra sync, 383 formatted files, Ruff clean,
whole Pyrefly 0 errors (11 suppressed, 59 warnings not shown); 3,522 Python tests
passed, 40 deselected in 417.54 seconds. Source distribution/wheel 0.1.10 built;
all actual locked isolated base/server/server+MCP installation/import/help/version
checks passed. Cockpit ESLint/Stylelint/TypeScript, 127 tests in 2.112 seconds
and production build in 1,234 ms passed. No full-gate failure/correction/restart,
runtime source change or new dependency/config/durable format.

Reviewed AD-21, decisions 124/125 and INV-002/003/007/010/016. Evidence links and
MCP/security traceability amend those records without changing the architectural
choice or creating a placeholder decision. Corrected stale executor/profile
availability descriptions; current INV-010 lists all three locked wheel profiles.
No domain algorithm, FS/TX rule, whole-archive role or consumer promotion authority
changes. No compatibility drill is required for unchanged formats. Final records/
links/current/dependencies, unchanged 29 REST modes, 125 unique indexed decisions,
27 mapped functions and whitespace pass; see the completed
[progress audit](../../progress.md).

Current selects MCP-004 pending after this package's commit; final MCP/API-017
acceptance remains separate. Live Hub/NFS and extra build-marker suites were not
run. The narrow capability is within the shared API process, not a separate OS
sandbox; unknown arbitrary secrets and dependency/parser/SDK or privileged host
compromise remain outside the proof. Installed TLS/proxy/socket/credential delivery/
rotation, actual worker no-IP/source masks/cgroups/custom paths, SELinux/NFS,
browser/PAM, drain/rollback/verify-calendar and MCP enablement stay operator holds
16–18. No production archive/service operation, installation, deployment, push,
merge or tag occurred.
