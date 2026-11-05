# The operation surface bends to the CLI, not the reverse

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts. This record preserves the superseded
launcher rationale; it is not a procedure for the removed interface.

- Decision identity: 089.

- Original decision date: 2026-07-30.

## Decision, context, and consequences

The original interface followed the existing CLI instead of expanding archive
authority to fit buttons. Publication belonged inside complete `sync`; repair
was the only replacement operation. A separate publish action was rejected.
Fixed service execution preserved memory, hardening and journal identity for
long work, while target shutdown, archive initialization, verification-calendar
activation and credential editing remained outside ordinary browser authority.

The original page-owned selector process was accepted as an interruption shape;
[decision 92](decision-092.md) superseded that lifetime with a transient unit.
Current API execution is owned by the server/private worker, so loss of the
browser or its observer cannot cancel accepted work or prove recovery safe.

## Later history and current interpretation

Partially superseded by [decision 92](decision-092.md): selector commands now
run in transient units and survive a closed tab; the browser loses its
waiter/envelope rather than cancelling the job. The CLI-defined surface and
excluded actions remain.

## Provenance and governing evidence

Original decision: [ebc112f](https://github.com/wtcross/hfcache/commit/ebc112f30995e70a1ad3c6d214ee53b803f43b7f).
The historical rationale above is paraphrased from the pre-removal record at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`. Current authority is defined by
[the CLI](../cli.md), [API](../api.md) and [security](../security.md).

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
