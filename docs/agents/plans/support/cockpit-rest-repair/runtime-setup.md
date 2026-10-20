# Disposable CPR runtime infrastructure

This is diagnostic infrastructure preparation during CPR-002, under the user's
2026-10-19 local-host development authorization. It does not complete V54 or
start CPR-008. Production hfcache installation, configuration, services,
credentials, guards, original locks, masks, mounts and NAS contents are outside
this fixture and have not been modified or accessed by this setup.

## Owned local state

- Fixture: `/home/tyler/Projects/hfcache/.local-fixtures/cpr-runtime`, created
  fresh with mode `0700`, on `/home` XFS (`/dev/mapper/cs-home`).
- Private subdirectories: `downloads`, `disks`, `seed`, `keys`, `evidence`,
  `rpms`, each initially `0700`. Synthetic keys/passwords and disk images are
  never committed. A local `/.local-fixtures/` entry was added to
  `.git/info/exclude`; no tracked ignore policy changed.
- Unprivileged KVM availability: `/dev/kvm` accessible, API version 12.
  Host SELinux was enforcing before provisioning.
- Initial available local disk: 55,198,961,664 bytes. The fixture does not bind
  host directories, block devices, production sockets or credentials into a guest.

## Host prerequisites actually installed

Saved the complete initial RPM name/NEVRA inventory before installation in
`evidence/host-packages-before.tsv`. Ran and reviewed:

```sh
rtk proxy sudo -n dnf --assumeno --setopt=install_weak_deps=False install qemu-kvm-core qemu-img genisoimage
```

The proposed transaction contained twelve new packages and no upgrades/removals.
Downloaded it with `--downloadonly` into the owned `rpms` directory, verified
each RPM with `rpm -K`, reviewed every package scriptlet and refused any package
file list overlapping `/etc/hfcache`, `/opt/hfcache` or `/srv/hfcache`.

Installed those exact local files using repositories disabled,
`install_weak_deps=False` and `localpkg_gpgcheck=True`. Actual result: exit 0;
twelve additions, zero removed/replaced RPM records in the complete inventory.

| Newly installed package | Version |
| --- | --- |
| capstone | 5.0.1-8.el10.x86_64 |
| edk2-ovmf | 20260821-2.el10.noarch |
| genisoimage | 1.1.11-58.el10_1.x86_64 |
| ipxe-roms-qemu | 20240119-5.gitde8a0821.el10.noarch |
| libfdt | 1.7.0-12.el10.x86_64 |
| libslirp | 4.7.0-10.el10.x86_64 |
| libusal | 1.1.11-58.el10_1.x86_64 |
| qemu-img | 18:11.1.0-1.el10.x86_64 |
| qemu-kvm-common | 18:11.1.0-1.el10.x86_64 |
| qemu-kvm-core | 18:11.1.0-1.el10.x86_64 |
| seabios-bin | 1.17.0-1.el10.noarch |
| seavgabios-bin | 1.17.0-1.el10.noarch |

CentOS AppStream supplied QEMU/dependencies; the already configured EPEL
repository supplied genisoimage/libusal. No libvirt or network bridge service
was installed. Scriptlets register normal mkisofs alternatives and create the
normal QEMU account/group if absent. Actual account changes: new QEMU UID/GID
107 and its membership in the existing KVM GID 36; new mkisofs/mkhybrid
alternatives, both absent before installation. Prior and resulting state are
retained in `evidence/host-account-alternatives-before.json` and
`evidence/host-account-alternatives-after.json`. Ordinary DNF transaction/cache
and RPM database changes accompany this reviewed prerequisite installation.

Exact argv, complete bounded transaction logs, RPM hashes/signature results,
scriptlets, and before/after inventories are in the private `evidence` directory:
`package-download-command.json`, `package-download.log`,
`reviewed-host-rpms.json`, `reviewed-host-scriptlets.txt`,
`package-install-command.json`, `package-install.log`,
`host-packages-after.tsv`, `host-package-delta.json`.

## Guest input and isolation

