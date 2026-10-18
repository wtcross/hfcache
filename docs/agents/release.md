# Releasing hfcache

The rule everything else hangs on (decisions 75 and 79): **a version is tagged
because it is deployed.** Deploying and tagging are one motion; nothing is
tagged that is not running, and nothing stays deployed that is not tagged.
`docs/deployment-centos-stream-10.md` §13–§14 is the operator authority this
checklist compresses.

## Preconditions

- Working tree clean; every package in the release committed and tracked in
  `docs/progress.md`.
- `scripts/check.sh --with-build` exits `0`.
- Opt-in suites as the changes warrant: `-m live` if the Hub adapter changed,
  `-m nfs` on the writer if storage changed.

## If a durable format changed

Decision 65 makes this unconditional: perform the **cross-format drill** on a
throwaway archive (`docs/recovery.md` §6 — its own UUID, never
`/srv/hfcache`). Write the new shape, read it with the *previous release's*
binary, and record what the old binary actually does. That observed behaviour
becomes the release's rollback rule in `docs/deployment-centos-stream-10.md`
§14 (0.1.3's null-SHA rule is the worked example). Bump `schema_version` per
`docs/schemas.md` §1.1, or record which widening precedent (decision 78) lets
the version stand.

## Cut

1. Bump `[project] version` in `pyproject.toml` — the single source;
   `hfcache.__version__` reads package metadata.
2. Add the `CHANGELOG.md` entry and refresh README `Status`.
3. Commit as a `REL-…` package; `scripts/check.sh --with-build` green.

## Deploy (deployment §13, compressed)

**API-014 amendment (2026-10-18, [decision 121](../adr/decision-121.md)).**
The historical command block below predates API-backed execution. Follow the
current [deployment quiescence procedure](../deployment-centos-stream-10.md#13-upgrade-plan-30):
pause timers, retain scheduled/operation handles, prevent API reactivation and
drain the actual API while private verifier status/result handoff stays available,
then stop/drain private activation/service. Switch/rebuild requires timers,
clients and actual API/worker sockets/services quiescent, including zero service
PIDs and no cgroup tasks, plus a noncreating orphan-lock check held through the
switch. Missing task accounting requires explicitly empty control-group evidence.
The installer refuses unknown quiescence and never auto-stops/kills.
Do not stop `hfcache.target`, unlink locks or treat client exit as termination.

Writer installation provisions locked `server` dependencies. Smoke parses actual
archive TOML through the installed strict loader without credentials/archive/
network, and exercises explicit CLI `config validate --local` against an owned
synthetic disabled-token policy. Required Hub credentials are not imported into
the installer; daemon-source validation remains operator/API preflight. Preserve
pending handles, both operation stores and previous release trees through rollback.
If `/var/lib/hfcache/scheduled` contains a pending handle, the installer refuses a
target whose actual installed Python lacks `hfcache.scheduled_client`; state links
also refuse. Trusted custom state layout uses `HFCACHE_CLIENT_STATE_DIRECTORY`.
The new [handle schema](../schemas.md#14-scheduled-client-observation-handle-api-014)
requires actual old/current binary compatibility drill in addition to archive
format drills. Real socket/cgroup/no-IP/no-credential/SELinux/NFS and executor-aware
hardening proof remain deployment prerequisites; repository fixtures do not pass
them. No deploy/tag/push is authorized by implementation of this task.

```bash
sudo systemctl stop hfcache-sync.timer          # quiesce — never hfcache.target
sudo scripts/install-release.sh --no-switch     # stage the new release
sudo -u hfcache /opt/hfcache/releases/<v>/.venv/bin/hfcache config validate
sudo scripts/install-release.sh --switch <v>    # atomic current-symlink switch
sudo systemctl daemon-reload
sudo systemctl start hfcache-sync.service       # one sync through the unit
sudo systemctl start hfcache-sync.timer
```

The unit run must end `Result=success`; an idempotent skip is success.

## Prove it

As the service identity, on the live archive: `verify --full` clean; `status`
exit `0` and not degraded; `recover --dry-run` actionable `0`, blocked `0`.
Then `sudo scripts/check-hardening.sh` on both service units (all checks
passing), `systemd-analyze verify` over the installed units (silent), and no
new SELinux AVC records. `REL-004`'s tracker entry shows a complete worked
run.

## Tag and publish

1. Annotated tag `v<version>`. The note is the complete release record:
   headline, what changed and why, any durable-format change with its
   rollback rule, state at release, and what deliberately remains. The
   `v0.1.2` and `v0.1.3` notes are the pattern.
2. `git push github main --follow-tags && git push forgejo main --follow-tags`.
3. Previous releases stay under `/opt/hfcache/releases` as rollback targets.

## Rollback

`docs/deployment-centos-stream-10.md` §14 is the authority — the same tool and
motion (`install-release.sh --switch <previous>`) plus the release-specific
constraints that section records (the prune-in-flight rule; 0.1.3's null-SHA
finding rule). A rollback that uses a different procedure than the install is
a procedure nobody has tested.
