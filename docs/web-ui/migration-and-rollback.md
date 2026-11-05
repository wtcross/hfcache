# Migrate interfaces and preserve rollback evidence

The web interface uses the existing HTTPS endpoint and API. Migrating the
interface must preserve original operations, configuration predecessors and
archive evidence. A production switch requires operator authorization and
profile-specific validation. Follow the selected profile's
[deployment procedure](deployment.md) under separate operator authorization.

## Match existing workflows

| Existing workflow | Web interface workflow |
| --- | --- |
| Inventory and repository inspection | [Library](library.md) and [exact-publication details](repository-details.md); configured policy, archived membership and metadata coverage remain separate. |
| Run jobs and inspect reports | [Operations](operations.md); durable admission, execution and the exact domain result are separate evidence. |
| Recover a lost acknowledgement | **Import original handle**, then **Observe original operation**; retain the original key, operation ID and credential namespace. |
| Edit configuration and tags | [Configuration and tags](configuration-and-tags.md); exact-base validation and a successful matching preview precede explicit Apply. |
| Retention, recovery and repair | [Maintenance](maintenance.md); review the exact preview/finding before a separately confirmed effect. |
| Host status, schedule and observer controls | [Administration](administration.md); supported native permissions and guarded rootless denials remain explicit. Verification scheduling is display-only. |
| Read an upstream README | [Archived README](readme-cards.md); bounded inert presentation is pinned to one immutable publication and never loads external assets. |

Opening a workspace performs no job submission. Signing in never releases the
archive guard, enables a timer or supplies additional host permission.

## Preserve the original authority and handles

Before switching, record the verified HTTPS authority, public prefix, archive
UUID, selected immutable release and original operation handles. Preserve the
complete installed configuration, candidate/base/predecessor and fixed backup,
original configuration lock inode, both API/private-worker operation stores,
scheduled observation handles, and helper outcome directories. Retain the
protected credentials separately with their existing ownership and access
rules; never copy them into browser evidence or documentation.

The new page cannot read another origin's session storage. Copy safe original
keys and IDs before leaving an earlier interface. In Operations choose
**Import original handle**, select its type and original credential class,
enter the exact value and choose **Save original handle**. Saving performs no
lookup or POST. **Observe original operation** is the separate read action.
See [original-handle recovery](operations.md#import-and-observe).

Previously retained bearer keys keep their credential-class namespace.
Administrator Basic keys belong to the stable administrator subject, independently of the
password. Keep legacy keys as unbound references; a missing Basic lookup cannot
establish that bearer work never ran. An authorized reader can inspect a known
original operation ID. Configuration host-outcome observation additionally
requires its original subject-scoped application key and configuration-read
permission. Password rotation must retain the stable subject if original Basic
key lookup is to continue.

Unknown, interrupted or missing evidence is a stop condition. Stopping a browser
or scheduled observer does not stop its executor. Do not submit a replacement
key, replay Apply, delete history, unlink a lock or remove a pending marker to
obtain a clean-looking migration.

## Compatibility and backups

Identify a rollback target by exact source, wheel, locked dependencies, UI
manifest and indexed native/rootless release. Displayed package versions alone
are insufficient; different builds can share a version. Preserve the complete
predecessor bundle and its configuration, index, policy and confinement bindings.

Older targets may parse a generic receipt yet lack the route or protected reader
needed to settle its outcome. Validate these boundaries with the actual target
binary against owned copies before selecting it:

| Boundary | Required compatibility check |
| --- | --- |
| Archive configuration | Validate a separate target-compatible document. Strict older models can reject tags; preserve the tagged original and historical snapshots. |
| Server configuration | Targets predating browser/host support can reject `host_helper`, `basic` and `web`. Prepare a reviewed compatible copy; never weaken strict parsing. |
| Published metadata | Test tags, observations and cards separately. Readable ordinary inventory does not prove an older archive inspector or card reader accepts the optional namespace. Unknown records stay preserved. |
| API receipts/results | Check route support and original key lookup as well as generic Envelope parsing. A readable terminal result does not implement a newer route. |
| Protected outcomes | Keep a compatible configuration/host-outcome reader whenever a newer outcome is unresolved. Missing reader support blocks rollback if observation cannot be maintained. |
| Scheduled pending handles | Validate the exact model and preserve the original inode. Successful parsing does not prove lookup, completion or executor termination. |
| Browser assets and state | Select assets matching the target backend contract. Preserve handles and unsaved work before explicit reload/reconnect; never copy old assets into a running release. |

The compatibility tests exercise retained old source objects with isolated
installed wheels; see [development validation](../development.md#examples-and-documentation).
Their offline scope does not establish a live NAS, production migration or
complete installed workflow. A legacy target's unavailable configuration reader
cannot be inferred working from successful Library or TLS reads.

Backups must include historical tag snapshots, publication observations and
card adjuncts beneath `published/metadata/`, as well as immutable publication
evidence. Current configuration cannot reconstruct removed historical labels.
Individual atomic records do not promise a globally simultaneous snapshot.
Preserve unknown formats and temporary evidence through coordinated backup and
rollback. The [durable-format rules](../schemas.md#1-conventions) and
[discovery backup procedure](../discovery.md#guarded-rollback-and-backup)
apply independently of the browser.

## Select a rollback scope

| Scope | Required selection and stop condition |
| --- | --- |
| Frontend selection | Use only a reviewed immutable UI artifact that matches the selected backend contract and asset identity. Never copy files into a running release. Schema/version drift requires explicit reload or compatible selection; preserve original handles before reloading. |
| Complete application and helper | Select the coherent indexed wheel/UI/helper/templates/policy unit through the existing profile installer. Prove actual API/private-worker/helper drain and preserve the original common locks, protected configuration and outcome state. |
| Legacy binary | Validate a separate target-compatible configuration and copied durable state with the exact target binary. Retain a compatible observer for any newer unresolved operation or helper outcome. If that observation cannot be maintained, rollback remains blocked. |

Follow [actual executor drain](../deployment-centos-stream-10.md#upgrade-and-drain)
before any authorized switch. A stopped client, free wrapper PID or timeout is
insufficient. Keep NAS read-only/independent guard, writer masks and disabled
calendars as required by the installed profile. Retain previous immutable
releases and their indexes. A failed or uncertain switch requires operator
reconciliation with the original evidence; no automatic replay, rollback,
forced termination or uncertain cleanup follows.

After a compatible selection, verify trusted TLS at the same authority/prefix,
UI/backend contract and assets, separate REST bearer/MCP access, helper binding
and permission denials. Reconnect explicitly and observe the original safe
handles. Retain the stable Basic subject through password/provider changes.
Writers and schedules remain disabled until their separate prerequisites are
approved. See the [rollback contract](../deployment-centos-stream-10.md#rollback-compatibility).

## Production migration checklist

These checks remain operator work; disposable acceptance checks none of these
boxes for the production installation.

- [ ] Inventory original keys/IDs, unknown operations, actual executors, both
  stores, private outcomes, candidates/backups and persistent locks.
- [ ] Create and verify a coordinated protected backup and target-compatible
  configuration without overwriting the installed originals.
- [ ] Review indexed release/closure/UI/helper identities and the target's
  observed durable-format and unresolved-operation compatibility.
- [ ] Authorize and perform the profile's actual drain and guarded selection,
  keeping archive, credential, SELinux and service-manager boundaries intact.
- [ ] Verify trusted TLS, sign-in, Library/details, original-handle recovery,
  configuration outcome observation, REST/MCP and expected host denials.
- [ ] Retain rollback artifacts and evidence. Approve schedules, writer changes
  or production/NAS workloads separately.
