# Separate curation from publication authority

- Decision identity: 133.
- Status: Accepted contract; corresponding interfaces require implementation.
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
REST/client acceptance precedes five proposed additive MCP tools; existing nine
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
