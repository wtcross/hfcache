# OPS-018: Deploy and accept the corrected listener locally

| Field | Value |
| --- | --- |
| Work package | `OPS-018` |
| Status | completed |
| Plan | [Container worker listener](../2026-10-18-plan-container-worker-listener.md) |
| Depends on | [REL-013](rel-013-container-worker-artifacts.md), committed 586b7c1 |
| Scope | Guarded local host rollout and non-executing acceptance; no live NAS file I/O or jobs |

## Scope and acceptance

1. Record host/runtime/current identities and prove the permanent readonly
   guard, host NFS-ro mount, legacy writer masks, disabled verification calendar,
   actual executor quiescence and original lock inodes. Reuse existing protected
   credentials and TLS sources without printing values. No remote change.
2. Drain API before worker without force and stop the old rootless .socket unit.
   Account for its RemoveOnStop=false pathname: retain and move only the proven
   old socket under reviewed quiescence into protected local evidence before
   the new worker binds. Unknown paths or active/ambiguous listeners refuse;
   neither startup nor the installer gets generic stale-socket cleanup power.
   Record exact old pathname/device/inode/owner/mode before its reviewed rename
   into new root 0700 /run/hfcache-retired-0.2.0-20261018 on the same /run
   filesystem. Retain a persistent nonsecret ledger under
   /opt/hfcache/deployment/20261018-worker-0.2.1; do not copy or unlink the socket
   across the different /opt filesystem or perform generic cleanup.
3. Perform the reviewed installer switch to REL-013's exact 0.2.1 stage while
   holding the original noncreating lock and continuous NAS-ro/mask barriers.
   Preserve both stores, pending observers, all locks and old artifacts. Reclaim
   the permanent guard before application startup; it remains independent of
   current. Reload both managers and inspect effective fragments/drop-ins and
   nine bindings. Verify the rootless .socket is dormant and cannot be manually
   started, while the native profile's historical activation is preserved.
4. Start the corrected target after actual worker READY and prove the actual API
   container can perform the fixed framed private PROBE against the worker-created listener with
   expected peer UID, unchanged SELinux enforcement and no label/policy bypass.
   Prove PID1/internal FD3, actual no-IP/secret/mask/capability/cgroup/root/lock
   barriers and a clean target drain/restart with socket cleanup and retained
   stores/locks. No production verification or other command is submitted.
5. Repeat verified local TLS and bounded REST version/capabilities/OpenAPI,
   authentication/read-write denial, MCP initialize/tools-list and fixed client
   readiness checks without invoking archive-reading tools/routes. Preserve
   protocol negotiation rules and sanitized nonsecret evidence. Record exact
   deployed source/images, guard, effective units and the new peer acceptance.
6. Keep live NAS write/full-domain/NFS-workload, calendar and other-host holds
   explicit. Rollback to 0.2.0 must drain cleanly, preserve state and restore its
   activation arrangement deliberately; it reintroduces its known API-worker
   SELinux hold rather than claiming equivalent acceptance.

## Contracts, invariants, and ADRs

Review the accepted OPS-017 listener decision; decisions
[65](../../adr/decision-065.md), [115](../../adr/decision-115.md),
[121](../../adr/decision-121.md), [126](../../adr/decision-126.md),
[127](../../adr/decision-127.md), [128](../../adr/decision-128.md),
[129](../../adr/decision-129.md); release/deployment/environment/containers
contracts; INV-002/003/005–007/010–016, AD-16/17/21 and FS/TX preservation.
Select only REL-013's exact clean application/Caddy images; no new application
or image implementation/build, credential authority or durable schema change is
part of the rollout. An unexpected required source fix receives an explicit task and
fresh artifacts before deployment continues.

## Validation

Planned, not execution evidence: protected host before/after ledger; reviewed
guard handoff and guarded selector switch; effective manager/unit/binding checks;
actual API-container framed PROBE and isolation; TLS/REST/MCP metadata-free
acceptance; clean drain/restart and lock/store preservation; record/link audits
and full NAS-masked `scripts/check.sh --with-build`. Forbidden NAS workload
checks remain NOT RUN. Root alone executes privileged local actions.

## Execution notes and handoff

Activated 2026-10-18 after REL-013 committed as
586b7c13b95c4e690150c4298c670a27a78a9efa. Root alone executes reviewed privileged
rollout from the protected 0.2.1 stage, immutable source 4088994, exact app image
sha256:e0ddb59be54236ba0853fe73578a9af0ec7b454159af511ea6d620c9f7b2e030,
Caddy sha256:fa2a5634a525af798ce6da2855d365f7cdf0f9a2d6d0eb56d461626e226acc10
and artifact-index SHA256
5baaa5e1cfc5a7d6b84a96ecb5c5ceac80ee56af0bd0f65b74b18d921efa9c9e.
Hold 22 stays open until the actual installed API-container PROBE passes. This
activation is not acceptance; no execution is claimed yet. Preserve old failed
AVC/probe evidence alongside future corrected actual container-origin proof,
without relabeling a historical failure as passing. NAS-ro/guard/masks/stores/
handles/hardening remain throughout; no NAS file I/O/jobs or remote actions.

