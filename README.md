# hfcache

Archive complete revisions of Hugging Face model and dataset repositories on
NFS-backed ZFS storage, then publish immutable ordinary-file trees that consumers
can copy and independently verify.

Each branch or tag resolves once to a full commit SHA. The writer downloads the
complete snapshot through the official Hugging Face client, hashes newly
introduced content locally, publishes its immutable tree and manifest, then
atomically updates references.
Repository content is data: hfcache never executes or imports it.

Operational CLI commands use an authenticated REST API. An optional read-only MCP
interface exposes archive metadata. Artifact bytes travel through the read-only
NFS export; neither API serves model downloads.

## Start here

| You want to | Guide |
| --- | --- |
| Organize and discover models/datasets | [Tags and local discovery](docs/discovery.md) |
| Inspect an existing archive through its API | [Reader quickstart](docs/quickstart.md) |
| Administer a writer | [Operations](docs/operations.md), [deployment](docs/deployment-centos-stream-10.md) |
| Connect an MCP client | [MCP connection and tools](docs/mcp.md) |
| Copy and verify a model or dataset | [Independent consumers](docs/consumers.md) |
| Use the browser interface | [Web interface and sign-in](docs/web-ui/README.md) |
| Contribute or run tests | [Development](docs/development.md) |
| Find a contract or helper | [Documentation index](docs/README.md), [script reference](docs/scripts.md) |

## Guarantees and boundaries

- Every publication is pinned to an immutable commit and includes every upstream
  file at that commit. There are no include/exclude filters.
- SHA-256 verification of new content precedes publication. Consumers verify the
  complete path set, sizes and hashes again on their own copies.
- Retention defaults to three unique revisions; five is also supported. The
  current revision is protected. Upstream errors or removal from configuration
  preserve local revisions; whole-repository deletion requires explicit review.
- Mutations serialize on a local lock and use durable transaction checkpoints.
  Ambiguous recovery states preserve evidence and require operator action.
- Private and gated repositories require an explicit protected Hub credential.
  All users of the shared export and metadata interfaces must be authorized for
  the whole archive; there are no per-repository ACLs.
- API readers need only a provisioned endpoint and protected REST credential.
  They need no archive mount, archive policy or Hub token. MCP uses a separate
  credential and cannot start jobs or perform integrity verification.

See [architecture](docs/architecture.md), [security](docs/security.md) and
[schemas](docs/schemas.md) for precise guarantees and compatibility domains.

## Installation profiles

| Profile | Requirements and entrypoint |
| --- | --- |
| API reader | Base Python package, verified HTTPS or an authorized Unix socket, protected REST-reader source |
| Native writer | Linux/systemd, managed Python 3.14, NFS archive, separate API/private verifier and protected named credentials |
| Rootless writer | Reviewed pinned UBI 10 micro images with the pinned Python runtime; host orchestration, user systemd services, Caddy TLS and fixed container client |
| Independent consumer | Server-enforced read-only published export and Python standard library; no hfcache installation required |

Select the profile before using an installation helper. The
[deployment guide](docs/deployment-centos-stream-10.md) separates native and
rootless managers, credentials, sockets, upgrades and rollback. The
[storage contract](docs/storage-requirements.md) defines NFSv4.2 semantics,
identity mapping and export protection. Writer preflight refuses a local-directory
archive fallback.

Configured tags and evidence-backed local discovery are available
through REST, CLI and fourteen read-only MCP tools. Explicit offline metadata
refresh uses writer-only keyed operations; reads never load models or contact Hub.
See [discovery](docs/discovery.md) for provenance, incomplete coverage and rollback.

## License

The application is [MIT licensed](LICENSE). Retained adapted recovery code in
the web workspace is LGPL-2.1-or-later; its attribution and full license text are
included in the [shipped notices](web/THIRD_PARTY_NOTICES.txt).
