# CAT-003: Add tag authoring to the existing repository configuration workflow

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 1 — Foundation |
| Depends on | [CAT-002](cat-002-configuration-tags-and-identities.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-003: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; completion evidence below records actual validation.

## Likely implementation touchpoints

cockpit/src/lib/config.ts; configuration.tsx; config-pipeline.ts; candidate-guard.ts; UI/unit tests; docs/cockpit.md and cockpit-plugin guides.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Extend RepositoryEntry with tags and handle legacy entries with omitted tags without mutation surprises. Add one tag input control to repository creation/editing with existing configured-tag suggestions, not category/group controls or a mandatory registry. Follow current UI conventions and accessible labels.

Preserve canonical tags through form/text switching, serialization, toggling enabled, candidate validation, preview selection, backup/install and cancellation. Display normalization clearly and use backend validation as authority. Tags do not force sizing/download previews for an otherwise unchanged target.

Audit candidate/base equality and optimistic guards: a tag-only edit must not disappear because the backend policy fingerprint is unchanged. Preserve the existing full content/base guard; do not replace it with the curation fingerprint alone. Reject stale concurrent edits without overwriting operator changes.

Keep host installation privilege boundaries unchanged. Initial suggestions can use tags in the candidate/installed config; do not depend on unimplemented REST routes or make direct archive access a new UI requirement. Future discovery can use the API-backed CLI without changing installation authority.

## Acceptance criteria

Operators can add and edit tags at sync configuration time. Legacy rows render safely; values round-trip through all edit/install paths. Concurrent tag-only edits trigger the right conflict checks. UI help explains flat labels and normalizer behavior. Actual frontend tests/lint/build run and pass, not skip.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V05, V06, V07

Run the installed frontend gate (make -C cockpit check) and focused pipeline/guard tests, then scripts/check.sh with a genuinely executed Cockpit stage.

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

Implemented optional legacy-safe frontend tags, shared backend grammar fixtures,
free comma-separated entry and bounded current-config suggestions. Form/text
switching now serializes/parses the actual draft, preserving tag edits. Tags do
not affect sizing selectors; backend validation and authority checks remain final.

Retained exact candidate/base guards. Added a fixed installed-confirm action:
compare exact expected bytes under the retained root flock, invoke installed API
validation without candidate path, withhold bounded stdout until postchecks and
require successful confirmation process completion. The last condition is
necessary because ordinary CLI observers intentionally accept exact domain
Envelopes from nonzero processes. No generic invocation/path authority, new
credential source or validation wrapper field. Confirmation tests preserve
backup/lock and reject tag-only races before/during validation.

Reviewed CP-02/03/08/11/12, INV-001/002/005/018, decisions 119/122/133. Updated
CP-11 human contract, invariant and ADR122 amendment plus usage/troubleshooting
and discovery support labeling. This implements existing exact-content authority;
no new architectural decision or runtime dependency. Actual frontend and full gates passed, including final output-bound regression.
When work starts, record any relevant newer-source reconciliation, implementation
choices, blockers and scope amendments here. Preserve prior completed evidence.

## Completion evidence

Completed 2026-10-19 (CAT-003, this commit). V05–V07 have shared backend/frontend
grammar fixtures, canonical draft/form/text/toggle/add/remove checks, tag-only
no-sizing pipeline checks and real shell fixtures for stale tag-only base/candidate
content, successful confirmation after candidate rename, during-validation tag
changes, bounded stdout, predecessor/lock preservation and rejected-process
success Envelopes. No registry, archive access, config API or extra operator fields.
Independent read-only review found the confirmation output/process edge, corrected
before final gate; final review found no further material issue.

`rtk proxy make -C cockpit check PNPM=/home/tyler/.local/share/pnpm/bin/pnpm`
actually executed lint/types, 168 tests and build; final focused guard/runner run
passed 36 tests including the added output-bound case. `rtk proxy scripts/check.sh`
exited 0: 4351 passed, 40 opt-in deselected in 484.73s; build, three locked
installation profiles and actual Cockpit lint/types/169 tests/build passed.
Final docs alignment (182 documents/19 helpers) and whitespace checks passed.
Reviewed CP-02/03/08/11/12, INV-001/002/005/018, decisions 119/122/133; amended
CP-11/ADR122 for exact content plus successful confirmation completion. No new
architectural choice/dependency. Updated Cockpit contract/guides and discovery.
All execution used owned fixtures; no production config/service/credential/live
archive action or push. CAT-004 is next; no later package has started.
