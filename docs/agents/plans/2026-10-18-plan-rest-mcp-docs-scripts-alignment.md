# Align hfcache documentation and scripts with REST and read-only MCP

| Field | Value |
| --- | --- |
| Status | active |
| Created | 2026-10-18 |
| Reviewed repository | `wtcross/hfcache` |
| Reviewed branch | `feat/rest-api-and-mcp` |
| Reviewed commit | `65b65714b29e835498138ec3122b5669571850cf` |
| Reviewed package version | `0.2.1` |
| Authorization | User instruction on 2026-10-18 to implement on feat/rest-api-and-mcp and commit each completed package; later instruction authorizes pushing the completed, validated feature branch to github and forgejo. No merge, tag, deploy or production archive operations. |
| Implementation branch | `feat/rest-api-and-mcp`; never implement on `main` |
| Existing selector at review | `docs/plans/current.md`: no active plan |
| Target selector after migration | `docs/agents/plans/current.md` |
| Task authority | The individual linked task files own status, acceptance and evidence. |

## Outcome

Make documentation and shipped scripts describe the system that exists now: an
API-backed operational CLI, a FastAPI writer service, a separately confined
verification worker, and an optional read-only FastMCP interface. A person must
be able to install the right profile, connect with the right credential, operate
safely, and understand failures without reading how an agent implemented it.

This is a corrective implementation plan, not permission to deploy, operate the
live archive, remove its safety barriers, run arbitrary probes, or resume an old
rollout. The source baseline is pinned above; newer branch changes must be reviewed
before implementation. The existing feature plan is completed; do not reopen or
renumber its tasks.

The detailed [review and evidence](../reviews/2026-10-18-rest-mcp-docs-scripts-review.md)
and [script disposition inventory](../reviews/2026-10-18-script-disposition.md)
are part of this draft. They distinguish confirmed source/documentation problems,
removal candidates requiring caller checks, and intentional features to retain.
This review is static. It did not run the application suite, inspect the production
host or validate the live NAS. Repository statements about local deployment are
recorded evidence, not fresh observations by this reviewer.

## 1. Required documentation boundary

### Human-facing surface

All documentation outside `docs/agents/` is for people: README, changelog,
quickstart, operations/recovery, API/client/MCP/server references, configuration,
schemas, architecture, invariants, technical ADRs, consumers, deployment,
container/Cockpit guides, and human developer/script instructions.

Human documents must not contain work-package IDs, task or implementation-plan
links, progress-record ownership, active-plan pointers, agent workflow instructions,
phase-by-phase implementation narration, or task-dependent claims of availability.
Remove these from titles, metadata tables, headings, prose, tables, links, reference
definitions and public help generated from code. Rewriting only the quoted MCP
introduction is insufficient.

Use current-tense product behavior, prerequisites, examples, supported profiles,
security boundaries, troubleshooting and compatibility notes. A user-visible feature
is described as supported or unsupported, not as something a named package "adds".

Technical identifiers are different: retain stable error codes, schema versions,
MCP tool names, operation states and architectural/storage invariant IDs where useful.
A domain `plan` command or retention/recovery plan is not agentic implementation
tracking. Technical ADRs can explain decisions/alternatives/consequences and cite
code/tests/commits; they must not require implementation tasks as the rationale.

### Agent-facing surface

Keep planning, work-package evidence, execution authorization, resumption, process
ADRs and historical implementation audits under `docs/agents/`. `AGENTS.md` and
its existing `CLAUDE.md` symlink are explicitly agent entrypoints, not human guides.
Agents may link to human contracts; human guides do not link back to tracking.

This requires a deliberate, one-time migration:

| Current path | Destination / treatment |
| --- | --- |
| `docs/plans/` | `docs/agents/plans/`; preserve dated filenames, task IDs and history |
| `docs/progress.md` | `docs/agents/progress.md`; extract a concise human operational-status/checklist, not a copy of the audit |
| `docs/plan.md` | `docs/agents/history/plan.md`, after all still-normative technical content has a current human home |
| Pure agent-process records in `docs/adr/` | `docs/agents/adr/`, with their identities and reasoning preserved |
| Agent-only planning invariant | Agent invariant guide, preserving identity; do not reuse its ID |
| Historical execution transcripts embedded in runbooks | Preserve as agent-only evidence; replace human instructions with current workflows |

