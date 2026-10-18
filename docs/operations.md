# Operating hfcache

Use the authenticated API client for operational commands. Before running a
workflow, check the [recorded deployment restrictions](deployment-status.md).
The selected installation remains guarded/read-only: these procedures describe
supported behavior and do not authorize NAS workloads, guard removal or schedules.

## Choose the client and authority

For the selected rootless writer host, use its fixed wrapper and protected
client settings. A shell array preserves argument boundaries:

```bash
HF=(/usr/local/libexec/hfcache-client --client-config /etc/hfcache/client.toml --json)
```

For a native writer-local or remote reader installation, use an installed client
and its own settings instead:

```bash
HF=(hfcache --client-config "$HOME/.config/hfcache/client.toml" --json)
```

Choose one definition. Native Unix clients use `/run/hfcache/api.sock`; the
selected rootless endpoint is `/run/hfcache/api/api.sock`. Remote clients use
verified HTTPS with the configured public prefix. See [client setup](api-client.md).
The settings select a protected REST bearer pathname or named API credential;
never put its value in arguments. A reader needs no archive mount, archive TOML,
Hub credential or service UID. Writer capability is required for mutation.
MCP credentials grant only the separate [metadata tools](mcp.md).

## Resolve uncertain work before starting more

Each deliberate job has one nonsecret idempotency key. The CLI prints that key
before POST and operation ID after admission, even with quiet output. Preserve
both. HTTP 202 acknowledges durable admission, not successful execution. Default
CLI observation returns the exact terminal server Envelope; inspect `outcome`,
`exit_code`, errors and partial results. HTTP 200 on a result can contain failure.

If acknowledgement, connectivity or an observer is lost, look up the original
key under the same credential class. These reader-capable requests observe only;
they submit no job and do not mutate archive or receipt evidence:

```bash
"${HF[@]}" operations lookup -- 'original-key'
"${HF[@]}" operations show -- '0123456789abcdef0123456789abcdef'
"${HF[@]}" --wait-timeout 300 operations wait --after 12 -- '0123456789abcdef0123456789abcdef'
```

Use your saved handles, rather than these synthetic identifiers. Wait shares one
finite deadline across event/status/result reads, retries and sleeps. `--after`
resumes a sequenced cursor; retained-history gaps are explicit stderr diagnostics.
Ordinary progress requires both streams to be terminals and quiet mode off.
Warnings/errors and safety handles remain visible with quiet and JSON output.

`HFAPI020` retains the original key when POST acknowledgement is uncertain;
`HFAPI019` covers connectivity/observation timeout. Exit 20 stops observation;
accepted work may continue. `HFAPI018` protocol/identity failure likewise does not
establish execution outcome. Missing, expired or interrupted history never proves
nonexecution. Never use a new key to repeat uncertain work. An explicit identical
route/body retry with the original key is distinct from lookup and must preserve
that binding. No client automatically replays a mutation.

