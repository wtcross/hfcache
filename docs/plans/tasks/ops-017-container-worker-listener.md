# OPS-017: Implement the confined worker-owned listener

| Field | Value |
| --- | --- |
| Work package | `OPS-017` |
| Status | completed |
| Plan | [Container worker listener](../2026-10-18-plan-container-worker-listener.md) |
| Depends on | [REL-011](rel-011-local-release-and-handoff.md), committed |
| Scope | Source, contracts and disposable tests only; no installed host or NAS action |

## Scope and acceptance

1. Publish the listener-at-creation architectural contract before source edits.
   Add the explicit rootless flag to the existing worker bootstrap, creating the
   protected listener inside the direct PID1 container and using internal FD3
   through the same verification runtime. Preserve strict native named-FD3
   activation, cold imports, startup-only offline initialization, rejected
   credential environment and unexplained inherited-descriptor refusal before
   NSS/shared imports. Rootless mode requires no inherited descriptor above
   stderr and no LISTEN_* activation fields before creating its own resources.
2. Hold the existing worker instance lock across private listener creation,
   runtime, joined drain and owned socket cleanup. Use a pinned no-follow
   protected euid/egid-owned mode-0700 parent, restrictive bind, mode 0600 and
   exact created inode proof.
   Existing/stale sockets and all other pre-existing paths refuse and remain;
   replacements survive cleanup. Neither instance nor archive lock is unlinked.
3. Change only worker private-directory access to writable. Keep API access
   read-only and all existing secret/network/seccomp/capability/root/cgroup
   constraints. Start worker.service with the rootless target and order API
   after it with Requires+After. Use worker Type=notify/NotifyAccess=all and
   --sdnotify=container; the direct worker sends AF_UNIX READY=1 only after
   secure listener, instance lock, store and VerificationWorker initialization
   succeed. No sleep or conmon-start notification substitutes for readiness.
   Remove worker Requires/Sockets and all target/API automatic .socket
   references; retain the indexed .socket artifact as dormant
   RefuseManualStart=yes so the nine-binding/index contract need not change.
   Preserve native-profile socket activation and infinite non-killing drain.
4. Preserve private frames, peer UID, operation/result identity, reconciliation,
   no replay, storage preflight and complete lock/persistence behavior. No Hub,
   API credential, in-process execution fallback or domain algorithm change.
5. Select application metadata 0.2.1 and update only its project lock record;
   dependencies remain unchanged. Update release notes/contracts/evidence with
   the distinction between source tests and later clean-image/installed proof.

## Contracts, invariants, and ADRs

The parent plan identifies the governing contracts. Review decisions
[115](../../adr/decision-115.md), [121](../../adr/decision-121.md),
[126](../../adr/decision-126.md), [127](../../adr/decision-127.md), offline
verification, INV-002/003/005–007/010–016, AD-16/17/21 and FS/TX preservation.
Create the next unused decision (128 at drafting), amend affected records and
the register in this work package. Keep the native-profile exception explicit.
No dependency or durable format change is intended.

## Validation

Planned, not execution evidence: actual entrypoint subprocess tests for both
modes; unsafe/stale/symlink/extra-FD/environment refusal; concurrent instance
exclusion; socket inode substitution and retained crash state; clean stop,
restart and active-work join; existing private protocol/service tests; rendered
unit/helper/installer-binding contracts; metadata-only lock change check;
record/link/whitespace audits and the NAS-masked full `scripts/check.sh --with-build`.
Actual container SELinux proof belongs to REL-013, not these source checks.

## Execution notes and handoff

Activated after REL-011 committed as 2d81df5 and root selected the parent plan. Collaborating source/test/docs owners share this single
task boundary; freeze before the gate. The internal FD3 setup must not make its
own pinned parent look like an unexplained inherited descriptor, and a proc-fd
bind spelling must not silently bypass exact listener/path validation.

