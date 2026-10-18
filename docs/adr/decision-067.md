# Keep consumer verification independent of the writer runtime

- Decision identity: 067.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.

## Context, decision and consequences

The copy example belongs with consumer-facing examples, rather than operator
scripts that require a writer deployment. It is standard-library-only and works
from a trusted transferred helper/checkout plus a read-only export. Native releases
also ship examples; rootless trees do not universally provide that host path.

Reusing application verification would force a consumer to install the writer's
Python/Hub/model dependencies merely to read ordinary files. Independently checking
paths, sizes and SHA-256 against the pinned manifest avoids that dependency and
provides an independent interpretation of the format. Changed, missing and extra
file fixtures must all refuse. A disagreement with writer verification is evidence,
not a reason to skip a check. The helper's own 0/1/2 exits are separate from the
application taxonomy. Use a new revision destination, never a serving/current
path: an existing destination can be replaced by the helper's promotion procedure.

## Provenance and governing evidence

The source entry first appears in
[53afd69](https://github.com/wtcross/hfcache/commit/53afd6901631f1e7237ecdf2d190561d406ee127)
(2026-07-27, `operational tooling: consumer copy-and-verify helper and docs/consumers.md`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/consumers.md](../consumers.md).

Implementation or shipped-artifact evidence:
[examples/copy-revision.py](../../examples/copy-revision.py).

Recorded operational verification: [recorded deployment scope](../deployment-status.md). The source decision records independent damage drills for changed, missing, and extra files; there is no claim here that the later model-store script tests verify this original helper.
