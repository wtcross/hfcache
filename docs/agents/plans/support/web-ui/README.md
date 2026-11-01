# Web UI implementation bundle

Created October 20, 2026 for Tyler's hfcache project. The explicit implementation
instruction activated the plan on `feat/web-ui`. This bundle is scope and design
evidence, not deployment authorization or completed feature-test evidence.

## Start here

Read [the dated plan](../../2026-10-20-plan-web-ui.md), then use the [kickoff prompt](KICKOFF.md). The plan follows the repository's current `docs/agents/plans/` convention, not the retired `docs/plans/` location. It does not replace `current.md`, `progress.md`, `AGENTS.md`, any existing contract, or a production configuration. Activation happens only when the implementation prompt is issued.

The bundle contains task records, design and API specifications, acceptance scenarios, a testing strategy, a human-documentation map, migration requirements, a pinned source review, and the approved interaction prototype. Task files own execution status. Support documents define acceptance requirements; they do not silently override living contracts. Every behavioral change requires the repository's contract/invariant/ADR loop.

## Extract at the repository root

For the supplied tar archive, use GNU tar's collision refusal:

```bash
cd /path/to/hfcache
tar --keep-old-files -xzf /path/to/hfcache-web-ui-plan-bundle.tar.gz
sha256sum --check docs/agents/plans/support/web-ui/SHA256SUMS
```

All member paths start with `docs/agents/plans/`; there is no extra enclosing directory. The ZIP contains the identical payload. Configure ZIP extraction to refuse replacement of existing files. On any collision, stop and inspect; extraction can have added earlier noncolliding files. Never force-overwrite an older plan or its execution evidence. Hash verification checks the supplied draft bytes, not whether later implementation edits are correct.

## Supporting specifications

- [Architecture and security](architecture.md), [API and authority contracts](api-contracts.md), and [interface behavior and parity](interface-and-parity.md).
- [Testing strategy](testing-strategy.md), [acceptance scenario matrix](acceptance-matrix.md), and machine-readable `acceptance-cases.json` / `task-index.json`.
- [Human documentation requirements](documentation-map.md), [migration and compatibility](migration-and-compatibility.md), and [source review](source-review.md).
- [Approved prototype](reference/hfcache-web-ui-mockup.html) and [reference screenshots](reference/README.md).

Read the support specification relevant to the selected task; do not load all history on every session. Preserve this bundle and its reference prototype as design evidence. Production documentation belongs in human-facing guides, not solely in this plan.

## Execution records

[Resolved execution contracts](execution-contract.md) freeze the accepted
boundary choices against the exact baseline. [Prerequisites](prerequisites.md)
records read-only infrastructure discovery and safe provisioning requirements.
`acceptance-evidence.json` assigns planned test identifiers to every required
layer; an empty execution list is explicitly pending. The implementing task
must create the tests and replace or confirm the planned identifiers with real
commands and artifact-bound outcomes. Planned identifiers never prove acceptance.

`SHA256SUMS`, `bundle-manifest.json` and `VALIDATION.json` retain original input
provenance. Their mutable plan/task/support file hashes naturally differ after
execution updates; do not rewrite them to manufacture a clean extraction.
Reference-asset bytes remain unchanged and are checked by the plan tests.

## WEB-023–026 execution amendment

Applied after WEB-022/9d11738 and before WEB-023: follow the [bounded-testing policy](testing-strategy.md#web-023026-bounded-product-testing-and-effort)
and task-specific GPT-6.1-sol high/medium/high/medium rationale. All95 underlying
behaviors remain under accepted product-focused criteria. This does not rewrite
original bundle hashes/reviews/kickoff or authorize production work.

## Execution boundaries

Default implementation branch: `feat/web-ui`. Commit one work package at a time. Do not merge, push, tag, deploy, reload the production Caddy instance, change production services/timers/credentials, touch NAS contents, or infer renewed authority from historical rollout records. Use owned local fixtures and isolated guests. Build-time dependency acquisition is allowed where repository/environment policy permits, without production credentials or automatic image pulls. Missing required test infrastructure is a blocker, never a pass.
