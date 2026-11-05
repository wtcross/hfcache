# Development and validation

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
runs offline pytest, builds the distribution and smoke-installs locked base,
server and server-plus-MCP wheels. `--with-build` adds isolated wheel-install
tests. The current browser workspace is validated through the required web
checks below.

Use `scripts/check.sh --require-web --with-build` for web interface
validation. `--require-web` first requires the web package manifest, frozen
pnpm lock, TypeScript configuration, Node and pnpm. It checks the authoritative
Python contract export after locked Python synchronization, then retains every
backend check above. Its web stage runs frozen
installation, then `check:wire`, lint, types, deliberately
invalid strictness fixtures, `test:auth-sandbox`, `test:functional-metadata`, unit tests, component tests,
a production build, the built source-fixture browser workflows and an actual
200% Chromium zoom workflow in that order. The zoom workflow uses a temporary
owned profile and extension with the provisioned full Chromium binary; it
confirms browser zoom through the browser API and closes its exact owned process.
It changes no product read bound, persistent preference or user browser profile.
The real API React read fixture follows those checks.
Any failed stage or missing required browser fails the gate. Backend-only mode
prints an explicit web omission; that result does not validate the web interface.

The full source gate and installed workflow acceptance are separate requirements.
The preliminary browser smoke does not establish real Caddy authentication, API,
worker, helper or installed native/rootless behavior. Exercise those boundaries
against the selected built release as described below.

`--with-web-functional` is an optional instrumented diagnostic. It implies
`--require-web` and invokes the existing runner with all profiles and `--final`;
its strict case, cell, fixture and proof validators are unchanged. Set
`HFCACHE_WEB_FUNCTIONAL_MANIFEST` to the explicit absolute protected fixture
manifest path; there is no ambient fixture discovery or credential environment
input. Missing provisioned prerequisites fail before the source gate. Direct
installed acceptance does not claim that this optional command passed.

Application safety checks raise exceptions instead of relying on assertions.
Keep durable-format golden fixtures and checkpoint-contract tests synchronized
with their contracts. Specialized test dependencies require a concrete test
that cannot be expressed cleanly with pytest fixtures and deterministic doubles.

## Web workspace

The web interface has a separate [web package](../web/package.json)
and frozen [pnpm lock](../web/pnpm-lock.yaml). Node and pnpm are build/test
tools only. Base Python wheel builds and reader/server installations do not
invoke Node or install frontend dependencies. Production serving remains owned
by the application behind its existing Caddy endpoint; the preliminary test
server is an owned loopback fixture only.

| Tool | Selected version |
| --- | --- |
| Node / pnpm | `24.18.1` / `11.18.0` |
| React / React DOM | `18.3.1` |
| React Markdown / remark-gfm / rehype-sanitize | `10.1.0` / `4.0.1` / `6.0.0` |
| TypeScript | `6.0.3` |
| Vite / React plugin | `8.3.4` / `6.1.2` |
| ESLint / JavaScript rules / typescript-eslint | `10.13.0` / `10.0.1` / `8.63.0` |
| Vitest / V8 coverage | `5.0.5` |
| React Testing Library / user-event / jsdom | `16.3.3` / `14.6.8` / `30.1.3` |
| Playwright | `1.64.1` |
| axe Playwright integration / axe-core | `4.14.0` |
| Prettier | `3.9.10` |

