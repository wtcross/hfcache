# Architectural decision records

Start with the topic map below, then read only the records relevant to the
change. [The invariant register](../invariants.md) states current constraints;
[architecture](../architecture.md) and the other area contracts contain the
detailed requirements. ADRs explain the choices, alternatives, consequences,
and amendment history. A historical accepted decision is not evidence that
its original policy is still current: follow its status and amendment links.

## Coverage and provenance

The initial backfill preserves the existing `AD-01`–`AD-21` identifiers and
all 105 numbered decisions already in [the progress log](../progress.md#decisions),
including operational, release, and tooling choices whose consequences explain
the architecture. Three additional records capture existing framework,
verification, and scheduling decisions that had no individual `AD-nn` section.
Decision 106 records this documentation change. Existing identifiers are not
renumbered: `ad-04.md` is architecture `AD-04`, while `decision-004.md` is
progress decision 4, a different choice.

Records were reconstructed from the governing documents, implementation,
tests, and actual introducing/amending git commits. Original dates describe
when the decision was made, not the backfill date (2026-10-17). Source prose
and its evidence remain available; no missing alternative is invented. The
progress Decisions log remains append-only and the progress file retains
completed work-package evidence and Operator handoff. Under
[decision 107](decision-107.md), [current.md](../plans/current.md) selects the
active plan, and task files own active execution status; historical backlog
does not activate itself.

## Topic map

| Area | Start here | Related implementation decisions |
| --- | --- | --- |
| Complete snapshots and observations | [AD-01](ad-01.md), [AD-02](ad-02.md), [AD-03](ad-03.md) | [Safe paths](decision-014.md), [collision policy](decision-015.md) |
| Storage, publication, and hashing | [AD-09](ad-09.md), [AD-10](ad-10.md), [AD-11](ad-11.md), [AD-18](ad-18.md) | [Path bases](decision-013.md), [same-operation inode evidence](decision-093.md) |
| Retention, repair, and deletion | [AD-04](ad-04.md), [AD-05](ad-05.md), [AD-06](ad-06.md), [AD-13](ad-13.md), [AD-20](ad-20.md) | [Prune commit semantics](decision-077.md), [purge](decision-096.md), [three-revision default](decision-102.md), [HTTP maintenance authority](decision-117.md) |
| Recovery and quarantine | [AD-12](ad-12.md), [AD-14](ad-14.md), [AD-16](ad-16.md), [AD-17](ad-17.md) | [Journal unknown fields](decision-020.md), [cleanup authority](decision-103.md), [supervised cancellation](decision-104.md), [legacy history](decision-105.md) |
| Hub access, credentials, and dependencies | [AD-07](ad-07.md), [AD-08](ad-08.md), [AD-15](ad-15.md), [AD-21](ad-21.md) | [Credential validation](decision-011.md), [explicit restricted scope](decision-098.md), [server credentials and capabilities](decision-112.md), [command/candidate authority](decision-116.md), [candidate validity/authority](decision-119.md) |
| Sync throughput and capacity | [AD-19](ad-19.md) | [Bounded memory](decision-086.md), [one producer](decision-094.md), [failed reports with warnings](decision-095.md), [context propagation](decision-111.md) |
| Verification and durable reporting | [Offline verification](offline-verification.md) | [Verification state](decision-051.md), [publication identity](decision-062.md), [retained set](decision-073.md), [nullable corrupt identity](decision-078.md), [complete verification lock](decision-110.md), [execution/process isolation](decision-111.md), [private verifier/reconciliation](decision-115.md) |
| Deployment, scheduling, and hardening | [Scheduling authority](systemd-scheduling.md) | [Mount units](decision-058.md), [hardening probe](decision-059.md), [offline egress](decision-060.md), [setgid exception](decision-061.md), [safe deploy](decision-065.md) |
| Consumers and serving | [AD-10](ad-10.md) | [Independent copy helper](decision-067.md), [promotion ownership](decision-099.md), [serving mounts](decision-100.md) |
| Cockpit administration | [Plugin boundary](decision-087.md) | [Operation surface](decision-089.md), [bundled TOML](decision-091.md), [credential import](decision-092.md), [repository links](decision-101.md), [candidate validity/authority](decision-119.md) |
| Framework, dependencies, and development | [FW-01–FW-04](fw-01.md) | [Transport boundary](decision-108.md), [submission receipts](decision-109.md), [scoped correlation/redaction](decision-111.md), [server dependency/configuration boundary](decision-112.md), [authenticated metadata lifespan](decision-113.md), [durable admission without replay](decision-114.md), [bounded execution/private verifier](decision-115.md), [typed command admission](decision-116.md), [explicit maintenance authority](decision-117.md), [independent typed client](decision-118.md), [reader/candidate integration](decision-119.md), [Runtime baseline](decision-007.md), [provider-neutral gate](decision-008.md), [plugin toolchain](decision-088.md) |
| Documentation and work-package process | [Router](decision-081.md), [workflow](decision-082.md), [register upkeep](decision-106.md), [plan/task authority](decision-107.md) | [Portable runbooks](decision-085.md), [current invariant register](../invariants.md), [planning guide](../agents/planning.md) |

## Maintenance rules

For every change or new plan being implemented:

1. Review the affected invariant sections and relevant ADRs before implementing.
   Record this review in the work-package evidence. When no invariant or
   architectural choice changes, do not create a placeholder ADR.
2. Add every new invariant to `docs/invariants.md` in the same work package;
   update changed constraints and detailed contracts together. Preserve IDs,
   and explicitly record any retirement, replacement, or narrow exception.
3. Record each new architectural choice in the numbered progress Decisions
   log and in `decision-NNN.md`, using the same number, padded to at least
   three digits. Add it to this index and the relevant topic row. A new
   `AD-nn` architectural rule also receives its corresponding `ad-nn.md` and
   architecture section, with links between the rule and its progress record.
4. Amend an existing ADR's status and amendment links when the choice evolves.
   Retain its original context, decision, rationale, and evidence. A replacement
   decision gets a new record; link both directions and identify whether it
   supersedes the whole record or just one policy. Never reuse an identifier.
5. Keep contracts, invariants, ADRs, index, plan amendments where needed, and
   the task/plan/current records and completed `docs/progress.md` evidence
   together in the implementation commit. Run the repository
   gate and verify local documentation links and record coverage before
   committing, as required by [the workflow](../agents/workflow.md).

Each new record must identify:

- **Identity and status:** stable source ID, title, original decision date,
  work package, and `Proposed`, `Accepted`, `Amended`, or `Superseded` status
  (qualified historical status is appropriate for backfilled records).
- **Context and decision:** the problem or constraint and the selected approach.
- **Rationale and alternatives:** why it was selected and what was rejected.
  If the historical source does not document an alternative, say so.
- **Consequences:** resulting behaviour, tradeoffs, compatibility, and limits.
- **Evidence and relationships:** source contract/plan/progress links, relevant
  implementation and tests, introducing/amending commits, and any predecessor
  or replacement. A new uncommitted decision cites its work package and
  "this commit"; do not invent a hash before the commit exists.

The two legacy namespaces and three named records above remain stable.
Do not create a third sequence for new decisions; use the progress number.

## Architecture records

| ID | Decision |
| --- | --- |
| `AD-01` | [The archive unit is a complete snapshot at one resolved commit SHA](ad-01.md) |
| `AD-02` | [The first sync preserves the latest observed revision; there is no backfill](ad-02.md) |
| `AD-03` | [Subsequent revisions are whatever each scheduled run observes](ad-03.md) |
| `AD-04` | [Retention defaults to three unique published revisions per repository](ad-04.md) |
| `AD-05` | [Retention order comes from an immutable publication generation, never from time](ad-05.md) |
| `AD-06` | [Upstream disappearance never deletes local content](ad-06.md) |
| `AD-07` | [Dependencies are detected statically and warned about, never resolved](ad-07.md) |
| `AD-08` | [Hub access is the official Python client only](ad-08.md) |
| `AD-09` | [The native Hub cache on the archive dataset is the canonical download store](ad-09.md) |
| `AD-10` | [Consumers receive an immutable ordinary-file publication tree](ad-10.md) |
| `AD-11` | [Publication hardlinks within the dataset; copy mode is explicit and never a silent fallback](ad-11.md) |
| `AD-12` | [Durable state is JSON on the filesystem; there is no database](ad-12.md) |
| `AD-13` | [Repair replaces a damaged instance without changing what the revision *is*](ad-13.md) |
| `AD-14` | [Every mutation is bounded by an atomic filesystem operation and a durable checkpoint](ad-14.md) |
| `AD-15` | [Repository content is data, never code](ad-15.md) |
| `AD-16` | [Ambiguity stops the machine; it never triggers a guess](ad-16.md) |
| `AD-17` | [One writer; locking is local](ad-17.md) |
| `AD-18` | [Ingestion verification hashes bytes; it does not trust identifiers](ad-18.md) |
| `AD-19` | [Download ahead with one bounded producer](ad-19.md) |
| `AD-20` | [Repository removal is explicit, unmanaged, and transactional](ad-20.md) |
| `AD-21` | [Restricted Hub scope is explicit and shares one consumer boundary](ad-21.md) |
| `FW-01`–`FW-04` | [Deterministic functions and a closed runtime dependency set](fw-01.md) |
| Verification policy | [Quarterly offline verification against immutable manifests](offline-verification.md) |
| Scheduling authority | [systemd owns scheduling and lifecycle](systemd-scheduling.md) |

## Numbered progress decisions

These entries retain their original chronology. Read the individual record's
status and current-contract links before applying a historical choice.

| Source decision | Record |
| --- | --- |
| 1 | [`docs/schemas.md` added beyond the plan §7 documentation set](decision-001.md) |
| 2 | [`docs/cli.md` added beyond the plan §7 documentation set](decision-002.md) |
| 3 | [Exit-code aggregation order fixed as `40`, `50`, `30`](decision-003.md) |
| 4 | [Prune removes the per-SHA reference before tombstoning the tree](decision-004.md) |
| 5 | [`sync.stale_staging_age_hours` added to the configuration schema](decision-005.md) |
| 6 | [MIT license, `uv_build` backend](decision-006.md) |
| 7 | [Python 3.14 pin confirmed; `hf-xet` is a required dependency, not an extra](decision-007.md) |
| 8 | [`scripts/` added to the project layout; no CI-provider configuration](decision-008.md) |
| 9 | [`--token-file` with `token_mode = "disabled"` is `HFARG002`, not a silent choice](decision-009.md) |
| 10 | [`HFARG006` added for a systemd credential that is present but unusable](decision-010.md) |
| 11 | [A credential file is validated, never sanitized](decision-011.md) |
| 12 | [`hub.credential_name` may not be `.` or `..`](decision-012.md) |
| 13 | [A reference's paths are relative to `published/`, every other artifact's are archive-relative](decision-013.md) |
| 14 | [The repository-relative path grammar is published](decision-014.md) |
| 15 | [Collision folding is deliberately stricter than any one filesystem](decision-015.md) |
| 16 | [Five identifier grammars accepted a trailing newline; fixed](decision-016.md) |
| 17 | [`credentials.py` and `identity.py` added to the plan §7 module list](decision-017.md) |
| 18 | [Durable files are indented; the `--json` envelope is not](decision-018.md) |
| 19 | [Reading a durable artifact takes the caller's error class *and* code](decision-019.md) |
| 20 | [§1.1's "unknown keys are preserved when rewritten" applies only to the journal](decision-020.md) |
| 21 | [A Pydantic validator must raise `ValueError`, never `TypeError`](decision-021.md) |
| 22 | [`config validate` reports `token_source`](decision-022.md) |
| 23 | [A whole-table constraint is not reported alongside a bad field in the same table](decision-023.md) |
| 24 | [A partially implemented command reports what it probed, not a placeholder](decision-024.md) |
| 25 | [The taxonomy is checked against the documents that define it, in both directions](decision-025.md) |
| 26 | [The `--json` envelope is a model, not a dict](decision-026.md) |
| 27 | [`archive init` writes the configured archive id; it does not mint one](decision-027.md) |
| 28 | [`STO-000` lands the primitives it cannot be correct without](decision-028.md) |
| 29 | [`archive init --inspect` exits `0` for an already-initialized archive](decision-029.md) |
| 30 | [A leftover `.tmp-` sibling is part of the known-empty layout contract](decision-030.md) |
| 31 | [`published/` adoption compares ownership against the archive root](decision-031.md) |
| 32 | [A write that fails after every check passed is `HFMNT008`](decision-032.md) |
| 33 | [The check runner is its own module, `preflight.py`](decision-033.md) |
| 34 | [`archive_root` reports `HFMNT015` as well as `HFMNT001`](decision-034.md) |
| 35 | [A skipped check has three meanings, and the gate reads them differently](decision-035.md) |
| 36 | [`archive.py` split out of `storage.py`](decision-036.md) |
| 37 | [The `sentinel` check owns "the archive is not initialized"](decision-037.md) |
| 38 | [`HFWRN005` fires at a tenth of the reserve](decision-038.md) |
| 39 | [`free_space` does not need an initialized archive](decision-039.md) |
| 40 | [`locking.py` added to the plan §7 module list](decision-040.md) |
| 41 | [The capability probes stay inside `.store/health/`](decision-041.md) |
| 42 | [Checkpoint evidence names paths by key suffix](decision-042.md) |
| 43 | [The recovery report is a run report](decision-043.md) |
| 44 | [`projected_publication_bytes` is measured under the configured mode, not hypothetically under copy](decision-044.md) |
| 45 | [An empty tree listing is reported; an entry with no path is refused](decision-045.md) |
| 46 | [A hashing failure's error class must match its code's family](decision-046.md) |
| 47 | [`HFSYN009` added for content that cannot be read while hashing](decision-047.md) |
| 48 | [`hfcache list` lands at `SYNC-002`](decision-048.md) |
| 49 | [A verification finding may name no publication instance, and `HFARG004` now covers a revision or a run this archive does not hold](decision-049.md) |
| 50 | [`verify --estimate` reports storage maintenance as `undetectable`](decision-050.md) |
| 51 | [`verification_state` comes from `catalog/verification.json`, and a revision nothing has re-read is `unverified`](decision-051.md) |
| 52 | [`storage.write_model` takes the caller's error class, not just its code](decision-052.md) |
| 53 | [Evidence for a path a later checkpoint moves carries no `_path` suffix](decision-053.md) |
| 54 | [`repair.py` added beyond plan §7's module list](decision-054.md) |
| 55 | [A crashed sync run journal closes; it does not stop the machine](decision-055.md) |
| 56 | [A committed publication or repair discards its staging area](decision-056.md) |
| 57 | [The `--config` and `--token-file` options do not check readability at parse time](decision-057.md) |
| 58 | [The archive mount is defined by explicit units and the fstab line is retired](decision-058.md) |
| 59 | [The hardening is tested by a probe that reads the deployed unit](decision-059.md) |
| 60 | [`IPAddressDeny=any` on the verification unit rather than `PrivateNetwork=true`](decision-060.md) |
| 61 | [`RestrictSUIDSGID=true` is the one §22.5 setting not applied](decision-061.md) |
| 62 | [The reported verification state is keyed by publication instance, not by SHA](decision-062.md) |
| 63 | [§24's host half is two shipped files, not two runbook steps](decision-063.md) |
| 64 | [The event log is emitted, not returned; and its vocabulary is closed](decision-064.md) |
| 65 | [Plan §30 step 1 would have unmounted the archive; and a rollback needs two releases](decision-065.md) |
| 66 | [A setgid directory on this mount is made by `chmod`, not by `mkdir`'s mode argument](decision-066.md) |
| 67 | [The consumer helper is `examples/copy-revision.py`, and it may not import `hfcache`](decision-067.md) |
| 68 | [A prune's container cleanup is checkpoint 10, after the commit point, and its atomic act is `rmdir`](decision-068.md) |
| 69 | [There is no `tests/integration/`; the tier lives beside its fixtures, and §26.6's map is a test rather than a comment](decision-069.md) |
| 70 | [An artifact that will not parse is not an absent artifact](decision-070.md) |
| 71 | [The release is deployed from a wheel already; it is not deployed from `dist/`, and it should not be](decision-071.md) |
| 72 | [A throwaway archive has to be a real NFS mount, so the writer exports one to itself](decision-072.md) |
| 73 | [Verification enumerates the retained set, and `current.json` is not in it](decision-073.md) |
| 74 | [The interpreter directory is part of the deployment and was outside every sweep](decision-074.md) |
| 75 | [The first release is `v0.1.2`, because that is what is deployed](decision-075.md) |
| 76 | [The rename decision 69 deferred is performed, and the index that made it safe now checks itself](decision-076.md) |
| 77 | [The docs move to the code, because the built mechanism already delivers §7.4's semantics and a failure-time checkpoint buys recovery nothing](decision-077.md) |
| 78 | [`commit_sha` widens to nullable with no schema bump, and the entry the retained-key rule cannot see gets its own clearing rule](decision-078.md) |
| 79 | [0.1.3 is tagged because it is deployed, and it is still not 1.0.0](decision-079.md) |
| 80 | [A `DOC` package family, tracked outside §28's phase set](decision-080.md) |
| 81 | [`AGENTS.md`, `CLAUDE.md`, and `docs/agents/` added beyond plan §7's layout](decision-081.md) |
| 82 | [`docs/agents/workflow.md` supersedes plan §36 for sessions after the build-out; pushing joins the loop](decision-082.md) |
| 83 | [`CHANGELOG.md` beside the annotated tags, and README `Status` stops accreting release notes](decision-083.md) |
| 84 | [Placeholders replace environment specifics, records included](decision-084.md) |
| 85 | [The storage contract becomes server-agnostic, and evaluation gets a first run](decision-085.md) |
| 86 | [Guest memory is bounded in the units, not trusted to the host](decision-086.md) |
| 87 | [A Cockpit plugin in `cockpit/`, contracted by `docs/cockpit.md`, tracked as the `CPT` family](decision-087.md) |
| 88 | [The starter kit runs under pnpm; node is a build-time toolchain, not a dependency](decision-088.md) |
| 89 | [The operation surface bends to the CLI, not the reverse](decision-089.md) |
| 90 | [`cockpit/` carries LGPL-2.1-or-later beside the repository's MIT](decision-090.md) |
| 91 | [`smol-toml` is bundled for configuration round-tripping](decision-091.md) |
| 92 | [Plugin CLI invocations run in transient units that import the deployment's encrypted Hub credential](decision-092.md) |
| 93 | [A hardlink carries same-operation content evidence only with exact object identity](decision-093.md) |
| 94 | [Queue-ahead uses one repository producer inside the existing run lock](decision-094.md) |
| 95 | [A failed report may retain warnings observed before another repository failed](decision-095.md) |
| 96 | [Whole-repository deletion is explicit, unmanaged-only, and reuses the prune commit point](decision-096.md) |
| 97 | [A completed 0.1.5 purge is operationally readable by 0.1.4; an open one is the rollback barrier](decision-097.md) |
| 98 | [Restricted Hub scope requires explicit `required` token policy and one shared consumer authorization boundary](decision-098.md) |
| 99 | [Consumer revision creation and serving promotion have separate ownership boundaries](decision-099.md) |
| 100 | [Serving consumes the verified ordinary-file tree through read-only container mounts](decision-100.md) |
| 101 | [Repository names are canonical, type-aware external links](decision-101.md) |
| 102 | [Retention defaults to three while explicit five remains compatible](decision-102.md) |
| 103 | [Only resolved, proven redundant staging quarantine may be released](decision-103.md) |
| 104 | [Confirmed operator cancellation may replace the empty-staging age heuristic](decision-104.md) |
| 105 | [Only journals supplying deletion authority need current checkpoint order](decision-105.md) |
| 106 | [Current invariants and individual ADRs accompany every implementation](decision-106.md) |
| 107 | [Active plans and task records own execution; progress retains the audit](decision-107.md) |
| 108 | [Typed services and maintained transport implementations](decision-108.md) |
| 109 | [Bounded non-resuming operation receipts](decision-109.md) |
| 110 | [Guard complete command execution and verification persistence](decision-110.md) |
| 111 | [Scope execution correlation and offline process initialization](decision-111.md) |
| 112 | [Separate server authority and verified bearer capabilities](decision-112.md) |
| 113 | [Serve bounded metadata through one authenticated lifespan](decision-113.md) |
| 114 | [Persist non-resuming admission without discarding uncertainty](decision-114.md) |
| 115 | [Execute one bounded lane and reconcile the exact verifier](decision-115.md) |
| 116 | [Admit typed command routes without widening server authority](decision-116.md) |
| 117 | [Revalidate explicit maintenance authority at execution](decision-117.md) |
| 118 | [Observe one API authority without replaying uncertain submissions](decision-118.md) |
| 119 | [Preserve server read identity and separate candidate validity from authority](decision-119.md) |
