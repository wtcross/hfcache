# API-017: Close the plan with integrated evidence and an operator rollout handoff

| Field | Value |
| --- | --- |
| Work package | `API-017` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [MCP-004](mcp-004-mcp-client-docs-and-acceptance.md) |
| Phase | 5 — Closure |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-017: complete REST and MCP integration and operator handoff` |

## Scope and acceptance

1. Review the complete feature-branch diff and incremental commit history. Verify every scoped task is complete or explicitly dispositioned, every behavior change has same-package docs/evidence, and no unintended direct CLI backend, public file server, generic MCP dispatch, secret leak, or unrelated RET-011 fix slipped in.
2. Run full integration across REST writer/read credentials, writer-local and remote-style CLI, systemd wrapper protocols, Cockpit, read-only MCP, interrupted jobs, verification worker isolation, and large results. Re-run the durable/config compatibility drill and document rollback constraints for service-state records.
3. Produce a concrete operator rollout checklist: credentials/permissions, TLS/proxy/firewall, frozen dependencies, server/worker socket units, no-IP worker probe, real NFS/hardening acceptance, drain and rollback, existing client-unit monitoring, and verification timer still disabled. Do not perform these production changes under draft/implementation authority alone.
4. Record all actual gate results and explicitly pending host checks. Close the dated plan and clear only its current active selection. Preserve task/ADR/progress evidence and deliver the local work-package commit series. Do not merge, squash, push, tag, or deploy without separate instruction.

## Contracts, invariants, and ADRs

All affected invariant/ADR sections; `INV-010`/`INV-011`; planning/workflow/environment/release rules; plan §§11–12.

Use the [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Final consistency sweep across newly created and affected docs, with no deferral of earlier packages’ documentation. Complete plan lifecycle/task evidence/progress and Operator handoff links, retaining deployment holds and historical records.

## Validation

Planned checks, not execution evidence:

`scripts/check.sh --with-build` with all implemented extras and the Cockpit toolchain; all real throwaway transport/integration tests; docs/OpenAPI/tool-schema/examples/link checks; no secret artifacts; branch/history/status audit. Explicitly state which opt-in live/NFS/host probes were not run and why.

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

Activated 2026-10-18 under Tyler's authorized sequential plan after MCP-004
committed clean as `f9a96dd`. Git history, clean branch, current selector and
completed dependency agree; API-017 is the sole task in progress. MCP-004's first
required --with-build gate passed 3,616 Python tests, three locked wheel profiles,
127 Cockpit tests and four additional wheel smokes. Root owns the fresh actual
compatibility drill/history/security review; collaborators own integrated/full
acceptance and independent artifacts/docs/invariant audit. Final Markdown has
one owner. Existing environment/release/whole-archive/transport/worker/state and
publication contracts remain binding; no release/version/deployment authority
or unrelated backlog is selected.

The final operator checklist will separate repository acceptance from real
credential/permissions, TLS/proxy/firewall/Unix socket, locked artifact/version,
API/private-worker activation/egress/source masks, NFS/SELinux/hardening,
state-retaining drain/rollback, client monitoring and still-disabled verification
timer acceptance. No host operation, release, tag, push, merge or production
archive work is authorized. Plan/task closure and clearing only this active
selection remain pending all actual required evidence and full gate exit 0.

Final independent audit reconciles all 21 task records (20 completed before this
package), their same-package implementation/tests/docs/progress/current evidence,
REST-before-MCP commits and unchanged domain/FS/TX/RET-011 scope. Lock grows from
37 to 94 packages without changing prior versions. Current wheel/sdist member
scans contain no private key/cert/token/env/.scratch/.venv artifacts; tracked
matches are source/test names and intentional unit-test token constants. No
operational local CLI backend, generic MCP/file server or secret artifact is found.

A real OS CLI subprocess through both actual Unix/TCP listeners exposed a genuine
observer bug before the final gate: event requests fixed at limit 100 failed when
max_page_size or operation_max_events was 1, even after durable sync success.
Correct existing bounded-client behavior by omitting limit for the adaptive
min(100,max_page_size,operation_max_events) default. Drain contiguous retained
pages through empty under the same absolute deadline; the final empty response
counts toward each drain's max_pages. Explicit integer limit/response bounds,
retention gaps, admitted identity and known key/operation handles remain. No new
capability request, role/schema/dependency or architectural decision. ADR 118/120,
client/CLI/invariant wording accompanies the correction.

Final focused command
`rtk proxy uv run --locked --extra server --extra mcp pytest tests/unit/test_interface_integration.py tests/unit/test_rest_examples_gate.py tests/unit/test_api_client.py tests/unit/test_api_client_adversarial.py tests/unit/test_cli_operation_helpers.py tests/unit/test_cli_operations_adversarial.py -q > .scratch/api-017-observer-final.log 2>&1`
passed 176 in 24.54 seconds. Four actual CLI socket/private-worker cases cover
Unix/TCP × one-row/one-retained-event caps, exact successful sync and full verify,
reader metadata/history/writer refusal and no extra operation/leak. Direct helper
cases prove final-empty page budgets and bounded default event responses. Broader
15-file integration passed 375 in 78.05 seconds before the final small-page
regressions. Standalone complete `rtk make -C cockpit check` exited 0; exact test/
build evidence will also be supplied by the required full gate. All source/test
owners are released with format/lint/whole types/whitespace green.

The obsolete unqualified direct-backend quickstart was found and replaced with
useful authenticated API client setup, separate current writer/MCP links and
correct reader diagnostic job semantics. It now belongs to the current-interface
anchor audit. README/deployment provenance distinguish historical observations
from unperformed current rollout. The concrete pending checklist covers separate
credentials/whole-archive scope, deliberate artifact/profile/version, actual
TLS/proxy/firewall/Unix/worker source masks/egress, NFS/SELinux/hardening,
state-retaining drain/rollback/client monitoring and verify timer still disabled.
Handoff 18 now records completed repository MCP acceptance while retaining host
holds; new handoff 19 links all pending rollout checks.

Fresh final-source compatibility command
`rtk proxy uv run --locked --extra server --extra mcp python .scratch/api-017-drill-final.py > .scratch/api-017-compatibility-final.log 2>&1`
exited 0. Owned result/cases/commands are in .scratch/api-017-compatibility-final;
the preliminary 42-case artifacts in .scratch/api-017-compatibility are preserved
but their earlier current-wheel hash is not final evidence. Final 42 cases use
actual installed Python readers: predecessor 9ba89cf and the final API-017 working
tree based on f9a96dd each read seven schema 1 families and refuse seven future 2
variants (28 cases). Pre-feature 86f6e8b reads archive-config 1/refuses archive-config 2;
its six new service/config readers are absent for both versions (12 unavailable
cases, not schema-aware success/refusal). Families are archive/server/client TOML,
receipt/event/result-reference JSON and private scheduled handle. All record bytes
remain unchanged; only owned fixture state/locks are involved, with no archive,
credential, network, listener or daemon operation.

All three application metadata versions remain 0.1.10, but artifacts differ:

| Installed binary | Wheel SHA-256 |
| --- | --- |
| Predecessor feature commit 9ba89cf | c57e8a0c81e8af558210ec75f0e1026dc6ab6d1157de7809e83be5727649e35d |
| Final working tree on f9a96dd | aa59d3d35af3a3f562e16b5f5b9157c0afadbe9d53994f6d2a5f3ae02515e972 |
| Pre-feature baseline 86f6e8b | 5bfc6e07df81e60d7921c6d411789887af2e75a180cd5d12974e547d056e549f |

Final probe SHA-256 is 90762b202ecb9b361909e13d10b9e411d372c5850130c1bafee7f3334806ba7f.
These are feature/baseline artifacts, not a deployed previous-release claim.
Retain both operation stores and scheduled handles through guarded rollback;
unsupported observers/unknown history never prove nonexecution. Disable MCP
before server-only/pre-MCP startup. Final full-gate and closure evidence follows.


## Completion evidence

Completed 2026-10-18, this commit. Final branch/history, current/task/dependency,
contract/invariant/ADR, artifact and integration reviews account for all 21 work
packages in dependency order, including the committed REST acceptance boundary
before any MCP implementation. All task records are completed; the dated plan is
completed and only its active selection is cleared. No unrelated backlog is
activated. Each earlier package retains its own same-commit implementation,
tests, documentation, progress and required gate evidence.

The actual CLI subprocess proof found and corrected the existing fixed event-limit
observer defect before the full gate. Adaptive omitted limits and bounded draining
through empty preserve the exact terminal Envelope, original admitted identity,
explicit limits and safety handles under the same absolute observation deadline.
The final empty response consumes that drain's page budget. Four real Unix/TCP ×
small-page/retained-event cases cover reader roles, exact sync/full verification,
private-worker execution and no duplicate operation. The final focused command
above passed 176 tests in 24.54 seconds; the earlier broad integration selection
passed 375 in 78.05 seconds. Standalone Cockpit check also exited 0. These tests
use disposable fixtures, not installed systemd/cgroup/NFS acceptance.

The final-source installed-reader drill above exited 0 across 42 cases. Preserve
its distinction between 28 supported schema reads/refusals, two baseline archive
schema cases and 12 unavailable baseline readers. All record bytes were preserved.
The recorded wheel/probe hashes identify those tested artifacts; unchanged source
version 0.1.10 is neither byte identity nor a release/tag. Earlier preliminary
artifacts remain separate. No durable/archive/config shape or dependency changed
in this package; rollback retains both operation stores and scheduled evidence,
refuses unsupported observation targets and deliberately disables MCP before
server-only/pre-MCP startup.

First required full command
`rtk proxy bash scripts/check.sh --with-build > .scratch/api-017-gate.log 2>&1`
confirmed actual process exit 0: 94-package lock and both-extra sync, 388 formatted
files, Ruff clean, whole Pyrefly 0 errors (11 suppressed, 59 warnings not shown);
3,624 Python tests passed, 40 deselected in 442.05 seconds. Source distribution
and wheel 0.1.10 built; all three actual locked isolated base/server/server+MCP
installation/import/help/version profiles passed, including the exact-nine
optional registry and no resources/templates/prompts. Cockpit ESLint/Stylelint/
TypeScript passed, 127 tests passed with no failures in 2.110 seconds, and the
production build passed in 1,291 ms. Required additional wheel smoke subset:
4 passed, 3,660 deselected in 5.33 seconds. No full-gate failure, correction or
restart, and no source/semantic-doc change after freeze. The pre-gate observer
defect and its correction remain recorded separately.

The current authenticated quickstart replaces invalid direct-backend instructions
and distinguishes metadata queries from the reader-authorized diagnostic job.
README, Unreleased and deployment provenance distinguish completed local acceptance
from unperformed rollout. Client/CLI/invariant contracts and decisions 118/120
record the observer correction; the 125 indexed decisions and all affected
INV-001–016, AD-21, FS/TX and framework/retention boundaries were reviewed without
a new architectural decision. Archive retention/publication/hashing/transaction/
manifest/path/purge/quarantine algorithms and unrelated RET-011 remain unchanged.
The final interface anchor/parity selection passed 63 tests in 1.07 seconds before
freeze; final local links, task dependencies, all 21 completed records, cleared
current selector, 29 REST modes, decision uniqueness and whitespace pass. See the
completed [progress audit](../../progress.md).

[Rollout checklist](../../../deployment-centos-stream-10.md#17-rest-and-mcp-rollout-checklist-api-017)
and Operator handoff 16–19 retain actual credential delivery/rotation, TLS/proxy/
firewall/Unix activation, worker no-IP/source masks/custom paths/cgroup, NFS/
SELinux/hardening, client monitoring and state-retaining drain/rollback acceptance.
The verification timer stays disabled pending its separate calendar approval.
Live Hub/NFS suites and installed host/browser/PAM probes were not run; the
required build-marked wheel subset was. No production archive/service operation,
installation, release/version bump, tag, push, merge or deployment occurred.
