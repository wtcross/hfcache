# Deploying hfcache on CentOS Stream 10

| Field | Value |
| --- | --- |
| Status | Runbook, exercised on `hfcachewriter.lab.example.com` |
| Work package | `OPS-001` |
| Derived from | `docs/plan.md` §21, §22, §29, §30, §35 |
| Companion | `docs/operations.md` for running it once it is up |

Takes a bare CentOS Stream 10 VM to a running `hfcache.target`. Every command
here was run on the writer; every block marked **observed** is real output, not
an illustration. Where a step cannot be re-run — there is exactly one of those,
`archive init` — this document says so and gives the evidence from when it was.

**What this does not cover.** Everything on the TrueNAS side: the dataset, the
service identities, the writer export, the consumer export, snapshots and
replication. Those are plan §20 and the operator handoff in
`docs/progress.md`. This document assumes the writer export already exists and
that the archive dataset is reachable, because until it is there is nothing for
the writer to mount.

---

## 0. What you need before starting

| Input | Example value | Where it comes from |
| --- | --- | --- |
| Storage host | `nas.lab.example.com` (`192.0.2.4`) | plan §34 |
| Export path | `/mnt/tank/huggingface-archive` | plan §34 |
| Writer static IP | `192.0.2.90`, in the export's allow list | plan §34 |
| Archive UUID | `00000000-0000-0000-0000-000000000000` | provisioned once; see §8 |
| Repository list | two small public test repositories | `docs/progress.md` |

The values above — and every concrete hostname, address, and UUID in this
repository — are placeholders of the right shape: hostnames under
`lab.example.com` (RFC 2606), addresses in the `192.0.2.0/24` documentation
range (RFC 5737), an all-zeros archive UUID. Substitute your deployment's own
values as you go; the real ones belong in the deployment itself —
`/etc/hfcache/config.toml`, the sentinel, the NAS configuration — never in
this repository.

The archive UUID is the one value you must decide **before** initializing and can
never change afterwards: it goes into `storage.archive_id` and into the sentinel,
and a disagreement between them is fatal and deliberately unrepairable
(`FS-03`). Generate it with `uuidgen` and record it somewhere outside the VM.

---

## 1. Base operating system

SELinux stays enforcing throughout (plan §23). Nothing in this runbook needs it
weakened, and if a step appears to require that, the step is wrong.

```bash
sudo dnf install -y git nfs-utils chrony
sudo systemctl enable --now chronyd
```

Give the host a static address and working forward and reverse DNS before going
further; the NFS export is allowed by exact IP, so an address that moves silently
removes the writer's access.

**Observed:**

```text
$ cat /etc/redhat-release
CentOS Stream release 10 (Coughlan)
$ getenforce
Enforcing
$ rpm -q git nfs-utils chrony
git-2.52.0-1.el10.x86_64
nfs-utils-2.8.3-8.el10.x86_64
chrony-4.8-2.el10.x86_64
```

---

## 2. Service identity and local paths

A locked system account with no home, no shell, no password, and no sudo (plan
§21.2):

```bash
sudo useradd --system --no-create-home --home-dir /nonexistent \
  --shell /usr/sbin/nologin hfcache
```

```bash
sudo install -d -m 0755 -o root -g root /opt/hfcache /etc/hfcache
sudo install -d -m 0750 -o hfcache -g hfcache /var/cache/hfcache /var/lib/hfcache
sudo install -d -m 0755 -o root -g root /srv/hfcache
```

`/opt/hfcache` and `/etc/hfcache` are **root-owned**, so the account that runs the
archive cannot modify the code or the configuration that runs it. The bare
`/srv/hfcache` mount point is root-owned and not writable by `hfcache` for a
different reason: if the NFS mount is ever missing, a write must fail rather than
silently land on the VM's root filesystem.

**Observed** (after the mount is up, which is why `/srv/hfcache` reads
differently — see §5):

```text
$ getent passwd hfcache
hfcache:x:981:981::/nonexistent:/usr/sbin/nologin
$ stat -c '%a %U:%G %n' /opt/hfcache /etc/hfcache /var/cache/hfcache /var/lib/hfcache /srv/hfcache
755 root:root /opt/hfcache
755 root:root /etc/hfcache
750 hfcache:hfcache /var/cache/hfcache
750 hfcache:hfcache /var/lib/hfcache
750 UNKNOWN:UNKNOWN /srv/hfcache
```

