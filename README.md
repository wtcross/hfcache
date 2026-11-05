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
| Use the browser interface | [Web interface, availability and sign-in](docs/web-ui/README.md), [administrator provisioning](docs/web-ui/deployment.md), [migration and rollback](docs/web-ui/migration-and-rollback.md) |
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
| Rootless writer | Reviewed pinned UBI 10 micro images with Python 3.14.6; host orchestration, user systemd services, Caddy TLS and fixed container client |
| Independent consumer | Server-enforced read-only published export and Python standard library; no hfcache installation required |

Select the profile before using an installation helper. The
[deployment guide](docs/deployment-centos-stream-10.md) separates native and
rootless managers, credentials, sockets, upgrades and rollback. The
[storage contract](docs/storage-requirements.md) defines NFSv4.2 semantics,
identity mapping and export protection. Writer preflight refuses a local-directory
archive fallback.

Configured tags and evidence-backed local discovery are available in source
through REST, CLI and fourteen read-only MCP tools. Explicit offline metadata
refresh uses writer-only keyed operations; reads never load models or contact Hub.
See [discovery](docs/discovery.md) for provenance, incomplete coverage and rollback.

## Status

Version **0.3.3** is being prepared to correct bounded original-request review
for larger journal histories. The installed **0.3.2-guarded-readonly** release,
clean source `2d4c9cc`, supplies accessible job readiness, bounded GET-only
recovery and protected rootless writer profiles. Installed read-only and genuine
administrator UI/assets/helper/configuration reads pass. The original request
still needs the accounting correction before review can complete; writer pilots
and bounded metadata backfill remain pending. The archive is read-only.
See [deployment status](docs/deployment-status.md) and
[release notes](CHANGELOG.md) for actual state and acceptance limits.

Owned native/rootless0.3.2 qualification includes actual application writes and
preserving guarded rollback; that evidence retains its original scope.

The following completed0.3.1 acceptance is historical; the active plan records
the current-boot runtime prerequisites. At that acceptance the API, private
worker, Caddy and confined host helper were ready.
Automated installed read-only checks pass verified TLS, REST/MCP credential
separation and the fourteen-tool listing, API-origin worker PROBE, fixed
client version, original-operation observation and recorded confinement.

Genuine trusted-terminal administrator Basic, indexed UI assets, stable bootstrap
identity, API-origin helper status and managed configuration reads pass in
11 GETs, all HTTP 200, over verified TLS with the original permissions preserved.
This validation runs no browser JavaScript, Apply, job or NAS workload.

The retained predecessor is **0.3.0**, clean source `3d6670d`; older immutable
rollback artifacts and original operation evidence remain preserved. No
archive, configuration, API, operation or receipt format changes in 0.3.1.

The deliberate inactive guard setting is restored through reviewed
zero-executor handoff; no domain-lock holder is intentionally retained.
The reviewed graceful restart and repeated automated checks pass.
The explicit local publication scope retains the no-tag instruction: 0.3.1
has no new release tag. Exact source/artifact identities identify this
selection; existing tags remain unchanged.

The archive remains read-only with writers and calendars disabled. See
[recorded deployment scope](docs/deployment-status.md) and
[migration and rollback](docs/web-ui/migration-and-rollback.md) for actual
acceptance, preserved state and remaining boot/NAS/other-host holds.

## Repository layout

| Path | Contents |
| --- | --- |
| `src/hfcache/` | Archive services, HTTP client, CLI and optional REST/MCP transports |
| `docs/` | Human guides, technical contracts and architectural rationale |
| `web/` | Independent React/TypeScript interface, frozen build inputs and bundled browser assets |
| `packaging/` | Native and container units, configuration, image inputs and runtime templates |
| `scripts/` | Reviewed build, install, diagnostic, test and consumer helpers; [complete catalog](docs/scripts.md) |
| `examples/` | Archive policy, independent copy helper and protected-file MCP client |
| `tests/` | Offline unit fixtures, explicit opt-in system tests and schema goldens |

## Development

From a trusted checkout, install the complete locked test environment:

```bash
uv sync --locked --extra server --extra mcp
scripts/check.sh
```

The gate includes format, lint, types, offline tests, build and three isolated
installation profiles. Use `scripts/check.sh --require-web --with-build` for
strict web UI and wheel validation. [Development instructions](docs/development.md)
describe safe examples, build smoke tests and separately authorized live/NFS work.

## License

The application is [MIT licensed](LICENSE). Retained adapted recovery code in
the web workspace is LGPL-2.1-or-later; its attribution and full license text are
included in the [shipped notices](web/THIRD_PARTY_NOTICES.txt).
