# Roll out the local rootless runtime without changing NAS data

| Field | Value |
| --- | --- |
| Plan ID | `2026-10-18-plan-local-rootless-rollout` |
| Status | active |
| Created | 2026-10-18 |
| Authorization | Tyler authorized review, local release and production rollout on this host, then required Caddy and rootless Podman runtime; NAS content/metadata writes and changes to other hosts remain forbidden. |
| Reviewed baseline | `c73822d`, completed REST/MCP implementation on `feat/rest-api-and-mcp`; source metadata `0.1.10` |
| Tracker | [current.md](current.md) |
| Execution | Six sequential work packages; one active task and one implementation/evidence commit per package |

## Outcome and boundaries

Deploy the reviewed API/MCP implementation behind Caddy using rootless Podman
for Caddy, API, private verification and runtime clients. A local `hfcache.target`
entrypoint must start Caddy and API through a reviewed system-to-user manager
bridge. Preserve one application, bounded execution/metadata pools, exact durable
observation, peer-checked private verification and whole-archive credentials.
The explicit user-service/container details are OPS-015 work, not an assumption that existing host
services or tests already prove a container deployment.

This authorization is local to `hfcachewriter.lab.cross.solutions`. It permits
necessary reviewed local packages, accounts/user-manager configuration, protected
secrets, unit/container/proxy configuration, installation, local review/landing
and annotated release tagging. It does not authorize remote pushes, registry
publication, ACME issuance, changes to DNS/NAS/other hosts or another host's trust
store. Reuse appropriate existing secrets without printing their values. Hub,
REST and optional MCP authority remain separate; missing API/MCP credentials may
be generated and protected locally.

**No NAS content or metadata writes.** Before rollout, snapshot local state,
pause/disable and block legacy scheduled writers, prove actual executors are
quiescent and retain a noncreating local flock guard. Enforce a client-side
read-only remount without unmount/disconnect and a persistent local mount-unit
override. Do not stop the existing lifecycle target or weaken SELinux/hardening.
Every subsequent container must bind NAS read-only without ownership/label/copyup
changes. Never use `:U`, `:z`, `:Z`, chown, chmod, relabel, repair, initialization,
sync, non-estimate verification or an archive-writing probe on NAS. Keep sync
stopped and verification scheduling disabled. No pending observation evidence is
reset to authorize replay. OPS-014 performs no NAS file I/O; its evidence comes
from local unit/process/cgroup/mount information and the existing local lock.

Local deployment acceptance is deliberately partial. Version/capability/auth/
proxy/registry/credential/isolation/drain checks and owned host-local disposable
fixtures may pass; real NAS write, complete sync/full-verify/catalog/report,
NFS publication/recovery and NAS workload hardening checks remain NOT RUN, not
passing. Production metadata reads must also be reviewed against the no-metadata-
change constraint; a client read-only bind alone is not a claim about server
access-time policy. Do not issue an unreviewed archive read as a substitute.

## Reviewed facts and contracts

Root's local inventory reports Podman 6.0.2 installed and Caddy absent; service
UID/GID 981 (`hfcache`), home `/nonexistent`, nologin, no subordinate IDs or linger;
deployed bare-host application 0.1.10; sync inactive/MainPID 0, sync timer active
with next event 2026-10-19 02:01 EDT; verify timer disabled; NAS at `/srv/hfcache`
is currently read-write NFS 4.2; SELinux enforcing. Existing encrypted `hf-token`
and Cockpit self-signed TLS material exist, but API/MCP sources do not. These
are initial inventory facts, not implementation or acceptance claims.

Review [invariants](../invariants.md) INV-002/003/005–007/010–016 and AD-16/17/21,
[environment](../agents/environment.md), [release](../agents/release.md),
[deployment](../deployment-centos-stream-10.md), [server](../server.md),
[security](../security.md), [scheduling](../adr/systemd-scheduling.md) and
[decision 121](../adr/decision-121.md). [Decision 126](../adr/decision-126.md)
defines this data-preserving authorization/host guard and partial acceptance.
[Decision 127](../adr/decision-127.md) records the selected explicit rootless
user-service architecture and predecessor amendments before implementation;
actual container proof remains OPS-015 evidence. REL-010 will introduce version
0.2.0 for the breaking API-only operational CLI and explicit container deployment
contract; OPS-015 itself changes no version.

## Tasks and dependency order

