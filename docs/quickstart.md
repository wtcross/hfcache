# Quickstart: connect to the authenticated API

Use the current CLI against an already provisioned writer API. Reader hosts need
no archive mount, archive TOML, service UID or Hub credential. The CLI never
falls back to local execution or starts a daemon. Use a provisioned endpoint;
reader setup does not initialize or change an archive.

## 1. Install the client environment

From a trusted checkout, the locked base reader environment needs no server or
MCP framework:

```bash
uv sync --locked --no-dev
uv run --locked --no-dev hfcache --help
uv run --locked --no-dev hfcache version
```

Help and local version need no server or credential. A packaged reader may use
an operator-supplied base wheel. A production writer selects its locked `server`
or `server`+`mcp` artifact profile separately. For the complete test environment,
use the [development setup](development.md); installing dependencies starts no
listener.

## 2. Select one endpoint and protected API credential

Ask the operator for the intended API URL or Unix socket, archive UUID and a
protected REST-reader credential file. The credential is not a Hub or MCP token;
no token value belongs in configuration, argv, URLs or browser storage. See the
[protected source rules](server.md#credentials-and-capabilities).

Create `quickstart-client.toml`, substituting the provisioned authority/path/UUID:

```toml
schema_version = 1
api_url = "https://archive.example.com/management"
api_token_file = "/etc/hfcache/api-reader.token"
expected_archive_id = "01234567-89ab-4cde-8fab-0123456789ab"
# ca_file = "/etc/hfcache/archive-ca.pem"
```

For a provisioned **native** authenticated Unix interface, replace `api_url` with
`api_socket = "/run/hfcache/api.sock"`; do not configure both. Use a trusted CA
file for a private certificate, never disable TLS verification. A missing/unsafe
selected credential or unavailable API is an error, not anonymous/local fallback.
[Client settings](api-client.md) define precedence, finite limits and safe URLs.

A shell function keeps the explicit client configuration and arguments separate:

```bash
H() {
    uv run --locked --no-dev hfcache \
        --client-config "$PWD/quickstart-client.toml" --json "$@"
}
H version --server
H status
H list --revisions
H verify --estimate
```

Status, list and estimate read metadata; they do not verify archived bytes or
create confidence. With `--json`, commands return the server schema-1 Envelope.
Inspect `outcome`, `exit_code`, warnings and `data`, rather than HTTP success
alone. No client setting selects a different server archive or grants authority.

For example, these selected fields indicate a successful status query (this is
an illustrative fragment, not a complete response):

```json
{"command": "status", "outcome": "success", "exit_code": 0}
```

Its `data.archive` describes archive health and unfinished work;
a successful query can still report a degraded archive. `H list --revisions`
then shows retained publications, identified by commit SHA and publication ID.
Those identities matter because repair can replace a publication at the same SHA.

## 3. Search and inspect

Keep using the same client configuration and protected reader credential:

```bash
H search --scope configured --tag coding
H search --type model --format gguf --quantization Q4_K_M
H tags --tag-source current_only
H catalog show model:organization/model-name
H catalog variants model:organization/model-name
```

Replace the repository placeholder with a result from your search. Configured
tags include enabled, disabled and unpublished entries. Technical filters need
retained publication observations; incomplete coverage means zero matches do not
prove absence. [Discovery](discovery.md) explains scopes, coverage and predicates.
For usable model files, continue with the independently verified
[consumer copy workflow](consumers.md).

## 4. Jobs and reconnect

A writer uses its distinct provisioned REST-writer source and the same client
contract. Follow [operations](operations.md#resolve-uncertain-work-before-starting-more)
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
observer disappeared. See [uncertain outcomes](recovery.md#preserve-four-kinds-of-authority).

## 5. Optional MCP metadata

MCP requires deliberate server enablement and a separate protected MCP-reader
source; the REST credential above cannot authorize it. The
[protected-file example](mcp.md#connect) uses the
locked SDK and canonical `/mcp/` URL, with finite response/page/deadline bounds.
It returns discovery counts, never file payloads, jobs or complete-copy authority.
Whole-archive restricted metadata is visible to that capability; there is no
repository ACL or OAuth provisioning flow. Copy and promotion still follow the
[consumer contract](consumers.md).

## 6. Provision a writer separately

A disposable development writer still requires a real NFS/NFSv4 mount, its own
archive UUID/paths, protected REST sources, separate server/client settings and
the private verification executor. Use [server/bootstrap configuration](server.md)
and the [deployment checklist](deployment-centos-stream-10.md#acceptance-checklist)
for the actual API/private-worker boundary; reader setup does not create it.
The [recovery rehearsal](recovery.md#rehearse-with-disposable-services)
describes isolated disposable storage with its own identity. Do not create/delete shared `/run/hfcache`, mount/export paths,
state or locks on an existing writer to follow a quickstart.

Writer provisioning requires the relevant operator authority and profile-specific
TLS, credentials, SELinux, NFS, hardening and drain checks. Native and rootless
local client/socket paths are described in [operations](operations.md#choose-the-client-and-authority).
Scheduling is a separate operator decision. These setup procedures are not run
by documentation checks.
