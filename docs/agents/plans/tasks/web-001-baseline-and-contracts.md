# WEB-001: Activate the reviewed scope and resolve contracts

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

Compare current HEAD to the pinned baseline, re-audit existing REST/Cockpit/host/Caddy surfaces and record any drift in source-review.md. Freeze endpoint additions and configuration managed-edit DTOs, permission model, helper protocol boundary, static asset release model and card schema/capture semantics. Preserve all existing read/write/metadata contracts unless the same package explicitly amends them. Confirm supported native and rootless positive/negative host behavior; avoid turning current rootless denied permissions into a new scheduler project.

Allocate actual ADR numbers from the live index for SPA serving/authentication, narrow privileged administration/config application, card presentation records, frontend dependencies/test gates and eventual Cockpit retirement. Add invariant amendments/new IDs only where justified. Keep future/deferred details labelled proposed until implementation establishes them. Resolve design questions inside authorized scope with documented conservative decisions, not indefinite TODOs. Create human documentation entrypoints and a truthful implementation-status note. Register acceptance case ownership and incremental test delivery. The complete new bundle may be committed with this activation package; every subsequent package updates only its own evidence and affected support records.

## Unit and component validation

Validate bundle task IDs, dependency graph, reciprocal plan/task links and schema of machine-readable indexes. Run existing documentation validators and tests for relevant route/schema/architecture contracts before changing them.

## Integration validation

Run the unchanged repository baseline gate, including strict Cockpit gate where available/required, and record actual results. A baseline failure is fixed in authorized scope or recorded as a blocking dependency; never claim a green baseline from this plan file.

## Functional validation

Inventory exact functional prerequisites without contacting production managers or archive. Record browser/Caddy/guest/image availability and the safe provisioning path. Functional feature tests are not yet possible; this task may complete with an explicitly tracked later infrastructure dependency, but final/retirement gates may not waive it.

## Human documentation deliverables

Create docs/web-ui/README.md as a truthful introduction/status page and update the human docs index. Update affected standing contracts and ADRs for accepted design changes. Do not claim the new UI is installed or operational.

## Acceptance

An active plan/current selector/branch exist consistently; task IDs are collision-free; architecture choices and exact API delta are resolved; real baseline evidence and prerequisite blockers are recorded; no production changes or remote publication occurred.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Activated 2026-10-20 by the explicit implementation instruction. HEAD is exactly
the reviewed `6b8fae2e0997403ae5c716a2e92148af0a972af9`; only the intended
untracked bundle existed. The inactive selector displaced no plan. No existing
WEB work-package IDs or `feat/web-ui` branch existed; the branch was created
without resetting source. The retained rollout/browser/NAS holds remain separate.

Contract, acceptance-index and safe prerequisite audits collaborate within this
package; later tasks remain pending. No production manager, archive, credential
or remote has been accessed.

Validation attempts are retained honestly. The first working-tree invocation
overlapped documentation authoring and failed three transient link/anchor tests
(5296 passed); it is not baseline evidence. Those tests now pass in the focused
86-test plan/documentation selection. An independent detached baseline at
`.scratch/web-baseline` passed all 5299 Python tests, build and three installation
profiles, then failed one of 570 Cockpit unit tests: installed confirmation,
`cockpit/test/candidate-guard.test.ts:227` (expected exit 0, observed guard refusal
1). Log: `.scratch/web-baseline-gate.log`. A focused isolated reproduction passes;
the original failure remains under investigation and is not silently waived.
Supplementary explicit source/test Pyrefly globs pass because the baseline
worktree's ignored parent suppresses its normal project test discovery.

The first complete feature-tree gate passed 5308 Python tests, all three
installation profiles, 570 Cockpit unit tests, 110 mounted Firefox tests and the
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
web acceptance, installed-host fix or Cockpit retirement is claimed. Next task
is WEB-002; later browser/installed closure remains required, not waived.

## Completion evidence

Evidence recorded on 2026-10-20 for WEB-001, this commit (parent exactly
`6b8fae2e0997403ae5c716a2e92148af0a972af9`). Acceptance for this baseline/contracts
package passes; no web feature acceptance is claimed.

- Collision scan `git grep -n -E 'WEB-[0-9]{3}' 6b8fae2... --` returned no
  matches; original branch/selector/bundle state reconciled without reset or loss.
  All 26 task records and 95 matrix cases validate; original five HTML/PNG
  reference assets retain exact supplied hashes. Original extraction manifests
  remain historical provenance rather than fabricated current-file hashes.
- `uv run --locked --extra server --extra mcp pytest tests/unit/test_web_plan.py
  tests/unit/test_docs_alignment.py tests/unit/test_docs_config_contract.py
  tests/unit/test_docs_migration.py tests/unit/test_rest_examples_gate.py -q`:
  exit 0, 86 passed. Plan tests cover graph/reciprocal links/case schema/owners,
  matrix correspondence/reference hashes and five false-completion refusals.
  Evidence index has all 95 rows pending with no claimed executions.
