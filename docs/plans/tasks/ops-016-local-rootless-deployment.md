# OPS-016: Deploy the local runtime with read-only acceptance

| Field | Value |
| --- | --- |
| Work package | `OPS-016` |
| Status | completed |
| Plan | [2026-10-18-plan-local-rootless-rollout.md](../2026-10-18-plan-local-rootless-rollout.md) |
| Depends on | [REL-012](rel-012-clean-container-release-artifacts.md) |
| Scope | Local host only; no NAS content/metadata writes or other-host changes |

## Scope and acceptance

1. Recheck the committed guardrails, NAS read-only mount, paused/blocked writers and actual executor quiescence before host-local deployment. Preserve local backups and retain the noncreating shared lock across any runtime switch.
2. Root installs reviewed local account/user-manager/container/proxy/config/credential/unit changes and switches only to REL-012's clean-source identified staged artifacts. Provision the nine exact root-owned through-current bindings and real protected overlay placeholders under quiescence; reload both managers after selection and inspect actual FragmentPath/effective drop-ins for overrides before activation. Start the reviewed target so Caddy and API run rootless; verify the private worker and runtime client container boundaries.
3. Prove actual local TLS/Unix/proxy/auth/registry, no-IP/no-credential worker, rootless UID/cgroup/activation/drain and non-NAS writable paths using bounded local checks and disposable local fixtures. Do not test NAS write denial by attempting a NAS mutation.
4. Keep all sync work stopped and verify scheduling disabled; no archive init, sync, non-estimate verification, mutation/probing jobs, write-bearing NFS tests or real archive hardening workload. No ACME issuance, remote push, other-host trust/config changes or NAS administration.
5. Record actual deployed identity, every successful/failed/not-run check and guarded rollback constraints. Deployment is partial data-preserving acceptance, never a falsely green full storage rollout.

Actual acceptance is explicitly limited to metadata/proxy/runtime isolation and
drain. API-container-to-private-worker SELinux connectivity remains a release
hold; a host-origin peer probe is not end-to-end verification acceptance. No
policy allow, changed container label or execution bypass is authorized to close
that hold. A future reviewed label-at-creation/container-activation design needs
its own authorized task; the existing plan permits this honest partial rollout.

## Contracts, invariants, and ADRs

Decision 126 and OPS-015 architecture; INV-002/003/005–007/010–016, FS/TX preservation, environment/release/deployment rules, credential whole-archive scope and actual executor/observer separation.

Read the [invariant register](../../invariants.md), [ADR index](../../adr/README.md),
[environment](../../agents/environment.md), [release](../../agents/release.md),
[planning](../../agents/planning.md) and [workflow](../../agents/workflow.md).
Record actual review/amendments with completion evidence; preserve historical
records rather than silently rewriting their earlier authority.

## Validation

Planned, not execution evidence: `scripts/check.sh` (plus `--with-build` at
release/container boundaries), meaningful scope-specific tests and local
record/link/decision/whitespace audits. Host tests must preserve the absolute
NAS-write ban. Record forbidden storage checks as NOT RUN, never passing.
Only root performs privileged host mutations and never prints secret values.

## Execution notes and handoff

Activated after committed REL-012 (`7d27e86`). Install only the immutable staged
0.2.0 artifacts from clean source `481fcc4`; retain the read-only NAS mount,
legacy writer masks and noncreating original lock throughout the guarded switch.

The modest permanent boot-guard refinement amends decisions 126/127 before
implementation. Fixed host-only helper/system notify service, independent of
current, runs UID/GID 981 and holds the original noncreating lock after strict
metadata/path identity checks. READY requires actual host NFS-ro evidence from
/proc/1/mountinfo. It checks once before readiness, not continuously. A protected
bridge Requires/After drop-in and no user-default app-target enablement enforce
the normal start order; boot tmpfiles creates locks without truncation and
0700 runtime directories. Root alone transfers old guard→installer→new guard
under continuous NAS-ro/writer masks/quiescence before application startup.
Application/immutable release artifacts remain clean-source 481fcc4; new fixed
host policy is deliberately separate so app rollback cannot remove the barrier.

Root's actual hfcache-ops016-host-mountinfo-proof probe exits 0 in 85 ms,
invocation fd47431b1a6d4783be84db6f93346b21. UID/GID 981 with NoNewPrivileges,
ProtectSystem=strict, ProtectHome, PrivateTmp/PrivateNetwork, AF_UNIX and empty
capabilities can read host /proc/1/mountinfo and distinguish host root rw from
private self root ro. This proves the source/view boundary without relaxing
hardening or reading NAS files; it is not application readiness/deployment proof.

