# Separate curation from publication authority

- Decision identity: 133.
- Status: Amended contract; corresponding interfaces require implementation.
- Replacement design: see the 2026-10-20 amendment below; executable conformance remains pending.
- Date: 2026-10-19.

## Context and decision

Operator labels must be immediately searchable without new publications or changed
integrity evidence. Current config owns current tags. A strict historical snapshot
records only actual last writer-observed tags; it cannot be reconstructed from
present config. Derived technical observations bind exact retained publication
identity and manifest evidence. Preserve the operational policy hash and introduce
separate curation/catalog identities. Tags confer no authorization or file policy.

Permit optional `published/metadata/` records and approved directory creation as
independently atomic idempotent units under the sole local writer lock, initialized
identity, storage preflight and unfinished-journal guards. This is the only new
FS-17/TX-01 exception. No multi-file atomicity, replay, automatic cleanup or change
to existing transactions/catalogs is authorized. Unsafe/unsupported prior records
remain preserved and refuse replacement.

## Rationale and alternatives

Putting mutable tags in immutable manifests would redefine publication evidence.
A second tagging database would duplicate current configuration authority.
An aggregate search index would require another consistency boundary. Per-record
atomic JSON gives whole records after crashes while exposing partial coverage.
Historical labels have a deliberately narrower authority than publication data.

## Consequences

Queries are bounded metadata-only readers without payload, writer, Hub or credential
capabilities. Technical predicates bind the same complete eligible variant; missing
observations stay unknown. Rows come from configuration and retained references. Retained references gate
publication matches, so leftover records cannot resurrect deleted publications. Back up historical labels. Preserve old
fingerprint goldens, candidate byte comparisons and existing strict read wrappers.
REST/client acceptance precedes five explicit additive MCP tools; existing nine
remain the current registered set until implemented. Whole-archive trust remains.

New tags/layout/operation kinds may block old binaries. Actual disposable-fixture
compatibility tests must establish rollback barriers; never delete state to force
startup. No new runtime dependency or production operation is approved.

## Evidence and relationships

