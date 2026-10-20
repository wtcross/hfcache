# Functional prerequisite inventory

WEB-001 inspected these prerequisites on 2026-10-20 without contacting a
production manager, the production API, any retained guest or the live archive.
This inventory establishes availability only. It does not establish that a
web functional deployment or any acceptance scenario has passed.

## Available tools and inputs

| Input | Observed availability |
| --- | --- |
| Locked development tools | `uv`, Python, `make`, Node `v24.18.1`, pnpm `11.18.0` and existing `cockpit/node_modules` are present. |
| Browser | `/usr/bin/firefox`, Mozilla Firefox `140.13.0esr`, runs its version command. Browser execution for the new UI is unperformed. |
| Three-engine test closure | Chromium/Chrome and Caddy are absent from `PATH`; `~/.cache/ms-playwright` and `~/.cache/puppeteer` are absent. Other locations and dependency closure are unverified. This is not proof that those prerequisites cannot be provisioned. |
| TLS tooling | OpenSSL `3.5.7` and `curl` are present. No test CA has been created for this plan. |
| Rootless runtime | `/usr/bin/podman` exists. No engine, manager, container or production runtime was contacted for this inventory. |
| Guest runtime | `/usr/libexec/qemu-kvm` exists and reports `11.1.0`; `/dev/kvm` is accessible for reading/writing; `/usr/bin/genisoimage` and `qemu-img` exist. `qemu-system-x86_64`, libvirt tools, `systemd-nspawn` and `machinectl` are absent from `PATH`, which does not block the existing QEMU path. |
| Isolation tools | `bwrap` and `unshare` are present. Their presence alone does not establish guest or hardening acceptance. |
| CentOS guest base | The retained mode-0400 base image described below is present; its actual SHA256 was rechecked successfully. |
| Offline Caddy image | The retained OCI archive described below is present and its index/config metadata was inspected without importing or running it. |

The retained CentOS Stream 10 base is
`.local-fixtures/cpr-runtime/downloads/CentOS-Stream-GenericCloud-10-20261013.0.x86_64.qcow2`,
1,045,299,200 bytes, SHA256
`a88076a3b342d97cd9f980ef7e36ab647f174338bce0d999963748e4cc698847`.
This matches the pinned historical acquisition record in
[the isolated runtime setup](../cockpit-rest-repair/runtime-setup.md).
The image was not booted or modified by this inventory.

The retained Caddy archive is
`.local-fixtures/cpr-runtime/cpr008-pipe/transfer/caddy.oci`,
26,818,560 bytes, SHA256
`923329e60a0ab1e09fb0b637036990078fec7ea8749b751b9c8305f69ec4448a`.
Its OCI manifest digest is
`sha256:6a59112d6ddc496dfa485f33dc16bc1b2a4b97604c456509371e075e8b3c9253`;
the config/image identity is
`sha256:fa2a5634a525af798ce6da2855d365f7cdf0f9a2d6d0eb56d461626e226acc10`.
The config labels identify Caddy `v2.11.7`, Linux amd64, on pinned UBI 10 micro.
This is an available test input, not acceptance of the new UI's release artifact.

## Retained guests and evidence

Five prior QEMU fixtures remain. This inventory read only positively identified
saved process metadata and the corresponding `/proc/<pid>/stat`, ownership and
QEMU fixture name; it sent no command or signal to them. The first saved
starttime was compared directly; the remaining current starttimes are recorded
here for later identity reconciliation, not authority to control a process.

| Saved fixture record | Current PID | UID | Current starttime | QEMU fixture name |
| --- | --- | --- | --- | --- |
| `cpr-runtime/evidence/qemu-process.json` | 1422140 | 1000 | 393250994 | `cpr-runtime-c9ec65d937d5420da32606a2c8f6304f` |
| `cpr-runtime/cpr008/evidence/qemu-process.json` | 1634668 | 1000 | 394793949 | `cpr008-2ff1176a1d9b4f1fbd046824a4635d2e` |
| `cpr-runtime/cpr008-fixed/evidence/qemu-process.json` | 1655053 | 1000 | 394913847 | `cpr008-9e6c9b6666ad43f09a886dae844866c2` |
| `cpr-runtime/cpr008-framed/evidence/qemu-process.json` | 1724602 | 1000 | 395413371 | `cpr008-framed-61853348c277414282d483fc7e37bc2e` |
| `cpr-runtime/cpr008-pipe/evidence/qemu-process.json` | 1773207 | 1000 | 396308915 | `cpr008-pipe-d901b229bbca4eaf8a0520dbb91505b4` |

Paths in that table are relative to `.local-fixtures/`. Preserve all five
guests, original disks, guards, locks, credentials, operation handles,
candidates, backups and unknown/unconfirmed attempts. Do not reuse or clean
them as a shortcut for this plan. Prior installed acceptance is historical
evidence, not acceptance of new source.

## Safe provisioning and outstanding verification

Create a new explicitly owned WEB workspace under the repository's ignored
fixture root with restricted modes, its own fresh disk overlay, NoCloud seed,
synthetic credentials, keys, test CA and unused loopback ports. Revalidate the
base hash and backing chain before launch. Use the reviewed QEMU KVM path with
restricted user networking, no gateway/DNS/external route, and no host
directory, archive, device, production credential, socket or manager bind.
Guest root operations stay inside the positively identified disposable guest.
No production Caddy, system/user manager, timer, guard or archive is a test
surface.

Before functional runtime execution, separately provision and verify pinned
three-engine browser/test dependencies and offline native/rootless guest
dependency closure. Audit available historical offline bundles before reuse;
their presence does not prove completeness, correct versions or new-source
identity. Build/install the selected wheel, web assets, helper and worker,
record their hashes, and verify installed bytes. Import only reviewed exact
local image artifacts; runtime gates must not pull images automatically.
Generate fixture state through owned builders and never run archive init on
the host.

The existing tools/base/image provide a concrete provisioning path. No
infrastructure blocker is inferred solely from a missing `PATH` entry or
browser cache. Browser closure, new fixture provisioning, actual manager/peer
behavior, trusted test TLS, private-worker confinement and installed artifact
identity remain unverified prerequisites for the tasks that require them. A
failed required check must record its actual failure and unblock condition;
missing or skipped checks cannot establish functional acceptance.

## Inventory commands and limits

The audit used `shutil.which`, bounded filesystem metadata/listing under the
owned fixture root, version-only tool invocations, streaming SHA256 of the
known immutable base, and read-only OCI tar/index/config inspection. It did
not read credential files, invoke Podman, enter a guest, contact a service,
inspect production control stores or read live NAS contents. Existing
documentation alignment passed separately: 188 human documents and 19 helpers.