Amend the planning stable-path rule explicitly before applying this one-time move.
Preserve each original identity, completed result and rationale. Record a migration
manifest and repair relative links. Do not leave two active selectors or a chain
of human-facing redirect pages pointing to agent history. Existing contracts that
still cite the original plan must be rehomed, not lost.

Because this bundle already uses the desired agent directory, migration must merge
existing tracked files into it **without overwriting this new plan or its tasks**.
At the end of the work there are no leftover human tracking references. Transitional
pre-existing references may be inventoried during early packages, but no blanket
exception may survive final acceptance.

## 2. Scope and protected behavior

### In scope

Correct identified script safety/profiling issues; fix CLI diagnostics/help where
behavior disagrees with the contract; remove proven-unused migration remnants;
rewrite human documentation; separate current operational facts from execution
history; improve examples; and add automated contract/documentation checks.

### Not in scope

Do not redesign the API, add MCP write tools, add a workflow engine, implement a
new scheduler, introduce arbitrary file download/upload, retire native activation,
replace NFS consumer copying, broaden credentials, or change durable formats merely
for editorial convenience. Do not migrate Cockpit's host-local report browser to a
new API client without a separate scoped design. Document its existing exception
accurately. No dependency upgrade is required to make prose match upstream examples.

Preserve single-writer/local-lock authority, mount/sentinel checks, immutable
publication/manifests, guarded maintenance/recovery, bounded receipts and metadata,
exact-key/no-automatic-replay semantics, all observer handles, the private verifier's
no-IP/no-credential boundary, and the exact nine-tool MCP allowlist.

The selected local rootless deployment remains guarded/read-only. Preserve the
independent host guard, original lock inodes, writer masks, disabled verification
calendar, both operation stores and scheduled handles. A free lock, observer exit,
unit wrapper exit or documentation cleanup does not prove executor termination.
No commands in this plan authorize NAS I/O, a root remount, token rotation, service
start/stop, deployment selection, tag creation, push, registry publication or changes
to another host.

## 3. Priority findings and chosen corrections

| Finding | Priority | Correction |
| --- | --- | --- |
| F01 | Required | Remove agentic implementation narrative from every human guide, including the entire MCP guide, and migrate records under agents. |
| F02 | High | Replace accumulated provisional/current-state claims with concise product status and a dated human acceptance page. |
| F03 | High | Separate native and rootless profiles; guard script misuse and stop leading with unsupported-on-this-profile native paths. |
| F04 | High | Correct obsolete base-image and listener/readiness descriptions against current templates and helpers. |
| F05 | High | Stop implicit/import-time/live-default hardening workloads; validate before any allowed write and remove dangerous host-setting probes. |
| F06 | High | Make denial evidence distinguish real policy enforcement from import/network/prerequisite failure. |
| F07 | Medium | Correct CLI help and command side-effect claims; distinguish HTTP/control state from archive mutation. |
| F08 | Medium | Remove proven-unused CLI migration helpers after branch-wide caller and coverage checks. |
| F09 | Medium | Preserve quiet errors/warnings, implement actual no-color behavior and align verbosity/non-TTY progress semantics. |
| F10 | High | Separate API/MCP/Hub credential sources and profile-specific delivery, rather than universal native setup recipes. |
| F11 | Medium | Remove the false promise of an unbounded local operational CLI; document complete-or-explicit-failure collection. |
| F12 | Medium | Explain Cockpit's actual host-only/blocked controls and direct-report-read exception; retain independent consumers. |
| F13 | Medium | Maintain a complete supported-script inventory, not the obsolete README list; do not delete supported tools as "dead". |
| F14 | High | Add executable audience/link/interface checks and preserve normative coverage during historical-document migration. |

High here means first-order safety, operational ambiguity or a prerequisite to
trustworthy guidance; it is not a claim of an exploited production vulnerability.
F08 contains deletion candidates, not a claim that every external caller has been
ruled out. The review describes the limits of each finding.

## 4. Canonical human documentation structure

Prefer rewriting existing guides over adding a competing guide for each task.
Create only missing audience/navigation/acceptance surfaces.

