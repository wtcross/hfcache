# Confirm installed configuration through a pipe and bounded local collector

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

- Decision identity: 139.
- Status: Accepted; amended as described below.
- Date: 2026-10-20.

## 2026-10-21 protected-reader amendment

[Decision150](decision-150.md) supplies protected host/config-base reads; fixed
configuration writes in [decision154](decision-154.md) retain exact guarded
confirmation and durable uncertainty from this record. Original candidates,
backups and operation handles remain evidence; helper availability never proves
an uncertain apply did not occur.

## Context and decision

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

## Replacement UI design amendment (2026-10-20)

The pre-removal record remains in Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`; removed interface-only
instructions and source evidence are historical, not current operating steps.
