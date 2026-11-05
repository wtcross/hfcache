# hfcache documentation remediation plan

**Repository:** <https://github.com/wtcross/hfcache>  
**Review baseline:** [`7410aaaad0179a3546d7e74fcecf2c2ea98dec97`](https://github.com/wtcross/hfcache/commit/7410aaaad0179a3546d7e74fcecf2c2ea98dec97), reviewed November 5, 2026.  
**Execution model:** `gpt-6.1-sol` for the coordinator and every subagent, with effort assigned by responsibility.  
**Deliverable:** An implementation plan. This review has not changed repository files or activated implementation.

## 1. Outcome and scope

Make hfcache understandable from the root README, with accurate task guides for its users and precise references for its integrators and maintainers. Every retained document must have an identifiable audience, a useful purpose, and a verified relationship to the implementation.

The review inventoried 556 tracked Markdown paths: 217 human-document candidates, 337 files under `docs/agents/`, and the two root agent entrypoints. The human set includes 177 ADR/index files, 24 general guide/reference files, 13 browser guides, and three other Markdown files. Detailed review covered the main reader, operator, browser, interface, and governance documents, their relevant implementation, and documentation-dependent tests. The ADR collection received inventory and targeted review; execution must still assess every file individually.

Apply these scope rules:

- Remove the root README's entire **Status** section. Do not recreate it under another heading or replace it with a deployment-history link.
- Treat `docs/agents/` as an exception to the human audience requirement only. It is **not** an exception to the request to remove plan progression and agent state from maintained repository documentation.
- Keep reusable agent instructions under `docs/agents/`. Retire checked-in current-task selectors, execution logs, completed-task ledgers, and obsolete plan snapshots after extracting any durable requirements. Keep this implementation's mutable coordination records in the execution system outside the versioned documentation tree.
- Preserve product concepts such as `hfcache plan`, operation progress, `pending` states, transaction checkpoints, and ADR decision status. They describe the software or its design, not agent execution state.
- Preserve licensing, attribution, security boundaries, compatibility requirements, and useful architectural rationale. Age or length alone does not make a document obsolete.
- Limit implementation to documentation, examples, navigation, and the documentation validation machinery needed for this cleanup. Report application defects separately; do not change product behavior to make a documentation rewrite easier.

The current [agent router][s-agents] and [planning policy][s-planning] require plan/task/progress files and preservation of completed records. The [technical-record policy][s-record-policy] also prescribes tracking references that conflict with its human-document boundary. This plan deliberately changes those documentation policies before retiring their artifacts. The existing rules must not be silently bypassed or allowed to recreate the removed material.

## 2. Findings that determine the work

These are source-backed findings at the review baseline, not a generic documentation checklist.

| Finding | Evidence | Required response |
| --- | --- | --- |
| README contains a deployment and execution ledger. | [Root README][s-readme] describes an installed 0.3.3 profile, pending pilots, prior acceptance, active-plan prerequisites, and publication instructions. | Delete the complete Status section; keep product capabilities and stable boundaries. |
| Several documents describe different local deployments as current. | [Browser overview][s-web-overview] names 0.3.1; [deployment guide][s-deploy] opens with 0.3.0; [deployment record][s-status] names 0.3.4-manual-writer. | Remove local installed-state assertions from reusable guides. Do not globally substitute the package version for deployment evidence. |
| The release procedure would recreate the unwanted section. | [Agent release instructions][s-release] explicitly require refreshing README Status. | Correct release policy in the first editing batch. |
| A documented missing command is implemented. | [Operations][s-operations] says there is no `runs` CLI command; [CLI source][s-cli-source] registers `runs list` and `runs show`. | Correct the guide and add a report-reading example with operation IDs distinguished from domain run IDs. |
| Feature descriptions retain obsolete future-work wording. | [CLI reference][s-cli] calls card reads subsequent work; [API source][s-api-source] implements them. [Server reference][s-server] disclaims original-intent implementation; [intent routes][s-intents] implement it. | Describe supported behavior, prerequisites, and limitations in the present tense. |
| Interface summaries are incomplete. | [CLI command overview][s-cli] omits search/tags/catalog; [server configuration table][s-server] omits `web` and `host_helper`, which exist in [ServerConfig][s-server-config]. | Complete the summaries and connect them to the existing detailed sections. |
| Reader examples lose continuity. | [Quickstart][s-quickstart] creates `quickstart-client.toml` and an `H()` wrapper, then switches to bare `hfcache` and `/etc/hfcache/client.toml`. | Use one installation, endpoint, credential source, configuration file, and command convention through the tutorial. |
| Consumer examples do not form one complete workflow. | [Consumer guide][s-consumers] uses different setup, copy, and serving paths. [Copy helper][s-copy] selects current publications and removes an existing destination after verification. | Supply a consistent verified-copy-to-serving example; state current-only helper selection and require a new destination. Do not invent a retained-revision flag. |
| Human entrypoints expose test history before useful instructions. | [Browser troubleshooting][s-web-troubleshooting] begins with Playwright/WebKit acceptance failures. [Development][s-development] begins with a specialized browser authentication fixture. | Put user symptoms first in troubleshooting and ordinary setup first in development. Relocate reusable fixture instructions into developer reference material. |
| Existing documentation checks encode obsolete process requirements. | [Alignment tests][s-doc-tests] require more than 150 human documents; [migration tests][s-migration-tests] require old selectors/snapshots; [web-plan tests][s-web-plan-tests] validate task and execution ledgers. | Replace process-history assertions with meaningful documentation or product-conformance checks; retire assertions that only preserve obsolete state. |
| Some documentation is executable test input. | [REST example tests][s-example-tests] require exactly one Python block; [configuration tests][s-config-tests] parse tables; transaction, verification, REST, and MCP tests parse other reference structures. | Identify consumers before restructuring. Preserve semantic coverage while updating brittle extraction rules. |
| A real implementation limitation is already disclosed correctly. | [Architecture AD-05][s-architecture] and [publication allocator][s-publication] distinguish the desired lifetime-generation rule from retained-reference allocation. | Preserve the limitation. Do not present the stronger contract as implemented or quietly weaken it. |

The main navigation problem is excessive depth and mixed purpose, not an established repository-wide broken-link problem. A targeted link/anchor review of the reader and browser routes found no missing local targets; the execution plan still requires a full check after changes.

## 3. Documentation design

### Personas and primary routes

Assign one primary persona and one primary task to every file. A secondary audience may be supported through links; it should not take over the opening sections.

| Persona | Question to answer | Primary documentation |
| --- | --- | --- |
| Evaluator | What does hfcache do, and which path should I follow? | Root `README.md` |
| API reader / catalog user | How do I connect, search, and inspect an archive? | `docs/quickstart.md`, task-oriented portions of `docs/discovery.md` |
| Model or dataset consumer | How do I obtain and independently verify usable files? | `docs/consumers.md` |
| Browser administrator | How do I sign in and complete a task in the interface? | `docs/web-ui/README.md` and focused browser task guides |
| Writer operator | How do I inspect jobs, run approved work, and recover safely? | `docs/operations.md`, `docs/recovery.md` |
| Installer / platform administrator | How do I provision a supported profile and upgrade it? | Deployment, container, storage, and browser deployment guides |
| API / SDK / MCP integrator | What inputs, outputs, authorization, limits, and failures must I handle? | `api.md`, `api-client.md`, `mcp.md`, relevant CLI/configuration references |
| Contributor / security reviewer | How is the system structured, why, and how is it verified? | `development.md`, architecture, invariants, schemas, security, host-administration, ADRs |
| Coding agent | What stable instructions and relevant contracts govern this task? | A short root router and reusable `docs/agents/` instructions |

The browser interface currently uses an administrator identity. Do not imply a browser reader role merely because a page displays read-only metadata. Distinguish authentication identity, effective permissions, and whether an individual action mutates state.

### Progressive disclosure

Use four levels: **README orientation → persona task guide → detailed reference → design rationale**. Readers should not need an ADR, implementation plan, or installation transcript to complete a routine task.

The root README should contain:

1. A short description and the main use cases.
2. A compact explanation of archived publications, metadata access, and file copying.
3. A task chooser linking to the first useful guide for each major persona.
4. Essential boundaries: complete immutable revisions, independent verification, metadata versus payload transport, authorization, and supported deployment requirements.
5. Contributor, documentation-index, and license links.

Aim for roughly 400–700 words as an editorial guide, not a test-enforced quota. Route the browser user to one browser starting page, not simultaneously to provisioning, migration, rollback, and acceptance records. Move build details and complete directory catalogs to contributor/reference pages when they obstruct orientation.

`docs/README.md` should be a concise audience/task index. Each main task should be reachable directly from the root README or through that index. Deeper links should answer the reader's next question. Keep existing useful paths and anchors where practical; create a new page only when it has a distinct task or reference purpose.

### Writing rules

- Start task guides with the outcome, prerequisites, steps, expected result, and a relevant next step.
- Start references with scope, audience, and a short navigation aid. Define unfamiliar terms once and link to the canonical explanation.
- Use present-tense behavior descriptions. Replace ambiguous “unreleased,” “next,” or “pending implementation” claims with verified capabilities and concrete version/profile prerequisites where necessary.
- Keep a single authoritative explanation of each complex rule. Other pages get a concise contextual summary and a link.
- Prefer short paragraphs, descriptive headings, numbered procedures, and tables for exact mappings. Avoid acceptance-report prose, repeated warnings, unexplained abbreviations, and dense parenthetical chains.
- Keep warnings next to the action they govern. Concision must not erase destructive effects, credential requirements, uncertainty semantics, or recovery limits.
- Keep technical references human-readable even when they are detailed. Do not move schemas or architectural contracts into `docs/agents/` merely because they are difficult to edit.
- Keep release notes about user-visible changes, compatibility, and migration. Remove local selected-host status, agent work summaries, pending rollout tasks, and push/tag instructions.

## 4. Team and coordination

Every role uses **`gpt-6.1-sol`**. Effort is explicit in each assignment.

| Role | Effort | Responsibility |
| --- | --- | --- |
| Coordinator / integrator | `high` | Own the document map, dependency order, file assignments, cross-document consistency, integration, and final acceptance. |
| Behavior auditor | `high` | Trace claims and examples to code, configuration models, tests, and supported runtime profiles. Classify disagreements before editing. |
| Documentation architect / policy editor | `high` | Establish personas and navigation; revise policies that regenerate state or duplicated documentation. |
| Task-guide editor | `medium` | Rewrite bounded reader/browser/contributor guides after their behavioral facts are established. |
| Technical-reference editor | `high` | Edit API, configuration, recovery, security, schema, and architecture contracts without changing their meaning. |
| Example and contract validator | `high` | Check command continuity, inputs/outputs, side effects, meaningful test coverage, and parsed-document dependencies. |
| Mechanical cleanup editor | `low` | Perform already-approved link, anchor, index, and asset-reference repairs. Make no independent deletion or behavior decisions. |
| Independent reviewer | `high` | Review a batch from a fresh context for technical accuracy, persona fit, completeness, and readability. |

Use `xhigh` only for a specific unresolved cross-contract or compatibility judgment, such as the disposition of durable requirements embedded in a plan. Do not use it for ordinary prose or link edits. Do not silently switch model families.

Keep at most **one coordinator and three active subagents**. Roles are reused across batches rather than all running simultaneously. Parallelize discovery and disjoint file groups. Keep policy changes, shared-index edits, integration, and dependent cleanup sequential.

For each writing batch:

1. The coordinator supplies a current base commit, persona, bounded objective, exact owned files, required sources, and acceptance checks.
2. A behavior auditor establishes the relevant claims and discrepancies. The editor reads both the document and its implementation evidence.
3. The editor changes only its assigned files, normally one to three substantial documents or up to five small related documents. Treat a large contract as its own batch.
4. A different agent reviews the patch. The writer resolves concrete findings before integration.
5. The coordinator integrates, repairs shared navigation, runs the applicable checks and required repository gate, and advances dependent work.

Use isolated worktrees when writers run concurrently. With a shared checkout, grant one writer exclusive ownership at a time. Never allow two subagents to rewrite the same reference or update the same test parser concurrently. The coordinator owns root README, documentation indexes, shared policy, and checker changes unless explicitly delegated for one batch.

Store the working inventory, claim matrix, deletion decisions, review results, and resumable handoff in the external execution record. These are coordination artifacts, not new permanent repository manuals. Resume against Git and the actual working tree; never overwrite an uncommitted change based on stale handoff text.

## 5. Execution sequence

The phases below define dependency order. Each phase can contain several small, separately reviewed batches. A phase number is not a new identifier to scatter through the documentation.

### Phase 1 — Refresh the baseline and build the complete map

**Owners:** Behavior auditor (`high`) and documentation architect (`high`), coordinated by the integrator.

Confirm the execution checkout and compare it with the reviewed commit. Re-audit changed files before relying on this plan's findings. Inventory every tracked documentation surface, including ADRs, agent instructions, fixture READMEs, generated references, Markdown links, screenshot assets, example configuration, script help, and relevant package metadata. Classify license/attribution and generated artifacts separately so they are not treated as disposable prose.

For every document record: path, primary persona, reader task, entry links, behavioral authorities, duplication, missing examples, proposed disposition, and tests or generators that consume it. Each file must receive an explicit keep/rewrite/merge/delete decision; scanning for keywords alone is not review.

Build a claim matrix for CLI commands, REST routes, MCP tools, configuration defaults, browser actions, deployment profiles, consumer copying, and durable-format guarantees. Trace actual behavior to source and tests. Classify each disagreement as documentation drift, a missing explanation, a real implementation defect, a compatibility constraint, or unresolved evidence.

**Exit:** Complete inventory, prioritized findings, proposed navigation, and known test dependencies. No unsupported claim is treated as a settled editing fact.

### Phase 2 — Stop the policies and tests from recreating the problem

**Owners:** Policy editor (`high`), validator (`high`), independent reviewer (`high`).

Review and update `AGENTS.md`, its `CLAUDE.md` symlink, and `docs/agents/{workflow,planning,conventions,human-docs-policy,technical-record-policy,invariants,release}.md`.

Keep the root router short and human-readable; put detailed agent instructions under `docs/agents/`. Remove the requirements to refresh README Status, select work through checked-in `current.md`, append progress logs, or add plan/work-package references to human ADRs. Replace them with stateless contribution, validation, and release instructions. Explicitly retire the agent planning rule `INV-011`; reserve its identifier rather than reusing it. Preserve relevant technical invariant and ADR identifiers.

Separate durable ADR requirements from execution evidence. A technical ADR should retain its decision identity, context, rationale, alternatives, consequences, compatibility, and source/test or actual commit references. It should not need a mutable task record to establish authority.

Migrate the process-bound tests in `test_docs_migration.py` and `test_web_plan.py` as their retained obligations change. Replace the document-count floor in `test_docs_alignment.py` with meaningful required-entrypoint and discovered-document coverage checks. Preserve link validation, source/test parity, security assertions, and reusable product acceptance checks. Do not delete a whole test module until each assertion has been classified.

Intermediate commits may retain legacy ledgers while their durable content is extracted. Do not add new execution state to them. Introduce final absence assertions with the corresponding removal batch, including the README Status assertion in Phase 3; enable the complete no-state boundary after Phase 8. This keeps incremental gates usable without creating a permanent exemption or skipping extraction.

**Exit:** Updated policies support the requested end state, tests distinguish durable contracts from execution bookkeeping, and no release/contribution instruction requires the removed Status section or checked-in agent-state ledgers.

### Phase 3 — Repair README and first-use journeys

**Owners:** Task-guide editor (`medium`), behavior auditor and reviewer (`high`).

First edit root `README.md` and `docs/README.md`. Delete Status, remove deployment-history routes, simplify the task chooser, and retain only essential product boundaries. Then edit `docs/quickstart.md` and `docs/web-ui/README.md` in a second batch.

Make the reader path install → configure → connect → inspect → search. Reuse the same `H()` wrapper and `quickstart-client.toml`. Include one short, representative output with an explanation of the fields that matter. Move writer provisioning and the fixed privileged/rootless client behind links. Move `doctor --read-only` out of the initial metadata-read sequence: it admits a diagnostic job and may contact Hub despite its name.

Start browser documentation with the provisioned URL, administrator sign-in, and task choices. Explain permission-dependent availability in product terms. Remove local deployment claims, superseded-interface narration, and fixture acceptance links.

**Exit:** A new reader can choose a route and reach the first useful action without reading deployment history, implementation plans, or deep contracts.

### Phase 4 — Complete discovery, copying, and browser tasks

**Owners:** Separate task-guide editors (`medium`) for disjoint groups, validator and reviewer (`high`).

Work in these bounded groups:

- **Discovery and consumption:** `docs/discovery.md`, `docs/consumers.md`, relevant examples. Lead discovery with search/filter/detail workflows; move schema/parser budgets behind reference links. Provide one consistent copy → verify → optional promotion/serving workflow. Use a new destination, coherent paths, and an explained serving configuration. Explicitly distinguish current-only helper copying from exact retained-publication browsing.
- **Browser reading:** `web-ui/library.md`, `repository-details.md`, `readme-cards.md`, `browser-and-keyboard.md`. Explain scope, filtering, retained selection, incomplete metadata, card availability, and navigation before wire formats or rendering policy. Check action labels against current components.
- **Browser actions:** `web-ui/configuration-and-tags.md`, `operations.md`, `maintenance.md`, `administration.md`. Describe the actual user steps, confirmation, expected result, and recovery path. Keep configuration edits, archive jobs, and protected host actions distinct where their permissions and effects differ.
- **Browser troubleshooting:** `web-ui/troubleshooting.md`. Organize around symptoms and safe next steps. Remove historical harness failures; retain reusable developer diagnostics only in the developer's reference location.

Remove before/after acceptance commentary and obsolete screenshots. Keep an illustration only when it accurately explains the current interface; give it a task-focused caption. Do not manufacture a screenshot or success result to fill a gap.

**Exit:** Each task has consistent prerequisites, meaningful steps, observable results, and an appropriate failure path. No example promises a capability the helper or interface lacks.

### Phase 5 — Reconcile interfaces and configuration

**Owners:** Technical-reference editor, behavior auditor, and validator (`high`).

Use separate batches for CLI, REST/SDK, MCP, and configuration/server references:

| Group | Owned documents | Required checks |
| --- | --- | --- |
| CLI | `docs/cli.md` | Inventory all commands/options and effects; add search/tags/catalog to the overview; remove obsolete card-read future wording; verify run-report commands. |
| REST / SDK | `docs/api.md`, `docs/api-client.md` | Registered routes, authorization, pagination, defaults, error envelopes, idempotency, observation versus effects, current readiness/recovery endpoints. |
| MCP | `docs/mcp.md` | Exact mounted tool set and schemas, separate credentials, bounded metadata behavior, useful request/response examples, no mutation or artifact-download claims. |
| Configuration / server | `docs/configuration.md`, `docs/server.md`, corresponding example TOML | Required/optional fields, defaults, constraints, precedence, `web`, `host_helper`, profile differences, restart behavior, protected credential sources. |

For every claim, distinguish supported behavior from a specific host's demonstrated acceptance. Verify uncertain observations with focused hermetic tests when necessary; do not weaken a normative security contract merely because static source inspection suggests a gap.

Coordinate test extractor updates before adding code blocks or moving tables. The REST example test's exactly-one-Python-block rule must not prevent useful examples; identify executable example blocks explicitly and test their behavior. Preserve route/mode coverage, capability requirements, execution effects, independent authentication evidence, tool/field coverage, and failure semantics rather than freezing arbitrary surrounding prose.

**Exit:** Public surface inventories match the implementation, examples preserve actual semantics, and no cross-interface contradiction remains unexplained.

### Phase 6 — Rewrite operator and deployment guidance as reusable procedures

**Owners:** Technical-reference editor and behavior auditor (`high`), independent reviewer (`high`).

Review `operations.md`, `recovery.md`, `deployment-centos-stream-10.md`, `containers.md`, `storage-requirements.md`, `web-ui/deployment.md`, and `web-ui/migration-and-rollback.md` in small related batches.

Correct the false statement that `runs` commands do not exist. Put routine inspection before advanced recovery. Convert deployment transcripts into profile-specific prerequisites, procedures, checks, and rollback constraints. Replace selected-host names, local operation IDs, receipt hashes, boot IDs, completed probes, and obsolete selected-version claims with reusable instructions or remove them.

Preserve the technical requirements behind the history: original handles, uncertain outcomes, complete drain, compatible readers, immutable publications, server-enforced read-only consumer exports, protected credential delivery, SELinux enforcement, and profile-specific permissions. Document manual versus unattended startup support accurately; a source build or local acceptance record does not prove every deployment profile works.

Make native and rootless manager/socket paths explicit in the relevant procedure. Do not merge their commands into an ambiguous “run this” block. Keep deployment-specific authorization in the operator's execution context rather than embedding an old authorization as standing documentation.

**Exit:** An operator can determine which procedure applies, what it changes, what proves success, and when to stop, without consulting a historical agent handoff.

### Phase 7 — Consolidate technical contracts, ADRs, and contributor guidance

**Owners:** Technical-reference editor (`high`), separate reviewer (`high`); use `xhigh` only for a concrete unresolved contract conflict.

Handle `architecture.md`, `invariants.md`, `schemas.md`, `security.md`, `host-administration.md`, and `job-recovery.md` one substantial document at a time. Turn appended amendment transcripts into a coherent description of the current system. Keep rationale and evolution in ADRs; keep the invariant register focused on constraints and authority links.

Fix duplicate schema section numbering and repair inbound anchors. Preserve format versions, technical IDs, transaction checkpoint semantics, and existing parser coverage. For job recovery, explain the behavior and boundary rather than describing it simultaneously as implemented and “next” work.

Resolve the credential-ACL contradiction explicitly: architecture describes installed acceptance as pending, while [security documentation][s-security] records owned native/rootless application acceptance for the narrow policy. Establish the actual control and supported prerequisites from source and scoped evidence, then remove the mutable acceptance narrative. Review decisions 130 and 161 for superseded preservation rules and decisions 142, 152, and 164 for stale implementation-stage summaries; do not renumber them.

Review every ADR in topical batches. Retain useful accepted/superseded design rationale, alternatives, compatibility history, and real commit provenance. Remove execution-stage summaries and unexplained “this commit” references. Merge or delete an ADR only after demonstrating it has no remaining unique technical purpose; do not renumber surviving records.

In a separate contributor batch, put environment setup and the ordinary quality gate first in `development.md`. Move detailed fixture/provisioning instructions later or into a focused human developer reference. Keep `scripts.md` a complete catalog of helper purpose, inputs, effects, inspection mode, and verification. Review the fixture README, relevant package descriptions, and changelog for the same audience rules.

**Exit:** Current requirements have one clear owner, historical rationale is understandable, contributor setup is easy to find, and known conformance gaps remain accurately disclosed.

### Phase 8 — Remove obsolete documentation and assets

**Owners:** Documentation architect (`high`) decides dispositions; cleanup editor (`low`) applies approved mechanical changes; reviewer (`high`) verifies preservation.

Strong candidates include `docs/deployment-status.md`, `docs/web-ui/test-release-acceptance.md`, and their now-unneeded evidence-only assets. Under `docs/agents/`, review `plans/current.md`, dated plans, task files, plan/task routers, `progress.md`, pre-rewrite snapshots, migration manifests, `historical-contract-map.md`, and historical removal ledgers.

Inspect support directories file by file. Some contain reusable fixture inputs, technical acceptance requirements, or assets that must move to current tests/reference locations. Reusable environment and release instructions remain, stripped of historical state. Agent process ADRs also need individual review.

A deletion is ready only when:

1. Its remaining useful requirements, limitations, examples, and compatibility rules have a named current home.
2. All live links, tests, scripts, generators, and package references have been updated.
3. Its remaining content is redundant, obsolete, or execution history.
4. The external review record identifies the deleted path, reason, any replacement, and Git provenance.

Preserve Git history. Do not copy all deleted material into a new archive directory or create a permanent removal/progress ledger. Retain a small redirect only when an existing external entrypoint demonstrably needs it; do not keep empty placeholders merely to avoid updating links.

**Exit:** Every removal has an explained disposition, useful content and fixtures survive, and maintained docs contain no residual task-state authority.

### Phase 9 — Independent walkthrough and acceptance

**Owners:** Independent reviewer (`high`), validator (`high`), coordinator (`high`).

Review the integrated repository from a fresh context. Follow the evaluator, reader, consumer, browser administrator, writer operator, installer, integrator, and contributor routes from README. Check retained agent instructions separately.

Run the current documentation checker and relevant contract/example tests. Run the repository quality gate at each integrated commit boundary required by the updated workflow. Use stricter browser/build checks only when affected code, assets, examples, or release behavior require them. Do not claim installed acceptance from documentation tests.

Return remaining findings to the responsible editor in a bounded follow-up batch. Stop when the acceptance criteria below are met; avoid an open-ended rewriting loop.

**Exit:** Final diff, complete file dispositions, verified examples, preserved limitations, validation results, and an external completion report.

## 6. Example requirements

Add examples where they help a reader make a decision or complete a task, not to fill every page.

| Scenario | Minimum useful example |
| --- | --- |
| First API read | One configured client, connection/version check, inventory read, short explained output. |
| Discovery | Search by tag/format, inspect a result, interpret incomplete coverage without treating zero matches as proof of absence. |
| Run reports | `runs list` then `runs show` with the returned domain run ID; distinguish it from operation and request IDs. |
| Uncertain job acknowledgement | Preserve the original key, observe the original request/result, and explain why a timeout does not justify a new submission. |
| Consumer copy | Read-only published mount, unique destination, verified result, optional coherent local promotion/serving steps. State helper selection limits. |
| MCP | Protected client configuration, a representative tool call, and an explained response using the actual registered schema. |
| Configuration | Minimal valid configuration plus a focused extension; defaults and validators match the model. |
| Browser action | Actual action labels, permission prerequisite, confirmation if relevant, result, and the appropriate recovery link. |

Label placeholders and representative output. Use small synthetic fixtures for executable examples. Keep credential values out of command arguments and responses; supported protected credential file pathname options remain valid. Explain cleanup only for resources the example creates. Verify examples through existing hermetic tests where possible; do not run production jobs, initialize an archive, mount storage, or download model weights merely to validate prose.

## 7. Validation and regression prevention

### Preserve meaningful existing checks

The baseline contains substantial documentation-dependent tests. Map and retain their behavioral purpose:

| Check family | Preserve | Adapt when restructuring |
| --- | --- | --- |
| `test_docs_alignment.py` / `check-docs.py` | Local links, anchors, audience boundaries, helper catalog, public help checks. | Count floors, obsolete inventory dependencies, known leakage patterns. |
| `test_docs_config_contract.py` | Fields, required settings, defaults, bounds, and validation semantics. | Heading/table selectors and coverage of newly summarized fields. |
| `test_rest_parity_gate.py`, `test_rest_security_gate.py` | Documented route/effect coverage against registered routes and auth behavior. | Exact prose/order coupling where it blocks clearer presentation. |
| `test_rest_examples_gate.py` | Executable SDK examples with mocked transport and meaningful output assertions. | The assumption that the entire document has exactly one Python block. |
| `test_mcp_tools.py`, `test_mcp_client.py` | Actual tool schemas and valid client examples. | Heading, table, and success-output extraction. |
| `test_transactions.py`, `test_verification.py` | Transaction checkpoint sequence and integrity/error taxonomy. | Numbered-heading dependencies when sections move. |
| `test_docs_migration.py`, `test_web_plan.py` | Any still-useful fixture, technical coverage, and provenance guarantees. | Retire obsolete selector, task-status, copied-snapshot, and execution-ledger requirements. |

Use the locked environment during execution:

```bash
uv sync --locked --extra server --extra mcp
uv run --locked --extra server --extra mcp python scripts/check-docs.py
uv run --locked --extra server --extra mcp pytest \
  tests/unit/test_docs_alignment.py \
  tests/unit/test_docs_config_contract.py \
  tests/unit/test_docs_migration.py \
  tests/unit/test_web_plan.py \
  tests/unit/test_verification.py \
  tests/unit/test_transactions.py \
  tests/unit/test_rest_parity_gate.py \
  tests/unit/test_rest_security_gate.py \
  tests/unit/test_rest_examples_gate.py \
  tests/unit/test_mcp_tools.py \
  tests/unit/test_mcp_client.py \
  tests/unit/test_runbook_examples.py
scripts/check.sh
```

The test list is the concrete baseline documentation/contract set. Run affected subsets during editing and use retained or replacement paths as process tests migrate; do not invoke removed files or retain obsolete tests merely to preserve this command. The full gate also performs environment synchronization, lint, types, offline tests, build, and installation checks. When relevant, use `scripts/check.sh --require-web --with-build`; installed functional acceptance requires its own explicitly provisioned fixture and is not a documentation-only default.

### Add only focused regression protection

Use the existing checker rather than introduce a new documentation platform. Enforce removal of the root README Status heading and known agent-tracking references from retained docs. Check new documentation files automatically rather than maintain a fixed minimum count. Preserve exceptions for real domain commands, runtime state, technical IDs, and ADR status.

Do not ban the words “plan,” “status,” “pending,” or “progress” globally. Automated checks can catch specific leakage patterns; a fresh semantic review must catch stale availability claims, misleading examples, unexplained jargon, and wrong-persona openings. Avoid exact-sentence tests and arbitrary word-count gates.

## 8. Acceptance criteria

- Every tracked documentation surface has an explicit disposition and primary audience.
- README has no Status section, local deployment ledger, or replacement progress section.
- README and the documentation index lead each major persona to a useful starting guide.
- Every retained human document is understandable without agent plans, task IDs, handoffs, or transcripts.
- `docs/agents/` contains reusable guidance; no retained documentation acts as a current-plan selector, task-state database, progress log, or agent handoff ledger.
- Source-backed contradictions identified in this review are corrected. Any unresolved product defect is described as a specific limitation, not silently resolved through prose.
- CLI, REST, MCP, configuration, and browser descriptions match their implemented interfaces and supported profiles.
- Examples use consistent prerequisites and paths, show meaningful outcomes, and disclose relevant effects.
- Obsolete files and assets are removed after unique durable content and live references are handled.
- Technical IDs, licensing, attribution, compatibility rules, and meaningful contract/security tests are preserved.
- Documentation and required repository gates pass. The final report distinguishes executed checks, source inspection, and checks that remain environment-dependent.
- A separate reviewer completes the persona walkthroughs and confirms that contribution/release policies cannot recreate the removed material.

## 9. Reusable subagent assignment

```text
Model: gpt-6.1-sol
Reasoning effort: <low | medium | high | xhigh, assigned by role>
Repository/base commit: <current reviewed execution base>
Role and persona: <one responsibility; one primary reader>
Owned files: <exact allowlist>
Task: <one bounded documentation outcome>

Read the assigned documents and the relevant implementation, models, tests,
and durable contracts. Establish facts before rewriting. Distinguish stale
documentation from an implementation defect or a compatibility constraint.

Edit only owned files. Write current behavior for the assigned persona.
Preserve security and recovery semantics. Remove plan-progress and agent-state
content; do not relocate it into another maintained document. Extract unique
durable requirements before recommending deletion. Do not invent flags,
outputs, release claims, tests, or installed acceptance.

Keep task examples coherent. Coordinate parsed tables/anchors with their test
consumers. Use existing hermetic fixtures; do not operate a live archive or host.
Do not change application behavior as part of this documentation assignment.

Return the patch, source-backed claim checks, deletion/replacement rationale,
checks actually run and results, unresolved limitations, and cross-file requests
to the coordinator through the execution system, outside repository docs.
```

## 10. Review limitations

This plan is based on the pinned source checkout, documentation, test code, and static cross-reference review. It does not establish live deployment behavior. The existing documentation checker could not start in the review environment because `markdown_it` was unavailable; the locked application environment and full repository gate were not installed or run. No passing gate or installed acceptance is claimed. The execution team must refresh the baseline and run the prescribed checks in the proper environment.

## Source references

All links below are pinned to the reviewed commit. Implementation should refresh them against its actual base.

[s-readme]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/README.md
[s-web-overview]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/web-ui/README.md
[s-deploy]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/deployment-centos-stream-10.md
[s-status]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/deployment-status.md
[s-release]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/agents/release.md#L130-L135
[s-operations]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/operations.md#L99-L102
[s-cli-source]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/src/hfcache/cli.py#L298-L345
[s-cli]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/cli.md
[s-api-source]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/src/hfcache/api/app.py#L1434-L1460
[s-server]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/server.md
[s-intents]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/src/hfcache/api/intent_routes.py
[s-server-config]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/src/hfcache/server_config.py#L298-L312
[s-quickstart]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/quickstart.md
[s-consumers]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/consumers.md
[s-copy]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/examples/copy-revision.py#L271-L353
[s-web-troubleshooting]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/web-ui/troubleshooting.md
[s-development]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/development.md
[s-doc-tests]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/tests/unit/test_docs_alignment.py
[s-migration-tests]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/tests/unit/test_docs_migration.py
[s-web-plan-tests]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/tests/unit/test_web_plan.py
[s-example-tests]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/tests/unit/test_rest_examples_gate.py
[s-config-tests]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/tests/unit/test_docs_config_contract.py
[s-architecture]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/architecture.md#L280-L303
[s-publication]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/src/hfcache/publication.py#L596-L605
[s-agents]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/AGENTS.md
[s-planning]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/agents/planning.md
[s-record-policy]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/agents/technical-record-policy.md
[s-security]: https://github.com/wtcross/hfcache/blob/7410aaaad0179a3546d7e74fcecf2c2ea98dec97/docs/security.md#L325-L340

