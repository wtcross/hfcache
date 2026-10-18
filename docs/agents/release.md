# Releasing hfcache

The rule everything else hangs on (decisions 75 and 79): **a version is tagged
because it is deployed.** Deploying and tagging are one motion; nothing is
tagged that is not running, and nothing stays deployed that is not tagged.
`docs/deployment-centos-stream-10.md` §13–§14 is the operator authority this
checklist compresses.

The [API-017 rollout checklist](../deployment-centos-stream-10.md#17-rest-and-mcp-rollout-checklist-api-017)
is the current API/private-worker/state acceptance companion. Feature completion
keeps application metadata 0.1.10 unchanged; it does not cut or deploy a release,
create a tag or authorize any step below. Commit and wheel/sdist hashes identify
an artifact; equal displayed versions do not. Actual previous-feature/baseline
compatibility evidence must not be relabelled as a deployed previous release.

## Current data-preserving local release scope (OPS-014)

The new [local rollout plan](../plans/2026-10-18-plan-local-rootless-rollout.md)
authorizes reviewed local release/deployment/tagging while forbidding all NAS
content/metadata writes and changes to other hosts. [Decision 126](../adr/decision-126.md)
narrowly adapts acceptance: do not execute the historical supervised sync, live
full verification, archive-writing hardening workload or automatic sync-timer
resumption below. Their status remains NOT RUN, not passing. Actual local
container/proxy/credential/isolation checks and disposable local fixtures provide
explicit partial acceptance only. Preserve the read-only client mount, blocked
writers, retained state and actual executor drain/lock guards.

A local annotated tag must identify the actually deployed reviewed artifact and
state these remaining restrictions. No remote push, registry publication or ACME
issuance is authorized; the historical publishing steps below are excluded.
Version/profile/image selection and all actual outcomes remain their task's work,
not an authorization to bypass missing proof. All ordinary safety requirements
continue unless this stricter no-write scope forbids a specific acceptance step.

## Preconditions

- Working tree clean; every package in the release committed and tracked in
  `docs/progress.md`.
- For an evidence-only local closure, a separate clean detached worktree of the
  reviewed deployed tag target may establish this source precondition. Task/
  release evidence outside that worktree is gated and committed after the actual
  tag; it cannot change an application/image/profile or silently move the tag.
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

Writer installation provisions locked `server` dependencies. MCP-001 adds
an explicit installer `--with-mcp` selection for both server/MCP dependencies;
default staging remains server-only. The flag does not enable server config,
provision a credential, change services or relax quiescence/rollback guards.
See the [MCP contract](../mcp.md). Smoke parses actual
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

Rollback to a server-only/pre-MCP target requires deliberate disabled MCP config
before startup; older binaries can parse the existing slot but refuse enablement.
There is no migration or automatic transport fallback, and `--with-mcp` cannot
add packages to an existing switch target. Preserve normal executor drain and
state/lock guards. See [MCP rollback](../mcp.md#rollback-and-deployment-limits).

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


## Rootless artifact and drain requirements (OPS-015)

The selected [rootless profile](../adr/decision-127.md) uses explicit user systemd
units and a reviewed system bridge. Stage exact platform base/Caddy digests, built
wheel and hashed locked closure into an immutable runtime image; no runtime
resolution, auto-update, pull, replacement, init or persistent-role automatic
container removal. Only finite stateless observer clients may auto-remove their
own containers; accepted execution/state remains independently server-owned.
The separate protected rootless installer validates its immutable manifest/current
selector, read-only guards and actual container/libpod-cgroup drain; it does not
silently reinterpret the historical native installer. Retain old artifacts/state.

Unknown running containers or failed stop remain blocked, never a force cleanup
or default timeout kill. Explicit infinite Podman/application drain and systemd
stop timeout require real tests with running work. Account/peer mapping, FD3/PID1,
secret separation, Caddy verified TLS/Unix proxy and worker no-IP must be proved
in actual local containers, with no NAS bind during OPS-015. REL-010 commits
reviewed 0.2.0 source; its dirty working-tree builds are previews. REL-012 builds
final identified wheel/sdist/images from that clean committed source and records
evidence without changing package inputs. Use a clean detached source worktree
outside ignored repository parents (REL-012 uses /var/tmp/hfcache-rel-012-source)
so type/test discovery is not silently excluded. Keep final production artifacts,
contexts, provenance and logs outside that source checkout. Normal ignored gate
outputs such as .venv, cockpit/node_modules and dist may be inside while tracked
Git state stays clean.
Main-workspace task/evidence edits cannot contaminate source provenance; source
and evidence commits remain distinct. A stopped or incompletely scoped gate is
not passing evidence even if its wrapper returns 0.

Stage non-secret immutable runtime artifacts with umask 022 and verify directory/
file readability as the actual service UID/GID before selection. A root-only
successful validation does not prove runtime readability. Keep private manifest/
backup permissions separate; retain and verify a known unusable stage before any
explained relocation/restage, never clean it automatically.

During this readonly rollout, the permanent host notify guard is independent of
current. Drain/quiesce actual executors before root transfers its original lock
through the installer and back to READY guard ownership, with NAS-ro and writer
masks maintained. The system bridge requires that READY state; user-default app
autostart is forbidden. Keep the fixed host policy/effective drop-ins in rollback
evidence separately from the selected app artifacts; no rollback may remove the
write barrier or fabricate host-ro proof from a private mount namespace.
Production enablement stays OPS-016; no tag or
NAS/full-domain acceptance follows from packaging. Decision 126 restrictions remain.

Detailed [rootless runtime/build/profile contract](../containers.md) owns the selected deployment boundaries and actual task evidence.

## Worker-listener correction release boundary (OPS-017)

[Decision 128](../adr/decision-128.md) changes the planned rootless listener to
creation inside the confined PID1 worker with real container-proxied READY.
Native inherited activation stays strict. Source fixtures do not close the
deployed 0.2.0 API-to-worker SELinux hold: clean committed 0.2.1 artifacts, actual
separate-container notify/peer/isolation proof and guarded installed PROBE must
precede a corrected local release. No dependency or durable format change is
intended; retain actual compatibility evidence rather than assume it.
Join active work before exact-owned socket cleanup; stale/replacement evidence
or unknown executors must refuse rather than trigger unlink, force or replay.
Rollback to 0.2.0 returns to its documented worker hold. Keep independent host
guard, NAS-ro, writer masks, both stores/observer handles and lock inodes. No NAS
file I/O/jobs or remote publication is authorized by this correction.

## UBI 10 prerequisite for corrected artifacts (OPS-019)

[Decision 129](../adr/decision-129.md) requires pinned UBI micro for every app/
Caddy FROM stage and verified portable interpreter/binary/Red Hat CA inputs.
Preserve initial REL-013 Debian build/proof/compatibility as superseded; its
stopped gate is not passing and exported image is not promoted. REL-013 restarts
from committed OPS-019, rebuilds both UBI service images and repeats clean runtime/
domain/compatibility/stage/gate acceptance. Version stays pre-release 0.2.1.
No production change or worker/NAS hold clearance follows from source packaging.

### 0.2.1 deployment evidence (OPS-018, 2026-10-18)

[OPS-018](../plans/tasks/ops-018-container-worker-rollout.md) proves actual installed
API-origin peer/TLS/drain acceptance from clean 4088994 UBI artifacts, closing
hold 22 only. Completed REL-014 records actual annotated local v0.2.1 at reviewed
deployment 156506f, distinct from artifact source 4088994. No remote push occurs.
Retain0.2.0 rollback's connection limitation and all NAS/storage/calendar/other-host
holds; clean artifact and connectivity evidence is not live workload acceptance.
