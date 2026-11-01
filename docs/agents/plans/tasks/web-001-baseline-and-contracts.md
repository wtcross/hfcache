# WEB-001: Activate the reviewed scope and resolve contracts

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `ef98d734cc68925fd5620e50ffe52cc1a0e354d72f0c78823bdb40068bea9a5f`,
original content SHA-256 `73fdfb5fbb047f68bef717ccd0ccd05cfe23a538d9a548ef710e0ae44ab96e02`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P0 |
| Depends on | None |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-001: activate web contracts and stabilize baseline framing` |

## Read before implementation

AGENTS.md; docs/agents/planning.md, workflow.md, invariants.md, environment.md; current selector and relevant progress/handoff; docs/invariants.md and the ADR topic index; all bundle support specifications.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Reconcile git history, dirty/untracked work and current plan selection. Treat newly extracted bundle files as intended plan additions, not disposable noise. Create/resume feat/web-ui without resetting or overwriting unrelated work. The issued kickoff is implementation/activation authority; record it, activate this dated plan, select this task, and deliberately establish WEB as the work-package family after checking ID collisions. Do not invent a second task numbering sequence.

## Unit and component validation

Validate bundle task IDs, dependency graph, reciprocal plan/task links and schema of machine-readable indexes. Run existing documentation validators and tests for relevant route/schema/architecture contracts before changing them.

## Integration validation

## Functional validation

Inventory exact functional prerequisites without contacting production managers or archive. Record browser/Caddy/guest/image availability and the safe provisioning path. Functional feature tests are not yet possible; this task may complete with an explicitly tracked later infrastructure dependency, but final/retirement gates may not waive it.

## Human documentation deliverables

Create docs/web-ui/README.md as a truthful introduction/status page and update the human docs index. Update affected standing contracts and ADRs for accepted design changes. Do not claim the new UI is installed or operational.

## Acceptance

An active plan/current selector/branch exist consistently; task IDs are collision-free; architecture choices and exact API delta are resolved; real baseline evidence and prerequisite blockers are recorded; no production changes or remote publication occurred.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

Activated 2026-10-20 by the explicit implementation instruction. HEAD is exactly
the reviewed `6b8fae2e0997403ae5c716a2e92148af0a972af9`; only the intended
untracked bundle existed. The inactive selector displaced no plan. No existing
WEB work-package IDs or `feat/web-ui` branch existed; the branch was created
without resetting source. The retained rollout/browser/NAS holds remain separate.

Contract, acceptance-index and safe prerequisite audits collaborate within this
package; later tasks remain pending. No production manager, archive, credential
or remote has been accessed.

The first complete feature-tree gate passed 5308 Python tests, all three
installation profiles, 570 historical frontend unit tests, 110 mounted Firefox tests and the
production build. Log `.scratch/web-001-final-gate.log`, SHA256
`218296edd6230711e04ca333fa62321a2669495707aba8980961b5f502562112`.
It still contained the intermittent baseline defect, so it does not waive that
failure. Focused repetition failed again at attempt 15; actual-helper xtrace and
a shell-only reproduction localized the second builtin-only process-substitution
wait returning `-1` on Bash 5.2.26, before files/locks/managers. The correction
uses bounded in-memory splitting/exact frame reconstruction while retaining all
external I/O completion, base64/UTF-8/size and pre-effect checks. A deterministic
actual-guard injection fails old source and passes the correction; malformed
frames remain refused. The detached baseline stays unchanged.

The corrected full gate exits 0 at `.scratch/web-001-corrected-gate.log`.
Source regression/performance and final documentation checks pass. No functional
web acceptance, installed-host fix or historical frontend retirement is claimed. Next task
is WEB-002; later browser/installed closure remains required, not waived.

## Completion evidence

Evidence recorded on 2026-10-20 for WEB-001, this commit (parent exactly
`6b8fae2e0997403ae5c716a2e92148af0a972af9`). Acceptance for this baseline/contracts
package passes; no web feature acceptance is claimed.
