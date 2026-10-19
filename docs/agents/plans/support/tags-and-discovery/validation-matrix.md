# Acceptance and validation matrix

All cases below are **planned, not executed**. Task completion evidence must cite
actual test names, commands, outcomes and relevant fixtures. IDs are test-scenario
references, not another work-package/task sequence. Synthetic repositories and
small constructed headers are required; never download real weights for tests.

| Case | Owning package | Scenario | Required observable result |
| --- | --- | --- | --- |
| V01 | CAT-002 | Old configs and explicit tags=[] | Both validate; omitted tags equal empty; old policy fingerprint goldens remain identical. |
| V02 | CAT-002 | Tag normalization | Case/outer-space variants deduplicate and sort; a second normalization is unchanged. |
| V03 | CAT-002 | Bad tag inputs | Nonstring/coercive/empty/control/non-ASCII/oversized values and >64 raw elements refuse without echoing secrets. |
| V04 | CAT-002 | Tag-only edit | Curation identity changes; operational policy/publication/integrity identity does not. |
| V05 | CAT-003 | Full candidate comparison | Concurrent tag-only edits cannot be accepted as an unchanged candidate/base; no lost update. |
| V06 | CAT-003 | All Cockpit edit paths | Add/edit/disable/form-text round trip, validation, backup and installation preserve canonical tags. |
| V07 | CAT-003 | UI suggestions and backend authority | Existing local tags are suggested without a registry; backend rejects a malicious/invalid bypass. |
| V08 | CAT-004 | Record schema/path identity | Round-trip goldens preserve fields/order; wrong archive/repo/SHA/publication/manifest identity refuses. |
| V09 | CAT-004 | Unknown existing record | Unsupported version, malformed canonical JSON or symlink is preserved and refuses replacement. |
| V10 | CAT-004 | Atomic-write failure points | Before temp fsync/replace/parent fsync and between records: only whole old/new records visible; no multi-file atomicity claim. |
| V11 | CAT-004 | Initialized archive guards | Missing/wrong sentinel, local-directory fallback or unsafe new namespace fails; no init or sentinel rewrite. |
| V12 | CAT-005 | Safe bounded card/JSON parsing | Alias bombs, deep nesting, duplicate JSON keys, huge declarations and invalid Unicode are bounded and diagnosed, never executed. |
| V13 | CAT-005 | Curated versus upstream tags | Upstream tags cannot add/remove effective operator labels; evidence keeps its source. |
| V14 | CAT-005 | Dataset static declarations | Formats and declared splits/configs remain attributed; no loaders, external payload fetch or inferred row count. |
| V15 | CAT-006 | Single GGUF positive/float fixtures | Known headers map to exact schemes; F16/F32 are encodings, not quantized Q variants. |
| V16 | CAT-006 | Misleading filenames | A filename-only Q4 claim does not override a conflicting header or prove a scheme. |
| V17 | CAT-006 | Hostile GGUF header | Huge counts, overflow, truncation, unsupported versions/types, invalid endian handling and nested arrays terminate within bounds. |
| V18 | CAT-006 | Shard completeness | Full unique same-publication shard set matches; missing/duplicate/conflicting/cross-directory sets do not falsely combine. |
| V19 | CAT-006 | Auxiliary weights | Projector/adapter/unknown-role candidate does not satisfy an available primary-model search. |
| V20 | CAT-007 | AWQ/GPTQ static declarations | Known method/bits/group-size tied to an unambiguous weight bundle; no inference-library imports. |
| V21 | CAT-007 | Weight-index membership | Escaping, absent, duplicate and ambiguous members are diagnosed; config-only/LFS pointers are not complete weights. |
| V22 | CAT-007 | Multiple quantized subdirectories | A root declaration is not propagated into unrelated bundles; each variant retains scoped evidence. |
| V23 | CAT-008 | Successful sync with new revision | Exact publication observations and tag snapshot are recorded under existing lock ownership after publication. |
| V24 | CAT-008 | Retained-SHA sync and tag changes | Tags/metadata can refresh without new model download/publication; original manifest bytes remain unchanged. |
| V25 | CAT-008 | Extractor failure and producer lifetime | Valid archive publication survives supplemental failure, warning/coverage is honest, producer is joined before lock release. |
| V26 | CAT-009 | Offline refresh and permissions | Writer refresh handles configured/retained/unmanaged scope with no Hub/model load/verification or config write. |
| V27 | CAT-009 | Partial refresh and idempotency | Per-record progress is honest; duplicate key observes original result; new capture requires a new key. |
| V28 | CAT-009 | Removal before/after capture | Historical tags exist only after a real capture; uncaptured labels are not invented; empty re-added config wins. |
| V29 | CAT-010 | Configured/archived/all scope | Disabled/unarchived/unmanaged states behave as specified; type+ID identity union has no duplicates/phantoms. |
| V30 | CAT-010 | Tag ALL/ANY and text | Exact normalized set predicates; AND across fields; q is literal substring, never regex/instructions. |
| V31 | CAT-010 | Same-variant conjunction | Q4=4GB plus Q8=8GB does not match Q8<=5GB; no cross-revision or cross-format predicate mixing. |
| V32 | CAT-010 | Current versus retained | Use explicit current even when its generation is lower; pruned/retired repair observations cannot match. |
| V33 | CAT-010 | Missing/failed observation coverage | Known matches may return with explicit scoped incompleteness; zero does not imply absence; scan exhaustion fails. |
| V34 | CAT-010 | Facet counts | Distinct repositories after full filters; no shard/revision inflation or values from unrelated variants; correct historical source scope. |
| V35 | CAT-010 | Representative versus full variants | One deterministic representative and accurate full count; paged variants enumerate without silent omission. |
| V36 | CAT-011 | Cursor equality and staleness | Tag order/duplicates canonicalize; tag edits, repair/prune/current/enrichment/coverage changes invalidate continuation. |
| V37 | CAT-011 | HTTP route grammar | Unknown keys/repeated scalars/GET bodies/invalid numerics/oversized headers/query/path escapes refuse safely. |
| V38 | CAT-011 | Transport auth and strict wrappers | REST reader/writer succeed on reads; MCP/Hub/absent bearer refuse; old wrappers and inventory routes retain compatibility. |
| V39 | CAT-012 | Refresh admission boundaries | Only writer can POST; missing key/invalid booleans/path/URL/credential overrides refuse; no automatic retry/replay. |
| V40 | CAT-012 | Observer disconnect/restart | Handles and exact result identities survive; disconnect never cancels or duplicates accepted refresh. |
| V41 | CAT-013 | CLI/SDK complete collection | Bounded complete pages, exact archive/policy/catalog identity checks; stale cursor, budget or partial walk fails visibly. |
| V42 | CAT-013 | Reader profile isolation | Base client/CLI import and install without server/MCP/model runtimes; no mount, Hub token or local fallback. |
| V43 | CAT-013 | CLI output parity | JSON retains exact server evidence; human/quiet modes show incomplete coverage/warnings; no misleading empty-success rendering. |
| V44 | CAT-014 | Exact MCP tool set | Nine original plus five new names at baseline; aliases and refresh/write tools absent; existing calls unchanged. |
| V45 | CAT-014 | MCP capability injection | Tools/adapters cannot reach commands, app/request, Hub credentials or writable storage; annotations alone are not accepted proof. |
| V46 | CAT-014 | REST/MCP semantic parity | Equivalent normalized queries yield same identities/tags/variant predicates/facets/coverage and consistent pagination. |
| V47 | CAT-015 | Prompt injection and display safety | Malicious card text, filenames and labels remain data; safe terminal/browser rendering; no code, shell or URL execution. |
| V48 | CAT-015 | No read side effects | Filesystem/lock/network/import spies show searches cannot open model payloads, rebuild observations, write records or contact Hub. |
| V49 | CAT-015 | Shared work/wire ceilings | Queue saturation, canceled readers, tiny page/full scan, huge single variant and response encoding all stay bounded and honest. |
| V50 | CAT-015 | Registered-secret side channels | Filtering, facets, diagnostics and cursor hashes cannot reveal a sanitized secret value or distinguish hidden substitutions. |
| V51 | CAT-016 | Repair/prune/purge lifecycle | New pub gets independent observations; removed instances never match; inert metadata cannot resurrect inventory or confidence. |
| V52 | CAT-016 | Old-binary layout/config/operation drill | Test actual compatibility and refusals; preserve unsupported state; document a non-destructive operator rollback path. |
| V53 | CAT-016 | Old evidence/format compatibility | Existing manifest/ref/report goldens unchanged; old inventory and original MCP tools still pass. |
| V54 | CAT-016 | Docs and installation profiles | Current behavior documented; agent/human separation holds; full check.sh --with-build and actual frontend gate pass. |
| V55 | CAT-016 | Final workflow closure | All task evidence and incremental commits agree; plan completed/current inactive; no unauthorized push/deploy/live action. |