Selected the dated
[CentOS Stream 10 image](https://cloud.centos.org/centos/10-stream/x86_64/images/CentOS-Stream-GenericCloud-10-20261013.0.x86_64.qcow2)
and pinned its 1,045,299,200-byte size and SHA256
`a88076a3b342d97cd9f980ef7e36ab647f174338bce0d999963748e4cc698847`
against the official
[CHECKSUM](https://cloud.centos.org/centos/10-stream/x86_64/images/CHECKSUM).
Acquisition uses HTTPS with environmental proxies disabled; no registry or
production credential is involved. Download and exact size/hash verification
completed successfully; the base is mode `0400`. `qemu-img info` confirmed qcow2
with no backing dependency. A fresh 24 GiB sparse qcow2 overlay uses that base.

The running guest has two vCPUs and 4 GiB RAM, the immutable verified
base with a private overlay, an owned NoCloud seed and synthetic SSH/PAM
credentials. Both guest and host SELinux are enforcing. QEMU uses
`restrict=on,ipv6=off`, with only `127.0.0.1:22054` to guest SSH and
`127.0.0.1:19054` to guest Cockpit.
[QEMU's documented isolation](https://www.qemu.org/docs/master/system/qemu-manpage.html)
blocks guest host/external access while retaining those explicit forwards.
No TAP, host bridge, shared filesystem, SSH agent forwarding or guest forwarding
is permitted. The seed configures a static `10.0.2.15/24` address with no gateway
or DNS configuration. Guest IPv4 and IPv6 route inventories confirmed no default
route. IPv6 guest routes are local/link-local only; the QEMU backend has IPv6
disabled. Later guest package installation must use an offline signed RPM bundle.

## Actual bootstrap proof

| Observation | Result |
| --- | --- |
| QEMU invocation identity | `cpr-runtime-c9ec65d937d5420da32606a2c8f6304f` |
| Owned host process | QEMU PID `1422140`, UID 1000; launcher PID `1422139` |
| Process identity check | `/proc/1422140/stat` starttime `393250994`; revalidate before any signal |
| QEMU hardening | `NoNewPrivs=1`, `Seccomp=2`; no control disabled |
| Forwarded host listeners | QEMU owns only `127.0.0.1:22054` and `127.0.0.1:19054` for this fixture |
| SSH | Successful on second bounded attempt; strict pre-pinned synthetic host key, explicit fixture client key, no agent/config/environment forwarding |
| SSH host-key identity | `SHA256:f2ojPZqcmAFZmxTv0DzDQ75Wmp86a00/XVk/0YPtyzM` |
| Guest identity | `cprtester`, UID/GID 1000, wheel membership; password required for guest sudo |
| Guest hostname/kernel | `cpr-fixture.local`, `6.12.0-275.el10.x86_64` |
| Guest base release | `centos-stream-release-10.0-23.el10.noarch` |
| Guest systemd / SSH / cloud-init | `257-34.el10` / `9.9p1-33.el10` / `24.4-7.el10.1` |
| Existing guest Cockpit / Podman | Image already contains `cockpit-ws-368-1.el10` and `podman-6.1.0-2.el10`; this task did not install, update or activate them |
| Guest archive isolation | `/srv/hfcache` absent; no `nfs`/`nfs4` mounts; no archive initialized |
| Cloud-init completion | Exact fixture final-message marker observed |

The image's Cockpit/Podman versions differ from the previously recorded host
versions. This is explicit fixture identity, not installed-version parity proof.
Synthetic private inputs are only in `keys/` and `seed/`, mode `0600` under the
owned `0700` directory; neither values nor password hashes appear in this record.
Git exclusion was checked against both `seed/user-data` and the password file.

Exact QEMU argv, process identity, guest route/address/package/mount observations,
SSH argv and first identity, and host loopback listener/sandbox observations are
preserved privately as `evidence/qemu-argv.json`, `qemu-process.json`,
`guest-image.json`, `guest-seed.json`, `guest-bootstrap-proof.json`,
`ssh-argv.json`, `ssh-first-identity.txt`, `host-qemu-proof.json` and
`host-fixture-listeners.txt`. Console/launcher logs remain private and bounded
inspection did not export user-data or secret material.

## Current evidence and remaining work

Host prerequisites and guest boot/SSH isolation are proven. Provisioning paused
at this package boundary by the coordinating agent's instruction. No hfcache
application, release bindings, role secrets, fixture NFS export or rootless
application manager has been installed or started inside the guest. No real
Cockpit/PAM/rootless application-chain result is claimed; V54 remains unpassed.

The guest may remain running safely while paused: it is a disposable independent
kernel/disk, has no external route, no host share/credential/archive attachment,
and exposes only the two loopback forwards under its synthetic identities.
Resource allocation remains bounded above. Retain the guest and its exact
evidence for the next explicitly active work package; no automatic work is queued.

Next infrastructure action is to review the preinstalled guest package versions,
then provision the synthetic application release/profile/secret fixture and
guest-only NFS barrier before exercising the real Cockpit chain. Existing source
regressions and guest bootstrap do not establish the original installed cause.

Unchanged API/worker launchers require an actual read-only NFS mount; the guard
independently checks guest PID 1's mount table. A future guest-only loopback NFS
fixture must satisfy those checks. Do not replace NFS with ext4, fake mountinfo,
relax the guard, or attach the host's archive. Candidate/version/authenticated
refusal diagnostics can use an empty guest-only export without archive init.

## Cleanup handoff

Before stopping, verify the saved QEMU PID, process starttime, UID and exact argv
still identify this owned guest. Prefer authenticated SSH with the pinned fixture
host/client keys and synthetic sudo password supplied privately on stdin to run
guest `systemctl poweroff`; do not print or place the password in argv/environment.
If the guest is unresponsive, investigate only that verified owned QEMU process;
no production service control follows from its state.

Stop only this identified guest after fixture work drains, preserve evidence,
and remove only its explained owned files. Reconcile the recorded twelve-package
delta against current package use before any removal; do not blindly run DNF
autoremove. QEMU account/group and alternatives require comparison with their
saved initial state. No production hfcache backup/restoration is needed because
this setup did not alter that installation. Retain this record and the private
evidence until diagnostic acceptance and cleanup are complete.
