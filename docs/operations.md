# Operating hfcache

| Field | Value |
| --- | --- |
| Status | Runbook, exercised on `hfcachewriter.lab.example.com` |
| Work package | `OPS-002` |
| Derived from | `docs/plan.md` §11.2, §15, §16, §24, §29; `docs/cli.md` |
| Companion | `docs/deployment-centos-stream-10.md` for getting it up in the first place |

Day-to-day operation: what each command reports, what every exit code means and
what to do about it, how to read a run report and the journal, what each warning
code is telling you, and how to administer the timers.

**Every command block below was run on this deployment.** Where output is
abbreviated it is marked with `…`; nothing is invented.

Throughout, `$H` stands for the invocation an operator uses. Scheduled runs use
exactly the same commands, which is what makes a behaviour reproducible by hand:

```bash
H="sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache --config /etc/hfcache/config.toml"
```

The service account has a `nologin` shell; invoking the binary directly works
anyway, and that is the supported way to exercise the CLI as the identity the
timers use. Running as yourself will fail — `/etc/hfcache/config.toml` is
`0640 root:hfcache`.

---

## 1. Is the archive healthy?

`status` is the first command and answers in one screen.

```text
$ hfcache status
model:hf-internal-testing/tiny-random-gpt2  enabled  verified
dataset:hf-internal-testing/fixtures_ade20k  enabled  verified
exit=0
```

The human form is deliberately thin. The answer to "is anything wrong" is in
`--json`, and that is the form to use when you are actually investigating:

```bash
$H --json status | python3 -m json.tool
```

```json
{
  "archive": {
    "archive_id": "00000000-0000-0000-0000-000000000000",
    "available_gib": 36037.6,
    "deferred_cleanup": 0,
    "findings": [],
    "quarantined_bytes": 0,
    "reachable": true,
    "unfinished_transactions": 0,
    "unknown_entries": [],
    "verification": {
      "degraded": false,
      "last_full_verification": { "outcome": "clean", "unique_objects": 23, "…": "…" },
      "outstanding_failures": 0
    }
  },
  "repositories": [ { "…": "…" } ]
}
```

The six fields to read, and what a non-default value means:

| Field | Healthy | If not |
| --- | --- | --- |
| `reachable` | `true` | The mount is gone. Nothing will run; see §7 |
| `unfinished_transactions` | `0` | A run stopped part way. `recover --dry-run` (§6) |
| `findings` | `[]` | Warnings are outstanding. Each carries an `HFWRN` code; §8 |
| `unknown_entries` | `[]` | Files the application cannot explain, preserved not deleted |
| `verification.degraded` | `false` | A verification found something. §4 |
| `deferred_cleanup` | `0` | A prune committed but its bytes are still on the dataset; §5 |

`verification_state` per repository is keyed on the **publication instance**, not
the SHA — a revision that was pruned and later re-synced is a different instance
and reads unverified until something re-reads it (decision 62).

---

## 2. What is archived?

```text
$ hfcache list
dataset:hf-internal-testing/fixtures_ade20k  5 revisions  current 850d349e5038f291284e7999fcacbedc0922534b
model:hf-internal-testing/tiny-random-gpt2   1 revisions  current 71034c5d8bde858ff824298bdedc65515b97d2b9
exit=0
```

Three revisions is the default steady-state maximum per repository (`AD-04`);
the example above uses an explicit five-revision policy. One means
the repository has only ever published once, not that anything is wrong.

`list` reports what is **archived**, which is not the same as what is
configured. A repository removed from `config.toml` keeps every revision it has
and continues to appear here — removal from configuration never deletes anything
(`AD-06`). The human line does not distinguish the two; `--json` carries
`"managed": false` for a repository the archive holds but configuration no longer
names, and `status` reports it as `HFWRN007`.

Selectors restrict the *configured* set, so passing one never hides an unmanaged
repository you did not ask about by name.

---

## 3. What would a sync do?

`plan` resolves every configured repository against the Hub and reports the work
without downloading anything.