The contract-first [decision 128](../../adr/decision-128.md) is published with
its index/progress entry and amendments to native/rootless isolation, lifecycle
and rollout contracts. The explicit flag is --container-listener, PID1-only;
native activation stays the default strict mode. The stdlib-only helper
module verification_listener and its local tests cannot substitute for later
clean-image/installed proof. Contract publication claimed no execution result;
actual source and dirty-preview evidence follows below.
Reserve owned unbound FD3 immediately after the no-inheritance audit, before
NSS/shared imports; bind later under instance/parent ownership. Owned mode alone
requires valid NOTIFY_SOCKET and suppresses READY after a pending stop request.
Owned SIGTERM/SIGINT handlers now follow the cold audit immediately, before FD3
reservation/NSS/imports, with one stop Event through runtime. A deterministic
real-process fixture exposed stop-during-initialization becoming late READY;
the corrected three stop/initialization cases pass in 2.54 seconds. Its PID1
precondition is explicitly simulated, not actual container PID1 proof. Native
handler placement is unchanged; the final owner suite is recorded below.
The contract-first path refinement requires lexical socket/archive-root
disjointness plus bounded fixed /proc/self/mountinfo proof of a local parent
filesystem before traversal/bind. Unknown/network evidence refuses without
realpath, NAS stat or directory access; native inherited behavior is unchanged.

Root updates pyproject/uv.lock metadata 0.2.0→0.2.1. Parsed lock comparison
confirms all 93 nonproject records are identical and only the project version
changes; locked check and server+MCP sync exit 0, installing editable 0.2.1.
A preparatory build-helper --help first uses system Python 3.12 and refuses the
existing PEP-758 syntax before any build/mutation. The corrected
`rtk uv run --locked python scripts/build-container.py --help` uses project
Python 3.14 and passes. Build tooling is not one of the fixed stdlib-only host
controls required to run on 3.12; no compatibility/source defect is claimed.

Runtime/proof focused checks pass:
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_container_service.py tests/unit/test_container_runtime.py tests/unit/test_systemd_units.py tests/unit/test_container_release_installer.py -q`
reports 197 passed in 10.56 seconds, with scoped Ruff clean and earlier whole
Pyrefly 0. The harness requires actual notify/all manager readiness and
MainPID==ConmonPid, a separate ordinary-container API peer over read-only socket
directory and a separate direct-PID1 isolation companion. It cannot infer PID1
seccomp from podman exec. Validated exact-ID drain retains containers; actual
clean-image acceptance and installed protected-helper/target drain remain later
task evidence. This focused selection alone claims no actual container success.

The API-role peer fixture is an ordinary container_t process using the exact app
image/UID mapping and read-only private directory for fixed VerificationClient
PROBE; it is not an HTTP server or admission. A separate direct-PID1 companion
tests seccomp, distinct from actual worker metadata/notify attribution. No podman
exec result substitutes for PID1 filter proof or installed API acceptance.

Root's first dirty preview is superseded without any container proof run:
image sha256:95889edd26969a889dc6b4e60558b5cbcea706c651936e1ae7cc5bf5f179cfde,
wheel SHA256 944d0dac9bd41d7419fa9b64d4d0afdd4f50e815f8598055d4b8f6d47871fc9d.
The deterministic startup-stop correction required a new preview; neither
working-tree artifact is a clean release. Corrected preview/proof and final gate
evidence follow.

Preview 2 is actually built from dirty source 2d81df5, not a release:
wheel SHA256 b6267b56dfb714b1165909b10a3be0ce26d2f1475e6311ff6e5d928cac0b798a,
image sha256:7293dd14c5844f1de49b73f20d8b5ab43d325de5b52b6c23491f1b8ac0d59128,
record .scratch/ops-017-preview2-image/build.json. The locked closure is unchanged.
At this checkpoint actual fixture results were pending. The full NAS-masked
--with-build gate runs in .scratch/ops-017-gate.log, unit hfcache-ops017-gate, invocation
42ab771951b943619cadcbc746a843e6; initial 415-file format and lint stages pass.
These initial stages alone establish no final process exit or production success.

Application source/tests are frozen and released. Exact final selection:
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_verification_worker_bootstrap.py tests/unit/test_verification_listener.py tests/unit/test_verification_executor.py tests/unit/test_execution_adversarial.py -q -x`
exits 0 with 162 passed in 30.18 seconds (49 bootstrap, 42 owned listener/kernel,
45 private executor, 26 adversarial), log .scratch/ops-017-worker-python-final.log.
It includes actual kernel ownership/locality/notification/FD3 proofs, real child
bootstrap with explicitly simulated namespace PID1 precondition plus true non-PID1
refusal, all three guarded verification modes on local fake-NFS fixtures with
Hub/credential tripwires, and active-thread joined socket/store/instance lifetime.
The early-NSS stop regression is retained as one failing case in 1.01 seconds,
then three corrected cases in 2.54 seconds. Five owned files format/Ruff clean,
whole Pyrefly 0 and whitespace pass. Actual confined PID1/proxy/SELinux proof
remains separate from these source fixtures; final gate evidence follows below.