`UNKNOWN:UNKNOWN` is correct and is not a fault. The writer export maps every
client identity to the NAS-side `hfcache-sync:hfcache-archive` (uid 3001, gid
3002 — this server's choice of values, `docs/storage-requirements.md` §2), and
those ids have no local passwd entry. This is exactly why preflight
proves writability with a real create/fsync/rename/delete probe instead of
comparing `st_uid` against the service uid (plan §35.3).

---

## 3. uv and the pinned interpreter

uv is pinned, and `scripts/install-release.sh` refuses to run against any other
version — a deployment tool that accepts whatever resolver happens to be present
is not a deployment tool.

```bash
curl -LsSf https://astral.sh/uv/0.11.32/install.sh | sh
```

The pinned version is the one in the script (`REQUIRED_UV_VERSION`), so a
newer checkout may pin newer — install that version's URL instead. To run
deliberately against a different uv, set `HFCACHE_UV_VERSION`; the script's
`--help` lists every override (`HFCACHE_PREFIX`, `HFCACHE_SOURCE`,
`HFCACHE_UV`).

**Observed:**

```text
$ uv --version
uv 0.11.32 (x86_64-unknown-linux-gnu)
```

You do **not** install Python separately. CentOS Stream 10 ships 3.12 and EPEL
reaches 3.13, so `install-release.sh` installs the pinned CPython into
`/opt/hfcache/python` as a uv-managed build and uses only that. This is not
cosmetic: a virtual environment whose `home` points under `/home` starts fine on
a workstation and fails as a service under `ProtectHome=true`, and it fails at
`SYS-002` rather than at install time.

---

## 4. Get the source

```bash
git clone https://github.com/wtcross/hfcache.git /home/<operator>/Projects/hfcache
```

The public repository is `github.com/wtcross/hfcache`, mirrored on the lab
Forgejo (`git.lab.example.com`). The working tree on the writer is the
source of releases: `install-release.sh` copies a fixed subset of it into each
release directory — `src`, `docs`, `packaging`, `scripts`, `examples`,
`pyproject.toml`, `uv.lock`, and the license — so the release tree is
self-contained and the units can point `Documentation=` at it.

---

## 5. The NFS mount

Plan §21.3 permits either explicit units or an `/etc/fstab` line that generates
them, and is explicit that you must not have both: a unit in
`/etc/systemd/system` shadows the generated one, so the fstab line an operator
edits first would have no effect at all. **This deployment uses the units**
(decision 58); the fstab line is commented out in place with a pointer, and the
original is preserved at `/etc/fstab.pre-hfcache-units`.

```bash
cd /home/<operator>/Projects/hfcache
sudo install -m 0644 -o root -g root \
  packaging/systemd/srv-hfcache.mount \
  packaging/systemd/srv-hfcache.automount \
  /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now srv-hfcache.automount
```

Network ordering belongs on the **mount**, never on the automount. An automount
unit carries an implicit `Before=local-fs.target`, so `After=network-online.target`
on it produces a genuine ordering cycle. Judge `systemd-analyze verify` by its
**output**, not its exit status — it exits `0` while reporting cycles.

**Observed:**

```text
$ findmnt -T /srv/hfcache
TARGET       SOURCE                                                FSTYPE OPTIONS
/srv/hfcache systemd-1                                             autofs rw,relatime,fd=51,...
/srv/hfcache nas.lab.example.com:/mnt/tank/huggingface-archive nfs4   rw,nosuid,nodev,noexec,
                                                                          relatime,vers=4.2,hard,
                                                                          proto=tcp,nconnect=4,...
```

**If your archive root is not `/srv/hfcache`:** the path is a convention
shared by more than the configuration. systemd derives a mount unit's name
from its `Where=`, so `srv-hfcache.mount` and `srv-hfcache.automount` must be
renamed to what `systemd-escape --path <your-path>` produces, with `Where=`
updated; both service units carry `RequiresMountsFor=` and `ReadWritePaths=`
for the same path; and `storage.archive_root` in the configuration must
agree. One path, five files.

---

## 6. Configuration

Copy `examples/config.toml`, set `storage.archive_id` to the UUID from §0, and
install it root-owned and group-readable by the service:

```bash
sudo install -m 0640 -o root -g hfcache examples/config.toml /etc/hfcache/config.toml
sudo -e /etc/hfcache/config.toml
```

`0640 root:hfcache` is the contract, and it is why `--config` and `--token-file`
pass `readable=False` to their option parsers: an unreadable configuration is an
application outcome reported as `HFCFG001` at exit `10`, not a usage error at
exit `2` (decision 57).

---

## 7. Install the release

```bash
sudo scripts/install-release.sh
```

This performs plan §21.4 rather than describing it: it verifies the uv pin,
installs the pinned interpreter, stages the release tree and renames it into
place, runs `uv sync --frozen --no-dev --no-editable --no-python-downloads`,
makes the whole tree root-owned and read-only to the service, runs the smoke
checks, relabels with `restorecon -RF`, and switches `current` atomically.

The environment is built in its **final** path, not staged and moved: a virtual
environment records absolute paths in `pyvenv.cfg` and in every console-script
shebang, so one built elsewhere and moved has an interpreter that does not exist.
What guards a half-finished build instead is `switch_to`, which refuses a release
with no `.venv/bin/hfcache`.

**Observed** (tail):

```text
==> ownership and modes

==> smoke checks
application       0.1.1
huggingface hub   1.24.0
python            3.14.6
transfer backend  xet 1.5.2

==> hfcache config validate
config fingerprint    266d272b64f9a0de049057816a52315bf09afda71f21932b382b5232a39f685e
enabled repositories  2
repositories          2
token source          none

==> restorecon

==> switch
current -> releases/0.1.1

release 0.1.1 is live at /opt/hfcache/current
retained releases:
  0.1.0
  0.1.1
```

---

## 8. Initialize the archive — once, ever

> **This is the one irreversible step.** `archive init` runs exactly once per
> archive. Re-running it against an initialized archive is refused, and it must
> never be attempted as a repair. On this deployment it was run on 2026-07-26 and
> the authorization for it is spent.

Inspect first — this mutates nothing:

```bash
sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache \
  --config /etc/hfcache/config.toml archive init \
  --archive-root /srv/hfcache --inspect
```

Then, only if `initializable` is true and `unknown entries` is `0`:

```bash
sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache \
  --config /etc/hfcache/config.toml archive init \
  --archive-root /srv/hfcache \
  --archive-id 00000000-0000-0000-0000-000000000000 --confirm
```

The root and the UUID are restated on the command line deliberately: this is the
one act that cannot be undone, so it does not take its target from a file alone.
`--archive-id` must agree with `storage.archive_id` or the command is `HFARG002`.

**Recorded when it was run** (`docs/progress.md`, live rollout checkpoints):
`--inspect` reported `initializable: true`, `adopted_published: true`, and no
unknown entries; the run created the fifteen remaining directories and
`.hfcache-root`, and adopted the pre-created empty `published/` per plan §6.2 —
TrueNAS needs that directory to exist before the consumer export can be defined,
which is why it is the single documented adoption exception.

---

## 9. Host integration: tmpfiles, journald, sysctl, and the failure hook

```bash
sudo install -m 0644 -o root -g root packaging/tmpfiles.d/hfcache.conf /etc/tmpfiles.d/hfcache.conf
sudo systemd-tmpfiles --create /etc/tmpfiles.d/hfcache.conf

sudo install -d -m 0755 /etc/systemd/journald.conf.d
sudo install -m 0644 -o root -g root \
  packaging/journald.conf.d/hfcache.conf /etc/systemd/journald.conf.d/hfcache.conf
sudo systemctl restart systemd-journald && sudo journalctl --flush
```

`/run/hfcache` holds the one exclusive lock. The units create it themselves via
`RuntimeDirectory=`, but `/run` is a tmpfs and the service account cannot create
a directory there, so the tmpfiles fragment exists for the other caller: an
operator running the CLI by hand.

The journald drop-in is **not optional** (plan §24). CentOS Stream 10 ships no
`journald.conf` at all, and the compiled default `Storage=auto` is persistent
only if `/var/log/journal` already exists — it does not. Without this, every line
a scheduled run logs is lost at the next reboot, and the runs that leave no
durable report at all (preflight refusal, lock timeout, a crash mid-download) are
exactly the ones that leave nothing else.

**Observed:**

```text
$ systemd-analyze cat-config systemd/journald.conf | grep -E '^(Storage|SystemMaxUse|MaxRetentionSec)'
Storage=persistent
SystemMaxUse=1G
MaxRetentionSec=1year
$ ls -d /var/log/journal
/var/log/journal
```

Install the dirty-page bounds:

```bash
sudo install -m 0644 -o root -g root packaging/sysctl.d/hfcache.conf /etc/sysctl.d/hfcache.conf
sudo sysctl -p /etc/sysctl.d/hfcache.conf
```

This fragment and the `MemoryHigh=` line in each service unit are one design
(decision 86): a terabyte-scale sync or a full verification streams every byte
through the page cache, and on a virtual machine an unbounded cache makes the
guest touch all of its RAM — memory the hypervisor has then committed whether or
not the guest ever needs it again. On an overcommitted host that is how a
healthy guest gets OOM-killed mid-transfer. `MemoryHigh=` keeps each run's
footprint near a fixed working set; the sysctl keeps the dirty share of that set
small enough that reclaim always has clean pages to take. The half that only the
hypervisor can do — returning reclaimed pages to the host (virtio-balloon free
page reporting) or not overcommitting this guest at all — is the host operator's,
and this deployment assumes one of the two is in place.

Optionally, wire the failure hook. It ships complete and uninstalled at
`packaging/systemd/hfcache-failure@.service.example`; activating it is installing
that file without the suffix and uncommenting one `OnFailure=` line in each
service unit. Do this if anything is going to watch for failures — nothing else
notices a failed run until somebody runs `hfcache status`.

---

## 10. Install the units

```bash
sudo install -m 0644 -o root -g root \
  packaging/systemd/hfcache.target \
  packaging/systemd/hfcache-sync.service \
  packaging/systemd/hfcache-sync.timer \
  packaging/systemd/hfcache-verify.service \
  packaging/systemd/hfcache-verify.timer \
  /etc/systemd/system/
sudo restorecon -F /etc/systemd/system/hfcache*
sudo systemctl daemon-reload
sudo systemd-analyze verify hfcache.target hfcache-sync.service hfcache-sync.timer \
  hfcache-verify.service hfcache-verify.timer srv-hfcache.mount srv-hfcache.automount
```

`systemd-analyze verify` must produce **no output**. It exits `0` while reporting
ordering cycles, so the exit status is not the gate.

Prove the hardening actually applies, rather than assuming the unit file means
what it says:

```bash
sudo /opt/hfcache/current/scripts/check-hardening.sh
sudo /opt/hfcache/current/scripts/check-hardening.sh hfcache-verify.service
```

Run it from the **installed release**, not from a source checkout: the probe runs
under the unit's own `ProtectHome=true`, so a copy under `/home` is unreadable to
it. All 23 checks must pass on both units. Re-run after any change to a unit's
hardening and after any `huggingface_hub`, `hf_xet`, or Python upgrade.

---

## 11. Prove the deployment before enabling anything

```bash
H="sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache --config /etc/hfcache/config.toml"
$H doctor
$H plan
$H sync
$H verify --full
$H status
```

`doctor` must be clean. It is the same check runner a mutating command's hard
gate uses, so the report an operator reads and the preflight a scheduled run
performs cannot describe different things.

**Observed:**

```text
$ hfcache doctor
pass     configuration            /etc/hfcache/config.toml is valid; fingerprint 266d272b64f9
pass     archive_root             /srv/hfcache exists and is a directory
pass     mount_point              /srv/hfcache is a mount point of nas.lab.example.com:/mnt/tank/huggingface-archive
pass     filesystem_type          nfs4 from nas.lab.example.com:/mnt/tank/huggingface-archive
pass     mount_writable           mounted read/write
pass     sentinel                 /srv/hfcache/.hfcache-root names archive 00000000-0000-0000-0000-000000000000
pass     directory_writability    create, fsync, rename, and delete succeeded under /srv/hfcache/.store/health
pass     staging_filesystem       staging and 6 publication destinations share one filesystem
pass     hardlink_capability      proven under /srv/hfcache/.store/health
pass     atomic_directory_rename  proven under /srv/hfcache/.store/health
pass     reference_replacement    proven under /srv/hfcache/.store/health
pass     free_space               36037.6 GiB free of 36037.6 GiB, reserve 3603.8 GiB
pass     credential               no token; Hub calls pass token=False
pass     hub_endpoint             https://huggingface.co is a well-formed https endpoint
pass     hub_dns                  huggingface.co resolves to 2600:9000:28bc:0:17:b174:6d00:93a1, ...
pass     hub_tls                  TLSv1.3, certificate valid until Sep 27 23:59:59 2026 GMT
skipped  hub_identity             hub.expected_account is not set, so there is no identity to verify against; an anonymous archive of public content is a normal deployment
exit=0
```

`hub_identity` skipping is normal for an anonymous archive of public content. The
three publication capabilities — hardlink, atomic directory rename, reference
replacement — are **proven on the real dataset**, which under the Mapall export
is the only way they can be proven at all.

---

## 12. Enable the schedule

```bash
sudo systemctl enable --now hfcache.target
sudo systemctl enable --now hfcache-sync.timer
```

Leave the verification timer installed and **disabled** until an operator has
confirmed the quarterly calendar does not overlap the NAS scrub, SMART, or
replication windows (plan §34):

```bash
sudo systemctl status hfcache-verify.timer   # installed, disabled, inactive
```

That state is expressible only because the timers attach through their own
`[Install] WantedBy=hfcache.target` rather than a `Wants=` in the target — a
`Wants=` starts a unit whether or not it is enabled, which would have started the
one that must stay off.

**Observed:**

```text
$ systemctl list-unit-files 'hfcache*' 'srv-hfcache*' --no-legend
hfcache-sync.service       static
hfcache-sync.timer         enabled
hfcache.target             enabled
hfcache-verify.service     static
hfcache-verify.timer       disabled
srv-hfcache.automount      enabled
srv-hfcache.mount          static
```

---

## 13. Upgrade (plan §30)

> **Read this before step 1.** Plan §30 says "stop `hfcache.target`". On this
> deployment `srv-hfcache.mount` is `PartOf=hfcache.target`, so stopping the
> target **unmounts `/srv/hfcache`**. That is harmless between releases — the
> automount re-triggers on the next access — but it is surprising, and it will
> disconnect anything working in that directory, including the shell you are
> typing in. Stopping the two timers achieves what step 1 is actually for, which
> is that no job is running when `current` moves.

```bash
# 1-2. quiesce, and prove nothing is running
sudo systemctl stop hfcache-sync.timer
# Stopping the timer does not stop an active service. Wait for it, or stop it
# deliberately; never move `current` while either service or the lock is active.
sudo systemctl stop hfcache-sync.service       # only when interruption is intended
systemctl is-active hfcache-sync.timer hfcache-verify.timer \
                    hfcache-sync.service hfcache-verify.service
sudo fuser -v /run/hfcache/hfcache.lock      # no holder = no active run

# 3. install the new version beside the old one, without switching
sudo scripts/install-release.sh --no-switch

# 5. validate on the new tree before it is live
sudo -u hfcache /opt/hfcache/releases/<new>/.venv/bin/hfcache \
  --config /etc/hfcache/config.toml config validate

# 6. switch
sudo scripts/install-release.sh --switch <new>

# 7. reload if any unit changed
sudo systemctl daemon-reload

# 8-9. a no-change sync, then restart the timer
sudo systemctl start hfcache-sync.service
sudo systemctl start hfcache-sync.timer
```

**Observed, quiescing:**

```text
$ sudo systemctl stop hfcache-sync.timer
$ systemctl is-active hfcache-sync.timer hfcache-verify.timer hfcache-sync.service hfcache-verify.service
inactive
inactive
inactive
inactive
$ sudo fuser -v /run/hfcache/hfcache.lock
(no process holds the lock)
$ scripts/install-release.sh --list
prefix:  /opt/hfcache
current: releases/0.1.0
releases:
  0.1.0
```

**Observed, staging without switching.** `--no-switch` leaves `current` where it
is, so the new release can be validated before anything depends on it:

```text
==> staged
release 0.1.0 is installed; `current` is unchanged
```

Rebuilding the version that is *currently live* is supported but warns, because
`current` is a symlink to the release **name** and therefore dangles while the
tree is replaced. This is the case §30 step 1 exists for:

```text
note: current points at 0.1.0 and is being rebuilt in place;
      hfcache.target should be stopped (plan §30 upgrade step 1)
```

**Observed, switching and running:**

```text
$ sudo scripts/install-release.sh --switch 0.1.1
current -> releases/0.1.1
$ sudo systemctl start hfcache-sync.service
$ systemctl show hfcache-sync.service --property=Result --property=ExecMainStatus
Result=success
ExecMainStatus=0
```

And the run in the journal, which is what the §24 event log is for:

```text
$ sudo journalctl -u hfcache-sync.service --since '-2 min' -o cat
Starting hfcache-sync.service - Synchronize configured Hugging Face repositories...
event=run.started level=info run_id=cccb23522c9a4d4d9520f9cc782670a6 archive_id=00000000-0000-0000-0000-000000000000 command=sync config_fingerprint=266d272b… invocation=systemd repositories=2
event=repository.resolved level=info run_id=cccb23522c9a4d4d9520f9cc782670a6 commit_sha=71034c5d8bde858ff824298bdedc65515b97d2b9 repository=model:hf-internal-testing/tiny-random-gpt2 requested_revision=main
event=repository.skipped level=info run_id=cccb23522c9a4d4d9520f9cc782670a6 commit_sha=71034c5d8bde858ff824298bdedc65515b97d2b9 repository=model:hf-internal-testing/tiny-random-gpt2 status=skipped
event=run.completed level=info run_id=cccb23522c9a4d4d9520f9cc782670a6 command=sync downloaded_bytes=0 exit_code=0 hashed_bytes=0 outcome=success report=runs/20260727T104452Z-cccb23522c9a4d4d9520f9cc782670a6.json repositories=2 reused_bytes=0
Finished hfcache-sync.service - Synchronize configured Hugging Face repositories.
```

---

## 14. Rollback (plan §30)

Rollback is the **same tool** as install, with `--switch`. A rollback that used a
different procedure than the install would be a procedure nobody has tested.

```bash
sudo systemctl stop hfcache-sync.timer
systemctl is-active hfcache-sync.timer hfcache-verify.timer \
                    hfcache-sync.service hfcache-verify.service
sudo fuser -v /run/hfcache/hfcache.lock          # wait or stop before continuing
sudo scripts/install-release.sh --list          # what is installed, and what is live
sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache --config /etc/hfcache/config.toml recover --dry-run
sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache --config /etc/hfcache/config.toml status
sudo scripts/install-release.sh --switch <previous>
sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache --config /etc/hfcache/config.toml recover --dry-run
sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache --config /etc/hfcache/config.toml status
sudo systemctl start hfcache-sync.timer
```

**Do not roll back archive data.** Only the application moves. Durable formats
are versioned and a newer version is refused rather than read speculatively,
which is what makes going back safe.

**Restricted-scope configuration is an application compatibility boundary, not
an archive-format boundary.** Releases before `HUB-010` reject
`hub.token_mode = "required"` as `HFCFG015`. Before rolling back across that
package, stop the sync timer and use the newer binary to install and validate a
configuration with `token_mode = "optional"`; do not run a sync on the older
release while private/gated repositories remain enabled. Existing restricted
publications and all durable JSON remain readable because their formats did not
change. Roll forward before restoring `required`. Never delete or rewrite archive
data to make a rollback accept configuration.

**Observed** — a real rollback from 0.1.1 to 0.1.0 and back:

```text
$ sudo scripts/install-release.sh --switch 0.1.0
current -> releases/0.1.0
$ sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache version
application       0.1.0
huggingface hub   1.24.0
python            3.14.6
transfer backend  xet 1.5.2
$ sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache --config /etc/hfcache/config.toml recover --dry-run
actionable  0
applied     -
blocked     0
exit=0
$ sudo scripts/install-release.sh --switch 0.1.1
current -> releases/0.1.1
```

The step that matters there is the third: the previous release read an archive
the newer one had written, and found nothing to reconcile and nothing blocked.
That is the property rollback depends on, and it is worth re-checking whenever a
release touches a durable format.

**0.1.2 is the first release that did touch one**, so it was re-checked. `RET-008`
added checkpoint 10, `containers_removed`, to §7.4's prune sequence. Fed a prune
journal recording it, the two releases answer differently, and the difference is
the guarantee working:

```text
=== release 0.1.2 reading it ===
   accepted
=== release 0.1.1 reading it ===
   ['HFTXN002']
    prune journal … records checkpoints […], which is not a prefix of the
    documented sequence …; no valid execution produces this combination
```

So the operational rule for this rollback, and any later one across a checkpoint
change: **roll back with no prune in flight.** A *completed* prune journal is
closed and recovery never reads it, so the ordinary case is unaffected — which is
why the `recover --dry-run` above is clean. But if a prune is interrupted and you
then roll back, the older release will refuse the journal at exit `20` and wait
for an operator rather than guess. That is the correct answer and not a
regression; it is simply not a state you want to discover at 02:00. Check
`recover --dry-run` **before** switching, as the sequence above does.

**0.1.3 touched a durable format too** — `VER-009` made `commit_sha` nullable in
a verification finding and in `catalog/verification.json`'s
`outstanding_failures[]`, for a `current.json` that will not parse — so the same
cross-format check was performed, on a throwaway archive with its current
reference broken. Both releases read the same catalog, and the difference is
this rollback's operational rule:

```text
=== release 0.1.3 reading it ===
degraded: true   outstanding_failures: 1   last_full_verification: failed
=== release 0.1.2 reading it ===
degraded: false  outstanding_failures: 0   last_full_verification: null
```

0.1.2 does not refuse the catalog the way an older release refuses a journal:
the catalog is derived (`FS-16`), so a validation failure reads as `None` and
every revision reports `unverified` — confidence lowered, never raised. What is
lost is the **degraded signal itself**, silently, along with the last full
verification's summary. So: **roll back to 0.1.2 only with no null-SHA finding
outstanding.** A clean `verify --full` first is what clears the entry — observed
on the drill: after one, 0.1.2 read the same catalog fully, `verified` and not
degraded. `status` on the *new* release before switching is the check, exactly
where `recover --dry-run` sits in the sequence above.

**0.1.4 widens another schema-version-1 combination:** a failed sync report may
carry warnings observed before a later repository failed. The cross-format
drill wrote that shape with 0.1.4. Its reader accepted `outcome: "failed"`, exit
`50`, warning `HFWRN005`, and error `HFRET002`; 0.1.3 refused the same file as
`HFVER007` because it required warnings if and only if the outcome was
`success_with_warnings`. The refusal is safe, but one read path is deliberately
lenient: 0.1.3 `status` skipped the incompatible newest report and showed the
preceding compatible repository status, while 0.1.4 showed `failed`. A later
ordinary compatible 0.1.4 report superseded the mixed report and both releases
then read the later status without deleting or rewriting history.

So: **roll back to 0.1.3 only when the newest sync report has an older-valid
combination, or after a later compatible 0.1.4 sync report supersedes a mixed
failure.** Success, success-with-warnings, and failure-without-warnings are
older-valid; failure-with-warnings is not. Do not delete or rewrite the mixed
report to make rollback appear clean. Stay on 0.1.4 (or roll forward to it) to
inspect that report by run ID. This rule is in addition to the no-prune-in-flight
rule above; a rollback farther to 0.1.2 also retains the null-SHA rule.

**0.1.5 adds a complete-repository purge plan and a prune-record reason.** The
cross-format drill used the isolated loopback NFS archive from
`docs/recovery.md` §6 with its own UUID and the 12.5 MB public test model. The
0.1.5 writer synced generation 1, purged it completely, and left a committed
prune-family journal plus byte-for-byte manifest and
`operator_requested_repository_purge` record. The installed 0.1.4 commands
then both succeeded: `status` reported no repositories and no unfinished work;
`recover --dry-run` reported actionable `0`, blocked `0`. Re-adding the same
repository and running a real 0.1.4 sync also succeeded and preserved
publication generation 1 from the archived manifest. A second 0.1.5 purge left
the same successful 0.1.4 status/recovery result.

The one incompatible direct read is deliberate: 0.1.4's
`PrunedRevisionRecord` model rejects the new reason literal. Normal 0.1.4
commands do not parse that record after a completed purge, and the archived
manifest remains the generation authority. So: **roll back to 0.1.4 only with
no purge transaction in flight.** A completed purge is command-compatible,
including later re-addition; use 0.1.5 for direct tooling that parses its
`.prune.json` record, and never delete or rewrite the record to make an older
parser accept it. The 0.1.4 failed-plus-warning report rule above remains an
independent rollback condition.

**0.1.7 retention-policy rollback (RET-010, decision 102).** Older binaries
reject `storage.maximum_revisions = 3`. Stop the sync timer, finish any open
transaction with the newer binary, and atomically install a validated
configuration with an explicit `maximum_revisions = 5` before switching back.
An omitted value also means five to an older binary, but the explicit value
keeps the rollback policy reviewable. This changes the future retention limit;
it does not restore deleted revisions. Archive JSON formats and the historical
retention reason remain compatible. Required-token rollback rules above still
apply independently when going back before 0.1.6.

**0.1.8–0.1.9 quarantine-cleanup rollback (QUA-001/QUA-002, decisions 103–104).** Cleanup changes
no durable JSON shape and preserves its original terminal publication and
committed recovery journals. After the cleanup process releases the writer
lock, 0.1.7 can read the remaining archive using the same configuration; it
simply has no `quarantine` command. Removed redundant quarantine entries are
not restored by rollback. The retention-policy barrier above still applies
when going back before 0.1.7.

Keep at least the previous release installed (plan §21.4 item 7). `--list` is how
you see what you have:

```text
$ scripts/install-release.sh --list
prefix:  /opt/hfcache
current: releases/0.1.1
releases:
  0.1.0
  0.1.1
```

---

## 15. Acceptance checklist

| Check | Expected |
| --- | --- |
| `getenforce` | `Enforcing` |
| `findmnt -T /srv/hfcache` | `nfs4` from the NAS, `rw,nosuid,nodev,noexec,vers=4.2` |
| `systemd-analyze verify` on all units | **no output** |
| `check-hardening.sh` on both service units | 23 of 23 pass |
| `hfcache doctor` | exit `0`; `hub_identity` may be `skipped` only for public scope, and must name the expected account for `token_mode = "required"` |
| `hfcache status` | exit `0`, `degraded: false`, `unfinished_transactions: 0` |
| `systemctl list-unit-files 'hfcache*'` | target and sync timer `enabled`, verify timer `disabled` |
| `journalctl --disk-usage` | reports the `/var/log/journal` store |
| `ausearch -m avc -ts boot` | `<no matches>` |
| `install-release.sh --list` | at least two releases, `current` on the newer |

Two acceptance items cannot be checked from the writer and are operator work:
reboot persistence, and everything that needs a second host — the consumer
export, its read-only enforcement, and a downstream copy. Both are in the handoff
list in `docs/progress.md`.

## 16. The Cockpit plugin

Optional browser administration for this deployment; `docs/cockpit.md` is its
contract, and `docs/cockpit-plugin/` is the full installation and usage
guide — this section is the deployment-step summary. The plugin is static
files — nothing runs server-side beyond cockpit itself, and the application
is untouched (`CP-01`, `CP-14`).

Build-host requirements: the pnpm toolchain in the operator's `PNPM_HOME`
(decision 88) and `make`. Runtime requirements: `cockpit` with its socket
enabled — this deployment runs cockpit 364.

```bash
# production build, then install to /usr/share/cockpit/hfcache (root-owned)
make -C cockpit clean && make -C cockpit NODE_ENV=production
sudo make -C cockpit install

# development loop instead: per-user symlink, rebuild + browser refresh
make -C cockpit devel-install
cockpit-bridge --packages | grep hfcache
```

`install` copies whatever `dist/` holds: without `NODE_ENV=production` the
result is an unminified development bundle, and `clean` forces the rebuild
make would otherwise consider up to date.

Update is rebuild plus `sudo make -C cockpit install` again; removal is
`sudo rm -rf /usr/share/cockpit/hfcache`, plus `make -C cockpit
devel-uninstall` where the development symlink was used. The plugin's only
host state outside that directory is what its contract names: the managed
schedule drop-in `/etc/systemd/system/hfcache-sync.timer.d/50-cockpit.conf`
and the configuration pipeline's candidate and predecessor beside
`/etc/hfcache/config.toml` (`docs/cockpit.md` §6–§7).

Administrative Cockpit access is required for everything mutating: the
plugin escalates through the superuser bridge and drops to the service
identity for CLI work (`CP-03`); a session without that access gets
read-only state. SELinux stays enforcing; nothing here relaxes §22.5
(`CP-13`).