```text
$ hfcache plan
[dry-run] Fetching 10 files: 100%|██████████| 10/10 [00:00<00:00, 1844.70it/s]
[dry-run] Fetching 7 files: 100%|██████████| 7/7 [00:00<00:00, 1115.51it/s]
model:hf-internal-testing/tiny-random-gpt2@main  71034c5d8bde858ff824298bdedc65515b97d2b9  10 files, 11.9 MiB, 0 B new
dataset:hf-internal-testing/fixtures_ade20k@main  850d349e5038f291284e7999fcacbedc0922534b  7 files, 201.3 KiB, 0 B new
exit=0
```

`0 B new` means the private cache already holds every byte, so a sync would
resolve and skip. The two numbers are not interchangeable and both matter:
the size of the revision, and how much of it is not already here.

The `[dry-run] Fetching` lines are `huggingface_hub`'s own progress on **stderr**,
not hfcache's. Redirect stderr if you are scripting `plan`. They do not reach
journald, because `plan` is not a unit — the scheduled units have never logged a
progress line.

**This is the command to run before adding a production repository.** It reports
the dry-run size the TrueNAS quota decision needs, without downloading.

---

## 4. Syncing

### Restricted repositories

Private and gated repositories are an explicit deployment mode, not a property
an installed token silently enables (`AD-21`). Set:

```toml
[hub]
token_mode = "required"
credential_name = "hf-token"
expected_account = "the-service-account"
```

Install the encrypted systemd credential using
`packaging/systemd/hfcache-sync.service.d/credential.conf.example`, then run the
example's transient-unit `doctor --read-only` acceptance command. Require the
`credential` row to name `systemd-credential`, the `hub_identity` row to name the
configured account, and exit `0`. Run `plan` for each newly configured restricted
repository before syncing, exactly as for a public repository.

`token_mode = "optional"` remains public-only even when it finds that same
credential; a private/gated repository is `HFHUB006`. `required` with no resolved
credential is `HFARG008` before any Hub request. If upstream later revokes access,
the next Hub operation fails but every retained publication remains readable.
When continued retention is no longer authorized, remove the repository from
configuration, review `purge --dry-run`, and only then use `purge --apply` — never
delete archive paths manually (`AD-06`, `AD-20`, `FS-19`).

The timer runs this daily at 02:00 with up to 30 minutes of randomized delay.
To run it by hand, prefer the unit over the CLI, because the unit is what
production uses — same sandbox, same environment, same identity:

```bash
sudo systemctl start hfcache-sync.service
systemctl show hfcache-sync.service --property=Result --property=ExecMainStatus
```

```text
Result=success
ExecMainStatus=0
```

### Reading the run in the journal

Every run leaves a structured trail (plan §24). One line per thing that became
durable — never per chunk, so the volume is a function of how many repositories
were touched, not how many bytes moved.

```text
$ sudo journalctl -u hfcache-sync.service --since '-2 min' -o cat
Starting hfcache-sync.service - Synchronize configured Hugging Face repositories...
event=run.started level=info run_id=cccb23522c9a4d4d9520f9cc782670a6 archive_id=00000000-… command=sync config_fingerprint=266d272b… invocation=systemd repositories=2
event=repository.resolved level=info run_id=cccb23522c9a4d4d9520f9cc782670a6 commit_sha=71034c5d8bde858ff824298bdedc65515b97d2b9 repository=model:hf-internal-testing/tiny-random-gpt2 requested_revision=main
event=repository.skipped level=info run_id=cccb23522c9a4d4d9520f9cc782670a6 commit_sha=71034c5d8bde858ff824298bdedc65515b97d2b9 repository=model:hf-internal-testing/tiny-random-gpt2 status=skipped
event=run.completed level=info run_id=cccb23522c9a4d4d9520f9cc782670a6 command=sync downloaded_bytes=0 exit_code=0 hashed_bytes=0 outcome=success report=runs/20260727T104452Z-cccb23522c9a4d4d9520f9cc782670a6.json repositories=2 reused_bytes=0
Finished hfcache-sync.service - Synchronize configured Hugging Face repositories.
```

Useful selections:

```bash
sudo journalctl -u hfcache-sync.service -p err            # failures only
sudo journalctl -u hfcache-sync.service --since today
sudo journalctl _SYSTEMD_INVOCATION_ID=<id>               # exactly one run
sudo journalctl -u hfcache-sync.service | grep event=publication.completed
```

