# Derive precise browser contracts and preserve numeric source before decoding

- Decision identity: 145.
- Status: Accepted; source implementation is present. Executable acceptance is
  recorded in the introducing task and commit.
- Date: 2026-10-20.
- Introducing evidence: this commit; source acceptance is recorded separately.

## Context and decision

The stable REST wrapper contains a generic domain Envelope. OpenAPI alone cannot
distinguish status from repository and revision inventory, or installed from
literal-candidate validation. Strict TypeScript declarations do not validate
network input. JSON numbers can lose precision before a safe-integer check, and
Pydantic custom validators carry rules that its JSON Schema does not express.

Keep the established REST, CLI and MCP wire bytes. Add pure strict projections
over existing dictionary serializers and reuse existing public domain/client
models. A deterministic registry selects each payload by method, route and
request mode. Original operation results use the original receipt route and
allowed domain command; a new page or action never invents that identity. Private
operation-store fields are excluded. Request DTO imports remain export-only when
their optional service closure is unavailable to the base reader.

Export an audited schema IR, then generate reconstructing TypeScript decoders
and types from it. Response properties are required even when Python supplies a
default during construction; request omission and explicit null remain distinct.
Normalize known tuple bounds from the authoritative field/core schema and retain
decimal-string numeric bounds. Named semantic hooks cover custom scalar,
cross-field and cross-response rules. Unknown keywords, validators, serializers
and changed unaudited hooks refuse generation. Check both exports for drift in
the strict gate. Independent malformed fixtures and actual Python serialization
roundtrips supplement generated expectations.

Use native JSON grammar with reviver source context, checked before accepting
numeric fields. A bounded scanner rejects duplicate decoded keys, malformed
strings, excessive nesting and work. Fatal UTF-8 collection has separate byte
ceilings. Preserve raw numeric tokens privately until their field decoder checks
integer syntax, decimal BigInt bounds and JavaScript safety before conversion.
Unsafe integers refuse explicitly; they never become rounded selectors, sizes or
counts. Missing native source-context support refuses rather than falling back.
Keep timestamp microseconds and Unicode code-point ordering where Python semantics
require them. No new runtime JSON-parser dependency is introduced.

The checked Python authority uses Unicode 16.0.0 while the selected Node runtime
uses Unicode 17.0. Native NFC/lowercasing therefore cannot define archive path
collisions. Export the pinned Python authority's canonical decomposition,
composition, combining-class, full-casefold and nonprintable-point tables,
implement bounded NFC
including algorithmic Hangul, then full casefold with no final normalization.
Retain the Unicode license and exact official normalization/casefold fixtures.
Known compatibility distinctions remain intact; no NFKC or approximate lowercase
replacement is allowed. Shared manifest Unicode work is capped at 8,000,000
steps. A table/Unicode upgrade requires explicit regeneration and review.
Compatibility-only archive initialization also validates Python printability
against these pinned tables rather than the browser's Unicode categories; this
adds no browser initialization action.

The same-origin client exposes named read and mutation paths, finite body reads,
AbortSignal and validated configured-prefix links. It follows no redirects and
never retries a POST. API problems, failed domain Envelopes, malformed protocol,
transport failure and aborted observation are distinct values. A failed Envelope
is inspected before requiring success data; separately validated partial evidence
remains informational. Cache identities include authenticated authority, archive
and exact publication identity; credentials are never stored in those keys.

## Rationale and alternatives

Generic OpenAPI output plus an assertion would leave the domain boundary
unchecked. Handwritten duplicate DTO declarations would drift from server
authority. A schema-only validator would miss custom and cross-response rules.
A new lossless JSON library still needs duplicate-key, string and work controls;
the native source-context interface supplies exact numeric tokens without adding
a shipped dependency. A handwritten replacement JSON grammar adds maintenance
without strengthening the existing native grammar. Capability refusal makes the
supported-engine requirement explicit.

## Consequences and evidence

Browser reads can refuse a response that exceeds their own finite budget or
safe integer range even when a server can produce it. Such refusal cannot become
an empty/healthy result or mutation readiness. The browser does not replace
server authorization, archive validation, page completeness or operation control.
Base/server/MCP profiles and all existing operation handles remain supported.

