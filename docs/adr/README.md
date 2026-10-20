# Architectural decision records

Start with the topic map below, then read only the records relevant to the
change. [The invariant register](../invariants.md) states current constraints;
[architecture](../architecture.md) and the other area contracts contain the
detailed requirements. ADRs explain the choices, alternatives, consequences,
and amendment history. A historical accepted decision is not evidence that
its original policy is still current: follow its status and amendment links.

## Identity and authority

Architecture records retain stable AD identifiers; numbered decisions retain
their separate decision identity, original dates and commit provenance. These
namespaces describe different records and are never renumbered or reused.
Contracts state current requirements; accepted ADRs explain rationale,
alternatives, consequences and subsequent amendments. Follow current status and
amendment links when a historical policy has changed. Source/test/commit links
provide technical evidence, not a claim of installed-host acceptance.

## Topic map

| Area | Start here | Related implementation decisions |
| --- | --- | --- |
| Complete snapshots and observations | [AD-01 — Archive complete snapshots at resolved immutable commits](ad-01.md), [AD-02 — Begin with the latest observed revision without backfill](ad-02.md), [AD-03 — Retain revisions observed by scheduled runs](ad-03.md) | [The repository-relative path grammar is published](decision-014.md), [Collision folding is deliberately stricter than any one filesystem](decision-015.md) |
| Storage, publication, and hashing | [AD-09 — Keep the canonical Hub download cache on the archive dataset](ad-09.md), [AD-10 — Publish immutable ordinary-file trees for consumers](ad-10.md), [AD-11 — Use hardlink publication by default and require explicit copy mode](ad-11.md), [AD-18 — Prove archived bytes by local SHA-256 and exact object identity](ad-18.md) | [A reference's paths are relative to `published/`, every other artifact's are archive-relative](decision-013.md), [A hardlink carries same-operation content evidence only with exact object identity](decision-093.md) |
| Retention, repair, and deletion | [AD-04 — Bound retention to three revisions by default and preserve explicit five](ad-04.md), [AD-05 — Order retention by immutable publication generation](ad-05.md), [AD-06 — Preserve local content when upstream or configuration changes](ad-06.md), [AD-13 — Repair an instance without redefining the revision](ad-13.md), [AD-20 — Remove whole repositories only through explicit unmanaged purge](ad-20.md) | [The docs move to the code, because the built mechanism already delivers §7.4's semantics and a failure-time checkpoint buys recovery nothing](decision-077.md), [Whole-repository deletion is explicit, unmanaged-only, and reuses the prune commit point](decision-096.md), [Retention defaults to three while explicit five remains compatible](decision-102.md), [Revalidate explicit maintenance authority at execution](decision-117.md) |
| Recovery and quarantine | [AD-12 — Keep durable authority in versioned filesystem JSON](ad-12.md), [AD-14 — Bound mutations by durable checkpoints and atomic filesystem acts](ad-14.md), [AD-16 — Preserve ambiguity and stop instead of guessing](ad-16.md), [AD-17 — Use one writer host and one local exclusive lock](ad-17.md) | [Preserve unknown journal fields while rejecting unknown model keys](decision-020.md), [Only resolved, proven redundant staging quarantine may be released](decision-103.md), [Confirmed operator cancellation may replace the empty-staging age heuristic](decision-104.md), [Only journals supplying deletion authority need current checkpoint order](decision-105.md), [Separate command execution from resumable CLI observation](decision-120.md) |
| Hub access, credentials, and dependencies | [AD-07 — Detect dependencies statically and never fetch them implicitly](ad-07.md), [AD-08 — Reach the Hub through the official injectable Python adapter](ad-08.md), [AD-15 — Treat repository content as untrusted data](ad-15.md), [AD-21 — Require explicit restricted Hub scope and one consumer authorization boundary](ad-21.md) | [A credential file is validated, never sanitized](decision-011.md), [Restricted Hub scope requires explicit `required` token policy and one shared consumer authorization boundary](decision-098.md), [Separate server authority and verified bearer capabilities](decision-112.md), [Admit typed command routes without widening server authority](decision-116.md), [Preserve server read identity and separate candidate validity from authority](decision-119.md), [Add an optional authenticated MCP transport after REST acceptance](decision-124.md), [Expose nine typed metadata tools through a narrow read capability](decision-125.md) |
| Sync throughput and capacity | [AD-19 — Overlap downloads with hashing through one bounded producer](ad-19.md) | [Guest memory is bounded in the units, not trusted to the host](decision-086.md), [Queue-ahead uses one repository producer inside the existing run lock](decision-094.md), [A failed report may retain warnings observed before another repository failed](decision-095.md), [Scope execution correlation and offline process initialization](decision-111.md) |
| Verification and durable reporting | [Quarterly full verification reads the retained archive offline](offline-verification.md) | [Separate ingestion hashing from published-instance confidence](decision-051.md), [The reported verification state is keyed by publication instance, not by SHA](decision-062.md), [Verification enumerates the retained set, and `current.json` is not in it](decision-073.md), [`commit_sha` widens to nullable with no schema bump, and the entry the retained-key rule cannot see gets its own clearing rule](decision-078.md), [Guard complete command execution and verification persistence](decision-110.md), [Scope execution correlation and offline process initialization](decision-111.md), [Execute one bounded lane and reconcile the exact verifier](decision-115.md), [Create the rootless verifier listener inside its confinement](decision-128.md) |
| Deployment, scheduling, and hardening | [Keep host scheduling in systemd timers and drop-ins](systemd-scheduling.md) | [The archive mount is defined by explicit units and the fstab line is retired](decision-058.md), [The hardening is tested by a probe that reads the deployed unit](decision-059.md), [`IPAddressDeny=any` on the verification unit rather than `PrivateNetwork=true`](decision-060.md), [Preserve required setgid directories with compensating privilege controls](decision-061.md), [Quiesce executors without unmounting the archive](decision-065.md), [Activate one server and retain scheduled observation without replay](decision-121.md), [Guard a local rollout without NAS writes or false acceptance](decision-126.md), [Run reviewed rootless containers without forced executor cleanup](decision-127.md), [Create the rootless verifier listener inside its confinement](decision-128.md) |
| Consumers and serving | [AD-10 — Publish immutable ordinary-file trees for consumers](ad-10.md) | [Keep consumer verification independent of the writer runtime](decision-067.md), [Consumer revision creation and serving promotion have separate ownership boundaries](decision-099.md), [Serving consumes the verified ordinary-file tree through read-only container mounts](decision-100.md), [Keep public prefixes separate from native Unix REST paths](decision-123.md), [Add an optional authenticated MCP transport after REST acceptance](decision-124.md), [Expose nine typed metadata tools through a narrow read capability](decision-125.md) |
| Cockpit administration | [Keep the Cockpit plugin and its technical contract in the application repository](decision-087.md) | [The operation surface bends to the CLI, not the reverse](decision-089.md), [`smol-toml` is bundled for configuration round-tripping](decision-091.md), [Plugin CLI invocations run in transient units that import the deployment's encrypted Hub credential](decision-092.md), [Repository names are canonical, type-aware external links](decision-101.md), [Preserve server read identity and separate candidate validity from authority](decision-119.md), [Preserve Cockpit authority through the API client and guarded candidates](decision-122.md), [Preserve Cockpit failure evidence and original operation identity](decision-134.md) |
| Framework, dependencies, and development | [FW-01 — Keep deterministic functions and a closed runtime dependency set](fw-01.md) | [Typed services and maintained transport implementations](decision-108.md), [Bounded non-resuming operation receipts](decision-109.md), [Scope execution correlation and offline process initialization](decision-111.md), [Add an optional authenticated MCP transport after REST acceptance](decision-124.md), [Separate server authority and verified bearer capabilities](decision-112.md), [Serve bounded metadata through one authenticated lifespan](decision-113.md), [Persist non-resuming admission without discarding uncertainty](decision-114.md), [Execute one bounded lane and reconcile the exact verifier](decision-115.md), [Admit typed command routes without widening server authority](decision-116.md), [Revalidate explicit maintenance authority at execution](decision-117.md), [Observe one API authority without replaying uncertain submissions](decision-118.md), [Preserve server read identity and separate candidate validity from authority](decision-119.md), [Separate command execution from resumable CLI observation](decision-120.md), [Activate one server and retain scheduled observation without replay](decision-121.md), [Python 3.14 pin confirmed; `hf-xet` is a required dependency, not an extra](decision-007.md), [Use one provider-neutral executable quality gate](decision-008.md), [Keep the Cockpit build toolchain separate from application runtime](decision-088.md) |

| Local discovery and supplemental metadata | [Separate curation from publication authority](decision-133.md) | [AD-12](ad-12.md), [AD-14](ad-14.md), [AD-17](ad-17.md), [Candidate identity](decision-119.md), [Cockpit guards](decision-122.md), [MCP read capability](decision-125.md) |

## Architecture records

| ID | Decision |
| --- | --- |
| `AD-01` | [AD-01 — Archive complete snapshots at resolved immutable commits](ad-01.md) |
| `AD-02` | [AD-02 — Begin with the latest observed revision without backfill](ad-02.md) |
| `AD-03` | [AD-03 — Retain revisions observed by scheduled runs](ad-03.md) |
| `AD-04` | [AD-04 — Bound retention to three revisions by default and preserve explicit five](ad-04.md) |
| `AD-05` | [AD-05 — Order retention by immutable publication generation](ad-05.md) |
| `AD-06` | [AD-06 — Preserve local content when upstream or configuration changes](ad-06.md) |
| `AD-07` | [AD-07 — Detect dependencies statically and never fetch them implicitly](ad-07.md) |
| `AD-08` | [AD-08 — Reach the Hub through the official injectable Python adapter](ad-08.md) |
| `AD-09` | [AD-09 — Keep the canonical Hub download cache on the archive dataset](ad-09.md) |
| `AD-10` | [AD-10 — Publish immutable ordinary-file trees for consumers](ad-10.md) |
| `AD-11` | [AD-11 — Use hardlink publication by default and require explicit copy mode](ad-11.md) |
| `AD-12` | [AD-12 — Keep durable authority in versioned filesystem JSON](ad-12.md) |
| `AD-13` | [AD-13 — Repair an instance without redefining the revision](ad-13.md) |
| `AD-14` | [AD-14 — Bound mutations by durable checkpoints and atomic filesystem acts](ad-14.md) |
| `AD-15` | [AD-15 — Treat repository content as untrusted data](ad-15.md) |
| `AD-16` | [AD-16 — Preserve ambiguity and stop instead of guessing](ad-16.md) |
| `AD-17` | [AD-17 — Use one writer host and one local exclusive lock](ad-17.md) |
| `AD-18` | [AD-18 — Prove archived bytes by local SHA-256 and exact object identity](ad-18.md) |
| `AD-19` | [AD-19 — Overlap downloads with hashing through one bounded producer](ad-19.md) |
| `AD-20` | [AD-20 — Remove whole repositories only through explicit unmanaged purge](ad-20.md) |
| `AD-21` | [AD-21 — Require explicit restricted Hub scope and one consumer authorization boundary](ad-21.md) |
| `FW-01`–`FW-04` | [FW-01 — Keep deterministic functions and a closed runtime dependency set](fw-01.md) |
| Verification policy | [Quarterly full verification reads the retained archive offline](offline-verification.md) |
| Scheduling authority | [Keep host scheduling in systemd timers and drop-ins](systemd-scheduling.md) |

## Numbered progress decisions

These entries retain their original chronology. Read the individual record's
status and current-contract links before applying a historical choice.

| Source decision | Record |
| --- | --- |
| 1 | [Separate durable schemas from operator configuration](decision-001.md) |
| 2 | [Keep the CLI reference separate from operational workflows](decision-002.md) |
| 3 | [Exit-code aggregation order fixed as `40`, `50`, `30`](decision-003.md) |
| 4 | [Remove prune references before tombstoning content](decision-004.md) |
| 5 | [Delay stale-staging recovery under explicit ownership proof](decision-005.md) |
| 6 | [MIT license, `uv_build` backend](decision-006.md) |
| 7 | [Python 3.14 pin confirmed; `hf-xet` is a required dependency, not an extra](decision-007.md) |
| 8 | [Use one provider-neutral executable quality gate](decision-008.md) |
| 9 | [`--token-file` with `token_mode = "disabled"` is `HFARG002`, not a silent choice](decision-009.md) |
| 10 | [Reject a present but unusable systemd credential](decision-010.md) |
| 11 | [A credential file is validated, never sanitized](decision-011.md) |
| 12 | [`hub.credential_name` may not be `.` or `..`](decision-012.md) |
| 13 | [A reference's paths are relative to `published/`, every other artifact's are archive-relative](decision-013.md) |
| 14 | [The repository-relative path grammar is published](decision-014.md) |
| 15 | [Collision folding is deliberately stricter than any one filesystem](decision-015.md) |
| 16 | [Five identifier grammars accepted a trailing newline; fixed](decision-016.md) |
| 17 | [Validate identifiers before constructing archive paths](decision-017.md) |
| 18 | [Durable files are indented; the `--json` envelope is not](decision-018.md) |
| 19 | [Reading a durable artifact takes the caller's error class *and* code](decision-019.md) |
| 20 | [Preserve unknown journal fields while rejecting unknown model keys](decision-020.md) |
| 21 | [A Pydantic validator must raise `ValueError`, never `TypeError`](decision-021.md) |
| 22 | [`config validate` reports `token_source`](decision-022.md) |
| 23 | [A whole-table constraint is not reported alongside a bad field in the same table](decision-023.md) |
| 24 | [Report established checks without inventing capability](decision-024.md) |
| 25 | [The taxonomy is checked against the documents that define it, in both directions](decision-025.md) |
| 26 | [The `--json` envelope is a model, not a dict](decision-026.md) |
| 27 | [`archive init` writes the configured archive id; it does not mint one](decision-027.md) |
| 28 | [Guarded initialization requires storage and atomic-write proof](decision-028.md) |
| 29 | [`archive init --inspect` exits `0` for an already-initialized archive](decision-029.md) |
| 30 | [A leftover `.tmp-` sibling is part of the known-empty layout contract](decision-030.md) |
| 31 | [`published/` adoption compares ownership against the archive root](decision-031.md) |
| 32 | [A write that fails after every check passed is `HFMNT008`](decision-032.md) |
| 33 | [Share diagnostic ordering and mutation preflight](decision-033.md) |
| 34 | [`archive_root` reports `HFMNT015` as well as `HFMNT001`](decision-034.md) |
| 35 | [A skipped check has three meanings, and the gate reads them differently](decision-035.md) |
| 36 | [Separate archive initialization from storage primitives](decision-036.md) |
| 37 | [The `sentinel` check owns "the archive is not initialized"](decision-037.md) |
| 38 | [`HFWRN005` fires at a tenth of the reserve](decision-038.md) |
| 39 | [`free_space` does not need an initialized archive](decision-039.md) |
| 40 | [Keep local lock lifetime separate from storage checks](decision-040.md) |
| 41 | [The capability probes stay inside `.store/health/`](decision-041.md) |
| 42 | [Checkpoint evidence names paths by key suffix](decision-042.md) |
| 43 | [The recovery report is a run report](decision-043.md) |
| 44 | [`projected_publication_bytes` is measured under the configured mode, not hypothetically under copy](decision-044.md) |
| 45 | [An empty tree listing is reported; an entry with no path is refused](decision-045.md) |
| 46 | [A hashing failure's error class must match its code's family](decision-046.md) |
| 47 | [Classify content that cannot be read while hashing](decision-047.md) |
| 48 | [Read inventory from authoritative references and manifests](decision-048.md) |
| 49 | [A verification finding may name no publication instance, and `HFARG004` now covers a revision or a run this archive does not hold](decision-049.md) |
| 50 | [`verify --estimate` reports storage maintenance as `undetectable`](decision-050.md) |
| 51 | [Separate ingestion hashing from published-instance confidence](decision-051.md) |
| 52 | [`storage.write_model` takes the caller's error class, not just its code](decision-052.md) |
| 53 | [Evidence for a path a later checkpoint moves carries no `_path` suffix](decision-053.md) |
| 54 | [Keep instance repair separate from retention deletion](decision-054.md) |
| 55 | [A crashed sync run journal closes; it does not stop the machine](decision-055.md) |
| 56 | [A committed publication or repair discards its staging area](decision-056.md) |
| 57 | [The `--config` and `--token-file` options do not check readability at parse time](decision-057.md) |
| 58 | [The archive mount is defined by explicit units and the fstab line is retired](decision-058.md) |
| 59 | [The hardening is tested by a probe that reads the deployed unit](decision-059.md) |
| 60 | [`IPAddressDeny=any` on the verification unit rather than `PrivateNetwork=true`](decision-060.md) |
| 61 | [Preserve required setgid directories with compensating privilege controls](decision-061.md) |
| 62 | [The reported verification state is keyed by publication instance, not by SHA](decision-062.md) |
| 63 | [Ship bounded persistent journald settings and an optional read-only failure hook](decision-063.md) |
| 64 | [The event log is emitted, not returned; and its vocabulary is closed](decision-064.md) |
| 65 | [Quiesce executors without unmounting the archive](decision-065.md) |
| 66 | [A setgid directory on this mount is made by `chmod`, not by `mkdir`'s mode argument](decision-066.md) |
| 67 | [Keep consumer verification independent of the writer runtime](decision-067.md) |
| 68 | [A prune's container cleanup is checkpoint 10, after the commit point, and its atomic act is `rmdir`](decision-068.md) |
| 69 | [Organize integration coverage with its shared fixtures](decision-069.md) |
| 70 | [An artifact that will not parse is not an absent artifact](decision-070.md) |
| 71 | [Install native wheels from the locked staged source tree](decision-071.md) |
| 72 | [A throwaway archive has to be a real NFS mount, so the writer exports one to itself](decision-072.md) |
| 73 | [Verification enumerates the retained set, and `current.json` is not in it](decision-073.md) |
| 74 | [The interpreter directory is part of the deployment and was outside every sweep](decision-074.md) |
| 75 | [Tag the deployed tested artifact with proportionate release scope](decision-075.md) |
| 76 | [Name crash-injection tests clearly and verify the coverage index](decision-076.md) |
| 77 | [The docs move to the code, because the built mechanism already delivers §7.4's semantics and a failure-time checkpoint buys recovery nothing](decision-077.md) |
| 78 | [`commit_sha` widens to nullable with no schema bump, and the entry the retained-key rule cannot see gets its own clearing rule](decision-078.md) |
| 79 | [Keep a narrow release around a durable compatibility change](decision-079.md) |
| 83 | [`CHANGELOG.md` beside the annotated tags, and README `Status` stops accreting release notes](decision-083.md) |
| 84 | [Placeholders replace environment specifics, records included](decision-084.md) |
| 85 | [Keep storage requirements portable without weakening NFS safety](decision-085.md) |
| 86 | [Guest memory is bounded in the units, not trusted to the host](decision-086.md) |
| 87 | [Keep the Cockpit plugin and its technical contract in the application repository](decision-087.md) |
| 88 | [Keep the Cockpit build toolchain separate from application runtime](decision-088.md) |
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
| 119 | [Preserve server read identity and separate candidate validity from authority](decision-119.md), [empty Unix writes amendment](decision-119.md#empty-unix-writes-amendment-2026-10-20) |
| 120 | [Separate command execution from resumable CLI observation](decision-120.md) |
| 121 | [Activate one server and retain scheduled observation without replay](decision-121.md) |
| 122 | [Preserve Cockpit authority through the API client and guarded candidates](decision-122.md), [Preserve Cockpit failure evidence and original operation identity](decision-134.md) |
| 123 | [Keep public prefixes separate from native Unix REST paths](decision-123.md) |
| 124 | [Add an optional authenticated MCP transport after REST acceptance](decision-124.md) |
| 125 | [Expose nine typed metadata tools through a narrow read capability](decision-125.md) |
| 126 | [Guard a local rollout without NAS writes or false acceptance](decision-126.md) |
| 127 | [Run reviewed rootless containers without forced executor cleanup](decision-127.md) |
| 128 | [Create the rootless verifier listener inside its confinement](decision-128.md) |
| 129 | [Build all service image stages on pinned UBI 10 micro](decision-129.md) |
| 131 | [Explicit disposable probes and qualified isolation evidence](decision-131.md) |
| 132 | [Positively classify native releases before effects](decision-132.md) |
| 133 | [Separate curation from publication authority](decision-133.md) |
| 134 | [Preserve Cockpit failure evidence and original operation identity](decision-134.md) |
| 135 | [Separate manual REST jobs from guarded host observers](decision-135.md) |
