# Keep strict web assets separate from Python runtime and require real acceptance

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

- Decision identity: 143.
- Asset/bootstrap refinement: [decision147](decision-147.md).
- Status: Amended; strict source/build and scoped direct installed replacement acceptance recorded. Production releases and other-platform acceptance remain separate.
- Date: 2026-10-20.

The acceptance-method amendment below governs current conformance. Earlier
requirements to use the instrumented runner for every scenario in every cell
remain historical; its protocol stays strict when that optional tool is used.

Typed browser contracts are refined by [decision 145](decision-145.md); release
artifact and installed functional conformance remain independently required.

## Context and decision

Require `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`,
type-aware unsafe-assignment/no-explicit-any lint and known-state exhaustiveness.
Mechanically derive transport types and runtime validators from the precise
server/domain schema registry; generic nested Envelope dictionaries in OpenAPI
do not establish domain typing. Validate unknown wire data before presentation,
preserve failed Envelopes and integer safety, and bind cached queries/operation
observation to authenticated authority, archive and exact publication identity.

Produce a separate immutable web artifact, alongside the backend wheel, with
source commit, UI contract version, toolchain/lock identity, indexed paths,
per-file size/hash/MIME and license notices. Native releases stage it in the
immutable release; rootless images copy a verified artifact to a fixed read-only
application directory. Full releases require this artifact. Base Python wheel
build/install remains Node-independent. Do not commit dependency trees, generated
dist, browser profiles or credential-bearing screenshots.

Every feature includes unit/component and integration tests plus functional
coverage delivered with its working boundary. Real functional acceptance uses
the built UI through actual Caddy/TLS and the installed API, including isolated
native/rootless host behavior and Chromium/Firefox/WebKit. Record test identity,
artifact hashes, profile/browser, commands/results and safe evidence location.
Human user/operator guides, API references and deployment/troubleshooting
instructions must change with the feature. Agent records are not human guides.

## Rationale and alternatives

A separate artifact preserves reader/backend installation independence while
allowing exact deployed UI/backend compatibility checks. Packaging Node or
building assets during base wheel installation would enlarge runtime authority
and break existing installation profiles. Type assertions or generated generic
OpenAPI dictionaries would merely move unchecked input into trusted components.
Mocked auth/host/browser success would leave the replaced privilege/transport
boundary unproved.

## Consequences and conformance

Version selection is compatibility-tested and locked during toolchain creation;
this decision does not guess future package versions. New server runtime
dependencies require their own correctness rationale, including the bounded
Argon2id exception in [140](decision-140.md). Final acceptance may remain blocked
by unavailable real infrastructure; it cannot redefine a required scenario into
a skip or use production services/archive as a fixture.

## Selected workspace tooling and preliminary gate amendment (2026-10-20)

