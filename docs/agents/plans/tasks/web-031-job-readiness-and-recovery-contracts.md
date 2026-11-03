# WEB-031: Contract-first state/UX design, disposition and legacy recovery protocol, writer-profile scope, invariant/ADR amendments and finite acceptance matrix

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | None |
| Execution | `gpt-6.1-sol` / `high`; explicit task-agent setting required |

## Scope and acceptance

Contract-first state/UX design, disposition and legacy recovery protocol, writer-profile scope, invariant/ADR amendments and finite acceptance matrix; stop design when these decisions are executable.

The parent plan's applicable scope, acceptance criteria and safety prerequisites
are binding. No remote pushes, image publication, release tags, automatic
schedules, unrelated permissions, archive initialization, manual archive writes,
reboots, NFS disconnection or other-host effects are authorized.

## Contracts, invariants, and ADRs

Reviewed FS02/19/21–23, AD16/17 and INV003/004/005/010/013/014/015/018–022;
FS02/19/21–23, AD16/17 and existing capacity/domain-format/verification/discovery
authority remain. Amend INV003/014/021 and add INV023 for permanent key closure.
ADR164 accepts dispositions, interlock, legacy review and visible GET recovery;
ADR165 accepts protected writer mode/domain and current-boot reversible handoff.
ADRs114/115/118/126/127/141/145/146/150/154/159/162 retain original rationale with
explicit amendment links. Exact current store/runner/auth and predecessor source
were inspected; design is not conformance. Contracts: API/server/schema/security/
containers/host administration/deployment/recovery/discovery and job/admin guides.

## Validation

The finite design-check table below was recorded after the initial contract
text was drafted and before focused validation/gate. No source implementation
has started. Behavioral execution belongs to the named downstream tasks.

| Changed requirement | Smallest meaningful check | Required gate | Evidence/result |
| --- | --- | --- | --- |
| Readiness reasons and scoped automatic GET recovery | Read contract against existing controller/host authorization and hidden-page rules; preserve advisory/unknown distinctions | Focused documentation checks, default gate | Design specified in docs/job-recovery.md; executable/browser checks assigned below |
| Permanent fresh-refusal fence and old-intent retirement | Review serialization, independent flock descriptions, lease handoff, worker/helper pending evidence, failure/capacity/rollback rules against current store/runner | Focused documentation checks, default gate | ADR164 and INV023 specify finite protocol; source behavior pending API-019 |
| Protected writer mode and reversible selection | Review actual runtime/guard/helper/CIL boundaries; fixed role mounts and dedicated writer domain; current-boot manual procedure | Focused documentation checks, default gate | ADR165 specifies executable scope; installed behavior pending OPS-027 onward |
| Independent formats and exact previous reader | Name new disposition1/browser2/runtime2/manifest2 fields and exact 0.3.1 c23abba reader behavior | Documentation link/record checks, default gate | Formats fixed; actual compatibility drills assigned to API-019/WEB-033 |
| Plan activation and technical records | Confirm preserved draft hash, all eight task records, ADR/index/register amendments, one active selector and no extra backlog | Documentation alignment and default gate | Eight task records and exact draft provenance checked; default gate and focused docs pass |

### Finite downstream acceptance matrix

These rows are a handoff of changed requirements, not a new harness or a claim
of passed product acceptance. Each owning task records its smallest checks and
results before source implementation. Reuse unchanged existing evidence with
its original scope. Add rows only for a changed requirement or reproduced gap.

| Owner | Requirement / smallest meaningful behavioral check | Required evidence and gate |
| --- | --- | --- |
| API-019 | Admission/fence concurrency, duplicate after permission change, canonical-body conflict and namespace rotation/separation | Existing store/HTTP tests with exact execution counts; default gate |
| API-019 | Atomic fence crash/fsync/rename failures, absent/partial/corrupt/future state, quotas, receipt expiry/restart non-revival; no compaction | Focused durable-store injection, golden disposition fixture; default gate |
| API-019 | Cross-process shared/exclusive leases with separate open descriptions, queue/worker overlap, failed enqueue, API crash while worker continues, review timeout | Existing runner/private-worker and subprocess flock tests; no helper under store/domain/config locks; default gate |
| API-019 | Own-Basic-key review while archive/control/schedule/observer/host-read are denied; foreign subject/bearer/ID-only refusal | Actual bounded helper/API integration; pending/unknown cohort/effect/worker/journal refusal; default gate |
| API-019 | Exact predecessor 0.3.1 c23abba operation reader against new empty/populated disposition file | Actual previous _scan refuses lookup/list/admit/expire while exact-ID receipt/result still reads; retention leaves fence intact; default gate |
| WEB-032 | Action readiness entry/change/recheck; denied and NFS-ro zero POST; unknown distinct and advisory; server permission race | Built browser + actual API checks with exact POST counts, accessible explanation; default gate with --require-web |
| WEB-032 | Real admission lost ACK, terminal failure, rejected/retired record reload, same-subject rotation, foreign namespaces, storage/malformed/cross-tab/hidden/reconnect | Existing controller/browser tests; GET-only automatic recovery, no replay, separate protected-outcome blocks; --require-web |
| WEB-032 | Atomic schema1-to-2 preserve all handles/scopes/summaries and refuse failed migration | Exact predecessor schema1 decoder refuses2 without overwrite, bounds unchanged; --require-web |
| OPS-027 | Guarded defaults and explicit matching writer runtime/index/helper/profile; unknown/mismatch refusal | Rootless installed owned fixtures prove API/worker RW, Caddy/client no archive, same original/companion locks and fixed mounts; default gate |
| OPS-027 | Actual writer process-domain NFS label authority and helper/observer neverallows, identity/capacity refusals, drained restart and rollback | Owned Enforcing positive/negative role proofs; actual NFS proof deferred OPS-029, retain unchanged verifier isolation evidence; default gate |
| WEB-033 | Changed shared UI/API workflows across affected native/rootless profiles, keyboard/screen-reader labels/narrow layout/200% zoom | Direct installed product acceptance through actual Caddy/TLS/API/browser/worker/helper; no optional --with-web-functional runner; --require-web |
| WEB-033 | Runtime2/manifest2/protected-index and browser2 rollback readers against exact 0.3.1 c23abba | Actual previous readers refuse new authority; retained compatible recovery/admission target works without deleting state; --require-web |
| REL-018 | Matching clean immutable backend/UI/image/helper artifacts and compatible rollback | Existing reproducible release tooling and --require-web --with-build gate |
| OPS-028 | Coordinated backup, real drain, original-lock handoff and NFS-ro selection; genuine Basic negative grants and reported key review | Installed current-boot observation of original key only; preserve historical unknown/handles, zero job replay; --require-web --with-build |
| OPS-029 | Separate authorized NFS writer transition and one selected technical-refresh/Sync pilot each | Exact host/export/UUID/ownership/capacity/reserve/preflight and actual Enforcing transactional writes, genuine admin UI/original API results; no manual archive probes/replay |
| OPS-029 | One enumerated bounded current-publication backfill and final scoped operational handoff | 256-repository/512-publication caps, shared budgets, per-publication bound result or actionable failure; no weights/model-info enrichment; preserve original results/masks/schedules |

