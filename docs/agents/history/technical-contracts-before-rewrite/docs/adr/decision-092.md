> Historical technical reference preserved before consolidation. Current authority is the living contract.

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `950f428faa32460e1a2ae964adde639fb0df2d9996bddb8a42e7995f1b5caa03`,
original content SHA-256 `8986d5772d5a5d1e5fcd1938510594da586cfe417ac420e1144dba547ca17eac`.
Historical proof hashes identify the original artifacts, not this edited record.

# Decision 092: Plugin CLI invocations run in transient units that import the deployment's encrypted Hub credential

- Original decision date: 2026-07-30.
- Original work package: `CPT-013`.
- Source: [decision 92 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The
`runuser` shape ran every plugin-spawned command anonymously, because
the credential exists only inside units systemd loads it into —
invisible while `hub.expected_account` was empty, and an honest
`HFHUB003` refusal ("the Hub reports this run as 'anonymous'") on every
plugin doctor and mutating preflight the moment the operator set it.
The one invocation shape becomes `systemd-run --quiet --wait --pipe
--collect` with `User=`/`Group=` the service identity,
`ImportCredential=hf-token`, and `UMask=`/`MemoryHigh=`/`Environment=`
parity with `hfcache-sync.service` (the memory bound is decision 86's
protection extended to page-spawned selector syncs). The credential
moves to systemd's system credential store,
`/etc/credstore.encrypted/hf-token` — where `ImportCredential=`
searches — and the sync service's drop-in becomes the same one-line
import: one credential, one location, every consumer. Import of an
absent credential is silently skipped, which is `token_mode =
"optional"` restated at the unit layer, so credential-less deployments
keep a working, anonymous plugin. The ciphertext is bound to the host
and the credential *name*, not to one unit — the old example text
claiming unit binding was wrong and is corrected; name binding is
exactly what lets the scheduled sync and the plugin's transient units
share it. Lifetime semantics change deliberately: a transient unit
outlives its page-side waiter (verified: unit stayed `active` after the
waiter was killed), so closing a tab now detaches the view and loses
the envelope rather than killing the run — contract §5, the UI copy,
and `docs/agents/history/removed-interface-records.md` restate it. `CP-08` holds:
decryption is PID 1's, token bytes never pass through the bridge or
the page. **Rejected: probing for a credential file and conditionally
passing `LoadCredentialEncrypted=`** — turns the pure argv builder into
an async, two-shape surface and hardcodes a path where systemd already
owns a search order, and a missing explicit source fails the unit
where an absent import is skipped. **Rejected: keeping `runuser` and
unsetting `expected_account`** — gives up the swapped- and
missing-token guard to keep the UI anonymous, inverting the operator's
stated intent. One host finding recorded with the shape: `systemd-run
--pipe` with stdout redirected to a user-labelled file hands PID 1 an
fd SELinux denies (`init_t` write on `user_tmp_t`), which drops PID 1
off the API bus with a cryptic `Remote peer disconnected` (self-heals,
or `kill -USR1 1`); the denial is correct, nothing is weakened, the
plugin always spawns onto pipes, and the operator docs say "pipe, don't
redirect".

## Later history and current interpretation

The anonymous fallback for an absent imported credential applies to `optional`
policy. [Decision 98](../../../../../adr/decision-098.md) adds `required`, under which the
application refuses missing credentials. Transient-unit lifetime supersedes
[decision 89](../../../../../adr/decision-089.md)'s tab-cancellation behavior.

## Provenance and governing evidence

The source entry first appears in
[99ef932](https://github.com/wtcross/hfcache/commit/99ef93274a7119c662ed8a8a0eb4af0194e416d6)
(2026-07-30, `CPT-013: authenticated plugin invocations — transient units with
ImportCredential`). The decision text above preserves the complete reasoning in
the current historical log, including its recorded alternatives and
consequences.

Current governing documents: [docs/agents/history/removed-interface-records.md](../../../removed-interface-records.md),
[docs/security.md](../../../../../security.md).
