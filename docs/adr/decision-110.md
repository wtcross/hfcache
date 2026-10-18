# Decision 110 — Guard complete command execution and verification persistence

- Status: Accepted and implemented.
- Date: 2026-10-17.
- Work package: API-003, this commit.
- Source: [progress decision 110](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-003-extract-guarded-commands.md).

## Context and decision

Baseline CLI full verification released its lock before report/catalog
persistence, and new/revision verification took no common lock. The catalog
merge reads prior state before atomic replacement, so concurrent merges could
lose unrelated findings or verification state. This is a demonstrated protection
gap and reproducible test interleaving, not evidence of production corruption.

Extract every command's orchestration into typed `CommandServices`, using the
existing domain engines and schema-1 results. Public services acquire their own
common archive lock exactly once; adapters and later runners do not pre-lock
those calls. Every non-estimate verification acquires that lock, runs storage
preflight, resolves scope, hashes, writes its report, and completes catalog
read/merge/write before releasing ownership. Domain persistence helpers require
caller ownership and do not acquire nested locks. Estimates remain lock-free,
non-hashing, non-persisting metadata queries.

Probe-enabled doctor and explicitly confirmed initialization also hold the
common lock. They use their own diagnostic/initialization checks rather than an
entry preflight that requires the sentinel they must inspect or create.
Read-only doctor and initialization inspection remain lock-free. Quarantine
keeps its separate rule: refuse unfinished unrelated work, never reconcile it.
Sync still cancels pending producer work and joins the active transfer before
releasing lock ownership on a foreground failure.

## Rationale and alternatives

Atomic JSON replacement prevents partial readers, but cannot serialize a
read/merge/write transaction. Per-mode locks, locking persistence alone, or
releasing after hashing leave races against scope changes or catalog merges.
The existing cross-process flock also excludes separate local commands; an
in-process mutex or future executor queue would not replace it. Reusing domain
engines preserves refusal, journal, recovery and publication semantics.

## Consequences and relationships

Amends [AD-17](ad-17.md), [offline verification](offline-verification.md), and
[decision 40](decision-040.md)'s historical doctor exception. INV-007 and
INV-015 now identify the full read-and-persist boundary. Narrow verification
also refuses unproven mount/sentinel storage before writing a report. Immutable
archive formats, publication identities, clearing rules and exit taxonomy stay
unchanged. Service results correlate recovery reports and repair/prune journals
with their emitted invocation IDs; partial persistence/refusal payloads remain
visible in CLI output.

The scoped full-verification environment guard remains until API-004; this
package adds no concurrent server, networking mechanism, REST route, dependency,
or MCP code. The isolated no-IP executor remains API-008/014 work.

Evidence: [phase and multiprocess merge regression tests](../../tests/unit/test_command_locking.py),
[command guard and refusal tests](../../tests/unit/test_command_services.py),
and the existing sync/crash/verification/maintenance suites.
