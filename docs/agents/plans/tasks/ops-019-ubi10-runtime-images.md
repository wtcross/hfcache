# OPS-019: Build service images on minimal viable UBI 10 bases

| Field | Value |
| --- | --- |
| Work package | `OPS-019` |
| Status | completed |
| Plan | [Container worker listener](../2026-10-18-plan-container-worker-listener.md) |
| Depends on | [OPS-017](ops-017-container-worker-listener.md), committed |
| Scope | Source/contracts and NAS-free local build/proof; no production switch |

## Authorization and scope

Tyler requires every built service image to use the Red Hat UBI 10 family from
registry.access.redhat.com/ubi10, choosing the most minimal viable variant.
This supersedes the initial Debian app/Alpine Caddy candidates. REL-013 returns
pending and builds fresh artifacts only after this source package commits.
Version remains pre-release 0.2.1; deployed/tagged 0.2.0 remains unchanged.

## Acceptance and validation

Publish reviewed decision 129/contracts before source implementation. Use pinned
UBI micro for ALL FROM stages; pinned minimal is only a Red Hat CA-PEM donor.
External uv/Caddy images are binary-only donors, never FROM stages or foreign
OS-library/CA sources. No package-manager transaction is needed; actual micro
contains required tools and is not shell-free.
Preserve exact Python/application dependencies, native/owned worker startup,
readiness, peer/secret/network/seccomp/SELinux/root/cgroup/drain/lock boundaries.
Record immutable base/interpreter/binary/CA/closure provenance and actual NAS-free
preview proofs, meaningful source/build tests and masked --with-build gate.
Previews are not clean release artifacts; REL-013 repeats all clean acceptance.

## Contracts and execution history

The following notes preserve the ordered review/build/proof attempts. Current
acceptance and remaining boundaries are stated in Completion evidence below.

Review [containers](../../../containers.md), [release](../../release.md),
[environment](../../environment.md), [security](../../../security.md),
[invariants](../../../invariants.md) INV-002/003/005–007/010–016, FW-03/04 and
decisions [126](../../../adr/decision-126.md), [127](../../../adr/decision-127.md),
[128](../../../adr/decision-128.md). Actual scan found OPS-019/decision129 unused.
Activated under new user steering after committed OPS-017. Reviewed
[decision 129](../../../adr/decision-129.md) publishes the accepted technical contract
before source implementation. Root alone owns privileged local actions. No NAS
file I/O/job/write, other-host change or remote publication; guard/hold22 remain.

Root explicitly prefetched only the pinned public micro/minimal images as the
login user, using an empty auth file rather than existing credential discovery.
Both pulls exit 0 and inspect linux/amd64: micro config ID
34f13727686218ace5c6965056e54b43ea6fb25ce1fac947ffa755507bc51452;
minimal config ID 5f0afad86767ed90c6a0dd76d2deede1e5c5dc23c9502a7f50b3fe13e5c9fbdc.
This is input preparation, not image execution, source implementation or host
service change. Decision 129's all-micro refinement follows actual included-tool
inspection; earlier minimal-tooling proposals are superseded, not implemented.

Fetcher source is released as scripts/fetch-container-python.py with explicit
--images-json packaging/containers/images.json --output NEW_LOCAL_FILE. It reads
the pinned python_distribution(version,url,sha256), permits no URL override or
extraction, bounds HTTPS/manual redirects/time/bytes, ignores ambient proxy/auth/
SSL_CERT_* and exclusively publishes only complete verified bytes; partials stay.
Its 45 hermetic cases pass in 0.50 seconds with scoped static checks clean.
Image/runtime proof is separate; the builder independently authenticates the
required --python-archive and safe extraction. No actual new image is claimed.

Caddy helper source/tests are frozen: scripts/build-caddy-container.py uses
--context NEW_LOCAL_DIR --tag localhost/hfcache:TAG and trusted fixed image pins.
`rtk proxy uv run --locked --extra server --extra mcp pytest -q tests/unit/test_caddy_container_build.py`
passes 40 cases in 0.47 seconds; scoped Ruff/format/targeted Pyrefly 0/whitespace
pass. Provenance includes exact source/base/donor/binary/CA/Containerfile inputs;
successful build adds image/version/empty-capabilities/retained-probe identity.
Finite UID981/no-network/caps0/NNP/read-only hash/getcap/version inspection starts
no server and retains named container/CID on any outcome. Tests include actual
GNU install/fresh-inode xattr removal and unknown/timeout refusal; no actual UBI
Caddy build or served-TLS success is claimed by these source tests.

