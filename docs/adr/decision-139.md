# Confirm installed configuration through a pipe and bounded local collector

- Decision identity: 139.
- Status: Accepted; source FD/status regressions and actual enforcing disposable installation/confirmation passed; original installed symptom remains separate.
- Date: 2026-10-20.

## Context and decision

An actual disposable Cockpit installation wrote and validated its candidate,
then installed exact bytes and retained the exact predecessor. Confirmation
failed before another client unit started. The enforcing audit log records PID1
`init_t` denied `write` to an `etc_t` file. The guard redirected `systemd-run
--pipe` stdout directly to its root-owned confirmation file in the configuration
directory. This recreates the pipe-only lesson in [decision 92](decision-092.md),
independently of that record's superseded credential delivery.

Give the fixed launcher an anonymous stdout pipe. A local privileged collector
alone writes the existing bounded root-owned confirmation spool while the same
original configuration flock remains held. Explicitly require its file limit.
Capture launcher and collector exit statuses independently and immediately.
Collector failure withholds all stdout, even when it emitted a plausible complete
result. Successful collection preserves the exact launcher exit. Unexpected
launcher exits also withhold stdout without replacing their status. Retain the
existing output-size limit and installed-byte checks before and after validation;
only then release the classified result. No apparent success bypasses a failed
process, collector or postcheck.

## Rationale and alternatives

Changing SELinux policy, enforcement or file labels to permit PID1 configuration
file writes would weaken the boundary. Direct forwarding would release a result
before exact installed-byte postchecks. A pipe and bounded local collector retain
both confinement and delayed authority using existing Bash/coreutils. Pipeline
status alone cannot distinguish a collector's domain-like exit from the original
CLI exit; keep the two statuses separate.

## Consequences and relationships

Amends [decision 122](decision-122.md) and [decision 134](decision-134.md), retains
[decision 138](decision-138.md), CP-11, INV-006 and the fixed API-only rootless
launcher/credential separation in [decision 127](decision-127.md). No new runtime
dependency, service option, API route, credential source, archive authority or
replay/cleanup/rollback permission follows. Keep the already installed bytes,
predecessor, original lock and failed confirmation evidence. Source correction
does not confirm that installation or prove the original production symptom.

[Guard implementation](../../cockpit/src/lib/candidate-guard.ts),
[filesystem/FD regressions](../../cockpit/test/candidate-guard.test.ts),
[Cockpit contract](../cockpit.md) and the
[invariant register](../invariants.md#cockpit-boundary) define the boundary.
Native denial, source regression, fresh disposable acceptance and later installed
verification remain separate evidence.
