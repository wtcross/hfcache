> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 069: There is no `tests/integration/`; the tier lives beside its fixtures, and §26.6's map is a test rather than a comment

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.
- Original work package: `OPS-005`.
- Source: [decision 69 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan
§7 listed `tests/integration/` from Phase 0 and it never held anything but
`.gitkeep`. Two ways to resolve that, and the plan is amended rather than the
tree populated.

The reason is not effort. §26.2 names eighteen integration behaviours — first
sync, sixth-revision rotation, interrupted publication at each transaction
boundary, corrupt catalog reconstruction, and so on — and **every one of them
exists and passes**. They sit in `tests/unit/` because they share the fixtures
of the modules they exercise: `client`, `layout`, `config`, and the injectable
fake Hub. Moving them would separate each from the fixture that builds its
world, and would need those fixtures duplicated or promoted into a conftest
serving two directories, for no gain in what is tested.

The deeper reason is that the tier boundary does not fall where the directory
split would put it. `tests/unit/test_synchronize.py` holds both a pure
retention-ordering assertion over in-memory objects and a full six-revision
publish-and-prune cycle against a fake Hub and a real temporary filesystem.
Those are a unit test and an integration test by any definition, they are
fifty lines apart, and they belong together because they are about the same
thing. A directory that sorted them would be sorting by a property nobody
reading the file cares about.

What the empty directory *was* hiding is worth stating, because it is the
real defect and it is not a layout problem: the whole §26.6 failure-injection
matrix lives in `tests/unit/test_repair.py`, whose name suggests it holds
repair tests. It holds the publication boundaries, the prune boundaries, the
recovery remedies, and the repair switches — twenty-four crash injections
through one `crash_at` helper. Nothing pointed at them, and the coverage
claim in plan §28 had to be re-derived by reading them.

So `tests/unit/test_failure_matrix.py` is the index, and it is executable:
it names the covering tests for each of the eleven points and asserts every
name still resolves. It found a wrong attribution in itself on its first run.
Renaming `test_repair.py` to match its contents was the other candidate and
was rejected as churn against a green suite with the phase unfinished; the
map makes the location discoverable, which is what was actually missing.

## Later history and current interpretation

Partially superseded by [decision 76](../../../../../adr/decision-076.md): the formerly deferred
`test_repair.py` rename was performed as `test_crash_injection.py`. The
executable coverage matrix and shared-fixture organization remain.

## Provenance and governing evidence

The source entry first appears in
[69323a9](https://github.com/wtcross/hfcache/commit/69323a95a4fc932aaf7e53f91a285de9d6a0e0e9)
(2026-07-27, `OPS-005: close §26.6's failure-injection matrix`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents:
[docs/agents/conventions.md](../../../../conventions.md),
[docs/agents/history/plan.md](../../../plan.md).

Implementation or shipped-artifact evidence:
[tests/unit/test_crash_injection.py](../../../../../../tests/unit/test_crash_injection.py).

Relevant verification:
[tests/unit/test_failure_matrix.py](../../../../../../tests/unit/test_failure_matrix.py).