[Decision155](adr/decision-155.md) records the bundled Markdown/GFM/sanitizer
selection and its closed rendering/work policy. Provision and audit its exact
closure explicitly before offline validation; source strings cannot request
plugins or network-loaded dependencies. Markdown is lazy-loaded; deployment
still needs no Node. The package manifest and lock contain the complete
direct/transitive selection.
The workspace enables strict engine and peer checks; incompatible Node/pnpm
versions and unresolved peer requirements fail installation.
Keep the [license inventory](../web/dependencies/licenses.json) and
[third-party notices](../web/THIRD_PARTY_NOTICES.txt) synchronized with changes;
browser libraries become shipped static assets, while lint/test/browser tools
remain development dependencies. Preserve the LGPL notices for retained adapted
code. The application-owned recovery registry is a local LGPL-2.1-or-later
adaptation. Its reviewed local-source provenance and full LGPL text are included
in the shipped notices; the workspace license is `(MIT AND LGPL-2.1-or-later)`.
This adds no npm package or separate runtime bridge. The npm closure retains
reviewed package-specific licenses: MIT packages and the exact ISC-licensed `@ungap/structured-clone@1.4.0`
are recorded with full texts in the inventory and shipped notices.
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
pnpm --dir web run test:library-zoom
uv run --locked --extra server --extra mcp python scripts/check-web-read-fixture.py
scripts/check.sh --require-web
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

`test:browser` exercises the production-built startup refusal and inert fallback
in pinned Chromium on an owned loopback fixture, with desktop/mobile axe scans
and a keyboard-accessible reload link. No successful bootstrap or connected
domain values are fabricated: one route returns no bootstrap, and another
deliberately lacks its main JavaScript chunk. Both must preserve useful HTML
without mounting the authenticated application. There is no archive or
credential request.
The wrapper owns the sandboxed Chromium process and loopback listeners, closes
them on success or failure and waits for the exact browser process to exit.
Failed or timed-out cleanup fails the check; preserve its evidence for diagnosis.
Missing browser prerequisites fail rather than skip. This preliminary smoke does
not replace the later Chromium, Firefox and WebKit workflows through real Caddy
and installed native/rootless services. See [UI availability](web-ui/README.md)
for the current user-facing status.

### Clean backend/UI/helper release construction

Use [build-web-release.py](../scripts/build-web-release.py) from a clean worktree
at the exact reviewed commit, preferably a detached build worktree. Keep output
outside that worktree on local storage, and run as the login builder:

```bash
uv run --locked --extra server --extra mcp python scripts/build-web-release.py \
  --output /var/tmp/hfcache-web-release
```

The output directory must be new. The builder freezes `SOURCE_DATE_EPOCH` to the
commit time, runs locked Python/frozen pnpm installation, builds a wheel/source
distribution and UI, validates the original Python UI schema, then repeats the UI
build and compares the manifest and every member byte. Dirty source or source
changes during construction refuse. It captures the committed source into
`source/` and artifacts into `wheels/`, `ui/` and `host-helper/`, with build logs
and canonical `web-release.json`. Keep the printed index/UI-manifest SHA256 values
with the release inventory. Failed output remains for diagnosis; use a new
directory for another attempt.

The existing UI manifest binds the prebundle input snapshot, application/wire/UI
schema, frozen pnpm lock, exact Node/pnpm/TypeScript/Vite versions and shipped
license inventory/notices. The outer release index binds the committed source,
backend artifacts, complete UI and fixed protected-helper closure. This build
does not read credentials or the archive, access managers/containers, select
`current` or activate a policy. Normal `uv build` and base/server/server+MCP wheel
installation remain Node-independent.