Generated Unicode tables are shipped data under Unicode-3.0, separately indexed
from the unchanged npm dependency closure. Offline notice checks bind the data
and exact license bytes. The implementation follows the
[normalization specification](https://www.unicode.org/reports/tr15/)
and is checked against the pinned Unicode 16 official vectors; current browser
normalization is not its oracle.

The temporary real-API React read fixture precedes authenticated application
static serving. It proves the wire/presentation boundary only, with explicit
post-service corruption faults; it does not establish shared-Caddy, Basic,
installed native/rootless or live NAS acceptance. Required source/test results
belong to the execution evidence; none are claimed by accepting this design.

This refines [decision 143](decision-143.md) and the presentation requirements of
[decision 137](decision-137.md), preserving [118](decision-118.md),
[119](decision-119.md), [123](decision-123.md), INV-005/006/007 and INV-021.
See [API wire rules](../api.md#browser-wire-boundary),
[schema compatibility](../schemas.md#11-validation-summary),
[development](../development.md#generated-browser-contracts), and the
[ECMAScript JSON.parse specification](https://tc39.es/ecma262/multipage/structured-data.html#sec-json.parse).

## Bounded session observation amendment (2026-10-26)

The typed client supports a per-read response limit that can only lower its
registered route ceiling. The application observation controller uses8MiB;
ordinary16MiB, artifact64MiB and card2MiB ceilings still apply. Submission options
remain separate and do not inherit a read cap. Shared32MiB encoded logical
retention is not an exact heap measurement. Concurrency, finite GET retry/time/
cycle budgets and bounded event buffers preserve unknown/gap classifications;
they never retry POST or infer nonexecution from observation failure.

The route-independent controller retains original receipt route/identity and
uses the original authenticated key or ID. Restored metadata requires fresh
observation; ID import proves no creator/key association. Reconnect refreshes
current authenticated read context while retaining original admitted authority.
Local auth-generation invalidation applies even when server scope values match.
The [session contract](../schemas.md#186-browser-recovery-metadata-schema-1) and
[user guide](../web-ui/operations.md) refine the recovery design of
[decision134](decision-134.md) and query semantics of [decision137](decision-137.md).
No server DTO, receipt format, REST/MCP permission or execution authority changes.

## Typed Library composition amendment (2026-10-26)

The Library reuses the typed read client and session query ownership for bounded
catalog pages, explicit facet pages and inventory/status enrichment. Keys retain
normalized predicates and authority; joins retain repository type/ID and exact
SHA/publication identity. A stale/malformed/inconsistent enrichment cannot
silently reattribute newer current-publication size or integrity to an older
retained catalog representative. Loaded extent, whole scoped coverage and known
matches remain distinct, including zero under incomplete coverage.

Browser navigation stores allowlisted filters in bounded fragments, because the
existing shell refuses query strings. Fragments cannot choose another endpoint
or authority. API requests keep their existing supported query keys, bounds and
route semantics. Dataset selection clears model-only predicates visibly. Finite
stale-continuation resets and explicit limit failures replace hidden all-page
collection; existing response/retention limits are not enlarged. This is read
composition, with no new wire schema, endpoint, dependency or writer capability.
See [Library procedures](../web-ui/library.md) and [catalog semantics](../discovery.md#queries-coverage-and-pages).

## Exact-publication detail composition amendment (2026-10-26)

Detail routes and bounded paired SHA/publication fragments are presentation
identity, never endpoint or authority input. Current reference resolution is
separate; derived panels join only the selected exact publication/generation and
authenticated scope. Selection/auth changes retire superseded requests, and late
old responses cannot supply a new identity's card, variants, size or confidence.
Same-SHA repair and missing retained identity never authorize latest fallback.
The selected full-SHA reference gates retained membership independently of
optional adjuncts; an accessible preserved predecessor manifest is insufficient.

REST manifests remain whole bounded artifacts with explicit numeric/byte refusal
and local file-table paging. Available manifest-file digests come from the
existing exact card boundary, never a browser JSON reserialization. Integrity
uses exact revision evidence independently of metadata completeness or readiness;
Activity retains limited loaded-history provenance. Existing wire schemas,
response/retention ceilings and read-only authority remain unchanged. See
[detail procedures](../web-ui/repository-details.md).
