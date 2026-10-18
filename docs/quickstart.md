# Quickstart: connect to the authenticated API

Use the current CLI against an already provisioned writer API. Reader hosts need
no archive mount, archive TOML, service UID or Hub credential. This page replaces
the old direct-backend/loopback-NFS command sequence: operational `--config`
overrides are now refused, and the CLI never falls back to local execution or
starts a daemon. The examples below are setup instructions, not commands run on
the production writer.

## 1. Install the client environment

From a trusted checkout, the development environment includes every implemented
extra so the documented examples and offline tests share one locked environment:

```bash
uv sync --locked --extra server --extra mcp
uv run --locked --extra server --extra mcp hfcache --help
uv run --locked --extra server --extra mcp hfcache version
```

Help and local version need no server or credential. A deployed reader can use
the base wheel without either optional framework; a production writer selects
its deliberate locked `server` or `server`+`mcp` artifact profile separately.
Development selection alone starts no listener and deploys nothing.

## 2. Select one endpoint and protected API credential

Ask the operator for the intended API URL or Unix socket, archive UUID and a
protected REST-reader credential file. The credential is not a Hub or MCP token;
no token value belongs in configuration, argv, URLs or browser storage. See the
[protected source rules](server.md#implemented-credential-and-capability-boundary-api-005).

Create `quickstart-client.toml`, substituting the provisioned authority/path/UUID:

```toml
schema_version = 1
api_url = "https://archive.example.com/management"
api_token_file = "/etc/hfcache/api-reader.token"
expected_archive_id = "01234567-89ab-4cde-8fab-0123456789ab"
# ca_file = "/etc/hfcache/archive-ca.pem"
```

For the local authenticated Unix interface, replace `api_url` with
`api_socket = "/run/hfcache/api.sock"`; do not configure both. Use a trusted CA
file for a private certificate, never disable TLS verification. A missing/unsafe
selected credential or unavailable API is an error, not anonymous/local fallback.
[Client settings](api-client.md) define precedence, finite limits and safe URLs.

A shell function keeps the explicit client configuration and arguments separate:

```bash
H() {
    uv run --locked --extra server --extra mcp hfcache \
        --client-config "$PWD/quickstart-client.toml" --json "$@"
}
H version --server
H status
H list --revisions
H doctor --read-only   # admitted reader job; may contact Hub via installed credentials
H verify --estimate
```

Status/list/estimate are metadata reads; estimates do not verify archived bytes
or create confidence. `doctor --read-only` is an admitted reader diagnostic job
that may contact Hub using installed credentials, creates an operation receipt
and performs no write probes. Its key/operation notices appear before the exact
terminal result. Domain output is the exact server schema-1 Envelope, including
failures, IDs and times. Do not infer integrity merely from HTTP success. No
client setting selects a different server archive or grants write authority.

## 3. Writer work and reconnect

A writer uses its distinct provisioned REST-writer source and the same client
contract. Follow [operations](operations.md#cli-submit-and-reconnect-api-013)
for authorized plan/sync/verification/maintenance work on the intended target.
Writer capability does not bypass common locks, fresh scope/evidence checks,
private verification or explicit initialization guards. No archive mutation is needed
to try the reader commands above; never initialize an existing archive.

Submission prints its validated key before POST and accepted operation ID before
waiting, even in quiet mode. Keep both if the client times out or disconnects;
accepted work may continue. An authorized reader or writer can observe a known
operation ID; key lookup additionally requires the original credential class:

```bash
H operations show -- '<operation-id>'
H operations wait -- '<operation-id>'
# Only when H selects the same class that submitted the original request:
H operations lookup -- '<original-key>'
```

Replace the quoted placeholders with retained handles; keep `--` so a key cannot
be parsed as an option. Missing/expired history does not prove nonexecution.
Do not replay with a new key, cancel execution or run recovery because an
observer disappeared. See [uncertain outcomes](recovery.md#10-operation-history-and-uncertain-submissions).

## 4. Optional MCP metadata

MCP requires deliberate server enablement and a separate protected MCP-reader
source; the REST credential above cannot authorize it. The
[protected-file example](mcp.md#protected-file-example-client-mcp-004) uses the
locked SDK and canonical `/mcp/` URL, with finite response/page/deadline bounds.
It returns discovery counts, never file payloads, jobs or complete-copy authority.
Whole-archive restricted metadata is visible to that capability; there is no
repository ACL or OAuth provisioning flow. Copy and promotion still follow the
[consumer contract](consumers.md).

## 5. Provision a writer separately

A disposable development writer still requires a real NFS/NFSv4 mount, its own
archive UUID/paths, protected REST sources, separate server/client settings and
the private verification executor. Use [server/bootstrap configuration](server.md)
and the [deployment checklist](deployment-centos-stream-10.md#17-rest-and-mcp-rollout-checklist-api-017)
for the actual API/private-worker boundary; reader setup does not create it.
The [recovery rehearsal](recovery.md#6-building-a-throwaway-archive-to-rehearse-on)
retains the historical disposable-storage context, not permission to touch a
production mount. Do not create/delete shared `/run/hfcache`, mount/export paths,
state or locks on an existing writer to follow a quickstart.

Production rollout, credentials/TLS/firewall, actual worker no-IP/source masks,
SELinux/NFS/hardening and drain/rollback require separate operator acceptance.
The verification timer remains disabled pending calendar approval. This guide
performs no host setup, archive operation, release, deployment or cleanup.