`-p err` works because each line carries a syslog priority prefix under systemd
which journald turns into `PRIORITY`. The event names are a **closed
vocabulary** — `hfcache.logging.EVENTS` is all of them — so a filter written
today keeps matching.

For a queue-ahead sync, read the latest event per repository:
`repository.queued` is admitted but waiting, `download.started` is the only
state expected to use Hub bandwidth, `download.completed` means the canonical
cache is ready, and `hash.started` means low WAN traffic is normal because the
foreground is reading local/NFS bytes. `hash.completed` is followed by staging
and `publication.completed`; no byte percentage is implied between checkpoints.

Storage is persistent and bounded at 1 GiB or one year, whichever binds first.
Before that was configured the journal was volatile and every scheduled run was
lost at reboot.

### Reading the durable run report

The journal says what happened; `runs/<UTC>-<run-id>.json` says what the run
*did*, and it is the authority. The `run_id` joins them.

```bash
sudo -u hfcache bash -c 'python3 -m json.tool "$(ls -t /srv/hfcache/runs/*.json | head -1)"'
```

```json
{
  "command": "sync",
  "exit_code": 0,
  "invocation_mode": "systemd",
  "outcome": "success",
  "repositories": [
    {
      "downloaded_bytes": 0,
      "hashed_bytes": 0,
      "publication_generation": 7,
      "repository_id": "hf-internal-testing/fixtures_ade20k",
      "resolved_commit_sha": "850d349e5038f291284e7999fcacbedc0922534b",
      "reused_bytes": 0,
      "status": "skipped"
    }
  ],
  "run_id": "9e6a6461d7994e65b1e625543f88d3be",
  "totals": {
    "downloaded_bytes": 0, "hashed_bytes": 0, "pruned_logical_bytes": 0,
    "published_bytes": 0, "reused_bytes": 0, "xet_cache_peak_bytes": 0
  }
}
```

Per-repository `status` is one of `skipped`, `ref_moved_to_retained_revision`,
`published`, `completed_with_warnings`, `failed`, or `disabled`. A `disabled`
repository is reported rather than omitted, so an operator can see the run knew
about it.

**A run report only exists if the run got far enough to write one.** A run that
died in preflight, on a lock timeout, or mid-download has no report — the journal
is the only record, which is why it is persistent.

---

## 5. Verification

Three modes, and they answer different questions.

```text
$ hfcache verify --estimate
estimated duration   0s
repositories         2
revisions            6
storage maintenance  undetectable
unique bytes         12.3 MiB
unique objects       23
exit=0
```

Run `--estimate` before scheduling a full verification on a real archive; it is
what you size the maintenance window from. `storage maintenance: undetectable`
means the writer cannot see the NAS scrub schedule from here — coordinating that
is an operator judgement, not something the tool can check.

```text
$ hfcache verify --full
event=verification.completed level=info run_id=e49eb54994db49fbb87e25f6bcc41fe7 bytes_read=12890456 command="verify --full" exit_code=0 findings=0 objects_read=23 outcome=clean report=runs/20260727T105133Z-…json repositories=2 revisions=6
bytes read    12.3 MiB
findings      0
objects read  23
outcome       clean
report        runs/20260727T105133Z-e49eb54994db49fbb87e25f6bcc41fe7.json
repositories  2
revisions     6
exit=0
```

23 unique objects across 6 revisions — shared hardlinked content is read **once**,
which is why `objects read` is smaller than the sum of the revisions' file counts.

One revision at a time, which is the mode to use after a targeted suspicion:

```text
$ hfcache verify --revision model:hf-internal-testing/tiny-random-gpt2@71034c5d8bde858ff824298bdedc65515b97d2b9
bytes read    11.9 MiB
findings      0
objects read  10
outcome       clean
report        runs/20260727T105135Z-c174d3c355e64aa4acff1afc49248971.json
repositories  1
revisions     1
exit=0
```

`--revision` needs the full 40-character SHA; an abbreviated one is refused,
because a repository has more than one retained revision and a prefix is a guess.

