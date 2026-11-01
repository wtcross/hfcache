# Derive precise browser contracts and preserve numeric source before decoding

- Decision identity: 145.
- Status: Accepted; source implementation is present. Executable acceptance is
  recorded in the introducing task and commit.
- Date: 2026-10-20.
- Fresh-byte parsing amendment: [decision157](decision-157.md).
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

Original-handle announcement clarification (2026-10-29): original-handle import keeps a
typed local success/error outcome. Rejected input is presented as an error alert;
a successful local save remains a polite status announcement. This changes only
feedback semantics, without moving focus, looking up a handle or submitting an
operation. Recovery identity, authority, wire formats and dependencies are
unchanged. Matching installed reader acceptance remains separately required.

### Large manifest presentation refinement (2026-10-27)

The authority metadata scanner advances between structural bytes and quoted
string boundaries using native byte searches. Quote termination still depends on
the complete adjacent backslash run's parity. The existing depth 32 and 100,000
structural-token ceilings, byte caps and subsequent strict JSON/model validation
remain unchanged. This reduces repeated work for long UTF-8 manifest paths while
retaining every existing refusal and fresh authority read.

Catalog projections bind each present observation through its fresh authoritative
reference and manifest once. A missing observation still requires that binding
before it may be classified as missing. This removes an immediately repeated
authority read without caching a previous query, trusting an adjunct or changing
the configured byte/traversal ceilings. Lexical containment uses an exact anchor
and component prefix for the common case, retaining the standard path operation
as its fallback. The descriptor reader still rejects relative paths and `..`
before opening anything, and walks every absolute component with `O_NOFOLLOW`.

The reviewed storage, metadata and path source pins and affected publication
context pins are renewed for these implementation changes. Public definitions,
routes, operation results and
browser semantic ports are unchanged; the conservative source digest changes
and an old open page still requires the normal interface-version check. Boundary,
escape-parity, independent tree-oracle and real-query equivalence tests accompany
the change. Installed performance acceptance remains a separate measured gate.

Initialized-layout conformance review (2026-10-30): archive inspection
recognizes the documented managed catalog, journal, report and namespace
boundaries after initialization, while preserving unknown/type/symlink refusals,
bounded reads and the separate typed consumers' content authority. Renew the
reviewed archive source pin for this runtime correction. Public definitions,
semantic ports, routes, result shapes and limits stay unchanged; only the
conservative source digest changes. Installed UI validation follows a fresh
matching backend/UI build.

[Decision157](decision-157.md) subsequently permits bounded reuse of frozen
parsed models by exact freshly read bytes. The earlier duplicate-binding
optimization remains independent; no previous query result, membership or
authority is reused. Filesystem reads and their query charges still occur before
the parser memo lookup.

Keep whole-manifest validation, exact publication identity and existing response,
Unicode-work and shared retention limits. Small file collections retain local
25-row pages. Above100 files, use a virtualized metadata table with at most24
mounted file rows and inert height spacers, without a new dependency. Fixed
summary-row heights and one separately selected full-metadata panel avoid
unbounded expanded provenance rows. Preserve column headers and actual row
indices/counts, retain a focused row across scrolling, and support arrows,
Page Up/Down, Home/End and explicit file-number navigation. Publication changes
reset the window and selected metadata before display. Viewport movement and
selection perform no network request and grant no operation authority.

Metadata action names include the visible phrase **Inspect metadata** and the
loaded file number. The full path remains in the row header and selected evidence.
This keeps the accessible action name consistent with its visible label and
avoids repeating a potentially long path inside every button name. Real connected
scans exposed the earlier label mismatch; file identity and validation are unchanged.

This fulfills the large-manifest virtualization requirement rather than calling
existing pagination virtualization. The server still sends one complete bounded
manifest; an oversized/unsafe artifact remains an explicit refusal. No arbitrary
file route, download, source-digest invention or publication fallback is added.
Existing finite pagination remains appropriate for other bounded detail/report
collections. Actual keyboard, zoom, reader, DOM/retention and real-Caddy evidence
belongs to task020, not this decision text.

### Repository text contrast refinement (2026-10-27)

