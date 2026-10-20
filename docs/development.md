# Development and validation

## Browser authentication fixture

`uv run --locked --extra server --extra mcp python scripts/check-web-auth-fixture.py --help`
is safe inspection. Running the check requires a separately provisioned disposable
guest and an explicit protected manifest; it never discovers a live installation
or downloads missing dependencies. Run it inside that guest with
`--manifest ABSOLUTE_PROVISIONED_JSON` using the installed-wheel environment.
The manifest binds exact source inventory, wheel/installed package bytes,
private TLS fixture, numeric loopback origins and fixed offline browser launcher.
Provision pinned Node24.18.1 and Playwright1.64.1 package/browser closure first.
Missing engines, wrong ownership/hashes or unsupported trust are failures.

The check runs Chromium, Firefox and WebKit sequentially for root and
`/management` paths. Native `httpCredentials` handles the actual first401 challenge
and retry; page scripts never receive the password. It verifies trusted TLS and
untrusted-CA refusal, authorized same-origin reads/JSON POST and real foreign-origin
form/text/multipart/preflight refusal. No `Authorization` injection, ignored TLS
errors, browser sandbox disablement or network pull establishes acceptance.
Reports retain exact engine versions, case outcomes, artifact identities and
observed browser/API drain. Test passwords remain in memory/owned pipes; do not
enable traces/HAR or record credential headers. The fixed launcher uses rootless
non-root browser tooling entirely inside the owned CentOS guest; any host-network
mode refers only to that guest's isolated loopback. Keep SELinux/seccomp active.

This mandatory authentication subset accompanies the complete source gate.
The required source gate also runs `pnpm --dir web run test:auth-sandbox`, bounded
Node metadata/drain unit tests whose retained TAP must show a positive all-pass
count and zero failures, cancellation, skips or TODOs. Those tests supplement the
actual browser sandbox proof; fabricated process metadata cannot establish it.
It proves direct API TLS/authentication; shared-Caddy and complete installed
UI/platform acceptance follow with authenticated static serving. Synthetic fixture
storage supplies no live NAS evidence. Preserve failed workspaces and original
operation handles; never drain or reuse an older unknown guest.

## Python development environment

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
Use `scripts/check.sh --require-cockpit` for plugin work and acceptance that needs
frontend coverage. It refuses missing plugin sources, pnpm or make before
running the backend checks, and never accepts a skipped frontend stage. Combine
it with `--with-build` when both gates are required. Firefox remains mandatory
for the executed frontend tests; its absence fails that stage. The default mode
retains its loud toolchain skip for backend-only development; that result is not
plugin proof.

Use `scripts/check.sh --require-web --require-cockpit` for replacement web
interface work. `--require-web` first requires the web package manifest, frozen
pnpm lock, TypeScript configuration, Node and pnpm. It checks the authoritative
Python contract export after locked Python synchronization, then retains every
backend and applicable Cockpit check above. Its web stage runs frozen
installation, then `check:wire`, lint, types, deliberately
invalid strictness fixtures, `test:auth-sandbox`, unit tests, component tests,
a production build and the preliminary real-browser smoke in that order.
The real API React read fixture follows those checks.
Any failed stage or missing required browser fails the gate. Backend-only mode
prints an explicit web omission; that result does not validate the web interface.

The installed application/platform functional runner is not available yet.
`--with-web-functional` is currently an unknown argument and exits nonzero;
the preliminary browser smoke does not establish Caddy, authentication, API,
worker, helper or installed native/rootless acceptance.

Application safety checks raise exceptions instead of relying on assertions.
Keep durable-format golden fixtures and checkpoint-contract tests synchronized
with their contracts. Specialized test dependencies require a concrete test
that cannot be expressed cleanly with pytest fixtures and deterministic doubles.

## Web workspace

The replacement interface has a separate [web package](../web/package.json)
and frozen [pnpm lock](../web/pnpm-lock.yaml). Node and pnpm are build/test
tools only. Base Python wheel builds and reader/server installations do not
invoke Node or install frontend dependencies. Production serving remains owned
by the application behind its existing Caddy endpoint; the preliminary test
server is an owned loopback fixture only.

| Tool | Selected version |
| --- | --- |
| Node / pnpm | `24.18.1` / `11.18.0` |
| React / React DOM | `18.3.1` |
| TypeScript | `6.0.3` |
| Vite / React plugin | `8.3.4` / `6.1.2` |
| ESLint / JavaScript rules / typescript-eslint | `10.13.0` / `10.0.1` / `8.63.0` |
| Vitest / V8 coverage | `5.0.5` |
| React Testing Library / user-event / jsdom | `16.3.3` / `14.6.8` / `30.1.3` |
| Playwright | `1.64.1` |
| axe Playwright integration / axe-core | `4.14.0` |
| Prettier | `3.9.10` |