Verification never repairs. A mismatch is reported and the manifest is left
exactly as it was — an expected digest is never rewritten to match what was
found, which is the whole point of having one. Repair is a separate, explicit
command; that is `OPS-003`.

**Run `verify --full` after** a ZFS checksum or scrub error, a restore from
snapshot or replica, a migration, an unexpected shutdown during publication, any
manual modification of the archive, a repair, or a change to publication mode.

The quarterly timer is installed and **disabled** pending calendar confirmation
against the NAS maintenance schedule; see §9.

---

## 6. Retention and recovery

```text
$ hfcache prune --dry-run
retention  nothing to prune
exit=0
```

Retention is applied automatically by a **successful publication** beyond
`storage.maximum_revisions` (`AD-04`): at the default of three, a fourth unique
revision rotates the oldest non-current one out. `prune --apply` also finishes
a rotation that a previous run left incomplete or applies a reduced limit.

To adopt three revisions from an existing explicit five-revision policy, edit
`storage.maximum_revisions = 3` through the validated configuration pipeline
(`docs/cockpit.md` §6). The key is `maximum_revisions`, not `max_revisions`. Changing it alone
does not delete anything. Review `prune --dry-run` with explicit repository
selectors and run `prune --apply` with the same selectors. Each invocation
removes at most one eligible revision per repository, ordered by immutable
publication generation; review and repeat until the dry run has no plans.
`list` then confirms the retained revisions. The current revision is always
protected. Select only the repositories whose history should be reduced;
disabled configured repositories can still be selected, while unmanaged ones
cannot.
Manifest audit evidence survives deletion; filesystem or ZFS snapshots may
continue to hold physical blocks after the application removes its copies.

Neither `--dry-run` nor `--apply` is a default; omitting both is an error, because
one describes and the other performs.

### Removing repositories no longer configured

Removing a repository from configuration does not delete it; `HFWRN007` is the
deliberate reminder that its published revisions are still retained. Permanent
removal is a separate two-step operation:

```text
$ hfcache purge --dry-run --all-unmanaged
model:organization/old-model  purge 2 revisions, 486.1 MiB logical
exit=0

$ hfcache purge --apply --all-unmanaged
model:organization/old-model  purge 2 revisions, 486.1 MiB logical
exit=0
```

Prefer explicit selectors when the list is small:

```text
$ hfcache purge --dry-run model:organization/old-model
$ hfcache purge --apply model:organization/old-model
```

Review the dry-run's exact repository IDs, revision count, and logical-byte
estimate before apply. The command refuses a target still in configuration
(`HFARG007`) and refuses unknown content rather than deleting it (`HFRET001`). It
runs one durable transaction per repository, so an error after earlier entries
committed leaves those earlier purges complete and the later repository
untouched. Manifests and purge-reason records remain under `audit/pruned/`; the
publication trees and supported Hub cache revisions do not. ZFS snapshots may
continue to hold the physical blocks even after the logical-byte total is gone.

After apply, run `recover --dry-run`. It should report no actionable purge. If
the command was interrupted, `docs/recovery.md` §5 explains why recovery either
restores the entire repository before the commit point or completes audit and
trash cleanup after it.

```text
$ hfcache recover --dry-run
actionable  0
applied     -
blocked     0
exit=0
```

`recover --dry-run` mutates nothing and is always safe, including on an archive
that has stopped accepting writes. Read the two numbers:

- **`actionable`** — unfinished transactions with exactly one correct resolution.
  `recover --apply` will finish them, and is idempotent.
- **`blocked`** — states with no unambiguous resolution. `recover --apply` will
  *not* touch these and neither should you until you understand them. Each
  carries a code: `HFTXN001` (unknown journal version), `HFTXN002` (impossible
  checkpoint combination), `HFTXN003` (journal contradicts the filesystem),
  `HFTXN004` (two equally valid resolutions).

A blocked journal stops every mutating command at exit `20` before the Hub is
contacted. `status`, `list`, `verify`, and `recover --dry-run` keep working, so
there is always a way to inspect an archive that has stopped.

Recovery prefers over-retention to deletion and never guesses: it will not
replace an expected digest, pick a current revision by modification time, or
remove data it cannot explain.