## Execution notes and handoff

Activated 2026-11-03 by the user's explicit end-to-end implementation instruction.
Execution actually uses a fresh-context task agent with explicit
`model="gpt-6.1-sol"`, `reasoning_effort="high"`; the coordinator runtime was not
changed or inferred. No effort escalation or additional agents.

Chosen protocol: one bounded permanent disposition file, existing store flock,
one exact cross-process companion interlock, closed own-key review, existing
worker/helper/outcome machinery and fixed writer mode/domain. No generic
workflow engine, framework, scheduler, dependency or new acceptance harness.
Protected deployment, controlled writable transition, selected Sync and refresh
pilots and bounded metadata backfill are authorized after the reviewed safety
prerequisites. Scope is this host/current boot with fail-closed manual startup
permitted; unattended boot acceptance remains separate.

## Completion evidence

The default `rtk proxy scripts/check.sh` passes in1269.9471049308777s as login
UID1000/nice10, with private empty read-only archive shadow and short owned
`/var/tmp/.w31a`:9594 backend tests,52 opt-in deselected, build and three locked
wheel installation profiles.1268 input names/hashes stay unchanged throughout.
Inner log SHA256
`88f546da24202b56aebea862946b2c80d647bc8aef0a747c44d14ad48b8f7032`;
shadow `2ce8936f98522ec01cc38c373e17533d3549150ccd834d8b922ac5b24f332b74`.
Raw logs/results/frozen hashes remain in `.scratch/web031-validation/`.
No frontend, installed behavior or writer acceptance is claimed by this gate.

After the frozen gate, coordinator review resolves two concrete contract
clarifications: immutable mode sibling release_id joins and observation-only
safe-store degradation when disposition authority is unavailable. Active-plan
language is reconciled with actual activation, and completion records advance.
These subsequent documentation changes are explicitly outside the gate-time
hash manifest; focused documentation alignment passes216 human documents/29
helpers and all69 documentation tests pass. Final metadata validation and
whitespace checks are recorded in the same evidence directory. No product
source code, architecture checkpoint table or CLI taxonomy table changes.

The first docs checker rejected new ADR audience leakage (task IDs/link);
corrected human ADR metadata/links. Initial documentation tests passed68/failed1
because relocated verbatim draft Markdown links resolved against its new
directory. Rename only the preserved artifact to original-draft.txt, retaining
exact SHA256 `2b823aae1a8b18c01f019a75a46587a9cbeae88ec4ea8cf2d36367ca04fa491b`.
Raw initial failures are preserved; no assertion or gate stage was weakened.

Only this successful gate's exact temp root dev64768/inode204471662 is retired,
after root-agent review, complete159824-entry inventory, verified compressed
manifest25d7622c7a887e989ad13c8cf0df2fa7c121195ce7a769e34689855e5f3e1658,
two stable inventories and fresh all-UID337-process zero-reference proofs.
Retirement receipt
`fc6fe3b501774d9d4c357faa7cf89f6fec8a097ee579045a92a68edf78f58278`
remains under `/var/tmp/hfcache-web031-gate1-retirement/`; root free returns to
1214545920 bytes. All raw logs, original failures, historical fixtures and
application artifacts remain. No engine, service, production/archive state,
permission, mount or original application lock is changed.

ADR164/165 and INV023 complete design acceptance; implementation and actual
installed conformance belong to the finite downstream matrix. API-019 is next
and pending, with no known source blocker. Preserve the separate first-upgrade
actual executor drain; new interlock ownership alone cannot prove older
uninterlocked executors ended.
