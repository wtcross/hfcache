# Remove the superseded interface and its documentation

- Decision identity: 161.
- Status: Accepted by explicit user instruction.
- Date: 2026-11-01.
- Introducing change: this commit.

## Context and decision

The replacement web UI has completed its scoped source and disposable installed
acceptance. The user now requests complete repository removal of the superseded
interface and all of its documentation references. Remove its implementation,
dedicated configuration, build/test hooks, guides and superseded records. Keep
shared host/client safety mechanisms and attribution for code still shipped.

This explicit instruction narrowly overrides earlier retain-as-deprecated policy
and normal preservation of obsolete document paths/snapshots. The original records
and exact historical execution invocations remain in Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`; current retained evidence must not claim
that a rewritten invocation or snapshot is the original executed artifact.

## Rationale and alternatives

Keeping deprecated implementation and obsolete instructions would leave the
requested removal incomplete. Deleting shared helpers would weaken the current
web UI, so current consumers and safety contracts determine what stays. Git
preserves the historical material without presenting obsolete instructions in
today's documentation. Necessary attribution for retained adapted code remains.

## Consequences and relationships

The default and strict source gates validate the current web workspace only.
Obsolete interface-only requirements and predecessor retention policies retire;
current application authentication, host authority, protected configuration,
original-operation recovery and compatible rollback rules remain in force.
No production uninstall, service selection, credential, archive, calendar,
release/tag publication or new runtime dependency change follows. The authorized
source branch push does not deploy the running application. See the current
[web guide](../web-ui/README.md), [development](../development.md) and
[invariant register](../invariants.md).