- [Discovery contract](../discovery.md), [schemas](../schemas.md#17-supplemental-discovery-records),
  [INV-018](../invariants.md#tags-and-supplemental-discovery-metadata).
- Amends [AD-12](ad-12.md), [AD-14](ad-14.md), [AD-17](ad-17.md),
  [119](decision-119.md), [122](decision-122.md), [125](decision-125.md).
- [Strict record models](../../src/hfcache/catalog_models.py),
  [atomic adjunct store](../../src/hfcache/catalog_storage.py) and
  [failure/identity/preservation tests](../../tests/unit/test_catalog_storage.py)
  enforce the record boundary with caller-held lock/preflight and bounded JSON.
- Contract review inspected config fingerprint enumeration, safe atomic writes,
  layout validation and candidate byte comparisons. Parser, storage, capability
  and compatibility evidence must accompany corresponding implementation.
- No production acceptance is claimed.
- [Typed offline refresh](../../src/hfcache/catalog_refresh.py) reserves finite
  scope/result capacity before writes and records independent per-record outcomes.
  Its TX-07 guard refuses unfinished archive work without applying recovery:
  automatic repair/prune/cleanup would exceed the metadata-only command's intent.
  [Reference inventory](../../src/hfcache/catalog_inventory.py) has one bounded
  no-follow reader; orphan instances and metadata snapshots confer no membership.
  [Service fixtures](../../tests/unit/test_catalog_refresh.py) and
  [existing-runner replay](../../tests/unit/test_catalog_refresh_replay.py) preserve
  offline scope, historical curation, partial progress and exact keyed observation.
- [Joined sync/repair capture](../../src/hfcache/catalog_capture.py) obtains fresh
  curation under the original lock without replacing admitted execution policy.
  [Lifecycle fixtures](../../tests/unit/test_catalog_lifecycle.py) preserve exact
  publications, retained generations, repair grace, immutable manifests and
  successful domain exits through optional failures. Bounded journal guards
  exempt only the exact active sync and validated committed-repair grace state.
- [Scoped weight declarations](../../src/hfcache/catalog_weights.py) bind explicit
  producer fields and safe indexes to one directory's unambiguous retained member
  set. [Counterexample fixtures](../../tests/unit/test_catalog_weights.py) retain
  missing/ambiguous/unsupported state without root-policy inheritance, tensor
  reads, runtime imports, unsafe deserialization or new dependencies.
- [GGUF headers/grouping](../../src/hfcache/catalog_gguf.py) use pinned primary
  mappings and bounded unbuffered access, with exact publication/directory/prefix
  shard identity and first-shard declaration authority. Tensor metadata provides
  safe extent checks and contradiction suppression without tensor-body reads.
  [Synthetic fixtures](../../tests/unit/test_catalog_gguf.py) cover unsupported,
  auxiliary, ambiguous and incomplete cases without inference dependencies.
- [Static source access/extraction](../../src/hfcache/catalog_extractors.py) and
  [conservative data parsers](../../src/hfcache/catalog_parsing.py) preserve
  AD-15 without new runtime dependencies. Shared actual-read/work limits include
  failed reads and skipped fields. [Hostile source fixtures](../../tests/unit/test_catalog_extractors.py)
  distinguish declarations from availability and upstream from operator tags.

- Shared catalog reads hash the visible projection rather than raw source digests.
  Historical curation hashes may encode suppressed labels, so public nullable
  curation fingerprints are withheld while durable provenance remains intact.
  Whole member bundles are suppressed when their membership is sensitive; nullable
  technical fields become unknown before matching. This concretizes the accepted
  redaction boundary without changing operational or curation fingerprint formats.
  [Query fixtures](../../tests/unit/test_catalog_queries.py) cover same-variant
  conjunction, exact retained identity, coverage, facets, cursor invalidation,
  secret-substitution invariance and absence of writer/payload capabilities.
- Authenticated REST catalog adapters reuse the existing metadata pool, lease
  lifetime, policy snapshot, error sanitizer and exact read wrapper. Keep the
  version-1 capabilities object unchanged: its existing reads permission covers
  additive routes, while OpenAPI advertises independent catalog schemas. New
  fields on that strict object would unnecessarily reject old clients. No
  command, writer or verifier dispatch is reachable from catalog GET handlers.
- Keyed writer-only refresh admission reuses the original serialized runner,
  guard hooks and exact operation observation. Canonical route and Envelope command
  identify the new kind; independent refresh result schema 1 leaves existing
  receipt/result-reference/Envelope fields unchanged. Current clients recognize
  the new operation route; older explicit allowlists may refuse it. Restart never
  reconstructs refresh intent or dispatches it to the private verifier.
- Base-client catalog reads validate pure independent payload models, exact
  requested detail/publication identities and complete ordered cursor walks. They
  retain archive/policy/catalog/coverage identity and fail on unfinished or oversized
  collection. Refresh result DTOs live in a pure module so observation imports no
  writer or optional framework. CLI search/tags/detail/variants use only REST,
  preserve first-server Envelope evidence and escape untrusted human text. Keyed
  refresh uses existing uncertain handles and never automatically resubmits.

The accepted MCP extension registers fourteen explicit names through separate
nine-method metadata and five-method catalog read ports. Catalog tools share REST
query semantics, bounded pool ownership and strict payloads. Dataset search omits
quantization knobs. Unknown arguments, dispatcher aliases and refresh attempts
refuse with fixed safe errors; no writable or credential capability enters tools.

Catalog secret checks also suppress casefolded registered values before visible
projection. Tag and technical identifier normalization can change case before
queries see values; exact-literal-only checks would expose those normalized
representations through results/counts/cursors. The stricter catalog check is
explicit and leaves ordinary exact output redaction semantics unchanged.

Actual isolated installed wheels from pre-feature 75d93a5 and deployed application
source 4088994 (both displayed 0.2.1) confirm the compatibility boundary. Tag-free
config validates; explicit tags, even empty, refuse. All 17 old goldens remain
identical/parseable. The old initialization inspector flags the optional metadata
directory in a controlled empty layout; ordinary published inventory still reads.
Strict old client route allowlists refuse refresh receipts, while generic stores
preserve completed results and old runner startup interrupts queued work without
replay. These are separate surfaces, not universal old-startup failure. Preserve
new state and validate a reviewed rollback target under actual executor drain.


## Replacement UI design amendment (2026-10-20)

[Decision 142](decision-142.md) amends this record for the accepted
replacement design. Accepted card adjunct design extends only the approved optional metadata namespace and bounded writer-owned README source-copy check; existing records, integrity confidence and read-only transport authority remain unchanged. Card conformance is pending.

## Independent card capture clarification (2026-10-25)

[Decision 142](decision-142.md#writer-capture-amendment-2026-10-25) now implements
writer capture in unreleased source. It adds independent cards under the approved
optional namespace without placing presentation in structured observations or
widening old request/result schemas. `technical=true` requests both outputs under
shared invocation limits; observation rows, statuses and counts remain truthful
to observations. Card failures add existing bounded `HFWRN011` warnings, while
absent README remains normal. The bounded fresh README digest is source-copy
provenance only and grants no verification confidence. Card API reads and display
remain separate later work; old-format compatibility requires an actual target
drill rather than inference from unchanged version numbers.

## Browser Library presentation amendment (2026-10-26)

The replacement Library presents the existing catalog, status and inventory reads
without a new endpoint or execution capability. The UI explicitly defaults to
repository scope `all`; the API's `archived` default is unchanged. Current versus
retained publications and current versus last-observed tags remain separate
sources. Literal ID/eligible-tag text is not README search or live Hub discovery.
All/any tag groups combine with the other predicates through AND; every model
technical predicate still matches one eligible variant in one publication.

Known repository matches, whole scoped coverage, loaded table rows and loaded
facet values retain their distinct meanings, including incomplete zero results.
Separately fetched inventory is joined by validated authority/type/ID and exact
publication pair, never list position or a presumed atomic global snapshot.
Logical sizes cannot become physical storage or hardware-fit claims. Bounded
fragment bookmarks preserve the existing query-free shell; API GETs retain
their supported query grammar. Changed filters reset continuations, stale pages
restart finitely and unsupported/incomplete responses remain explicit.

The [Library guide](../web-ui/library.md) documents the read workflow. Exact card
reads are implemented separately; repository details, README rendering and edit/
job forms are not implied by Library availability. Existing record schemas,
refresh counts, writer guards, MCP tools and immutable archive authority remain.

## Exact-publication detail composition amendment (2026-10-26)

WEB013 composes existing bounded reference, manifest, catalog/variant, card and
revision/history reads into type-aware repository detail pages. Resolve current
separately and retain the selected exact pair/generation across all publication
panels. Repair at the same SHA does not authorize adopting a different publication;
vanished retained identity remains unavailable. Missing or refused supplemental
evidence leaves independently valid manifest/inventory useful, without increasing
verification confidence. Model/dataset declarations retain source, status and
coverage; loaded archive history is not a complete repository audit. This adds no
writer, Hub, payload-serving or new durable-record authority. See the
[detail guide](../web-ui/repository-details.md). README rendering remains WEB014.

## Structured current-curation editing clarification (2026-10-26)

The browser editor composes the managed configuration boundary of
[decisions153](decision-153.md) and [154](decision-154.md); it adds no tag store,
CRUD endpoint or publication writer. Current configured tags are editable through
complete repository entries, including disabled entries. Last-observed unmanaged
labels remain historical and read-only; reconfiguration explicitly creates current
intent. A selected older publication does not select an older configuration to
edit. Disable/removal changes intent while preserving retained archive bytes.
Existing subsequent catalog reads reflect current curation without a refresh
mutation or rewriting historical snapshots. See the
[configuration guide](../web-ui/configuration-and-tags.md).
