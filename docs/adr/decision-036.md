# Separate archive initialization from storage primitives

- Decision identity: 036.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Context, decision and consequences

storage.py owns mount metadata, atomic writes, probes, same-filesystem proof and
sentinel reading. archive.py owns known-layout initialization, empty-published
adoption, inspection and sentinel-last creation. A shared sentinel reader supplies
identity facts while callers decide mismatch meaning. This boundary avoids mixing
one-time creation policy into every existing-archive safety check and keeps tests
organized around the corresponding subjects.

## Provenance and governing evidence

The source entry first appears in
[b8f11c1](https://github.com/wtcross/hfcache/commit/b8f11c120552febe4a75e420b7a7325c4b5eae99)
(2026-07-25, `storage primitives: implement the sentinel check and split archive.py out of
storage.py`). The decision retains its rationale, alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/archive.py](../../src/hfcache/archive.py),
[src/hfcache/storage.py](../../src/hfcache/storage.py).

Relevant verification:
[tests/unit/test_archive.py](../../tests/unit/test_archive.py),
[tests/unit/test_storage.py](../../tests/unit/test_storage.py).
