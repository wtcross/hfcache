# Make legacy Cockpit validation opt-in and focus completion on the new web UI

- Decision identity: 160.
- Status: Accepted by explicit user direction.
- Date: 2026-11-01.
- Introducing change: this commit.

## Context and decision

The user directs “ignore the cockpit plugin moving forward” and selects its
immediate deprecation once the new web UI is complete. Earlier plan/ADR language
required continuing Cockpit gates and a separate inventory, test-porting and
removal project. Those obligations no longer govern this goal.

The default provider-neutral gate does not discover or run the legacy plugin.
Strict `--require-web`, backend, documentation, locked installation and build
checks remain required. Keep `--require-cockpit` as explicit legacy opt-in with
its existing strict semantics; do not invoke it for current new-web acceptance.
All95 new-web behaviors and minimum test layers remain required, including real
installed compatibility, rollback and independent operation.

Record proportional deprecation and handoff after replacement guide
acceptance. Preserve legacy source/tests, historical evidence, attribution,
existing deployment and generic client/runtime helpers. No further plugin
maintenance, exhaustive retirement inventory, safety-test porting project,
dependency cleanup or live uninstall is required.

## Rationale and alternatives

Mandatory legacy validation would continue work the user explicitly excluded.
An explicit legacy flag preserves existing invocation compatibility without
making it part of new-web completion. Deleting old files or shared helpers would
add unrequested scope and could erase useful history or affect other clients.
New-web safety behavior remains enforced by its own current tests and installed
observations.

## Consequences and evidence

Only development gate orchestration and its control tests change. No runtime
permission, durable format, dependency, deployment, service, credential, archive,
guard or calendar change follows. Source/fixture acceptance does not modify the
production installation. Gate-control fixtures validate omission/explicit opt-in;
they do not execute or certify the deprecated plugin.

Amends [088](decision-088.md), [143](decision-143.md) and [144](decision-144.md).
The earlier requirements and executed results remain historical. See the
[development gate](../development.md#web-workspace) and
[replacement migration guide](../web-ui/migration-from-cockpit.md).
