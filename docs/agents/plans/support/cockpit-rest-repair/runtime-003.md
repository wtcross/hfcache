# CPR-003 disposable application fixture

This continues the isolated guest in [runtime-setup.md](runtime-setup.md), during
the sole active CPR-003 package. It prepares candidate diagnostics; it does not
complete CPR-008/V54 or prove the original installed symptom. All installation,
service, mount, account and credential changes below occur **inside the owned
guest**, except the explicitly identified local image/transfer files. Production
hfcache installation, original locks/guards/masks, credentials and NAS are untouched.

## Inputs and local image

- Source: `92f19b5a5991b1de3425d9ee3f92400253279cdb`.
- Gate-built wheel: `hfcache-0.2.1-py3-none-any.whl`, SHA256
  `b5ddaadf4301e2c76ad41a697d5d0ad8549bb438190ab033e9af5c1f1d4e735b`.
  Compared all 88 wheel Python files with current source: exact match.
- Existing local UBI application base:
  `sha256:e0ddb59be54236ba0853fe73578a9af0ec7b454159af511ea6d620c9f7b2e030`.
  Its 80 installed dependencies exactly match `uv export --offline --locked
  --no-dev --extra server --extra mcp --no-emit-project --format requirements-txt`
  for Linux/amd64/Python 3.14.6: no missing, changed or extra dependencies.
- Derived untagged application image:
  `sha256:21cd4a2027cde144133d302d5abb803ddb1670b56a47b90c127e981be402258c`.
  Built rootlessly with `--pull=never --network=none --no-cache --iidfile`,
  replacing only the application wheel through the existing local UV donor.
  The temporary installer and copied wheel are absent from the final filesystem;
  no runtime dependency changed. No image tag or registry operation was used.
- Existing local Caddy image:
  `sha256:fa2a5634a525af798ce6da2855d365f7cdf0f9a2d6d0eb56d461626e226acc10`.

Private host inputs/evidence are under
`.local-fixtures/cpr-runtime/cpr003/`. OCI save/transfer used local image IDs;
transport reference-name annotations were removed before guest import, which
preserved exact image IDs and empty `RepoTags`. SSH/SCP used only the previously
pinned synthetic host/client keys, no agent or existing SSH configuration.

Transfer hashes:

| File | SHA256 |
| --- | --- |
| app.oci | `07cd9f5bd5bd29737892c6033f96de455799d38c72be1168f81bb1de6cf2c27c` |
| caddy.oci | `923329e60a0ab1e09fb0b637036990078fec7ea8749b751b9c8305f69ec4448a` |
| container-release.json | `00dda732b03fb48e9cf28287166e779b620ddd8c04e52c08e35b70da8046ec75` |
| source.tar | `6f3f92dfadc0536531c6f7b64cadd39739bce3542ca93da68dfe95dbe36ff03c` |

## Actual guest provisioning

The image already contained NFS utilities, Cockpit 368, Podman 6.1.0,
container-selinux, passt, subordinate-ID tools and the default seccomp profile.
No additional guest RPM installation was necessary.

Created a new guest-only `hfcache` UID/GID 981, private `/var/lib/hfcache` home,
subordinate UID/GID range 655360–720895 and its user manager. Eight legacy
system-manager API/verifier/sync/verify units and calendars were masked; user
manager application units remain a separate authority. No calendar was enabled.

Created an **empty** local backing directory `/var/lib/cpr-nfs/empty`, labeled
with the standard public read-only content type. NFSd binds guest loopback,
exports only to `127.0.0.1` with `ro,sync,root_squash,no_subtree_check,fsid=0`,
and offers NFSv4.2 only. The guest mount unit mounts `127.0.0.1:/` at
`/srv/hfcache` with `ro,nosuid,nodev,noexec,vers=4.2,proto=tcp,timeo=50,retrans=2`.
Actual guest PID 1 mountinfo proved one read-only NFS4 mount; the tree is empty.
No archive sentinel or archive initialization was created.