The initial workspace selects Node `24.18.1`, pnpm `11.18.0`, React/React DOM
`18.3.1`, TypeScript `6.0.3`, Vite `8.3.4` with React plugin `6.1.2`,
ESLint `10.13.0` with JavaScript rules `10.0.1` and typescript-eslint `8.63.0`,
Vitest/V8 coverage `5.0.5`,
React Testing Library `16.3.3`, user-event `14.6.8`, jsdom `30.1.3`,
Playwright `1.64.1`, axe Playwright integration/axe-core `4.14.0` and Prettier
`3.9.10`. Exact remaining dependencies and
transitive resolution live in the separate frozen web lock; license inventory
and notices accompany that selection. These are browser asset or build/test
dependencies and add no deployed Node process or Python runtime requirement.
Reusing the repository's TypeScript-6-compatible lint release avoids unnecessary
package release-age exceptions while retaining strict dependency admission.
Select the maintained ESLint 10 line: the official
[support policy](https://eslint.org/version-support/) records ESLint 9's end of
life on 2026-08-06. The selected type-aware and React plugins declare compatible
peers. The older JSX accessibility plugin does not support that major; semantic
component/keyboard tests and actual desktop/mobile axe browser checks provide
accessibility enforcement instead. The MPL-2.0 axe packages are test-only and
are not shipped in the browser application bundle.

The implemented script contract is `lint`, `typecheck`, `test:strict-fixtures`,
`test:unit`, `test:component`, `build`, `test:browser`. The strictness fixtures
exercise deliberate invalid TypeScript/unsafe assignments rather than accepting
configuration flags alone. Combined new-source unit/component coverage must meet
90% lines and 85% branches; existing Python coverage is not redefined.

### Historical workspace-stage scope (2026-10-20)

The following records the initial shell-only stage; the dated source-implementation
clarification below describes current unreleased tooling.

Browser dependency provisioning is explicit and separate from execution.
The initial `test:browser` uses a production-built shell in pinned Chromium on
an owned loopback fixture, with a clear development/ disconnected status and no
API authentication or archive behavior. It must fail if Chromium is unavailable.
This preliminary check is deliberately distinct from the required three-engine
real Caddy/installed application/platform acceptance. The future
`--with-web-functional` option is not yet implemented and currently remains an
unknown argument, rather than a successful placeholder.

Workspace/gate source conformance and actual command results are recorded when
their checks run. This tooling amendment alone claims no passing test, Caddy
integration, installed availability or production rollout. See the
[development commands](../development.md#web-workspace),
[web package](../../web/package.json), [license inventory](../../web/dependencies/licenses.json)
and [user status](../web-ui/README.md).

The workspace and preliminary gate implement the first part of this decision.
Precise API wire schemas, authentication, application-owned static serving,
immutable native/rootless release integration and full three-engine installed
functional acceptance remain pending. Their requirements are unchanged by a
successful shell-only check.

## Evidence and relationships

## Authenticated asset and bootstrap amendment (2026-10-20)

[Decision147](decision-147.md) amends this record. This refinement fixes deterministic source/toolchain/license/member identity and a source digest computed from the actual installed backend. Prebundle compiled source identity avoids a circular manifest fingerprint. Native platform hashing validates context; final functional gating requires all95 scenarios through actual Caddy and installed native/rootless roles, while early profiles keep future cases pending. The UI ships inside the pinned UBI10micro API image without Node.

## Source implementation clarification (2026-10-21)

The preceding shell-stage unknown-option and pending-implementation statements
remain historical. Unreleased source now includes precise wire contracts under
[decision145](decision-145.md), bounded Basic under [decision146](decision-146.md)
and deterministic indexed artifacts/bootstrap/static serving under
[decision147](decision-147.md). The provider-neutral application/platform/all
runner and `--with-web-functional` gate are implemented; their required installed
inputs still fail closed. Early scoped runs report later cases pending; the final
flag requires all95 scenarios and is not replaced by source or shell tests.

## Installed acceptance execution clarification (2026-10-31)

Canonical profiles may run on separate owned, boot-bound guests. `all` denotes
complete application/native/rootless × prefix × browser coverage, not mixed
installation layouts on one boot. Application may use native confinement; all18
cells still require fresh fixtures, actual installed roles and paired lifecycles.
One fresh run identity joins only the existing runner's three normal profile
outputs under explicit common artifact/test-source authority. Offline retained
proof copies preserve original guest metadata; they do not re-probe remote state
or establish copied-inode identity. No one-off receipt or pending case supplies
acceptance. The [functional development contract](../development.md#installed-shared-caddy-functional-fixture)
retains the required staged and final matrices, with unchanged runtime authority,
artifact identity and isolation requirements. This corrects test orchestration;
it introduces no runtime dependency or new architectural decision.

## Bounded Markdown asset dependency amendment (2026-10-26)

[Decision155](decision-155.md) records the material correctness rationale for
react-markdown 10.1.0, remark-gfm 4.0.1 and rehype-sanitize 6.0.0 as bundled browser
assets, with an explicitly provisioned frozen license-audited closure. No Python
runtime dependency, runtime Node, remote plugin or asset fetching follows. The
existing immutable build/source/license identity and installed acceptance
requirements remain unchanged; the decision is not execution evidence.

## Immutable release construction refinement (2026-10-29)

[Decision158](decision-158.md) refines native full web runtime delivery: a fresh
release/source-specific interpreter copy excludes optional Python installers
without changing shared managed donors or previous runtimes.

The clean release constructor builds wheel, sdist and the separately indexed UI
twice from one clean committed source and compares bytes. Pin the existing
`uv_build` backend to `0.11.32`, matching the already pinned uv tool, rather than
resolving a floating backend during release construction. This tightens a build
dependency; it adds no runtime dependency. A separate canonical deployment index
binds all captured source files, backend artifacts, the UI manifest and the exact
nine-file helper closure. The native installer verifies this explicit digest
before effects and checks the copied source again before staging assets.
Native dependency installation uses ordinary copying so release bytes are
independent of mutable cache links and filesystem reflink support.

The rootless builder accepts a paired asset directory/digest and copies captured
verified bytes into `/opt/hfcache/ui` in the existing API image. An explicit
authenticated rootless `web.toml` input selects that digest and the fixed API-only
Basic hash location. Absent/disabled input retains backend-only behavior. Existing
schema-1 rootless release maps carry these additional indexed files; UI assets
remain separate from secrets, writable policy, sockets and archive storage.

These delivery checks reuse the original UI schema during construction and
startup, with a standard-library-only installer verifier for bounded canonical
manifest/hash/path checks. They neither provision host policy or secrets nor
activate services. Runtime confinement and original handles remain unchanged.
The protected host reader executes the captured indexed verifier and retains
all source/UI reads inside its existing per-inspection metadata/hash accounting;
it never imports a verifier by a freshly reopened candidate pathname. Empty
bytes are accepted only for explicitly indexed public UI members, preserving
the ordinary nonempty authority-file rule and existing aggregate limits.
Expanded foundation checks use actual image ancestry/size and reject Node,
package managers, compilers and browsers. Source implementation and focused
tests alone do not prove clean or installed release conformance; exact artifact
and disposable installed acceptance remain required.

## Product acceptance method amendment (2026-11-01)

Retain every required product and safety scenario, with executable evidence at
the appropriate unit, component, integration and installed-workflow boundary.
Actual native and rootless installations still require trusted same-Caddy
Chromium, Firefox and WebKit coverage at both public prefixes. Deeper domain,
failure and privilege combinations run where the relevant boundary exists;
every scenario need not repeat across the entire profile/browser/prefix product.

Reuse passing evidence only for its actual scope, with an unchanged-subsystem
justification. Retain failed attempts and original operation identities; a later
continuation can cover an unfinished clause without relabelling the earlier run.
Missing required behavior still prevents completion. Add a focused regression
for a real defect or an uncovered requirement, without creating a new framework,
proof schema or lifecycle model. Runtime bounds, authorization, confinement,
immutable publication identity and production/NAS limits are unchanged.

This amendment supersedes only the mandatory instrumented-runner and exhaustive
cross-product execution method above. See the current
[development acceptance procedure](../development.md#installed-shared-caddy-functional-fixture).

## User-directed deprecation scope (2026-11-01)

## Recorded final source and product acceptance (2026-11-01)