Native staging requires both `--web-release` and `--web-release-sha256` with
`HFCACHE_SOURCE` set to the captured source. Rootless app image construction uses
both `--web-assets` and `--web-manifest-sha256`; static assets join the existing
pinned UBI 10 micro API image. Its foundation probe checks actual ordered base
ancestry, image size and runtime tool absence. Image recipes/labels, dirty
fixtures and component tests do not establish clean-release or installed browser
acceptance. See the [operator procedure](web-ui/deployment.md#build-and-select-a-clean-release)
for explicit optional enablement, Basic provisioning and separate host-helper
installation. Use the documented owned functional manifest and all three engines
for installed acceptance; no source build grants production rollout authority.

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

The Library composes these existing typed GETs through the shared query store.
Its bounded filter fragments stay under the fixed shell route; only allowlisted
catalog predicates enter API query strings. Preserve raw bounded Unicode search
for server matching, exact repository type/ID joins, full publication-qualified
size facts, complete coverage and explicit page/facet extent. An unavailable or
stale join is not zero, a global total or permission to issue another request
without a bound. Dataset changes must visibly clear model-only filters.

Independent Library fixtures should exercise configured disabled/unpublished and
unmanaged archived repositories, identical IDs across types, historical tags,
same-variant conjunction, incomplete zero-known-match results, changed current
pairs and curation-only stale cursors. Three-browser installed workflows must
follow the [human guide](web-ui/library.md) through the real Caddy/API, including
filter bookmarks and explicit paging, while retaining network/closure proof.
Design-reference screenshots and synthetic fixture labels are illustrative;
they are never measurements or installed acceptance by themselves. No hidden
all-page collector, new endpoint, writer/Hub dispatch or runtime dependency is
needed for this composition.

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
boundary. A finite query-pool scenario runs 100 refresh/handle cycles through the
actual typed client, query store, shared two-read coordinator and encoded-retention
budget. Delayed genuine service replies expose their real headers before body
delivery; cancellation and authority retirement then prove late-body fencing.
Explicit post-service faults check unknown schema, oversize and unsafe-integer
refusal; those negative faults do not replace the real-route positives. Encoded
retention observations measure neither browser heap nor installed route churn.
The fixture
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

### Browser authentication fixture

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
The pinned Chromium can rewrite child command lines as lossy process titles,
including truncation immediately after one literal space. Preserve the exact
raw title and its observed-only qualifier. Tokenization may recognize that one
terminal separator; internal or repeated empty tokens, other whitespace,
quotes, backslashes and disabling flags still refuse. A title never reconstructs
original argv or replaces the independent live sandbox/namespace proof.
It proves direct API TLS/authentication; shared-Caddy and complete installed
UI/platform acceptance follow with authenticated static serving. Synthetic fixture
storage supplies no live NAS evidence. Preserve failed workspaces and original
operation handles; never drain or reuse an older unknown guest.

### Installed product workflow acceptance

After the full source gate, exercise the selected built release on explicitly
owned isolated native and rootless deployments. Use real Caddy/TLS, installed
API/worker/helper roles and Chromium, Firefox and WebKit at both root and
`/management` entrypoints, with fresh browser contexts. Cover authentication and
routing, Library filters and details, README/Files, configuration forms and
representative request/error handling. Source fixtures and mocked HTTP cannot
replace these installed observations.

Keep every required behavior and safety clause. Use unit/component and real
integration tests for deterministic validation, interruption and fault
boundaries, with direct installed workflows for browser and platform behavior.
Run deeper domain/fault combinations at the relevant boundary rather than every
scenario in every browser/profile cell. Supported native schedule/observer
controls and maintenance/Repair require actual positive paths; rootless
restrictions require actual denials. Record real CLI and all fourteen MCP tools
through the shared trusted Caddy at both aliases, including browser/client
overlap, and identify whether report reads refer to genuine worker outcomes.

Identify source, indexed artifacts, installed roles, fixture scope, commands and
observed results in the existing acceptance records. Retain actual hardening,
peer, mount and process/resource-closure observations; no selected command or
security setting may be weakened for a test. Finite stream/deadline/disconnect
and resource-release behavior remains required at the appropriate real boundary;
source review alone does not establish an exercised outcome. No new collector,
evidence schema, binder or instrumented lifecycle framework is required.

Reuse earlier passing evidence only with its original scope and a stated
unchanged-subsystem/source/artifact justification. Repeat checks for changed
behavior, unresolved failures or uncovered requirements. Preserve original
failed results and accepted-operation identities; observe original outcomes and
recovery rather than replaying an effect to manufacture a clean aggregate.
Maintain an explicit missing-clause list: missing required behavior blocks
completion. Source acceptance, disposable installed acceptance and production
rollout remain separate statuses.

### Installed shared-Caddy functional fixture

The optional instrumented runner checks an explicitly provisioned disposable
fixture. Its protected manifest, full profile/prefix/browser matrix, source and
installed artifact bindings, lifecycle proof and finite stream checks are
specified in [web functional testing](web-functional-testing.md). Use its safe
inspection mode before provisioning:

```bash
python -S scripts/check-web-functional.py --help
```

To request the complete instrumented check with the source gate:

```bash
HFCACHE_WEB_FUNCTIONAL_MANIFEST=/absolute/owned/fixture.json \
  scripts/check.sh --require-web --with-build --with-web-functional
```

The flag selects all profiles and strict final mode. Partial reports, failed
attempts and missing prerequisites cannot pass. Direct installed workflow
evidence is recorded separately; it is not a passing invocation of this runner.
Synthetic local storage proves no live NAS or production acceptance.

### Protected host-reader validation

Run the focused protocol/client/policy/peer/daemon/API boundary tests while
changing the fixed helper:

```bash
uv run --locked --extra server --extra mcp pytest \
  tests/unit/test_host_protocol.py tests/unit/test_host_helper_client.py \
  tests/unit/test_host_policy.py tests/unit/test_host_peer.py \
  tests/unit/test_host_daemon.py tests/unit/test_host_models.py \
  tests/unit/test_host_status.py tests/unit/test_host_authorization.py \
  tests/unit/test_host_action_routes.py tests/unit/test_container_host_helper.py
```

These establish local framing/original-pidfd/descriptor ownership, strict models,
bounded inspection and policy/admission/lifecycle behavior. Simulated root
metadata and manager/container outputs are labeled source fixtures. They cannot
establish installed native/rootless identity, SELinux, read-only mount projection,
actual UID/GID maps or Caddy/built-UI behavior. The isolated installed fixture must
use genuine fixed `/opt/hfcache/current` profile bindings and actual managers,
engine and installed bytes. A relocated layout or copied proof is insufficient.
Retain every failed attempt and actual process/cgroup/container drain evidence.
Each owned isolated guest may use its own source label and32-hex identity.
Its root-owned marker still binds the exact fixture UUID, repository,
guest identity and current boot; earlier guest histories are not prerequisites.
Required missing kernel/runtime/browser support is a blocker, never a skip or a
reason to weaken hardening. The full source gate and every required installed
behavior remain necessary; the optional instrumented runner retains its own
strict final acceptance set if requested.

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
observations. See the [deployment acceptance checklist](deployment-centos-stream-10.md#acceptance-checklist).

Distinguish socket refusal from packet filtering when proving verifier network
isolation. A bounded TCP timeout or missing errno alone proves neither denial
nor a successful connection. Native acceptance binds the actual worker process,
cgroup and network namespace to verified ingress/egress deny programs before
and after fresh attempts, successful same-UID/same-namespace positive controls,
and continuous listener observations with no accepted worker connection.
Rootless acceptance pins the actual applied AF_UNIX-only seccomp policy and its
configured denial errno, proves socket-family availability with the same image
and kernel under the stock policy, and observes successful AF_UNIX creation in
the restricted worker. Unknown outcomes, changed bindings or missing controls
refuse acceptance; do not change isolation to make a probe pass.

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

## Repository map

| Path | Contributor use |
| --- | --- |
| `src/hfcache/` | Domain services, authenticated client, CLI and optional REST/MCP transports |
| `docs/` | Task guides, technical contracts and architectural rationale |
| `web/` | React/TypeScript interface, frozen build inputs and bundled browser assets |
| `packaging/` | Native/container units, configuration, image inputs and runtime templates |
| `scripts/` | Build, install, diagnostic, test and consumer helpers; [catalog](scripts.md) |
| `examples/` | Archive policy, independent copy helper and protected-file MCP client |
| `tests/` | Offline fixtures, explicit opt-in system tests and durable-format goldens |
