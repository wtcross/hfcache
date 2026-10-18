# OPS-015: Package and test Caddy and the rootless runtime

| Field | Value |
| --- | --- |
| Work package | `OPS-015` |
| Status | completed |
| Plan | [2026-10-18-plan-local-rootless-rollout.md](../2026-10-18-plan-local-rootless-rollout.md) |
| Depends on | [OPS-014](ops-014-local-rollout-guardrails.md) |
| Scope | Local host only; no NAS content/metadata writes or other-host changes |

## Scope and acceptance

1. Settle and record the rootless architecture before source changes: explicit rootless user-manager systemd units plus a reviewed system target bridge, Caddy Unix upstream, one API app and a separate Network=none verifier with real inherited-FD activation.
2. Containerize runtime clients as well as executors; explicitly migrate or safely disable incompatible bare-host Cockpit/client paths. Reuse appropriate local TLS/Hub sources, keep API/MCP class separation and deliver no secrets or host credential stores to the worker.
3. Preserve peer UID/namespace mapping, common local flock and separate private durable stores; prove activation, concurrency, shutdown/drain, exact outcomes and retained-state compatibility with actual disposable containers where available.
4. Bind NAS only read-only, without chown/relabel/copyup options; keep graphroot, images, Caddy state and all writable paths local. Preserve SELinux enforcement and deny privileged/label-disable/host-Podman-socket shortcuts.
5. Package deterministic Caddy/config/image/rendered-unit validation and meaningful hermetic tests, current docs/examples and actual tool-version evidence. No production switch or release tag in this task.

## Contracts, invariants, and ADRs

INV-002/003/006/010–016, AD-17/21, FW-03/04, CP client/service boundaries; server/security/configuration/scheduling/activation/deployment contracts and decision 126. [Decision 127](../../../adr/decision-127.md) governs the actual architecture; amend affected predecessor records in this package.

Read the [invariant register](../../../invariants.md), [ADR index](../../../adr/README.md),
[environment](../../environment.md), [release](../../release.md),
[planning](../../planning.md) and [workflow](../../workflow.md).
Record actual review/amendments with completion evidence; preserve historical
records rather than silently rewriting their earlier authority.

## Validation

Required validation: `scripts/check.sh --with-build`, meaningful scope-specific
tests and local record/link/decision/whitespace audits. Actual results are below.
Host tests preserve the absolute
NAS-write ban. Record forbidden storage checks as NOT RUN, never passing.
Only root performs privileged host mutations and never prints secret values.

## Execution notes and handoff

Activated 2026-10-18 after OPS-014 committed as 28f9934. Git/current/dependency
records agreed; OPS-015 was the sole task in progress. Root owned units, runtime/
security helpers and protected installer; collaborators own image/closure/real
activation proof and Cockpit container bridge/tests. Markdown has one owner.
Source started after decision 127's contract-ready notice.

The initial Quadlet proposal is amended to explicit rootless USER systemd service
units. Generated forced cleanup/default short stop timeouts and replacement make
unknown surviving executors unsafe; explicit reviewed argv, non-killing drain and
refusal of unknown containers avoid those generator override assumptions. No
rootful fallback, init process, persistent-role auto-removal or force replacement
is acceptable. Only finite stateless observer clients may use --rm, as decision
127 specifies; accepted execution and its evidence remain server-owned.
Root may provision only necessary local service-account/home/subordinate IDs/
linger and disposable container proof infrastructure in this package. Actual
OPS-015 container proofs use owned local fixtures with no NAS bind, never a
production runtime switch. The OPS-014 host read-only mount, masks and held
original lock remain. Release version/artifact selection stays REL-010.

Decision 127 and affected server/security/Cockpit/deployment/release/invariant
amendments were published before source work; explicit contract-ready notice
released collaborators. Host ImportCredential is removed in the selected profile:
the fixed launcher mounts API-only Podman authority inside its client container.
Actual source/profile schemas and runtime evidence are synchronized below.

### Released Cockpit adapter evidence

