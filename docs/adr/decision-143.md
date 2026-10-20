# Keep strict web assets separate from Python runtime and require real acceptance

- Decision identity: 143.
- Status: Accepted design; implementation and conformance pending.
- Date: 2026-10-20.

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

## Evidence and relationships

Amends [088](decision-088.md), [FW-01–FW-04](fw-01.md),
[113](decision-113.md) and [140](decision-140.md).
See [server asset design](../server.md#web-ui-design-and-current-availability),
[record formats](../schemas.md#18-web-ui-and-administration-design-records),
[web UI status](../web-ui/README.md), [development](../development.md),
[security](../security.md#browser-administration-design) and
[conditional retirement](decision-144.md). Introducing design is this commit;
implementation and executable gate evidence remains pending.
