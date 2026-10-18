# API-003: Extract guarded command services and close verification lock gaps

| Field | Value |
| --- | --- |
| Work package | `API-003` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-002](api-002-extract-queries-and-results.md) |
| Phase | 1 — Shared services |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-003: extract guarded commands and serialize verification persistence` |

## Scope and acceptance

1. Move sync/plan/doctor and prune/purge/recover/quarantine/repair/init command orchestration into typed services. Reuse existing domain functions and preserve command-specific ordering, refusal rules, exact run/result provenance, and partial failure payloads.
2. Preserve lock-before-preflight and reconciliation-before-Hub for commands that require it. Preserve quarantine’s different rule: validate selected evidence, refuse unfinished unrelated work, and never reconcile it implicitly. Make lock ownership explicit to prevent nested acquisitions.
3. Correct all non-estimate verification modes to acquire the common archive lock before resolving their scope and hold it through hashing, report write, and catalog read/merge/write. Remove or amend the persistence comment that atomic replacement justifies concurrent merges. Estimates remain non-persisting reads.
4. Add a reproducible interleaving regression test showing catalog updates cannot lose unrelated failures or verification state. Extend command guard tests to probing doctor and explicit initialization without changing their domain safety rules. Do not operate on the live archive.

## Contracts, invariants, and ADRs

`AD-13`–`AD-20`, `FS-19`, `TX-01`–`TX-07`, `INV-006`/`INV-007`; plan §§2, 4–6.

Use the [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update CLI verification effect/lock tables, architecture/invariants, verification persistence contract, and offline-verification/related ADR amendments. Record the observed baseline protection gap and the chosen tighter boundary, not an unsupported claim of observed production corruption.

## Validation

Planned checks, not execution evidence:

Existing sync, verification, retention, purge, repair, recovery, quarantine, preflight, and initialization suites; new multi-process lock/interleaving tests using temp paths. Assert every non-estimate verification persistence call occurs while the archive lock is held. Test failure paths release locks only after child transfer work stops. Run `scripts/check.sh`.

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

Implementation authorized by the active plan and Tyler's 2026-10-17 instruction;
API-002 is completed in `b2b3793`. Implemented only API-003 on the selected feature
branch. Added immutable requests and `CommandServices`, with command-level
credential resolution, selection, domain guards, reconciliation and classified
partial results; Typer remains a parsing/rendering adapter. Existing domain
engines and schema-1 artifacts remain authoritative.

Baseline review confirmed a protection gap: full verification released its guard
before persistence and new/revision verification did not take the common lock.
Decision 110 tightens every non-estimate mode to lock, storage preflight, scope
resolution, hashing, report write and complete catalog merge under one ownership.
The regression deliberately pauses a real merge across spawned processes and
proves unrelated failures and exact-instance state survive. No production
corruption is asserted. Doctor probes and confirmed initialization now serialize
without invalid sentinel entry preflight or nested service locks. Quarantine's
refuse-unfinished-work rule and sync's cancel/join-before-release behavior remain.

Characterization caught human quiet-mode persistence-error suppression and
malformed repair/config refusal precedence during extraction; both were corrected
with regressions. Existing doctor/init tests needed temporary lock-directory
fixtures for their newly serialized modes. Exact recovery report IDs propagate to
the envelope; repair/prune journal IDs use the invocation context.

The full-only scoped offline environment guard remains unchanged until API-004;
REST routes, isolated executor, policy freshness and MCP remain planned. No new
runtime dependency or durable schema was introduced. No production, deployment,
remote publication, release, or host-hardening operation was performed.

## Completion evidence

2026-10-17, API-003, this commit.

Moved sync/plan/doctor/init/verification and prune/purge/recover/quarantine/repair
orchestration into immutable typed command services. CLI keeps parsing/rendering
and bootstrap config loading; source-import tests prohibit direct domain
orchestration there. Classified errors, partial persistence/recovery payloads,
selector refusal order, exact report IDs and existing domain engines are retained.

Decision 110 closes the baseline verification protection gap: all non-estimate
modes hold the common lock and storage preflight from target resolution through
hashing, report write and catalog read/merge/write. A spawned-process regression
pauses a real catalog merge and proves unrelated failures and exact publication
states survive. Phase tests assert lock ownership through resolution, hashing,
report construction, persistence and merge; missing-sentinel tests refuse every
mode before work. Probing doctor and confirmed initialization own one raw common
lock without requiring a sentinel entry preflight. Read-only diagnostics,
inspection, estimates and previews remain unlocked. Sync interruption tests prove
the active transfer stops before ownership is released; quarantine never invokes
implicit reconciliation.

Reviewed AD-13–20, FS-02/03/19, TX-01–07, INV-006/007/012/015 and decisions
40/51/108/109. Added decision 110 and index entry; amended AD-17, offline
verification and historical doctor-lock decision 40; updated architecture,
CLI effects/locking, schemas persistence prose, invariants, original-plan
amendment, API service boundary and Unreleased notes. No durable schema or
runtime dependency changed. REST routes and isolated executor remain planned;
full-only scoped offline environment handling remains API-004 scope.

Validation:

- `rtk uv run pytest tests/unit/test_readonly_commands.py tests/unit/test_archive_init.py -q`:
  113 passed. Initial extraction runs exposed the newly required temporary lock
  fixtures, which were added; no host runtime directory is used by these tests.
- `rtk uv run pytest tests/unit/test_cli.py tests/unit/test_config_validate.py tests/unit/test_verify_command.py tests/unit/test_quarantine.py tests/unit/test_command_locking.py -q`:
  177 passed, including 8 new lock/interleaving tests.
- `rtk uv run pytest tests/unit/test_synchronize.py tests/unit/test_crash_injection.py tests/unit/test_retention.py tests/unit/test_purge.py tests/unit/test_recovery.py tests/unit/test_recovery_planning.py tests/unit/test_preflight.py -q`:
  320 passed. Existing command-injection test seams moved from CLI to services.
- `rtk uv run pytest tests/unit/test_command_services.py tests/unit/test_command_locking.py tests/unit/test_synchronize.py -k 'test_an_interrupt_finishes_the_active_download or not test_synchronize' -q`:
  20 passed, 113 deselected; direct service/CLI provenance, doctor/init guards,
  quiet persistence failure, repair refusal precedence and transfer joining.
- `rtk uv run ruff check` on affected source/tests, `ruff format`, and
  `rtk uv run pyrefly check`: passed; Pyrefly 0 errors (10 existing suppressions).
- `rtk proxy bash scripts/check.sh > .scratch/api-003-gate.log 2>&1`: exits 0,
  lock check, format, lint, types, 1,816 Python tests, 45 Cockpit tests,
  wheel/sdist builds and production plugin build pass.
- `rtk proxy python .scratch/audit_records.py` and `rtk proxy git diff --check`: local links,
  task dependencies/current pointer, API parity matrix and whitespace pass.

No live/NFS/host/deployment checks or production operations were performed.
No push, merge, tag or deployment. No API-004 or MCP implementation started;
next task is API-004.

[Progress audit](../../progress.md#rest-api-and-read-only-mcp-api-2026-10-17).