The package manifest and lock contain the complete direct/transitive selection.
The workspace enables strict engine and peer checks; incompatible Node/pnpm
versions and unresolved peer requirements fail installation.
Keep the [license inventory](../web/dependencies/licenses.json) and
[third-party notices](../web/THIRD_PARTY_NOTICES.txt) synchronized with changes;
browser libraries become shipped static assets, while lint/test/browser tools
remain development dependencies. Preserve any reused Cockpit LGPL notices.
After changing the lock, refresh the inventory explicitly with
`pnpm --dir web exec node scripts/licenses.ts --refresh`. This contacts the
registry for exact locked versions, including optional packages for other
platforms, and retains actual bundled license texts. Review the resulting
inventory and notices. `pnpm --dir web run licenses` checks their frozen-lock
binding offline; the production build also performs that check.
Generated Unicode data has its own [reviewed source record](../web/dependencies/unicode.json)
and [Unicode license](../web/dependencies/UNICODE-LICENSE.txt), separate from the
npm package inventory. `pnpm --dir web exec node scripts/licenses.ts --refresh-notices`
rebuilds notices offline from already reviewed package/data inputs; it does not
refresh the registry inventory or approve changed Unicode data.

Provision dependencies explicitly before running offline validation. From the
repository root, run frozen installation twice to check that the resolved lock
remains unchanged, then provision the pinned preliminary Chromium binary into
the owned web cache:

```bash
pnpm --dir web install --frozen-lockfile
pnpm --dir web install --frozen-lockfile
PLAYWRIGHT_BROWSERS_PATH="$PWD/web/.cache/ms-playwright" pnpm --dir web exec playwright install chromium
```

Browser provisioning downloads test dependencies; validation never downloads a
missing browser or invokes a system dependency installer. Missing host libraries
are a prerequisite failure to resolve in a suitable owned test environment.
Keep browser caches, coverage, traces and build output in ignored web artifact
directories: `web/.cache/`, `web/coverage/`, `web/.artifacts/` and `web/dist/`.
The documentation checker excludes these exact generated roots while continuing
to check web source guides. Do not commit dependency trees, `dist/` or private
browser profiles.

Run individual stages with:

```bash
pnpm --dir web run lint
pnpm --dir web run typecheck
uv run --locked --extra server --extra mcp python scripts/export-web-contracts.py --check
pnpm --dir web run check:wire
pnpm --dir web run test:strict-fixtures
pnpm --dir web run test:unit
pnpm --dir web run test:component
pnpm --dir web run build
pnpm --dir web run test:browser
uv run --locked --extra server --extra mcp python scripts/check-web-read-fixture.py
scripts/check.sh --require-web --require-cockpit
```

Strict fixtures must demonstrate that unsafe assignments and deliberately invalid
TypeScript fail validation. Unit/component coverage includes all new source and
requires at least 90% lines and 85% branches. `test:unit` runs the isolated utility
project; `test:component` runs both projects together with enforced coverage.
The existing Python coverage policy is unchanged. Component fixtures may control
their own external boundaries, but
cannot establish authenticated or installed behavior.

Required test wrappers reject empty, skipped, pending, todo or inconsistent
reports. Retries are disabled; browser reports must show one passing execution
per test. A timeout fails even if the child leaves a positive report and exits
zero. Each run retains its evidence under `web/.artifacts/unit-*/`,
`component-*/` or `browser-*/`; retain failed reports and screenshots when
investigating a later passing run.
Component coverage is retained in each run's `component-*/coverage/` directory,
so a later run cannot overwrite its coverage evidence.

`test:browser` exercises the production-built shell and keyboard navigation in
the pinned Chromium on an owned loopback fixture, including desktop/mobile axe
scans and semantic navigation checks. It retains an explicit
development-preview status and makes no API, archive or credential request.
The wrapper owns the sandboxed Chromium process and loopback listeners, closes
them on success or failure and waits for the exact browser process to exit.
Failed or timed-out cleanup fails the check; preserve its evidence for diagnosis.
Missing browser prerequisites fail rather than skip. This preliminary smoke does
not replace the later Chromium, Firefox and WebKit workflows through real Caddy
and installed native/rootless services. See [UI availability](web-ui/README.md)
for the current user-facing status.

### Generated browser contracts

