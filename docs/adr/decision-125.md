# Decision 125 — Expose nine typed metadata tools through a narrow read capability

- Status: Accepted; implemented by MCP-002.
- Date: 2026-10-18.
- Work package: MCP-002, this commit.
- Source: [progress decision 125](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/mcp-002-curated-read-only-tools.md).

## Context and decision

MCP-001 committed authenticated transport (`d808a05`) without tools. Expose exactly
nine named metadata tools from plan §8, through explicit typed async adapters and
a narrow read protocol. No resources/prompts, dynamic dispatcher, full OpenAPI
conversion, command service, writable helper, Hub/credential resolver or arbitrary
path/URL input is available to adapters. The app owns bounded metadata offload;
the transport-neutral backend reads existing validated authoritative evidence.
No tool accepts an SDK Context/Request/application object that exposes the wider
writer. Read-only/non-destructive/idempotent/closed-world annotations describe
this structural boundary; they are not authorization or side-effect proof.

Return a strict frozen `MetadataRead` wire object with independent schema 1,
server request ID, archive UUID, fresh installed config fingerprint, the existing
typed domain Envelope and optional next cursor. A backend `QueryPage` contains
its immutable ServiceResult and cursor. Preserve original report run identity,
policy fingerprint and timestamps inside the report projection; fresh wrapper/
query metadata never replaces historical evidence. No new durable/config schema
or dependency is introduced.

Bounds are explicit: omitted limit resolves to min(100, configured server maximum),
requested limits are 1–10,000 and cannot exceed that maximum, at most 64 selectors
of at most 256 characters each, and cursor at most 256 characters. Fixed typed
identifiers use shared repository/SHA/publication/run grammars. Inventory SHA
suffixes follow shared legacy semantics and are ignored for repository scope;
selector order/duplicates canonicalize for cursor scope without changing source
ordering. No user argument selects an archive/config/credential pathname or endpoint. Scan/artifact/response
budgets and the existing transport/metadata capacity fail visibly, never return
a silently truncated successful result.

Inventory/status/revisions and report lists preserve existing domain ordering
and unmanaged/empty distinctions. Their cursors bind tool, normalized filters,
installed fingerprint and the complete selected row collection. Status archive
headline/warnings are fresh observations on each page, not snapshot-bound:
benign free-space changes must not invalidate a repository-row continuation.
Changed policy or rows refuse HFAPI007. Pages are not a global archive snapshot;
only explicit next-cursor exhaustion completes the selected collection.

Current reference is read once with validated `published/`-relative locators;
manifest reads require the exact full SHA and publication ID. A vanished or
mismatched requested instance never falls back to a newer current publication.
Manifest output is explicitly `projection=true`: original header without both
files/dependencies, selected collection, paged entries, total_entries and
`tree_base="archive-root/"`. Header file_count/total_bytes describe the complete
validated manifest, never just its returned page. Reassembling both collections
is required before treating it as the original durable record.

Reports are likewise explicit projections: report_type, original header without
its primary collection, collection, entries and total_entries. General run reads
accept run/recovery/verification evidence; the verification-specific tool requires
a VerificationReport and refuses the wrong kind with HFARG004. Collections are
repositories/remediations/findings respectively. Bind immutable artifact cursors
to the entire validated sanitized source, including unreturned headers and collections. Sanitize registered values,
including known numeric literals, before hashing: hidden secret substitutions
must not create credential-dependent cursor fingerprints. Changes to visible
headers or collections refuse continuation.
Reading findings or estimating metadata cost never hashes, persists verification,
increases confidence, repairs content or rebuilds a missing catalog.

Failure never fabricates MetadataRead with an unknown fingerprint or successful
page. Classified backend HfcacheErrors become explicit MCP ToolError containing
stable code(s) plus fixed `metadata query failed`, without paths/rejected values.
Supported SDK call middleware converts SDK argument validation to fixed HFAPI006
and unknown tool to HFAPI007. An exact-name guard runs before SDK lookup/tracing
and refuses aliases as well as unapproved names. Raw validation can bypass the
SDK's mask flag, so that flag alone is insufficient. Unexpected failures remain fixed/masked. The
middleware is a protocol error guard, not a context/app capability supplied to
the nine tool functions or read backend.