Client exit, browser closure or a stopped scheduled oneshot does not stop an
executor. Before recovery, mount changes, upgrade or rollback, identify exact
operations and [drain/reconcile the API and verifier](server.md#restart-and-drain).
Keep the verifier available for API outcome handoff, then drain it. A free flock,
PID, elapsed timeout or wrapper exit alone proves neither completion nor death.
Preserve both operation stores, scheduled pending handles and original lock inodes.

## Read status and inventory

These reader commands perform authenticated HTTP and bounded archive metadata
reads. They do not contact the Hub, hash payloads, take the archive lock or create
operation receipts. Availability of the installed archive/policy is still required:

```bash
"${HF[@]}" status
"${HF[@]}" list
"${HF[@]}" list --revisions
"${HF[@]}" verify --estimate
```

Inspect `data.archive` for reachability, unfinished transactions, unknown entries,
quarantined bytes, deferred cleanup and degraded verification. A successful status
query can report a degraded archive; it does not turn an integrity finding into
exit 40. Confidence belongs to an exact SHA/publication instance. A reintroduced
revision or repaired instance must not inherit another instance's confidence.

Inventory includes archived unmanaged repositories; configuration removal never
deletes their data. Explicit selectors filter the combined configured/published
scope, including unmanaged rows. Status retains configured empty repositories.
Collection walks either finish with consistent archive/policy/publication identity
or fail explicitly at byte/page/scan bounds. They are not a global snapshot under
concurrent publication. Do not treat a partial walk as a complete inventory.
Reference locators are published-relative; manifest trees are archive-relative.
Bulk transfer remains the independent [consumer workflow](consumers.md).

Existing reports are authenticated resources `GET /api/v1/runs` and
`GET /api/v1/runs/{run_id}` through the SDK/HTTP interface, not a `runs` CLI command.
Use the exact domain run ID; operation and request IDs are different identities.
See [metadata reads](api.md#metadata-reads) and [report formats](schemas.md).

## Plan, diagnose and synchronize

Installed `plan` and read-only doctor accept a reader. Both are keyed jobs that
contact the Hub with installed executor authority and persist local receipt/
event/result history, while leaving archive data unchanged:

```bash
"${HF[@]}" plan model:organization/model
"${HF[@]}" doctor --read-only
```

Planning resolves immutable SHAs and expected size without payload download.
`0 B new` means the private cache has those bytes; it does not prove publication
or that sync will skip. Size the dataset quota and maintenance window from actual
repository plans, rather than a small historical benchmark. Read-only doctor
skips write probes/lock and reports unproven capabilities; it is not offline.
Ordinary `doctor` needs a writer, uses the archive lock and temporary health
artifacts, and remains subject to mount/sentinel/capacity/permission checks.

When the installation is accepted for writes, a writer can synchronize selected
configured repositories:

```bash
"${HF[@]}" sync model:organization/model
```

Sync contacts the Hub, uses cache/staging, hashes content, publishes ordinary-file
immutable trees and reports, and can rotate retention after successful publication.
It persists control history and takes the common writer lock. Successful earlier
repositories remain published if a later repository fails. Do not infer zero
archive effects from a nonzero aggregate exit.

Restricted repositories require installed `[hub] token_mode="required"`, an
explicit usable Hub source and whole-export authorization. Optional mode remains
public-only even with a token; missing required authority refuses before Hub I/O.
Deliver the Hub source to the API executor using its selected profile, separately
from the client's REST credential. Revocation prevents future fetches but does not
remove retained content. See [credential policy](configuration.md#7-credentials).

## Verify integrity

Estimation above is reader metadata/stat work, with no hashing, reports, archive
lock or confidence increase. Actual verification requires a writer and the private
no-IP/no-credential verifier. It is offline, takes the common lock, hashes payloads
and persists verification reports/catalog state and control history:

```bash
"${HF[@]}" verify --new
"${HF[@]}" verify --full
"${HF[@]}" verify --revision model:organization/model@0123456789abcdef0123456789abcdef01234567
```

Choose exactly one mode. `--new` can restrict to an existing sync `--run-id`;
`--revision` requires a full SHA. Missing/untrusted verifier status refuses before
fresh admission; there is no in-process fallback. A finding exits 40 without
repairing, pruning or rewriting manifest expectations. Preserve the exact report
and follow [recovery](recovery.md#integrity-failure-and-repair).

Full verification is required after corruption/scrub errors, snapshot/replica
restore, migration, interrupted publication, manual archive modification, repair,
publication-mode change or manifest-schema change. Size its read workload first
and coordinate with NAS scrub, SMART, snapshots and replication. Verification
cannot discover the NAS maintenance calendar itself.

## Preview and apply maintenance

Every preview below is a reader-capable keyed job: it creates receipt/event/result
history and reads live metadata, although it changes no archive data. A preview
never grants later apply authority. Apply requires a writer, a separate request
and fresh scope/evidence under the archive lock. Read-only deployment restrictions
still apply to both inspection and workloads.

```bash
"${HF[@]}" prune --dry-run model:organization/model
"${HF[@]}" prune --apply model:organization/model
"${HF[@]}" purge --dry-run model:organization/old-model
"${HF[@]}" purge --apply model:organization/old-model
"${HF[@]}" quarantine --dry-run 0123456789abcdef0123456789abcdef
"${HF[@]}" quarantine --apply 0123456789abcdef0123456789abcdef
"${HF[@]}" recover --dry-run
"${HF[@]}" recover --apply
```

Choose exactly one of `--dry-run` and `--apply`; neither defaults. Review the exact
selection and current evidence before each deliberate apply.

Prune handles configured retention only. Three revisions is the default, five is
an explicit compatible policy. After reducing `storage.maximum_revisions`, review
and repeat one round at a time: each invocation removes at most one eligible
non-current revision per repository, ordered by immutable publication generation.
Current is protected. Disabled configured repositories may be selected; unmanaged
ones require purge. Failed upstream access never triggers deletion.

Purge requires explicit whole-repository unmanaged selectors XOR
`--all-unmanaged`; it refuses configured targets, SHA selectors and unexplained
layout. Each repository has its own transaction: earlier purges can stay committed
after later failure. Manifest and purge-reason audit evidence survives. Logical
bytes released are not physically reclaimable ZFS space; hardlinks, compression,
deduplication and snapshots affect physical allocation.

Quarantine cleanup takes explicit recovered publication-staging transaction IDs.
It proves the whole batch empty or redundant against freshly verified matching files in the repository's current retained publication
before removal, and preserves repair, unique, unknown and unfinished evidence.
Recovery resolves only unambiguous journal/checkpoint evidence and prefers
over-retention. See [transaction recovery](recovery.md#transaction-refusals).
No recovery workflow initializes an existing archive.

## Diagnose failures

| Outcome | Meaning and next step |
| --- | --- |
| Usage exit 2 | Fix CLI grammar; no command callback ran |
| 0 | Successful classified result, possibly warnings; inspect status and warning fields |
| 10 | Invalid policy/invocation; inspect exact result and admission history before assuming no prior effects |
| 20 | Safety, transport, protocol or observation refusal; retain handles, establish execution state and diagnose mount/sentinel/lock/limits |
| 30 | Repository sync failure; inspect partial results and exact run report |
| 40 | Integrity findings; preserve evidence and original expectations; use the recovery workflow |
| 50 | Retention/repair failure; inspect transaction/audit evidence and preview recovery after quiescence |

| Symptom | Diagnosis |
| --- | --- |
| API unavailable | Check selected endpoint/socket, CA/public prefix and correct profile/manager; never fall back to local mutation |
| Verifier unavailable | Inspect exact API/worker status and protected listener/readiness; preserve active receipts and keep admission closed if liveness/outcome is unknown |
| HFAPI001 / 401 | Invalid, stale or wrong-interface bearer; MCP and Hub tokens cannot substitute for REST |
| HFAPI002 / 403 | Valid REST credential with insufficient capability; provision the required class |
| Invalid policy | Validate installed policy or an explicit candidate; candidate syntax and installed-authority compatibility are separate |
| HFAPI005 / response/page/scan bound | Fail incomplete collection; review source size/server limits rather than silently dropping rows |
| HFMNT010 / lock wait | Identify real executor/operation; never unlink a lock or infer completion from its availability |
| HFTXN001–004 | Preserve journals/filesystem evidence; use the refusal table in recovery |

Ordinary daemon logs belong to the API executor; actual verification logs belong
to the private worker. Scheduled native sync/verify services are observers, so
their systemd invocation ID is not the daemon's domain run ID. Join sanitized
closed-vocabulary events by request/operation/domain run identities. API verbosity
is restart-only; client `--verbose` changes local diagnostics. Selected rootless
services use the service account's user manager; native services use the system
manager. See [deployment profiles](deployment-centos-stream-10.md).

## Warnings

| Code | Meaning | Response |
| --- | --- | --- |
| `HFDEP001` | Undeclared dependency detected in repository metadata | Add it to `declared_dependencies`, or configure the dependency as its own repository. Never downloaded implicitly |
| `HFWRN001` | Temporary over-retention: retained revisions exceed the configured limit | `recover --dry-run`, then `prune --apply` |
| `HFWRN002` | Logical prune committed, trash removal outstanding | Physical only; the revision is gone logically. `recover --apply` retries the cleanup |
| `HFWRN003` | Unknown files in an application-owned area | **Preserved, never deleted.** Identify them before removing anything by hand |
| `HFWRN004` | Stale staging directory | A run stopped part way and aged past `sync.stale_staging_age_hours`. `recover --dry-run` |
| `HFWRN005` | Free space approaching the configured reserve | Capacity work. Note ZFS snapshots hold blocks after an application prune |
| `HFWRN006` | Upstream repository unreachable | Nothing to do. Every local revision is preserved; this never triggers a prune |
| `HFWRN007` | Archived repository is not in configuration | Its revisions are kept. If removal is intentional, review `purge --dry-run` before `purge --apply` |
| `HFWRN008` | Retired repair instance past its grace period | `recover --apply` quarantines it |
| `HFWRN009` | Local Xet transfer cache exceeded its advisory ceiling | Writer-local disk, not the archive. Check `/var/cache/hfcache/xet` |
| `HFWRN010` | Verification may overlap storage maintenance | Reschedule one of them |

Warnings alone do not change a successful exit. Unknown data stays preserved.
Stale staging requires diagnosis, not automatic removal; retired repair instances
follow grace/quarantine rules. Xet cache warnings concern writer-local storage,
not the published archive.

## Scheduling and capacity

The selected guarded rootless deployment keeps legacy writers masked and the
verification calendar disabled. Do not enable them as a documentation check.
Native scheduled services retain observation handles and repeat finite windows;
stopping an observer preserves lookup-only recovery, never replay authority.

| Native timer | Calendar in America/New_York | Persistent | Random delay | Accuracy |
| --- | --- | --- | --- | --- |
| Sync | Daily 02:00 | true | 30m | 1m |
| Verification | First Wednesday of Jan/Apr/Jul/Oct at 04:00 | true | 2h | systemd default |

A oneshot already active at the next elapse consumes that trigger without a
second invocation. Persistent timers replay host-down misses, not busy-unit
triggers. Long syncs legitimately reduce observations; retained depth counts
observed revisions, not every upstream commit. Start timeout is infinite; the
common lock additionally serializes manual/scheduled writers. Default scheduled
sync lock wait is one hour and verification wait is 24 hours. A preflight/lock
refusal may have no domain run report; API receipt and sanitized logs still matter.

Pause only the appropriate timer under the selected manager after operator
approval. Stopping `hfcache.target` is not a pause shortcut: the native mount is
PartOf the target and may unmount. Never release mounts beneath live executors.
Persistent journald sizing is 1 GiB/one year; the optional failure-hook template
integrates monitoring. Neither logs nor readiness replace integrity verification.

Use [capacity/performance measurements](storage-requirements.md) after NAS/network/Hub-library
changes or before large repositories. Measure logical versus unique-inode bytes,
snapshot-held space and actual read/publication throughput; do not extrapolate
small idle-host results into a production quota or verification window.
