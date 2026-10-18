# Decision 129 — Build all service image stages on pinned UBI 10 micro

- Status: Accepted and implemented in OPS-019, with actual dirty UBI preview
  foundation/worker/TLS proof and the full gate passing. REL-013 records fresh
  clean artifact acceptance and OPS-018 records actual installed UBI runtime/peer/
  lifecycle acceptance. Live NAS workloads and other-host acceptance remain unrun.
- Date: 2026-10-18.
- Work package: OPS-019, this commit.
- Source: [progress decision 129](../agents/progress.md#decisions),
  [UBI steering amendment](../agents/plans/2026-10-18-plan-container-worker-listener.md),
  [task](../agents/plans/tasks/ops-019-ubi10-runtime-images.md).

## Context and choice

Tyler requires the Red Hat UBI 10 family for every built service image and the
most minimal viable variant per image. The initial REL-013 Debian candidate,
Alpine-derived Caddy and its genuine proof/compatibility results are superseded,
not UBI release acceptance. Its stopped gate is not passing. Deployed/tagged
0.2.0 stays unchanged until a later guarded rollout.

Use registry.access.redhat.com/ubi10/ubi-micro for **every FROM stage** in both
the shared API/worker/client image and Caddy build, including preparation stages.
Pin linux/amd64 manifest
sha256:87a27d7189dbae57f63db332a11de17f7ed6be91cdc956731c30141af2e8dc49
(observed 10.2-1791898871). Actual layer inspection finds bash, install,
sha256sum, stat, getcap and required glibc/libgcc; no package-manager transaction
is needed. Micro is not claimed shell-free. The host's required CPU features and
native wheel linkage are reviewed; this local artifact is not a portability
claim for another architecture/host.

Reject full/minimal runtime or tooling FROM stages when micro already suffices.
Minimal remains only a pinned Red Hat CA-data donor:
registry.access.redhat.com/ubi10/ubi-minimal@sha256:4f48c7a351edbe9cc13fc3c0ef2402340a96bb44df07cfa7efbc4f9f7b4b57fc
(10.2-1791891203). Copy only
/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem to /etc/ssl/cert.pem.
The runtime image intentionally sets fixed SSL_CERT_FILE=/etc/ssl/cert.pem;
this is a public trust-data path, not a credential or ambient override. Foundation
proof requires exactly that intended value and verifies its CA bytes. The host fetcher
still ignores ambient SSL_CERT_* inputs; these are separate trust boundaries.
Do not copy Debian/Alpine OS libraries, CA trees or filesystem defaults. If
actual tools prove insufficient, record a justified contract amendment before
introducing a less minimal stage; no silent base substitution.

## Interpreter and binary inputs

Keep Python 3.14.6 and all locked application dependency versions. Use the exact
official portable CPython build 20260718 artifact:
[cpython-3.14.6+20260718-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz](https://github.com/astral-sh/python-build-standalone/releases/download/20260718/cpython-3.14.6%2B20260718-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz),
SHA256 86bf107f65fc30b56f2b263b26797fcbb1661f5315910cdbf27f733eb8738b74.
Verify its hash and safe contained extraction before build. This interpreter
distribution and its bundled runtime are explicit provenance inputs, not a
foreign service root filesystem. Native runtime linkage must pass on micro.

### Exact optional-installer pruning

Actual pinned PBS inspection identifies optional installer content. Omit only
these exact paths relative to the portable runtime prefix, inside the UBI build
layer before final COPY:

- bin/pip, bin/pip3, bin/pip3.14;
- lib/python3.14/site-packages/pip;
- lib/python3.14/site-packages/pip-26.1.2.dist-info;
- lib/python3.14/ensurepip, including its bundled pip 26.1.2 wheel.

Preserve the original verified archive and extracted build-context input. No
wildcard/system-wide cleanup, application dependency change or removal of
domain-required standard-library functionality is allowed. The recipe records
this precise immutable-runtime reduction. Foundation proof must require both
PATH executable absence and Python-module absence for pip/ensurepip/uv; do not
weaken the failed check. uv remains build-only. Unknown future installer content
requires review rather than a broader deletion rule.

The existing pinned uv donor
ghcr.io/astral-sh/uv@sha256:0d127b3a7049b879a6e18a79c7f33fea59aa83c226464248f89cfb716a6b96f5
provides only its build-time executable via external COPY, never FROM or runtime
resolution. The pinned Caddy 2.11.7 donor
docker.io/library/caddy@sha256:173b26306d711395accaeba8b67afcaad2a085ccb1e6bf26010bfe8c095a5229
provides only its static executable. Verified binary SHA256:
678ade3bfc088749c81a681adc603333ee0bb023b6a6cfe3c0f58bef8ff854e9.
Install it into a fresh inode and require empty getcap output; never preserve
its unnecessary cap_net_bind_service xattr or relax NNP/cap-drop for TLS 8443.
These donor images contribute no FROM stage, OS libraries, CA data, environment,
entrypoint, account or other filesystem defaults.

Explicitly recreate reviewed ENV/entrypoint/user, local writable directories and
mask mountpoints on micro. Keep exact wheel plus hashed locked server+MCP closure,
fixed runtime paths and read-only source/root boundaries. Normal build/start uses
pull=never and no auto-update. A separate explicit host-only fetch/prefetch step
may obtain only pinned public inputs without application secrets; it grants no
remote push or unreviewed network input.

## Provenance, isolation and release boundary

Record source/dirty state, wheel/lock/closure, both UBI donor/base digests,
CPython URL/hash, CA source/hash and uv/Caddy donor/binary identities. Hashes and
actual runtime imports/linkage, not a tag or label alone, establish foundation
identity. Runtime profile/release manifest/index shapes and application durable
schemas stay unchanged; build provenance explicitly expands its foundation data.

Foundation proof exercises supported package imports under the retained seccomp
policy. caio normally catches an unavailable optional linux_uring backend and
selects linux_aio or its thread fallback. Prove the normal caio package and
linux_aio/thread native imports, record the preferred backend and io_uring
unavailability, and neither force linux_uring nor set CAIO_IMPL or relax seccomp.
The proof invocation alone may set HF_XET_LOG_DEST=/dev/null to prevent native
SDK diagnostics from corrupting its single JSON document. This is not an image
or application environment change; all CA, installer, NSS, caps and other
foundation assertions remain required. Preserve failed direct-backend attempts.

Preserve [128](decision-128.md)'s native/owned listener modes, actual READY,
peer/framing/cleanup, no-IP/Unix-only seccomp, no secrets/masks, empty caps/NNP,
read-only root/UID/cgroup limits, original lock and infinite non-killing drain.
No SELinux allow/label, host executor, privileged or control-socket shortcut.
Caddy retains verified TLS/Unix upstream without ACME/admin/file service.

OPS-019 may prove explicitly dirty NAS-free UBI previews. Only its committed
source can produce fresh REL-013 clean artifacts; repeat clean peer/notify/
isolation/domain/compatibility/staging/gate acceptance, preserving the simulated-
NFS domain distinction. OPS-018 alone can close installed worker hold 22; local
0.2.0 rollback restores its documented hold. No NAS file I/O/jobs/writes, other-
host change or remote publication. Source version remains pre-release 0.2.1.

Primary interface rationale: Red Hat's
[UBI image types](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/building_running_and_managing_containers/types-of-container-images)
and [adding software](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/building_running_and_managing_containers/adding-software-to-a-ubi-container),
plus [Podman build contexts](https://docs.podman.io/en/stable/markdown/podman-build.1.html#build-context-name-value).
Actual pinned-layer/build/runtime evidence remains task-owned.

Source enforcement: [app recipe](../../packaging/containers/Containerfile),
[Caddy recipe](../../packaging/containers/Containerfile.caddy),
[immutable inputs](../../packaging/containers/images.json),
[app builder](../../scripts/build-container.py),
[Caddy builder](../../scripts/build-caddy-container.py),
[public interpreter fetcher](../../scripts/fetch-container-python.py) and
[foundation proof](../../scripts/check-container-foundation.py).
Hermetic evidence: [app build](../../tests/unit/test_container_runtime.py),
[Caddy build](../../tests/unit/test_caddy_container_build.py),
[fetch](../../tests/unit/test_fetch_container_python.py) and
[foundation](../../tests/unit/test_container_foundation.py). Actual dirty and
clean image evidence remains separated in the task records.