The source owner released command.ts with fixed /usr/local/libexec/hfcache-client
and /run/hfcache/api/api.sock, outer systemd-run identity/UMask/MemoryHigh retained
and host ImportCredential removed. Candidate config flock and system-bus controls
remain unchanged. New container-client.test.ts has eight actual Node child-process
cases: exact terminal JSON at exit 0/10/20/30/40/50, progress/handles, option-shaped
data and missing-result/no retry. Updated command tests pass seven cases and
candidate guard nineteen; `rtk pnpm test` from cockpit/ passes the complete suite
of 135 in 3.08 seconds,
with types/ESLint/whitespace green. This is adapter/fixture evidence, not actual
container/secret/directory-bind or browser/production acceptance. Runtime/image
owners supplied that proof separately; at this stage the full --with-build gate
was still pending.

### Image and worker-proof development history

The exact builder interface is
`.venv/bin/python scripts/build-container.py --wheel <wheel> --wheel-sha256 <hex> --context <new-local-dir> --tag localhost/hfcache:<tag>`.
It authenticates the supplied wheel and hashed locked server+MCP closure, retains
inputs.json before build and adds final image identity in build.json. No uv,
editable source or dependency resolution is in the runtime. The first actual
fixture image built successfully as
sha256:9e0505de750a95272568dbc2161ac84d6c77c9911c8e0121d440a62176a0a2ca.
This identifies the tested working snapshot, not a release or production switch.

`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_container_runtime.py -q -x`
passes 32 hermetic cases in 0.44 seconds. The actual probe interface is
`.venv/bin/python scripts/check-container-worker.py --image sha256:<id> --workspace <new-short-local-dir> --seccomp-profile <derived-file>`.
It retains containers/logs/proof.json or fixed safe failure.json; this hermetic
proof is distinct from successful real container isolation.

Two early actual attempts remain preserved and safely stopped:

- /var/tmp/hfcache-ops015-worker, named hfcache-proof-ded657beae13ca19-worker,
  container 96d3a3da3e4a64a02ef4335bd87fa79f213999fb0406ecc3c002a14ae584a8ce:
  activated worker became available, but the harness rejected Podman's valid
  bare image-hash spelling. Root verified exact identity and stopped it using
  --time -1, exit 0. The reader now recognizes only exact bare/prefixed digest.
- /var/tmp/hfcache-ops015-worker-2, container 6143bc8cd0d3: activation/identity
  passed, then the isolation exec failed. failure.json records stage=isolation,
  class=CalledProcessError without raw exception/private input; root confirmed
  known stopped exit 0 and zero-byte worker log.

Both are retained, with no operation or NAS mount. At that point full isolation
still required labeled diagnostics and fresh actual proof.

Latest hermetic runtime command above passes 33 cases in 0.48 seconds, including
a fixed-check negative control for an IP-permitting policy. A third actual worker
attempt activated successfully but its labeled ip4_socket check proved IPv4 was
still permitted by the appended-ERRNO policy. Root confirmed graceful stopped
state and retained evidence. The installer owner is correcting allow-rule
composition to remove socket/socketcall from base ALLOW and permit only native
AF_UNIX, preserving other defaults/denies. Fresh actual isolation acceptance
was still pending; neither Network=none nor hermetic passes substitutes for it.

Root's first fixture wheel SHA-256 is
3014ac715344b525ad677b59524101967d6f4a58f3f7560d9db044008ba4d513;
image provenance is .scratch/ops-015-image-build, dirty working source based on
28f9934, not a release artifact. Immutable Python/uv/Caddy 2.11.7 bases were pulled
by the rootless login engine. A separate actual NAS-free API/Caddy/verified-TLS/
Podman-secret/container-client fixture had not passed at that point.
Source helper/probe/build exchanges force --remote=false. Actual payload
memory.high, credential-store masks and proc-only NFS-read-only startup guard
are required independent container boundaries.

Additional actual fixture findings preceded final corrected acceptance:

- API/Caddy attempt 1 lacked a fixture directory before startup. Attempt 2 API
  configuration rejected a duplicate localhost allowed-host entry; the fixture
  was corrected without changing the real FQDN policy.
- The immutable upstream Caddy binary carries cap_net_bind_service=ep. Under
  existing cap-drop ALL plus NoNewPrivileges it correctly failed exec with EPERM.
  Rather than weaken runtime hardening, root builds a derivative from the pinned
  upstream using Containerfile.caddy, strips that unnecessary file capability,
  asserts getcap is empty and runs UID 981; TLS 8443 needs no privileged-port cap.
  Its derived image identity and successful stack proof are recorded below.