---

## 7. Exit codes, and what to do about each

Plan §11.2. `1` and `2` are deliberately unused — Typer reserves them for
malformed command lines, so a scheduler can tell a bad invocation from an
application outcome.

| Code | Meaning | What to do |
| --- | --- | --- |
| `0` | Success, including non-fatal dependency warnings | Nothing. Check `status.findings` if warnings were reported |
| `10` | Invalid configuration or invocation | Fix the command or the file. Nothing was touched |
| `20` | Mount, sentinel, permission, capacity, or lock safety | **Stop.** Nothing was downloaded or changed. §7.1 |
| `30` | One or more repository sync failures | Other repositories may have succeeded. Read the run report |
| `40` | Integrity verification failure | **Do not sync or prune.** Preserve evidence; go to `OPS-003` |
| `50` | Prune, purge, or repair failure | The archive prefers preservation; `recover --dry-run` |

Observed on this deployment:

```text
$ hfcache --config /etc/hfcache/absent.toml status
HFCFG001 [/etc/hfcache/absent.toml]: configuration file /etc/hfcache/absent.toml does not exist
exit=10

$ hfcache sync model:organization/not-configured
HFARG004 [model:organization/not-configured]: selector model:organization/not-configured names a repository that is not in configuration
exit=10

$ hfcache verify --revision model:hf-internal-testing/tiny-random-gpt2
HFARG001 [--revision]: --revision 'model:…/tiny-random-gpt2' names no revision; it takes TYPE:ID@SHA with the full 40-character commit SHA, because a repository has more than one retained revision
exit=10

$ hfcache prune
HFARG002: exactly one of --dry-run and --apply is required: one describes what would happen and the other performs it, and neither is a safe default
exit=10
```

`40` and `50` are deliberately **not** provoked against the live archive — both
require published content to be damaged, and the application is not permitted to
rewrite `/srv/hfcache` outside its own transactional contracts. They are covered
by the test suites instead: the live-Hub suite flips a byte in a freshly
published revision on a throwaway archive and asserts `40` with the manifest and
the reference unchanged, and the retention and repair suites assert `50`.

### 7.1 Exit 20 in practice

The common cause is benign — another mutating command is already running. Exactly
one runs at a time (`AD-17`), and sync, verify, prune, purge, repair, and
`recover --apply` all share the one lock.

```text
$ hfcache sync            # while another process holds the lock
HFMNT010 [/run/hfcache/hfcache.lock]: sync could not acquire the exclusive lock /run/hfcache/hfcache.lock within 1s; the holder left no record. Exactly one mutating command runs at a time (`AD-17`)
exit=20
```

A scheduled sync waits an hour for the lock and a verification waits 24, so a
long sync finishes rather than racing. If nothing should be running:

```bash
sudo fuser -v /run/hfcache/hfcache.lock     # who holds it
systemctl is-active hfcache-sync.service hfcache-verify.service
```

The lock is `flock(2)`, so the kernel releases it when the holder dies. A crashed
run never leaves a lock to clear by hand.

The other causes of `20` are the §19 storage requirements, and every one of them
is reported by name:

```bash
$H doctor
```

`doctor` runs the same check set the mutating preflight runs, so its report and
the gate cannot describe different things. A failed run also logs
`event=preflight.failed` with the codes, which is the one durable trace of a
refusal that wrote no run report.

---

## 8. Warning codes

Warnings never change a `0` exit on their own. They appear in `status.findings`,
in the run report, and in the journal.

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

`HFWRN004` deserves care: it is the signal that a run really did stop half way.
It used to fire after every successful publication because a committed
transaction left its staging directory behind (decision 56). That is fixed, so if
you see it now, believe it.

---

## 9. Timers

```text
$ systemctl list-timers 'hfcache*' --all
NEXT                        LEFT LAST                              PASSED UNIT               ACTIVATES
Tue 2026-07-28 02:03:06 EDT  19h Mon 2026-07-27 02:19:23 EDT 4h 33min ago hfcache-sync.timer hfcache-sync.service

1 timers listed.

$ systemctl is-enabled hfcache.target hfcache-sync.timer hfcache-verify.timer
enabled
enabled
disabled
```