| Order | Work package and task | Depends on |
| --- | --- | --- |
| 1 | [OPS-014 — establish local rollout guardrails](tasks/ops-014-local-rollout-guardrails.md) | None |
| 2 | [OPS-015 — package the rootless runtime](tasks/ops-015-rootless-container-runtime.md) | OPS-014 |
| 3 | [REL-010 — review and commit 0.2.0 source](tasks/rel-010-rootless-release-artifacts.md) | OPS-015 |
| 4 | [REL-012 — build clean committed release artifacts](tasks/rel-012-clean-container-release-artifacts.md) | REL-010 |
| 5 | [OPS-016 — roll out and prove the local runtime](tasks/ops-016-local-rootless-deployment.md) | REL-012 |
| 6 | [REL-011 — record the local release and handoff](tasks/rel-011-local-release-and-handoff.md) | OPS-016 |

Task records own mutable status. Do not start a dependent package until its
predecessor is completed and committed. Collaborators share the selected task;
only root performs privileged changes. Existing completed feature records remain
unchanged, and unrelated backlog is not activated.

## Acceptance and validation

Every package passes `scripts/check.sh`; release/container boundaries require
`--with-build` and meaningful image/rendered-unit/Caddy/peer/activation/drain/secret/
read-only fixtures. Record actual installed tool versions, source commit and
wheel/sdist/image digests with locked dependency profiles; do not equate displayed
version with artifact identity. No auto-update or runtime unreviewed image pull.
Use actual target readers for retained archive/service/scheduled state; missing
old support is not schema refusal or proof of nonexecution. Preserve rollback
artifacts, both operation stores, scheduled handles and persistent lock inodes.

The local rollout must prove rootless ownership/user namespaces, target starts
Caddy/API, private worker no-IP/no-credentials, protected Unix access and verified
TLS/proxy routing using the actual containers. Keep all writes on reviewed local
filesystems. Do not expose an alternative bare-host operational runtime or an
unrestricted Podman socket to containers. Review Cockpit/client invocation and
system-versus-user manager boundaries explicitly. Real NAS write acceptance and
other-host/NAS/calendar work remain open in final release notes. A local tag may
identify the actually deployed artifact with this partial acceptance stated; it
does not certify forbidden tests. Never push the tag or branch remotely.

## Lifecycle

- 2026-10-18: Activated under the new user authorization after completed feature
  commit `c73822d`; OPS-014 is the sole task in progress. Five unused task IDs
  were checked against actual repository records. Previous no-deploy scope stays
  historical; this plan grants only the local actions and constraints above.

- 2026-10-18T14:08:47Z: OPS-014's actual root guard exits 0. Local backup,
  blocked legacy activation, quiescent UID/services/cgroups, retained original
  local lock, persistent client read-only remount, active target and Enforcing
  SELinux are recorded in the task. The gate runs behind an empty read-only
  tmpfs covering NAS; its corrected launch and final result are separate evidence.
  OPS-014 completion still waits the actual required gate, and OPS-015 remains
  pending until the guard package is completed and committed.

- 2026-10-18T14:25:55Z: OPS-014 completed with actual corrected NAS-masked gate
  exit 0: 3,624 Python tests (40 deselected, 455.10 seconds), format/lint/whole
  types, 0.1.10 builds/three locked installation profiles and 127 Cockpit tests/
  production build. First launch refusal and inherited-environment failed gate
  remain recorded in the task; no production/test source changed. Root rechecked
  read-only NAS, four masked inactive units and retained guard after acceptance.
  Current selects OPS-015 pending; its activation waits this package's commit.

- 2026-10-18: OPS-015 activated after guard commit 28f9934. Amend the initial
  Quadlet proposal to explicit rootless user systemd services: reviewed argv and
  non-killing stop/removal avoid generated replacement/forced-cleanup/short-timeout
  hazards for unknown surviving executors. Decision 127 governs the required
  Caddy/API/private-worker/client boundaries. Necessary root-owned local account/
  rootless test infrastructure and actual disposable proof are authorized here,
  without a NAS bind or production switch; release/version remains REL-010.

- 2026-10-18, OPS-015 handoff amendment: split pending source/version and final
  artifact work to avoid building a deployable artifact from uncommitted source
  or adding a second commit to one work package. REL-010 commits reviewed 0.2.0
  source and required gate evidence; its working-tree builds are previews only.
  New unused REL-012 builds and proves immutable artifacts from that clean
  committed source, then records evidence without changing package inputs.
  OPS-016 now depends on REL-012. All three remain pending; no release execution,
  production selection or tag is authorized before their committed dependencies.

