# Deploy the optional web interface

This describes optional authentication and immutable asset serving in unreleased
source. Installed systems still use their recorded release and Cockpit. A source
build does not install assets, select a release or enable `[web]`. Do not change a
running installation merely to try the developer preview. See
[current installed scope](../deployment-status.md) before planning a migration.

The replacement uses one whole-archive human administrator. The browser handles
the HTTP Basic challenge over verified HTTPS. Page scripts receive neither its
password nor a REST/Hub token. Signing in grants no storage writability, protected
host policy, Hub access or permission to bypass a guard. REST writer/reader and
read-only MCP bearers remain separate. Basic credentials never authenticate MCP.

## Create a protected record

Use a trusted terminal and the selected source's locked server environment.
Choose a stable subject such as `archive-admin`; keep that subject through
password/username rotation so original operation keys remain recoverable. A new
subject represents a new identity with a separate key namespace. Record the
nonsecret subject with the deployment inventory.

Prepare a new local output path under a private directory owned by the operator,
with no symlink or group/other-writable ancestor. The helper refuses network
mounts and `/srv` paths. It never overwrites an existing file. For example, after
creating such a directory at the example absolute path:

```bash
uv run --locked --extra server python scripts/provision-ui-administrator.py \
  archive-admin administrator \
  --output /home/operator/private-ui-records/administrator-v1.json
```

The helper prompts twice without echo. It accepts at most 1024 UTF-8 password
bytes and refuses empty provisioning input. Do not supply passwords in arguments,
environment variables, redirected files or command history. The API does not
normalize passwords; exact input matters. The output is a mode `0600` strict JSON
record containing schema, stable subject, username and a fresh salted Argon2id
hash using fixed 64 MiB, three iterations and one lane. It contains no plaintext
password. Protect the hash against offline guessing and unauthorized replacement;
do not paste it into TOML, logs, screenshots or support reports. Failed writes
remain for inspection and are never automatically removed.

## Configure the provider

Server transport/authentication settings belong in the separate server TOML,
not the archive configuration. `[basic]` is optional and disabled when absent.
When enabled, its origin must be the exact browser-canonical HTTPS origin,
including a nondefault port if used, with no path or trailing slash. Put its
hostname in `listener.allowed_hosts` and the same full origin in
`listener.allowed_origins`. A public path prefix belongs in `listener.root_path`,
separately from the origin. Do not use wildcard allowlists.

An illustrative native configuration is:

```toml
[basic]
origin = "https://archive.example.com:8443"
[basic.administrator]
systemd_name = "hfcache.ui-administrator"
```

This fragment requires the existing writer source and complete listener policy.
It is not a complete server file. Exactly one `systemd_name` or absolute `file`
source is allowed. Missing, unsafe, malformed or unsupported records refuse
startup; there is no fallback to another credential. Source and hash changes
require a reviewed service restart. Archive policy reload does not rotate them.

## Deliver the record to the selected profile

For native system services, the operator encrypts the protected hash record into
the machine's systemd credential store and adds an explicit API-only service
drop-in containing:

```ini
[Service]
LoadCredentialEncrypted=hfcache.ui-administrator:/etc/credstore.encrypted/hfcache.ui-administrator
```

The matching `systemd_name` resolves only inside that API service's
`CREDENTIALS_DIRECTORY`. Do not give this credential to Caddy, the verification
worker or CLI observer services. Installing the encrypted credential/drop-in,
reloading a manager and restarting services are deployment actions, requiring a
separate authorized rollout and normal executor-drain checks. This source change
does none of them.

For the existing rootless profile, the API already reads the protected policy
directory. An explicitly reviewed release may select:

```toml
[basic]
origin = "https://archive.example.com:8443"
[basic.administrator]
file = "/etc/hfcache/credentials/ui-administrator.json"
```

