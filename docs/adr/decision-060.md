# Decision 060: `IPAddressDeny=any` on the verification unit rather than `PrivateNetwork=true`

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `SYS-002`.
- Source: [decision 60 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

§22.3 asks that
`PrivateNetwork=true` be tested on the deployed NFS mount and enabled "if the
already-mounted filesystem remains reliable **under reconnect**".

Both were tested. Under `PrivateNetwork=true` and under `IPAddressDeny=any`
alike, a probe read all 21 published files — 12 721 220 bytes — off the
already-mounted archive while outbound TCP and DNS both failed. Steady-state
reads are fine either way, so that is not what decides it.

The condition is the reconnect, and it cannot be met here: §36.4 defers NFS
interruption against the live mount to an operator-supervised window, so this
session has no way to provoke one. §22.3's own instruction for that case is to
keep the command application-offline and document the narrower host egress
control — so `HF_HUB_OFFLINE=1` stays, the structural guarantee stays
(`verify` builds no `HubClient` and resolves no credential, asserted in the
suite), and the third layer is `IPAddressDeny=any`.

It is the better fit independently of the untested condition.
`IPAddressDeny` filters the unit's own sockets through its cgroup and does not
move the unit into a different network namespace at all; the NFS client's RPC
sockets belong to the kernel and are untouched, so there is no reconnect path
to be unsure about in the first place. `PrivateNetwork=true` would put the
process in a namespace holding only loopback, and any NFS behaviour that
depends on the caller's namespace — an upcall, a referral, a re-established
connection — becomes a question this deployment cannot currently answer.

Handoff item 10 carries the `PrivateNetwork=true` evaluation for the operator
window that can answer it.

## Later history and current interpretation

This records the narrower deployed egress control and the reason reconnect
testing was deferred. It does not claim that `PrivateNetwork=true` was validated
under an interrupted NFS connection.

## Provenance and governing evidence

The source entry first appears in
[999ed19](https://github.com/wtcross/hfcache/commit/999ed19a88059a155e462b962505e6687c78c786)
(2026-07-26, `SYS-002: apply the §22.5 hardening and test every setting`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/security.md](../security.md),
[docs/deployment-centos-stream-10.md](../deployment-centos-stream-10.md).

Implementation or shipped-artifact evidence:
[packaging/systemd/hfcache-verify.service](../../packaging/systemd/hfcache-verify.service).

Relevant verification:
[scripts/hardening-probe.py](../../scripts/hardening-probe.py),
[tests/unit/test_verify_command.py](../../tests/unit/test_verify_command.py).

## Explicit diagnostic and evidence amendment

[Decision 131](decision-131.md) replaces implicit live workloads and generic
exception-as-denial classification. Static entrypoints, explicit disposable
authority, identity/lock proof and qualified results govern current probes.
Original dated results remain historical evidence, not current acceptance.
