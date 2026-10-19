# Configuration tags and evidence-backed model/dataset discovery

| Field | Value |
| --- | --- |
| Status | active |
| Created | 2026-10-19 |
| Authorization | User explicitly requested implementation and the linked execution instruction on 2026-10-19; scoped offline implementation is authorized. |
| Reviewed repository / branch | `wtcross/hfcache` / `main` |
| Reviewed commit | `45f91c3534244d8f2b360a68e79be3e58c97b239` |
| Implementation branch | `feat/tags-and-discovery`; never implement on `main` |
| Tracker | `docs/agents/plans/current.md` |
| Selector at review | Inactive; no active plan. Recheck actual checkout before activation. |
| Task authority | Linked task files own status, requirements, dependencies and evidence. |

## Outcome and scope

Make model/dataset organization a single `tags` list configured alongside each
sync repository. Expose local discovery by tags and structured technical evidence
through REST, the API-backed CLI and then the read-only MCP server. A user can add
an entry tagged `coding` and `local-inference`, find it immediately as configured,
and later find a retained GGUF `Q4_K_M` variant with exact publication identity.
Datasets share the same tag vocabulary and scope rules without model-only fields.

This is a drop-in **draft plan bundle**, not executable implementation, installation
or authority to operate the live writer. The bundle deliberately supplies no
replacement `current.md`, no root configuration and no modified application code.

### Required user-facing results

- One optional direct `[[repositories]].tags` field; no categories, groups,
  curated use_cases, expected_variants, hierarchy or parallel annotation system.
- Config-time authoring through current TOML/Cockpit flows, normalized labels and
  existing-value suggestions. Tags are labels, not auth, retention or file filters.
- Fresh configured-tag search without syncing; disabled repositories retain tags;
  unmanaged retained repositories show only honestly recorded historical labels.
- Structured exact-publication model variants with format/scheme/method/bit-width,
  member completeness, size and provenance. Technical filters match one variant,
  not a repository-wide union of unrelated facts. Dataset facts remain static,
  attributed observations, never loader execution or inferred physical splits.
- One bounded transport-neutral query service, stable ALL/ANY tag predicates,
  current/retained and configured/archived scopes, paged variant detail and facets.
- Writer-only offline refresh/backfill for metadata, using existing REST keyed
  operations. Reads never refresh, touch model payloads, contact Hub or write.
- REST and client/CLI completion before the five explicit MCP discovery tools.
  Preserve the existing nine tools and the actual narrow read-only capability.

### Explicitly out of scope

No live Hub search, semantic/vector/LLM search, model loading/benchmarking, runtime
compatibility or RAM/VRAM recommendations, selective downloads, implicit dependency
fetches, external dataset payloads, config-install/tag-edit REST API, MCP mutations,
new scheduler/database, automatic metadata garbage collection, tag registry,
per-repository ACLs, dependency upgrade or production rollout. Extra descriptive
operator fields are not needed to implement the agreed tags design.

## Read the supporting specifications

- [Start here](support/tags-and-discovery/START-HERE.md) — safe extraction and entry point.
- [Design](support/tags-and-discovery/design.md) — chosen technical behavior and boundaries.
- [Validation matrix](support/tags-and-discovery/validation-matrix.md) — 55 planned observable cases.
- [Pinned source review](support/tags-and-discovery/source-review.md) — baseline facts and source map.
- [Implementation prompt](support/tags-and-discovery/implementation-prompt.md) — authorization/start/resume instruction.
- [Proposed TOML fragment](support/tags-and-discovery/repositories.example.toml) and
  [query examples](support/tags-and-discovery/search-examples.json) — fictional, not deployed examples.

The design supplements this plan but cannot silently supersede a living contract.
CAT-001 records/amends the affected contract before code depends on changed behavior.
No supplied assertion is evidence that an implementation test has passed.

## Contracts, invariants and architectural decisions

Read only the relevant sections of `docs/configuration.md`, `docs/discovery.md`
(new), `docs/architecture.md`, `docs/schemas.md`, `docs/invariants.md`,
`docs/security.md`, `docs/api.md`, `docs/server.md`, `docs/api-client.md`,
`docs/cli.md`, `docs/mcp.md`, `docs/cockpit.md`, `docs/consumers.md`,
`docs/operations.md` and the current ADR index. Agent workflow authority is
`AGENTS.md`, `docs/agents/planning.md`, `workflow.md`, `invariants.md`, environment,
release and technical-record policy under `docs/agents/`.