Root's app Containerfile/shared build changes are frozen for preview. The focused
72 cases pass in 0.49 seconds with Ruff/format/types 0, covering strict all-micro/
donor recipe pins and bounded independently authenticated Python-only extraction
that refuses hardlinks/special files/escapes. This is not a full source freeze:
foundation-proof helper/tests are still in progress.

Actual reviewed fetch exits 0: .scratch/ops-019-python-fetch.json records
35,942,823 bytes at .scratch/ops-019-inputs/cpython-3.14.6.tar.gz, SHA256
86bf107f65fc30b56f2b263b26797fcbb1661f5315910cdbf27f733eb8738b74.
It uses verified host CA/TLS without ambient proxy/credential discovery.
The dirty preview wheel under .scratch/ops-019-preview-artifacts has SHA256
b064e478cd869b66196881d93399359dcc34152567c2c613ff14cdb31dd24ade.
App/Caddy builds are running in .scratch/ops-019-app-preview and
.scratch/ops-019-caddy-preview; no actual new-image success, protected stage or
production change is claimed. These working-tree builds are previews only.

Both actual dirty UBI builds exit 0, source 03a986f/source_dirty=true:

| Preview artifact | SHA256 identity |
| --- | --- |
| App image | bfae24fd02b3e9f0f9e2499911df8b0dd8a7eb5282d6e975d8fcc2c2217806ed |
| App recipe | d9a9d3e387192d9620f5e2f682b245fd28e8a84746c892d8cdbe6b878b502738 |
| Requirements | dc563a092ba88853d5282d95f240a9475d2ecbf7c238ae9790fd5c7b086f68c9 |
| Caddy image | fa2a5634a525af798ce6da2855d365f7cdf0f9a2d6d0eb56d461626e226acc10 |
| Caddy recipe | dda85b411f206cd7d42be05ccc8c354ee72303f27134ad9af73d966a76b05163 |
| Red Hat CA PEM | 00411c197b16f659945fba3c2f970a26030f56eef5d445c913cb59a089c813b9 |

The image IDs use sha256: in engine calls; build.json files under the two preview
directories retain all foundation inputs. Locked closure remains unchanged.
Caddy's finite retained probe exits 0 with binary hash/version 2.11.7, CA hash and
empty getcap verified. It is not a served-TLS test. Worker/foundation proof and
full gate are still pending; no preview is a clean release or production change.

Foundation helper source is frozen:
scripts/check-container-foundation.py --image EXACT_ID --workspace NEW_LOCAL_DIR
--images-json packaging/containers/images.json [--build-record PATH]. Combined
fetch/foundation tests pass 67 cases (45+22) in 0.89 seconds, log
.scratch/ops-019-input-foundation-tests.log, with scoped static checks clean.
The proof requires selected micro manifest→config ID→ordered RootFS diff-ID prefix,
not os-release alone, then bind-free/no-network/read-only/caps0/NNP actual PID1,
native imports/NSS/CA/SSL/glibc and retained stopped container evidence. Actual
execution/acceptance still awaits root review; source tests are not that proof.

## Review corrections and preserved attempts

Independent review catches/fixes a build-provenance race: hash the validated
recipe bytes actually copied, never a later source reread. The new injected-
source-change regression passes in the 73-case app selection (0.47 seconds),
with static checks clean. The preview recipe bytes/hash are unchanged and match
its context; clean builds must repeat from committed final source.

Actual dirty UBI worker proof exits 0 at /var/tmp/hfcache-ops019-worker/proof.json,
SHA256 aac8fbb3eebdb209e526a249b62ed428fcb94cafddf8d6cc9bbbd78e06275438.
Real notify/all PID 772852, ordinary container_t API-role PROBE under Enforcing,
worker PID1/FD3, separate PID1 companion IP denial errno38/masks/offline/RO/lock,
protected reader and exact drain pass. Own socket inode 204617737 is removed;
store retains only .lock. This is still dirty preview, not clean/installed proof.

Root stops the first OPS-019 gate for a concrete foundation-inspector mismatch:
it rejected intended fixed image SSL_CERT_FILE. Preserve log
.scratch/ops-019-gate-pre-foundation-env-review.log SHA256
9b8b09c27e29c6ddd7e02a659fb1283e7ba536aeb28b2d2acc7f112db41613b2,
invocation e5d9e395a004441498c4d4ae4fd29493, TERM15 after 52.956 seconds.
Wrapper exit0 is NOT a pass. The narrow correction accepts only the intended
public /etc/ssl/cert.pem path with verified CA bytes; it does not permit ambient
trust overrides or secrets. Actual foundation proof and fresh full gate await it.

