# MCP-002: Expose a curated, structurally read-only archive toolset

| Field | Value |
| --- | --- |
| Work package | `MCP-002` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [MCP-001](mcp-001-mount-authenticated-fastmcp.md) |
| Phase | 4 — Read-only MCP |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `MCP-002: expose curated read-only archive tools` |

## Scope and acceptance

1. Implement exactly the initial tool allowlist in plan §8 using the narrow read-service interface: status; repository/revision inventory; exact current reference and manifest; existing run/verification evidence; and estimate-only verification cost. Register stable descriptive names, typed inputs/outputs, bounded pagination, and honest unknown/stale results.
2. Pin publication identity when resolving refs/manifests. Do not substitute a newer instance when a requested publication vanishes. Read authoritative evidence and never repair/rebuild a catalog as part of a read. Treat metadata/content-derived strings as untrusted data.
3. Make command submission, writable helpers, Hub clients, credential resolution, and arbitrary path/URL reads unavailable to tool adapters. No automatic full-OpenAPI conversion, generic dispatch, doctor probes, actual verify, download, mutation, recovery, or cleanup tools.
4. Add read-only/non-destructive annotations as descriptions, not enforcement. Enumerate the complete registry and test exact equality to the approved allowlist. Any new resource/prompt handler must receive the same structural and side-effect review rather than becoming a hidden bypass.

## Contracts, invariants, and ADRs

`AD-15`/`AD-21`, `FS-08`–`FS-12`/`FS-16`, `INV-005`/`INV-007`/`INV-008`; plan §8.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Document every tool’s inputs, output, ordering/bounds, source of truth, cost, confidence limitations, and error cases in MCP docs. Update API/consumer cross-references and the invariant/ADR rationale for whitelist-only exposure.

## Validation

Planned checks, not execution evidence:

Tool schema/registry snapshots, parity with REST/shared read service results, pagination and large manifests/reports, corrupt/missing catalogs, unmanaged data, partial archives, traversal/identity mismatch, stale publication, and unknown verification confidence. Assert no Hub/command/mutation adapters are called. Run `scripts/check.sh`.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../agents/workflow.md). Work only on
`feat/rest-api-and-mcp`. A task may include several related subtasks, but this
work package owns one implementation commit. Read the affected invariant and ADR
sections before editing; update their enforcement/decision links where behavior
changes. Include code, tests, documentation, task evidence, the current pointer,
and completed progress audit together. Do not run production operations or weaken
host controls. Do not push, merge, tag, or deploy.

Mark `in_progress` only when authorized and dependencies are complete. On a real
blocker, record the exact missing prerequisite and unblock condition. A skipped
required test is not passing evidence. Use `this commit` until a real commit exists.

## Execution notes and handoff

Activated 2026-10-18 under Tyler's authorized REST-first plan after completed
dependency MCP-001 committed clean as `d808a05`. Git/current/dependency were
reconciled; MCP-002 was the sole task in progress. MCP-001's definitive full gate
passed 3,394 Python tests, all three locked wheel profiles and 127 Cockpit tests.
Collaborators own a transport-neutral narrow read backend, explicit typed MCP
adapters/app wiring and actual registry/schema/adversarial tool proof; all
Markdown belongs to this work package. Decision 125 follows the actual log.

Contract-first design admits exactly the nine plan-§8 read names, no resources
or prompts. The adapter receives only the narrow read protocol, with no command,
Hub, credential resolver, writable helper or arbitrary path/URL input. Existing
safe authoritative reads, immutable publication identity, unknown-confidence
semantics and metadata budgets remain. Collaborator inspection settled the exact
inputs, projections, cursors and source/side-effect proof below. No new dependency,
durable/config format, production operation, deployment, push/merge/tag or
MCP-003/004/API-017 implementation. Operator-only acceptance stays held.

Decision 125 and the nine-tool contract precede implementation. Strict frozen
MetadataRead has independent schema 1, request_id/archive_id/config_fingerprint,
existing typed Envelope and nullable next_cursor; QueryPage holds ServiceResult
and cursor. Limits resolve min100/servermax, explicit 1..10000 within servermax,
selectors at most64×256 and cursor at most256. Manifest projections omit both
files/dependencies from original headers and page the chosen collection; reports
omit their primary repositories/remediations/findings collection. Full validated
sanitized artifact content (including other collections/headers), requested identity, tool/collection and current policy bind artifact cursors.
Inventory/status/revision cursors instead bind complete selected rows/filter/
policy; headline/warnings are fresh per page, so benign free-space changes do not
break continuation. Registered values, including numeric literals, are sanitized
before hashing; hidden secret substitutions cannot create credential fingerprints.
No current fallback for vanished exact publication, false complete-artifact claim or confidence increase.