Preserve AD-01 complete snapshots, AD-06 non-deletion on errors/config removal,
AD-07 no implicit dependency resolution, AD-12 filesystem authority, AD-13 exact
repair identity, AD-15 no execution, AD-17 sole writer/local lock and AD-18 integrity
provenance. Review FS-01/02/03/05–12/15–17/19/21–23 and TX-01/TX-07 around the new
namespace. Keep the full set of unrelated retention/recovery/capacity/producer and
verification-worker invariants unchanged.

New historical tag records are not reconstructible from present config; distinguish
their historical-only authority from derived publication observations. The design
requires an explicit narrow independent-atomic-file exception for supplemental
metadata and approved layout extension, not a quiet weakening of transaction safety.
Amend relevant ADRs and add indexed technical decisions with new current IDs.
Preserve strict old policy fingerprints, read wrappers and original evidence formats;
assess new config/layout/operation-kind rollback barriers with real fixtures.

The current API, client and MCP architecture decisions referenced by contracts
include 108, 113–120 and 125. Review their amendments and exact allowlist/read
boundaries, not just this list. Human docs contain technical product behavior and
rationale, not work-package/task links or agent progress narration.

## Execution and authorization rules

When instructed to implement, inspect git log/status, the current selector and
recent relevant progress/handoff first. Review changes after the pinned baseline
and preserve unrelated work. Create/safely reuse `feat/tags-and-discovery` and
activate this plan; no additional activation approval is needed after an explicit
implementation instruction. If another plan is active, reconcile it explicitly
without silently abandoning work. Check CAT ID collisions before activation.

Run one task at a time, normally in table order, with dependencies authoritative
in its task file. Parallel work is not authorized by this plan. If a task is blocked,
record the exact missing prerequisite and a current-selector pointer; another ready
in-scope task may proceed serially. Do not fake a dependency completion. Split a
package that cannot remain one coherent passing commit by adding unused IDs/tasks
and recording an in-scope amendment; never renumber completed packages.

For each package: mark in progress, review/amend contracts, implement, run focused
checks and `scripts/check.sh`, complete acceptance/evidence and human docs, update
ADR/invariants/progress/current pointers, then commit `<CAT-ID>: <summary>`. One
work package is one commit. Do not squash away package boundaries, mark a red or
skipped required gate green, or defer all documentation until the final package.

No git push/force push/merge, release tag, deployment, service or timer changes,
SELinux/systemd weakening, registry publication, live Hub/NFS tests, credential
access, archive init or live `/srv/hfcache` operation is authorized. Historical
host authorizations do not carry forward. The checkout may be on the live writer;
use offline temporary fixtures and read the environment limits before host work.
Leave code committed on the feature branch and provide an operator handoff.

## Phases and ordered tasks

Task files, not this table, own mutable status. This graph deliberately allows
metadata work to proceed serially if the frontend toolchain blocks CAT-003, but
final acceptance still requires an actually executed frontend gate.

| Order | Phase | Work package | Depends on |
| --- | --- | --- | --- |
| 1 | 1 — Foundation | [CAT-001 — Activate the feature plan and establish technical contracts](tasks/cat-001-contracts-and-activation.md) | None |
| 2 | 1 — Foundation | [CAT-002 — Add strict configuration tags and separate curation identity](tasks/cat-002-configuration-tags-and-identities.md) | CAT-001 |
| 3 | 1 — Foundation | [CAT-003 — Add tag authoring to the existing repository configuration workflow](tasks/cat-003-cockpit-tag-authoring.md) | CAT-002 |
| 4 | 2 — Metadata foundation | [CAT-004 — Implement bounded versioned tag snapshots and publication observations](tasks/cat-004-metadata-records-and-storage.md) | CAT-002 |
| 5 | 2 — Metadata foundation | [CAT-005 — Extract bounded static model and dataset declarations](tasks/cat-005-bounded-static-metadata-extraction.md) | CAT-004 |
| 6 | 2 — Metadata foundation | [CAT-006 — Detect GGUF formats, quantization schemes and complete variant sets](tasks/cat-006-gguf-variants-and-shards.md) | CAT-005 |
| 7 | 2 — Metadata foundation | [CAT-007 — Detect scoped AWQ/GPTQ weight-bundle declarations](tasks/cat-007-quantized-weight-config-variants.md) | CAT-005, CAT-006 |
| 8 | 3 — Writer lifecycle | [CAT-008 — Integrate supplemental metadata capture with existing sync and repair](tasks/cat-008-sync-metadata-lifecycle.md) | CAT-004, CAT-005, CAT-006, CAT-007 |
| 9 | 3 — Writer lifecycle | [CAT-009 — Add a typed writer-only offline catalog refresh service](tasks/cat-009-offline-refresh-service.md) | CAT-004, CAT-005, CAT-006, CAT-007 |
| 10 | 4 — REST and CLI | [CAT-010 — Build shared tag and variant search with truthful coverage and facets](tasks/cat-010-catalog-queries-and-facets.md) | CAT-002, CAT-004, CAT-005, CAT-006, CAT-007 |
| 11 | 4 — REST and CLI | [CAT-011 — Expose authenticated bounded REST catalog reads](tasks/cat-011-rest-catalog-read-routes.md) | CAT-010 |
| 12 | 4 — REST and CLI | [CAT-012 — Expose writer-only keyed offline refresh operations](tasks/cat-012-rest-catalog-refresh-admission.md) | CAT-009, CAT-011 |
| 13 | 4 — REST and CLI | [CAT-013 — Add typed API client and CLI discovery and refresh commands](tasks/cat-013-catalog-client-and-cli.md) | CAT-011, CAT-012 |
| 14 | 5 — MCP | [CAT-014 — Expose five explicit read-only MCP discovery tools](tasks/cat-014-read-only-mcp-catalog-tools.md) | CAT-013 |
| 15 | 6 — Acceptance | [CAT-015 — Prove read-only, bounded and cross-transport discovery behavior](tasks/cat-015-adversarial-and-parity-validation.md) | CAT-003, CAT-008, CAT-014 |
| 16 | 6 — Acceptance | [CAT-016 — Complete lifecycle compatibility drills, documentation and plan handoff](tasks/cat-016-compatibility-docs-and-final-acceptance.md) | CAT-008, CAT-009, CAT-015 |

