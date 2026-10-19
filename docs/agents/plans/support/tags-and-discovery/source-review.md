# Reviewed baseline and source map

Reviewed on 2026-10-19; repository `wtcross/hfcache`, default branch `main`, commit
`45f91c3534244d8f2b360a68e79be3e58c97b239` (`DOC-019: complete documentation and script alignment audit`).
The connector's branch response identified this commit as current during review.
The active selector at that commit is inactive. This is static source/document
review, not a checkout execution, production inspection or live storage test.
A local clone could not be obtained in the artifact environment; selected source
and documentation were read through the connected GitHub service instead.

Every repository source below is pinned to the reviewed commit. At implementation,
read the real checkout and review intervening changes; do not reset it to this
baseline or replace newer contracts with this snapshot.

## Confirmed findings

| Area | Confirmed baseline | Consequence for this plan |
| --- | --- | --- |
| Agent planning | `AGENTS.md`, `docs/agents/planning.md`, `workflow.md` and the current selector use `docs/agents/plans/`; one work package is one task/commit | Add only new draft files; leave selector unchanged until implementation authorization |
| Documentation boundaries | The completed alignment plan separates human product docs from agent tracking | New human discovery docs must not link to CAT tasks or narrate task completion |
| Config | `RepositoryConfig` has identity/type/revision/enabled/dependencies, no tags; unknown fields refuse | Add a strict optional tags field and explicitly document old-binary rollback |
| Fingerprint | Config policy fingerprint enumerates repository operational fields explicitly | Preserve it; introduce separate curation/catalog identities and audit candidate comparison callers |
| Candidates | `services/candidates.py` validates TOML without network and compares six fixed installed-authority fields | Tags cannot bypass authority checks or create config-install authority |
| Archive evidence | `manifests.py` makes publication manifests immutable and checks path, size and arithmetic consistency | Do not inject mutable organization into existing manifests |
| Existing catalog | AD-12 / FS-16 reserve catalogs for derived data subordinate to manifests/refs | Historical tag snapshots need an explicit distinct, narrowly defined authority |
| Static metadata | `dependencies.py` reads known metadata as data, reporting ambiguity; no model execution | Reuse its static-inspection pattern, with stronger explicit input/resource bounds |
| Shared queries | `services/queries.py` has a narrow read-only protocol and authoritative configured/published inventory semantics | Extend via a catalog query service, not CLI subprocesses or a writable tool capability |
| REST | API docs define strict authenticated reads, bounded pagination and keyed writer operations | Add routes using existing wrappers, guards and admission rather than a new daemon |
| MCP | MCP guide and async metadata adapter expose nine named tools, separate bearer and read-only capability | Add five explicit tools only after REST; amend exact-set tests/contracts |
| Cockpit | `cockpit/src/lib/config.ts` has typed repository entries, parse/serialize and preview-selection helpers | Preserve tags across every editing path and retain candidate/base comparison |
| Gate | `scripts/check.sh` checks locked extras, formatting/lint/types, docs, offline tests, build and install profiles; frontend gate can loudly skip if tools missing | A skipped frontend gate cannot complete the Cockpit task |

## Pinned repository reading list

The following are source references, not files bundled or overwritten here.

- `AGENTS.md` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/AGENTS.md`
- `docs/agents/planning.md` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/docs/agents/planning.md`
- `docs/agents/workflow.md` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/docs/agents/workflow.md`
- `docs/agents/plans/current.md` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/docs/agents/plans/current.md`
- `docs/agents/plans/2026-10-18-plan-rest-mcp-docs-scripts-alignment.md` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/docs/agents/plans/2026-10-18-plan-rest-mcp-docs-scripts-alignment.md`
- `docs/configuration.md` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/docs/configuration.md`
- `src/hfcache/config.py` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/src/hfcache/config.py`
- `src/hfcache/services/candidates.py` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/src/hfcache/services/candidates.py`
- `src/hfcache/manifests.py` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/src/hfcache/manifests.py`
- `src/hfcache/dependencies.py` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/src/hfcache/dependencies.py`
- `src/hfcache/services/queries.py` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/src/hfcache/services/queries.py`
- `src/hfcache/api/mcp_reads.py` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/src/hfcache/api/mcp_reads.py`
- `docs/api.md` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/docs/api.md`
- `docs/mcp.md` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/docs/mcp.md`
- `docs/invariants.md` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/docs/invariants.md`
- `docs/adr/ad-12.md` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/docs/adr/ad-12.md`
- `cockpit/src/lib/config.ts` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/cockpit/src/lib/config.ts`
- `scripts/check.sh` — `https://github.com/wtcross/hfcache/blob/45f91c3534244d8f2b360a68e79be3e58c97b239/scripts/check.sh`