## Rationale and alternatives

A full REST conversion would expose jobs, diagnostics/probes and credential-bearing
planning that are outside the MCP metadata boundary. Hints alone cannot prevent
those effects. Explicit adapters with only nine read methods keep authority
inspectable and complete-registry equality testable.

Returning a partial file/report array as a complete durable object would falsify
its totals and verification authority. Explicit projections preserve header
meaning and exact identity while bounding transport cost. Offset-only cursors
could silently skip changed rows; content binding refuses instead. Pinning an
old reference but substituting a new manifest would violate FS-12.

## Consequences and evidence

Amends [124](decision-124.md), [113](decision-113.md),
[AD-10](ad-10.md), [AD-15](ad-15.md) and [AD-21](ad-21.md). Preserves FS-08–12/16,
INV-005/007/008/012/013/016 and existing domain/error/unknown-confidence semantics.
Archive-sourced strings remain untrusted data, never executable instructions.
MCP-003/004 and final acceptance remain later tasks; operator holds remain.

[MCP](../mcp.md) defines every tool's inputs/output/order/cost/errors;
[API](../api.md) and [consumers](../consumers.md) retain bulk-copy and exact locator
boundaries. Task evidence must include complete registry/input/output schemas,
actual mounted success/failure calls, REST/shared parity, changed/stale identity,
large/partial/unknown metadata and archive/control-state side-effect snapshots.
No production operation, deployment, push, merge or tag is authorized.

Official [FastMCP tool/typed output/annotation reference](https://gofastmcp.com/servers/tools)
was checked against locked 4.1.1. Supported middleware handles argument/not-found
errors rather than trusting the SDK mask flag to hide rejected values.

Implementation: [transport-neutral backend/models](../../src/hfcache/services/mcp_queries.py),
[nine tools/narrow protocol](../../src/hfcache/mcp_tools.py),
[app-owned facade](../../src/hfcache/api/mcp_reads.py),
[bounded wiring](../../src/hfcache/api/app.py),
[backend cases](../../tests/unit/test_mcp_queries.py) and
[actual registry/tool proof](../../tests/unit/test_mcp_tools.py).

Repository acceptance completed 2026-10-18: actual mounted registry/tool selection
passes 65 cases, final mounted/pool selection 66 and direct backend/legacy readers
32. The first full gate exits 0 with 3,481 Python tests (40 deselected, 401.60
seconds), all three locked wheel profiles and 127 Cockpit tests/production build.
No gate correction or post-freeze source change. The task owns exact commands,
results and remaining operator holds; MCP-003/004 and final acceptance remain
pending after this package's commit.

## 2026-10-18 mounted security traceability (MCP-003)

[MCP-003](../plans/tasks/mcp-003-mcp-security-and-side-effect-tests.md) maps this
existing decision to required [threat/control/test evidence](../mcp.md#threat-control-and-test-traceability-mcp-003).
Parent-lifespan mounted authorization, closed registry/arguments, whole-state
snapshots, malformed evidence and secret containment, finite mixed-interface
work and cancellation/drain ownership are proofs of the existing boundary.
They add no role/tool/durable format or architectural choice. Post-startup
baselines exclude atime and permit sanitized operational logging; concurrent REST
fixture effects remain attributable to REST. Actual host credential/egress/
transport/SELinux/NFS/drain/rollback acceptance remains separate operator work.
Repository proof completed 2026-10-18: the first full gate exits 0 with 3,522
Python tests (40 deselected, 417.54 seconds), all three locked wheel profiles and
127 Cockpit tests/production build. No runtime source or architectural choice
changed. The task owns exact evidence; MCP-004/API-017 and real host acceptance
remain separate. No new numbered decision is introduced for these proofs.
