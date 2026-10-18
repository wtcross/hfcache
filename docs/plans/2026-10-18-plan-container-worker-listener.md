# Let the confined rootless verifier own its private listener

| Field | Value |
| --- | --- |
| Plan ID | `2026-10-18-plan-container-worker-listener` |
| Status | active |
| Created | 2026-10-18 |
| Authorization | Tyler's continuing local review, release and rollout instruction covers this necessary verifier-connectivity correction; activated after committed REL-011 2d81df5, preserving the NAS-write ban. |
| Baseline | Deployed 0.2.0 application source `481fcc4`; OPS-016 evidence `11ddd55`; REL-011 closure 2d81df5 is committed. |
| Tracker | [current.md](current.md) |
| Execution | Five sequential work packages after UBI steering; collaborating agents share each selected task boundary. |

## Outcome and scope

Remove the installed API-to-worker SELinux connection failure without changing
SELinux policy, container process labels or the verifier's confinement. The
rootless worker creates its AF_UNIX listener inside its existing PID1 container,
so the kernel socket receives the ordinary container process context. It runs
the same private verification protocol and command implementation, with the
existing peer checks, exact durable identities, offline initialization, shared
archive lock and non-killing drain. Preserve native-profile named inherited-FD3
activation as a separate explicit startup mode.

This follows the completed local rootless rollout's documented partial
acceptance. It does not rewrite the successful or failed 0.2.0 evidence, promise
that a host-origin peer probe proves container access, or claim live NAS
verification acceptance. The intended corrected application version is 0.2.1,
built only after its source commit and deployed through the guarded immutable
selector. No version or image changes occur during drafting.

The scope remains this host only. Keep the permanent host guard, original lock
inodes, NAS read-only mount, blocked legacy writers and disabled verification
calendar. No live archive file I/O, verification/sync submission, NAS content or
metadata write, remote push, registry publication, other-host change or ACME
issuance is authorized. Disposable complete-domain tests use only local fixture
archives. Build and test as the login user. Only root performs privileged local
provision/switch/acceptance steps; source work does not mutate the installed host.

## Runtime boundary (decision 128)

1. Add an explicit rootless-listener flag to the existing
   `hfcache.verification_worker` entrypoint. Native inherited-FD3 activation
   remains strict and never falls back to binding. Rootless mode refuses
   inherited activation environment and every inherited descriptor above stderr
   before shared imports, NSS, policy or state access. It creates its own
   AF_UNIX listener and normalizes it to FD3 without a supervisor, shell or init
   process. Own bootstrap descriptors are distinct from inherited authority.
2. Acquire the existing worker instance lock before binding, and retain it
   through shutdown and socket cleanup. Open the protected private directory
   without following symlinks; require the final directory to be euid/egid-owned
   mode 0700 and refuse any pre-existing pathname, including a stale socket.
   Bind with a restrictive umask and exact 0600 mode, retain its
   created pathname device/inode, then listen and enter the existing runtime.
   Bind through the pinned parent's proc-fd address and prove that exact trusted
   bound spelling in owned mode; preserve native activation's canonical
   getsockname check unchanged. The configured filesystem path still requires
   the pinned-parent socket inode/owner/mode checks.
3. Stop accepting new requests and join active work before closing the listener
   and removing only the exact socket inode created by this invocation. Keep
   the pinned parent and instance lock through that comparison/cleanup. Never
   unlink an unexplained replacement, remove the instance/domain lock, replay
   old receipts or clear stores. A crash may leave a stale socket; startup
   refuses it until reviewed operator handling preserves the evidence.
4. Make only the worker's private socket-directory bind writable; keep the API
   view read-only. Retain read-only root, credential masks, no secrets, no IP
   networking, native AF_UNIX-only seccomp, empty capabilities, NoNewPrivileges,
   UID mapping, local stores and exact shared domain-lock inode. No SELinux
   allow module, label override/disable, privileged container or `+` execution
   prefix is part of this design.