## Implementation touchpoints to inspect, not fully reviewed claims

Read relevant sections and callers rather than assuming a filename settles behavior:
`src/hfcache/paths.py`, `metadata.py`, `storage.py`, `sync.py`, `publication.py`,
`repair.py`, `retention.py`, `purge.py`, `recovery.py`, `services/commands.py`,
`services/mcp_queries.py`, `mcp_tools.py`, `mcp_server.py`, `api/app.py`,
`api/commands.py`, `api/command_models.py`, `api/operations.py`, `api/runner.py`,
`client.py`, `client_models.py`, `cli.py`, `cli_client.py`, server configuration
and installation checks. Discover actual names/callers if newer source reorganized them.
Proposed new modules in tasks are suggestions, not assertions that they already exist.

Review `cockpit/src/configuration.tsx`, `cockpit/src/lib/config-pipeline.ts` and
`candidate-guard.ts`, and their tests before changing edit/validation/install flows.
Read relevant `docs/agents/progress.md` decisions/handoff, environment, conventions,
release and technical-record policy at activation; this bundle does not reproduce
or renew any historical operational authorization.

Relevant architectural decisions include AD-01/06/07/12/13/15/17/18/20 and the
shared service, REST, operation, candidate, CLI and read-only MCP decisions
108, 113–120 and 125 referenced by current contracts. Use the actual ADR index to
locate amendments and allocate new decision numbers; do not preassign a potentially
colliding decision ID. Review FS-01/02/03/05–12/15–17/19/21–23 and TX-01/TX-07
where the new records touch their guarantees. Add new invariants only as precise
technical requirements with enforcement/tests, not as package-completion claims.

## External primary references checked for extractor design

These support a small subset of technical decisions; they do not authorize using
upstream loading/install examples or upgrading dependencies. At implementation,
pin the precise enum/spec version in fixtures and source comments where needed.

| Source | Relevant fact and implementation use |
| --- | --- |
| `https://github.com/ggml-org/ggml/blob/master/docs/gguf.md` | GGUF has typed metadata, optional general.file_type, named encodings and shard conventions. Filenames are not guaranteed perfectly parseable. Implement bounded header handling and cautious file grouping. |
| `https://huggingface.co/docs/transformers/en/quantization/awq` | Static quantization_config can declare quant_method, bits and group_size. Extract declarations without executing the loading examples. |
| `https://huggingface.co/docs/hub/en/model-cards` | Model cards have structured front-matter declarations, including tags/tasks/language/license/base model. Preserve origin; do not merge into local operator tags. |
| `https://huggingface.co/docs/hub/en/datasets-cards` | Dataset cards carry structured descriptive metadata. Treat declarations separately from physically verified dataset properties. |

GPTQ-specific supported static fields and safetensors index grouping must be
checked against current primary schemas/source during CAT-007. This bundle does
not claim every producer's quantization layout has been inspected or supported.

## Deliberate departures from the earlier discussion

The user accepted a tag-only organizational design. Consequently this bundle does
not carry forward categories/groups/curated use_cases or expected_variants.
It adds a paged model-variant detail tool in addition to search/detail/facets,
so all matches can be inspected without unbounded nested search results.
Historical tags mean last writer-observed labels, not guaranteed preservation of
uncaptured edits. No user-entered label is ever evidence of quantization availability.