## Required checks per work package

Run the affected focused offline tests during development, then `scripts/check.sh`
and record its exit status and reported results. The gate already selects locked
server and MCP extras; do not use a base-only environment that silently omits tests.
Run `make -C cockpit check` with the installed toolchain for every Cockpit change;
a skip in the overarching script is not success for that task. At final acceptance
run `scripts/check.sh --with-build` and confirm the frontend stage actually ran.

Do not fabricate test totals or success hashes in advance. Required missing tools
or failing baseline tests are blockers with exact unblock conditions, not reasons
to weaken assertions. All archive/workload tests here use offline temporary
fixtures and injectable preflight; live/NFS markers require separate operator
authorization and are not prerequisites to claiming only offline acceptance.

## Test organization

Prefer small dedicated suites for tag normalization, metadata records, GGUF and
quantization extraction, catalog queries, REST catalog reads/commands, catalog
client/CLI and MCP catalog tools. Integrate shared domain/transport fixtures rather
than cloning implementation algorithms in assertions. Property-style generated
cases may use existing tooling; no new dependency is assumed.

Test counterexamples, not merely happy response snapshots: unknown versus false,
current versus largest generation, primary versus auxiliary variants, one variant
versus repository unions, tag identity versus policy identity, and last observed
versus current configuration. Use file/network/import spies and fault injection to
prove read-only and bounded behavior. A small `limit` never justifies skipping a
large underlying validation budget.