Actual foundation attempt fails its no-runtime-package-manager check: retained
container e72fd6c… is stopped/exit 1, with stderr.log under
/var/tmp/hfcache-ops019-foundation. Read-only inspection identifies pip/pip3/
pip3.14 entrypoints in the official PBS input. This is a failed UBI preview,
not superseded Debian evidence or a passing foundation result. Root reviews a
narrow runtime-pruning correction; the proof is not weakened and no source/NAS/
production effect is attributed to this failed disposable run.

Contract-first runtime-pruning refinement follows actual pinned PBS inspection:
omit only bin/{pip,pip3,pip3.14}, lib/python3.14/site-packages/pip,
lib/python3.14/site-packages/pip-26.1.2.dist-info and lib/python3.14/ensurepip
(including bundled pip26.1.2) inside the UBI build layer before final COPY.
Original verified archive/extracted context remain unchanged; no wildcard or
system cleanup, app-dependency change or removal of domain stdlib functionality.
ADR129 publishes this before code. Strengthen PATH plus pip/ensurepip/uv module
absence proof; preserve failed bfae… preview and rebuild in fresh contexts.
No full gate is currently running and no new acceptance is yet claimed.

The strengthened fetch/foundation selection is frozen: 75 passed in 0.55 seconds
(45 fetch +30 foundation), scoped static checks clean. Foundation requires fixed
SSL_CERT_FILE=/etc/ssl/cert.pem, rejects SSL_CERT_DIR/credential/proxy overrides,
and checks both installer PATH and pip/ensurepip/uv module absence. Actual preview2
run remains pending; this is stronger source proof, not actual image acceptance.

Preview 2 app build actually exits 0 with exact known installer pruning:
image sha256:1be22257a7996a695e01d1ef3cd3f28290ee6c54d62b7b81a22d2db3b27ff6ad,
recipe SHA256 55af221b60a89c88e2d524e7602d428b3653f71bd623ce47fd8a6636289cc2a8,
record .scratch/ops-019-app-preview2/build.json. It retains dirty source 03a986f,
wheel b064…/PBS86bf…/unchanged closure; original context/archive stay intact.
All source is now frozen: combined app73/fetch45/foundation30/Caddy40 selection
passes 188 cases in 1.61 seconds. Actual Caddy base RootFS prefix proof is retained
at .scratch/ops-019-caddy-foundation.json, SHA256
a473e2979042bd4b58a1fb183ae37626762a63a3ddfca6c407612c41eb6ef5ef.
Actual foundation2/worker2/served-TLS stack remain pending, with a fresh full gate
after foundation acceptance. No clean release or installed result is claimed.

### Preview 2 worker and served-TLS proof

Both actual dirty preview-2 runtime proofs exit 0; they remain NAS-free fixture
acceptance, not clean artifacts or installed hold-22 closure:

| Evidence | SHA256 |
| --- | --- |
| /var/tmp/hfcache-ops019-worker2/proof.json | f1162916f3f5d9bb78c41c610d7ed9dec32800a53479f7af8f2b3203d8d00269 |
| /var/tmp/hfcache-ops019-stack/proof.json | 4a1e06ca59e48eb524756b02f3297db8c5350343a4ea0bbb5f4d8a0f569b0fe2 |
| .scratch/ops-019-stack-proof.py | 20f3664cce7490ba260602c731d75c57a03deb91d2b7cbbc3c15c9cbeba5fea6 |

Worker uses app1be222… and actual notify/all unit
hfcache-proof-9c0df40190c4e7a0-worker.service/MainPID777719. Enforcing API-role
container peer, worker PID1/FD3/caps0/NNP/seccomp, offline/masks/read-only root,
original fixture lock contention and protected reader pass; clean stop removes
its own socket inode2379377. Stack uses app1be222… + Caddyfa2a… on loopback19443:
verified synthetic-CA TLS/Unix REST, class denials, version0.2.1/OpenAPI, negotiated
MCP2025-11-25/exact nine tools and separate protected-reader CLI pass. State
snapshots stay unchanged with no jobs/NAS. All containers remain stopped/exit0;
six synthetic secrets are retained. Root reviewed the stack script before use.

Exact commands (fixture bus belongs to the login user, not the production UID):

```bash
rtk proxy env -u XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus /home/tyler/Projects/hfcache/.venv/bin/python scripts/check-container-worker.py --image sha256:1be22257a7996a695e01d1ef3cd3f28290ee6c54d62b7b81a22d2db3b27ff6ad --workspace /var/tmp/hfcache-ops019-worker2 --seccomp-profile /opt/hfcache/releases/0.2.0/rendered/worker-seccomp.json > .scratch/ops-019-worker2-harness.log 2>&1
rtk proxy env -u XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus /home/tyler/Projects/hfcache/.venv/bin/python .scratch/ops-019-stack-proof.py > .scratch/ops-019-stack-harness.log 2>&1
```