## Documentation delivered throughout implementation

| Area | Guides/contracts to create or update with behavior |
| --- | --- |
| Tags and authoring | `docs/configuration.md`, `docs/discovery.md`, examples, `docs/cockpit.md`, `docs/cockpit-plugin/` |
| Artifacts and provenance | `docs/schemas.md`, `docs/architecture.md`, `docs/invariants.md`, relevant technical ADRs, `docs/security.md` |
| Search and operations | `docs/api.md`, `docs/server.md`, `docs/operations.md`, `docs/discovery.md` |
| Reader workflows | `docs/api-client.md`, `docs/cli.md`, `docs/quickstart.md`, `docs/consumers.md` |
| MCP | `docs/mcp.md`, tool examples, security/consumer docs and exact allowlist references |
| Release/compatibility/navigation | `README.md`, `docs/README.md`, `CHANGELOG.md`, developer/install/rollback guides where affected |
| Agent-only execution | This plan/tasks, `docs/agents/plans/current.md`, completed progress and Decisions/handoff |

Update the supported script catalog only for real shipped-script changes. Do not
add links to this bundle in human docs or turn its examples into install scripts.
Do not update recorded deployment status as though feature code has been deployed.

## Plan acceptance and validation

The plan is complete only when all scoped task criteria are met and V01–V55 have
actual appropriate evidence. In particular: tag-only edits are immediately
searchable; disabled and unmanaged behavior is truthful; old evidence is unchanged;
no query can write/refresh/network/read payloads; same-variant constraints and
facets are correct; technical coverage is honest; metadata-only work is bounded;
REST/CLI and MCP agree; credentials and exact read-only capabilities remain confined.

Every package passes `scripts/check.sh`; every frontend change requires real
frontend execution. Final acceptance runs `scripts/check.sh --with-build` plus
lifecycle/old-binary compatibility and all installation-profile tests, with the
frontend stage actually executed. Use offline synthetic data, never real weight
downloads. Record baseline or toolchain blockers without suppressing failures.
Offline evidence does not establish NFS semantics, production fit or deployment.

Audit all commits, contracts, invariants/ADRs, docs, task statuses and current
selector. Complete this plan and clear its selector only after acceptance, retaining
the original dated paths and task IDs. Do not silently cancel necessary scope to
claim completion. Final handoff states implementation results, verification scope,
compatibility barriers and any separate operator prerequisites.

## Lifecycle and amendments

- 2026-10-19: Draft bundle created for the user's accepted tag-only organization and
  model/dataset discovery design. No implementation, activation, repository commit,
  test execution, deployment or live archive action performed by this draft.

- 2026-10-19: Activated on `feat/tags-and-discovery` from `75d93a5`. The
  sole intervening commit after reviewed `45f91c3` is operational evidence for
  the separate Timestral task; source/contracts are unchanged. Its completed
  plan and guard-held operation remain preserved and are not selected here.
  CAT-001–016 and decision 133/INV-018 were checked for collisions; none exist.
  The supplied bundle is retained intact except explicit lifecycle/evidence updates.