| Guide | Required ownership |
| --- | --- |
| `README.md`, `docs/README.md` | Product overview and reader/writer/MCP/operator/developer routes; no execution tracking |
| `docs/quickstart.md` | API reader setup with a provisioned endpoint and separate protected credential |
| `docs/api.md` | Current REST route, capability, request/response, job and failure reference |
| `docs/api-client.md`, `docs/cli.md` | Client settings/precedence, local exceptions, commands, output, complete collection and reconnect |
| `docs/mcp.md` | Enable/connect/use nine read tools; endpoint, auth, bounds, rotation and incompatibilities |
| `docs/server.md` | Server settings, policy snapshots, lifecycle, receipts, metadata bounds and private-worker boundary |
| `docs/configuration.md` | Archive policy, clearly distinguished from server/client/rendered deployment settings |
| `docs/operations.md`, `docs/recovery.md` | Current operational and incident workflows; no historical direct-writer aliases |
| `docs/containers.md` | Selected rootless role/build/lifecycle/profile contract, current UBI and worker-created listener |
| `docs/deployment-centos-stream-10.md` | Explicit profile selection, safe provision/upgrade/rollback and acceptance prerequisites |
| `docs/deployment-status.md` | Dated recorded deployment scope and remaining validation/restrictions in human terms |
| `docs/scripts.md` | Complete script purpose/profile/inputs/outputs/side-effects/safe-usage inventory |
| `docs/development.md` | Human contribution/build/test instructions and documentation checks, without agent execution process |
| `docs/architecture.md`, `docs/invariants.md`, `docs/security.md`, `docs/schemas.md` | Current technical guarantees, threat controls, identities and compatibility |
| `docs/adr/` | Human architectural rationale, not task provenance or agent process |
| `docs/cockpit.md`, `docs/cockpit-plugin/`, `cockpit/README.md` | Actual launcher, candidate flow, host-local boundaries and profile limitations |
| `docs/consumers.md`, consumer examples/helpers | NFS data path, exact publication identity, local verification and promotion |
| `CHANGELOG.md` | Versioned user-facing changes and rollback notes, not work-package completion evidence |

Use descriptive section anchors. Updating an anchor requires repairing internal
links and any documentation-parsing tests in the same package. Prefer executable
contract assertions over tests that enshrine a historical implementation paragraph.

## 5. Profile and side-effect rules to make explicit

The native package profile, selected rootless profile, reader installation and
consumer data path must not share one ambiguous command block. Native binaries
under the host release `.venv`, container binaries under `/opt/hfcache/.venv`, and
the host fixed container client wrapper are different entrypoints. Native services
and rootless user services use different managers, even where their names match.

The selected rootless API template uses Unix-only REST behind Caddy TLS, protected
file-mounted Podman secrets and a worker-created private listener. Native UDS/TCP
activation and systemd credential delivery remain separate supported behavior.
The dormant rootless socket artifact must not be presented as the active listener
or removed without changing and testing its release-binding contract.

Document four distinct effects where applicable: HTTP requests by the client,
local API/worker control-state writes, archived content/metadata changes, and Hub
network access. A plan/preview can avoid archive mutation yet be a keyed job;
actual verification writes reports/catalog; a read-only doctor is not necessarily
offline; MCP estimates/read tools do not run verification. Metadata read-only
claims exclude ordinary process/logging activity and do not promise that mounting
or accessing a filesystem has no operating-system-level effects.

Keep REST bearer, MCP-reader bearer and Hub credential terminology separate.
Protected-file examples pass paths, never literal token values. Native named
credentials and container secret-file mounts must use their actual source rules.
All users of the MCP/publication boundary must be entitled to all exposed restricted
metadata/content; do not invent per-repository ACLs.

## 6. Example human-centered MCP introduction

The following is newly drafted replacement prose, to be checked with the rest of
the rewritten guide and the pinned implementation:

> hfcache provides an optional, read-only MCP interface for exploring archive
> metadata. It exposes nine tools for inspecting archive status, repositories,
> retained revisions, references, manifests and existing run or verification
> reports, and for estimating verification work. The interface cannot start jobs,
> download repositories, repair or delete data, or perform integrity verification.
>
> Connect to the writer's `/mcp/` endpoint using a separately provisioned
> MCP-reader bearer token. This credential grants access to metadata across the
> entire archive, including restricted repositories. REST and Hugging Face
> credentials are not interchangeable with the MCP credential.
>
> Requests use Streamable HTTP with finite JSON responses. Each request is
> authenticated; sessions do not grant additional access. The service does not
> provide OAuth login or token issuance. Off-host clients must use verified HTTPS.

