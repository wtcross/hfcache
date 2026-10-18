# Recovering the hfcache archive

| Field | Value |
| --- | --- |
| Status | Runbook, exercised on a throwaway archive from `hfcachewriter.lab.example.com` |
| Work packages | `OPS-003` (corruption and repair), `OPS-004` (snapshot and replica restore) |
| Derived from | `docs/plan.md` §16.5, §31; `docs/architecture.md` §7.5, §7.9 |
| Companions | `docs/operations.md` for normal running, `docs/deployment-centos-stream-10.md` for building the host |

This is what to do when something is **wrong** with the archive: a revision whose
bytes no longer match its manifest, a reference that will not resolve, a
transaction that stopped and will not resume, or a host that is gone.

**The numbered historical recovery command blocks were run.** Not on `/srv/hfcache` — plan §36.5 forbids
damaging published content — but on a **throwaway archive**: a second NFSv4 export
served from the writer itself, initialized with its own UUID, synced from the real
Hub, and then deliberately broken. §6 explains how to build one, because being
able to rehearse this is the point. Dated REST/client additions describe current
repository behavior and interface examples, not commands exercised on a deployed
API installation.

In those historical blocks, `$D` is the throwaway; the original real-archive
alias was the invocation `docs/operations.md` called `$H`:

```bash
H="sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache --config /etc/hfcache/config.toml"
```

