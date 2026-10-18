# Development and validation

Use the pinned Python and `uv.lock`. Install both optional transport extras
for the complete offline suite:

```bash
uv sync --locked --extra server --extra mcp
scripts/check.sh
scripts/check.sh --with-build
```

The base reader uses `uv sync --locked --no-dev`; a REST-only writer selects
`--extra server`, and an MCP-enabled writer selects both extras. These installation
profiles do not change the complete test-collection requirement above. Host
bootstrap helpers support Python 3.12; the application uses the pinned 3.14 line.
See the [script reference](scripts.md) for each helper’s dependencies and effects.

## Quality gate

The provider-neutral gate checks the lock, synchronizes the locked environment,
checks Ruff formatting and lint, checks Pyrefly types, validates documentation,
runs offline pytest,
builds the distribution and smoke-installs locked base, server and
server-plus-MCP wheels. With pnpm and make it also runs the Cockpit frozen
install, lint, tests and production build. A skipped Cockpit stage does not
validate plugin changes. `--with-build` adds isolated wheel-install tests.

Application safety checks raise exceptions instead of relying on assertions.
Keep durable-format golden fixtures and checkpoint-contract tests synchronized
with their contracts. Specialized test dependencies require a concrete test
that cannot be expressed cleanly with pytest fixtures and deterministic doubles.

## Offline tests

The default suite is hermetic and removes ambient Hub credentials. Inject a
fake Hub adapter; do not patch client internals or depend on external services.
Cover strict configuration, credential scope, identifiers and duplicates,
paths and sentinel/mount checks, traversal and symlinks, deterministic schemas,
streaming SHA-256 and digest reuse, dependency warnings, atomic references,
retention and publication generations (including gaps and repair preservation),
current protection, over-retention on failure, journal validation/idempotence,
every recovery state, containment, unknown-file preservation, exit aggregation
and redaction. Property tests cover safe paths, retention order, duplicate SHA
observations, journal combinations and preservation of the current revision.

Integration fixtures cover first sync, skips, new publications, accumulation
and rotation at the configured retention limit, upstream 403/404 preservation,
incomplete download, every publication/prune boundary, reference and catalog
reconstruction, dry-run/apply recovery, unknown versions and ambiguous journals,
hardlink and explicit copy publication, public cache deletion, shared-inode
verification, missing/extra/replaced/corrupt files and partial multi-repository
failure. Repair covers both reference switches, grace retention and idempotent
cleanup. HTTP, Unix/TLS, authentication, pagination, receipts, no replay and MCP
use owned fixtures.

## Failure injection

At every point below, the previous current revision must remain usable and no
retained verified revision may be accidentally destroyed. The executable map
in `tests/unit/test_failure_matrix.py` names covering tests and checks they
exist. Its comments distinguish incomplete-transfer fixtures from killing an
actual network transfer.

| Injection point |
| --- |
| before download |
| mid-download |
| after download, before hash completion |
| during manifest creation |
| during staging publication |
| after revision rename, before ref replacement |
| after ref replacement, before pruning |
| during publication-tree removal |
| during hub cache cleanup |
| before and between repair ref replacements |
| during quarterly verification |

## Opt-in and installed acceptance

Live Hub tests use small public model and dataset repositories: resolve a
moving branch, download every file at its SHA, check local-only completeness,
publish/verify, then prove a second unchanged sync avoids download. Select with
`pytest -m live`; external availability never gates the default suite.

NFS tests (`pytest -m nfs`) require an authorized disposable dataset. Prove
hardlinks, atomic rename/reference replacement, racing current readers always
seeing complete trees/manifests during publication and repair, consumer copies
across repair switches and grace expiry, safe retry after expiry,
interruption/restart, no local-root fallback, service-umask readability,
Mapall/shared-group behavior and server denial of consumer create/modify/rename/
delete. Measure download, hash, copy and verification throughput. Network
disruption and reboot tests need a separate operator window.

Installed acceptance checks clean installation and locked Python, unit
verification output, profile-specific target lifecycle, NAS-unavailable boot
with visibly failed archive work, timer persistence, Enforcing SELinux without
unexplained AVCs, DNS/TLS/NFS/hash/Xet under hardening, and rollback. Inspect the
actual verifier's no-IP and credential masks, actual API-container peer access,
TLS/firewall and state-retaining drain. Repository tests cannot supply those
observations. See [recorded deployment restrictions](deployment-status.md).

## Examples and documentation

Keep human navigation in the [documentation index](README.md). Verify links and
anchors, strict configuration examples, actual REST routes/CLI modes, mounted MCP
tools, role boundaries and script catalog coverage with the offline suite.

Examples are reviewed individually. Shell recipes are syntax-checked; operational
CLI examples are parsed without invoking callbacks. The protected-file REST/MCP
clients run only against synthetic transports. The independent copy helper runs
against owned temporary publication trees, including corrupt and mismatched
evidence. Never execute every example or code fence: installation, image builds,
probes, mounts, service changes and serving workloads have real effects. Safe help
checks use an explicit inventory and must precede runtime/credential access.

Run documentation validation directly with:

```bash
uv run --locked --extra server --extra mcp python scripts/check-docs.py
```

It discovers human Markdown throughout the repository, validates rendered local
links and anchors, checks audience boundaries and requires each helper exactly
once in the catalog with an explicit inspection classification. Generated build,
cache, vendor and ignored session-scratch trees are excluded; architectural
records and newly added human guides are included. It uses the existing locked
Markdown parser, reads repository files only and executes no snippets. The test
suite additionally compares published defaults/ranges to strict models, actual
routes to the REST matrix, mounted tools to their names/argument fields, and role
settings to real launcher arguments. Bad-fixture tests prove failures, including
missing helpers, malformed references and changed numeric defaults/bounds.

Edit human reference tables and their governing source together. Keep independent
route/tool expectations: regenerating a table must not weaken the tests that
check its completeness, authorization or side effects.