### Image preparation, preserved refusals and guarded selection

All six existing service-UID 981 Podman secrets remain unchanged. Root protects,
verifies and loads exact clean app e0ddb59b…/Caddy fa2a5634… OCI images into the
981 rootless engine at /var/lib/hfcache/container-home/.local/share/containers/storage,
without activation at that point. Protected records below live under
/opt/hfcache/deployment/20261018-worker-0.2.1.

host-state-before.json SHA256
a041668f8d8e8f944c461a108836492d7dd60d833d497189736f56464e6af9e8
proves guard PID717169/original device 27:inode 2273, masks/NAS-ro, stores containing
only .lock, and old socket device 27:inode 208450. The first metadata preflight
refuses an unavailable timer MainPID property before mutation; preserve the
reviewed original script/host-snapshot-attempt1.json and corrected reviewed
helper. Earlier installer quiescence also refuses inaccessible inherited repository
working directory; rerun from / proves full quiescence without any earlier
selector change. These are operator inspection failures, not application defects.

Bridge-only stop exits 0. Root records and renames only exact old socket inode 208450
on the same /run filesystem into new root 0700
/run/hfcache-retired-0.2.0-20261018/verification.sock.0.2.0, retaining
retired-socket.json persistently; no socket copy/unlink or generic cleanup occurs.
Only new 0.2.1 local artifacts receive reviewed container_file_t/systemd_unit_file_t/
bin_t fcontexts and restorecon-F; no NAS labels, process-label bypass or allow rule.

Reviewed guarded switch actually exits 0: current→releases/0.2.1, source 4088994,
index 5baaa5e1…, with new permanent READY guard PID809950/invocation
9073507e26694ba88134c5905fa383cd holding the same device 27:inode 2273.
NAS-ro/masks remain continuous, stores stay unchanged and hfcache.target never
stops. guarded-switch.json preserves the transition.

Both managers reload. effective-units-before-start.json passes exact physical
fragments/no home override/no user drop-ins; worker Type=notify/NotifyAccess=all,
API Requires+After worker, target three roles, dormant inactive .socket with
RefuseManualStart=yes, infinite non-killing drain, memory limits and hardened
bridge alias remain. A first inspection refuses unavailable Sockets show-property;
preserve effective-units-attempt1.json. Final proof checks indexed absence of a
Sockets directive and actual dependency references, accounting for the manager's
:rbind representation rather than weakening the bind requirement.

Applications have not started at this checkpoint; selection is not readiness
and hold 22 stays open. Fresh NAS-masked full gate is running as
hfcache-ops018-ubi-gate, invocation 80ca5b2798834c369fbc5c57cfb4ef2a,
log .scratch/ops-018-ubi-gate.log. No final gate success is claimed yet.

### First installed acceptance and full gate

Actual first installed acceptance passes from the reviewed protected driver.
first-installed-acceptance.json under the protected deployment backup has SHA256
a8313536d14cd300e6e8c2e7a77819a7f745b516a735de9b092611f72e2c80e5.
All 13 verified-TLS REST/auth/MCP checks pass with exact nine tools and negotiated
2025-11-25. Actual API-container framed private PROBE accepts expected UID 981
under Enforcing SELinux: hold 22 can close for this corrected listener while the
old0.2.0 failure remains history. This submits no verification or NAS job.

Actual worker PID1/internal FD3/offline/masks/caps 0/NNP/read-only root/exact bind
inventory and cgroup limits 4GiB/4GiB/512MiB pass; worker READY precedes API start.
Worker notify-unit Conmon MainPID 812285 has READY 3818207159224 after
start 3818204910001. First socket is device 27:inode 209276; local stores remain
unchanged. Existing clean-artifact direct-PID1 socket-denial proof stays separate
from runtime metadata inspection; no podman-exec filter inheritance is inferred.

Root and user systemd-analyze verification exit0 with isolated runtime directories;
unit-verify.json records unchanged live981 manager socket device 76:inode 201.
The fixed host launcher as UID 981 runs --json version --server, exits 0 with empty
stderr, and performs only capability/version GETs: no NAS/Hub secret/state change.
fixed-client-acceptance.json does not treat an empty filtered event window as
container-ID attribution.

The actual NAS-masked full gate exits 0, invocation 80ca5b2798834c369fbc5c57cfb4ef2a,
elapsed 8m46.928s: all format/lint/whole types pass; 4,057 Python/40 deselected in
473.93s; three locked installation profiles; 135 Cockpit tests in 2,255.602718ms/
build 1,272ms and four wheel smokes in 7.02s. Log .scratch/ops-018-ubi-gate.log SHA256
9048611814592367e643e90ebc2cac4fb390649ad26e92bc206a8489032e4075.