Continue with **Connect**, **Available tools**, **Result identity and pagination**,
**Authentication and rotation**, **Limits and troubleshooting**, and **Deployment
profiles**. Do not replace a task-centric introduction with another history lesson.

## 7. Ordered tasks and commits

Execute sequentially; this plan does not authorize concurrent implementation.
Dependencies are authoritative in each task file. Each task is one work package
and one implementation commit, containing related code, tests and documentation.
Do not hold completed work for a single final commit.

| Order | Phase | Work package | Depends on |
| --- | --- | --- | --- |
| 1 | 0 | [DOC-011 — Separate human documentation from implementation records](tasks/doc-011-human-docs-authority-and-record-migration.md) | None |
| 2 | 1 | [OPS-020 — Make hardening probes explicit, safe and evidence-based](tasks/ops-020-safe-explicit-hardening-probes.md) | DOC-011 |
| 3 | 1 | [OPS-021 — Align installer and diagnostic entrypoints with deployment profiles](tasks/ops-021-profile-aware-install-and-diagnostic-scripts.md) | OPS-020 |
| 4 | 1 | [API-018 — Align CLI help and output; remove obsolete rendering paths](tasks/api-018-cli-help-output-and-migration-remnants.md) | OPS-021 |
| 5 | 2 | [DOC-012 — Rewrite REST and client documentation as current references](tasks/doc-012-human-rest-and-client-reference.md) | API-018 |
| 6 | 2 | [DOC-013 — Rewrite the MCP guide for users and administrators](tasks/doc-013-human-mcp-guide-and-tool-contract.md) | DOC-012 |
| 7 | 2 | [DOC-014 — Replace historical command transcripts with current runbooks](tasks/doc-014-current-operations-and-recovery-runbooks.md) | DOC-013 |
| 8 | 2 | [DOC-015 — Unify deployment, runtime and Cockpit guidance](tasks/doc-015-deployment-runtime-and-cockpit-guide-alignment.md) | DOC-014 |
| 9 | 2 | [DOC-016 — Consolidate living technical contracts and architectural rationale](tasks/doc-016-human-architecture-config-schemas-and-adrs.md) | DOC-015 |
| 10 | 2 | [DOC-017 — Make onboarding, examples and navigation reader-first](tasks/doc-017-reader-first-onboarding-and-human-navigation.md) | DOC-016 |
| 11 | 3 | [DOC-018 — Add executable documentation and script-alignment checks](tasks/doc-018-automated-docs-and-interface-alignment-gate.md) | DOC-017 |
| 12 | 3 | [DOC-019 — Audit final alignment and close the correction plan](tasks/doc-019-alignment-acceptance-and-final-disposition.md) | DOC-018 |

Phase 0 establishes authority and safe relocation. Phase 1 resolves the highest
impact script/CLI problems before documenting them as correct. Phase 2 rewrites
current guides without changing the transport/storage design. Phase 3 adds
regression protection and closes the plan only after integrated validation.

## 8. Autonomous execution protocol

1. Read git status and recent history, the actual current selector, relevant
   agent workflow/environment guidance and this plan. Recheck the feature branch
   head and review any delta from `65b6571`. Preserve user changes. Do not
   silently reset, stash, rebase, switch away from unrelated work or start on main.
   Reuse `feat/rest-api-and-mcp`; create only its normal local tracking branch if
   needed and safe. Do not create a second implementation branch by accident.
2. A later user instruction to implement authorizes activation; downloading this
   draft does not. If another plan is active, reconcile its scope/selection and
   record any pause before changing it. Never silently abandon it. Check all new
   work-package IDs for collisions; adjust only unstarted new records if necessary.
3. Mark the first task in progress before editing implementation. The initial
   selector/path migration is governed by DOC-011's explicit authority amendment.
   After that package, resume only through `docs/agents/plans/current.md`.
