# Build all service image stages on pinned UBI 10 micro

- Decision identity: 129.

- Status: Accepted; current profile is qualified by the recorded deployment scope.
- Date: 2026-10-18.


## Context, decision and rationale

Every application/Caddy FROM stage uses pinned UBI10 micro. Actual micro has the
needed tools and glibc/libgcc; no shell-free claim, package-manager transaction
or larger tooling stage is required. Pinned UBI minimal donates only Red Hat CA
PEM. External uv/Caddy images donate verified executables, never foreign OS
libraries/defaults/CA or FROM stages. This meets the selected platform requirement
without importing another runtime distribution. Preserve explicit user/environment,
entrypoint, credential-mask mountpoints, cap-drop ALL and NoNewPrivileges.

Authenticated portable CPython3.14.6 and the locked hashed server+MCP wheel closure
remain explicit inputs. Verify contained extraction/native linkage. uv is build-only;
Caddy is copied to a fresh inode with no file capability, since port8443 needs no
cap_net_bind_service. Record base/donor/interpreter/binary/CA/source/wheel/closure
hashes and final image identity. Normal build/start never pulls; public pinned
prefetch is explicit and carries no app secret. Dirty proof identifies its snapshot,
not a clean release.

Omit only the inspected Python prefix's bin/pip, bin/pip3, bin/pip3.14,
lib/python3.14/site-packages/pip, lib/python3.14/site-packages/pip-26.1.2.dist-info,
and lib/python3.14/ensurepip (including its bundled wheel), inside the build layer
before final COPY. Preserve original verified archive/context bytes. No wildcard
or system cleanup/domain library change is allowed. Foundation proves pip/ensurepip/
uv absent from PATH/modules; a failed preview stays preserved and requires new
contexts/images, never relabeling failed evidence.

Foundation compares pinned manifest config ID and ordered RootFS diff-ID prefix,
then uses bind-free/no-network/read-only/caps0/NNP direct PID1 imports, NSS, CA,
SSL/glibc checks. os-release or successful imports alone do not prove confinement,
notification, API peer or served TLS. Fixed SSL_CERT_FILE=/etc/ssl/cert.pem names
verified Red Hat CA and must match its hash; unexplained trust overrides refuse.
The host fetcher separately ignores ambient SSL_CERT_* proxies/auth, verifies HTTPS
and bounds redirects/bytes/deadline. Normal caio backend fallback is recorded;
unavailable optional io_uring is no reason to force a backend or widen seccomp.
Proof-only HF_XET_LOG_DEST=/dev/null keeps native diagnostics outside its single
JSON result without changing application defaults. Retain exact named containers,
proof/failure records and unknown state. Installed 0.2.1 peer/TLS/readiness evidence
is distinct from these input/build checks and from NAS/domain acceptance.

## Relationships and technical evidence

- [cpython-3.14.6+20260718-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz](https://github.com/astral-sh/python-build-standalone/releases/download/20260718/cpython-3.14.6%2B20260718-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz)
- [128](decision-128.md)
- [UBI image types](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/building_running_and_managing_containers/types-of-container-images)
- [adding software](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/building_running_and_managing_containers/adding-software-to-a-ubi-container)
- [Podman build contexts](https://docs.podman.io/en/stable/markdown/podman-build.1.html#build-context-name-value)
- [app recipe](../../packaging/containers/Containerfile)
- [Caddy recipe](../../packaging/containers/Containerfile.caddy)
- [immutable inputs](../../packaging/containers/images.json)
- [app builder](../../scripts/build-container.py)
- [Caddy builder](../../scripts/build-caddy-container.py)
- [public interpreter fetcher](../../scripts/fetch-container-python.py)
- [foundation proof](../../scripts/check-container-foundation.py)
- [app build](../../tests/unit/test_container_runtime.py)
- [Caddy build](../../tests/unit/test_caddy_container_build.py)
- [fetch](../../tests/unit/test_fetch_container_python.py)
- [foundation](../../tests/unit/test_container_foundation.py)

See [deployment status](../deployment-status.md) for recorded scope and remaining acceptance.