The final app log SHA256 is
2e8f0f23aae268360a8cee5457a3a0a9795bfaf6ce8945a772a5bc31b477b937.

### Actual dirty-preview confinement proof

Preview 2's actual fixture exits 0 at /var/tmp/hfcache-ops017-preview2-1;
proof.json SHA256 9d67f9f47c538c6d906c18dcbfc25cfbe8c4eefa67870183d927c381c39eb115.
The real user notify/all unit hfcache-proof-62d10dcbadbb0a94-worker.service is
active/running with MainPID 750968 equal to ConmonPid; readiness entry follows
main start. A separate ordinary container_t API-role peer passes framed PROBE
under Enforcing SELinux with expected UID 981. Actual worker PID1/internal FD3,
CapEff 0, NoNewPrivileges and Seccomp 2 pass. The separate direct-PID1 companion
denies IPv4/IPv6 with errno 38 and proves masks/offline/read-only root/private
namespaces/fixture-lock contention; protected-file reader proof is separate.

Validated exact-ID direct drain exits 0 and the unit finishes naturally; it is
not installed manager/target/protected-helper drain. All four containers are
retained stopped/exit 0, own socket inode 70750692 is removed, runtime directory
is empty and worker store contains only its retained .lock. Worker log is empty.
The image is exact dirty preview 7293dd14… and policy is 08f97ffb… from the
recorded builds, with no NAS bind/job. This source-design proof does not make
dirty artifacts deployable, certify clean REL-013 artifacts or close installed
worker hold 22; OPS-018 actual API-container PROBE remains required.

## Completion evidence

Completed 2026-10-18. Explicit --container-listener, stdlib ownership/locality/
notification helpers, paired trusted listener validation, native-mode preservation,
rootless notify/service ordering/RW-RO mounts and dormant socket/index bindings
implement decision 128. Metadata is 0.2.1; all 93 nonproject lock records remain
unchanged. The source/fixture, failed early-stop regression/correction and actual
dirty-preview outcomes above remain distinct from future clean/installed proof.

Actual NAS-masked `scripts/check.sh --with-build` exits 0, invocation
42ab771951b943619cadcbc746a843e6, unit elapsed 9m1.567s: 415 formatted/Ruff clean,
whole Pyrefly 0 (11 suppressed, 60 warnings not shown), 3,912 Python passed/
40 deselected in 487.56 seconds; 0.2.1 builds and all three locked isolated wheel
profiles; Cockpit lint/style/types, 135 tests in 2,324.192292 ms/build 1,385 ms;
four extra wheel smokes in 5.42 seconds. Log .scratch/ops-017-gate.log SHA256
b3c81f81bfdc736d907cafdd8212228d0bba189fe57becfc663aadcbce58054a.

Reviewed INV-002/003/005–007/010–016, AD-16/17/21, FS/TX preservation and decisions
115/121/126/127/128/offline verification; governing contracts/index/register and
source/test links accompany implementation. No dependency, durable schema or
verification-domain algorithm changes. Completed [progress audit](../../progress.md)
and final links/records/whitespace checks accompany this package. REL-013 is next
pending until this source commit. Deployed/tagged 0.2.0 and hold 22 remain unchanged;
no installed host change, NAS file I/O/job, other-host action or remote publication.
