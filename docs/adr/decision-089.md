# The operation surface bends to the CLI, not the reverse

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

- Decision identity: 089.

- Original decision date: 2026-07-30.

## Decision, context, and consequences

## Later history and current interpretation

Partially superseded by [decision 92](decision-092.md): selector commands now
run in transient units and survive a closed tab; the browser loses its
waiter/envelope rather than cancelling the job. The CLI-defined surface and
excluded actions remain.

## Provenance and governing evidence

## 2026-10-18 historical API integration amendment

Page/transient observer loss and stopping the sync client no longer imply
execution interruption. Accepted work belongs to the API/private worker; expose
retained key/operation lookup/wait and never automatic recovery or a cancellation
claim. Full sync/verification keep installed units; sync-timer-only/no-init/target
controls remain. See [decision 122](decision-122.md).

## Manual REST jobs amendment (2026-10-20)

[Decision 135](decision-135.md) supersedes the full-job service-start rule:
manual `sync` and `verify --full` use the fixed keyed REST client and original
operation recovery. Scheduled observers remain separate host objects. The plugin
never starts sync/verify units; optional stopping requires positive proof of the
fixed observation-only binding and explicit protected permission. Sync scheduling
stays on its fixed system timer. Guarded or unknown profiles deny effects.

The pre-removal record remains in Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`; removed interface-only
instructions and source evidence are historical, not current operating steps.
