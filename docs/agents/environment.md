# The writer VM and the live archive

`hfcache` is deployed on the host that usually holds this working copy. That
is unusual enough to say plainly: **a session editing this repository may be
sitting on the production writer**, one `sudo` away from a live archive. This
document is what such a session must know, and what it must not do.

## Where am I?

```bash
hostname                 # hfcachewriter.lab.example.com → the production writer
findmnt /srv/hfcache     # live NFSv4.2 mount of tank/huggingface-archive when deployed
```

On any other machine this document is background — but the hard limits below
apply wherever the archive mount exists.

## The deployment, in facts

- **Releases:** `/opt/hfcache/releases/<version>`, with `/opt/hfcache/current`
  switched by atomic rename and `/opt/hfcache/python` holding the pinned
  uv-managed CPython 3.14. All root-owned; the service identity cannot modify
  the code it runs. Install and switch only via `scripts/install-release.sh`.
- **Configuration:** `/etc/hfcache/config.toml`, `0640 root:hfcache`, and the
  default `--config` path, so installed-CLI invocations need no flag.
- **Service identity:** `hfcache`, nologin. Exercise the installed CLI as it:

  ```bash
  sudo -u hfcache /opt/hfcache/current/.venv/bin/hfcache status
  ```

- **Units:** `hfcache.target`; `hfcache-sync.service` + `.timer` (enabled,
  daily); `hfcache-verify.service` + `.timer` (installed, **disabled** until
  the operator confirms the quarterly calendar);
  `srv-hfcache.mount`/`.automount`; a journald drop-in (persistent storage);
  tmpfiles for `/run/hfcache`, where the exclusive lock lives (`AD-17`).
- **SELinux is enforcing.** Hardening is validated, not assumed:
  `sudo scripts/check-hardening.sh` runs the deployed unit's own `[Service]`
  properties around a real workload. Re-run it after any unit change and
  after `huggingface_hub`, `hf_xet`, or Python upgrades.
- **Archive layout and permissions:** `docs/architecture.md` §5. What is
  still open host-side: **Operator handoff** in `docs/progress.md`.

## Hard limits

**API-014 source/deployment boundary (2026-10-18).** The branch now packages API
and private verification socket/services plus API-only scheduled clients. Installed
facts above are historical deployment evidence, not proof these units are running.
The actual verifier, not its client wrapper, needs no-IP/offline/credential-source
masking acceptance. Custom development credential paths need explicit masks/probes.
Preserve API/verifier/scheduled state and shared runtime locks. Stopping a client
or seeing a free lock does not prove execution ended; follow actual server/worker
drain and exact operation evidence before release/mount work. Real activation,
cgroup no-IP/no-credential, SELinux/NFS and installed hardening remain operator
deployment holds. See [decision 121](../adr/decision-121.md) and
[deployment quiescence](../deployment-centos-stream-10.md#13-upgrade-plan-30).
This task authorizes no host operations or production archive work.

Carried from plan §36.4–§36.5 and not relaxed by §36's supersession
(decision 82). These bind any session on this host.

- **Never write under `/srv/hfcache`** outside the application's own
  transactional code paths — no manual creation, deletion, chmod, or "repair"
  of anything there. The application refuses to delete what it cannot explain
  (`FS-19`); a session does not get a lower bar.
- **Never run `hfcache archive init`.** It was performed once, under explicit
  pre-authorization, and the sentinel plus the configured UUID now prove
  identity (`FS-21`–`FS-23`). Re-initialization is refused by design; do not
  test that against the live mount.
- **Never weaken SELinux or systemd hardening** to make something pass
  (plan §22.5, §23). A probe failure is information about the sandbox, not an
  obstacle.
- **No reboots**, no restarting the network stack or `remote-fs.target`, and
  no NFS disconnection tests against the live mount (plan §26.4–§26.5) —
  those are operator-supervised items, and some would terminate the session
  itself.
- **Do not enable `hfcache-verify.timer`** — operator handoff item 8 owns the
  calendar decision. Quiesce during deploys by stopping `hfcache-sync.timer`,
  never `hfcache.target` (decision 65).
- **No NAS-side changes.** Everything on `nas.lab.example.com` — exports,
  snapshots, quotas, scrubs — is operator work, tracked in the handoff.
- Build and test as the login user; `sudo` is for installation and system
  configuration steps. Rehearsals that need a mutable archive use the
  throwaway loopback archive of `docs/recovery.md` §6, never `/srv/hfcache`.


API-017 consolidates these unchanged limits in the
[operator rollout checklist](../deployment-centos-stream-10.md#17-rest-and-mcp-rollout-checklist-api-017).
The API/MCP feature branch and throwaway installed wheels are repository evidence,
not a production release or permission to manipulate host services/state. Keep
both operation stores and scheduled observation handles through approved drain/
rollback, and preserve the disabled verification calendar. No repository plan
closure clears the actual no-IP/credential/NFS/SELinux/TLS/firewall holds.


## Current scoped local rollout authority (OPS-014, 2026-10-18)

Tyler's newer authorization selects the
[local rootless rollout](../plans/2026-10-18-plan-local-rootless-rollout.md),
qualifying the earlier feature task's no-host-action boundary. Only root performs
reviewed local host mutations. No NAS content or metadata writes, other-host
changes, remote push/registry publication or ACME issuance is permitted. Reuse
appropriate existing local secrets without printing them; credential classes
remain separate. The actual rootless Caddy/API/worker/client design follows in
OPS-015, after the guard task is completed and committed.

Before rollout, record local state, block legacy scheduling/writers, prove actual
executor quiescence and retain the noncreating local flock. Enforce a client-side
read-only remount plus persistent local mount-unit override without unmount,
disconnect, NAS file I/O or server policy changes. Keep sync stopped and verify
timer disabled. Never use NAS chown/relabel/copyup or a write probe to prove this
barrier; preserve SELinux/hardening, lock inodes, both operation stores and pending
observation handles. Unknown activity/state refuses further work. Host-local
throwaway tests are distinct from forbidden real storage acceptance; see
[decision 126](../adr/decision-126.md) and the selected task for actual evidence.

OPS-016 makes the guard permanent host policy outside the app's current selector:
UID/GID 981 holds the original noncreating flock and proves host NFS-ro via
/proc/1/mountinfo before READY. A protected bridge dependency and no user-default
app-target enablement preserve normal boot order; root alone performs the
quiescent holder handoff with NAS-ro/masks continuous. The guard is not a
continuous monitor and a private read-only sandbox view is not host proof.
Application/immutable artifacts remain clean 481fcc4; host policy, actual
activation and residual holds are separately recorded in
[OPS-016](../plans/tasks/ops-016-local-rootless-deployment.md).
