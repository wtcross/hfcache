# MCP-004: Complete MCP client guidance and the read-only acceptance gate

| Field | Value |
| --- | --- |
| Work package | `MCP-004` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [MCP-003](mcp-003-mcp-security-and-side-effect-tests.md) |
| Phase | 4 — Read-only MCP |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `MCP-004: document MCP clients and pass read-only acceptance` |

## Scope and acceptance

1. Provide a tested example client/setup using the locked FastMCP version and a protected credential file or explicitly supported secret mechanism. Do not put a real/static sample bearer in committed JSON, command arguments, URLs, or browser storage. Explain token acquisition is operator provisioning, not OAuth discovery.
2. Finish tool/reference documentation, expected resource costs and response limits, private/gated whole-archive trust boundary, exact publication locators, version/session compatibility, rotation/reconnect, disabled behavior, and troubleshooting.
3. Validate server packaging with REST alone and REST+MCP, ensuring optional MCP cannot alter REST auth/lifecycle or give the verification executor any credential. Keep worker egress and systemd timer policies intact.
4. Run the full MCP gate and REST regressions. Record actual mounted-HTTP evidence and remaining operator-only TLS/firewall/hardening checks, rather than suggesting unit tests proved host security. Fix in-scope issues in fresh coherent packages if necessary before marking complete.

## Contracts, invariants, and ADRs

All MCP/interface security invariants and `INV-010`/`INV-011`; plan §12 MCP gate.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Complete MCP, server, API-client/consumer cross-references, README, CHANGELOG, security/invariants, relevant ADR index/statuses, and agent context routing. Add no unrelated backlog to the plan.

## Validation

Planned checks, not execution evidence:

Complete registered-tool and mounted HTTP suites, example execution against a throwaway server, all-extra lock/install/import checks, REST disabled/enabled regressions, docs/schema/link validation, and `scripts/check.sh --with-build` including Cockpit.

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

Activated 2026-10-18 under Tyler's authorized sequential plan after MCP-003
committed clean as `91ca214`. Git history, clean working tree, current selector
and completed dependency agreed; MCP-004 was the sole task in progress. MCP-003's
first full gate passed 3,522 Python tests, all three locked wheel profiles and
127 Cockpit tests. This package owns tested protected-file client guidance,
complete interface/cost/identity/session/rotation/troubleshooting documentation,
packaging/REST isolation acceptance and the required --with-build gate. Root owns
AGENTS.md routing/commands; all other Markdown has one owner. No new role/tool or
architectural decision is selected for unchanged interface acceptance.

Operator-only installed TLS/firewall/socket/credential/worker hardening/NFS/
SELinux/drain/rollback checks remain explicit holds. No production operation,
installation, deployment, push/merge/tag or API-017 implementation is authorized
by this activation. At activation, acceptance and actual gate exit 0 remained pending.

Contract-first example interface is examples/mcp-client.py with explicit canonical
HTTP /mcp/ URL, protected token-file, optional CA/expected archive UUID, bounded
page-size/max-pages/overall timeout, auto/legacy protocol mode and optional typed
repository. It uses explicit StreamableHttpTransport rather than executable
inference, verified trust/no redirect/proxy, credential registration before
network, 16 MiB response cap and stable archive/policy/cursor/header identity.
Repository/current/both-manifest walks return discovery_summary counts only;
success 0 and fixed safe failure 1 are not domain Envelope/receipt outcomes.
No archive mount/config or Hub/REST credential is used. Documentation covers
operator provisioning, distinct whole-archive restricted metadata authority,
independent schemas, stateless reconnect, restart-only rotation, actual resource
costs and classified troubleshooting, with no complete-artifact/promotion claim.

