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
- Contract review inspected config fingerprint enumeration, safe atomic writes,
  layout validation and candidate byte comparisons. Parser, storage, capability
  and compatibility evidence must accompany corresponding implementation.
- No production acceptance is claimed.
