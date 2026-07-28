# The writer VM and the live archive

`hfcache` is deployed on the host that usually holds this working copy. That
is unusual enough to say plainly: **a session editing this repository may be
sitting on the production writer**, one `sudo` away from a live archive. This
document is what such a session must know, and what it must not do.

## Where am I?

```bash
hostname                 # hfcachewriter.lab.cross.solutions → the production writer
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
- **No NAS-side changes.** Everything on `nas.lab.cross.solutions` — exports,
  snapshots, quotas, scrubs — is operator work, tracked in the handoff.
- Build and test as the login user; `sudo` is for installation and system
  configuration steps. Rehearsals that need a mutable archive use the
  throwaway loopback archive of `docs/recovery.md` §6, never `/srv/hfcache`.