Root's AGENTS.md command/context routing and README developer commands select
locked implemented extras; production profiles stay separately selected. Current
server/API/invariant and Unreleased availability drift is reconciled without
rewriting historical ADR/task evidence. Decisions 124/125, AD-21 and INV-002/003/
008/010/011/012/013/016 remain the governing choices; no new ADR is needed for
unchanged-interface guidance and acceptance. All source/test owners released
before the gate. Positive example command
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_mcp_client.py -q -x`
passed 6 in 9.06 seconds: auto/legacy × actual HTTP/verified custom-CA TLS,
actual documented script subprocess with exact discovery_summary/no token,
fixed help/argument errors and legitimate sorted duplicate dependency keys.
Fresh uv build and all three actual locked wheel profiles pass, now including
exact nine tools and zero resources/templates/prompts in the enabled factory.

`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_mcp_acceptance.py tests/unit/test_mcp_client_security.py -q`
passed 88 in 4.46 seconds (5 acceptance and 83 negative example cases). REST
OpenAPI/auth/complete 34-route roles and real reader/writer commands match with
MCP disabled/enabled. Protected-file replacement stays inert until restart;
rotation changes only MCP authority. Default packaging leaves MCP off, never
imports its credential into the worker and preserves no-IP/timer policy. Negative
client proofs cover setup/source/wire/UUID/identity/cursor/schema/count/locator/
size/deadline/redirect/trust/diagnostic containment and logging restoration.
No runtime backend/role/schema/dependency change is involved. Actual required
full-gate acceptance follows.

## Completion evidence

Completed 2026-10-18, this commit. The protected-file runnable example and complete
client guidance exercise the existing optional metadata interface without adding
server/domain authority. Explicit HTTP transport avoids executable inference;
protected credentials register before network, verified TLS/optional CA remains,
and redirect/ambient proxy/credential fallback is disabled. One overall deadline,
16 MiB response cap and finite total tool-read budget preserve bounded discovery.
Strict versions/archive/policy/current/reference/manifest identity, both projection
headers/counts and cursor continuity refuse inconsistent or unfinished walks.
Output is discovery_summary counts with success 0 or fixed safe failure 1, never
a domain Envelope, receipt, payload transfer or complete manifest. Legitimate
sorted duplicate dependency keys remain valid; no false uniqueness assumption.

Positive command
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_mcp_client.py -q -x`
passed 6 in 9.06 seconds: auto/legacy × real HTTP/verified custom-CA TLS, actual
documented script subprocess with exact summary/no credential, safe help/errors
and duplicate dependency observations. Negative/packaging command
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_mcp_acceptance.py tests/unit/test_mcp_client_security.py -q`
passed 88 in 4.46 seconds (5 acceptance, 83 negative client). Setup/protected source
refusal precedes network; malformed wire/versions, changing UUID/fingerprint,
cursor cycles/incomplete walks, unsafe locators/counts/projections, deadlines,
oversized/lying streams, trust/redirect and raw descendant diagnostics fail safely
without credential/private-value echo. Logger state restores. Exact 34-route
REST role/auth/OpenAPI and real reader plan/writer sync/history behavior match
with MCP off/on. File replacement is inert until restart; rotation changes only
MCP auth. Default off/profile/unit/credential-free no-IP worker/API-backed timer
policy remains; host enforcement is not inferred.

Anchor/parity command
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_rest_examples_gate.py::test_current_interface_documentation_has_resolvable_local_files_and_anchors tests/unit/test_rest_parity_gate.py -q`
passed 63 in 1.03 seconds before freeze. Root's AGENTS.md context/locked-extra
commands and README developer commands agree. The record/link audit includes
AGENTS and all affected current client/server/API/config/security/consumer/MCP/
invariant/ADR/README/Unreleased guidance. Stale living availability wording is
corrected; historical decisions/tasks remain intact.

First required full
`rtk proxy bash scripts/check.sh --with-build > .scratch/mcp-004-gate.log 2>&1`
exited 0: 94-package lock/both-extra sync, 387 formatted files, Ruff clean,
whole Pyrefly 0 errors (11 suppressed, 59 warnings not shown); 3,616 Python tests
passed, 40 deselected in 425.94 seconds. Source distribution/wheel 0.1.10 built;
all three actual locked isolated base/server/server+MCP install/import/help/version
profiles passed, including enabled exact-nine tools and zero resources/templates/
prompts. Cockpit ESLint/Stylelint/TypeScript, 127 tests in 2.141 seconds and
production build in 1,268 ms passed. Required extra wheel smoke subset passed
4 tests, 3,652 deselected in 5.66 seconds. No full-gate failure/correction/restart
or post-freeze source/semantic change. Source version 0.1.10 is unchanged metadata,
not a release cut or tag.

Reviewed AD-21, decisions 124/125, INV-002/003/008/010/011/012/013/016 and existing
transport/read-only/publication/report/source boundaries. ADR/index evidence and
current invariant guidance retain the accepted decisions; no placeholder ADR or
new tool/role/backend/dependency/config/durable format is introduced. No format
compatibility drill is required for these unchanged formats. Final local links/
anchors, current/task/dependencies, unchanged 29 REST modes, 125 unique indexed
decisions and whitespace pass; see the completed [progress audit](../../progress.md).

MCP repository acceptance is complete; current selects API-017 pending after this
commit. Final integration/closure is separate and not activated here. Live Hub/NFS
were not run; the required build-marked wheel subset was. No installed socket/
firewall/TLS/credential-delivery/rotation, worker egress/source masks/cgroup/custom
paths, SELinux/NFS/browser/PAM or real drain/rollback/verify-calendar acceptance
is claimed. Operator holds 16–18 remain explicit. No production archive/service
operation, installation, deployment, push, merge, tag or version bump occurred.
