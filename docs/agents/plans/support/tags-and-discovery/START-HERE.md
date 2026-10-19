# Start here: tags and discovery implementation bundle

This is a **draft implementation plan**, not an implementation or deployment.
Extract the ZIP or tar archive into the root of a trusted `hfcache` checkout.
All archive members are new files beneath `docs/agents/plans/`; the bundle does
not supply `current.md`, replace an existing contract, or change source code.
Use extraction that refuses or skips existing files; inspect any collision
rather than overwriting a local plan or execution evidence.

## Read and start

1. Read the [parent plan](../../2026-10-19-plan-tags-and-discovery.md).
2. Give the coding agent the [implementation prompt](implementation-prompt.md).
3. The implementation instruction authorizes activation. The agent must inspect
   the actual branch, working tree, active selector and newer commits, then use
   `feat/tags-and-discovery`, not `main`.
4. Execute one linked task at a time. Each completed package is one passing,
   documented commit. Resume from the actual task record and git evidence.

The reviewed baseline is `wtcross/hfcache` main commit
`45f91c3534244d8f2b360a68e79be3e58c97b239`. Planning moved from `docs/plans/`
to `docs/agents/plans/` before that baseline. Do not recreate the old selector.

## Contents

| File | Purpose |
| --- | --- |
| [Parent plan](../../2026-10-19-plan-tags-and-discovery.md) | Scope, dependencies, phases, authority, completion criteria |
| [Design](design.md) | Tags, technical variants, persistence, query semantics and transport contracts |
| [Validation matrix](validation-matrix.md) | Observable behavior and adversarial/lifecycle cases |
| [Source review](source-review.md) | Pinned source findings, relevant files and external primary references |
| [Implementation prompt](implementation-prompt.md) | Copyable activation and autonomous execution instruction |
| [Configuration fragment](repositories.example.toml) | Proposed tag-only repository authoring; not a deployable config |
| [Search examples](search-examples.json) | Proposed typed query examples, not executable requests |
| `bundle-manifest.json` | Delivery-time hashes; not an application schema or a runtime gate |

The parent plan links all sixteen task records. Tasks start `pending`; the
plan starts `draft`. No implementation tests, live Hub requests, archive reads,
NAS acceptance, deployment or production checks have been performed by this bundle.
The package has only been checked for internal consistency and safe archive layout.

## Intended product

A single operator-maintained `tags` field organizes models and datasets at sync
configuration time. Current configured tags take effect on the next discovery
request, without a sync. Format/quantization/size filters use structured,
publication-specific observations, never operator tags as proof. REST and the
API-backed CLI ship before five new explicitly allowlisted read-only MCP tools.

There are no categories, groups, curated use-case fields, tag hierarchies,
separate annotation database, remote config-install API, semantic search service,
partial repository downloads or MCP mutations in this plan.
