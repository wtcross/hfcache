# Migrate interfaces and preserve rollback evidence

The web interface uses the existing HTTPS endpoint and API. Migrating the
interface must preserve original operations, configuration predecessors and
archive evidence. Source implementation and disposable test results do not
change the [installed production status](../deployment-status.md) or authorize
a production switch. Follow the selected profile's
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

Displayed package versions are insufficient to identify a rollback target.
The previous released application is source `1c68501` / version `0.2.2`; the
retained wheel SHA-256 is
`b88ffd0f8605d2410a16aa17379eb8a31362310f7143ca07dfab8ebf17bb6503`.
Later web-feature builds also used `0.2.2` metadata. Identify the exact source,
wheel, locked closure, UI manifest and indexed native/rootless release instead
of rebuilding or relabelling an old artifact.

The copied-state drill used that actual installed wheel against private copies
exported from disposable native/rootless `0.2.78` / source `f829857e` fixtures.
All 136 exported source files and both export manifests retained their original
bytes. The following table
distinguishes parser compatibility from a compatible running application; these
results do not establish production readiness.

| State or boundary | Observed result and operator consequence |
| --- | --- |
| Historical tags and structured observations | The old installed models accept the copied tag snapshot and all six publication observations. This preserves curation/interpretation readability; it does not verify publication payloads. |
| Current and private predecessor/candidate archive configuration | All 44 copied TOML documents parse with the old archive configuration model. This is syntax evidence, not permission to install a predecessor or point the old server at a different archive. |
| Generic private API receipts and results | The old installed models accept all 12 copied receipts and 12 exact Envelopes, including four `/api/v1/config/applications` receipts. Parsing the generic receipt does not supply the missing helper outcome reader or make its route supported by an old HTTP client. |
| Cards and old archive inspection | The old installed catalog module has no card reader. On an independent copy with exported source modes restored and a simulated NFS mount table, the old inspector reports `HFMNT014` / `unusable` and 15 unknown entries, including cards and existing staging/quarantine/journal/publication/run paths. An earlier retained control without cards was also unusable; cards alone are not the whole refusal. No unknown state was removed. |
| Private configuration and host outcomes | The old installed package has neither the configuration helper reader for 11 copied private outcomes nor the host-action reader for one copied sealed record. These are unavailable readers, not successful old-format reads. Keep a compatible observer whenever any outcome remains unresolved. |
| Scheduled observation handle | The old installed scheduled model accepts the exact copied native pending handle. This is parse-only evidence: the original pending inode remains untouched and uncertain; no lookup, replay, completion or executor-termination claim follows. |
| New server configuration | The old strict server model rejects `host_helper`, `basic` and `web` as unknown fields. Preserve the installed original and prepare a separate reviewed legacy-compatible server configuration. Never enable permissive parsing to force startup. |
| Old reader/writer/MCP against the new server | The exact old installed CLI passes seven native checks over verified TLS: reader/writer status at both aliases, literal candidate validation, one original Plan and lookup of that same Plan. Rootless reader/writer status and candidate validation also pass; its two Plans refuse under the restricted fixture profile, as described below. The strict old MCP client accepts all 14 tools at each alias in each profile (28 calls per profile). Native reads genuine retained reports; rootless reads labelled synthetic report fixtures. These checks do not establish a new worker or browser run. |
| Backend-only operation with UI disabled | Source integration starts a real backend lifespan and Unix HTTP server without UI/Basic configuration; disabled UI selects no assets and retains authenticated JSON 404 responses. Independent base/server/server-plus-MCP wheel installs also pass. These checks do not claim an installed daemon was switched to a disabled-UI profile. A legacy target still needs separately reviewed target-compatible server configuration. |
| An already open browser during a release change | Earlier installed native three-engine checks detect the changed build, preserve original recovery records and unsaved Tags through Stay, and require explicit reload/reconnect without replay. Current unit/component checks additionally reject schema, source, wire and asset identity drift. Historical native checks do not establish a new rootless upgrade outcome. |
| Native installed rollback and return | The disposable native installation completes indexed78 → 77 → 78 through its normal drain, matching bootstrap/configuration/helper binding and stock selection procedures. Trusted-TLS Chromium Library/bootstrap/reload checks pass on77 and restored78 with the same persistent browser profile. The exact old0.2.2 client looks up its original operation on77 and restored78, observing the same succeeded outcome without a new Plan. |
| Rootless installed rollback and return | The disposable rootless installation completes indexed78 → 77 → 78. Target77 has read-only qualification of the original started roles, strict TLS and a passing Chromium Library/bootstrap/reload check. Return78 selection/binding/start stages and its final Chromium Library/bootstrap/reload check pass with the same persistent browser profile. The exact old0.2.2 client looks up its original failed operation on77 and restored78 without replay; its outcome remains failed. |

The indexed predecessor77 is fixture `0.2.77` / source `004ea9e2`; the return
target is fixture `0.2.78` / source `f829857e`. These are disposable indexed
application/helper compatibility checks, distinct from the legacy0.2.2 parser
refusals above and from production deployment. The predecessor retains its known
configuration-read503 limitation; Library, TLS and original-handle checks do not
establish its complete configuration workflow.

Rootless target77 startup was qualified by read-only observation after failed
collectors. Those original aggregates remain failed; binding publication and
normal service starts were not replayed. Versioned worker seccomp paths were
accepted only after both deployment-bound artifact indexes verified identical
profile bytes; the other confinement checks remained exact. The drill does not
demonstrate rollback with an unresolved newer helper outcome. Preserve its
evidence and retain a compatible observer before selecting any target.

After return78, the actual rootless roles retain host UID/GID983, zero capability
sets, no-new-privileges, seccomp and SELinux confinement. The worker's IP denial
and the exact renewed leaf over strict TLS 1.3 are observed independently.

The initial native old-client attempt refused the expired fixture certificate
chain before submitting a Plan. After a separately reviewed fixture CA/leaf
renewal, strict TLS 1.3 qualification and the real-client checks above passed.
The renewal's first post-start assertion failed without retaining its snapshot;
that original aggregate remains failed. A separate read-only qualification
observed the original started Caddy and preserved unit, hardening and original
state without repeating the restart. This disposable fixture repair establishes
neither production certificate rotation nor production migration acceptance.

The first rootless Plan returns `HFARG002`: its literal candidate disables Hub
tokens while that installed API explicitly selects a token file. Lookup observes
the original failed operation. A separately reviewed candidate with optional
tokens validates, but its distinct Plan returns `HFAPI007` because its authority
does not match the restricted profile. Both refusals and their original handles
remain preserved; no installed policy/configuration was changed to force a pass.
The MCP checks use their normal HTTP transport, including POST requests, and
submit no Plan, Apply or replay. Rootless strict TLS 1.3 qualification passes;
the original drain/start/earlier qualification failures remain recorded without
repeating those service actions.

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
