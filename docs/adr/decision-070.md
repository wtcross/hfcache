# An artifact that will not parse is not an absent artifact

- Decision identity: 070.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.

## Decision, context, and consequences

Not a deviation from the plan — the plan is right and the code
disagreed with it. `docs/architecture.md` §7.9 says a state recovery cannot
resolve unambiguously stops the machine, and `TX-06` says a transaction that
can fail either way leaves more rather than less. This path did neither.

`pending_cleanups` skips a retirement record it cannot read. That is correct
and deliberate: it answers a scheduling question, and one damaged record must
not hide the others from `HFWRN008`. Its docstring even says which commands
are responsible for reporting damage instead.

`_repair_remediation` then asked it a different question — "does this repair
still have a cleanup outstanding?" — and read the empty answer as *no*. So a
record that could not be parsed became a repair that was finished, and the
remedy became `close_journal`. The journal is left open past checkpoint 15
for one reason, stated at the top of `repair.py`: it is the only durable
record `recover` can find on its own, and it is what stops a deferred cleanup
from being forgotten. Closing it forgot the cleanup. `status` kept warning
`HFWRN008` and kept naming `recover --apply` as the remedy, which now
reported `actionable 0`. The retired tree stayed published indefinitely.

The rule this settles, and it generalises past this one call site: **a
tolerant reader and a decision procedure must not share a return value.**
Skipping a damaged artifact is a kindness to a *report*; to a *decision* it is
a false negative, and here the false negative resolved toward discarding
work. Where a function has to answer "is there any", callers that will act on
"no" need to be able to distinguish "none exist" from "I could not tell", so
`unreadable_retirements` exists to be asked the second question and the
remediation is `BLOCKED` with `HFTXN003` when the answer is yes.

Found by running `operational tooling`'s drill rather than by the suite, and it took a
real deployment to surface: every test that damages a retirement record
damages it while checking something else, so nothing had ever asked recovery
what it made of one. That is the same argument  made for rolling out
before declaring anything done, and this is the fifth defect it has produced.

## Provenance and governing evidence

The source entry first appears in
[cd10962](https://github.com/wtcross/hfcache/commit/cd10962ebe6912677dea987dc9b681ec148927dc)
(2026-07-27, `repair: an unreadable retirement record stops recovery, not the
journal`). The decision retains its rationale, alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/recovery.md](../recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/repair.py](../../src/hfcache/repair.py),
[src/hfcache/recovery.py](../../src/hfcache/recovery.py).

Relevant verification:
[tests/unit/test_recovery_planning.py](../../tests/unit/test_recovery_planning.py).