Host-policy source is released: scripts/hold-readonly-guard.py,
packaging/containers/hfcache-readonly-guard.service and hfcache-rootless.conf,
with tests/unit/test_readonly_guard.py. The exact focused command
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_readonly_guard.py -q`
passes 35 cases in 0.48 seconds; Ruff/format, whole Pyrefly 0 and whitespace pass.
Actual system-Python notification/flock/clean-stop, host-rw no-READY and idempotent
nontruncating tmpfiles cases execute only owned fixtures. The tmpfiles test uses
a disposable root and current test UID/GID, not host installation or NAS. Root
owns actual fixed-file installation, service/bridge readiness and holder transfer.

### Initial host bootstrap (before activation)

Root's UID-981 account/rootless engine check passes, with no actual hfcache app
units or containers running. Exact app/Caddy OCI archives load into that service
engine and inspect as the expected AMD64 image IDs. Root reuses the active
encrypted hf-token and existing Cockpit TLS material, creates three distinct
host-key-encrypted API-class sources and provisions six fixed Podman secrets.
No secret value is printed or ad hoc plaintext credential file created.

Two precheck corrections are retained: a loose unit substring matched mount
description text and was replaced with exact unit-name-prefix matching; an empty
secret-list --format=json result failed parsing before secret creation and was
replaced with explicit name-template output. Neither proves an app was active
or authorizes overwriting unknown state. Fixed guard/boot files, nine bindings,
local SELinux labels and Cockpit binding are being installed under root control;
the old guard still owns the original lock and current still selects native.
The NAS-masked full gate is running, invocation
49ab5b67f73d44f6ab367e86b6d7aaf5. No application readiness or completion is claimed.

### Guarded selection and bridge correction (not readiness)

The actual guarded installer switch exits 0 and current selects releases/0.2.0.
The new readonly guard is READY, PID 717169, invocation
3b2b8f079b824ce3a16ce80fd9259b06, retaining original device 27/inode 2273;
independent exclusive-lock contention proves ownership. No application has
started. Seven effective system/user bindings resolve through current without
unexpected overrides, and both syntax reviews exit 0.

The first live-XDG user syntax check replaced the manager private socket: DBus
remained responsive but systemctl refused. Root verified no containers, restarted
the idle user@981 manager and restored its socket. Future syntax review must use
a disposable runtime directory. Initial bridge startup then refused because
ProtectHome=yes hides /run/user; retain the failed attempt. A hardened actual
probe succeeds with only the fixed private socket bound at
/run/hfcache/user-manager/systemd/private and bridge-only XDG_RUNTIME_DIR pointing
to /run/hfcache/user-manager. Existing hardening stays unchanged. The host drop-in
and two protected tmpfiles directories implement that narrow alias outside the
immutable 481fcc4 artifacts; actual target/API readiness still awaits it.

The released host template is
packaging/containers/hfcache-readonly-bridge.conf.in; it adds only guard ordering,
the bridge-specific XDG alias and read-only private-socket bind. The final same
focused guard command passes 35 tests in 0.98 seconds, including actual fixture
tmpfiles creation of all five protected directories and preservation of the held
lock. Ruff/format, whole Pyrefly 0 and whitespace pass. These are source/fixture
checks, not a host activation result.

Local label review also found the first matching rule omitted hfcache.target.
Root adds the exact local rule and uses restorecon -F for the known customizable
container_file_t label that normal restorecon skipped. SELinux remains Enforcing;
no NAS label or content is touched and no permissive/label-disable fallback is used.

### Actual partial runtime readiness

The system bridge is active, invocation fed1a06d63734927881a17dd97298957, with
rootless Caddy/API and listener 0.0.0.0:8443. Verified local TLS uses FQDN SNI and
the existing Cockpit trust material. The corrected HTTPS probe passes all 13
checks, including version 0.2.0 and the exact nine MCP tools; its record is
/var/lib/hfcache/container-home/rollout-acceptance-corrected.json. Initialize
negotiates 2025-11-25 from the SDK's supported HANDSHAKE_PROTOCOL_VERSIONS. The
initial equality assertion against modern LATEST was too strict; that probe
failure is preserved and required no application change.

An actual system transient client invocation 20d63f8b878e4c9ab623dd76c50256c2
returns exact schema-1 version --server, exit 0 in 2.889 seconds. Its first attempt
exits 126 because OCI could not reopen an empty root-owned credential placeholder
at mode 0700. Root changes only that empty host placeholder to 0755; the worker/
client in-container credential-store masks remain inaccessible mode 000.

Actual payloads run UID 981 in user-981 cgroups, with no effective capabilities,
NoNewPrivileges and read-only roots. API/worker memory.high is 4 GiB and Caddy's
is 512 MiB. The first metadata assertion expected literal CapDrop=ALL, although
the engine expanded that list; actual CapEff=0 proves the intended boundary.
The local firewall permits TCP 8443 in runtime and permanent configuration after
backup; no remote firewall, trust store or ACME changes occur.

The actual private worker proves PID1/named-FD3 activation, IPv4/IPv6 socket
denial errno 38, offline/no-credential masks and original-lock contention.
However, API-to-worker probe fails SELinux connectto with EACCES from container_t
to the user-manager-bound unconfined_t socket. This is an explicit unresolved
readiness hold, not a passed end-to-end verification check; exact AVC evidence is
retained. A reviewed activation/label design remains operator work. No NAS job,
archive scan, verification submission or write-bearing acceptance is run.

The first full NAS-masked gate passes 3,827 Python tests (40 deselected,
461.25 seconds), 135 Cockpit tests and four extra wheel smokes; elapsed unit time
is 8m32.899s. It precedes the final alias source freeze; final gate evidence follows.

### Final drain and partial acceptance

The checkpointed actual drain/restart ledger is
/opt/hfcache/deployment/20261018-rootless-0.2.0/actual-drain-restart.json.
Bridge stop takes 0.059 seconds; all three exact old role containers/PIDs are
gone without force while the system target and readonly guard remain active.
Original runtime lock inodes and both local-store lock bytes/inodes are preserved.
Restart creates new role IDs. The actual host standard-library UID-981 framed
FD3 worker probe returns available with peer UID 981/981; it does not prove the
blocked API-container SELinux connectto path. The first stop attempt returned 0
but its immediate disappearance assertion failed before a ledger; its cause was
not established. Later quiescence and the bounded checkpointed rerun pass. Both outcomes
are retained without claiming an unobserved first-run pass.

Final-host-state.json in the same protected directory passes: all 13 HTTPS checks
after restart, exact 0.2.0 indexed stage/nine bindings/source 481fcc4/image IDs,
enabled active system target, active bridge and original dev-27/inode-2273 guard.
NFS remains ro, SELinux Enforcing, all four legacy sync/verify units masked and
inactive, and local TCP 8443 is allowed in runtime/permanent firewall. The final
HTTPS record SHA256 is b081d5cb736ba16220961bf68b4618c89f52541610d3323af6bbe7ffd7dbceae;
probe script SHA256 is 81368dcb14b568059e56b9968b9ebf59593a2061963debb75362961d56c3bd08.
No NAS file I/O/job, remote action, ACME or tag occurs. API-to-worker SELinux
access remains unresolved and is carried explicitly into operator handoff.

The static guard also has an explicit independent boot binding, created with
`systemctl add-wants multi-user.target hfcache-readonly-guard.service`:
/etc/systemd/system/multi-user.target.wants/hfcache-readonly-guard.service is a
root-owned link to the fixed /etc/systemd/system unit, independent of current.
The final ledger records this binding. Podman's protected UID-981 file-driver
secret storage is engine-managed and is not claimed encrypted; no ad hoc
plaintext credential file was created. Earlier ledger wording is preserved in
service-secrets-before-wording-clarification.json with the corrected record beside it.

Protected ledger SHA256 values: final-host-state.json
44b074dcf3b785026b45ec59d7d69b1dbe980629683bb93a88f0e485c55baa94;
actual-drain-restart.json
a6e124bbeb15a86867b77d12a606aec9983423b13d1f3696711cee92ad869b31;
actual-runtime-isolation.json
2a7c3bc0f604053dfa6bd854733762ad6162a6de607f5723fe61f4345c81467d.

## Completion evidence

Completed 2026-10-18 under the partial acceptance above. The actual final
NAS-masked `scripts/check.sh --with-build` pipeline exits 0 after all host-policy
source freezes, invocation 71300b042f624b2a96dc1daeaaefdcea:
407 formatted files, Ruff clean, whole Pyrefly 0; 3,827 Python passed/40 deselected
in 471.22 seconds; 0.2.0 wheel/sdist and three locked isolated installation
profiles; Cockpit lint/style/types, 135 tests in 2,255.084017 ms/build 1,247 ms;
four extra wheel smokes/3,863 deselected in 5.34 seconds. Unit runtime 8m43.299s.
Log .scratch/ops-016-final-gate.log SHA256
34f6c22c1403486692f3ec896e4c8eb085d644fd1e593336ea0c9d98c0e151e6.
Earlier successful gate and all failed/corrected probes remain separate evidence.

Reviewed INV-002/003/005–007/010–016 and decisions 65/75/79/121/126/127;
amendments preserve the fixed boot guard, strict socket alias and actual worker
hold without a new app schema/dependency or weakened hardening. Application
artifacts remain clean-source 481fcc4; this package adds independent host policy.
The completed [progress audit](../../progress.md) and final record/link/whitespace
checks accompany this package. REL-011 is next pending until this commit. Live
NAS write/full-domain/NFS workload, other-host/calendar and end-to-end API worker
acceptance remain NOT RUN or failed/held, never passed by metadata readiness.
