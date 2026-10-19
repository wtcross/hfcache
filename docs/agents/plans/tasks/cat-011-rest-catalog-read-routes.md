# CAT-011: Expose authenticated bounded REST catalog reads

| Field | Value |
| --- | --- |
| Status | complete |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 4 — REST and CLI |
| Depends on | [CAT-010](cat-010-catalog-queries-and-facets.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-011: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
The status above and completion evidence below own execution truth.

## Likely implementation touchpoints

api/app.py and proposed api/catalog.py/query models; capabilities/OpenAPI; shared read response and pagination adapters; REST tests.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Add the four read routes in design section 9, using shared service DTOs, existing ReadResponse/Envelope conventions, archive/policy identity and the new catalog payload identity. Preserve public-prefix/Unix/HTTPS and pre-routing authentication behavior. A detail route must not embed an unbounded list of variants.

Validate repeated tag parameters versus scalars, strict numbers, known allowed keys, paired exact publication identity, URI component grammars, total query/header/body budgets and no arbitrary paths/URLs. Existing repository routes and strict old wrappers must retain their behavior.

Bind cursors to normalized query, route, curation, authoritative selected publications, visible observations and coverage. Equivalent set permutations canonicalize; relevant tag-only/source changes refuse continuation with existing classified stale-cursor semantics. Do not silently continue partial results or expand scan limits for small pages.

Use existing bounded metadata executor/lease/response lifecycle, sanitization and classified failures. Update capabilities/OpenAPI and version compatibility deliberately, accounting for strict base clients. Add current human API/discovery documentation alongside implementation, not only at final acceptance.

## Acceptance criteria

REST reader/writer can search, inspect variants and enumerate facets; wrong credential classes and invalid requests refuse. Cursors and encoded response bounds pass race/adversarial fixtures. Existing routes and clients remain green. No write or network work is reachable from these handlers.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V36, V37, V38

Real in-process HTTP tests for auth, query/body grammar, cursor identity/races, response budgets and old-route compatibility; full gate.

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

Four explicit authenticated GET routes use the shared reader and existing pool,
lease, renderer and fresh policy. Strict keys/repetitions/numbers/body/exact pairs
refuse safely. Model-only variants refuse at both route and shared core; unknown
dataset format spellings remain partial/unknown. OpenAPI advertises independent
catalog schemas and constraints. Existing capabilities/API version and wrappers
remain exact; reads already covers the additive routes.

The first full gate was interrupted (130) to tighten model-only/OpenAPI behavior.
The next full gate reported three independent route-audit failures (4866 passed,
40 deselected in 535.43s). Added the four exact methods to the independent security
inventory and human route reference, plus actual named HTTP evidence; no fabricated
unimplemented CLI parity. A further in-progress gate was interrupted (130) after
taxonomy review: absence now uses HFAPI007/404/10, unsafe namespace uses
HFVER007/409/40, and hidden exact identities refuse uniformly before membership.
All these runs remain historical evidence, never passing gate claims.

## Completion evidence

Completed 2026-10-19 (CAT-011, this commit). Expanded query/storage/HTTP and
independent REST security/parity/pagination/transport selection: 208 passed in
15.15s. Ruff and focused Pyrefly pass (zero errors). Final `scripts/check.sh`
exited 0: 4875 passed, 40 deselected in 535.67s; wheel/sdist, all three locked
installation profiles and actual Cockpit lint/types/169 tests/build passed.
Reviewed INV-012/014/015/016/018, relevant FS/AD rules and decisions 108,
113-120/125/133. Human API/server/discovery contracts, invariant and ADR links
are current; no existing transaction, confidence, dependency or MCP tool changes.
[Progress](../../progress.md) records completion. Next is CAT-012. No deployment,
production/live workload, credential access, host change or push was performed.