Repository selection labels, summary captions, small evidence text, fact labels
and local page controls use the shared muted foreground. The former lighter
detail-specific colors failed the actual connected model overview contrast
scan. The shared foreground provides at least 4.5:1 contrast on the interface's
white, page, table-header and warning backgrounds at ordinary text sizes.
Descriptions use the same foreground so text remains readable outside white
cards. Disabled controls retain their distinct unavailable presentation.
Final built-browser scans remain required; calculated palette ratios alone do
not establish accessibility acceptance. This changes presentation only, with
no new invariant, public wire shape, dependency or architectural authority.

### Primary repository action hover refinement (2026-10-28)

Primary repository actions retain white text on a dark accent background when
hovered. Their hover rule must take precedence over the generic pale repository
button hover background. The source8 installed cancellation/fresh-return case
exposes the former cascade conflict as a serious contrast violation on **Select
current publication**. This correction fulfills the existing text-contrast
requirement; matching built-browser checks remain required for the new source.
It changes no invariant, wire shape, dependency or architectural authority.

### Named content groups refinement (2026-10-27)

Author-labelled content groups must expose a supported nameable role. The
Sanitized README source, Selected job effects and Host controls use explicit
group semantics with their existing labels. A label on a generic `div` or `pre`
alone does not supply that semantic grouping. Source text remains exact,
escaped and keyboard-focusable; related explanations and controls retain their
existing order, layout and authority. Component regressions resolve these groups
by role and name and check their content or controls. This fulfills the existing
presentation boundary without a new API, dependency or operation. Built-browser
and reader acceptance remain required for the revised source; earlier artifact
evidence is not relabelled as acceptance of this refinement.

### Document visibility refinement (2026-10-27)

Visibility is a local observation gate. A hidden document pauses active original
receipt/event/result observation, aborts its GET and finite retry/poll/deadline
ownership, and fences late responses. Explicit original configuration and host
outcome reads are gated and aborted too: a hidden or superseded response cannot
provide fresh private outcome proof. Ordinary explicit query ownership retains
its existing route/lifecycle rules. No visibility transition cancels a submitted
POST, erases an original handle or implies that backend execution stopped.

Returning visible does not restart observation. The user deliberately chooses
Observe for the preserved original. An admission acknowledgement crossing a hide
transition still saves its original key/ID, but cannot automatically begin reads
after return. This makes the existing `hidden` pause reason effective at the
mount-owned document boundary and avoids hidden polling without adding a retry
loop, credential store, API, dependency or authority. Actual lifecycle and
installed-browser evidence belong to task020; this amendment alone claims none.

### Document navigation refinement (2026-10-29)

A clean document departure retires the Library, repository and Administration
read owners before cancelled reads can start the next request in a batch.
Page departure also fences queued searches and location work. A dirty-form
beforeunload veto runs first: choosing Stay preserves the document's draft,
original handles and usable reads. Page restoration reactivates only the current
route, whose existing location reader revalidates its state; it does not revive
another route or replay an admitted operation. The initial pageshow is not a
refresh trigger. These rules cover browser history restoration without requiring
the browser to retain a document in its back-forward cache.

An already-started read promise is observed even when its signal was aborted
before the bounded await begins. Abort still returns immediately and cannot
extend the read deadline; later rejection cannot become an unowned exception.
This fulfills INV-021's existing ownership boundary without a network-error
filter, new polling loop, authority change, API or dependency. Matching installed
browser evidence remains independently required.

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

## Repository read ownership refinement (2026-10-26)

Repository detail queries belong to the active view. Keeping a ready query
subscription after leaving that view can prevent another feature, such as repair
evidence checking, from acquiring the identical query under the existing active
duplicate guard. A completed read does not justify permanent view ownership.

Pausing or leaving repository details therefore releases all of its query
subscriptions and aggregate payload references, including ready evidence. Only
the repository identity, selected full SHA/publication pair and tab remain for
navigation. Returning explicitly creates fresh authenticated read handles and
revalidates the selected full-SHA reference before publication data is qualified.
Missing or replaced membership remains unavailable without a current/latest
fallback. Immutable response reuse across a complete route exit is not required.

This changes no query identity, active duplicate guard, response/retention bound,
API, schema or capability. It adds no background read or automatic retry. Original
operation ownership remains with the session controller; leaving a read view
never cancels or replays accepted work.

