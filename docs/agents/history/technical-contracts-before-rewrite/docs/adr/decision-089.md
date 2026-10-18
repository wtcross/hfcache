> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 089: The operation surface bends to the CLI, not the reverse

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.
API-backed Cockpit mechanisms are amended by [decision 122](../../../../../adr/decision-122.md).

- Original decision date: 2026-07-30.
- Original work package: `CPT-001`.
- Source: [decision 89 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Three shapes settled with the operator. **No publish action:**
`docs/cli.md` §2 has no publish command — publication is an atomic
stage inside `sync`, and `repair` is the only republish — so the UI
says "Sync now" and renders published state from `list --revisions`,
rather than the CLI growing a command to match a button. **Selector
sync as a page-spawned process, in version 1:** a spawn dies with the
browser tab, accepted for selector-restricted runs because interruption
is a crash shape the application is designed for (`AD-09`,
per-repository transactions, `docs/operations.md` §9) and the UI
surfaces `recover --dry-run` afterward; the alternative — a templated
`hfcache-sync@.service` carrying selectors under the full §22.5
hardening — is recorded as the follow-up seam rather than built now,
packaging surface ahead of demonstrated need. Full sync and full
verification stay behind the shipped units unconditionally (`CP-04`):
the units carry the sandbox, `MemoryHigh=`, and the journal identity,
and Cockpit's own guidance is not to run long uninterruptible work from
a page. **Excluded outright** (`CP-05`–`CP-08`): touching
`hfcache.target`, enabling `hfcache-verify.timer` (handoff item 8 owns
that calendar), `archive init` in any form, and any credential surface.

## Later history and current interpretation

Partially superseded by [decision 92](../../../../../adr/decision-092.md): selector commands now
run in transient units and survive a closed tab; the browser loses its
waiter/envelope rather than cancelling the job. The CLI-defined surface and
excluded actions remain.

## Provenance and governing evidence

The source entry first appears in
[ebc112f](https://github.com/wtcross/hfcache/commit/ebc112f30995e70a1ad3c6d214ee53b803f43b7f)
(2026-07-30, `CPT-001: Cockpit plugin contract and work-package plan`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/cockpit.md](../../../../../cockpit.md),
[docs/cli.md](../../../../../cli.md).

Implementation or shipped-artifact evidence:
[cockpit/src/sync.tsx](../../../../../../cockpit/src/sync.tsx),
[cockpit/src/lib/command.ts](../../../../../../cockpit/src/lib/command.ts).

Relevant verification:
[cockpit/test/command.test.ts](../../../../../../cockpit/test/command.test.ts).


## 2026-10-18 Cockpit API integration amendment (API-015)

Page/transient observer loss and stopping the sync client no longer imply
execution interruption. Accepted work belongs to the API/private worker; expose
retained key/operation lookup/wait and never automatic recovery or a cancellation
claim. Full sync/verification keep installed units; sync-timer-only/no-init/target
controls remain. See [decision 122](../../../../../adr/decision-122.md).