- 2026-10-18: OPS-015 completed with actual NAS-free rootless worker, Caddy/TLS/
  API/MCP/client and selected-overlay proofs, rendered-unit syntax, exact
  protected selection/rollback tests and corrected NAS-masked --with-build
  pipeline exit 0: 3,792 Python tests (40 deselected, 453.62 seconds), three
  locked installation profiles, 135 Cockpit tests/build and four extra wheel
  smokes. Failed real policy/fixture findings, the manually stopped metadata-
  review gate and passing pre-selector gate remain separate task evidence.
  Runtime source version remains 0.1.10; no production switch/release/tag or NAS
  file I/O. Current selects REL-010 pending until this package is committed.
  The live guard and installed-manager/full-storage acceptance holds remain.

- 2026-10-18: REL-010 activated after OPS-015 committed as edef480. Root's local
  main fast-forward review lands 86f6e8b→edef480 and returns to the clean feature
  branch without another worktree or remote action. This package prepares and
  gates 0.2.0 source metadata; clean final artifacts wait REL-012, deployment
  waits OPS-016 and local tagging waits REL-011.

- 2026-10-18: REL-010 completed local review and project-only 0.2.0 preparation;
  all 93 nonproject lock records are unchanged. The actual NAS-masked --with-build
  gate exits 0: 3,792 Python tests/40 deselected in 461.15 seconds, three locked
  installation profiles, 135 Cockpit tests/build and four extra wheel smokes.
  README/CHANGELOG remain preparing/not deployed/tagged. Preview hashes are task
  evidence, not deployable artifacts; current selects REL-012 pending until this
  source/version commit exists. All host/NAS guards and acceptance holds remain.

- 2026-10-18: REL-012 activated after REL-010 committed as 481fcc4. The clean
  detached source checkout now lives outside ignored repository parents at
  /var/tmp/hfcache-rel-012-source. The first .scratch checkout caused Pyrefly
  test skipping; its 19.907-second/SIGTERM-stopped gate is preserved, not passed
  despite wrapper exit 0. Final artifacts/contexts/provenance/logs stay outside
  the clean source; normal ignored gate outputs may be inside. No runtime source
  change or production activation follows from this execution-path correction.

- 2026-10-18: REL-012 completed clean 481fcc4 source builds/provenance, actual
  new-image worker proof, 90 compatibility observations, protected indexed stage/
  UID-981 controls and local OCI exports. The ignored-parent stopped gate and
  preserved umask-077 stage/readability failure are separate from corrected
  acceptance. Final --with-build exits 0: 3,792 Python tests/40 deselected in
  507.85 seconds, three locked installation profiles, 135 Cockpit tests/build and
  four extra wheel smokes. Package inputs/source stay unchanged and Git-clean;
  source/evidence commits remain distinct. Current selects OPS-016 pending until
  this evidence commit exists. No production switch, service-engine image load,
  runtime activation or NAS file I/O; native 0.1.10 and host guards remain.

- 2026-10-18: OPS-016 activated after REL-012 committed as 7d27e86. Before host
  enablement, decisions 126/127 refine the persistent guard into fixed host-only
  notify policy independent of app current, with host /proc/1 mount proof,
  original lock, bridge readiness ordering and no user-default app autostart.
  Root's actual strict-sandbox source/view proof passes without NAS file I/O;
  no application readiness/deployed README claim is made before actual startup.

- 2026-10-18: OPS-016 completed guarded local selection and partial rootless
  deployment: TLS/auth/metadata/MCP registry, container client, isolation and
  non-killing drain/restart pass, with original lock/stores preserved. Actual
  API-to-worker SELinux connectto is refused and remains a release hold; host
  FD3 peer proof is not end-to-end verification. No hardening bypass is used.
  Final NAS-masked --with-build exits 0: 3,827 Python tests/40 deselected in
  471.22 seconds, three locked installation profiles, 135 Cockpit tests/build
  and four extra wheel smokes. NFS-ro, four legacy writer masks, Enforcing policy
  and forbidden NAS/other-host/calendar acceptance holds remain. REL-011 is next
  pending until this package commits; no tag or remote publication occurs here.
