# Provision browser administrator access

This describes the unreleased optional authentication provider. Installed systems
still use their recorded release and Cockpit. The application does not yet serve
`/ui/`; authenticated static serving follows separately. Do not change a running
installation merely to try the developer preview. See
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

## Connect and rotate safely

The final UI will use `/ui/` or the configured prefix followed by `/ui/`, through
the same existing Caddy TLS endpoint and Unix API upstream as REST/MCP. Keep
Basic verification in the application; do not add a Caddy-wide Basic gate,
frontend server, public listener or Node runtime. Static assets will ship in the
existing pinned UBI 10 micro API image. Caddy owns TLS credentials only.

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
