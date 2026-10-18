# Tag the deployed tested artifact with proportionate release scope

- Decision identity: 075.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.

## Context, decision and consequences

The historical 0.1.2 release identified the actual installed/tested tree rather
than choosing a tidier version for an untested artifact. Earlier 0.1.0/0.1.1 trees
remained useful predecessors for exercising a real rollback, rather than merely
rewriting one selector. Retain at least the predecessor.

A 1.0 claim would have overstated unfinished consumer export, data protection,
other-host disjointness/copying, reboot and calendar acceptance. An annotated tag
records the tested scope; a version number does not certify outstanding operator
work. Current release/acceptance status belongs to the changelog and dated
deployment status, not this historical selection rationale.

## Provenance and governing evidence

The source entry first appears in
[e62ddbc](https://github.com/wtcross/hfcache/commit/e62ddbcf09376c3ad531c607faf3ee7f51b4fd25)
(2026-07-27, `release preparation: tag and document the first release`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents:
[CHANGELOG.md](../../CHANGELOG.md).

Implementation or shipped-artifact evidence:
[pyproject.toml](../../pyproject.toml).

Verification or recorded operational evidence:
[recorded deployment scope](../deployment-status.md).


## 2026-10-18 data-preserving local rollout amendment

[Decision 126](decision-126.md) records new local-host release/rollout authority
with an absolute NAS content/metadata-write ban and no other-host changes. Retain
artifact identity, actual-executor quiescence and state/lock preservation; live
sync/full verification/archive-write acceptance is forbidden and remains NOT RUN.
Any local deployed tag records this partial acceptance explicitly. No remote push
or ACME issuance is authorized. Rootless runtime design/proof belongs to rootless runtime.
