# Recovering hfcache

Start with execution state, then archive evidence. The selected deployment's
[guarded/read-only restrictions](deployment-status.md) remain in force. A generic
recovery procedure does not authorize NAS I/O, restore, writer enablement or
changes to guards, services, mounts or credentials.

## Establish execution state

Use the [profile-specific API client](operations.md#choose-the-client-and-authority),
with a protected REST credential. Commands below use that guide's `HF` shell array.
A reader can observe and preview; actual recovery/repair/verification needs a writer.
All archive reads require the appropriate live-storage prerequisites and acceptance.

For a lost acknowledgement, observe first. Before filesystem maintenance, restore,
upgrade or rollback, establish the required quiescence:

1. Preserve the original key, operation ID, exact result/error and known domain
   run/transaction IDs. Look up the original key in its credential-class namespace.
2. Inspect exact operation status/events/result under a finite deadline. HTTP 202
   is admission and result HTTP 200 can contain a failed domain outcome.
3. If outcome/liveness is uncertain, preserve all evidence. A missing/expired or
   interrupted receipt does not prove nonexecution; never repeat with a new key.
4. When filesystem quiescence is required, stop fresh API admission and drain
   accepted work while the verifier remains
   available for exact outcome handoff. Then drain the verifier. Follow
   [server restart/drain](server.md#restart-and-drain) and the selected deployment
   lifecycle; client exit, free flock, old running label, PID or wrapper exit is
   insufficient proof that execution ended.

Normal lookup/observation or an explicit identical-key retry does not require
taking services down. After approved quiescence/restore, deliberately restart or
reopen compatible API/verifier services with reconciled history before submitting
new maintenance/verification jobs; a drained runner rejects new work. Reopening
services never lifts the selected read-only guard or supplies workload approval.

Reader-capable observation creates no operation and changes no archive evidence:

```bash
"${HF[@]}" operations lookup -- 'original-key'
"${HF[@]}" operations show -- '0123456789abcdef0123456789abcdef'
"${HF[@]}" --wait-timeout 300 operations wait --after 12 -- '0123456789abcdef0123456789abcdef'
```

Use saved handles rather than synthetic examples. `HFAPI020` preserves uncertain
POST acknowledgement; `HFAPI019` stops connectivity/observation; `HFAPI018`
rejects protocol/identity. None grants cancellation, replay or recovery authority.
Quiet output still retains handles, warnings/errors and explicit event gaps.

## Preserve four kinds of authority

| Evidence | Authority and preservation |
| --- | --- |
| Archive manifests/references/journals/reports/audit | Immutable content expectations, exact publication and transactional checkpoints; authoritative archive evidence |
| API receipt/event/result store | Durable key/route/body-digest/class binding before 202, admitted policy and exact terminal result; service-private, not exported |
| Private verifier receipt/result store | Exact surviving worker execution/outcome and result digest; distinct from the API store |
| Scheduled pending handles | Durable original key before the sole POST; existing handle permits lookup/observation only |

Preserve all four across restart, credential rotation, backup and rollback. API
state defaults to `/var/lib/hfcache/api`; selected profile paths are explicit in
[server](server.md) and [containers](containers.md). API/verifier stores contain no raw key or credential; scheduled handles
intentionally retain the original nonsecret key. None is replaceable by an
archive snapshot. Never merge stores,
hand-edit states, clear uncertain history or unlink any instance/store/archive lock.
Only validated terminal succeeded/failed API history may expire under configured
retention (30 days by default). Count/space exhaustion refuses new admission,
rather than shortening the window or deleting uncertain evidence.

On API restart, ordinary queued/running work is not requeued. Exact matching live
verifier state is reattached; exact matching terminal evidence closes the parent
receipt without rerunning. Unavailable, unsafe or mismatched status preserves the
active receipt and closes execution admission across restarts. Trusted missing/
interrupted worker evidence permits parent interruption. A restarted worker cannot
be its previous live instance and marks unresolved private receipts interrupted.
Healthy exact-ID/metadata observation remains available for diagnosis. No crash
protocol promises automatic exactly-once execution after history loss.

## Inspect before changing archive state

These reader metadata commands use authenticated HTTP without Hub contact,
payload hashing, archive lock or receipts:

```bash
"${HF[@]}" status
"${HF[@]}" list --revisions
"${HF[@]}" verify --estimate
```

Status may succeed while reporting degradation, unknown confidence, quarantined
bytes, unfinished transactions or unexplained entries. Existing reports are read
through authenticated `/api/v1/runs` and `/api/v1/runs/{run_id}` resources or SDK
methods; there is no public `runs` command. Inspect the exact publication and
original report identity, independently of the current query fingerprint.

Recovery preview is a reader-capable keyed job. It reads metadata and persists
receipt/event/result history, although it changes no archive state:

```bash
"${HF[@]}" recover --dry-run
```

It is subject to deployment/storage restrictions and does not establish executor
termination. Review `actionable`, `blocked` and each remedy. Apply is a separate
writer request, derives fresh evidence under the common lock and never trusts a
posted preview. Both recovery HTTP bodies are exactly `{}`. Never initialize an
existing archive; missing sentinel/health/recovery does not authorize initialization.

## Integrity failure and repair

Actual verification is an offline writer job in the private no-IP/no-credential
worker: locked preflight, payload hashing, report/catalog and receipt persistence.
It does not repair, prune or change expected digests. Full verification finding
exit 40 is different from a successful status query reporting degradation.

```bash
"${HF[@]}" verify --full
```

Preserve findings with repository, full SHA, publication ID, path, expected and
observed size/digest. The immutable manifest's expectation never changes to match
damaged bytes. If upstream still serves the immutable revision, use explicit repair;
otherwise consider an authorized snapshot restore. If neither source exists,
preserve the manifest/audit and stop rather than inventing content.

```bash
"${HF[@]}" repair model:organization/model@0123456789abcdef0123456789abcdef01234567 --reason 'digest mismatch investigation'
```

Repair requires writer capability, installed Hub authority, common lock and NAS
write acceptance. It creates receipt/history, isolated repair cache, replacement,
audit and reports. The sequence preserves original findings and damaged instance,
downloads only that immutable SHA into `.store/repair/<txn>/hub`, verifies every
path/size/SHA-256 against the original manifest, and re-reads the new immutable
publication before switching references. It uses a new publication ID but retains
publication generation and original expectations. Per-SHA reference switches first;
current switches only when it names the replaced instance. The retirement record
captures reason and old identity; the implicated canonical cache revision is removed.

Upstream mismatch refuses `HFRET006`/50 without replacing the published instance;
it can still leave isolated cache/transaction/control evidence. Do not describe
that refusal as proof of no writes. Successful earlier independent work also
survives later failure. After repair, full verification must establish clean bytes.

### Grace and quarantine

The retired locator remains readable for `repair.retired_instance_grace_hours` (at least seven days; seven days
by default), allowing pinned consumers to finish. Grace is finite; consumers fail
closed/retry a fresh current resolution if an exact locator disappears.
After grace, `recover --apply` moves the retired tree into quarantine, preserves
the original manifest byte-for-byte in repair audit and completes retirement
cleanup. It does not delete the retired tree or empty quarantine automatically.

Supported quarantine cleanup applies only to explicitly named abandoned publication
staging already rolled back by recovery. Review the IDs supplied by status:

```bash
"${HF[@]}" quarantine --dry-run 0123456789abcdef0123456789abcdef
"${HF[@]}" quarantine --apply 0123456789abcdef0123456789abcdef
```

Preview is a reader-capable receipt-producing job; apply is a separately keyed
writer/locked archive mutation. Complete batch proof precedes any removal: each
entry must be empty or redundant against freshly verified matching files in the repository's current retained
publication, with matching current/per-SHA references and manifest.
Repair quarantine, unique/unexplained bytes, unknown identities and unfinished
work refuse. Journals survive and interrupted cleanup can resume through the same
proof. No unrelated recovery or arbitrary path deletion is authorized. Quarantined
logical bytes are not uniquely reclaimable NAS space.

## Transaction refusals

Recovery prefers over-retention and stops at exit 20 when it cannot prove one
resolution. Preserve original journals, timestamps, trees and audit; do not move
journals aside, rewrite checkpoints or manually quarantine a tree to unblock work.

| Code | Evidence problem | Next step |
| --- | --- | --- |
| HFTXN001 | Unsupported/malformed journal | Use a compatible reader or authorized restore; preserve original bytes, never edit them to parse |
| HFTXN002 | Impossible checkpoint order | Establish provenance and actual filesystem state against the checkpoint contract |
| HFTXN003 | Journal/filesystem contradiction or malformed retirement evidence | Diagnose restore/deletion history; preserve named evidence and restore only through a reviewed procedure |
| HFTXN004 | Ambiguity or needs_operator state | Resolve the underlying condition with explicit evidence; never guess or discard the blocking record |

Read-only metadata and recovery previews remain diagnostic paths subject to their
own bounds and safe-read refusals. Actual verification can diagnose readable
retained data but is still a writer/locked/report-producing workload, not a
universal bypass for broken mounts or unsafe policy.

Prune and whole-repository purge share `prune_logically_committed`. Before it,
`rollback_prune` restores all manifests/trees and refs last. At/after it,
`complete_prune` finishes byte-identical manifest audit, per-revision purge reasons
and owned trash cleanup without republishing. A purge is one transaction per
repository; previous committed repositories may remain removed after a later
failure. Keep journals when choosing a rollback binary.

An interrupted download retains reusable cache but may leave publication staging.
Ordinary recovery honors `sync.stale_staging_age_hours`. The narrow supervised
zero-age exception requires exact stopped-run identity, proven executor exit,
common lock, no other unfinished work, and an empty `staging_created`-only
publication. There is no public CLI/API threshold override; posting `{}` does not
select this exception. It requires a separately reviewed procedure and grants no
general cancellation, replay or permission to edit timestamps/configuration.

## Restore from a snapshot or replica

NAS restore is separate operator work, after exact execution quiescence and an
authorized restore decision. Record damaged identities/findings, resolve or
explicitly account for open transactions, and select evidence from after the
publication but before damage. Prefer the narrowest proven scope: individual
files, one publication instance, one repository, then the whole dataset only when
necessary. Never copy directly into a publication as an ad hoc repair procedure.
Any reviewed restore must preserve original expectations and account for shared
hardlink/cache inodes, refs, journals and audit together.

Do not restore `.store/` selectively: journals, staging and cache must remain
consistent with publication state. An archive rollback does not roll back local
API/verifier stores or pending handles. Preserve/reconcile those independently;
missing history remains uncertainty. After an accepted restore, full verification
must reach clean/0 and recovery preview must show actionable 0/blocked 0. A failed
verification means the source snapshot or restore scope is wrong; expectations
never change to make it pass.

## Lost host and damaged derived metadata

Losing the writer can lose authoritative local control history even when NAS data
survives. Recover protected settings, API/verifier stores, scheduled handles and
credential delivery through an authorized replacement-host procedure; do not treat
all `/var/lib/hfcache` data as rebuildable. Preserve the existing archive UUID and
export identity, never initialize it again. Mount/sentinel/credential/read-only
acceptance must precede any workload.

Catalogs are derived convenience data; metadata readers use authoritative
manifests/references and report unknown confidence for unsafe/missing verification
catalogs. Do not delete a catalog to demonstrate reconstruction or trigger a write
on a guarded installation. Normal separately authorized writer activity maintains
its derived output; MCP/metadata reads never rebuild it.

A damaged `current.json` is an integrity finding (`HFVER008`); unreadable identity
has null SHA/publication in the report rather than invented attribution. It stays
outstanding until full verification re-reads it. Consumers fail closed. Highest
retained generation alone cannot reconstruct intended current: a valid sync can
return to an older retained SHA. Use unambiguous original references/checkpoints
and intended-current evidence; never infer from mtimes or copy a guessed reference.
If that evidence is unavailable, preserve everything and seek an authorized restore.

## Rehearse with disposable services

The repository fixtures allocate owned temporary archive policy, synthetic mount
proof, API/private-verifier stores, locks, sockets, credentials and clients. Hub
responses are fixtures; no production manager, secret, NAS export or system setting
is used. The maintenance fixture exercises repair against original expectations;
the private worker fixture covers real socket delegation, findings and restart:

```bash
uv run --locked --extra server --extra mcp pytest \
    tests/unit/test_api_maintenance.py tests/unit/test_verification_executor.py \
    tests/unit/test_cli_operations_adversarial.py --no-cov
```

Fixtures deliberately damage only their owned archive paths. They configure each
service policy and client separately, rather than passing an alternate archive
`--config` to operational commands. They test uncertainty, exact result import,
refusal and no replay; they do not certify installed no-IP/SELinux/NFS behavior.
No loopback NFS server, production service name or host setting needs changing.

## Recovery acceptance

After separately approved restoration/recovery, require exact executor/receipt
reconciliation, no unexplained actionable/blocked transactions, full verification
clean/0, and status without outstanding degradation. A deliberately authorized
sync can then establish writer readiness; it is not mandatory on the guarded
installation and must never lift its restrictions. Finish separately with an
independent consumer copy pinned to one exact publication and full local path/
size/hash verification before serving. See [consumers](consumers.md) and the
[deployment acceptance scope](deployment-status.md).