5. The rootless user target starts worker.service as well as API/Caddy. The API
   Requires and orders after worker.service, which no longer Requires or takes
   Sockets from the host .socket unit. Retain the rootless .socket artifact and
   its existing indexed binding, but make it dormant with RefuseManualStart=yes
   and no target/service Wants/Requires reference. Preserve the nine-binding
   and artifact-index shapes where possible; native package activation stays
   unchanged. Use Type=notify/NotifyAccess=all and Podman's supported
   --sdnotify=container forwarding. The direct worker sends a standard-library
   AF_UNIX READY=1 only after the secure listener, instance lock, operation store
   and VerificationWorker initialization succeed, before serving. Prove that
   notification proxy under SELinux; do not replace readiness with sleeps or
   Type=exec ordering. Fresh verification admission retains its private probe.
6. Keep the existing infinite executor stop/drain and API-before-worker stop
   ordering. Clean stop permits restart; a crash/stale pathname refuses rather
   than gaining automatic cleanup authority. Record rollback to 0.2.0 as a
   deliberate return to its known API-to-worker SELinux hold.

## Contracts and decisions

Before implementation, publish the next unused architectural decision (128 was
unused at drafting) for the rootless listener-at-creation boundary. Amend
[decision 127](../adr/decision-127.md), the applicable rootless qualification of
[decision 121](../adr/decision-121.md),
[private verifier/reconciliation](../adr/decision-115.md),
[offline verification](../adr/offline-verification.md),
[server](../server.md), [security](../security.md),
[containers](../containers.md),
[deployment](../deployment-centos-stream-10.md),
[release](../agents/release.md), [environment](../agents/environment.md) and
the [invariant register](../invariants.md) where affected. Review INV-002/003/
005–007/010–016, AD-16/17/21 and FS/TX preservation. Keep native activation,
whole-archive credentials, exact receipt/result schemas, no-resume semantics,
NAS barriers and unchanged domain algorithms explicit. No dependency or durable
format change is intended; the format drill verifies that conclusion.

## Tasks

| Order | Work package and task file | Depends on |
| --- | --- | --- |
| 1 | [OPS-017: Implement the confined worker-owned listener](tasks/ops-017-container-worker-listener.md) | [REL-011](tasks/rel-011-local-release-and-handoff.md), committed |
| 2 | [OPS-019: Implement minimal viable UBI 10 service images](tasks/ops-019-ubi10-runtime-images.md) | OPS-017 |
| 3 | [REL-013: Build clean 0.2.1 artifacts and prove container peer access](tasks/rel-013-container-worker-artifacts.md) | OPS-019 |
| 4 | [OPS-018: Deploy and accept the corrected listener locally](tasks/ops-018-container-worker-rollout.md) | REL-013 |
| 5 | [REL-014: Record the corrected local release and handoff](tasks/rel-014-container-worker-release.md) | OPS-018 |

Task files own execution status; this table declares prerequisite order only.
Finish and commit one work package before beginning the next. Collaborating
agents may own separate files within the selected task, with one documentation
owner and coordinated source freeze before its gate.

## Acceptance and validation

- Both explicit worker startup modes pass real-process tests. Rootless mode
  owns its listener under the actual confined process context; native named FD3
  mode retains its strict identity and descriptor checks. No malformed
  environment, extra descriptor, unsafe path, stale socket or concurrent worker
  gains startup or cleanup authority.
- Disposable fixtures prove all verification modes, exact result/restart
  reconciliation, no replay, dropped observer safety and joined shutdown using
  the unchanged private protocol and guarded commands. Socket replacement and
  crash evidence remain intact. Actual API-container-to-worker-container
  framed PROBE passes under SELinux Enforcing; host-only access is insufficient.
- Actual new-image fixtures prove PID1/internal FD3, denied IPv4/IPv6 creation,
  offline flags, no secrets/credential access, empty capabilities, read-only
  roots, cgroup limits, shared lock contention and graceful drain. Keep failed
  attempts distinct from final proof, without weakening assertions or policy.
- Clean wheel/sdist/image/closure/base/source identities and the immutable
  selected profile/index are recorded. Existing archive/receipt/observer formats
  pass predecessor/current compatibility or preserve/refuse honestly.
- The guarded local switch preserves the permanent host guard and all NAS-ro,
  writer-mask, state, secret and lock barriers. Only non-executing private PROBE,
  TLS/HTTP authentication/metadata-free readiness, MCP initialize/tools-list,
  isolation and clean lifecycle checks run against production containers.
  Live NAS workload/full verification remains NOT RUN.
- Every work package passes the required `scripts/check.sh --with-build` gate
  and records its actual exit. On this writer host, the gate's kernel namespace
  must hide the live NAS path, including collection; marker deselection alone
  does not establish protection. Draft record/link/whitespace checks are not
  implementation, artifact or installed acceptance.
