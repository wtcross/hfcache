# Remove the superseded interface and its documentation

- Decision identity: 161.
- Status: Accepted; narrow removal exception for the superseded interface.
- Date: 2026-11-01.
- Record introduced: `f7d12463919bdfe46a664b24948bdafe9c051501`.

## Context and decision

The replacement web UI makes the earlier interface redundant. The decision
removes the superseded interface and its documentation from the repository:
its implementation,
dedicated configuration, build/test hooks, guides and superseded records. Keep
shared host/client safety mechanisms and attribution for code still shipped.

This supersedes the earlier retain-as-deprecated interface policy. Its removal
scope is limited to superseded interface material; it does not establish a
general record-retirement policy. The original interface records
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
release/tag publication or new runtime dependency change follows. Repository
removal does not uninstall a running application. See the current
[web guide](../web-ui/README.md), [development](../development.md) and
[invariant register](../invariants.md).