- Worker attempt 4 hit crun EEXIST during the narrowed policy load, before isolation
  success. Root is examining native-only architecture mapping to match prior
  SystemCallArchitectures=native, without allowing more syscalls. All other base
  defaults/rules remain required; fresh corrected proof was still required.

### Protected installer source release

`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_container_release_installer.py -q`
passes 77 cases in 5.62 seconds; owned Ruff/format/whitespace and whole types are
green. Stable cases prove original noncreating flock held across atomic selection,
lock-path swap refusal/preservation and new-current preservation when parent fsync
fails after rename. Partial stage/unknown artifact evidence is retained rather
than cleaned. The ten-field release manifest and exhaustive independent index are
in schemas §16; stage fsyncs before rename and switch revalidates exact indexed and
recomputed bytes. Known autofs plus one read-only NFS mount is accepted without
archive file I/O; unexpected local overmount refuses. This is actual temporary-file/
hermetic boundary evidence, not a production switch or completed real isolation.
The final renderer de-duplicates allowed hosts in stable hostname/localhost/
127.0.0.1 order; actual strict server/client loader cases cover FQDN, localhost
and numeric loopback, preventing a valid local manifest from rendering an
unusable duplicate allowlist. This changes no authorization or public schema.

Worker attempt 5's remaining harness mismatch was accepting only narrower denial
errno values. A decisive PID1 control measured the corrected native-AF_UNIX policy
denying IPv4/IPv6 with retained defaultErrnoRet 38/ENOSYS; successful creation under
the old appended policy still fails its negative control. The harness now accepts
measured EPERM/EACCES/ENOSYS refusal and records the exact errno, never a successful
socket creation. Its focused suite passes 34 in 1.13 seconds; final actual proof
is distinct from that hermetic result.

### Actual local container acceptance

Root's sixth worker fixture exits 0 with the exact command:

```bash
rtk .venv/bin/python scripts/check-container-worker.py --image sha256:9e0505de750a95272568dbc2161ac84d6c77c9911c8e0121d440a62176a0a2ca --workspace /var/tmp/hfcache-ops015-worker-6 --seccomp-profile /home/tyler/Projects/hfcache/.scratch/ops-015-worker-seccomp-final.json
```

/var/tmp/hfcache-ops015-worker-6/proof.json proves real FD3/Python PID1/peer UID,
private PID/network namespaces, offline initialization, no credential environment,
unreadable masked credential stores, read-only image, the shared lock inode and
actual contention, IPv4/IPv6 socket refusal with errno 38, clean non-killing stop
and the same socket inode
69228458. Its operation store remains empty; no NAS bind or submit occurred.
This is rootless host UID 1000 mapped to container UID 981, not production
service-account/user-manager acceptance.
The separate protected-reader client fixture proves UID 981 can load its intended
protected token file; that credential is never delivered to the worker.
The decisive PID1 negative control permits both IP families under the original
policy, whereas the corrected native policy refuses both with Seccomp=2 and one
filter. Derived policy SHA-256:
08f97ffb4a6e9b48dcf95ec19fd41432b766b2a69c42fcc4e5991dd1d571c221.
Worker proof SHA-256:
a2c04cfde96796d57840628ab6baf26bba3ea878b9054b9c696533f2524cc920.

The rootless stack command `rtk .venv/bin/python .scratch/ops-015-stack-proof.py`
also exits 0. /var/tmp/hfcache-ops015-stack-6/proof.json covers the source's fixed
role commands adapted only for owned synthetic local paths/names/secrets and
loopback port 18443: verified fixture TLS through the derived Caddy image and API
Unix upstream, reader/writer refusals, REST/MCP cross-class 401, exact nine-tool
registry and API-only container CLI version exit 0. No NAS bind/file I/O or domain
operation occurs. An earlier raw MCP fixture incorrectly supplied a latest-version
header before initialization and received a classified 400; correcting negotiation
fixed the fixture without an application change. The derived Caddy image is
sha256:b6112cfbb3ea8dbbb41a9a7910301ecf548ccc9fde9455f5b386d76005459bc6.
Stack script SHA-256:
23ced6af0fa4dd943f310fec282d30da916473371122b5b9decfc527e0fcd590;
stack proof SHA-256:
de4218a2541fe24f34c0ed7f9af31a2a2b27c828dec5c13f69d5c08531f9e648.
These fixture images and working-tree bytes identify local proof, not the later
REL-010 release. Root confirms no fixture containers remain running; persistent
fixture containers are retained and finite observer-only clients may auto-remove.