### Drain/restart checkpoints, not yet final acceptance

Bridge-only stop exits 0. The first immediate installer quiescence check correctly
refuses still-deactivating PartOf units; retain drain-restart.json. A later
authoritative check passes all three roles Result=success/ExecMainStatus=0, no
PIDs/cgroup tasks, API inactive before worker, exact socket 209276 removed and all
locks/stores unchanged. Guard 809950 and system target remain continuous. Restart
and repeated installed acceptance are in progress; wait for drain-restart-final.json
and final host ledger before completing the task. No NAS file I/O/jobs occur.

### Definitive installed drain/restart and final acceptance

All final acceptance actually completes. The acceptance helper does not perform
the lifecycle (its drain_restart_performed=false); the separate definitive
lifecycle ledger proves the drain/restart before the repeated checks. Protected records under
/opt/hfcache/deployment/20261018-worker-0.2.1:

| Record | SHA256 |
| --- | --- |
| final-installed-acceptance.json | 2f879ff38f17df7eb9f1f0a4a5c602b4c6c13f56c6ccc35bd6fd826c8331034f |
| host-state-final.json | cd032e257cd1ffad4ec46172a3572f2f43572cc4872b4e2e0e7ccb8f4c6f1f31 |
| drain-restart-complete.json | d2a245696821b155d99c44f8cd9eb51eabd438e1caad51f1aa84c71024275d52 |

After real drain/restart, all 13 verified TLS/auth REST/MCP checks, exact nine
tools, actual installed API-container private PROBE under Enforcing and unchanged
isolation/local state pass again. Final exact container IDs:

| Role | Container ID |
| --- | --- |
| API | bdf99487359e60d7a874dfa3715eb5325ead9b5f29b9a0d725a7ca52f825348e |
| Worker | 7b44c231bc8064d80b94cb4411acbdcb41362d65c16981a2126a15ba12b6fcd5 |
| Caddy | d4310bf6397fc70638f2d3a9acbf9fd5e35d8db57377fadaa1b4cf9fd38f7efa |

Worker notify Conmon MainPID 813950/start 3818584710000 reaches
READY 3818586759054 before API startup; actual worker/API/Caddy PIDs are
813953/814035/814041. Lifecycle proves API inactive before worker, all three
Result=success/ExecMainStatus=0, no old PIDs/cgroup tasks/active engine containers,
then replacement roles on the exact selected images. Old owned socket 209276 is
removed; new owned socket 209339 appears. All lock/store bytes and inodes remain,
including original device 27:inode 2273; retired old device 27:inode 208450 remains.
All six secret IDs are unchanged since 0.2.0. Guard 809950/system target stay active
through the lifecycle. Actual host guard/bridge/tmpfiles hashes match the original
protected OPS-016 ledger; immutable app source/images are unchanged.

Preserve two strict intermediate refusals: still-draining PartOf units and an
initial post-Type=exec snapshot before all containers existed. Later authoritative
quiescence/all-role/strong repeat checks pass, without force or cleanup shortcuts.
First complete-ledger assembly also refuses a transcribed tmpfiles-hash mismatch;
the actual protected OPS-016 host_policy_sha256 resolves the expected value,
without changing host policy or files. None is an application-source correction.

## Completion evidence

Completed 2026-10-18, OPS-018, this commit. The protected 0.2.1 stage from immutable
source 4088994 and exact clean UBI app/Caddy/index identities is selected and
running. Actual installed API-origin PROBE closes hold 22 for this listener;
0.2.0 failure/rollback limitations remain history. Verified TLS/auth/MCP/client,
worker READY/peer/confinement, effective units and non-killing drain/restart pass;
all stores/handles/locks/secrets and NAS barriers remain. This is not live NAS
verification or general storage/full-domain acceptance. No NAS file I/O/jobs,
other-host action, remote publication or ACME occurs; verification scheduling
remains disabled and legacy writers masked.

The full NAS-masked --with-build gate actually exits 0:423 formatted/Ruff/whole
types 0;4,057 Python/40 deselected in 473.93s; three locked wheel profiles;
135 Cockpit tests/build and four wheel smokes. Exact command, invocation/log hash
and timings are above. Reviewed INV-002/003/005–007/010–016, AD-16/17/21, FS/TX
and decisions 65/115/121/126–129; no source/image implementation, dependency,
credential authority or schema change. Living contracts/README/CHANGELOG,
[operator hold 22/progress audit](../../progress.md), task/plan/current, links and
whitespace reconcile. REL-014 remains pending until this rollout commit; 0.2.1
has no local tag yet. Root alone performed privileged actions. Independent read-only reconciliation of
seven sealed actual records finds no blocker across source/images/index, exact
roles/READY/peer, guards/locks/stores/sockets/secrets and TLS/auth/MCP outcomes;
IP-companion, empty client-event and separate-lifecycle scope qualifications agree.