4. For each ready task, read only its affected contracts/invariants/ADRs and
   relevant tests. Correct contract and code disagreements explicitly in the
   same package. Preserve technical requirements when deleting historical prose.
5. Implement, update human docs for that body of work, then run its focused checks
   and `scripts/check.sh`. Use all required server/MCP extras. Required Cockpit
   checks must actually run for changes to that area; a skipped stage is not
   passing evidence. Do not use live Hub/NFS/installed-host tests under this plan.
6. Record actual evidence, invariant/ADR review and any remaining restriction in
   the task and agent progress log, not human docs. Update the next-task pointer
   and commit using the task's `<ID>: <summary>`. An uncommitted result refers to
   "this commit"; never invent a commit hash. Do not squash away package boundaries.
7. If blocked, preserve the work and write the exact blocker and unblock condition.
   Never remove a safeguard, mark an unrun check passed, or broaden scope to make
   progress. Necessary scoped implementation details do not need repeated approval.
   New runtime features or host operations require separate authorization.
8. At final acceptance, reconcile all finding dispositions, migrated records and
   human contracts, complete the task/plan, and clear the agent selector. Leave
   completed records in place. Do not push, merge, tag, deploy or activate backlog.

## 9. Validation and completion criteria

The final repository must satisfy all of the following:

- Human docs and public help contain **zero** task IDs, agent implementation
  plans/progress links or execution-phase narrative. The checker permits actual
  product concepts, architectural invariants and runtime error codes.
- Every human link/anchor resolves. Normative requirements formerly only in the
  historical plan have current homes. Preserved records are accounted for by
  migration hashes/paths and agent indexes.
- Documented REST routes, CLI modes, capability and side-effect distinctions,
  configuration defaults and the exact nine MCP tools match executable fixtures.
- Example commands parse against the actual CLI; selected safe workflows execute
  against owned fixtures. Invasive snippets are never blindly executed by tests.
- Script inventory is complete. Each removal has usage/installation/rollback
  evidence; intentional native/consumer/dormant artifacts are retained. No blanket
  deletion of old-looking tools, reports or historical records occurs.
- Hardening checks cannot run on import/help, cannot write before identity proof,
  cannot alter real host settings as a denial test, and cannot call unrelated
  exceptions successful enforcement.
- CLI quiet/error/warning/color/progress behavior matches its human contract;
  JSON and no-replay/retained-handle semantics are unchanged.
- `scripts/check.sh --with-build`, documentation checks and required Cockpit checks
  pass, with exact results recorded. No assertion is made that offline fixtures
  prove live NAS, cgroup, SELinux or installed-image acceptance.
- Current guards, locks, credential isolation, receipt stores, immutable archive
  guarantees and restricted-deployment state remain untouched.

A feature or file is not dead simply because a particular host has it disabled.
Conversely, test-only references to obsolete implementation seams do not require
retaining dead code forever: replace the coverage with meaningful public-contract
checks and record the decision.

## 10. Lifecycle and amendments

- 2026-10-18: Activated by the user's implementation instruction. Git HEAD is
  the reviewed 65b6571 on feat/rest-api-and-mcp; no tracked delta and no active
  predecessor. The supplied untracked plan/review bundle is preserved. DOC-011
  records the explicit stable-path exception before any relocation. Read-only
  delegated audits support this task; implementation remains sequential.
- 2026-10-18: Draft created after a pinned feature-branch review. Incorporated
  the user's requirement that documentation outside `docs/agents/` be human-centered
  and free of agentic implementation references. No activation or repository/host
  mutation performed by this review.
- Activation, subsequent amendments and final outcome must be recorded here by
  the implementing agent with actual dates/evidence. Do not copy mutable task
  statuses into this plan table.

- 2026-10-18: Later user steering authorizes pushing the completed, validated
  feat/rest-api-and-mcp branch to github and forgejo after final acceptance.
  This supersedes this plan/task bundle's earlier no-push statements only.
  Per-package local commits and all merge/tag/deploy/production restrictions
  remain. Never force-push; remote divergence must be reconciled safely.

- 2026-10-18: Authority migration established the sole selector under
  docs/agents/plans/current.md with 47 collision-checked records and original
  hashes. The coverage map rehomes normative requirements; transitional human
  tracking references are individually inventoried for the ordered rewrites.