Actual `systemd-analyze --user verify --man=no /var/tmp/hfcache-ops015-unit-review/user/*`
exits 0 silently with the fixture and /usr/lib/systemd/user unit paths. Only the
uninstalled helper executable path is substituted with the same executable repo
script. Separate system bridge/target verification also exits 0 silently with
fixture, /etc/systemd/system and /usr/lib/systemd/system unit paths. Logs are
.scratch/ops-015-user-units.log and .scratch/ops-015-system-units.log. This proves
rendered syntax/dependencies; installed-path and actual manager/target activation
remain OPS-016 acceptance.

### Full gate and final execution-metadata correction

The first --with-build gate selected 3,760 tests (40 deselected), reached 57%
without failure markers and was manually stopped for a concrete final review
correction. Podman does not implicitly forward the launcher's INVOCATION_ID; an
actual one-shot check returned false. The helper now forwards only a canonical
non-secret 32-lowercase-hex unit invocation ID to API/worker, never arbitrary
ambient environment. This preserves executing-process systemd metadata and log
framing; it does not attest timer or submitting-client origin. The new helper
regression selection passes 26 in 0.42 seconds.

The stopped run is retained in
.scratch/ops-015-gate-pre-metadata-review-stopped.log: service terminated by
SIGTERM 15 after 3 minutes 15.772 seconds. Its systemd Result=success is not a
completed gate pass and there is no final pytest total. The corrected full
--with-build gate in .scratch/ops-015-gate.log, invocation
eb0bbdc2b8304052910a8f0d3a410050, has confirmed pipeline exit 0 (session 95317).
It runs in the NAS-shadowed transient test namespace, clearing only test
INVOCATION_ID/SYSTEMD_EXEC_PID as in OPS-014. The payload
`rtk proxy bash scripts/check.sh --with-build` passes lock/both-extra sync,
404 formatted files, Ruff, whole Pyrefly 0 errors (11 suppressed, 59 warnings
not shown), 3,761 Python tests/40 deselected in 447.22 seconds, 0.1.10 sdist/wheel
and three actual locked base/server/server+MCP installation profiles. Cockpit
lint/style/types, 135 tests in 2.383 seconds and production build 1,172 ms pass;
the extra wheel subset passes 4 with 3,797 deselected in 5.12 seconds. Service
runtime is 8 minutes 18.000 seconds.

This is passing **pre-final-selector-review** evidence, not task completion.
The retained log is .scratch/ops-015-gate-pre-selector-review.log, SHA-256
e3b72f2c4d17dc37071f14e4c940daef9ef5ad7ba74697ddd903b597ceef1153.
Final review found that switching current alone may leave the runtime helper
using static profile/image paths. Actual release selection must govern the
executed immutable profile/images. The correction pins the physical release
resolved from the helper's own file, loads its rendered/runtime.json with a
no-follow final open and overlays that same rendered tree/client.toml after the
base policy bind; host worker policy/Caddy sources pin the same release. Exact
root-owned libexec/system/user-unit links through current are mandatory and drift
refuses, with provisioning/both-manager reload/effective FragmentPath/drop-in
checks left to OPS-016. The non-secret profile is staged root-owned 0644 with
no group/other writes and now rejects duplicate JSON keys.

The helper's 28 focused cases pass in 0.31 seconds, including a real two-release
symlink import that changes new helper/profile selection while the already loaded
helper stays pinned to its original tree. Ruff, whole types and actual host
Python 3.12 compilation pass. Root's new selected-overlay stack fixture command
`rtk .venv/bin/python .scratch/ops-015-stack-selector-proof.py` exits 0 with
graceful final drain and no running containers. Its local stack-7 proof has the
same fixed-outcome SHA-256 as stack-6, while the new script hash is
5e6d184b5889189b566b5a680d48bd2350cb781a6c2a5365c3d2923c679579a0.
These actual TLS/REST/MCP/client results prove the selected overlays rather than
the earlier static profile layout. The bridge now Requires the mount while its
system target only Wants the bridge; fresh rendered-unit verification and the
installer's two-release switch/rollback proofs are recorded separately. At this
point completion still required the corrected full --with-build gate. Root rechecked guard PID 653008,
read-only NAS and Enforcing SELinux. All proofs use local fixtures; no production
switch, NAS file I/O, live sync/full verification or forbidden storage acceptance ran.