Only one timer is listed because the quarterly verification timer is installed
and **disabled**, pending confirmation that its calendar does not overlap the NAS
scrub, SMART, or replication windows. Check the calendar before enabling it:

```text
$ systemd-analyze calendar 'Wed *-01,04,07,10-01..07 04:00:00'
Normalized form: Wed *-01,04,07,10-01..07 04:00:00
    Next elapse: Wed 2026-10-07 04:00:00 EDT
       (in UTC): Wed 2026-10-07 08:00:00 UTC
       From now: 2 months 11 days left
```

Then:

```bash
sudo systemctl enable --now hfcache-verify.timer
```

Both timers are `Persistent=true`, so a missed calendar event runs after the host
comes back rather than being skipped.

### When a run outlasts the schedule

A first sync of a large repository legitimately takes hours, and the service is
deliberately never killed for being long (`TimeoutStartSec=infinity`; the
unit's own comment says why). Three things bound and shape a long run instead:

- **It cannot overlap itself.** The service is `Type=oneshot`; if the next
  02:00 elapses while a run is still executing, systemd merges the new start
  job into the running one. No second instance starts, nothing queues, and
  that day's trigger is consumed — the day is skipped. `Persistent=true`
  replays an elapse missed while the *host* was down, not one consumed while
  the unit was busy.
- **A skipped day is the designed semantics, not a fault.** The archive holds
  what each run observes (`AD-02`/`AD-03`): commits between observations are
  legitimately skipped, and retention depth is measured in observations — tune
  the timer to tune depth. Nothing fetched is lost to the overrun either:
  downloads resume from the cache's partials (`AD-09`), each repository is its
  own transaction, so everything published before an interruption stays
  published, and the next run reuses every byte already on disk.
- **The lock is the second wall** (`AD-17`), for what systemd cannot
  serialize: manual runs and the other mutating commands. A scheduled sync
  waits `sync.lock_wait_seconds` — one hour by default — then gives up with
  `HFMNT010` at exit `20`, before contacting the Hub; verification waits 24
  hours, so a legitimately long sync delays it rather than losing to it
  (`docs/configuration.md` §5).

A sync that gives up on the lock leaves **no run report** — the journal is the
only record, which is precisely the case the failure hook below exists for.
The next day's timer simply tries again. If runs chronically outlast the day,
the symptom is fewer observations per repository, never a damaged archive;
size a repository with `hfcache plan` before adding it, and add large
repositories in stages.

To pause the schedule without disturbing the mount:

```bash
sudo systemctl stop hfcache-sync.timer
```

> **Do not `systemctl stop hfcache.target` to pause things.**
> `srv-hfcache.mount` is `PartOf=hfcache.target`, so stopping the target
> **unmounts `/srv/hfcache`**. The automount re-triggers on next access so this
> is recoverable, but it will disconnect anything working in that directory.
> Stopping the timers is what "pause the schedule" means.

Nothing notices a failed run on its own. `packaging/systemd/hfcache-failure@.service.example`
is the seam for that — see the deployment runbook §9. Until it is activated,
`status` and the journal are the only things that will tell you.

---

## 10. Measured performance and capacity (plan §27)

Measured 2026-07-27 (`OPS-006`) on `hfcachewriter.lab.example.com` against
`nas.lab.example.com:/mnt/tank/huggingface-archive` over NFSv4.2, `nconnect=4`,
1 MiB rsize/wsize. Work ran in `/srv/hfcache/.store/health/`, the archive's own
probe area, and was removed afterwards.

**Re-measure after** a NAS or network change, a `huggingface_hub`/`hf_xet`
upgrade, or before activating a repository substantially larger than the current
set. These are one host's numbers on an idle archive, not a specification.

| Quantity | Measured | Method |
| --- | --- | --- |
| Writer → NFS sequential write | **114 MB/s** | `dd bs=1M count=1024 conv=fsync` |
| NFS sequential read, uncached | **94 MB/s** | `dd bs=1M iflag=direct` |
| NFS sequential read, cached | **117 MB/s** | `dd bs=1M`, warm page cache |
| SHA-256 throughput | **1 660 MB/s** | `hashing.sha256_file` over 1 GiB |
| Hub → writer download | **14.3 MB/s** | `snapshot_download`, 12.5 MiB, 10 files, anonymous |
| Hardlink publication rate | **91 links/s** | 2 000 `os.link` calls on the mount |
| Copy-mode fallback | **41 files/s** | 2.2× slower per file than hardlinking |
| Metadata (`stat`) | **95 000 /s** | warm; not a bottleneck |
| Local Xet cache peak | **252 KiB** | `/var/cache/hfcache/xet` after the test syncs |

### What these numbers mean in practice

**Publication is metadata-bound, not bandwidth-bound.** 91 hardlinks per second
is the number to plan with: a 10-file model publishes in a tenth of a second, and
a 10 000-file dataset spends about **two minutes** in publication alone, having
already downloaded and hashed. If a large dataset repository is ever activated,
this — not throughput — is what determines the sync window.

**Hashing is free relative to the mount.** SHA-256 runs at 1 660 MB/s against a
mount that reads at 94 MB/s uncached, and hashing local disk measured the same
1 672 MB/s, so it is CPU-bound and roughly eighteen times faster than the storage
feeding it. Ingestion verification costs nothing worth optimising; a full
verification's cost is the **read**, which is why `verify --estimate` reports
unique bytes rather than a file count.

**A full verification of this archive reads at storage speed.** Take 94 MB/s as
the planning figure for `verify --full`: roughly 5.6 GiB per minute, 340 GiB per
hour. That is the number to schedule the quarterly job against, and the reason
plan §16.2 says not to overlap it with a scrub.

**Copy mode costs about 2.2× per file** at small file sizes, on top of consuming
real space instead of sharing inodes. Hardlink mode is confirmed working here
(`doctor`), so this is a fallback figure only.

### Deferred, with their method recorded

Two of §27's quantities are **not** measured, and cannot honestly be until the
archive holds production content:

- **Space retained by five application revisions.** Needs the production
  repository list (Operator decision 1). Method: publish five revisions, then
  `du -sb --count-links` against `du -sb` on `published/` — the first counts every
  hardlink, the second counts unique inodes, and the ratio is what retention
  actually costs. On the current two test repositories the ratio is **1.01×**,
  which measures nothing useful: their revisions share almost no files, and the
  sample is 12.5 MiB.
- **Space retained by ZFS snapshots after application pruning.** Needs `NAS-006`
  (handoff item 3); there is no snapshot schedule on this dataset yet. Method:
  record `zfs list -o used,usedbysnapshots,usedbydataset` before a prune and
  after, and note that logical release and physical release differ — plan §15.3,
  and `unique_bytes_released_estimate` in a prune plan is explicitly the logical
  figure.

Until both exist, the dataset quota (handoff item 4) should be set from
`hfcache plan`'s dry-run sizes for the production list rather than extrapolated
from anything above.

---

## 11. Quick reference

```bash
H="sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache --config /etc/hfcache/config.toml"

$H status                     # is anything wrong
$H --json status              # the form to investigate with
$H list                       # what is archived
$H plan                       # what a sync would do, and its size
$H doctor                     # prove the deployment can still do its job
$H verify --estimate          # size the maintenance window
$H verify --full              # the quarterly integrity read
$H recover --dry-run          # always safe, including on a stopped archive
$H prune --dry-run            # what retention would rotate out
$H purge --dry-run --all-unmanaged  # what explicit repository removal would delete

sudo systemctl start hfcache-sync.service              # run a sync as production does
sudo systemctl stop  hfcache-sync.timer                # pause the schedule
sudo journalctl -u hfcache-sync.service -p err         # failures only
sudo journalctl _SYSTEMD_INVOCATION_ID=<id>            # exactly one run
```

Not covered here: corruption and repair (`OPS-003`), snapshot and replica restore
(`OPS-004`), and the consumer-side copy, which happens on a different host.

The Cockpit plugin (`docs/cockpit.md`) is a browser front-end for exactly this
runbook — the same commands, the same units, and this document's guidance
carried inline. Nothing it can do is anything this runbook does not describe.
