# Local 0.3.0 migration evidence

Recorded 2026-11-02 for the authorized replacement of this host's rootless
deployment, including web UI, REST, MCP and removal of its hfcache Cockpit
entrypoint. This is installed read-only migration acceptance, not permission for
archive work or a general production workload certification.

## Immutable identity

| Artifact | Identity |
| --- | --- |
| Selected version | 0.3.0 |
| Clean artifact source | `3d6670d8dd0e8f2c941991ce154ecca7ac63c73c` |
| Full captured source snapshot | `9fe27c935508e986465943a63dd3408575cfd458331dce65085f9dd44d0c1cd2` |
| Wheel SHA256 | `ca3cf2bd31d35c96e212980c3d66435e7a5c1a9666444d16072f38f9f8fca4b8` |
| UI manifest SHA256 | `60c2cf945b46af7f92227c673e193bc9f4588c61a452fc7361e1615450ad1698` |
| App image | `sha256:bcfccd85b263beaeed5d2c424d9b638f4f4a17406137def5aab1aa514e5cb68e` |
| Retained Caddy image | `sha256:fa2a5634a525af798ce6da2855d365f7cdf0f9a2d6d0eb56d461626e226acc10` |
| Input manifest SHA256 | `e6e69df1b30931b086e34bc35a8200ab67e433a3081fc561a9786706306d175a` |
| OCI SHA256 | `06582873ad1f0410205d0b35fec0258d9fa0270b50c027a1084c93a552fb705e` |
| Installed 77-file index SHA256 | `251958ef55288266385d0bc99079dc9fb3bfd676f9c656b188570e1042b7c635` |
| Protected helper deployment SHA256 | `14157fe5779e58efbcbc72570136bfd5cb6fb4659d7919bcf325ee86f8095818` |
| Loaded helper CIL SHA256 | `cd9e923f7aead03b98a95673baf0f4ad2163f9eee3c467d54dcb010fbd79d6e7` |
| Helper SELinux receipt SHA256 | `67beb2fff11dd3d586e8d179c808bf197479247a164c86d456c85ad7808ce18b` |

All seven clean construction phases pass once, as login UID1000 with an empty
read-only private NAS shadow. Final image foundation/private-worker/Caddy proofs
are distinct from actual installed acceptance below. Protected root capture and
independent re-render precede staging. Neither reproducible construction nor
image import is replayed after success. All nine through-current bindings and
service-UID traversal/hash readability are verified.

## State preservation and cutover

Root-private coordinated backup and ledgers remain at
`/opt/hfcache/deployment/20261101-web-0.3.0`. Its `before.json` SHA256 is
`c15401645b5e2d965db3bd9bec9b09112be80fd35c7aa756af3701bbf38537c9`;
48 local files/514,987 bytes were captured under the original configuration flock.
Full installed configuration remains byte-identical, SHA256
`3a61672724c763b2fd24ca1231abba8a0de3e12f20bc0e4baf7978d24fedc64c`:
165 enabled models and zero dataset entries. Existing archived datasets are
unaffected by the absence of configured dataset entries. No archive payload
migration, initialization, mutation or workload runs.

The preserved service remains UID/GID981 with home
`/var/lib/hfcache/container-home` and its original graphroot. Podman6.0.2 uses the
three exact measured stock configuration hashes. No account/store relocation,
package update or fallback store selection occurs. Existing API/worker stores,
five terminal operation receipts and results, handles, retired candidates,
backups, TLS/REST/MCP/Hub secret identities and bytes remain preserved.

Actual API-first graceful drain retains the worker until API execution ends,
then drains worker/Caddy. Original PIDs/start identities, both managers, libpod
cgroups and sockets prove quiescence; launcher removal of exact stopped owned
containers is accounted separately from unexplained absence. The noncreating
domain lock remains dev27/inode1728, UID/GID981,0600,single-link; configuration
lock remains dev64768/inode138322689,root:root0600. Root coordinates the
temporary guard/installer/root/guard handoff. Official selection runs once.

The host NFS mount remains ro,nosuid,nodev,noexec; all four writer/timer units
remain masked and inactive. SELinux stays Enforcing. Only four original local
file ctimes change from explicit SELinux relabeling: config, backup,
configuration lock and common lock. Original bytes/inodes/owners/modes/mtimes
remain. No NAS label, ownership or filesystem change is made.

## Actual authentication and helper acceptance

The separately provisioned administrator hash is exclusively delivered as
UID/GID981,mode0400, then assigned the helper-denied secret label. Passwords
remain in the user's trusted terminal and transient validator memory; no hash
payload or password is printed or copied into an evidence record. Bearers remain
separate and cannot replace the original API's Basic administrator/helper peer.

The exact selected bootstrap, priority400 underscore CIL module, bounded local
labels, fifteen-role receipt, new protected key and finite-home deployment index
are installed before helper startup. The helper reaches READY in
`hfcache_host_helper_t` before the API. Initial policy is independently all-false,
SHA256 `3761028f542df36fd8a08c0e9f83203f224c216c46f806c8fe169c0212e1efea`.

