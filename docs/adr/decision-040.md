# Keep local lock lifetime separate from storage checks

- Decision identity: 040.

Status: accepted when recorded; amended by [decision 110](decision-110.md).
Retained as historical evidence. Dated implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Context, decision and consequences

The common lock lives outside NFS under /run/hfcache and is held through the
actual operation, not checked once as a storage property. A dedicated locking
module keeps ownership/lifetime separate from storage primitives and diagnostic
ordering. Non-estimate verification, probing doctor and explicit initialization
honor the service-owned common-lock rules; read-only inspection remains distinct.

Use flock rather than a PID file: kernel ownership follows the open file
description and ends when real holders close/die. Never unlink its inode. The
holder record is diagnostic, never liveness or deletion authority; clearing it on
release avoids stale holder messages. In API/rootless execution a client/wrapper
exit does not prove real holders ended. Decisions 110/115/121 qualify operation,
worker and daemon/store lock lifetimes independently.

## Provenance and governing evidence

The source entry first appears in
[0f643a8](https://github.com/wtcross/hfcache/commit/0f643a83a16b863b4cc4e9a5eaab8e762d76f1a0)
(2026-07-25, `storage primitives: implement the local exclusive lock every mutating command
takes`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/security.md](../security.md).

Implementation or shipped-artifact evidence:
[src/hfcache/locking.py](../../src/hfcache/locking.py).

Relevant verification:
[tests/unit/test_locking.py](../../tests/unit/test_locking.py).

## guarded command services amendment (2026-10-17)

[Decision 110](decision-110.md) tightens the common-lock boundary: every
non-estimate verification proves storage safety and retains ownership through
scope resolution, hashing, report persistence and complete catalog merge.
Probing doctor and explicitly confirmed initialization also own the common
lock, while using their own checks so uninitialized storage remains diagnosable
and initializable. Read-only doctor and initialization inspection take no lock.
Public command services acquire once; adapters/runners must not pre-lock them.
This amendment changes no durable schema or systemd scheduling authority.
