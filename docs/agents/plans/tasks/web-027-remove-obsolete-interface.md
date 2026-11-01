# WEB-027: Remove obsolete interface source and documentation

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Remove the obsolete interface](../2026-11-01-plan-legacy-interface-removal.md) |
| Depends on | Completed web UI replacement |

## Scope and acceptance

Implement the parent plan's complete repository removal and documentation cleanup.
Preserve active shared host inspection, permission, scheduling, recovery and
confinement rules. Keep the current web frontend and required attribution.
Historical source is available at the recorded pre-removal Git commit; the user's
explicit instruction permits removing obsolete snapshots from today's documents.

## Contracts, invariants and ADRs

Review browser/host authority, dependency/build, record policy and documentation
contracts; implement decision 161 and retire obsolete interface-only requirements.
No runtime dependency or archive/durable operation format change is required.
Any shared compatibility spelling retained in code must have a concrete current
consumer and must not preserve a removed interface command surface.

## Validation

Completed: focused documentation/ledger and fixture checks, the full strict web/build gate, and final documentation closure checks recorded below.

## Execution notes and handoff

2026-11-01: Source, human docs and historical records are independently assigned
within this work package. Root owns the final shared contract/index reconciliation,
protected test namespace, evidence and commit/push to `github` and `forgejo` on `feat/web-ui`. Plugin-only tests
are explicitly included by the user. Production services, installed
files, archives, credentials, original handles and user caches remain untouched.

## Checkpoint: historical catalog evidence adaptation

The first strict gate preserves its actual failed result: 9,559 backend tests
pass and two catalog-history validators fail after authorized source/test removal
and a task rename. All 1,229 frozen files remain unchanged during that run.
The failure is retained in `.scratch/web-027-validation/gate1.log` and its result;
no failed aggregate is credited as passed. Adapt the validators to explicit
retirement of obsolete source-interface tests and exact original Git provenance.
Two Administration screenshots containing obsolete visible labels are removed;
all other 15 raster assets are visually clear, and original review counts retain
their historical scope. Rerun focused affected checks and the required full gate.

## Checkpoint: owned-launcher and real-worker fixture reliability

Gate2 retains its failed result: 9,555 backend tests pass and six late fixture
checks fail. All 1,227 frozen inputs remain unchanged. The observed failures are
cancellation during subprocess creation, a Node metadata subprocess outer wait,
and four real-worker observations exceeding a ten-second test budget while the
original operations subsequently complete during normal drain. No failed run is
relabelled as passed. Frontend lint passes separately.

The launcher now owns its exchange task before its first await, including child
creation, exchange and actual reap. Deterministic spawn/exchange cancellation
checks retain one child and require its normal close; no signal or kill is added.
The Node metadata test and the two real-worker modules receive finite sixty-second
outer observation budgets. The shared API test helper still defaults to ten
seconds. Submissions, original-key recovery, domain assertions and production
settings remain unchanged. Sequential focused checks pass all four real-worker
cases and all 54 host-fixture cases. The next full gate runs without concurrent
frontend lint. This fixes validation ownership and scheduling tolerance, adding
no application authority, dependency, durable operation format or service effect.

## Completion evidence

Completed 2026-11-01, WEB-027, this commit. The superseded frontend tree is absent,
including all 107 tracked files and its generated dependency/build tree. Its
standalone client configuration, optional gate/CLI inspection entrypoint and both
dedicated backend test suites are removed. Shared inspection primitives remain
only for actual current host-policy consumers. Fixed scheduling/previous-writer
safety and serialized recovery compatibility retain their existing semantics.
No application permission, runtime dependency or durable operation format changes.

Five dedicated human guides and obsolete dedicated plans/support/snapshots/ADRs
are removed. Current documentation has no removed-name content or pathname, and
no invented replacement source paths. The compatibility guide is now
`docs/web-ui/migration-and-rollback.md`. Two screenshots with obsolete visible
labels are removed; the other eleven genuine guide screenshots and four supplied
mockups are visually clear and byte-identical to the reviewed originals. The
original thirteen-image review remains historical, without manufactured captures.
Required LGPL attribution/license remains, with the original Git blob and SHA256.

Historical source and exact invocation bodies remain at pre-removal Git
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`. Preserved document inventories retain
original path/content hashes and distinguish current snapshots from originals.
The catalog retains 55 original IDs, with 53 active cases and two explicitly
retired frontend-only cases. Removed CAT-003 instructions are replaced by exact
original package/task provenance, never execution of removed tests. All 95 web
cases retain their IDs, owners, completed status, minimum layers and original
executed proof identities. Current independent-web wording and reciprocal task
and matrix links are reconciled.

### Required gate

`rtk proxy scripts/check.sh --require-web --with-build` passes with exit 0 in
1,598.087 seconds, as login UID 1000/nice10 in a private empty read-only archive
shadow. Both inner and outer results are 0. All 1,227 tracked inputs remain
unchanged, with no additions or removals during the run:

- 9,562 backend tests pass; 52 default opt-in marker deselections remain separate.
- 3,708 unit and 4,051 unique combined web tests pass, with no required skips;
  frontend line coverage is 95.02%, branches 90.13%.
- Three locked base/server/server-plus-MCP installations, two built Chromium
  startup checks, the real HTTP/API React read fixture and all 16 wheel smoke
  checks pass. These retain their actual source/synthetic scope, not new installed
  Caddy/profile, production, NAS or optional instrumented-runner acceptance.

Freeze SHA `8b03a419b0ab7aa82a059ea8a73c47cd2af7f097d1af75733e9755cacf7d480b`;
result `.scratch/web-027-validation/gate3-result.json` SHA
`970178e3077980a906cdd6be94a02019bebd64630d9062f5cc6070b93c0dae08`;
log SHA `b599413f832fd8d5d6cf1a1f26fac427b8f66a75317b61bcc62b6129e295efca`.
Outer result SHA
`8c51352b9eb46b195be2130068dd7bc82850648b5d58a0c723378998a8829d70`.

Focused checks pass 62 documentation/ledger/catalog tests, four real-worker
workflows and 54 host-fixture cases. Their logs remain under the same validation
root. Original Gate1/Gate2 and intermediate failed checks stay failed. Both failed
TMP trees are preserved as restrictive verified PAX archives plus complete metadata
and link/socket identities; ordinary bytes compare to their originals before
retiring only those exact generated trees. Metadata-only initial-read side effects
remain explicit. No live state, user cache or unrelated tree was retired.

### Contract review, closure and publication

Reviewed framework/dependency, current browser/host authority and record policy,
including INV-017/019–022 and FW-03/04. Decision 161 retires obsolete requirements;
current shared safeguards remain. The launcher fix enforces existing ownership
across creation/exchange/reap; finite fixture waits retain all assertions and do
not change production deadlines or control authority. No new architectural choice
or dependency is introduced by that validation correction.

Final post-gate changes are documentation/status only. The task/plan/current,
completed progress and operator handoff close in this commit. The user explicitly
authorizes normal branch-only pushes to `github` and `forgejo`; perform and verify
those after this commit, recording actual remote outcomes separately. No source
file claims publication succeeded before that verification. Production services,
credentials, archive state, original unknown handles/locks, calendars, installed
software and unrelated caches remain unchanged. No main/tag/force push or backlog
activation is authorized.

Post-gate closure covers 212 human documents/29 helpers, all 17 migration,
web-ledger and catalog-provenance checks, plus working/staged whitespace checks.
Only the five documentation/status adoption files differ from the successful
full source freeze; runtime, build, test and gate code remain unchanged. Actual
closure receipts remain under `.scratch/web-027-validation/`.