## Structured managed-edit composition clarification (2026-10-26)

The editor uses the existing generated editable projection, strict managed DTOs
and original-operation controller. One RAM-only draft and local intent diff bind
the exact full-byte base. Every edit invalidates validated/assessed readiness;
Apply requires the unchanged draft and original successful complete preview.
Supported JSON is the same editable schema, never arbitrary TOML or protected
values. Existing configuration-read/write grants are composed independently of
host-read, with no endpoint, dependency or server wire change. Explicit original
host-outcome reads cannot clear uncertainty from a generic failed receipt. See
[decisions153](decision-153.md) and [154](decision-154.md).

An explicit fresh original-key lookup and protected outcome may provide RAM-only
configuration knowledge for the exact application/archive. Only with a verified
terminal API receipt, `pending=false` and `confirmed` or `unchanged` may this
release the current-session submission precaution. It changes neither persisted
recovery metadata nor the generic receipt; reconnect clears the proof. Unchanged
is known no-install, not successful installation. Validation uses the existing
bounded shared read/retention ownership and is non-installing despite using POST.

## Preserve mutation Origin across browsers (2026-10-26)

Actual installed Firefox validation returned403/HFAPI010 with `Origin: null`
under the client's explicit `no-referrer` request policy, despite authenticated
same-origin fetch metadata. JSON POSTs therefore use `same-origin` request
referrer policy; GETs retain `no-referrer`. The closed API origin, same-origin
mode, refused redirects, no-store and non-simple request header remain. The
server still requires its exact configured Origin, including for validation.
Response headers and external links remain `no-referrer`. Accepting null Origin
would weaken the existing CSRF boundary; changing the request policy preserves
that boundary without a new endpoint, permission, dependency or automatic retry.


## Existing jobs and paged history composition (2026-10-26)

Named typed job DTOs retain explicit full/selected and verification/diagnostic/
refresh discriminators. A bounded read-only candidate-file upload is sizing-only,
never a TOML editor, durable browser body or protected configuration installation.
The same original-key controller owns every POST and exact result identity; event,
receipt and domain-report reads remain separate. Finite displayed history/local
report pages preserve current-session query ownership and existing byte limits.
[Operations procedures](../web-ui/operations.md) add no server DTO, permission,
route, mutation retry or new architecture rule.

Ready history rows and their known loaded extent are derived from the same query
snapshot. A query-ready notification can precede its awaiting caller's positional
bookkeeping; the displayed active-page count therefore comes from that ready
payload rather than a stale stored count. Previous positions and their finite
retention remain unchanged. This prevents a transient zero loaded extent beside
visible rows without scanning, inventing totals or altering read authority.


## Fixed host-effect amendment (2026-10-27)

[Decision156](decision-156.md) adds a bounded fixed-route host-action lane,
original-process observer stop, independent durable outcomes and finite diagnostic
reads. It preserves archive serialization, original operation identity and this
record's unrelated requirements. Implementation and actual installed conformance
are separately required.

## Administration presentation amendment (2026-10-27)

The Administration workspace composes the existing scoped status, readiness and
version reads with protected host status, configuration, diagnostics, fixed host
actions and original-operation recovery. It creates no new authority or wire
schema. API readiness, reachable archive capacity, verification evidence,
metadata coverage and software identity remain separate observations. Failed,
stale or missing reads cannot supply healthy labels, zero counts or permission.
No observed full verification is explicitly unknown, including when the current
degraded flag is false. Bounded warning guidance navigates to a workflow without
submitting it; journal events remain diagnostics rather than operation results.

Schedule validation retains the exact submitted input and authenticated revision.
Every edit attempt retires local review; only explicit one-use confirmation may
submit the reviewed intent. Display actual normalized systemd text and label its
server/systemd interpretation without inventing a timezone field or converting
it to browser-local time. Observer review binds the original invocation; stopping
that observer never claims backend cancellation. Existing original-key lookup
and protected-outcome reads preserve uncertainty after reply loss. The
[Administration guide](../web-ui/administration.md) describes these workflows.

[Decision156](decision-156.md#implementation-and-presentation-status-2026-10-27)
records committed scoped native/rootless API-contract proof. Rendered
Administration controls have their own required acceptance; neither implies
production rollout or broader platform conformance.
