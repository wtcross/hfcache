> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 131 — Explicit disposable probes and qualified isolation evidence

| Field | Value |
| --- | --- |
| Status | Accepted |
| Date | 2026-10-18 |
| Amends | [Hardening probes](../../../../../adr/decision-059.md), [egress evidence](../../../../../adr/decision-060.md) |

## Context and decision

Import-time checks, live archive defaults and generic exception-as-denial logic
can cause an invasive diagnostic to run before identity proof or certify an
unrelated failure as isolation. Diagnostic tooling must fail closed too.

Default, help and dry-run are static. Explicit inventory reads only property
names. Native disposable workloads require a profile, target UUID, existing
local lock and acknowledgement. Prove mount locality, no-follow paths,
sentinel schema/identity and ownership before writes, then revalidate under
the same lock. Confine artifacts to an exclusively owned health child and
clean only proven inodes. Refuse production targets, guarded/read-only
profiles and NFS workloads on a host carrying the production mount.

Never write real kernel tunables or system-directory scratch files. Report
observations with their actual scope. Only expected permission errno values
can establish denial of a specific attempted action. Missing imports, DNS,
timeouts and unexpected I/O remain not proven. A seccomp filter is evidence
of filter presence; neither it nor an action denial attributes individual rules.

## Rationale and alternatives

Retaining implicit workloads risks production I/O. Treating every exception
as successful enforcement accepts broken prerequisites. Copying production
credentials, lifecycle hooks and shared writable state into a disposable probe
is unnecessary authority. Copy selected sandbox and read-mask properties;
override health and private temporary storage explicitly. Report the difference
instead of claiming that a transient process reproduces the installed executor.

Direct and dependency output is suppressed or reduced to fixed diagnostics;
manager output is parsed and projected by known result names and states.
Never relay raw errors or property values. Credential-source opens never read
bytes, and ordinary DAC denial cannot prove namespace masking.

## Consequences and evidence

The original setgid mkdir/chmod and hardlink requirements remain. Disposable
checks also read and hash the exact owned content. Network compatibility checks
require separate explicit selection; a small download does not establish Xet
transfer compatibility. Rootless PID1/cgroup, peer, SELinux and actual NFS workload
acceptance remain distinct operator observations.

See [diagnostic modes](../../../../../security.md#hardening-diagnostics),
[probe](../../../../../../scripts/hardening-probe.py),
[wrapper](../../../../../../scripts/check-hardening.sh), and
[owned-fixture tests](../../../../../../tests/unit/test_hardening_probe.py).
No archive format, dependency or daemon sandbox policy changes.

## Native layout qualification

[Decision 132](../../../../../adr/decision-132.md) additionally requires positive installed-native
layout proof before native inventory, interpreter execution or workload effects.
An explicit profile acknowledgement cannot authorize a container or unknown release.
