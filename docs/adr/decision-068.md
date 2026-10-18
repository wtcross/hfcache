# A prune's container cleanup is checkpoint 10, after the commit point, and its atomic act is `rmdir`

- Decision identity: 068.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.

## Decision, context, and consequences

The retention contract and
`docs/architecture.md` §7.4 both described a prune that tombstones the
publication instance and its manifest and then stops. Both are amended here,
because that leaves two directories that nothing ever removes.

What the documents missed. The instance is
`revisions/<sha>/<publication-id>/` and its manifest is
`manifests/<sha>/<publication-id>.json`, so tombstoning empties the `<sha>`
directory *above* each of them. Nothing derived is wrong when they linger —
`list`, `status`, the catalog, `next_generation`, and `verify` all resolve
through references, and all five were checked against the live archive after
the 2026-07-26 rotation. But they are permanent, they accumulate one pair per
pruned SHA, and they are in `published/`, so a consumer listing `revisions/`
sees SHAs the archive does not retain. The carried item named only the first
of the two; the second was found by looking at the live archive rather than at
the text.

**Where it goes, and why not earlier.** The obvious placement is right after
the two tombstoning steps, where the containers become empty. That is wrong,
and the reason is the rollback path. Before checkpoint 7 the transaction can
still be rolled back, and `recovery._rollback_prune` puts the tree and the
manifest back *into these exact containers*. Removing them pre-commit would
make the rollback recreate them, which adds a failure mode to the one path in
§7.4 whose entire purpose is to restore six revisions safely. Post-commit,
the revision is never coming back, and an empty directory is definitionally
cleanup — which is precisely the regime checkpoints 8 and 9 already occupy and
which §7.4 already says is the only thing retried later. The cost is a window:
a crash between 7 and 10 leaves the containers until the next `recover
--apply`. That is reportable, harmless, and tested.

**Why `rmdir` and never `rmtree`.** Two states require a container to survive
its own SHA being pruned, and both are real: a repair inside its grace period
leaves the retired instance beside the replacement, so `revisions/<sha>/`
holds two instances; and a superseded manifest can sit beside the tombstoned
one. `rmdir` refuses a non-empty directory, so neither state needs to be
detected, and the code cannot be wrong about them — the kernel is. `rmtree`
would silently take both. `FS-19` is the rule this satisfies: the application
removes a directory it has *proven* empty, not one it has decided is unwanted.
`ENOTEMPTY` and `EEXIST` are the two answers POSIX permits for that refusal
and both are treated as "keep"; `ENOENT` is idempotence (`TX-04`); anything
else propagates, because reporting a permission failure as though the
directory had merely been busy would hide it forever.

The live archive was brought into conformance in the same commit rather than
left as a documented exception, because `operational tooling` documents this tree's shape
next and a runbook describing a shape the archive contradicts is worse than
either. The removal used `rmdir`, which cannot destroy content;
`verify --full` afterwards read 23 unique objects across 6 revisions and
reported `clean`.

## Later history and current interpretation

The container-cleanup boundary and empty-directory-only rule remain applicable.
Counts of six retained revisions describe the then-current five-revision policy;
[decision 102](decision-102.md) changes the default to three while allowing
explicit five.

## Provenance and governing evidence

The source entry first appears in
[5dc8d0a](https://github.com/wtcross/hfcache/commit/5dc8d0aa24f81f485ea0d2d81cdd149c5b726df2)
(2026-07-27, `retention: remove the containers a prune empties`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/schemas.md](../schemas.md).

Implementation or shipped-artifact evidence:
[src/hfcache/retention.py](../../src/hfcache/retention.py),
[src/hfcache/recovery.py](../../src/hfcache/recovery.py).

Relevant verification:
[tests/unit/test_retention.py](../../tests/unit/test_retention.py),
[tests/unit/test_crash_injection.py](../../tests/unit/test_crash_injection.py).