Classified backend failures use stable code(s)+fixed metadata-query-failed text,
not fabricated wrappers with unknown fingerprints. Supported call-error middleware
maps SDK argument validation to HFAPI006 and unknown tool to HFAPI007, preventing
raw rejected input echoes beyond the mask flag. Exact-name checks precede SDK
lookup/tracing and refuse aliases. Nine actual tool functions take
no SDK Context/Request/app object; that protocol guard grants no wider capability.
AD-10/15/21, FS-08–12/16, INV-005/007/008/012–016 and decisions113/124 are reviewed
and amended where exposure changes; unchanged dependencies/formats/framework
constraints remain.
Source names now settled: services/mcp_queries.py owns MetadataRead, QueryPage
and MetadataReadQueries; mcp_tools.py owns MetadataReadPort and nine explicit
async functions; api/mcp_reads.py owns MetadataReadAdapter, and app wiring alone
gets supported request context/submits bounded metadata work. Tools/backend get
no SDK Context/Request/app object or command capability. Selector scope follows
shared RepositoryQuery: valid SHA suffix ignored, sorted unique canonical TYPE:ID
scope binds cursors while returned order remains domain order. All source owners
released their focused source/schema/registry/side-effect proof before the full
gate. The actual completed acceptance follows.

## Completion evidence

Completed 2026-10-18, this commit. Exactly nine typed async metadata tools use a
narrow read protocol and app-owned bounded metadata offload over existing safe
readers. No resources/prompts, generic dispatcher, SDK app/request capability,
command/Hub/credential/write helper or arbitrary path/URL input is exposed.
Complete registry/input/output schemas, read-only hints and exact-name refusal
before SDK lookup/tracing are tested through the actual mounted SDK. Hints are
not the enforcement. Successful and failed calls preserve archive and operation
state, with command/Hub/credential/hash tripwires after startup.

Strict schema-1 MetadataRead retains fresh request/archive/policy metadata plus
the shared domain Envelope. Exact current/publication identity, canonical locator
bases and historical report run ID/fingerprint/times remain. Explicit manifest
and run/recovery/verification projections page selected collections without
claiming complete durable records. Both manifest collections or the report's
full primary collection must be reconstructed before validating an original.
Inventory cursors bind selected rows/filter/policy while status headline/warnings
remain fresh observations; a deterministic changing-capacity regression preserves
continuation and nested warnings. Immutable artifact cursors bind all sanitized
headers/collections. A direct two-registered-string substitution test proves
hidden values do not change visible-source cursor binding; encoded numeric
literals are also scrubbed in source, with separate transport refusal coverage.
Canonical selector SHA/order/duplicate equivalence preserves domain order.
Unknown catalogs stay unknown; estimates never hash/persist/increase confidence.
Classified fixed safe ToolError output never fabricates success or an unknown
fingerprint, including SDK validation/unknown names and stale/wrong-type evidence.

Final actual mounted command
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_mcp_tools.py -x -q`
passed 65 in 18.71 seconds. Its registry/side-effect/complete-collection/artifact
reconstruction/report provenance cases cover all nine tools, empty/unmanaged
and partial evidence, missing/corrupt catalogs, traversal/identity/stale cursors,
changed unreturned artifact headers/collections and explicit size/scan budgets.
After the exact-name prelookup guard, combined mounted/pool selection passed
66 in 18.68 seconds; final guard/pool selection passed 3 in 2.03 seconds. Shared
metadata-pool proof covers off-loop work, saturation/refusal, responsive REST and
lease release. Direct backend plus legacy reader selection passed 32 in 2.03
seconds; updated transport/core selection passed 63 in 14.82 seconds. Documentation
anchor/parity command
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_rest_examples_gate.py::test_current_interface_documentation_has_resolvable_local_files_and_anchors tests/unit/test_rest_parity_gate.py -q`
passed 63 in 1.14 seconds before semantic freeze.

First full
`rtk proxy bash scripts/check.sh > .scratch/mcp-002-gate.log 2>&1`
exited 0: lock/both-extra sync, 380 formatted files, Ruff clean, whole Pyrefly
0 errors (11 suppressed, 59 warnings not shown); 3,481 Python tests passed,
40 deselected in 401.60 seconds. Source distribution and wheel 0.1.10 built;
actual locked isolated base/server/server+MCP installation/import/help/version
checks passed. Cockpit ESLint/Stylelint/TypeScript passed, 127 tests passed with
0 failures in 2.093 seconds, and production build passed in 1,246 ms. No full-gate
failure/correction/restart or post-freeze source change.

Decision 125 and AD-10/15/21, 113/124 amendments preserve FS-08–12/16 and
INV-005/007/008/012–016. Shared readers and metadata/transport budgets remain the
enforcement; FS/TX/domain algorithms, whole-archive roles, dependencies and
archive/receipt/config formats are unchanged. No durable-format drill is needed
for this transport-only projection. MCP/server/API/config/security/consumer/
schema/architecture contracts, active plan, README and Unreleased agree.
Final local links/anchors, task/current/dependencies, unchanged 29 REST modes,
125 unique indexed decision/ADR records and whitespace pass; see the completed
[progress audit](../../progress.md).

Current selects MCP-003 pending after this package's commit. Its dedicated
security/side-effect acceptance and MCP-004/API-017 remain separate later work.
Live Hub/NFS and extra build-marker suites were not run. Real installed systemd/
cgroup/no-IP/credential masks/custom paths/browser/PAM/SELinux/NFS/drain/rollback/
verify-calendar and MCP enablement checks remain operator holds 16–18. No
production archive/service operation, installation, deployment, push, merge or tag
occurred.
