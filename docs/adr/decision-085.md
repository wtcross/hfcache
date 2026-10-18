# Keep storage requirements portable without weakening NFS safety

- Decision identity: 085.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-28.

## Context, decision and consequences

Storage administrators need a standalone server-neutral NFSv4.2 contract,
including TrueNAS Mapall and Linux all_squash equivalents, server-chosen IDs,
disjoint exports, snapshots and capacity. Reader onboarding instead needs endpoint,
protected REST source and verified HTTPS; it requires no writer mount or Hub source.
The audiences need separate guides rather than one host-specific transcript.

Reject relaxing FS-02 to allow an ordinary local directory for a writer evaluation:
missing NFS must fail instead of silently writing onto the VM filesystem. Owned
fixture mount proof is test-only, not a deployed local-filesystem bypass. Disposable
API/verifier/client rehearsals are separate from production installation and do
not change host NFS, guards, credentials or service managers.

## Provenance and governing evidence

The source entry first appears in
[6476c9b](https://github.com/wtcross/hfcache/commit/6476c9b8f85bc4c2fdfd0ccef8bb2711322adadd)
(2026-07-28, `documentation maintenance: storage requirements, quickstart, and README
requirements`). The decision retains its rationale, alternatives and consequences.

Current governing documents:
[docs/storage-requirements.md](../storage-requirements.md),
[docs/quickstart.md](../quickstart.md),
[docs/recovery.md](../recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/storage.py](../../src/hfcache/storage.py),
[src/hfcache/preflight.py](../../src/hfcache/preflight.py).

Relevant verification:
[tests/unit/test_preflight.py](../../tests/unit/test_preflight.py),
[tests/system/test_live_mount.py](../../tests/system/test_live_mount.py).