The browser's wire boundary is generated from the Python public models and the
precise [route registry](../src/hfcache/wire_registry.py), including payloads
that the generic OpenAPI Envelope cannot describe. The
[exporter](../scripts/export-web-contracts.py) reads code/models only; it never
starts the application, loads installed policy or accesses an archive. Its
schema IR is committed at `web/src/wire/contracts.json`; the exporter also writes
its sibling `unicode-data.json`. The TypeScript generator produces
`web/src/wire/generated.ts`. Check mode is the default and writes nothing.

After deliberately changing an authoritative DTO or an audited semantic rule,
regenerate explicitly, review both diffs and run the independent wire tests:

```bash
uv run --locked --extra server --extra mcp python scripts/export-web-contracts.py --write
pnpm --dir web run generate:wire
uv run --locked --extra server --extra mcp python scripts/export-web-contracts.py --check
pnpm --dir web run check:wire
pnpm --dir web run test:unit
pnpm --dir web run test:component
```

Unknown schema constructs, validators and serializers refuse export. Reviewing a
new semantic hook includes its TypeScript implementation and independent negative
fixtures; updating a hash alone is insufficient. Outputs require serialized
fields rather than fill Python defaults. Inputs preserve omission versus null.
Array bounds are checked against authoritative tuple fields, and numeric bounds
remain decimal strings until checked. The runtime reconstructs typed values from
unknown input and checks named semantic/cross-response rules. It never asserts
that arbitrary JSON is a domain payload.

Native JSON reviver source context is a browser prerequisite. Exact raw integer
tokens are checked before Number conversion; unsupported source context, duplicate
decoded keys, malformed UTF-8, lone surrogates, excessive work or unsafe integers
produce a classified protocol failure. The [API reference](api.md#browser-wire-boundary)
lists the independent browser byte/work ceilings. Do not add a rounded-number or
unchecked JSON.parse fallback to support an older engine.

Path collision rules use the pinned Python Unicode 16 authority, even when an
engine carries a newer Unicode release. The [pure table exporter](../src/hfcache/wire_unicode.py)
and browser NFC/full-casefold implementation retain the archive's exact rules.
Python printability uses pinned exclusion ranges too, so newer engine assignments
cannot broaden compatibility-only request validation.
Official Unicode normalization and full/common casefold vectors are preserved
byte-for-byte in compressed fixtures under `tests/fixtures/unicode16/`, with
source URLs, hashes and licensing. Their tests run offline. The generated JSON
artifacts keep their canonical exporter format rather than Prettier formatting;
source checking and regeneration drift still apply. Updating Python's Unicode
version requires explicit table/semantic/license review and conformance tests.

The [real API read fixture](../scripts/check-web-read-fixture.py) compiles a
test-only entry importing the actual React component/client, starts the real
application on an owned loopback socket and runs sandboxed Chromium. It uses only
generated private credentials and synthetic local state. Version, capabilities,
status and genuine failed inspection/API-problem responses cross the real service
boundary. A labelled post-service corruption fault checks unknown-schema handling;
that negative fault does not replace the real-route positives. The fixture
retains unique logs, source/artifact identities and browser reports under
`.scratch/`; it observes exact browser/API shutdown. A caller-supplied workspace
must be a new owned descendant of `.scratch/`. Missing prerequisites or uncertain
drain fail. No dependencies download during validation.

The required web gate runs Python export drift before backend validation, checks
TypeScript generation after frozen install and runs the real read fixture after
the preliminary built-shell smoke. This fixture uses temporary test routing
before normal authenticated static serving. It establishes the wire/presentation
boundary only; it does not replace same-Caddy/TLS, Basic or installed native/
rootless acceptance. The [troubleshooting guide](web-ui/troubleshooting.md)
explains the visible read states.

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

The extended build gate also exercises actual installed pre-feature wheels from
retained Git source objects against disposable catalog compatibility fixtures.
It requires the complete repository history for those targets and their locked
base/server/MCP dependency closure in uv's offline cache. Installed package bytes
are compared with the selected old sources before behavior is tested. Synthetic
mount tables and temporary state establish only offline behavior; no archive
initialization command, real mount, service, credential or Hub workload is used.


The Cockpit test command includes actual mounted React tests in
`/usr/bin/firefox` with fresh temporary profiles and owned loopback fixtures.
Firefox must be present for an executed frontend gate; absence fails rather than
silently skipping those tests. The fixtures control Cockpit's process/D-Bus and
privilege event boundaries, never access the installed archive or credentials,
and add no shipped browser dependency. Real Cockpit/PAM/systemd/rootless acceptance
requires a separately provisioned isolated environment and remains distinct.
