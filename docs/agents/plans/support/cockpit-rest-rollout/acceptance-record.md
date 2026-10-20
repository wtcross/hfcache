# Local rollout evidence

State: REL015 source preparation/gate accepted; OPS023 deployment pending.
No new release, deployment, tag or passing gate is claimed until actually recorded.

## Authority and source

The latest user explicitly requests merge to main/push both remotes, followed by
replacement deployment on this host. Main was fast-forwarded fromdcc2c56 to
cdc35a487dd0d41990b4c3305dc645450943a2a3, preserving nine repair commits. Both
remote main refs were read back at that exact SHA before deployment preparation.
No force or tags were pushed. Earlier repair selector was inactive; the new
2026-10-20 rollout plan/task IDs REL015/OPS023 were checked unused and activated.

0.2.2 was absent in local/GitHub/Forgejo tag refs and protected release/stage paths.
One initial GitHub DNS refusal passed on read-only retry without host/network
change. pyproject and uvlock change only project0.2.1→0.2.2, preserving all94locked
packages. Historical test fixtures retain their old version literals. README and
changelog distinguish candidate from recorded installed release and include tags/
discovery rollback limits as well as Cockpit source repairs.

## Read-only installed baseline (before deployment effects)

Host hfcachewriter.lab.cross.solutions, selected /opt/hfcache/current→releases/0.2.1.
Manifestab6c094292b05d99abbf5b8fb852b1a57a43e845041f00cc0cb94dcb8ef2e042,
index5baaa5e1cfc5a7d6b84a96ecb5c5ceac80ee56af0bd0f65b74b18d921efa9c9e,
source4088994f2b1e02f00a3c1e47cb8ebe662ca64a1b. Appimagee0ddb59be54236ba0853fe73578a9af0ec7b454159af511ea6d620c9f7b2e030;
Caddyfa2a5634a525af798ce6da2855d365f7cdf0f9a2d6d0eb56d461626e226acc10.
Actual service UID/GID981. Permanent system guardPID809950 remains active;
host /proc/1/mountinfo shows NFS4 mountid798/dev0:83 ro,nosuid,nodev,noexec.
Sync/verify timers remain masked/inactive; actual user API/worker/Caddy remain
running with original effective /etc/systemd/user fragments and no drop-ins.
All actual executor/container/cgroup checks still precede any later switch.

Existing config24905bytes/dev64768/inode138336766, predecessor24111bytes/
inode134411820 and candidate24905bytes/inode135083056 are root:9810640 regular.
Original .configuration.lock is root:root0600/dev64768/inode138322689.
No Cockpit policy file currently exists. Preserve these files/inodes; do not adopt,
overwrite or delete the candidate as deployment cleanup. Original domain lock is
separately guarded and must be freshly proved before handoff.

Original Timestral authenticated fixed installed CLI lookup from cwd/ as service
identity returns op0cb77c1c970e21033a9cab7fb8ea872d failed at2026-10-19T14:46:11Z.
Original-key namespace timestral-sync-20261019-410f6659ff9b48379249e7a167a36400
is unchanged. Explicit original-ID wait returns exact stored sync failed Envelope,
exit20/HFMNT010, Envelope runIDca8e75548b784920b44bb638da1692b0; stdoutSHA256
9c0b18f856db2a01bda7331238869ee904e5e820122075e28049e458af0f6b50.
This is the original admitted deadline refusal, not cancellation, replay, successful
sync/publication or permission to release the guard. Preserve the exact terminal
and all stores during protected backup/drain.

## REL015 source gate

First transient launcher with regular-file stdout refused “Remote peer
disconnected”, exit1, raw /tmp/hfcache-rel015-gate.log. Authoritative unit lookup
proved not-found/noPID/noControlGroup/noInvocationID, guard unchanged. No test pass
or installed-symptom cause is inferred from that unclassified launcher refusal.

Separate documented pipe/pipefail/tee launch runs:

```bash
rtk proxy bash -o pipefail -c 'rtk proxy sudo -n systemd-run --unit=hfcache-rel015-gate-20261020 --collect --wait --pipe --uid=tyler --property=WorkingDirectory=/home/tyler/Projects/hfcache --property=TemporaryFileSystem=/srv/hfcache:ro --setenv=PATH=/home/tyler/.local/bin:/home/tyler/.local/share/pnpm/bin:/usr/local/bin:/usr/bin:/bin /usr/bin/python3 .scratch/rel015-gate-wrapper.py 2>&1 | rtk proxy tee /tmp/hfcache-rel015-gate-pipe.log >/dev/null'
```

Invocation135107101a114644b8c9ba063138cef7, PID1819645/UID1000. Wrapper proves
tmpfs/ro,nodev/empty-private-mount at /srv/hfcache before collection, then execs
scripts/check.sh --with-build --require-cockpit with ambient invocation/PID fields
removed. The real host NFS mount is not changed. Actual strict extended gate exit0:5299Python/52deselected in702.67s, all3locked
wheel installation profiles, actual frontend lint/style/types/570unit0skip/
110mounted/fresh production build, then16build-marked/5335deselected in44.59s
(old-wheel2/smoke4/installedCLIprivateUDS10). Transient service success/status0,
runtime15min13.696s, CPU12min5.760s/memory1.3G/no swap. LogSHA256
ac3f7730fefc3c7e17f8e5ba2a55403abdd97517e0a612651d4b17807d716485. [Bounded mounted result](rel-015-mounted.json).
The first failed launcher remains separately recorded; no frontend skip is accepted.
Precommit gate builds remain dirty snapshots, not deployed clean artifacts.

## Build/deploy prerequisites and next action

Pinned portablePython cache35942823bytes/SHA86bf107f65fc30b56f2b263b26797fcbb1661f5315910cdbf27f733eb8738b74
is present, and login engine lists cached pinned UBI micro/minimal/uv/Caddy donors.
No OCI pull/registry operation is needed or authorized. The existing builder may
fetch only hash-locked public Python dependencies during a fresh app layer; cached
foundation images alone do not prove the dependency-install layer is offline.
Fresh app and Caddy builds must bind the exact clean REL015 commit and supplied
wheel; never reattribute old proof records. Worktree/artifact/build/protected
deployment paths are unused at baseline. OPS023 owns the new protected backup,
actual executor drain/guarded selection and installed acceptance. No service stop,
configuration/plugin/policy write, release stage/switch or new tag has occurred.

## Invariant and record review

INV002/003/005/006/010/014/015/016, agentINV011, CP01–14 and actual ADR65/75/79/
115/118–122/126–129/132/134–139 reviewed. No new architecture, dependency, durable
format or workload authority is intended. Old receipts/results, candidate/backup,
original locks, guard/NASro/masks, secret classes and all five disposable guests
remain. Never use source/fixture or metadata readiness as installed workload proof.
