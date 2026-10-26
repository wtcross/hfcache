# Keep strict web assets separate from Python runtime and require real acceptance

- Decision identity: 143.
- Asset/bootstrap refinement: [decision147](decision-147.md).
- Status: Amended; strict workspace, typed wire, Basic/indexed assets and functional-gate scaffolding are implemented in unreleased source. Complete replacement/release conformance remains separately required.
- Date: 2026-10-20.

Typed browser contracts are refined by [decision 145](decision-145.md); release
artifact and installed functional conformance remain independently required.

## Context and decision

Build the replacement UI in `web/` using React and strict TypeScript, with
committed frozen pnpm dependencies and pinned compatible Node/pnpm/tool versions.
Record dependency licenses and runtime/build classification. Browser libraries
are bundled assets; Node is never a deployed application runtime. Existing
LGPL-2.1-or-later notices survive any Cockpit code reuse.

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

Extend the provider-neutral gate with `--require-web` and
`--with-web-functional`; combine both with `--with-build` for final acceptance.
Frontend-required invocation refuses missing source/toolchain/browser/fixture
prerequisites. Skips or mocks cannot prove required installed functionality.
Preserve applicable existing Python, package, docs and Cockpit gates until
retirement is explicitly accepted.

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

At baseline `6b8fae2e0997403ae5c716a2e92148af0a972af9`, `web/` and its
strict gate/artifact do not exist. Existing Cockpit checks remain current. This
commit accepts the design and claims no frontend or installed acceptance.

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

`scripts/check.sh --require-web` preflights the package manifest, frozen lock,
TypeScript configuration and Node/pnpm before backend work. It preserves backend
and applicable Cockpit gates, then runs frozen web installation and every script
above in order. A missing tool/input/browser, failed stage or late disappearance
fails. Default backend-only invocation explicitly omits web validation and cannot
establish web acceptance. Help remains free of runtime/credential/archive access.

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

Amends [088](decision-088.md), [FW-01–FW-04](fw-01.md),
[113](decision-113.md) and [140](decision-140.md).
See [server asset design](../server.md#web-ui-design-and-current-availability),
[record formats](../schemas.md#18-web-ui-and-administration-design-records),
[web UI status](../web-ui/README.md), [development](../development.md),
[security](../security.md#browser-administration-design) and
[conditional retirement](decision-144.md). The initial accepted design remains
the basis for the implementation amendments above; each implemented boundary
requires its own executable evidence, and installed conformance remains pending.

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

This clarification changes no gate, artifact or runtime requirement. Dirty owned
artifacts retain their actual build provenance. Clean release packaging,
installed role/browser conformance, the remaining feature cases and conditional
Cockpit retirement require their own evidence; no rollout follows. See the
[functional development contract](../development.md#installed-shared-caddy-functional-fixture)
and [recorded installed scope](../deployment-status.md).

## Bounded Markdown asset dependency amendment (2026-10-26)

[Decision155](decision-155.md) records the material correctness rationale for
react-markdown 10.1.0, remark-gfm 4.0.1 and rehype-sanitize 6.0.0 as bundled browser
assets, with an explicitly provisioned frozen license-audited closure. No Python
runtime dependency, runtime Node, remote plugin or asset fetching follows. The
existing immutable build/source/license identity and installed acceptance
requirements remain unchanged; the decision is not execution evidence.