- Focused current API/security/candidate/transaction/verification selection:
  exit 0, 140 passed. Detached baseline default tests: 5299 passed/52 opt-in
  deselected; build and three locked installation profiles passed. Its strict
  Cockpit stage failed 1/570 as recorded above. Baseline worktree remains clean.
  Explicit baseline `pyrefly check 'src/**/*.py' 'tests/**/*.py'
  --use-ignore-files=false` exits 0; this supplements ignored-parent discovery.
- Actual Bash guard deterministic red/green:
  `cockpit/test/candidate-guard.test.ts::complete frame parsing does not depend on a line-producer process-substitution wait`
  fails original source and passes corrected source. The new
  `a valid empty installed base retains its exact empty second wire line` case
  passes, as do all-action malformed/no-file-effects, failed reader/decoder,
  maximal Unicode/frame and exact installed-content cases. Synthetic injected
  wait exists only in fixture argv, with no production bypass. Pinned Node
  `--test test/*.test.ts`: 572 passed, zero fail/skip/cancel in 58.699 s;
  targeted ESLint/types and diff checks pass. Log
  `.scratch/web-001-cockpit-unit-corrected.log`, SHA256
  `28ffe7e3036b6384f92dbd7780711b846f9997a93116645bcd2f3b757dae5ef2`.
- Real helper/source hashes: candidate guard
  `5eecb28502e3e612856c4a7bf27ca814b500f21080048ba3ac07f26be9a7532a`,
  candidate tests
  `018237b593360db1b2832631b837b98da8b4afae98807af85e343ed28b7ef54e`.
  Red/green logs `.scratch/web-001-frame-regression-{red,green}.log`;
  exact negative wait `.scratch/web-baseline-confirmation-wait-status.json`
  SHA256 `97ed20f435a9c7f53f9e7eacd0aab3543a7867abb8133c6b5fe7591142834473`.
  Corrected focused confirmation 20/20 runs pass with no retries; source-repeat
  record `.scratch/web-001-confirmation-after-repeats.json`. Repetition alone is
  not the fix proof: deterministic failure injection establishes the correction.
- Maximum 2,796,210-byte framing parse: 0.415 s in
  `.scratch/web-001-frame-regex-stages.json`, SHA256
  `ec5a2ee5b7eb39b56e3d31794e7fa1985faa01205ed59f5fe9a78ecda45016e7`.
  Rejected parameter-parser timing and original failure evidence are retained;
  scoped process audit found no remaining diagnostic burners. These are actual
  local shell/source fixtures with a controlled manager, not PAM/installed/NAS
  acceptance. Earlier five guests are untouched.
- Human introduction/status page, root/docs navigation, Cockpit transition and
  framing troubleshooting accompany accepted public API/server/security/schema/
  discovery contracts. Documentation checker exits 0: 194 human docs/19 helpers.
  No unimplemented UI route/config key is presented as currently available.
- Reviewed actual ADRs 108–129, 133–139 and AD-01/06/12/14/15/16/17/18/21;
  FS-05–11/15/16/19, CP-01–14, FW-01–04, affected INV-001–020 and agent
  INV-011. Decisions 140–143 accept design with conformance pending; 144 remains
  proposed. INV-018's narrow card extension and new INV-019/020 explicitly name
  source/test gaps. Predecessor status/amendment links retain historical reasons.
  The baseline parser correction is an implementation repair under decision 138,
  not a new wire/permission/architecture/dependency exception.
- Actual tool/image/guest inventory and safe provisioning path are in
  [prerequisites](../support/web-ui/prerequisites.md). Required later browser/
  installed closure is unverified, not silently skipped. No production manager,
  credential, Caddy, services, timers, guards, NAS or remote publication changed.
- Final `scripts/check.sh --require-cockpit`: exit 0. 5308 Python tests pass,
  52 nonselected opt-in tests; locked base/server/server+MCP install profiles,
  format/lint/types/docs/build all pass. Cockpit lint/style/types, 572 unit
  tests (zero skip/fail), 110 mounted Firefox tests and production build pass.
  Corrected gate log SHA256
  `7f3897c30cfafb66ef48eae468343e21162be3bf49537dc68d9dd40303e00d40`;
  mounted bundle `ba7e98028efde2a7ef594b508cb2cc9846d5e69aac3e4745e324c0c6d714721b`.
  Wheel SHA256 `7ba81b14b1d36dc6648cb37404d46dee5abf8978a548d0fe350005d900f22274`;
  sdist `59f2416e321d24aaedb1b92bbd77b8de154ceddf3492a3e1044ad19d8d5a0514`.
  These are development build artifacts, not a newly deployed release. Independent
  final ERE review passes the exact recorded source hash. Completed audit and
  Operator handoff 33 in [progress](../../progress.md) accompany this commit;
  current selector advances to WEB-002 with no outstanding WEB-001 blocker.