Imported the two exact local image IDs into the guest service account's rootless
store. Staged and selected `/opt/hfcache/releases/0.2.1` using the unchanged
protected installer and its 17-file digest manifest, actual guest default seccomp
profile, derived worker policy, quiescence checks and existing local flock.
All nine execution bindings point exactly through `/opt/hfcache/current`.

Created new, separate synthetic writer REST, reader REST, MCP reader, Hub and
TLS certificate/key secret inputs. Guest root retains their protected sources;
Podman supplies the existing role-specific file mounts. Values never enter
browser data, process arguments, environment or this record. The archive policy
uses synthetic UUID `554cf1bf-1c7e-4298-97aa-632908121e8a` and disabled Hub mode.

The original guest domain lock retained device 27/inode 2113 across selection.
Installed the unchanged standalone guard and protected bridge dependency. Actual
guard PID 6300 reached active/running READY with status “Original archive lock
held; host NFS is read-only”. Both guest and host SELinux remain enforcing;
no policy boolean, hardening option or guard check was relaxed.

## Refusals investigated

The first import refused before any image was loaded: administrative SSH inherited
`/home/cprtester`, mode 0700, and `runuser` could not traverse that different
user's directory. A read-only inspection confirmed an empty image store. Setup
then changed its own working directory to `/`; directory permissions and role
identities were preserved. This was a fixture invocation defect, not evidence
of the installed Cockpit trigger.

An import assertion then encountered Podman 6.1's bare hexadecimal `Id` shape.
Inspection confirmed the exact intended image hash and `RepoTags=[]`; the fixture
comparison now canonicalizes only the optional `sha256:` prefix. No production
launcher or identity check changed.

The first guest bridge activation failed with terminal status
`4/NOPERMISSION`; all three user roles were inactive with no payload containers.
The private setup's `umask 0077` had filtered the installer's requested public
directory mode `0755` to `0700`. Exact service-user reads failed for the indexed
unit links. Corrected only the six root-owned public artifact directories to the
declared `0755`, retaining every artifact/index byte, all secret/state `0700`
directories, the selected identity, original held lock and NFS-ro barrier.

The second activation still failed before payload startup. Bounded guest journal
inspection recorded the precise enforcing denial:

```text
denied { start }; scontext=system_u:system_r:init_t:s0;
tcontext=unconfined_u:object_r:usr_t:s0; tclass=service; permissive=0;
path=/etc/systemd/user/hfcache.target
```

The link resolves to
`/opt/hfcache/releases/0.2.1/rendered/hfcache.target`. The rootless staging
installer does not register SELinux rules or relabel. Historical
[OPS-018](../../tasks/ops-018-container-worker-rollout.md) already records reviewed
purpose-specific local fcontexts/`restorecon -F` for new immutable artifacts and
the inherited-CWD operator refusal. [OPS-016](../../tasks/ops-016-local-rootless-deployment.md)
records the initially omitted target label and its correction. The living
rootless staging instructions had omitted these explicit operator prerequisites;
this fresh fixture had not applied them. This evidence does not establish that
the previously installed host has those omissions.

After preserving both failed activation records, applied these exact guest-only
administrative argv (all exited 0), referencing the standard type on
`/usr/lib/systemd/user/basic.target` first:

```text
semanage fcontext -a -t systemd_unit_file_t /opt/hfcache/releases/[^/]+/(rendered|packaging/(containers|systemd))/[^/]+\.(service|socket|target)
semanage fcontext -a -t bin_t /opt/hfcache/releases/[^/]+/scripts(/.*)?
restorecon -RF /opt/hfcache /usr/local/libexec/hfcache-readonly-guard /etc/systemd/system/hfcache-readonly-guard.service /etc/systemd/system/hfcache-containers.service.d
systemctl daemon-reload
runuser -u hfcache -- env -u DBUS_SESSION_BUS_ADDRESS XDG_RUNTIME_DIR=/run/user/981 systemctl --user daemon-reload
```

These are standard object labeling for the new public code/units, without a new
allow rule, boolean change, permissive mode or process-label bypass. Exact
post-label observations (all at sensitivity `s0`):