Provision that hash record mode `0400` or `0600`, readable only by the actual
rootless service identity mapped to the API's UID 981. Host UID 981 is not
automatically that identity. Verify the effective owner inside the API. Keep the
parent directory private to its intended identities. Worker/client containers
mask this fixed credentials directory; Caddy does not mount `/etc/hfcache`.

The API needs search access through the credential's parent directories and
read access to the protected file. The loader does not list or read directory
contents. Keep the protected labels and directory permissions; do not grant
directory-read access merely to make administrator loading succeed.
Keep records inside this reviewed directory rather than elsewhere in the shared
policy tree. No new secret is required when Basic is disabled. Release indexing,
actual role isolation and installed native/rootless acceptance are completed by
the packaging and platform tests before rollout.

Native API startup also depends on the separate private verifier connection.
The system manager's kernel peer UID and the worker-owned socket file are
different identities. Configure peer UID `0` together with the measured numeric
worker/socket-owner UID as described in
[native verifier identity](../deployment-centos-stream-10.md#native-verifier-identity).
Do not copy a numeric service UID from another machine or give this private
connection a browser, Caddy or bearer credential. The rootless worker-created
listener keeps its existing equal owner/peer settings. Administrator login and
asset availability do not prove that verification execution is available.

## Select a matching immutable asset artifact

`[web]` belongs in the server TOML and is disabled by default. Enabling it
requires the Basic provider plus both an explicit absolute asset directory and
the lowercase SHA256 of that directory's canonical `manifest.json`:

```toml
[web]
enabled = true
asset_root = "/opt/hfcache/releases/RELEASE/ui"
manifest_sha256 = "REPLACE_WITH_THE_REVIEWED_64_CHARACTER_LOWERCASE_MANIFEST_SHA256"
```

`RELEASE` and the digest are placeholders, not runnable values. Review a newly
built artifact and its source inventory using the
[locked workspace build](../development.md#web-workspace); `pnpm --dir web run build`
writes `web/dist/manifest.json` and its indexed files. Node and pnpm belong only
in the build/test environment. The API needs neither a frontend server nor a
runtime package manager.

The artifact must match the installed application's version and Python-derived
wire authority. Keep its source commit, source snapshot, dirty flag, lock,
toolchain, license inventory and notices with release evidence. A dirty local
artifact can exercise an owned test fixture; it does not establish a clean
release. Current release installers do not automatically stage this new asset
tree. Clean release packaging, migration and Cockpit retirement remain separate
work; do not describe an ad-hoc copy as an accepted production release.

Use a protected local tree on ext4, xfs, btrfs, tmpfs or overlay. Every ancestor,
directory and file must be owned by root or the effective API service identity
and must not be group/other writable. Files must be regular, single-link files.
Symlinks, unindexed files, changed bytes, ambiguous mount identity and unsupported
filesystems refuse enabled startup. The artifact must be disjoint from archive,
configuration, API state, credentials and their delivery directories, sockets,
locks and configured application TLS material, including bind aliases. Do not
put it under the archive or weaken directory ownership to resolve a refusal.

The API verifies at most 4,096 indexed files, 4,096 directories and 8,193 total
entries, to depth eight. Each member is at most 8 MiB; raw members total at most
64 MiB, with a manifest at most 2 MiB. It captures approved bytes at startup,
keeps one protected root descriptor and serves the captured release until the
next authorized drained restart. Replacing files under a running process does
not hot-update that process. Missing, altered or incompatible enabled assets
refuse startup before operation-store construction or runner admission.

## Keep the existing Caddy boundary

The UI uses `/ui/` or the configured public prefix followed by `/ui/`, through
the **same existing Caddy instance and Unix API upstream** as REST and MCP.
Forward UI requests to that upstream with their Authorization header; Caddy does
not read or serve the asset directory and receives no administrator record.
Preserve the established TLS, Host/Origin, socket permissions and logging policy.
Do not add a Caddy-wide Basic gate, frontend server, public listener or runtime
Node. Do not enable Caddy administration or ACME as a test workaround.

`listener.root_path` is empty or a normalized absolute prefix without a trailing
slash. A leading `//` is refused. UI-enabled startup additionally bounds it to
1,024 UTF-8 bytes and the configured canonical HTTPS origin to 4,096 bytes.
Ordinary existing ASCII prefixes keep their acknowledgment and redirect bytes;
accepted Unicode, quotes and angle brackets are encoded in Location headers.
JSON operation links retain their original raw path identity. Use the supported
updated client when selecting such a prefix; older clients do not acquire new
Unicode-prefix support from a server upgrade.

`/ui` redirects to `/ui/` after authentication. The four current workspace paths
are exact document routes. Assets, unknown addresses and API/MCP errors never
receive an HTML history fallback. All UI responses carry the restricted CSP,
nosniff, no-referrer and disabled camera/microphone/geolocation policy. Documents,
bootstrap and errors are no-store; only validated indexed hashed assets get a
private one-hour immutable cache. `HEAD` preserves the corresponding status and
length while sending no body. Range requests are refused.

The API admits at most 16 active UI body streams with no waiting queue, sends
chunks of at most 64 KiB and limits the entire send, including headers, to 30
seconds. A full or draining UI service returns a classified unavailable response.
These streams have separate capacity from metadata reads and password hashing.
Shutdown stops admission, joins actual sends and releases the captured root
before releasing the instance lock.

## Install the protected host reader

This is a separate, explicitly authorized host installation. Do not infer that
enabling browser login installs a helper or grants a policy category. Start with
an accepted immutable release and measured API host UID/GID. Preserve the existing
guard, masks, disabled calendars, original locks, stores and pending handles.
Drain actual executors before replacing release bindings. Do not change NAS
contents or SELinux/systemd hardening to establish helper support.

For upgrades, staging or switching a native/rootless release does not refresh
these fixed host bootstrap copies. Drain the API and original helper/inspector
cohort first. Before installing any replacement, identify the reviewed predecessor
files and preserve their bytes, original inodes, ownership/modes and full SELinux
contexts in a protected rollback location. A byte copy alone does not preserve an
original inode. Retain unexpected files and refuse changes until they are reviewed;
never overwrite unknown evidence. Only then install the reviewed bootstrap copies
matching the selected release, before running the index preparer.

Verify the new files' required `hfcache_host_helper_exec_t` and
`hfcache_host_helper_code_t` types before publication and preparation. Read the
actual full contexts: do not infer a file's SELinux User component from the helper
process domain. Keep the independently installed CIL/module/kernel receipt and
permission policy under separate review. A code refresh neither reloads policy nor
changes the six permission booleans or the existing key.

1. Install the selected release's `scripts/host-helper.py` as the ordinary
   root-owned0755 `/usr/local/libexec/hfcache-host-helper`. Install its
   `host_protocol.py`, `host_policy.py`, `host_peer.py`, `host_configuration.py` and selected
   `packaging/selinux/hfcache-host-helper.cil` as root-owned0644 ordinary files
   under root-owned0755 `/usr/local/lib/hfcache-host-helper`. The modules are
   protected host Python3.12 standard-library copies, distinct from API code;
   the CIL is independently bound policy authority. Rootless staging captures
   all seven helper files in its manifest before indexing, including the CIL.
   Install the exact selected `hfcache-host-helper.service` as an ordinary
   root-owned0644 system unit. Rootless staged copies live under `host-helper/`;
   native copies come from `src/hfcache/`, `scripts/` and `packaging/systemd/`.
   The reviewed managed entry must preserve only ambient SETUID within the
   SETUID/SETGID ceiling, then clear all ambient/inheritable bits before threads
   or children. Verify actual steady root sets; a unit ceiling alone is not
   proof. Its fixed engine child may enter only the proved existing USER
   namespace. At fixed API-container exec, retain only namespace-local
   DAC_READ_SEARCH and SYS_ADMIN in effective/permitted/bounding sets (bits2+21,
   mask0x200004), empty inheritable/ambient sets and securebits0xCE.
   [Decision151](../adr/decision-151.md) supersedes only the SYS_ADMIN-only rule.
   Prove both protected ID maps: read/search DAC bypass covers all reachable
   mapped-UID-and-GID inodes, not one metadata path; it grants no write or
   regular-file execute bypass and does not replace SELinux. Grant no initial-
   USER DAC/SYS_ADMIN. SELinux must never authorize DAC_OVERRIDE; its bit must
   be absent at verified steady/fixed-exec boundaries. Do not change chmod/ACLs or
   payload/secret label access. Prove the retained masked MNT belongs to initial
   USER and actual MNT-entry/unshare, archive/Hub/IP and required inode/FD-alias
   denials under the revised bits. It never
   joins MNT/PID/NET. Keep the host
   observer's original masked MNT, NoNewPrivileges, AF_UNIX and secret/archive
   masks. Follow the [exact contract](../host-administration.md#managed-startup-and-fixed-engine-observation)
   rather than adding capabilities or forwarding arbitrary environment.
2. Explicitly install the reviewed CIL under module name
   `hfcache_host_helper` at priority400, preserving any unknown existing module.
   Use an exact-byte staging basename `hfcache_host_helper.cil` for module
   installation; the fixed installed authority copy retains its hyphenated name.
   Require Enforcing and the exact first-exec domain; no permissive or
   unconfined fallback is valid. Install the selected tmpfiles fragment as
   `/etc/tmpfiles.d/hfcache-host-helper.conf`, with the measured API group.
   Keep `SupplementaryGroups=hfcache` in the selected helper unit. This is the
   existing application group, not a new capability or per-request credential
   change. Its only new writable bind is fixed `/etc/hfcache`; all archive,
   credential and network restrictions remain in force.
   Provision the fixed labels in the
   [mandatory SELinux contract](../host-administration.md#mandatory-selinux-isolation).
   The exact `/etc/hfcache` directory needs
   `hfcache_host_helper_configuration_dir_t`. Installed configuration and owned
   `.candidate.toml`/`config.toml.bak` use `hfcache_host_helper_application_conf_t`;
   `.configuration.lock` and `.configuration.pending` use
   `hfcache_host_helper_configuration_guard_t`. The private
   `/etc/hfcache/.configuration-applications(/.*)?` context is
   `hfcache_host_helper_application_state_t`, except these fixed retained-original
   paths, which require `hfcache_host_helper_application_conf_t`:
   `/etc/hfcache/.configuration-applications/[0-9a-f]{32}/predecessor\.toml` and
   `/etc/hfcache/.configuration-applications/[0-9a-f]{32}/previous-backup\.toml`.
   Add those specific exceptions after the private-tree rule and verify effective
   `matchpathcon` results before provisioning; do not rely on regex specificity
   to override local rule ordering. Apply narrow persistent rules and
   inspect effective contexts before preparing the new deployment/SELinux
   receipt. A reviewed first upgrade may assign the new guard SID to the same
   original lock inode: record its before/after full contexts while retaining
   device/inode, mode and ownership. Never replace/unlink it. If no original guard
   exists, root must explicitly provision the fixed root:root0600 single-link lock
   once before enabling application; reads and the writer never create it.
   Preserve pending and
   private history evidence; unknown state refuses upgrade rather than being
   relabelled or removed.
   New helper-created files/directories use the compiled creation transitions.
   Legacy root `unconfined_t` candidate/backup publications use corresponding file
   and named guard transitions under this exact directory, without a new allow
   grant. Verify the actual Cockpit/root launch domain and resulting installed
   leaf SID during coexistence acceptance.
   The tmpfiles fragment creates only the root0700 history directory, never a
   pending marker or replacement lock. Historical original predecessor/backup
   inodes retain their exact0640 root:hfcache metadata and original application
   SID inside private0700; do not recursively restorecon/chmod that history.
   Runtime fcontext `/run/hfcache-host-helper(/.*)?` must be
   `hfcache_host_helper_runtime_t`, including the API subtree. After exact owned
   processes/socket work has drained, inspect any earlier owned
   `/run/hfcache-host-helper/api(/.*)?` rule using `container_file_t` and replace
   that reviewed obsolete rule explicitly. Do not leave an overlapping old rule
   winning at the API path or remove an unknown rule. Apply tmpfiles and restore
   the expected labels on this fixed runtime subtree.
   Preserve protected systemd symlinks and their `systemd_unit_file_t` label.
   The reviewed helper policy must permit only `getattr`/`read` on that type's
   `lnk_file` class so the fixed verifier can validate exact indexed targets.
   A policy change requires a fresh protected installation receipt and both
   deployment/index and permission-policy bindings before restarting the helper.
   Use the shared application-config type only for `/etc/hfcache/config.toml`;
   keep helper policy/index/key/receipt leaves on their private type. Label Hub
   home and the entire `/var/cache/hfcache` root/subtree with the separate
   helper-denied writable Hub-state type. Enabled API helper mounts preserve
   those labels without `:z`; verify both existing and newly created leaf labels
   across actual original application operations and restart. No directory-only
   assertion replaces that proof. Verify original relevant
   payload/secret inode labels, then write the independent protected installation
   receipt before preparing the index. Keep Enforcing. No production archive
   relabel, recursive user-home relabel, `:z` mount flag, allow-all policy or
   label-disable setting is part of this procedure.
   For rootless use, after genuine stock engine/image preparation, independently
   pin and label only the existing `overlay-images/images.lock` and
   `overlay-layers/layers.lock` leaves under the fixed graphroot, plus
   `/run/user/<protected host UID>/libpod/tmp/alive.lck` and
   `/run/user/<protected host UID>/containers/overlay-layers/mountpoints.lock`, with
   `hfcache_host_helper_engine_lock_t`. Require single-link ordinary0644
   service-account-owned files of64B/64B/0B/64B, held-descriptor labeling and
   fixed-path rejoin. Repeat independent provisioning of both runtime locks after reboot
   or recreation and genuine stock engine prewarming. Establish the current
   default temporary-directory/configuration/database epoch independently; the
   fixed-path guard does not authenticate database overrides, and `--tmpdir`
   alone does not prevent them. Nondefault state is unsupported.
   Persistent contexts name exactly these four leaves; do not relabel image payloads
   or grant image-type writes. Absent or wrong/default-type-recreated locks
   require fresh root provisioning and refuse reads meanwhile. The type-only
   receipt is not a historical inode pin; current inspection checks bracket
   changes, not prior otherwise-valid same-type replacements. Include the closed `engine_locks`
   receipt role. Native-only installation has no engine/lock prerequisite.
   Independently provision the separate `engine_shared_memory` role and
   `hfcache_host_helper_engine_shm_t` label on only the existing
   `/dev/shm/libpod_rootless_lock_<protected host UID>` stock2048-lock segment:
   ordinary, single-link, account-owned0600/82488B. Label through its held FD and
   rejoin the fixed path; require exact root:root01777 sticky `/dev/shm`. Repeat
   provisioning after reboot/recreation and genuine stock prewarming. A fixed
   context rule alone does not label a new object. No generic tmpfs relabel,
   creation, engine-backend replacement or ordinary-lock mapping is permitted.
   Include all twelve closed receipt roles. Shared mutex writes are allowed
   coordination; stable identity/label comparison excludes command-wide timestamp
   changes and establishes no content integrity or historical inode identity.
3. Prepare a deployment-index proposal using the selected read-only
   `prepare-host-helper.py` tool and the genuine build receipt's commit, snapshot
   and dirty/clean assertion. Review its measured files, modes, principal and
   profile evidence. Layout or a version string does not prove source identity.
   Install the reviewed index as root:root0644 at the fixed
   `/etc/hfcache/host-helper-deployment.json`; all ancestors must be protected
   local directories. The [schema contract](../host-administration.md) requires
   exact native package leaves/interpreter or original rootless stage plus all
   execution bindings. Index preparation grants nothing and starts no service.
4. Provision `/etc/hfcache/host-helper-policy.json` independently as a single-link
   root:root0600 regular file. Set its `deployment_sha256` to SHA256 of the exact
   reviewed index bytes and provide all six explicit permission booleans.
   On first provisioning, begin with all false; a reviewed configuration-only
   host may set only `configuration` true. For an upgrade or rollback to a target
   with host-reader support, retain the existing reviewed six values while
   rebinding `deployment_sha256` to the exact reviewed target index. Changing a
   permission requires separate authorization. Never infer grants from absent
   guards or migrate the existing Cockpit policy automatically. Only on first
   provisioning, independently create a fresh32-byte random
   `/etc/hfcache/host-helper.key`, root:root0600, using exclusive creation and
   durable write/parent sync. Upgrades and rollbacks preserve the existing key.
   A missing or unsafe key is an operator prerequisite, never something a read
   repairs.
5. Enable the helper configuration only in the reviewed selected profile.
   Native server TOML uses `[host_helper]`, `enabled=true`, `profile="native"`
   and the measured `api_host_gid`, with fixed archive policy path. Rootless
   staging uses the [captured opt-in input](../containers.md), preserving its
   original indexed renderer. Omit the optional deployment SHA from indexed
   templates; the helper's independent boot binding supplies it without a hash
   cycle. Never patch an already indexed rendered server file.
6. Reload/install only within the separately authorized deployment procedure,
   start the helper and observe actual READY before starting/restarting the API.
   API startup pins the protected address parent and deployment. Rootless uses
   only the fixed launcher's API-only read-only directory projection. The client
   traverses with search-only `O_PATH` handles; do not grant directory-read access
   to work around an older client's `O_RDONLY` refusal. Caddy,
   verifier and clients receive neither mount nor attestation. Do not give the
   API root, a manager/engine socket or writable `/etc`.
7. Through the existing trusted Caddy endpoint, sign in and open Administration.
   Verify the measured deployment/policy, explicit permission reasons and fixed
   unit/schedule observations. Test new actions only within their separately
   authorized scope. A successful status is not archive health or a write test.
   Actual native/rootless UID maps, peer identity and isolation must pass before
   calling that installation supported.

The host reader additionally requires the separately installed, enforcing
`hfcache_host_helper_t` SELinux policy from first exec, inherited by every helper
child. Install the exact selected CIL and fixed object labels, then independently
record the actual loaded module/kernel-policy and label facts in root-owned
`/etc/hfcache/host-helper-selinux.json`; the neutral index pins that receipt.
Archive/Hub/credential/container-secret object types must deny helper reads through
aliases as well as direct paths. Retain all masks, capability/namespace limits and
NoNewPrivileges. No policy/label installation or permission grant occurs on a
status read. Unsupported or stale policy/labels refuse. See the
[mandatory SELinux contract](../host-administration.md#mandatory-selinux-isolation).
The selected policy must also allow the trusted system manager to attach the
fixed inaccessible-directory masks and existing writable runtime bind: only
`init_t` directory `mounton` on the custom secret, Hub-state, archive and runtime
types. Keep every bind and label; a namespace setup denial is not a reason to
remove a mask/bind or grant the helper mount or additional runtime rights. Prove
the actual managed exec reaches the required confined domain after setup.
Owned nonsecret alias-denial and full installed API/helper proof remain required;
earlier source/INFO checks alone do not close this requirement.

The fixed rootless network-state directory must already exist under the proved
stock runroot. Its `ifconfig_var_run_t` directory `getattr` permission lets
shared command initialization recognize it; it does not authorize directory
creation, relabeling, enumeration or network setup. Keep the original state and
configuration rather than modifying them to bypass an unavailable read.

Rootless engine inspection initially supports only the measured Podman6.1 stock
storage configuration described in the
[engine configuration contract](../host-administration.md). It verifies the
stock main file and both exact RPM vendor drop-in bundles afresh, preserving
the original overlay/`nodev` configuration and skipping only private-mount
housekeeping. Each vendor directory must contain exactly its pinned leaf with
protected metadata and stable bounded capture; the other seven applicable
configuration/override paths remain absent. Missing/empty vendor bundles,
additional entries or changed inputs produce unavailable status until explicitly
supported. Keep those inputs and report the unsupported revision; do not delete
overrides, replace stock files, change the storage driver or widen mount
permissions to pass a check.

The helper service in initial USER has only account-switch capabilities for
its fixed read-only observer. Only the separate engine child's proved USER
namespace has the retained DAC_READ_SEARCH and SYS_ADMIN execution bits;
their mapped-inode scope and ancillary syscall limits follow
[decision151](../adr/decision-151.md). The service has
AF_UNIX socket authority, a writable owned runtime directory and the
fixed account's local Podman inspection state. It masks archive payloads, Hub
home/cache and credential/secret stores. These restrictions do not widen other
roles. There is no API-selected host path, unit, command or manager.

Normal helper restart replaces only its owned socket/binding leaves in the same
pinned parent. Stale or substituted nodes are preserved and refuse startup:
inspect their original process/boot/inode evidence before any separately
authorized remediation. Never unlink them simply because a timeout occurred.
Replacing the parent, changing the index or rebooting requires a reviewed API
restart. Keep old indexes, keys, bindings and original operation handles through
rollback review; do not remove unknown records to force an older binary to start.

A selector rollback alone does not restore `/usr/local` bootstrap copies. If the
predecessor supports the protected host reader, preserve the current copies and
original inodes before restoring its reviewed matching copies and required labels.
Prepare/review the matching deployment index and independent policy binding before
restarting its helper/API. Retain the reviewed six permission values and original
key; any permission change requires separate authorization.

If the target predates host-reader support, keep the helper stopped and restore a
preserved server configuration accepted by that target. Do not force unsupported
`host_helper` settings or manufacture bootstrap/index support for an older binary.
Retain the helper files, installation receipt, permission policy, key and original
operation evidence for review. In either case, review CIL/module/kernel-policy
compatibility separately; never rewind policy or regenerate a key automatically.

## Connect and rotate safely

Release packaging must place built static assets in the existing pinned UBI 10
micro API image, with no separate frontend image. Caddy owns TLS credentials only.
An accepted native/rootless fixture is evidence for its recorded artifacts and
profile, not permission to change the installed service.

Use a browser that trusts the endpoint certificate. Do not bypass certificate
warnings. The browser's native sign-in dialog asks for the provisioned username
and password. Basic authentication has no reliable application logout. Closing
tabs may leave browser-managed credentials cached; use a dedicated browser
profile on a trusted machine and close the profile/session when finished.

Rotate by creating a new protected record with the same stable subject, delivering
it through the selected profile and performing an authorized drained restart.
Existing browser sessions may keep sending the old password and receive another
challenge. Preserve original operation keys/IDs across rotation or a lost reply;
changing a password is not evidence that an admitted operation stopped. Never
resubmit an uncertain action with a replacement key.

See [login troubleshooting](troubleshooting.md#administrator-login),
[server configuration](../server.md), [security](../security.md) and
[deployment profiles](../deployment-centos-stream-10.md) for the surrounding
operator controls.
