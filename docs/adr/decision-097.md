# A completed 0.1.5 purge is operationally readable by 0.1.4; an open one is the rollback barrier

- Decision identity: 097.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-08-15.

## Decision, context, and consequences

The cross-format drill wrote
the new `PurgePlan` and purge-reason record through the real 0.1.5 CLI on an
isolated NFS archive. Installed 0.1.4 ignored the resolved journal exactly
as intended: `status` and `recover --dry-run` were clean, and a real
re-add/sync preserved generation 1 using the archived manifest. Its direct
`PrunedRevisionRecord` parser rejected
`operator_requested_repository_purge`, but no normal completed-purge read
path needs that record. Therefore rollback requires no open purge journal;
completed purge state is otherwise command-compatible, while direct audit
tooling stays on 0.1.5. **Rejected:** declaring every completed purge a
rollback blocker, because the old commands demonstrably consume the state;
and weakening the record reason to an older value, because that would make
the audit lie about why the complete repository disappeared.

## Later history and current interpretation

This is the exercised 0.1.5-to-0.1.4 rollback result, not a blanket promise for
all older versions or all audit readers. The open-journal barrier and
direct-parser limitation remain explicit.

## Provenance and governing evidence

The source entry first appears in
[f49edd9](https://github.com/wtcross/hfcache/commit/f49edd969b9cd103559260c7092c17a4d78a1468)
(2026-08-15, `release preparation: cut and compatibility-check 0.1.5`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents:
[docs/deployment-centos-stream-10.md](../deployment-centos-stream-10.md).

Implementation or shipped-artifact evidence:
[src/hfcache/models.py](../../src/hfcache/models.py),
[src/hfcache/recovery.py](../../src/hfcache/recovery.py).

Relevant verification:
[tests/unit/test_purge.py](../../tests/unit/test_purge.py).