| Guest file | SELinux context |
| --- | --- |
| `rendered/hfcache.target` | `system_u:object_r:systemd_unit_file_t:s0` |
| `rendered/hfcache-api.service` | `system_u:object_r:systemd_unit_file_t:s0` |
| `scripts/hfcache-client` | `system_u:object_r:bin_t:s0` |
| `scripts/container-service.py` | `system_u:object_r:bin_t:s0` |

Paths in this table are relative to `/opt/hfcache/releases/0.2.1` inside the
guest. Index/source bytes were independently reverified unchanged after the
standard labeling. The third activation is a separate deliberate attempt after
diagnosed setup corrections; earlier failure evidence remains failed.

## Current handoff

Paused after a stable read-only observation, exit 0, recorded privately in
`cpr003/evidence/runtime-handoff.json`. All three activation attempts and the
standard label proof remain separate guest records under `/root/cpr-fixture`.

| Actual state at pause | Evidence |
| --- | --- |
| System bridge | active/exited; MainPID 0 |
| User target | active |
| Caddy | running container `f350d526c19a26c40f43144aaa5f2bd94e5e7b03ed8e4e5377835a37fa06ce6d`, payload PID 7396, service launcher PID 7357 |
| Verifier | unit failed, MainPID 0, process exit 126; created container `7b07b8c0e2fe779d3e4978dc0eefdc0c283cb0ac2a3366c6c7aff2b8314612e4`, Running=false, payload PID 0 |
| API | inactive/dead, MainPID 0, dependency failed; no API socket |
| Private worker listener | absent |
| Both operation-state directories | empty; no admitted REST work |
| Original domain lock | device 27/inode 2113, UID 981/mode 0600; independent noncreating exclusive-flock attempt refused because guard still holds it |
| Guard | active, PID 6300, original-lock/NFS-ro READY status |
| Guest storage/network | same guest-only read-only NFS4 mount; no IPv4 default route; SELinux enforcing |

The verifier never reached application startup: crun refused to reopen the empty
host placeholder `etc/hfcache/credentials`, before installing its inaccessible
in-container mask. Unit process exit 126 is a launcher/OCI failure, not a domain
Envelope. The engine's created-container `ExitCode=0` is not execution success;
`StartedAt`/`FinishedAt` remain zero and no payload PID exists.

This exactly matches the already recorded empty-placeholder setup correction in
[OPS-016](../../tasks/ops-016-local-rootless-deployment.md). It is an omitted
fixture prerequisite, not a demonstrated new product defect. No host placeholder
permission has been changed at this pause. Exact read-only identity/emptiness
proof: `/etc/hfcache/credentials`, root UID/GID 0, directory mode `0700`, device
64515/inode 25174935, not a symlink, zero children.

**Unblock condition for the next active package:** independently recheck that
exact guest-only placeholder is still the same root-owned empty directory and
that the retained verifier container still has Running=false/PID 0. Only then
apply the historical intended placeholder mode `0755`; never chmod a nonempty or
unexplained credential directory. The fixed worker/client tmpfs masks must remain
read-only mode `000`. Reobserve unchanged guard/lock/NFS-ro/masks, then deliberately
start the known failed worker and dependent API through their exact user units.
Preserve the known created-container record and let the existing helper enforce
its own ownership/state checks; do not delete containers or sockets manually.

No authenticated CLI/API validation was attempted while its prerequisite listener
was absent. No healthy API/worker, real Cockpit/PAM chain, candidate pipeline or
V54 acceptance is claimed. Original installed `reconnected` cause remains
unresolved. This guest's isolated Caddy may remain running while paused; its
backend is unavailable and no archive job is active. Do not stop or replay
anything merely because an observer ended.

Keep the original guest lock/NFS-ro/masks, separate credentials, fixed launcher,
derived seccomp and manager binding protections. After that unblock condition,
inspect effective role state and execute bounded authenticated version/config
validation through the exact transient systemd → fixed rootless client →
Unix-socket API chain.
Candidate writes/install diagnostics must use the actual guarded helpers and
root configuration lock; an ordinary direct file write is not equivalent proof.

No real archive workload, Hub access, production inspection or deployment,
registry/push/tag operation, browser token or fallback transport is authorized.
Cleanup follows the identity/drain precautions in the retained bootstrap record.
