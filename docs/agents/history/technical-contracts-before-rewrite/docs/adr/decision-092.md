> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 092: Plugin CLI invocations run in transient units that import the deployment's encrypted Hub credential

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.
API-backed Cockpit mechanisms are amended by [decision 122](../../../../../adr/decision-122.md).

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
and `docs/cockpit-plugin/usage.md` restate it. `CP-08` holds:
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

Current governing documents: [docs/cockpit.md](../../../../../cockpit.md),
[docs/security.md](../../../../../security.md).

Implementation or shipped-artifact evidence:
[cockpit/src/lib/command.ts](../../../../../../cockpit/src/lib/command.ts),
[packaging/systemd/hfcache-sync.service.d/credential.conf.example](../../../../../../packaging/systemd/hfcache-sync.service.d/legacy-hub-credential-reset.conf.example).

Relevant verification:
[cockpit/test/command.test.ts](../../../../../../cockpit/test/command.test.ts).


## 2026-10-18 Cockpit API integration amendment (API-015)

The credential-delivery mechanism remains systemd, but its authority changes:
transient API clients import only `hfcache.api`, use fixed client TOML/socket and
omit ordinary archive config/Hub environment. Hub `hf-token` stays daemon-only;
there is no anonymous fallback for missing API credentials. Browser/argv/environment
bearers remain forbidden. Closing/stopping a client loses observation, never
cancels accepted execution or proves recovery safe. This supersedes the Hub-import
and direct-execution implications above; see [decision 122](../../../../../adr/decision-122.md).