### Foundation-2 failure and supported-backend correction

Foundation2 retains stopped/exit1 container
402b05a9fb813b4ac4d3bbdcc20c134a4786eeba0acf23336970e19af767fef4 at
/var/tmp/hfcache-ops019-foundation2. Installer PATH/module absence, CA/NSS and
standard-library checks pass, but a forced optional caio.linux_uring import gets
ENOSYS under unchanged seccomp. Installed caio0.12.9 primary source catches that
ImportError and selects an available linux_aio/thread backend during its normal
import. This is an overstrict proof expectation, not an application failure.

ADR129/containers publish the narrow correction before the helper changes:
prove supported normal caio plus native linux_aio/thread imports, record the
preferred backend and unavailable io_uring, never set CAIO_IMPL or relax seccomp.
Only the proof process sets documented HF_XET_LOG_DEST=/dev/null to keep SDK
cache-fallback diagnostics out of its single JSON output. Image/application
environment and all other assertions remain unchanged. Preserve failed logs;
third-party advice to disable seccomp is not followed. Fresh foundation3 and
full gate remain pending.

### Final foundation-3 acceptance and semantic freeze

Actual foundation3 exits 0 for dirty preview2 app1be222…:
/var/tmp/hfcache-ops019-foundation3/proof.json SHA256
e5d6d06916552d854c24cb33c89a471e1d50861a564106b5cca46ff4354d9f2b;
capture .scratch/ops-019-foundation3-actual.log. Retained container f05902a4…
is stopped/exit0. Actual selected micro config34f137…/ordered RootFS diff-ID prefix,
RHEL10.2/Python3.14.6/glibc2.39/OpenSSL3.5.7, exact CA00411…/146 trusted CAs,
native/server imports, preferred caio.linux_aio/thread availability/io_uring
unavailability, UID981/NSS/PID1/read-only root/caps0/NNP/seccomp/masks and absent
installer entrypoints/modules all pass. No host bind, network or NAS is involved.
The two failed foundation attempts remain preserved rather than reclassified.

Final fetch45+foundation35 selection passes 80 cases in 0.59 seconds with scoped
static checks clean. All source/test owners release; semantic Markdown, concrete
enforcement links, 18-file record/link/dependency/current audit and whitespace
are ready for the fresh masked --with-build gate. OPS-019 remains in progress
until its actual exit0; no preview is promoted to clean release or production.

## Completion evidence

Completed 2026-10-18, OPS-019, this commit. All app/Caddy FROM stages use the
reviewed pinned UBI 10 micro foundation, authenticated portable Python and exact
binary/Red Hat CA donors. Exact known optional installer omission and supported
caio fallback keep immutable-runtime/confinement requirements intact. No
application/Python/dependency version, durable schema or domain algorithm changes.

Focused source evidence passes app73, Caddy40 and final fetch45/foundation35
cases, with static checks clean. Actual explicitly dirty preview2 foundation,
notify/container-origin worker/isolation/cleanup and Caddy TLS/REST/MCP/client
proofs pass with exact identities above. Preserve superseded Debian candidates,
failed UBI foundations, the stopped gate and provenance-review correction;
none is silently reclassified as passing or clean.

Fresh full NAS-masked `scripts/check.sh --with-build` actually exits 0, invocation
1572f480adc64beca8cfdd97a45d7528, elapsed 8m39.845s:

- 423 files formatted; Ruff/lint and whole-project types 0 errors;
- 4,057 Python passed, 40 deselected in 469.08 seconds;
- 0.2.1 wheel/sdist and actual locked base/server/server+MCP installation profiles;
- Cockpit lint/style/types, 135 tests in 2,222.516944ms and build 1,168ms;
- four additional wheel smokes in 5.47 seconds.

Log .scratch/ops-019-gate.log SHA256
e7d9e83c896271856f4b03803e8a3b6eb8fbd052a7106a70978c0ce31d2de980.
Reviewed INV-002/003/005–007/010–016, FW-03/04, AD-16/17/21, FS/TX and decisions
126/127/128/129; area contracts/index/register/source/test links and completed
[progress audit](../../progress.md) reconcile. Final record/link/dependency/current
and whitespace checks pass.

REL-013 is next pending until this source commit, then must rebuild both clean
UBI images and repeat all clean acceptance. No dirty preview is deployed or
tagged; production 0.2.0/hold22, original guard/locks/NAS-ro/writer masks/stores/
handles and all forbidden NAS I/O/jobs, other-host and remote actions remain.