The first human attempt leaves a failed result with no completed GETs, SHA256
`d33ab41609fa0fbb87caf08cd16d3b2cebf468cfece621ba6113de19ecbb1802`.
The later attempt completes all checks, durably writes actual HostStatus SHA256
`974c14a84c7567896996ca5678c8dc3cc2cab9a4911e4dd218d1097942a45aa1`, then
fails while refusing to overwrite that earlier result. The pinned validator
`66bc99fd57bbe1ddb0ffd34ebb17ae3ca6c7789426b579f45f7dc5e9d0d5983d`
writes HostStatus only after TLS, Basic, document/bootstrap/six assets and exact
guarded/rootless/all-false checks pass. This is qualified control-flow recovery,
not a successful final receipt or recovered individual request hashes. Both
originals remain unchanged; `human-all-false-recovery1.json` SHA256
`a95d47ffc288cb0f7e5ecf3849c2a7ea39b9732661c12c723bc59649e93998aa`
records the distinction. The revised validator preflights both new outputs
before prompting and records failed HTTP status metadata without body values.

Independent root review preserves only configuration=true and Hub=true, matching
the actual prior grants; archive/control/schedule/observer remain false. Policy
SHA256 is `0c189ae7c06dcee81f9ae86592ff821c1183d73969acec13d256a5008daf5a4b`.
The original all-false policy inode is retained in the protected helper evidence.
A fresh trusted-terminal preserved-phase run passes all ten GETs, including
managed configuration, with result SHA256
`379ee005af3ac2156b72fbe614335fbf638b8d81c860cf3daddd78b90932c2bc` and
actual HostStatus SHA256
`910d58de130282c2cc3600d6bc3cde08106acc0ff4a502ef6f5eedfdb5f5688a`.
These reads exercise the actual API-origin fixed helper on Podman6.0.2.

## Final installed state

The public `/usr/share/cockpit/hfcache` symlink is retired by retaining its exact
original inode137967146 at `cockpit-hfcache-entrypoint.original` in the protected
backup. Old0.2.2 plugin assets, shared Cockpit components and original CA remain.
No unrelated package, credential or retained configuration is removed.

The user's October22 intentional inactive guard setting is restored after a
second graceful API-first drain, separate helper/inspector cohort drain and
worker/Caddy drain. Current process/start identities and the helper's recursive
cgroup prove zero executors before stopping the temporary guard. Root acquires
the original noncreating flock, proves kernel ownership, then deliberately
releases it at that zero-executor boundary. No selector/bootstrap/policy edit
occurs. Explicit helper READY then bridge startup restores the same application
release with the guard inactive. There is no reboot or schedule enablement.

Final `installed-preserved-inactive1.json` SHA256
`74ee1a854a3299e809a9d24c98dc6333c0038fbcadd07182b8f8a4df14ab29ea` passes
29 HTTP checks, verified TLS, reader/writer/MCP/Basic separation, the fourteen-tool
MCP listing, API-origin private worker PROBE, server version and exact five original
operation/result pairs without replay. It rechecks all indexed bytes/bindings,
original state, secret identities, actual PID1 capabilities/NNP/seccomp/read-only
root and worker masks, helper SID/bootstrap/module/receipt and preserved policy.
The earlier fixed host client separately reports server0.3.0. Positive Basic and
configuration checks precede the final unchanged-code restart; final automated
checks do not claim a new post-restart positive Basic request.

## Limits and closeout

No live NAS jobs/full verification/repair/retention, NFS interruption, archive
health certification, calendar enablement, reboot, export/consumer copying,
other-host operation, browser-JavaScript workflow or candidate Apply is accepted
here. New-host all-phase IP/inode-alias/counterpart negative companion acceptance
remains NOT RUN. Actual process/capability/mount/module/label and authenticated
fixed-helper observations retain their stated scope; historical owned-fixture
negative proofs are not relabelled as new-host syscall evidence.

Reviewed invariants INV-001–003/020, FS-19/21–23 and the applicable existing
release/transport/helper decisions remain intact. This operational migration
adds no archive, runtime or authority schema, dependency or privilege. Keep the
retained0.2.2/0.2.1 releases and compatible rollback configuration; rollback still
requires actual executor drain, original locks and a matching bootstrap/index.

Current-boot operation and the reviewed restart are accepted. Automatic recovery
after reboot/runtime-object recreation is not configured: helper is disabled,
and the bridge has no helper startup ordering. Before starting bridge/API after
such an event, an operator must independently provision the documented existing
runtime lock/shared-memory labels and helper parents/binding, then start helper
and observe READY. Persistent fcontext rules alone are insufficient. Reboot and
unattended boot recovery remain operator holds; no automatic root provisioner is
introduced here.

Final strict source/web/build gate passes:9590 backend,4051 combined web,16wheel,
three locked profiles, two Chromium startup checks and real HTTP/API React fixture.
All1234 tracked bodies/names, symlink targets and HEAD stay frozen during
1539.304s; log SHA256
`19a6def18e0d4270bc6662cc823a0150e4143304fc9524b80bd19aa26e18cc7d`.
Final post-gate preservation record SHA256
`725901e4eeff5595bdfc07667610a2b4686b365366bb2fac837e822d4e52619f`
confirms original files/stores/locks, active roles/helper, inactive guard/no domain
holder, NFSro/masks/Enforcing, retired plugin inode/assets and retained CA.
Local annotated `v0.3.0` object `013d982e71fcbd2a4eaad11f661326257e1dd28a`
targets the exact clean artifact source in the table. Operational evidence belongs
to the separate migration commit. No remote push or registry publication occurs.
