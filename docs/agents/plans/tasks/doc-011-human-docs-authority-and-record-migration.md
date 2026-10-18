# DOC-011: Separate human documentation from implementation records

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [REST/MCP documentation and script alignment](../2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |
| Depends on | None |
| Phase | 0 — Authority and inventory |
| Review findings | F01, F02, F14 |
| Suggested commit | `DOC-011: separate human docs from implementation records` |

## Scope and implementation requirements

Establish the user's documentation boundary without discarding implementation history or weakening a current technical contract. This is an explicit, recorded amendment to the existing stable-path planning rules, not permission to reorganize history silently.

Start from the reviewed feature branch, inspect current git evidence and the existing selector, and record implementation authorization. Inventory every tracked documentation file, executable/help surface, example and reference to the historical plan. Use the accompanying review as the starting evidence, not an exhaustive dead-code detector.

Move existing `docs/plans/` records into `docs/agents/plans/`, `docs/progress.md` into `docs/agents/progress.md`, and the historical `docs/plan.md` into `docs/agents/history/plan.md`. This bundle already adds new files in the destination: migrate per file with collision checks rather than nesting a directory or overwriting the new plan. Preserve dated filenames, work-package IDs, statuses, completed evidence and git history. Record old/new paths and pre-move content hashes in an agent-only migration manifest. Preserve original factual text; distinguish mechanical reference repair from substantive amendments.

Before moving the historical plan, map every still-normative section to a current human contract. Extract any requirement that exists only there into the appropriate living contract. Update live source/test authority references to current contracts; a link to archived implementation instructions must not be the only specification of behavior.

Move purely agent-process ADRs into `docs/agents/adr/`; identify them by content, not filename alone. Preserve human architectural ADRs under `docs/adr/`. Move the planning-only invariant and its enforcement rationale into an agent invariant guide, retaining its ID and history. Keep single-plan selection, task-owned evidence and one-work-package-per-commit semantics.

Update `AGENTS.md`, its symlink target relationship, planning/workflow/release/conventions guidance and every executable reference used to locate the selector. The single active selector ends this package at `docs/agents/plans/current.md`. Remove obsolete selector/index paths after successful migration; do not leave a second selector or human-facing redirect into task history.

Publish the human-document policy in an agent guide. During the phased rewrite, allow only an exact, inventoried pre-existing set of human-to-agent references; no new leaks. Later packages must reduce this set, and final acceptance requires zero. Never use an entire-document wildcard as a permanent exemption.

## Acceptance

- [x] Exactly one active selector selects this plan; every existing record is accounted for by the migration manifest and all new tasks already exist.
- [x] Current contracts own all required behavior formerly specified only in the historical plan; no test loses a requirement through relocation.
- [x] No file, task ID, decision rationale, release evidence or operator restriction is lost. No historical implementation authorization becomes current host-operation authorization.
- [x] Agent-only process rules, including the one-time path exception, are recorded in agent documentation; technical ADRs keep human-readable rationale.
- [x] Documentation links and test/source references resolve after migration, including changed relative paths. No obsolete active-plan index remains.

## Contracts, invariants and ADRs

`AGENTS.md`; `docs/agents/planning.md`; `docs/agents/workflow.md`; original `docs/adr/decision-107.md`; planning invariant `INV-011`; historical plan authority and current architecture/schema contracts. Record the path-policy amendment under the agent ADR policy, retaining previous identifiers.

Paths above use the reviewed repository's names for identification. DOC-011 owns
the authoritative relocation map; after that package use the current path and
preserve the same contract/record identity. Read relevant sections progressively.
Record an explicit no-impact review when no technical invariant changes; do not
create a ceremonial technical ADR for an editorial-only change.

## Documentation in this work package

Update the agent router/guides and indexes in this commit. Create the migration manifest, human-document policy and per-file inventory under `docs/agents/`. Extract missing technical requirements to human contracts before archive relocation.

Human docs describe current behavior, limitations and examples without task IDs,
plans, progress links or implementation chronology. This task file and the agent
progress log contain execution evidence. Keep related code/tests/docs together.

## Validation

Validate the migration manifest against git-tracked source paths/hashes, parent/task/dependency links, exactly one selector and absence of collisions. Run existing documentation-parsing tests and `scripts/check.sh`. No host/NFS actions.

2026-10-18 validation (all exit 0):

- `uv run --locked --extra server --extra mcp pytest tests/unit/test_docs_migration.py tests/unit/test_failure_matrix.py tests/unit/test_logging.py tests/unit/test_retention.py --no-cov`: 120 passed.
- `scripts/check.sh`: lock, full-extra sync, 446 formatted Python files, lint,
  Pyrefly (0 errors), 4062 passed/40 opt-in deselected in 469.25s, build, locked
  base/server/server+MCP installation smoke, and actual Cockpit frozen install,
  lint, 135 passed/0 skipped, production build. Full log retained locally at
  `/tmp/hfcache-doc011-gate.log`; no live/NFS/installed-host workload ran.
- Independent original-hash/47-record audit, Markdown destination/anchor scan
  (zero missing), and `git diff --check` passed. Migration tests validate every
  baseline hash and original tracked document, unique destinations, process
  record locations, symlink and single selector. The failure matrix now checks
  exact equality with the living development contract; coverage was strengthened.
- An earlier gate stopped at long citation lines; those were wrapped. A later
  run was interrupted to incorporate review corrections, then the complete final
  gate above passed. These attempts are not counted as acceptance evidence.

## Execution notes and handoff

Activated 2026-10-18 at reviewed HEAD 65b6571. Work on `feat/rest-api-and-mcp`, preserving existing user changes and
all live-host restrictions. Do not push, merge, tag, deploy, rotate credentials,
run production probes or manipulate NAS/services. If blocked, record the missing
prerequisite and precise unblock condition here and in the current selector.

## Completion evidence

2026-10-18, this commit: all acceptance checks completed. Collision-checked
47 per-file moves preserved original SHA-256/git provenance and supplied bundle.
Original historical facts remain, with mechanical path/link repairs separated
from the mapped normative extractions. Source/test comments now cite living
contracts; the sole application AST change beyond docstrings replaces an orphan
historical section citation in a retention refusal with stable AD-05 (no behavior
or code change). Unit Documentation URLs now name the living deployment guide.

Reviewed FS-02/03/04/19, AD-17/18, INV-010/011 and process decisions 82/106/107.
INV-011 and five process ADRs retain identity under agents; decision 130 records
only the authority-path exception. No technical invariant, dependency or durable
format changes. Live guard, locks, masks, read-only NAS, calendar, stores,
handles, credentials and hardening remain untouched. The dated human status
page records restrictions without renewing historical authorization.

See [completed progress entry](../../progress.md#documentation-authority-separation-2026-10-18),
[manifest](../../migration-manifest.json), [inventory](../../documentation-inventory.json),
[coverage map](../../historical-contract-map.md) and [agent decision 130](../../adr/decision-130.md).
Next ready task is OPS-020. The user's later steering authorizes both remote
feature-branch pushes only after final plan acceptance; merge/tag/deploy and
production operations remain forbidden.