- Local annotated release/tag and operator handoff identify exactly what ran,
  its source/image and actual container-peer acceptance, plus all remaining NAS,
  calendar and other-host holds. No remote publication occurs.

## Lifecycle and amendments

- 2026-10-18: Draft created while REL-011 remains the sole active task. Root's
  continuing authorized rollout scope includes the necessary connectivity fix;
  activation waits for REL-011 to complete and commit. No current selector,
  architectural contract, source, version, image or host is changed by this draft.

- 2026-10-18: Activated after REL-011 commit 2d81df5 and local main fast-forward
  edef480→2d81df5; root returned to feat/rest-api-and-mcp. The completed 0.2.0
  partial release/tag remains immutable history. OPS-017 is the sole task in
  progress; publish decision 128/contracts before source edits. This correction
  is necessary to the continuing authorized local rollout, not permission to
  execute unrelated operator backlog or any NAS workload.

- 2026-10-18: Decision 128 and governing contract amendments are published before
  source implementation. Explicit --container-listener reserves owned unbound FD3
  only after the inheritance audit, before NSS/shared imports, then binds under
  instance/pinned-parent ownership. Real owned-mode READY requires completed
  initialization and no pending stop. Source owners may implement within OPS-017;
  installed 0.2.0/hold 22 and all NAS/host boundaries remain unchanged.

- 2026-10-18: OPS-017 completed source 0.2.1 with unchanged dependency records,
  native activation and all confinement/domain/durable-format boundaries.
  Source tests and explicitly dirty preview prove secure owned listener,
  real notify/container-origin peer/isolation and exact cleanup; the failed
  startup-stop regression and superseded untested preview remain task evidence.
  Actual NAS-masked --with-build exits 0: 3,912 Python tests/40 deselected in
  487.56 seconds, three locked installation profiles, 135 Cockpit tests/build
  and four wheel smokes. REL-013 is next pending until this source commit;
  deployed 0.2.0/hold 22 and all NAS/other-host restrictions remain unchanged.

- 2026-10-18: REL-013 activated after source commit 03a986f. Root creates the
  clean detached source at /var/tmp/hfcache-rel013-source; final artifacts,
  contexts and proof outputs remain outside it, with evidence edits separate.
  Normal ignored gate outputs may be inside while tracked state stays clean.
  Only reviewed delegated clean-build/compatibility/disposable proof work starts;
  OPS-018 remains pending and deployed 0.2.0/hold 22/NAS guards stay unchanged.

- 2026-10-18 UBI steering: Tyler requires every built service image to use Red
  Hat UBI 10, with the most minimal viable variant. New OPS-019 is sole
  in_progress; decision 129/contracts follow technical review before source.
  REL-013 returns pending and now depends on OPS-019. Its initial clean Debian
  build/proof/compatibility evidence is superseded; root stops its gate with
  TERM15 after 4m25.945s, not passing despite wrapper exit0. Domain execution is
  held. Version remains pre-release 0.2.1; production 0.2.0/hold22/NAS barriers
  remain unchanged. Fresh clean UBI artifacts/acceptance follow OPS-019's commit.

- 2026-10-18: Technical review selects decision 129: every FROM stage uses pinned
  UBI micro; actual tools suffice without package transactions. Minimal is only
  a Red Hat CA-PEM data donor, and pinned uv/Caddy images only binary donors.
  Portable verified CPython 3.14.6/locked app versions and all confinement remain.
  The ADR/index/register/contracts are published before source authorization;
  OPS-019 may implement. No stopped/superseded candidate is promoted or deployed.

- 2026-10-18: OPS-019 completes all-micro app/Caddy source with unchanged locked
  dependency versions and confinement/domain/schema boundaries. Exact installer
  omission and supported caio fallback corrections retain failed foundation
  evidence. Dirty UBI foundation/notify/container-peer/isolation/TLS proofs pass;
  the fresh NAS-masked --with-build exits 0 with 4,057 Python/40 deselected,
  three locked profiles, 135 Cockpit tests/build and four wheel smokes. REL-013
  is next pending until this commit and must repeat clean UBI acceptance.
  Production 0.2.0/hold22/NAS/guard/writer-mask/state/remote barriers remain.