Keep that alias as provenance for the captured direct-writer results. Current
operational CLI commands use [API-only client settings and credentials](api-client.md),
with [separate service/client lifetimes](server.md#restart-and-drain). They do not
load local archive TOML or fall back to local execution. Follow the dated
observation/reconciliation sections before any recovery; installed-host rollout
and hardening checks remain explicit deployment holds.

---

## 1. Finding out that something is wrong

Three things tell you, in decreasing order of how much you will like hearing it.

**`status` says the archive is degraded.** The per-repository line reads `failed`
rather than `verified`, and a line goes to **stderr**:

```text
$ hfcache status
model:hf-internal-testing/tiny-random-gpt2  enabled  failed
archive degraded: 1 outstanding verification failures
exit=0
```

`status` still exits `0`. It reports; it does not adjudicate. The exit code that
means corruption comes from `verify`.

**`verify --full` exits `40`.** This is the quarterly job's answer, and the one a
scheduler sees:

```text
$ hfcache verify --full
bytes read    11.9 MiB
findings      1
objects read  10
outcome       failed
report        runs/20260727T143705Z-793e9c8787ea42e387ac15ebe0216a1d.json
repositories  1
revisions     1
HFVER001 (model:hf-internal-testing/tiny-random-gpt2): 1 digest_mismatch finding in model:hf-internal-testing/tiny-random-gpt2
exit=40
```

**The finding names the object.** `--json` carries what you need to decide:

```json
{
  "commit_sha": "71034c5d8bde858ff824298bdedc65515b97d2b9",
  "expected": "9ad49cd2ff58daa38243e4eeaac13b1259786d9418e45bfc01a1fd1fe1089e77",
  "kind": "digest_mismatch",
  "observed": "cb83ee975a0cc7cb251789216e28e978703643a03cb30a5a877d1cf420bfaab4",
  "path": "config.json",
  "publication_id": "edb94772f09d45dba2c6ecb80e52c4fa",
  "repository_id": "hf-internal-testing/tiny-random-gpt2",
  "repository_type": "model"
}
```

`expected` comes from the immutable manifest and `observed` from reading the bytes
now. **The archive never rewrites `expected` to match `observed`.** That is the
one rule the whole of repair is built to preserve (`AD-13`).

### Which way to go

| What you have | What to do |
| --- | --- |
| Upstream still has the revision | **Repair** — §2. Re-downloads the same immutable SHA and verifies it against the original manifest |
| Upstream is gone, but you have snapshots | **Restore** — §7. ZFS gives back the bytes that were there |
| Neither | Preserve everything and stop. The manifest and the audit records still prove what was there |
| A transaction stopped and commands exit `20` | §5 — the machine has stopped on purpose |

Do not delete the damaged revision to "clean up". It is evidence, it is what a
repair verifies against, and nothing else in the archive is at risk from it.

---

## 2. Repairing a revision from upstream

```bash
$H repair model:<org>/<name>@<full-sha> --reason "what prompted this"
```

The SHA must be the full 40 characters. `--reason` is recorded in the retirement
record and is how someone reading `audit/repairs/` in six months finds out why.

```text
$ hfcache repair model:hf-internal-testing/tiny-random-gpt2@71034c5d8bde858ff824298bdedc65515b97d2b9 \
    --reason "digest_mismatch on config.json, found by quarterly verification"
commit sha     71034c5d8bde858ff824298bdedc65515b97d2b9
grace expires  2026-08-03T14:37:18.004675+00:00
replacement    ad8d5a64672a48199289efcfb65ad7fb
retired        edb94772f09d45dba2c6ecb80e52c4fa
transaction    96c73340a0c4467cb4fec8a5a1264fa7
exit=0
```

What that did, in the order §7.5 fixes it:

1. Preserved the verification findings and the corrupt instance as evidence.
2. Made an **empty, isolated cache** at `.store/repair/<txn>/hub`. In hardlink
   mode the corrupt published file and its cache blob are the same inode, so
   re-downloading into the canonical cache could reuse the very object under
   suspicion. This is `FS-14`'s one exception and the reason it exists.
3. Downloaded the same immutable SHA into that cache only.
4. **The gate.** Verified every path, size, and SHA-256 against the *original*
   manifest. A single difference stops the transaction with `HFRET006` and leaves
   the published revision untouched.
5. Published the replacement under a **new publication id**, at a new immutable
   locator, and re-read it *from where it now lives* before any reference moved.
6. Switched `refs/revisions/<sha>.json`, then `refs/current.json`.
7. Wrote the retirement record and deleted the implicated canonical cache
   revision.

Afterwards the archive is clean and the repaired revision verifies:

```text
$ hfcache verify --full
findings      0
objects read  10
outcome       clean
exit=0
$ hfcache status
model:hf-internal-testing/tiny-random-gpt2  enabled  verified
```

**The generation does not change.** A repair replaces an instance, not a
revision, so retention order is untouched — the repaired SHA keeps its place and
`prune` still selects by the same key it always did.

**The original manifest is not rewritten.** Both manifests exist afterwards; the
replacement copies the original's expectations byte-identically and adds a
`repair` block naming what it replaced:

```json
{"reason": "…", "repair_of": "edb94772f09d45dba2c6ecb80e52c4fa",
 "repair_of_manifest": "published/manifests/…/edb94772f09d45dba2c6ecb80e52c4fa.json",
 "repaired_at": "…", "transaction_id": "96c73340a0c4467cb4fec8a5a1264fa7"}
```

### When a repair refuses

If the download does not match the original manifest, the command stops with
`HFRET006` at exit `50` and **changes nothing**. That is not a failure of the
tool. It means upstream no longer serves the bytes this archive recorded for that
SHA, and the archive is right to keep saying so. Go to §7 — a restore is the
remaining option, and if that is not available, what you have is the manifest and
the audit trail, which is still a true account of what was there.

---

## 3. The grace period

The repaired instance is live immediately, but the **retired one stays exactly
where it was** for the configured grace (seven days by default). A consumer that
resolved the old locator before the switch can finish its copy.

```text
$ ls published/repos/…/revisions/71034c5d…/
ad8d5a64672a48199289efcfb65ad7fb        <- the replacement, named by current.json
edb94772f09d45dba2c6ecb80e52c4fa        <- retired, readable until the grace expires
```

Inside the grace, recovery deliberately does nothing:

```text
$ hfcache recover --dry-run
actionable  0
applied     -
blocked     0

  remedy=wait
  reason=the retired instance is readable until 2026-08-03T14:37:18.004675+00:00,
         so an in-flight consumer copy can still finish
```

This is why `docs/consumers.md` tells a consumer to treat a vanished tree as
retryable: the grace is generous, but it is finite.

---

## 4. After the grace: quarantine, not deletion

Once the grace expires, `status` starts warning and names the command that
finishes it:

```text
HFWRN008 (model:…) [published/repos/…/edb94772f09d45dba2c6ecb80e52c4fa]: the retired
instance edb94772f09d45dba2c6ecb80e52c4fa of model:…@71034c5d… passed its grace period
at 2026-07-22T00:00:00+00:00 and awaits cleanup; `hfcache recover --apply` performs it
```

```text
$ hfcache recover --dry-run
actionable  1
blocked     0
  remedy=finish_repair_cleanup
  reason=the grace period expired, so the retired instance is quarantined and archived

$ hfcache recover --apply
actionable  1
applied     1
blocked     0
exit=0
```

The retired tree is **moved, never deleted**:

```text
published instances now:
  ad8d5a64672a48199289efcfb65ad7fb

.store/quarantine/96c73340a0c4467cb4fec8a5a1264fa7/
  .gitattributes  config.json  merges.txt  model.safetensors  pytorch_model.bin
  special_tokens_map.json  tf_model.h5  tokenizer.json  tokenizer_config.json  vocab.json

audit/repairs/models/…/71034c5d…/
  edb94772f09d45dba2c6ecb80e52c4fa.manifest.json     <- the original, byte for byte
  edb94772f09d45dba2c6ecb80e52c4fa.retirement.json   <- now cleanup: completed
```

```text
$ hfcache --json status | jq '.data.archive | {quarantined_bytes, deferred_cleanup}'
{"quarantined_bytes": 12512611, "deferred_cleanup": 0}
```

**Quarantine is retained until you decide otherwise.** No schedule removes it
(plan §16.5 item 12). Repaired or unvalidatable published trees remain evidence;
the supported cleanup below deliberately excludes them. Do not manually delete
archive paths (`docs/agents/environment.md`).

For abandoned publication staging that recovery has already rolled back, use
the exact transaction IDs shown by `status` or the Cockpit Overview:

```text
hfcache quarantine --dry-run TRANSACTION_ID ...
hfcache quarantine --apply TRANSACTION_ID ...
```

Review the dry run before applying the same explicit IDs. Empty directories are
eligible; remaining files must first be proven identical to verified files in
the repository's current retained publication. The command preserves journals
and refuses unique or unexplained evidence. It can safely resume an interrupted
cleanup and does not require manually editing the archive. `status` then omits
the removed entries, and refreshing Cockpit updates the Findings table.
`recover --apply` itself never empties quarantine. `quarantined_bytes` reports
the logical file bytes still held there, not uniquely reclaimable NAS space.

### Maintenance after an intentionally stopped download

The historical direct-service procedure stopped the actual sync with
`systemctl stop hfcache-sync.service`. That preserves its Hub
download cache but can leave an open publication journal. Ordinary recovery
still waits for `sync.stale_staging_age_hours`; stopping the service does not
silently waive that rule. When the operator explicitly chooses immediate
maintenance followed by restart, architecture §7.8.2 permits a supervised
exception for the exact stopped run's proven empty, `staging_created`-only
publication. Confirm the actual writer/executor has exited, hold the writer lock, reject
other unfinished work, and review the exact identities and empty staging before
using the installed recovery planner with a zero-hour threshold. Apply through
the normal recovery API and preserve its journals and report. Do not edit the
configuration, timestamps, source journals, or download cache to force recovery.
Explicitly clean the resulting empty quarantine along with the original
reviewed entries, then restart the sync service and restore its timer. A
download interrupted after later checkpoints or with populated staging does
not qualify for this exception.

For API-backed execution, a stopped CLI/systemd client or closed Cockpit session
is not proof that accepted work ended. Identify the exact operation, its domain
run/transactions and real daemon/verifier executor; reconcile exact worker status
or durable outcome before considering interruption. A PID or released lock alone
is insufficient. API-014 now packages observer clients and the actual API/private
executor; stop activation and drain/prove those executors, not just their clients.
Keep the verifier available while API outcome handoff completes, then stop/drain
its socket/service. Retain scheduled pending handles and both operation stores;
unknown/malformed/future history is preserved, never reset to replay. The supervised zero-age exception above still
requires every original identity/emptiness/lock check and grants no general
cancel/replay authority. See [decision 115](adr/decision-115.md),
[121](adr/decision-121.md) and
[deployment quiescence](deployment-centos-stream-10.md#13-upgrade-plan-30).

---

## 5. When the machine stops (`HFTXN001`–`HFTXN004`)

Automatic recovery halts, changes nothing, and exits `20` when it finds a state
it may not resolve (§7.9). `status`, `list`, `verify`, and `recover --dry-run`
still work, so you always have a way to look.

All four were provoked on the throwaway.

### Interrupted repository purge

Purge deliberately reuses the prune journal and its
`prune_logically_committed` boundary. `recover --dry-run` therefore reports the
same remedy names with complete-repository meaning:

- `rollback_prune` before that checkpoint restores every manifest and tree,
  then restores the complete `refs/` directory last. The repository is again
  consumer-visible in full.
- `complete_prune` at or after that checkpoint does not republish the repository.
  It finishes byte-for-byte manifest archival, one purge-reason record per
  revision, and transaction-owned trash cleanup.

Do not move an open purge journal aside merely to unblock sync: doing so discards
the record that says whether restoration or completion is safe. Run
`recover --dry-run`, then `recover --apply` when the plan is actionable. A purge
journal from a newer release also makes rollback across that release unsafe until
the purge is resolved.

### `HFTXN001` — a journal this release does not understand

```text
HFTXN001 [.store/transactions/aaaa….json]: schema_version 99 is newer than 1, which is
what this release understands; refusing to read it rather than guess at its meaning
exit=20
```

Also raised by a journal that is damaged rather than merely newer — a truncated
or hand-edited file fails validation and is reported the same way, naming the
field:

```text
HFTXN001 [.store/transactions/dddd….json:<root>]: Value error, last_checkpoint_at is
set exactly when at least one checkpoint exists
```

**What to do.** If the version is *newer*, you have rolled back across a format
change — roll forward again, or if you meant to roll back, see
`docs/deployment-centos-stream-10.md` §14. If the journal is *damaged*, the
transaction it describes cannot be reconstructed from it; move it aside into a
directory outside `.store/transactions/`, keep it, and run `verify --full` to
establish what the archive actually holds. Do not edit it to make it parse.

### `HFTXN002` — a checkpoint sequence no valid execution produces

```text
HFTXN002 [bbbb…]: publication journal bbbb… records checkpoints ['staging_created',
'download_completed', 'staging_built', 'content_hashed'], which is not a prefix of the
documented sequence [...]; no valid execution produces this combination
exit=20
```

**What to do.** The journal did not come from a run of this application, or it
has been altered. Preserve it, and treat the archive as unknown until
`verify --full` has read it. The checkpoint sequences are in
`docs/architecture.md` §7.3–§7.6 if you need to work out how far the operation
had actually got.

### `HFTXN003` — journal evidence that contradicts the filesystem

```text
HFTXN003 [revision_tree_renamed.published_tree_path]: checkpoint revision_tree_renamed
recorded published_tree_path=published/repos/models/…/eeee…, but /srv/hfcache/published/
repos/models/…/eeee… does not exist; the journal and the archive disagree about what happened
exit=20
```

Every checkpoint carries re-observable evidence, and recovery confirms it by
looking rather than by trusting the record (`TX-03`). This is that check failing.

**What to do.** Something removed a path the archive believed it had written.
That is usually a restore that went back further than the journal, or a manual
deletion. Establish which with `verify --full`, then §7. The named path is the
one to start from.

This is also the code `REP-001` now raises when a retirement record cannot be
parsed — the repair is committed but whether its retired instance still awaits
quarantine can no longer be determined. Restore that record from a snapshot if
you have one; otherwise the retired tree is identifiable from the journal's
`retired_tree` evidence and can be quarantined by hand.

### `HFTXN004` — two equally valid resolutions, or a transaction that asked for you

```text
HFTXN004 [dddd…]: transaction dddd… stopped and asked for an operator; recovery never
resolves what it was told not to
exit=20
```

```text
$ hfcache --json recover --dry-run | jq '.data'
{"actionable": 0, "blocked": 1, "plan": [{"remedy": "operator", ...}]}
```

**What to do.** A previous run set `state = "needs_operator"` because *it* could
not decide, and recovery will not overrule that. Read the journal: its
`checkpoints` say exactly how far the operation got, and `docs/architecture.md`
§7 says what each boundary means. Resolve the underlying condition, then either
complete the work by hand following the checkpoint sequence, or — far more often —
accept the over-retention and let the next run proceed by moving the journal
aside once you have established the archive is consistent.

### The general shape

Whatever the code, the sequence is the same:

```bash
$H recover --dry-run          # what it thinks, without touching anything
$H verify --full              # what is actually on disk
# … decide, act, then …
$H recover --dry-run          # confirm there is nothing left
$H verify --full              # confirm the archive is clean
```

Nothing in this section is time-critical. A stopped archive is still serving
consumers from `published/`; what has stopped is *writing*.

---

## 6. Building a throwaway archive to rehearse on

Everything above was run against one, and it is worth having. It is a second
NFSv4 export served by the writer to itself, so it needs no NAS change and cannot
touch the real dataset.

```bash
# a local directory, exported to this host only
sudo install -d -m 0750 -o hfcache -g hfcache /srv/hfcache-throwaway-src
echo '/srv/hfcache-throwaway-src 127.0.0.1(rw,sync,no_subtree_check,fsid=77)' \
  | sudo tee /etc/exports.d/hfcache-throwaway.exports
sudo systemctl start nfs-server && sudo exportfs -ra

# mount it — the export path, not the NFSv4 pseudo-root, which is read-only
sudo install -d -m 0755 /mnt/hfcache-throwaway
sudo mount -t nfs4 -o rw,hard,proto=tcp \
  127.0.0.1:/srv/hfcache-throwaway-src /mnt/hfcache-throwaway
```

The archive root **must** be a mount point of type `nfs`/`nfs4`; preflight checks
`/proc/self/mountinfo` and there is no override. Then give it its own config with
its **own `archive_id`**, and initialize it:

```bash
D="sudo -u hfcache HF_HOME=/var/tmp/hfcache-drill/hf \
   /opt/hfcache/current/.venv/bin/hfcache --config /var/tmp/hfcache-drill/config.toml"
$D archive init --archive-root /mnt/hfcache-throwaway \
    --archive-id 9c2f1e40-8a55-4b31-90ad-7e6c4d2b8f13 --confirm
$D doctor && $D sync
```

`doctor` passes all 17 checks against it, including the hardlink, atomic-rename,
and reference-replacement probes — which is what makes a rehearsal here mean
something.

Tear down when finished:

```bash
sudo umount /mnt/hfcache-throwaway
sudo rm -f /etc/exports.d/hfcache-throwaway.exports
sudo exportfs -ra && sudo systemctl stop nfs-server
sudo rm -rf /srv/hfcache-throwaway-src /mnt/hfcache-throwaway
```

**Never point a throwaway config at `/srv/hfcache`**, and never re-run
`archive init` against it. The real archive was initialized once, on 2026-07-26,
and that authorization is spent.

---

## 7. Restoring from a ZFS snapshot or replica

Use this when the bytes are gone or wrong and **upstream cannot supply them** —
the repository was deleted or gated, or `repair` refused because upstream no
longer serves what the manifest recorded.

The ZFS side is operator work on TrueNAS and is not something this application
does or can do. What is written here is the procedure around it: what to
establish first, what to restore, and what to run afterwards.

### Before you restore

```bash
$H verify --full          # exit 40, and the findings name every damaged path
$H recover --dry-run      # is anything mid-transaction?
$H --json status | jq '.data.archive'
```

Three things to establish, in this order:

1. **What is actually damaged.** The findings name repository, SHA, publication
   id, and path. Restoring the whole dataset when one file is wrong throws away
   good revisions published since the snapshot.
2. **Whether a transaction is in flight.** If `recover --dry-run` reports
   anything actionable or blocked, resolve that *first* — §5. A restore
   underneath an open transaction produces exactly the journal-contradicts-
   filesystem state `HFTXN003` exists to report.
3. **Which snapshot predates the damage.** The manifest's `published_at` and the
   run report in `runs/` bound when the revision was written; a snapshot from
   before the damage but after the publication is what you want.

### Restoring

Prefer the **narrowest** restore that covers the findings. In descending order of
preference:

| Scope | When |
| --- | --- |
| Individual files out of `.zfs/snapshot/<name>/` | A handful of paths, all named by findings |
| One publication instance directory | Many paths in one revision |
| One repository subtree | Several revisions of one repository |
| The whole dataset | The dataset is lost; see §8 |

Restoring individual files from a snapshot is a copy back into place, done on the
NAS or over the writer's mount, as the identity that owns the tree. It is safe
precisely because published trees are immutable: nothing else writes there, so a
file replaced with its own earlier bytes is not racing anything.

**Do not restore `.store/` selectively.** The cache, journals, and staging areas
are internally consistent with each other and with `published/`; mixing a
restored journal with a current tree is how you manufacture `HFTXN003`. If
`.store/` has to come back, take the whole dataset (§8).

### After you restore — this part is not optional

```bash
$H verify --full          # must reach exit 0
$H recover --dry-run      # must report actionable 0, blocked 0
$H status
```

`verify --full` is the only thing that establishes a restore worked. It re-reads
every retained revision against its manifest, so it will tell you both that the
damage is gone and that the restore did not bring back something stale. Plan
§16.3 lists restoration from snapshot or replica as an event requiring a full
verification for exactly this reason.

If verification still fails, the snapshot predates the publication or postdates
the damage. Try an earlier one; the manifest's expectations never change, so
there is no risk of "converging" on wrong bytes.

---

## 8. A lost writer, and rebuilding derived state

### The writer VM is gone

Nothing archive-side is lost with it. The writer holds no authoritative state:
`/srv/hfcache` is on the NAS, and `/opt/hfcache`, `/etc/hfcache`,
`/var/lib/hfcache`, and `/var/cache/hfcache` are all rebuildable.

1. Provision a replacement with the **same hostname and IP**
   (`hfcachewriter.lab.example.com`, `192.0.2.90`). The NFS export is
   scoped to that exact host, so a different address does not get write access —
   which is the export doing its job.
2. Follow `docs/deployment-centos-stream-10.md` from the top, with one
   exception: **do not run `archive init`.** The archive exists and has an
   identity. Put its existing UUID in `/etc/hfcache/config.toml`.
3. `$H doctor` — the sentinel check is what proves the new host is talking to the
   right archive.
4. `$H verify --full` and `$H recover --dry-run`.

The sentinel is the guard here. If `doctor` reports the archive id does not match
configuration, stop: either the config has the wrong UUID or the mount is
pointing somewhere unexpected, and both are better found now.

### Rebuilding the catalog

`published/catalog/repositories.json` is **derived** and always reconstructible
(`FS-16`). Destroying it costs nothing:

```text
$ rm published/catalog/repositories.json
$ hfcache list
model:hf-internal-testing/tiny-random-gpt2  1 revisions  current 71034c5d8bde858ff824298bdedc65515b97d2b9
$ hfcache status
model:hf-internal-testing/tiny-random-gpt2  enabled  verified
```

`list` and `status` still answer, because they read manifests and references
rather than the catalog. Any sync rebuilds it:

```text
$ hfcache sync
model:hf-internal-testing/tiny-random-gpt2  skipped  71034c5d8bde858ff824298bdedc65515b97d2b9
$ ls published/catalog/repositories.json
published/catalog/repositories.json
```

The catalog is a convenience for readers, never a source of truth. If it and the
manifests disagree, the manifests are right.

### A damaged `refs/current.json`

This is §31's "damaged current ref". `current.json` is the one file a consumer
must read, and it is **derived from the retained set**: the correct value is the
reference for the highest `publication_generation` among the SHAs that have a
`refs/revisions/<sha>.json`.

Full verification checks it (`VER-008`). A `current.json` that names an instance
the per-SHA reference does not is `HFVER008` at exit `40`:

```text
$ hfcache verify --full
outcome       failed
revisions     2
HFVER008 (model:hf-internal-testing/tiny-random-gpt2): 1 ref_invalid finding in model:…
exit=40
```

A `current.json` that will not parse at all is just as loud since `VER-009`
(0.1.3): `verify --full` reports it as `HFVER008` at exit `40`, with a finding
whose `commit_sha` and `publication_id` are null — the damage is the pointer
itself, and attributing it to a retained revision would assert exactly what the
unreadable file failed to say. The failure stays outstanding, and `status`
reports the archive degraded, until a `--full` re-reads the reference; a
consumer using `examples/copy-revision.py` fails closed at exit `2` throughout.
Observed on a throwaway archive, release 0.1.3 (`REL-004`'s drill):

```text
$ hfcache verify --full
outcome       failed
findings      1
revisions     2
HFVER008 (model:hf-internal-testing/tiny-random-gpt2): 1 ref_invalid finding in model:…
exit=40
$ hfcache status
model:hf-internal-testing/tiny-random-gpt2  enabled  unverified
archive degraded: 1 outstanding verification failures
```

and the finding in the report, attributed to nothing because the pointer itself
is the damage:

```json
{"commit_sha": null, "kind": "ref_invalid", "path": null, "publication_id": null,
 "observed": "the current reference could not be read: not valid JSON: …"}
```

On releases before 0.1.3 this case was quiet — `verify --full` reported `clean`
and only `status`'s `unverified` hinted at it — so on an old release, if
`status` says `unverified` for a repository whose revisions all verify, read
`current.json` by hand.

To reconstruct it:

```bash
# what the archive retains, and which generation is newest.
# --json is a *global* option and goes before the subcommand; `list --json`
# is "No such option" at exit 2.
$H --json list --revisions | jq '.data.repositories[].revisions'
# the per-SHA reference for that generation is the correct content
cat published/repos/<type>/<org>/<repo>/refs/revisions/<sha>.json
```

Observed:

```text
$ hfcache --json list --revisions
  hf-internal-testing/tiny-random-gpt2  [('71034c5d', 1)]
```

Copy that file to `current.json` — the two schemas are identical
(`docs/schemas.md` §4.2) — then re-verify. **Never choose a revision by directory
modification time** (§31): a backup, a restore, or a repair changes mtimes, and
the generation is the only ordering key that does not move (`AD-05`).

If the per-SHA references are also gone, the manifests still carry
`publication_generation` and can be read directly. If those are gone too, what
remains is `audit/`, which is enough to prove what the archive held but not to
serve it — restore from a snapshot.

---

## 9. Acceptance: what "recovered" means

An archive is recovered when all four of these hold, in this order:

```bash
$H recover --dry-run      # actionable 0, blocked 0
$H verify --full          # exit 0, outcome clean
$H status                 # exit 0, no "archive degraded" line on stderr
$H sync                   # exit 0
```

The last one matters and is easy to skip. `sync` is the first thing that takes
the exclusive lock and reconciles journals *before* contacting the Hub (`TX-07`),
so a clean sync is the proof that the archive will accept writes again — which is
the thing an interrupted transaction takes away.

Then, from a consumer, one copy end to end:

```bash
python3 copy-revision.py --mount /mnt/hfcache --type model \
  --repository <org>/<name> --destination ./check
```

That exercises the path a downstream machine actually depends on, and it is the
only check in this document that is performed from outside the writer.

## 10. Operation history and uncertain submissions

API-007's local operation receipts are control-plane history, separate from the
archive's reports, manifests and transaction journals. The service-private state
directory defaults to `/var/lib/hfcache/api/`; preserve it through backup,
credential rotation, restart and rollback. It contains no credential or raw
idempotency key. Do not copy it into the consumer export or treat a restored
archive snapshot as a restoration of operation history.

Operation observation requires a valid REST reader or writer credential, like
run-report access. An operation ID selects metadata; it grants no authority.
Idempotency lookup additionally searches only the authenticated credential-class
namespace. Rotation retains that coarse identity; changing from writer to reader
is a different lookup namespace. No individual-submitter attribution is promised.
API-007 supplies observation/admission primitives; API-009/010 now expose typed
command submissions. API-013 now supplies public CLI show/wait/lookup and explicit
detach, retaining exact terminal domain Envelopes.

When an acknowledgement is lost, look up the original key without submitting
another command. A match identifies the original operation even if archive policy
has changed. A key/request conflict is a refusal, not an invitation to change the
key. A missing/expired receipt means the server cannot establish the outcome;
it does not prove that work never ran. Never automatically replay an uncertain
mutation after receipt expiry, state loss or rollback to a binary that cannot
read this history.

After a restart, existing nonterminal receipts are never automatically queued.
API-007 opens the store without changing their state; a retained `running` label
is not proof of liveness. The explicit interruption primitive records unresolved
work as `interrupted`; API-008 must reconcile exact surviving workers first.
`interrupted` describes uncertainty; it is neither a domain failure report nor
permission to repeat the action. Use existing validated run,
report and transaction evidence to diagnose archive state through this runbook.
A PID, released flock, elapsed timeout, vanished client or disconnected socket is
insufficient proof of completion or termination. API-008 identifies the exact
surviving verifier operation and durable outcome before reattaching. Unavailable
or unsafe status preserves active evidence and closes execution admission across
restarts; it does not prove the worker ended.

Keep malformed, unknown-version, unsafe, interrupted, ambiguous and nonterminal
records. Do not delete them to make admission succeed. Preserve an incident copy
and diagnose the classified storage problem with a compatible binary; do not
hand-edit a receipt into success or reconstruct missing submissions from journals.
Such state can block new admission while healthy operation IDs remain observable.

Only validated application-owned succeeded/failed receipts and their results may
expire after the configured period, default 30 days. The service refuses new
admission when count/space reservations do not fit, rather than shortening that
window or deleting uncertain evidence. Restore capacity by addressing storage or
retention policy under operator control, not by removing unexpired bindings.
Changing retention is an explicit retry-history decision; communicate the new
window to callers. There is no automatic exactly-once guarantee across crashes.
See [the receipt schema](schemas.md#13-service-private-operation-control-state-api-007)
and [decision 114](adr/decision-114.md).

**API-008 reconciliation.** The execution runner examines existing nonterminal
receipts before accepting fresh execution. For verification it asks the protected
private executor about the exact operation/fingerprint and archive identity.
A matching terminal Envelope can close the API receipt without rerunning work;
a matching live operation is awaited/reattached. Only unresolved history is
classified interrupted. Ordinary old queued/running commands are never requeued.
If the worker is unavailable or its identity/outcome cannot be proved, preserve
the active API receipt and keep execution admission closed across restarts.
Metadata/healthy exact-ID reads remain available for diagnosis. Do not change the
receipt to interrupted merely to get past the next startup: that would discard
the execution barrier while an unreachable worker may still run. Trusted missing/
interrupted worker evidence permits parent interruption; restored exact live or
terminal status permits reattachment/result recovery. Do not use a new key to
retry automatically.

The worker's own separate store uses the existing schema and a retained sibling
instance lock. A restarted executor cannot be the previous live instance; it
marks unresolved private receipts interrupted rather than restarting them.
Never delete or merge API/verifier stores to make a result appear complete, and
never unlink a potentially held instance/store/archive lock. A saved worker
terminal result is execution evidence; a lost observer, free lock, PID or old
`running` label is not. See [decision 115](adr/decision-115.md) and
[server restart/drain](server.md#restart-and-drain).

## 11. REST maintenance without stale authority (API-010)

This section describes hermetic HTTP/domain acceptance, not an installed service
rollout. API-013's CLI uses these resources without a direct local backend. Separate
preview/apply [maintenance resources](api.md#implemented-maintenance-resources-api-010)
call the same services and retain all refusal/recovery rules above. Previews are
keyed read-capable jobs, not executable capabilities. Writer apply submits only
strict explicit scope; no preview/result body or proof is trusted. The runner
revalidates admitted policy under the service-owned archive lock before domain
work, and the shared service derives fresh scope and evidence there.

Purge still refuses a configured/newly configured repository and unknown shallow
entries. Recovery preserves blocked-plan diagnostics and does not guess among
ambiguous outcomes. Quarantine proves every selected transaction and retained
replacement before removing any batch entry; it refuses repair/unique/unknown
content and unfinished work without recovering unrelated transactions. Repair
retains original manifest expectations, generation, audit and grace-period rules.
Prune/purge interruption follows the existing pre/post-logical-commit boundary;
no new checkpoint or HTTP-specific recovery algorithm is introduced.

A lost acknowledgement or observation is not cancellation or proof of nonexecution.
Look up the original key, inspect its exact operation, then retrieve its exact
terminal Envelope, including domain exit/refusal and partial diagnostics. Do not
resubmit uncertain work with a new key, hand-edit history or reconstruct commands
from journals. Operation history loss remains uncertainty even when archive
recovery can explain some filesystem evidence.

Initialization is separately disabled by default, requires writer confirmation
and restated configured root/UUID, and uses its own locked known-layout checks.
The maintenance switch gates initialization only. Disabled initialization POST
retries remain refused while authenticated original history/lookup stays available.
Neither recovery, health nor missing sentinel triggers initialization; this
archive already exists and must not be initialized again.

## 12. Client uncertainty and finite observation (API-011)

The [typed client](api-client.md) generates or accepts one nonsecret key before
POST and exposes it before transmission. HFAPI020 retains that original key/route
when acknowledgement cannot be established, including malformed/truncated or
wrong-identity 202 and untrusted error bodies after transmission; it never
retries with a new key or
falls back to local archive mutation. Authenticated lookup with the same key is
observation only. Missing/expired history remains uncertainty, as §10 explains.

HFAPI019 connectivity or a finite polling deadline stops observation without
cancelling accepted server work. Continue diagnosis using the known operation ID
and original binding; old receipts/results retain their admitted archive UUID /
fingerprint and exact domain run/result rather than current policy metadata.
Protocol/version/identity failures (HFAPI018) are not evidence of command failure
or nonexecution. Do not change endpoint/expected archive identity merely to make
an unrelated operation response appear valid.

**API-013 CLI observation.** A keyed command prints its validated original key
before POST and its operation ID after acceptance, even in quiet mode. Default
output waits for the exact terminal server Envelope; explicit detach identifies
admission separately and grants no completion claim. Preserve both handles when
the observer times out, receives Ctrl-C or loses connectivity. HFAPI019/20 stops
waiting only; HFAPI020/20 retains uncertain acknowledgement. Other classified
errors keep their taxonomy and known handles. Accepted work may continue.

Use authenticated `operations lookup -- '<original-key>'` without submitting,
then `operations show ID` / `operations wait [--after N] -- '<operation-id>'`
under the same intended authority. Quote the key and use `--` so option-like or
tilde-prefixed keys remain literal arguments.
Show/lookup preserve exact metadata Envelopes; wait returns the stored terminal
domain Envelope, including failure/partial results. All event/status/result reads
share one finite observation deadline, and explicit retention gaps accompany
resumed event cursors. A stopped observer service, process or browser is not proof
that the writer/verifier stopped. Do not start a new-key duplicate, cancel work,
delete history or release mounts because the observer ended. Follow §10 and the
server drain/reconciliation procedure. See [decision 120](adr/decision-120.md),
[CLI operations](cli.md#operations) and
[client resume](api-client.md#submit-detach-and-resume-api-013).