### Selector correction source release and definitive gate

The installer owner releases the corrected source with
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_container_release_installer.py -q -x`:
106 passed in 10.94 seconds, scoped Ruff/format, whole Pyrefly 0 and whitespace
green. New cases prove all nine fixed bindings refuse missing/static/stale paths,
link ownership/parent protection and real temporary new→old→new selection under
the original noncreating lock. Helper, physical profile/image and unit paths
follow the same selected release while a previously loaded helper stays pinned.
Stable functions are test_every_fixed_entrypoint_binding_must_follow_current,
test_binding_link_owner_and_parent_are_protected and
test_two_release_switch_and_rollback_pin_helper_profile_and_units_together.
These are temporary installer fixtures, not installed-manager precedence proof.
Both-manager reload, effective FragmentPath/drop-in inspection and real protected
overlay placeholders remain explicit OPS-016 requirements. The new bridge's mount
dependency passes the repeated silent syntax/dependency verification.

The definitive NAS-masked --with-build gate ran as
hfcache-ops015-final-gate, invocation 15635df3a5434723a40661d350ca86e2, session
11424, in .scratch/ops-015-gate.log, with confirmed actual pipeline exit 0.
All source owners and semantic Markdown stayed frozen through this final run.
Lock/both-extra sync, 404 formatted files, Ruff and whole Pyrefly 0 pass;
3,792 Python tests pass with 40 deselected in 453.62 seconds. The 0.1.10 sdist/
wheel and three actual locked base/server/server+MCP installation/import/help/
version profiles pass. Cockpit lint/style/types, 135 tests in 2.213 seconds and
production build 1,178 ms pass; the extra wheel subset passes 4 with 3,828
deselected in 5.15 seconds. Service runtime is 8 minutes 24.015 seconds, success.
Final log SHA-256:
f9e3053fe7df71119fa5a9b0b105f902f3eaa98f8ddef0e6febeb1ab9da02e52.
The stopped run and pre-selector passing run remain separate preserved evidence.

The necessary release handoff also splits pending work into REL-010's reviewed
0.2.0 source commit and new REL-012's clean committed-source artifact build/
compatibility/staging/evidence commit. The API-only CLI and container deployment
break justify 0.2.0; no version changes in OPS-015. Working-tree previews are not
deployable artifacts, and OPS-016 now depends on REL-012. The unused ID and six-
task chain were checked; no pending task is activated here.

## Completion evidence

Completed 2026-10-18 in this work-package commit. Actual local worker/stack/
selected-overlay proofs, 106 installer/28 helper/34 build-probe focused cases,
rendered-unit verification, 135 Cockpit cases and the corrected required full
--with-build gate pass. Earlier real seccomp/activation/Caddy/fixture findings,
stopped gate and passing pre-selector gate remain recorded with their fixes and
scope; none is relabeled final acceptance. No new runtime dependency or archive/
service format, domain algorithm, release version, production switch or tag.

Reviewed INV-002/003/006/010–016, AD-16/17/21, FS/TX preservation, CP-01–14 and
decisions 111/121/122/126; decision 127 and affected contracts/predecessor ADRs,
schemas 15/16, invariant enforcement links, README/Unreleased/router agree.
The [progress audit](../../progress.md), six-task chain, current selector,
unique indexed decision 127, local links and whitespace are reconciled.
REL-010 is next pending until this commit. REL-012 owns clean-source artifact/
compatibility/staging evidence; OPS-016 owns actual service-account/manager/
effective-unit/target/secret/placeholder/TLS/firewall/SELinux deployment acceptance.
Preserve the OPS-014 guard/masks/read-only NAS and both stores/handles/lock inodes.
Live NAS reads/writes, sync/full verification/reports/catalogs, NFS-hardening,
other-host work, remote publication and ACME remain NOT RUN or forbidden; local
fixture/gate proof does not clear those holds.
