# Reuse parsed metadata only after reading identical authoritative bytes

- Decision identity: 157.
- Status: Accepted; amended as described below.
- Date: 2026-10-27.
- Record introduced: `c199c4af1d05356d56abe5a0b7b7c9b8f860ce48`.

## Context and decision

Repeated catalog queries parse the same complete reference and manifest bytes.
The original installed measurements missed the declared Library target after
correcting the browser collector's cache behavior. An isolated candidate reduced
the warm domain query from about 0.98 seconds to 0.63 seconds with identical output,
unchanged source and unchanged archive/configuration. This is evidence for an
optimization, not a browser-performance pass.

Keep every descriptor-anchored read and its byte/traversal accounting. After the
fresh bytes have been read, permit bounded process-local memoization of their
strict parsing into frozen `Reference` and `RevisionManifest` models. Keys contain
the exact byte string, the supported model family and the existing structural
depth/token ceilings. Equality compares bytes, without trusting a path, inode,
mtime, previously read digest or prior query result. The returned digest is
computed from the current read. All publication, generation, retention,
configuration and archive-identity joins remain outside this parsing step.

Retain at most 512 reference inputs of at most 4 KiB each and one manifest input
between 64 KiB and 8 MiB. These bounds retain at most 10 MiB of raw keys; decoded
models and concurrent reads require additional memory. Smaller manifests remain
uncached so they do not evict the large input during a catalog scan. Larger valid
records and every other model family retain normal uncached parsing. Invalid
records are never cached. Both supported families contain frozen models,
immutable tuples and scalar fields; mutable journal/operation state is excluded.
Eviction and process exit release entries. There is no persistent cache.

## Rationale and alternatives

Exact fresh-byte equality preserves the original validation result while avoiding
repeated CPU work. No filesystem check, query charge or current authority is
borrowed from an earlier request. The existing record/structure ceilings and
bounded metadata workers still apply.

Whole-query and path/inode/mtime caches were rejected because they could reuse
stale authority or bypass query accounting. Unbounded memoization was rejected
because metadata inputs are untrusted. A single slot for manifests of every size
was measured and rejected: small records evicted the large input on every scan.
Raising performance targets, weakening authentication or increasing record/read
limits does not address the measured repeated parsing cost.

## Consequences and evidence

Cold reads still validate completely. Alternating large inputs can evict each
other, so this is not a universal latency guarantee. Read failures, symlinks,
replacement, budget exhaustion and unknown schema versions still refuse before
cached parsing can confer any evidence. Public formats, permissions and runtime
dependencies are unchanged.

This refines [AD-12](ad-12.md), [bounded reads](decision-113.md) and the
[presentation refinement](decision-145.md). Contracts are in
[discovery](../discovery.md#queries-coverage-and-pages),
[server ownership](../server.md) and [INV-018](../invariants.md#tags-and-supplemental-discovery-metadata).
The implementation in [catalog storage](../../src/hfcache/catalog_storage.py)
performs `MetadataReader.read` before parser reuse and recomputes SHA-256 from
that read. Separate bounded parser functions retain the two frozen model families;
current publication and observation joins remain in their callers. Product
[fresh-byte regressions](../../tests/unit/test_catalog_authority_cache.py) and
[read-boundary regressions](../../tests/unit/test_catalog_read_boundaries.py)
exercise these constraints. The implementation was introduced in `c199c4a`.
Domain timing comparisons above do not establish browser latency, retained memory
or native/rootless installed performance; those require measurements against
the selected artifact and declared fixture.
