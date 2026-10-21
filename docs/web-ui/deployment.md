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
