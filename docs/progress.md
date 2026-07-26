# Implementation Progress

Authoritative work-package tracker for `docs/plan.md` §28, maintained under the
§36 Autonomous Implementation Protocol. Update this file **in the same commit**
as the work it records: mark the box, append `(YYYY-MM-DD, <short commit ref or
"this commit">)`.

Statuses: `[ ]` pending · `[x]` complete · `[b]` blocked (explain under
Operator handoff or Operator decisions needed).

Session startup: read `docs/plan.md` in full, then this file, then
`git log --oneline -20`; re-run the §8.4 quality gates if source exists;
continue at the first unchecked item in phase order.

## Phase 0 — Contract and Architecture

- [x] ARC-001 Record architecture decisions and non-goals (2026-07-24, this commit — `docs/architecture.md` §1–4: `AD-01`–`AD-18`, `NG-01`–`NG-12`)
- [x] ARC-002 Define filesystem layout and invariants (2026-07-24, this commit — `docs/architecture.md` §5–6: layout, ownership/modes, path grammar, `FS-01`–`FS-23`)
- [x] ARC-003 Define configuration schema version 1 (2026-07-24, this commit — `docs/configuration.md`: every key typed and constrained, credential resolution, `HFCFG001`–`HFCFG016`, config fingerprint)
- [x] ARC-004 Define manifest, catalog, run-report, and verification schemas (2026-07-24, this commit — `docs/schemas.md`: sentinel, manifest, refs, catalog, run report, verification report, prune plan, audit records, transaction journal)
- [x] ARC-005 Define CLI commands, JSON output, and exit codes (2026-07-24, this commit — `docs/cli.md`: every command and option, selector grammar, JSON envelope, exit-code aggregation, `HFARG`/`HFMNT`/`HFTXN`/`HFHUB`/`HFSYN`/`HFVER`/`HFRET`/`HFWRN` taxonomy)
- [x] ARC-006 Define transaction and crash-recovery boundaries (2026-07-24, this commit — `docs/architecture.md` §7: `TX-01`–`TX-07`, named checkpoints and crash matrices for publication/prune/repair/sync/recovery, prune commit point, `needs_operator` conditions)
- [x] ARC-007 Define security and threat assumptions (2026-07-24, this commit — `docs/security.md`: assets, trust boundaries, threats `T-01`–`T-12` with controls, hardening posture, explicit out-of-scope list, verification tests)
- [x] ARC-008 Enforce the framework boundary (no workflow engine in v1) (2026-07-24, this commit — `docs/architecture.md` §8 `FW-01`–`FW-04`, plus §9 Phase 0 acceptance)

**Phase 0 complete.** Contracts: `docs/architecture.md`, `docs/configuration.md`,
`docs/schemas.md`, `docs/cli.md`, `docs/security.md`. Acceptance evidence in
`docs/architecture.md` §9.

## Phase 1 — Project Bootstrap and Quality Gates

- [x] BOOT-001 Initialize uv project and `src/` layout (includes `git init` + initial docs commit per §36.2) (2026-07-24, this commit — `pyproject.toml`, `src/hfcache/`, `tests/{unit,integration,system,fixtures}`, `examples/`, `packaging/systemd/`, `README.md`, `LICENSE`, `.editorconfig`; git baseline commit `87323c2`)
- [x] BOOT-002 Pin Python and create `uv.lock` (2026-07-24, this commit — CPython 3.14.6 validated against the full locked set; `huggingface-hub` 1.24.0, `hf-xet` 1.5.2, `pydantic` 2.13.4, `typer` 0.27.0)
- [x] BOOT-003 Configure Ruff formatting and linting (2026-07-24, this commit — 37 rule families incl. `DTZ`, `S`, `PTH`, `TRY`, `FBT`, `SLF`; relative imports banned; `assert` flagged in `src/`)
- [x] BOOT-004 Configure Pyrefly (2026-07-24, this commit — `src` + `tests` checked, Python 3.14, non-permissive ignores; Ruff `ANN` added since pyrefly infers rather than requires annotations)
- [x] BOOT-005 Configure pytest and coverage (2026-07-24, this commit — strict markers/config, `live`/`nfs` opt-in markers deselected by default, warnings-as-errors, branch coverage; autouse fixture strips ambient Hub state from every test)
- [x] BOOT-006 Add Typer entry point and version command (2026-07-24, this commit — `src/hfcache/cli.py`, `errors.py` `ExitCode`, `__main__.py`, console script; `--json` envelope emitted and asserted against the `docs/cli.md` §4 contract)
- [x] BOOT-007 Add provider-neutral quality scripts and build smoke test (2026-07-24, this commit — `scripts/check.sh` runs the §8.4 gate; `tests/system/test_wheel_smoke.py` installs the wheel into a clean venv, marker `build`)

**Phase 1 complete.** `scripts/check.sh --with-build` passes from a clean
checkout: lock check, format, lint, pyrefly, pytest, `uv build`, and the wheel
install smoke test.

## Phase 2 — Configuration, Models, and Read-only CLI

- [x] CFG-001 Strict Pydantic configuration models (2026-07-24, this commit — `src/hfcache/config.py`, `errors.py` `Problem`/`HfcacheError`; all 16 `HFCFG###` codes implemented and each provoked by a test)
- [x] CFG-002 Token-source abstraction without literal secrets (2026-07-24, this commit — `src/hfcache/credentials.py`: §7 resolution order, `HFARG002`/`HFARG005`/`HFARG006`, `hub_argument` returns `False` and never `None`, redaction proven over generated tokens; no function in the module accepts a token value. The `--token-file` option is parsed by the CLI as of `BOOT-006`; it is *resolved* by the first command that loads configuration, which is `CFG-005`)
- [x] CFG-003 Repository identity and safe path mapping (2026-07-25, this commit — `src/hfcache/identity.py`: every Hub-facing grammar, `RepositoryIdentity` self-validating, `TYPE:ID[@SHA]` selectors, opaque-id minting; `src/hfcache/paths.py`: the whole §5.1 tree, relative-path grammar, containment, collision folding. Both at 100% branch coverage. `config.py` now imports its identifier grammars rather than defining them)
- [x] CFG-004 Manifest and report models (2026-07-25, this commit — `src/hfcache/models.py` (foundation, sentinel, reference, prune plan, audit records, journal), `manifests.py` (`RevisionManifest`), `reporting.py` (run report, verification report, catalog). One serializer for every writer including the CLI envelope; §1.1 version refusal; a golden fixture per format in `tests/fixtures/schemas/`. All three modules at 100% branch coverage)
- [x] CFG-005 `config validate` (2026-07-25, this commit — `config` sub-app in `src/hfcache/cli.py`; loads configuration and resolves the credential, takes no lock and makes no network call; failure envelope emitted with every problem, exit `10`; `--token-file` is now resolved as `CFG-002` said it would be here)
- [x] CFG-006 Read-only portions of `doctor`, `status`, and `plan` (2026-07-25, this commit — selector resolution with `HFARG001`/`HFARG004`; `doctor` check-runner with `configuration`, `credential`, `hub_endpoint`, and `--read-only`'s three explicit unproven capabilities; `plan` over enabled repositories in configuration order; `status` reporting local truth with `upstream_state: unknown`. **Still to come:** `doctor`'s storage probes at `STO-009` and its Hub reachability/identity checks at `HUB-001`/`HUB-002`; `plan`'s resolved SHA and size estimates at `HUB-003`/`HUB-004`; `status`'s retained-revision and health blocks at `STO-008`/`VER-005`)
- [x] CFG-007 Deterministic JSON output and error taxonomy (2026-07-25, this commit — `src/hfcache/taxonomy.py`: every family's exit classification and the §3 aggregation rule; `Envelope`/`EnvelopeProblem` in `reporting.py` so the `--json` contract is a model rather than a dict built per call site. `tests/unit/test_taxonomy.py` parses the code tables out of `docs/cli.md` §5 and `docs/configuration.md` §8 and checks both directions, so the taxonomy cannot drift from the documents that define it)

**Phase 2 complete.** Every operator input is validated before any network or
filesystem access: configuration, credentials, repository identity, path safety,
durable schemas, and the read-only command surface. `scripts/check.sh` passes
with 566 tests; every Phase 2 module is at 100% branch coverage except `cli.py`
at 99% and `config.py` at 89%, whose gaps are the non-string type guards that
predate `CFG-003`.

## Phase 3 — Storage Safety and Publication Primitives

- [x] STO-000 Guarded one-time archive initialization and inspection (2026-07-25, this commit — `src/hfcache/storage.py`: mount-table proof, durable byte writes, the known-empty-layout walk, and `initialize_archive`; `archive` sub-app in `src/hfcache/cli.py` with `init`, `--inspect`, `--confirm`, and `--archive-id`. The §6.2 empty-`published/` adoption is implemented with ownership compared against the archive root, per decision 31. 100% branch coverage. **Not yet run against `/srv/hfcache`:** the §36.4 one-time authorization is spent at the rollout checkpoint after `HOST-004`, not here)
- [x] STO-001 NFS mount and filesystem-type detection (2026-07-25, this commit — the detection itself landed at `STO-000` (decision 28); this is the shared preflight built on it. `src/hfcache/storage.py`: the `.store/health/probe-<probe-id>` create/fsync/rename/delete probe (`HFMNT008`, plan §19 items 6 and 10) which removes every artifact it made including after a failure, and the staging/destination same-filesystem proof (`HFMNT009`, `FS-04`). `src/hfcache/preflight.py` (new, decision 33): the ordered check runner `doctor` and every mutating command share, plus `require_storage_safety`, the hard gate that raises with every problem at once. `doctor` now emits `docs/cli.md` §2 rows 2–5, 7, and 8 in table order with `credential` and `hub_endpoint` at 13 and 14, skips the probe under `--read-only`, and exits `20` when any check failed. `storage.py` and `preflight.py` both at 100% branch coverage; `tests/system/test_live_mount.py` proves rows 2–5 against the live `/srv/hfcache` mount read-only, `-m nfs`)
- [x] STO-002 Sentinel/archive-ID validation (2026-07-25, this commit — `src/hfcache/archive.py` split out of `storage.py` first, per the `STO-001` sizing note and decision 36; `storage.read_sentinel` is now shared by both. `doctor` check 6 `sentinel` reports `HFMNT005` when the archive is not initialized, `HFMNT006` when the sentinel is unreadable, malformed, or from a newer release, and `HFMNT007` when it names a different archive (`FS-03`). The check owns the "not initialized" condition for the gate, so checks 7 and 8 skip on it without reporting it again — one missing archive is one problem. `storage_checks` and `require_storage_safety` now take the configured `archive_id`. `archive.py`, `preflight.py`, and `storage.py` all at 100% branch coverage)
- [x] STO-003 Free-space and reserve calculations (2026-07-25, this commit — `storage.describe_capacity` measures the filesystem through `statvfs`, which reports the ZFS quota as the size when one is set and so answers `docs/configuration.md` §4's "quota, or capacity" without the writer knowing which case it is in; `effective_reserve` is whichever configured minimum binds harder; `capacity_problems` is `HFMNT011` against the need *plus* the reserve (plan §19 item 9) and `capacity_warnings` is `HFWRN005` at a tenth of the reserve (decision 38). `doctor` check 12 `free_space` runs against any proven mount rather than only an initialized archive (decision 39), and the warning reaches the envelope's `warnings` array with the exit code still `0`. `storage_checks` and `require_storage_safety` now take the whole `[storage]` table plus this run's `needed_bytes`. 100% branch coverage)
- [x] STO-004 Local exclusive locking (2026-07-25, this commit — `src/hfcache/locking.py` (new, decision 40): `flock(2)` on `/run/hfcache/hfcache.lock`, so the kernel releases it when the process dies and a crashed sync never leaves a lock an operator has to clear. `HFMNT010` on timeout, naming the holder from a diagnostic record the holder writes into the file. `preflight.guarded` composes the lock and the checks in plan §13.1's order — lock at step 2, preflight at step 3 — and is the single entry point every mutating command will use. 100% branch coverage; contention is exercised in-process, since `flock` conflicts between open file descriptions rather than between processes)
- [x] STO-005 Atomic JSON and ref writes (2026-07-25, this commit — `storage.write_model` and `storage.read_model`: model-aware durable JSON on top of `atomic_write_bytes` and `models.load`, each taking the caller's code so a failed manifest write is `HFSYN008` and a failed reference write `HFSYN007`. `src/hfcache/publication.py` (plan §7, no deviation) holds the reference writers: `publish_revision_reference` (`FS-11`) and `publish_current_reference` (`FS-08`), both enforcing `FS-10` at the point of the write — a reference whose tree or manifest is not durable is refused, with every missing target reported at once. `read_reference` reports `HFVER008`, because reading one happens while something is being checked. 100% branch coverage. **Still to come at `STO-007`:** the hardlink and copy publication primitives that create the tree a reference names)
- [x] STO-006 Staging creation and containment (2026-07-25, this commit — added to `publication.py`, which now has two halves: building a tree and naming it. `create_staging` makes `.store/staging/<transaction-id>/tree` exclusively — a colliding id fails rather than building into another transaction's area — with the `tree/` at the *published* mode, since publication is a rename and a rename does not change a mode. `discard_staging` is the module's one deletion and stays inside `FS-19` because the path is derived from a validated transaction id rather than read off the filesystem (`FS-18`). `source_problems` is `FS-15`: symlinks are resolved rather than refused, because the Hub cache reaches every file through one, and what is rejected is a link that escapes the approved cache root, dangles, or lands on something that is not a regular file (`HFSYN004`). `staged_path` joins a repository-relative path only after the grammar has proven it cannot escape (T-02). 100% branch coverage)
- [x] STO-007 Hardlink and copy publication primitives (2026-07-25, this commit — `src/hfcache/hashing.py` (plan §7): `sha256_file` streams a file and returns digest *and* size from one read, so the two can never describe different content. `publication.stage_file` proves the source contained (`FS-15`) then links or copies per `publication_mode`, never downgrading a mode automatically (`AD-11`); copy mode verifies the copy against a fresh hash of the source, because a copy that lost bytes would otherwise be published as the revision. `promote_staging` is plan §13.2 step 15, and refuses an existing destination *explicitly* rather than relying on `rename(2)` — which fails on a non-empty directory but replaces an empty one, so the syscall alone would break `FS-05` for an instance directory a crash left empty. `storage` gained the three §14.2 capability probes and `doctor` checks 9-11 (`HFMNT012`, `HFMNT013`), with `publication_mode = "copy"` reporting the hardlink check as not exercised rather than failed (decision 41). 100% branch coverage)
- [x] STO-008 Storage reconciliation and stale-staging reporting (2026-07-25, this commit — `src/hfcache/recovery.py` (plan §7): `reconcile_storage` scans the four transaction areas and reports what they hold without touching any of it. `HFWRN004` for staging past `sync.stale_staging_age_hours`, `HFWRN002` for a prune tombstone whose physical removal is outstanding, `HFWRN003` for an entry whose name is not a 32-hex transaction id — preserved, whatever it is (`FS-19`). Quarantine is reported and never warned about, because plan §16.5 retains it until an operator approves cleanup, so age says nothing about it. `measure_health` adds free space against the reserve, and `status` now emits the archive health block `docs/cli.md` §2 describes, with warnings on stderr and the exit code still `0`. 100% branch coverage. **Reclamation is deliberately absent:** plan §13.3 and `FS-18` allow it only for a directory that also *has a journal*, which arrives at `STO-010`, so `STO-011` is where removing one belongs)
- [x] STO-009 Complete mutating `doctor` tests (2026-07-25, this commit — the checks themselves landed at `STO-001`, `STO-002`, `STO-003`, and `STO-007`, each with its own unit coverage against a temporary archive and a fabricated mount table. What this package adds is `tests/system/test_live_mount.py`'s mutating half: sentinel, effective writability, and all three §14.2 publication capabilities asserted against the real NFS dataset, plus the probe area left empty. They are written now and **skip until the archive is initialized**, which is the §29 rollout checkpoint after `HOST-004` — so the checkpoint runs a test that already exists rather than one written to fit whatever it found. Run with `pytest -m nfs`)
- [x] STO-010 Durable transaction journals and validated checkpoint evidence (2026-07-25, this commit — `src/hfcache/transactions.py` (plan §7): `open_transaction` writes the journal durably before the first mutation (`TX-01`); `Transaction.checkpoint` appends after the act it names (`TX-02`) and refuses a name that is not next in the operation's documented sequence (`HFTXN002`). `CHECKPOINTS` holds the §7.3-§7.6 sequences and `tests/unit/test_transactions.py` parses them back out of `docs/architecture.md`, so neither table is written twice. `evidence_problems` confirms path evidence against the filesystem (`TX-03`, `HFTXN003`) under the key convention in decision 42. `read_journal` preserves keys this release does not know, which is the half of `docs/schemas.md` §1.1 that decision 20 assigned here. `open_journals` is what `TX-07` reconciles, and treats `needs_operator` as unresolved because it is exactly what must stop the next run. 100% branch coverage)
- [x] STO-011 Dry-run and apply recovery planning (2026-07-25, this commit — `recovery.plan_recovery` validates every open journal (schema, then checkpoint order, then evidence) and proposes one of four remedies; `apply_recovery` performs only a plan with nothing blocked, records one checkpoint per remediation in a §7.7 recovery journal, and writes the durable report now documented as `docs/schemas.md` §12 (decision 43). The `recover` command takes `--dry-run` or `--apply`, and `--apply` takes the lock and runs the §19 preflight because it is a mutating command. Idempotent by construction: each remedy closes the journal it resolved, so a second run finds nothing. 100% branch coverage. **The remedies for states this codebase cannot yet produce are reported as blocked rather than guessed at** — rolling a publication forward from checkpoint 5 needs `HUB-009`'s manifests, a prune needs `RET-006`, a repair needs `VER-006`; each package adds its own remedy as it lands, the way `doctor`'s checks did)

**Phase 3 complete.** Unsafe storage mutation is now structurally hard rather
than merely avoided: the mount is proven before anything is written, the sentinel
is the archive's identity, effective writability and all three publication
capabilities are demonstrated rather than assumed, one exclusive lock serializes
every mutating command, every durable write is a rename, every mutation is
bounded by a journal checkpoint carrying re-observable evidence, and nothing the
application did not create is ever removed. `scripts/check.sh` passes with 977
tests; every Phase 3 module is at 100% branch coverage.

New modules beyond the plan's §7 list, each with a recorded decision:
`preflight.py` (33), `archive.py` (36), `locking.py` (40).

## Phase 4 — Hub Resolution and Repository Ingestion

- [x] HUB-001 Typed Hub client adapter (2026-07-25, this commit — `src/hfcache/hub.py` (plan §7): the only place `huggingface_hub` is called and the only place its exceptions are caught. `HubApi` is a `Protocol`, so a test supplies an object with those methods and no library machinery — plan §12's "deterministic fakes without mocking library internals" implemented as a seam this application defines. Every call passes `token=` explicitly and never `None` (`docs/security.md` T-07); `RepositoryFacts`/`TreeEntry`/`HubIdentity` are types this application owns, so a response-shape change breaks here rather than near the archive; `hub_problem` maps the library's hierarchy onto `HFHUB001`/`004`/`005`/`006`/`007`/`010`; private and gated repositories are refused before anything is fetched. 100% branch coverage, with the library's real exception types constructed rather than approximated)
- [x] HUB-002 Optional identity verification (2026-07-25, this commit — `hub.resolve_host`, `hub.verify_tls`, and `hub.identity_problems`, wired into `preflight.hub_checks` as `doctor` rows 15-17. DNS and TLS are separate checks because they fail for unrelated reasons and are fixed in different places; each depends on the one before, so a host that does not resolve skips the rest rather than reporting three failures for one cause. `hub_identity` is *skipped* when `hub.expected_account` is unset — nothing was verified, and an anonymous archive of public content is a normal deployment — and `HFHUB003` when the Hub names a different account, which catches a credential swapped by mistake before a scheduled run uses it. All three read only, so `--read-only` runs them. `verify_tls` takes an injectable context so `tests/unit/conftest.py` can prove it against a real local TLS server with its own CA: the trust anchor is injected, never the answer, so the code under test is still verifying. `tests/system/test_live_hub.py` (marker `live`) exercises the adapter against the real Hub; the unit suite never touches the network. 100% branch coverage)
- [x] HUB-003 Resolve branch/tag to full SHA (2026-07-25, this commit — `HubClient.repository` performs the resolution and refuses anything but a full 40-character lowercase SHA (`HFHUB007`), since every path, manifest, and reference is keyed by it and an abbreviation never reaches disk. `plan` now resolves each enabled repository and reports `resolved_commit_sha` and `upstream_state`; one repository failing does not abandon the rest, and the run exits `30` if any did. `upstream_state` describes what is true of the *repository* — `missing`, `forbidden`, `refused`, `unresolvable`, `unreachable` — rather than which call reported it. **Still to come at `HUB-004`:** `plan`'s logical size, estimated new bytes, and projected copy-mode publication bytes)
- [x] HUB-004 Repository tree and dry-run size (2026-07-26, this commit — `HubClient.tree` lists the revision recursively against the *resolved SHA*, draining the generator inside the `try` because `list_repo_tree` makes its request during iteration; a file entry with no path is `HFHUB008`, since the listing is the exact path set every later step joins onto a filesystem path. `HubClient.estimate` is plan §13.2 step 3's dry run, against the same private cache a real download writes to and with no allow/ignore filters — and it creates nothing, not even the cache directory, which is proven live so `plan` is safe against an uninitialized archive. `publication.projected_publication_bytes` states the `AD-11` cost model once, so the estimate an operator reads and the reserve a sync will enforce cannot disagree. `plan` now reports `file_count`, `logical_bytes`, `estimated_new_bytes`, `projected_publication_bytes`, and `publication_mode`; a failure at any of the three Hub reads leaves the fields below it `null` rather than guessed. `hub.py` and `publication.py` at 100% branch coverage; `tests/system/test_live_hub.py` proves the tree and the dry run against the real Hub, including that the two agree about the revision's size. **Still to come at `HUB-009`:** `plan`'s retained/current state, which needs the references that package writes)
- [x] HUB-005 Complete `snapshot_download` (2026-07-26, this commit — `HubClient.download` performs plan §13.2 step 5 with every argument plan §12 item 4 requires be explicit: repository id and type, the resolved full SHA rather than the reference that produced it, the cache path, the configured worker count, and the token; no allow or ignore filters exist as arguments, because there is no supported way to archive part of a repository. Resumption is the library's — the canonical download store is the native Hub cache on NFS (`AD-09`), so an interrupted run costs the bytes it had not yet fetched. The `HubApi` protocol is now overloaded on `dry_run` exactly as the library is, so `estimate` and `download` are each typed for the answer they get. `_snapshot_path` refuses a returned path that is missing, unresolvable, outside the cache root, or not a directory — all `HFHUB009`, because to an operator they mean one thing: no usable snapshot. Containment is proven rather than assumed even though the value came from a library and not from a repository (`FS-15`). 100% branch coverage; `tests/system/test_live_hub.py` downloads both test repositories in full and asserts every tree path landed at its stated size, then proves a second dry run reports zero new bytes — plan §26.3's "download every file" and "no unnecessary download" at the adapter level)
- [x] HUB-006 Local-only completeness verification (2026-07-26, this commit — two independent checks, because either alone is insufficient. `HubClient.verify_local` is plan §12 item 5: the same call the download made with `local_files_only=True`, so the library assembles the revision from the cache with the network taken away and reports `HFSYN001` when it cannot. That check is not one this application could write for itself without doing what plan §12 item 7 forbids — parsing the cache's private layout. `src/hfcache/sync.py` (plan §7, no deviation) is the other half: `completeness_problems` compares what landed against the Hub tree independently, reporting missing *and* extra paths as `HFSYN002`, size disagreements as `HFSYN003`, and unsafe sources as `HFSYN004` through the same `source_problems` publication itself uses (`FS-15`). Upstream metadata is treated as a claim and local bytes as the evidence: a size mismatch stops the revision without deciding which side is wrong, since the manifest records what was read (`AD-18`). Path grammar and `T-02` collision folding run here too, so a name that could escape or that would merge with another on a consumer filesystem is refused before it is joined onto anything. **A defect the tests found:** `Path.exists()` and `Path.is_dir()` follow symlinks, so a dangling link in the snapshot looked absent to one check and present to the other and passed completeness with nothing behind it — both now use `follow_symlinks=False`, and the case is pinned by its own test. `hub.py` and `sync.py` at 100% branch coverage; the live suite proves both checks against real downloads of both test repositories, that the local check works with `HF_HUB_OFFLINE=1`, and that deleting one blob fails it)
- [x] HUB-007 Hash new unique content (2026-07-26, this commit — `sync.hash_snapshot` reads every newly introduced unique *physical object* once, streaming in bounded chunks through `hashing.sha256_file`. `ObjectIdentity` is `(st_dev, st_ino)` read during this run and nothing else, because plan §16.1 rules out every other candidate — cache path, prior-run inode, mtime, Git SHA-1, Xet identifier — for the same reason: each can be equal for objects that differ. Two kinds of reuse and the difference between them is the whole of §16.1: *within* a run two paths on one inode are hashed once and both still record `hashed = true`, since the bytes were read; *across* runs a digest is reused only when the inode **and** the size both match a retained publication, and that entry records `hashed = false` naming its source, so no manifest can hold a digest whose origin does not trace back to bytes this archive read. `sync.published_digests` builds that index — manifest for the digest, filesystem for the identity, neither sufficient alone. 100% branch coverage. Two corrections landed with it, decisions 46 and 47)
- [x] HUB-008 Durable manifest generation (2026-07-26, this commit — `sync.build_manifest` assembles the §10.1 field set and is deliberately thin: `RevisionManifest` already enforces `file_count` against `len(files)`, `total_bytes` against the sum, `reused_digests` against the unhashed entries, byte-wise path ordering, collision folding, and the timeline's order, so the builder arranges inputs and does not decide whether they are consistent. Every number comes from what was read; `TreeEntry` gained `git_oid`, `lfs_sha256`, and `xet_hash` off the real listing and they are recorded beside the digest, never as it (`AD-18`). `Timeline` is passed rather than stamped, because the moments it names happened in the caller and stamping them here would record when the manifest was assembled. `reporting.RuntimeVersions.measured()` is new and now the single reader of the three version fields a manifest and a run report both carry — `cli.py` was measuring them separately. Nothing is written: plan §13.2 steps 12 and 16 belong to the transaction that owns the filesystem, which is `HUB-009`. 100% branch coverage; the live suite runs the whole sequence against the real dataset repository — resolve, list, download, check, hash, describe — and round-trips the manifest through its durable form)
- [x] HUB-009 Publish revision instance; atomic per-SHA and current refs (2026-07-26, this commit — `sync.publish_revision` performs §7.3 checkpoints 4-9, each act followed by the checkpoint that names it; `Transaction.checkpoint` refuses a name that is not next, so a journal this function produced can only describe an execution that really happened. Every adjacency in the order is load-bearing and the docstring says which: the manifest is written into *staging* before the rename (`StagingPaths.manifest` is a sibling of `tree/`, so it does not travel with it) which is what makes a crash between checkpoints 5 and 6 recoverable; the tree is renamed before the manifest is published; both are durable before the per-SHA reference and that before `current.json`, a single rename so the previous current revision is usable on either side of it (`FS-10`, `FS-12`). The staging loop is driven by `manifest.files`, so the published tree cannot contain a path its own manifest does not list — by construction rather than by agreement between three collections. `publication.py` gained the derived view: `published_repositories` (read off disk, not configuration, because `AD-06` keeps an unconfigured repository's data), `retained_references`, `next_generation` (`max + 1`, never `count + 1` — a prune would make counting reissue a generation), `rebuild_catalog`, and `publish_catalog`. `identity.TYPE_DIRECTORIES` is public now, since discovery needs the same two names. Both modules at 100% branch coverage; `tests/unit/test_publish_revision.py` publishes through the real code path rather than fabricating output, and the live suite archives both test repositories end to end on a throwaway archive — every Hub path present at its stated size and sharing an inode with its cache blob, references resolving, manifest describing exactly the published tree. **`/srv/hfcache` is deliberately untouched:** the §36.4 one-time authorization is spent at the rollout checkpoint, not by a test)

**Phase 4 complete.** One public model and one public dataset can be archived:
resolved to an immutable SHA, enumerated, costed, downloaded, checked for
completeness two independent ways, hashed object-by-object, described by an
immutable manifest, and published as a hardlink tree behind two atomic
references — every step bounded by a §7.3 checkpoint carrying re-observable
evidence. `scripts/check.sh` passes with 1160 tests; `-m live` runs 24 against
the real Hub, including the full end-to-end publication of both test
repositories. Every Phase 4 module is at 100% branch coverage.

`sync.py` was added from plan §7's list, no deviation. Decisions 44-47 record
this phase's four settled interpretations.

## Phase 5 — Multi-repository Sync and Retention

- [x] SYNC-001 Deterministic multi-repository orchestration (2026-07-26, this commit — `sync.synchronize_repository` runs plan §13.2 end to end for one repository and `sync.synchronize` runs §13.1 steps 5-11 over a selection, in *configuration* order rather than selector or alphabetical order, because two runs naming the same repositories have to do the same things in the same sequence for a partial run's journals to be interpretable. The `sync` command holds `preflight.guarded` — lock then §19 checks — for the whole run rather than per repository: proving the archive sound and then letting another command mutate it throughout would prove nothing. `preflight.require_capacity` is new, because §13.1's whole-run preflight runs before any repository is resolved and so knows a need of zero; the per-repository gate is the same measurement taken immediately before the download it guards, so the repository that would have overflowed is the one that reports it. A disabled repository is reported rather than omitted, and a SHA the archive already retains is `skipped` or `ref_moved_to_retained_revision` — the two look alike from outside and mean different things. **Continuation landed here rather than at `SYNC-002`:** a loop that cannot record a failure cannot be tested at all, so `continue_on_repository_error` and per-repository failure recording are in this commit; `SYNC-002` takes the aggregate reporting that sits on top of them. 100% branch coverage on `sync.py`; `tests/unit/test_synchronize.py` drives whole runs through a `HubApi` fake whose cache is real — blobs reached through symlinks — so the inode sharing publication depends on is exercised rather than approximated)
- [x] SYNC-002 Continuation and aggregate failure reporting (2026-07-26, this commit — the aggregate a run produces, and the two commands that read it afterwards. `taxonomy.aggregate_exit_code` now decides the run's single exit from every code encountered, in `docs/cli.md` §3's operator-urgency order, while the durable report and the `--json` envelope both list all of them — aggregation decides which number a scheduler sees and hides nothing. The envelope's `errors` and `warnings` arrays are rebuilt from the durable report rather than collected alongside it, so the two cannot describe different runs, and each entry names the repository it belongs to. `status` now reports per-repository retained count, retained generations, current SHA and generation, and last-run status, read from the *references* and the newest run report rather than from the catalog — `status` is what an operator runs when something is already wrong, and the catalog is derived (`FS-16`). It tolerates damage in both: an unreadable reference costs that repository's current-revision fields and an unreadable run report costs one field, neither costs the command. **`hfcache list` is implemented here** (decision 48). 100% branch coverage on `sync.py`; `cli.py` at 99%, the one gap still the unreachable `hf_xet` fallback)
- [x] RET-001 Immutable publication-generation retention ordering (2026-07-26, this commit — `src/hfcache/retention.py` (plan §7): `ordered_revisions` reads the retained set from `refs/revisions/<sha>.json` and sorts by `publication_generation` ascending, and the module docstring records why every alternative key was rejected — wall-clock time reorders under repair, upstream commit time reorders under a force-push or a branch reset, directory mtime reorders under a backup, and a SHA has no order at all. The references rather than the revision directories, because a directory can hold a superseded repair instance inside its grace period and that instance is not retained. Gaps mean nothing and collisions are impossible (`FS-20`). 100% branch coverage, with the ordering asserted as a Hypothesis property over arbitrary generation sets rather than only over examples)
- [x] RET-002 Five-revision selection (2026-07-26, this commit — `prune_candidate` is plan §15.2 step 3, and returns `None` in three cases that are all correct behaviour rather than limitations: at or below the limit including exactly five, since a prune is triggered by a successful publication *beyond* the maximum (`AD-04`) and never by a count; when the oldest revision is the current one, which is reachable when upstream moves back to a repository's earliest retained SHA and where over-retention is the right answer; and when nothing is retained. `selection_problems`/`require_valid_selection` refuse a selection before a plan is built, so a caller gets a coded `HFRET001` naming the policy rather than a validation error naming a field — `PrunePlan` enforces the same rules on a recorded plan, and the duplication is deliberate because the cost of being wrong is deleting the wrong revision. Two Hypothesis properties pin the invariants no failure may break: a selection is never the current revision, and is always the lowest generation)
- [x] RET-003 Dry-run prune plans (2026-07-26, this commit — `retention.plan_prune` is plan §15.2 steps 1-4, built from the same reads the prune performs, so a plan an operator reviewed is the plan that runs. Non-mutating by construction: the plan is a value, and persisting it is checkpoint 1 of the transaction, because a plan that was written down is a commitment and reading one should not be. `unique_bytes_released_estimate` is named an estimate and is the tree's logical size, which is an upper bound — blobs shared with retained revisions release nothing and ZFS snapshots may hold the rest for weeks (§15.3); reporting the bound is honest where a computed figure would imply precision the storage layer does not offer. `prune --dry-run` / `--apply` implemented, with `--apply` planning *inside* the lock because a plan made before it could be stale by the time it ran)
- [x] RET-004 Published-view and manifest cleanup (2026-07-26, this commit — see `RET-006`; the tombstone rename of the tree and the manifest, the catalog republication, and the `audit/pruned/` records are checkpoints 3-6 and 8 of one transaction and are not separable from it. The original manifest is copied byte for byte rather than re-serialized from a parsed model: it is the evidence of what was there, and this release's rendering of it is not the bytes the archive published (`FS-06`))
- [x] RET-005 Supported Hub cache revision deletion (2026-07-26, this commit — `hub.delete_cache_revision` goes through `scan_cache_dir(...).delete_revisions(...).execute()` and never removes a blob by path (`FS-14`, plan §12 item 7). This application does not know which blobs a revision uniquely owns — that is the library's bookkeeping and a revision's blobs are routinely shared with revisions that are staying. It runs at checkpoint 2, while all six revisions are still published, so the hardlinks hold the bytes whatever the cache does; a failure is `HFRET002` and the revision is preserved)
- [x] RET-006 Prune journals, tombstone rename, reconciliation after partial failure (2026-07-26, this commit — `retention.apply_prune` performs all ten §7.4 checkpoints. **Checkpoint 7 is the commit point** and divides the transaction into two opposite failure regimes: before it a failure leaves six revisions published, because over-retention is always preferable to a revision that should not have gone; at or after it nothing is ever republished, because five revisions are what consumers see and re-adding the sixth would contradict a decision the archive recorded. The per-SHA reference is removed *before* the tree is tombstoned (decision 4), so no reference ever names a tree that has been renamed away. Retention runs from `sync` after the publication transaction has committed, never inside it, so a prune failure is its own failure with its own journal and can never take the revision just published down with it. **A bug the tests found:** the `prune --apply` path passed `_run_envelope(config)` to `apply_prune`, which reads `envelope["run_id"]` — a key that envelope does not carry, so the command would have raised `KeyError` the first time it had real work to do. The deferred-prune test is what exercised it)
- [x] RET-007 Protect unmanaged and upstream-missing repositories (2026-07-26, this commit — the guarantee is structural rather than a check: a prune is reachable only from a *successful publication* of that repository (`AD-04`), so a repository nothing is publishing to cannot reach one. A repository removed from configuration is not processed, keeps every revision and its current reference, and reads as `managed = false` with `enabled = null` in the catalog; a disabled one is reported and left alone; a 403, a 404, and an unreachable endpoint all end the repository without touching a byte of it (`AD-06`). Asserted rather than assumed — the tests remove a repository from configuration, disable one, and fail one upstream three ways, each time comparing the retained set and the current reference before and after. **A gap the tests found:** the catalog was rebuilt only inside `publish_revision`, so a run that published nothing left it stale, and a repository removed from configuration kept reading as managed until something else happened to publish. Plan §13.1 step 10 is a *whole-run* step distinct from §7.3 checkpoint 9, and `synchronize` now performs it)

**Phase 5 complete.** Unattended rolling synchronization works end to end: a
run takes one lock, proves the §19 requirements once, processes repositories in
configuration order, continues past a failure when configured to, rotates the
oldest revision out when a sixth is published, and records everything in a
durable run report an operator reads back through `status` and `list`. Five
revisions accumulate unchanged; a sixth prunes exactly one; a failed prune
prunes nothing and leaves six. `scripts/check.sh` passes with 1257 tests; every
Phase 5 module is at 100% branch coverage.

`retention.py` was added from plan §7's list, no deviation. Decision 48 records
where `hfcache list` landed.

## Phase 6 — Dependency Warnings and Archive Verification

**Carried into this phase.** Two items are open that the packages above should
have closed, recorded here rather than left to be rediscovered:

1. **Recovery's roll-forward remedies are still `blocked`.** `STO-011` deferred
   them explicitly — "rolling a publication forward from checkpoint 5 needs
   `HUB-009`'s manifests, a prune needs `RET-006`; each package adds its own
   remedy as it lands" — and both packages landed without adding them.
   `recovery.plan_recovery` today resolves only a publication that crashed
   *before* checkpoint 5 (quarantine staging) and one with every checkpoint
   recorded (close the journal); all four `docs/architecture.md` §7.3 crash-matrix
   rows from "after 5, before 6" onward, and §7.4's prune rollback and
   roll-forward, return `operator` instead of the resolution the document
   already specifies. `VER-006` adds the repair remedy regardless, so the four
   belong together.

2. **`verification_state` is hardcoded `"verified"` in three places** —
   `publication.py` `_catalog_entry`, and `cli.py` `_status_entry` and
   `_listed_revision`. No document says whether a revision that was SHA-256
   verified at ingestion but never verified offline is `verified` or
   `unverified`, so this is an unsettled question rather than a defect; today
   `failed` is unreachable and `unverified` is never reported for a published
   revision. `VER-005` has to settle it, record the decision, and make all three
   read the same source.

- [x] DEP-001 Model-card dependency inspection (2026-07-26, this commit — `src/hfcache/dependencies.py` (plan §7) reads `README.md`'s YAML front matter through `huggingface_hub.repocard.metadata_load`, which parses with `yaml.safe_load`: no object construction, no tag that could reach a constructor (`AD-15`, T-04). A `base_model` holding a list produces one observation per entry, because a merged model legitimately names several parents. Detection reads the *snapshot*, so it sees the same bytes that were hashed and will be published — a detector reading anything else could report a dependency the archived revision does not declare)
- [x] DEP-002 Adapter-config dependency inspection (2026-07-26, this commit — `adapter_config.json` through `json.loads` and nothing else; PEFT would import it through its own loader, and reading it as the JSON document it is, is the whole difference between describing an adapter and running one. `base_model_name_or_path` is recorded at `high` confidence, above a card's `base_model`, because an adapter without its base cannot be loaded at all rather than merely being incomplete)
- [x] DEP-003 Compare observations with declared dependencies (2026-07-26, this commit — `declared` and `managed` are separate questions and the manifest records both: declared-but-unmanaged is an operator who knows and decided not to archive it, managed-but-undeclared is a stale declaration. Comparison is case-folded, because the Hub treats `Org/Model` and `org/model` as one repository while a `declared_dependencies` entry is typed by hand, and reporting a case difference as undeclared would train an operator to ignore the code. `managed` is matched on bare repository ids rather than selectors, since a `base_model` value carries no type prefix)
- [x] DEP-004 Persist and display non-fatal warnings (2026-07-26, this commit — an undeclared dependency emits `HFDEP001` once however many observations carry it (the code names the condition, not the instance), is written into the immutable manifest's `dependencies` array along with the declared ones, marks the repository `completed_with_warnings`, reaches the run report and the `--json` envelope, and leaves the exit code at `0`. It never triggers a download (`NG-05`): a detector that fetched what it found would turn one configured repository into an unbounded transitive closure. Unparseable metadata is recorded at `low` confidence rather than guessed at — 'this file did not parse' is a finding an operator can check. 100% branch coverage; the tests feed the detector a YAML tag naming a Python callable and assert the result is an observation rather than an effect)
- [x] VER-001 `verify --new` (2026-07-26, this commit — `src/hfcache/verification.py` (plan §7) and the `verify` command. The module has no write path at all, which is how plan §16.1's last line is enforced rather than remembered: a finding is a value, so a mismatch structurally cannot rewrite a manifest, prune a revision, or re-download over the evidence. Every artifact it reads can fail and none of those failures escape — an unparseable reference, a manifest that will not load, a manifest filed under the wrong SHA, and a tree that is not there are each a finding attributed to the revision they belong to, and the run continues to the next one, because `verify` is what an operator reaches for when the archive is *already* known to be wrong (§7.9). `ReadSet` is plan §16.2 item 4: keyed by `sync.ObjectIdentity` and confirmed with `samefile` rather than trusted, since an inode number is reused after deletion; sharing is decided per *file* from the manifest's own `publication_mode`, because a hardlink-mode and a copy-mode tree can both be retained and each has to be read the way its bytes are laid out. `--new` resolves through the archive's current references rather than the publication ids the run recorded, so a revision a later prune rotated out is not verified and one a later repair replaced is verified in its replacement. Exit `0` clean, `40` on any finding, with the envelope's `errors` grouped by `(kind, repository)` — the complete set is in `data`, and an array with one entry per finding is not something an operator reads. 100% branch coverage. **A correction landed with it:** `emit_envelope` minted a fresh run id for every command, so `sync`'s envelope and its durable report named different runs, which is precisely what `docs/cli.md` §4 says that field is for; both now pass the report's id. Decision 49 records the two contract amendments. **Still to come:** `--full` at `VER-002`, `--revision` at `VER-003`, `--estimate` at `VER-004`, and the durable report and catalog update at `VER-005` — this package builds the `VerificationReport` and emits it, and does not yet write it to `runs/`)
- [x] VER-002 Unique-object full verification (2026-07-26, this commit — `verify --full` over `verification.resolve_archive`, which reads the repository set off `published/repos/` rather than off configuration: removing a repository from configuration never deletes its archive (`AD-06`), so a quarterly job that skipped unmanaged repositories would leave exactly the content nothing else touches unchecked. The lock is `preflight.guarded` with `verification.lock_wait_seconds`, which is the *global* lock rather than a second one (§22.3) — that is what makes `--full` mutually exclusive with sync, prune, and repair, and it is taken before the §19 gate for the same reason every mutating command takes it first. `hub.networking_disabled` sets `HF_HUB_OFFLINE` for the duration and restores the previous value rather than clearing it, since a deployment may legitimately run offline; the real guarantee is structural, though, and is asserted as such — `verify` builds no `HubClient` and resolves no credential, and a test replaces `HubClient` with one that raises to prove it. Read-once is now demonstrated at archive scale: two revisions sharing hardlinked blobs report one read per object, and the same pair published in copy mode reports two. 100% branch coverage on `verification.py` and `hub.py`)
- [x] VER-003 Revision-scoped verification (2026-07-26, this commit — `verify --revision TYPE:ID@SHA`, the mode an operator uses after a `--full` reported a finding and again after a `repair` claims to have fixed it. The SHA is *required* rather than defaulted to the current revision: defaulting would answer a question nobody asked and would report clean while the suspect revision sat unexamined (`HFARG001` when the selector carries none). The repository need not be in configuration, because an unmanaged repository's data is still the archive's (`AD-06`) and a revision under investigation is often one whose repository was removed — so `--revision` deliberately does not go through `_select`. A SHA the archive does not retain is `HFARG004` at exit `10` rather than a finding at exit `40`, since telling a scheduler the archive is corrupt because somebody typed one wrong character is the worse failure; `verification.require_retained` owns that distinction and still returns a *damaged* revision as findings, because the operator asked about that SHA and it is there. `_mode_option` names the mode in the envelope's `command` even for an invocation that was itself the thing refused)
- [ ] VER-004 Verification estimation
- [ ] VER-005 Verification reports and current health
- [ ] VER-006 Isolated-cache repair, atomic ref switching, retirement grace, checkpointed cleanup

## Phase 7 — TrueNAS and CentOS Stream Deployment

- [x] NAS-001 Create and tune the TrueNAS dataset (2026-07-24, host prep — quota deferred to handoff item 4)
- [x] NAS-002 Create sync and read identities and permissions (2026-07-24, host prep)
- [x] NAS-003 Configure exact-host read/write export (2026-07-24, host prep; write-verified)
- [b] NAS-004 Server-side read-only consumer export — operator (handoff item 1)
- [b] NAS-005 Disjoint writer/consumer export proof — operator-assisted (handoff item 2); hardlink + atomic rename already proven on the live dataset 2026-07-24
- [b] NAS-006 Snapshots, replication, scrubs, capacity alerts — operator (handoff item 3)
- [x] HOST-001 Provision CentOS Stream 10 VM, DNS, time, updates (2026-07-24, host prep)
- [x] HOST-002 Service identity and local paths (2026-07-24, host prep)
- [x] HOST-003 Hard NFSv4 mount (2026-07-24, host prep; automount active)
- [ ] HOST-004 Install the locked application environment
- [ ] SYS-001 Install and validate systemd target, services, timers
- [ ] SYS-002 Apply and test systemd hardening
- [ ] SEL-001 Validate all operations with SELinux enforcing
- [ ] SEC-001 Validate optional systemd credential support

## Phase 8 — Operational Readiness and Release

- [ ] OPS-001 Installation and upgrade runbooks
- [ ] OPS-002 Sync, verification, pruning, and status runbooks
- [ ] OPS-003 Corruption and repair runbooks
- [ ] OPS-004 Snapshot/replica restore runbook
- [ ] OPS-005 Failure-injection suite (test-level §26.6; live-mount interruption tests are handoff item 7)
- [ ] OPS-006 Capacity and throughput benchmarks (writer-side measurements)
- [ ] OPS-007 Downstream copy and manifest verification (exercise the consumer helper from the writer against `published/`; the true consumer-client test is handoff item 5)
- [ ] REL-001 Build and install release candidate from wheel
- [ ] REL-002 Final quality and security gates
- [ ] REL-003 Tag and document the first release

## Live rollout checkpoints (§29, writer-side)

- [ ] Archive initialized on `/srv/hfcache` with the UUID already provisioned in
      `/etc/hfcache/config.toml` (§36.4 one-time authorization). `STO-000` built
      the command; the authorization is spent here, after `HOST-004` installs a
      release, so the layout is the one the finished application uses.
      `archive init --inspect` is non-mutating and may be run against the live
      mount at any time before that.
- [ ] `hfcache doctor` clean on the live mount
- [ ] Test repositories chosen and recorded below; `hfcache plan` reviewed
- [ ] First manual sync published both test repositories
- [ ] Second sync idempotent (skip)
- [ ] `hfcache verify --full` clean; `hfcache status` clean
- [ ] `hfcache.target` enabled; sync timer active; verification timer installed but disabled

## Test repositories (decided 2026-07-26 at `HUB-004`, §36.5)

- Model: **`hf-internal-testing/tiny-random-gpt2`** — 10 files, 12 512 611 bytes
  (11.9 MiB) at `71034c5d8bde858ff824298bdedc65515b97d2b9`.
- Dataset: **`hf-internal-testing/fixtures_ade20k`** — 7 files, 206 179 bytes
  (201.3 KiB) at `850d349e5038f291284e7999fcacbedc0922534b`.

Both public, neither private nor gated, sizes measured by `hfcache plan` against
the live Hub on 2026-07-26 without downloading anything. Recorded in
`examples/config.toml`, which validates, and used by `tests/system/test_live_hub.py`.

Why these two. `hf-internal-testing` is the organization Hugging Face maintains
for exactly this purpose, so the repositories are long-lived and unlikely to be
renamed or deleted out from under a test. Both are far under the §36.5 100 MB
ceiling, which matters because §36.6 item 7 requires a full sync, an idempotent
second sync, and a `verify --full` over them — a cycle that has to be cheap
enough to run repeatedly. And they differ in shape as well as size: the model is
a handful of large-ish weight files, the dataset a mix of images, a parquet file,
and a README, so publication and hashing are exercised over both profiles.

§36.5 authorizes the session to choose these; see **Operator decisions needed**
item 1 for the separate production-list question that does need an operator.

## Operator handoff

Keep instructions exact and copy-pasteable; add acceptance checks.

1. **NAS-004 — consumer export (TrueNAS UI on `nas.lab.cross.solutions`):**
   NFSv4 export of `/mnt/tank/huggingface-archive/published`, read-only enabled
   server-side, Mapall `hfcache-read:hfcache-archive`, allowed clients =
   explicit consumer hosts or consumer VLAN, **excluding** `192.168.10.90`
   (plan §20.2). Acceptance: consumer can read; consumer create/modify/
   rename/delete all fail at the server.
2. **NAS-005 — disjointness proof:** from a consumer client, mount the
   `published/` export and prove read works and writes fail while the writer
   export stays read/write; confirm TrueNAS 25.10.5 accepts the
   parent/subdirectory topology, else invoke the §20.2 two-dataset fallback.
3. **NAS-006 — data protection:** snapshots (daily ×14 d, weekly ×8 w, monthly
   ×12 m, daily before 02:00 sync), replication, scrub cadence, capacity
   alerts per plan §20.3.
4. **Dataset quota:** set after the session reports dry-run sizes for the
   chosen production repositories (plan §20.1).
5. **Consumer copy test (§29 steps 10–11):** from a consumer client, copy the
   current model and dataset revisions with the documented helper and verify
   against the manifests.
6. **Reboot persistence (§26.5):** reboot the writer; confirm mount, target,
   and timers return; confirm boot completes with the NAS down.
7. **Live-mount interruption window (§26.4):** operator-supervised NFS
   disconnect/reconnect during a test sync, or provision a disposable dataset.
8. **Verification timer enable (§29 step 14):** confirm the quarterly calendar
   does not overlap NAS scrub/SMART/replication, then enable.
9. **Optional cleanup:** revoke passwordless sudo
   (`sudo rm /etc/sudoers.d/tyler-nopasswd`) after rollout.

## Operator decisions needed

1. **Which repositories the archive is ultimately for** (raised 2026-07-24, during
   `CFG-002`; not blocking until `HUB-005`). Two separate questions have been
   conflated so far, so they are separated here:

   - *The two test repositories* (§36.5) did **not** need an operator: the plan
     authorizes the session to choose them, requiring only that each is public,
     well under 100 MB, and confirmed available at implementation time. **Settled
     2026-07-26 at `HUB-004`** — see "Test repositories" above; recorded in
     `examples/config.toml`. This half of the item is closed.
   - *The production repository list* does need an operator, because it is the
     only input to handoff item 4 (the TrueNAS dataset quota) and to §29 step 12.
     Nothing is blocked while it is open: Phases 3–6 are written against
     configuration, not against a particular repository.

   When the list is known, `hfcache plan` reports dry-run sizes for it without
   downloading anything, which is the number the quota decision wants.

## Decisions

_Settled implementation deviations from `docs/plan.md`, with rationale (§36.3)._

1. **`docs/schemas.md` added beyond the plan §7 documentation set** (2026-07-24,
   ARC-004). The plan's `docs/` listing has no home for `ARC-004`'s durable JSON
   schemas. Folding them into `architecture.md` would have made one document
   carry both the reasoning and roughly a thousand lines of format reference;
   folding them into `configuration.md` would have conflated operator input with
   application output. A dedicated schema reference is also the document a
   consumer or auditor reads without needing anything else. Plan §7 is updated
   in the `ARC-005` commit, once the full documentation-set deviation is known.

2. **`docs/cli.md` added beyond the plan §7 documentation set** (2026-07-24,
   ARC-005). Same reasoning as decision 1. `operations.md` is the Phase 8
   runbook document — task-oriented, "how do I rotate a revision" — and is the
   wrong home for a reference contract that Phase 2 code is written against.
   Keeping the command surface, JSON envelope, exit-code aggregation, and the
   complete error taxonomy in one place also means `CFG-007` has a single
   normative source. Plan §7's `docs/` listing is updated in this commit to
   include both `cli.md` and `schemas.md`; the deviation is now final.

3. **Exit-code aggregation order fixed as `40`, `50`, `30`** (2026-07-24,
   ARC-005). Plan §11.2 fixes the codes and requires a non-zero result when a
   run continues past a repository failure, but does not say which code wins
   when several arise in one run. Codes `10` and `20` abort before
   per-repository work, so only `30`/`40`/`50` can co-occur. They are ordered by
   operator urgency — possible corruption, then degraded retention, then stale
   content — and every classification encountered is still listed in the JSON
   envelope's `errors` array, so aggregation hides nothing.

4. **Prune removes the per-SHA reference before tombstoning the tree**
   (2026-07-24, ARC-006). Plan §15.2 ordered these the other way — tombstone the
   tree and manifest at step 8, remove `refs/revisions/<sha>.json` at step 9.
   That leaves a window in which a reference names a tree that has already been
   renamed into trash, which breaks the invariant that every existing reference
   resolves (`FS-10`) and would be visible to `verify` and `repair`, both of
   which resolve per-SHA refs. Recovery never needed the reference to find the
   tree: the persisted `PrunePlan` already names it. Every property plan §15.2
   asserts is preserved — cache deletion still happens while all six revisions
   are published, rollback before the commit point still restores six revisions,
   and the complete manifest is still recoverable from trash. Plan §15.2 steps
   8–9 are updated in this commit.

5. **`sync.stale_staging_age_hours` added to the configuration schema**
   (2026-07-24, ARC-006). Plan §13.3 requires that stale staging directories be
   reclaimed only when they "exceed a configurable age", but the §9 schema had no
   key for it, so the requirement was unimplementable as written. Added with a
   24-hour default and a `1..8760` range. The delay is not the safety mechanism
   on its own — reclamation also requires a transaction-ID-shaped name and an
   existing journal — it exists so a concurrent operator command cannot have its
   working directory reclaimed underneath it. Plan §9 and §9.1 are updated in
   this commit.

6. **MIT license, `uv_build` backend** (2026-07-24, BOOT-001). Plan §7 requires a
   `LICENSE` file but names no license, and §8.1 requires `uv build` artifacts
   without naming a backend. MIT is the conventional permissive default for an
   internal tool and constrains nothing; changing it is a one-file edit with no
   code impact. `uv_build` is uv's own PEP 517 backend, needs no extra build
   dependency, and supports the `src/` layout natively — consistent with §8.1's
   requirement to build both sdist and wheel with `uv build`.

7. **Python 3.14 pin confirmed; `hf-xet` is a required dependency, not an extra**
   (2026-07-24, BOOT-002). Plan §8.1 made the 3.14 pin "subject to final
   compatibility validation" and §8.2 left open whether the Xet backend arrives
   by default or via the `huggingface_hub[hf_xet]` extra. Both are now settled:
   `huggingface-hub` 1.24.0 requires `hf-xet` directly, and `hf-xet` 1.5.2 ships
   `cp38-abi3` manylinux wheels that install on CPython 3.14.6 with no source
   build. The fallback to 3.13 is not needed. Plan §8.1 and §8.2 updated in this
   commit.

   Also verified against the locked version, since the plan's design depends on
   them: `HfApi.{repo_info,model_info,dataset_info,list_repo_tree,whoami}`,
   `snapshot_download`, `scan_cache_dir`, `HFCacheInfo.delete_revisions`, and the
   `Cached{Repo,Revision,File}Info` types all exist. `snapshot_download` accepts
   `dry_run`, which is what plan §13.2 step 3 needs for pre-download size
   estimation — no separate estimation path is required.

8. **`scripts/` added to the project layout; no CI-provider configuration**
   (2026-07-24, BOOT-007). Plan §7's tree has nowhere to put the
   "provider-neutral quality scripts" `BOOT-007` requires, so `scripts/check.sh`
   is added and plan §7 updated in this commit. Deliberately *not* added: any
   CI-provider file. The gate is one script that a shell, a git hook, or a
   pipeline all invoke identically, so a green pipeline and a green workstation
   mean the same thing. A Makefile was considered and rejected — `make` is not
   installed on the CentOS Stream 10 writer, and bash is.

9. **`--token-file` with `token_mode = "disabled"` is `HFARG002`, not a silent
   choice** (2026-07-24, CFG-002). `docs/configuration.md` §3 says `"disabled"`
   means Hub calls *always* pass `token=False`; §7 says `--token-file` is the
   first-match-wins source. When both are present the two sentences disagree, and
   the contract did not say which wins. Honouring the flag violates the configured
   mode. Ignoring the flag is worse: the operator believes the run was
   authenticated and nothing says otherwise. So the combination is refused before
   any Hub request, consistent with `AD-11`'s rule that a mode is never silently
   downgraded. `docs/configuration.md` §7.2 and the `HFARG002` row in
   `docs/cli.md` §5.1 are updated in this commit.

10. **`HFARG006` added for a systemd credential that is present but unusable**
    (2026-07-24, CFG-002). The taxonomy had `HFARG005` for `--token-file` and
    nothing for the other source, so an empty, unreadable, or malformed systemd
    credential had no code. It needs one distinct from `HFARG005`, because the two
    conditions have different fixes — one is a mistyped command line, the other a
    broken unit or credential store. Absence still resolves to anonymous access,
    since `token_mode = "optional"` says a missing credential is normal; presence
    plus unusability does not, because continuing anonymously would report success
    for a run the operator believes was authenticated. `$CREDENTIALS_DIRECTORY`
    set to a relative path shares the code: systemd always sets it absolute, so a
    relative value means the environment is wrong and a credential would otherwise
    be read relative to the working directory. Added to `docs/cli.md` §5.1 in this
    commit; the plan does not enumerate `HFARG` codes, so no plan amendment is
    needed.

11. **A credential file is validated, never sanitized** (2026-07-24, CFG-002).
    §7 said to strip a single trailing newline and said nothing about what may
    remain. A token becomes an `Authorization` header, so a value containing a
    stray carriage return, tab, or second newline must not be forwarded — and must
    not be quietly cleaned up either, because a file that malformed is not
    reliably the token the operator intended. After the one newline is removed the
    remainder must be non-empty printable ASCII with no whitespace, in a regular
    file of at most 4096 bytes. The size cap keeps a mistyped path from reading a
    large file into memory before its contents are found unusable. Recorded as
    `docs/configuration.md` §7.1.

12. **`hub.credential_name` may not be `.` or `..`** (2026-07-24, CFG-002). Both
    match the published `[A-Za-z0-9._-]{1,64}` grammar, and both name a directory
    rather than a credential. Neither is exploitable — no `/` is permitted, so the
    worst case resolves to `$CREDENTIALS_DIRECTORY` itself and fails as "not a
    regular file" — but it fails at run time with a confusing message instead of
    at `config validate` with a clear one. Rejected as `HFCFG013`, and the §3
    constraint column is updated in this commit.

13. **A reference's paths are relative to `published/`, every other artifact's are
    archive-relative** (2026-07-25, CFG-003). `docs/schemas.md` §1 said every path
    field is archive-relative; §4.1 said a reference's `tree` and `manifest` are
    relative to `published/`, and its worked example was written that way. Only one
    can hold. `published/` wins, because it is not a stylistic choice: a consumer
    mounts `published/` and nothing else, so an archive-relative `published/repos/…`
    would resolve to `<mount>/published/repos/…`, which does not exist. The rule is
    now stated once with its exception, in `docs/schemas.md` §1 and in `FS-09`, both
    amended in this commit. `RepositoryLayout` exposes the two forms as separate
    methods — `tree_reference` and `manifest_tree_field` — so the distinction is
    made by the type of artifact being written rather than by a caller remembering
    which base applies.

    Extended at `CFG-004`: the prose was right and three *examples* were wrong.
    The manifest (§3), prune plan (§8), and journal (§10) examples had all copied
    the reference's published-relative form into fields their own prose calls
    archive-relative, so every one of them was missing the `published/` prefix.
    Corrected in the `CFG-004` commit. The rule that decides the base is narrow:
    a field is published-relative only when a consumer has to resolve it, which
    is true of exactly the reference's `tree` and `manifest`. Everything else is
    archive-relative, including `catalog/verification.json`'s `report`, which
    names a path under `runs/` that a consumer deliberately cannot follow.

14. **The repository-relative path grammar is published** (2026-07-25, CFG-003).
    `docs/security.md` T-02 required every repository path to be "normalized and
    validated to remain under the publication root" but never said against what
    grammar, so the requirement could not be implemented twice the same way. Now
    written out as a table in `docs/architecture.md` §5.3. The rule that generated
    it: reject what can **escape**, allow what is merely awkward. A backslash is
    rejected because it is a path separator on a consumer platform, where
    `a\..\..\b` traverses; a trailing space or a name like `CON` is left alone,
    because this application does not get to decide what a repository may call its
    files. Sizes are measured in bytes rather than characters, since `NAME_MAX` is.

15. **Collision folding is deliberately stricter than any one filesystem**
    (2026-07-25, CFG-003). T-02 requires rejecting two manifest entries that
    "resolve to the same on-disk path — including via case or Unicode-normalization
    collision" without fixing a fold. The fold is NFC plus `str.casefold`. Full case
    folding also maps some ligatures, so `ﬁle` and `file` are reported as colliding
    even though nothing would really merge them. That over-rejection is the intended
    direction: refusing a pair of names is visible, explainable, and recoverable by
    an operator, while publishing a tree in which two manifest entries resolve to
    one file is silent and corrupts the thing being archived (`AD-16`). NFKC is not
    applied — it folds superscripts and width variants that no consumer could
    confuse, and would refuse legitimate names for nothing.

16. **Five identifier grammars accepted a trailing newline; fixed** (2026-07-25,
    CFG-003). `config.py` compiled `^…$` and applied it with `re.match`, and in
    Python `$` also matches immediately before a trailing newline. So
    `parse_revision` accepted `"main\n"` and, worse, accepted a 40-character SHA
    with a newline glued to it and returned the value including the newline — which
    would then have been sent to the Hub and written into a path and a manifest.
    TOML can produce such a value through an escape or a multi-line string. All five
    patterns (`_SEGMENT`, `_REFERENCE_NAME`, `_COMMIT_SHA`, `_ACCOUNT`,
    `_CREDENTIAL_NAME`) now use `fullmatch` with no anchors, `tests/unit/
    test_identity.py` provokes the newline case for every grammar, and a structural
    test fails if any future pattern in the module is written anchored. This is the
    same defect found in `credentials.py` during `CFG-002`; finding it a second time
    is why the guard is now structural rather than another example.

17. **`credentials.py` and `identity.py` added to the plan §7 module list**
    (2026-07-25, CFG-003). Neither existed in the plan's source tree.
    `credentials.py` should have been added by `CFG-002` and was missed;
    `identity.py` is new here, splitting the *names* the archive uses from the
    *paths* built out of them. The split has a purpose beyond tidiness: `paths.py`
    joins identifiers straight into filesystem paths, so it needs a module whose
    whole contract is that a value which came out of it is safe to join. Plan §7 is
    updated in this commit.

18. **Durable files are indented; the `--json` envelope is not** (2026-07-25,
    CFG-004). `docs/schemas.md` §1 named the separators `(",", ": ")` but no
    indentation. That pair is exactly what `json.dumps` uses *when indentation is
    on* — the compact spelling would be `(",", ":")` — and every worked example in
    the document is 2-space indented, so indentation was intended and unstated.
    Now stated. The envelope stays unindented, which is not an inconsistency but
    the distinction that matters: a durable file is read and diffed by an operator
    during an incident, while the envelope is one machine-read line on a pipe.
    `docs/cli.md` §4 already listed only the three rules that carry over — sorted
    keys, UTF-8, trailing newline — so no change was needed there. Both paths call
    `models.serialize`, so §11's "one shared function" is literal rather than
    aspirational.

19. **Reading a durable artifact takes the caller's error class *and* code**
    (2026-07-25, CFG-004). The same malformed file means different things
    depending on which artifact it is: a bad manifest is `HFVER007` at exit `40`,
    a bad journal is `HFTXN001` at exit `20`, a bad sentinel is `HFMNT006` at exit
    `20`. `load` therefore takes both, and applies the code to every problem it
    reports, with the field path as the location. That is what lets the field
    validators in `hfcache.identity` and `hfcache.paths` stay ignorant of which
    artifact they are validating — the artifact names the code, the field names
    the place. `parse_archive_relative` and `parse_repository_relative` gained an
    optional `code`; omitted, they raise an uncoded `ValueError` for a validator
    to collect.

20. **§1.1's "unknown keys are preserved when rewritten" applies only to the
    journal** (2026-07-25, CFG-004). It contradicts §11's `extra="forbid"` as
    written. The contradiction is narrower than it looks: manifests are immutable,
    references are replaced wholesale, and the catalog is rebuilt from scratch, so
    the transaction journal is the only artifact that is ever read, modified, and
    written back — the only place an unknown key could be destroyed. Every model
    forbids unknown keys and reports them by location, which satisfies "reported
    and never silently dropped". The preservation half is a journal-rewrite
    concern and belongs to `STO-010`, which is where that rewrite is implemented.

21. **A Pydantic validator must raise `ValueError`, never `TypeError`**
    (2026-07-25, CFG-004). Found by a test: Pydantic converts `ValueError` and
    `AssertionError` into validation errors and lets everything else propagate, so
    a `TypeError` raised for a non-string digest escaped `load` as a bare
    exception instead of being reported as a coded problem naming the field — the
    one thing `load` exists to guarantee. Both sites now raise `ValueError` with a
    `# noqa: TRY004`, since Ruff reasonably prefers `TypeError` for a type check
    and is wrong about it here.

22. **`config validate` reports `token_source`** (2026-07-25, CFG-005).
    `docs/cli.md` §4.1 listed only the fingerprint and two counts. The command an
    operator runs before enabling the timer should also answer "did the credential
    resolve, and from where" — otherwise the first evidence that a systemd
    credential is missing or that `--token-file` is unreadable arrives during a
    scheduled run hours later. The field carries the *source* name only
    (`token-file`, `systemd-credential`, `none`), never the value, which is what
    `docs/security.md` T-07 permits. `docs/cli.md` §2 and §4.1 updated in this
    commit.

23. **A whole-table constraint is not reported alongside a bad field in the same
    table** (2026-07-25, CFG-005). Pydantic does not run a `mode="after"` model
    validator when a field in that model already failed, so a configuration with
    both a bad `storage.archive_root` and `maximum_revisions = 9` reports
    `HFCFG006` now and `HFCFG011` only after the path is fixed. This narrows
    `docs/configuration.md` §8's promise that an operator fixes one file once, and
    it is recorded rather than worked around: making it complete would mean
    turning every table-level rule into a field-level one, which would lose the
    cross-field checks that are the reason those validators exist. The behaviour
    is asserted in `tests/unit/test_config_validate.py` so it cannot change
    silently.

24. **A partially implemented command reports what it probed, not a placeholder**
    (2026-07-25, CFG-006). `doctor` is specified with fourteen checks; Phase 2 can
    perform three of them, because the rest need the storage layer or the Hub
    adapter. Two ways to handle that were rejected: emitting the missing checks
    with a `skipped` outcome and a "not implemented yet" detail, which puts
    development state into operator-facing output, and emitting them as `pass`,
    which is a lie. They are simply absent until the package that performs them
    lands, and the `checks[]` array is ordered and open-ended so appending is the
    natural way to add one. `--read-only` is the exception and is *not*
    development state: `docs/cli.md` §2 requires it to say that hardlink, rename,
    and ref-replacement capability are unproven, so those three entries are real
    output that will still be there at v1. The same rule governs `plan` and
    `status`: each reports the fields it can determine and omits the rest, and the
    checkbox above names the work package that completes each one.

25. **The taxonomy is checked against the documents that define it, in both
    directions** (2026-07-25, CFG-007). A table of codes in a document and a table
    of codes in a module drift the moment someone edits one. `test_taxonomy.py`
    therefore parses `docs/cli.md` §5 and `docs/configuration.md` §8 and asserts
    that every documented code classifies as its own section header says, that
    every family the code knows about appears in the documents, and that the
    `HFCFG` range has no gaps. It reads only the leading cell of a table row:
    §5.3's prose cross-references `HFVER002` while explaining how it differs from
    `HFSYN003`, and a mention is not a claim about which section a code belongs
    to. Classification is by family prefix rather than by a per-code table,
    because a code's family already determines its exit and a second table would
    be a second thing to keep in sync.

26. **The `--json` envelope is a model, not a dict** (2026-07-25, CFG-007). It is
    not durable — nothing on the archive is ever this shape — but it is a contract
    with automation, and it was being assembled by hand at each call site with the
    `outcome`/`exit_code` agreement enforced by a conditional expression. It is
    now `reporting.Envelope`, which refuses an undocumented exit code, an
    `outcome` that contradicts it, `success_with_warnings` without warnings, and a
    failure carrying no errors. It keeps its own `schema_version`, separate from
    the durable schemas, because an invocation record and an archived manifest
    change for different reasons.

27. **`archive init` writes the configured archive id; it does not mint one**
    (2026-07-25, STO-000). Plan §6.2 steps 4 and 7 had initialization generate a
    UUID and print it for the operator to paste into configuration. That cannot
    be reconciled with the rest of the contract. `--archive-root` must equal
    `storage.archive_root` (`docs/cli.md` §2), so configuration is loaded and
    fully validated before anything happens — and `storage.archive_id` is a
    *required* canonical UUID (`HFCFG012`), so the operator has necessarily
    already chosen one before `archive init` can run at all. Minting a second
    would write a sentinel that disagrees with configuration, which is precisely
    the state `FS-03` calls fatal and never repairable, and would leave the new
    archive unusable until an unrelated file was edited. The UUID is therefore
    provisioned into configuration — which is what the `"replace-with-provisioned-uuid"`
    placeholder in `docs/configuration.md` §4 has always asked for — and
    `--archive-id` is kept as the same deliberate restatement `--archive-root`
    is: the one irreversible command does not take its inputs from a file alone.
    Disagreement is `HFARG002`. Plan §6.2 and `docs/cli.md` §2 updated in this
    commit.

28. **`STO-000` lands the primitives it cannot be correct without** (2026-07-25,
    STO-000). It is the first package of Phase 3 but depends on three later
    ones: mount and filesystem-type detection (`STO-001`), reading the sentinel
    and comparing its id (`STO-002`), and atomic writes (`STO-005`). An
    initialization that cannot prove its target is NFS, cannot tell an
    initialized archive from unknown content, and cannot write its sentinel
    without a torn-write window is not a *guarded* initialization, so those
    pieces are here in their minimal form. The packages keep the rest of their
    scope: `STO-001` the shared preflight every mutating command runs plus
    `doctor`'s mount checks, `STO-002` that preflight's sentinel gate, `STO-005`
    the model-aware JSON and reference writers built on `atomic_write_bytes`.

29. **`archive init --inspect` exits `0` for an already-initialized archive**
    (2026-07-25, STO-000). `docs/cli.md` fixed no exit code for `--inspect`.
    Its two real uses both want a non-zero on a bad answer: confirming a target
    is clean before initializing, and confirming a failed initialization left
    only known partial paths so a retry is safe. But a healthy initialized
    archive is also "not initializable", and exiting `20` there would make the
    command useless as a routine check. So `--inspect` exits `0` when the target
    is initializable **or** correctly initialized, and `20` when it is neither —
    unknown content, symlinks, the wrong filesystem, or a malformed or
    mismatched sentinel. Recorded in `docs/cli.md` §2.

30. **A leftover `.tmp-` sibling is part of the known-empty layout contract**
    (2026-07-25, STO-000). §6.2 permits retrying a failed initialization once
    `--inspect` confirms the partial paths match the contract, but a crash
    between the sentinel's temporary write and its rename leaves a file the
    contract did not name — so the retry would refuse as "unknown content" and
    the archive could never be initialized without manual cleanup. Writing the
    sentinel in place instead was rejected: `O_EXCL` makes its *appearance*
    atomic but not its *contents*, and a truncated sentinel is worse than a
    stray temporary, because it looks like an initialized archive. The temporary
    is therefore recognised by its `<name>.tmp-<16 hex>` grammar, reported by
    `--inspect`, and removed by the retry. It is the only deletion this command
    performs and it is on a file the command owns, so `FS-19` is intact.

31. **`published/` adoption compares ownership against the archive root**
    (2026-07-25, STO-000). §6.2 and `FS-22` adopt a pre-existing `published/`
    only when "its ownership and mode already match §20.1", but §35.3 rules out
    the obvious implementation: the Mapall writer export presents NAS-side ids
    (`3001:3002`) that have no local account, so there is nothing local to
    compare `st_uid` with. "The same identity owns `published/` as owns the
    archive root" is the same rule in a form the writer can evaluate, and it
    fails exactly when the intended one would. The policy takes two
    `os.stat_result` values rather than two paths, which is what lets it be
    tested for identities this host cannot create — `tyler` cannot `chown` to
    3001. `docs/architecture.md` `FS-22` updated in this commit.

32. **A write that fails after every check passed is `HFMNT008`** (2026-07-25,
    STO-000). Everything `archive init` proves beforehand is a read, so a
    server-side read-only export presenting `rw` client options, a reached
    dataset quota, or the NAS going away mid-command are all discovered only by
    writing. Without a mapping those surface as an `OSError` traceback from the
    middle of a half-created layout. `docs/cli.md` §5.2 defines `HFMNT008` as a
    required directory being missing or failing the effective-write probe, which
    is the same condition observed a different way, so the whole mutation is
    wrapped and reported under it at exit `20`. The message names the failing
    path and points at `--inspect`, because decision 30 is what makes the retry
    safe.

33. **The check runner is its own module, `preflight.py`** (2026-07-25,
    STO-001). Plan §7's module list has no home for it, and neither of the two
    obvious ones works. `cli.py` is wrong because the runner is not the CLI's:
    a mutating command's hard gate uses the identical checks in the identical
    order, and a scheduled `sync` must not have to route through the command
    surface to reach them. `storage.py` is wrong because the table includes
    `configuration`, `credential`, and the four `hub_*` checks, which are not
    storage — and because `storage.py` is at 973 lines, near the point where one
    module carries everything. So the *primitives* stay in `storage.py`
    (`probe_writability`, `same_filesystem_problems`, `is_initialized`) and the
    *ordering, outcomes, and gate* are `preflight.py`, which is also where the
    normative `docs/cli.md` §2 table lives as `CHECK_ORDER`. Plan §7 updated in
    this commit.

    Sizing note for the next package: `storage.py` is now 973 lines and
    `STO-002` adds to it. The §36 protocol's instruction stands — split
    `archive init`/`--inspect` into `archive.py` at that point, with its own
    decision and plan §7 amendment. It is not done here because it would mix a
    large move into the commit that implements the preflight.

34. **`archive_root` reports `HFMNT015` as well as `HFMNT001`** (2026-07-25,
    STO-001). `docs/cli.md` §2 row 2 proved "the archive root exists" and named
    only `HFMNT001`. A symlink exists, and so does a regular file; neither is an
    archive root, and `mount_problems` already reports both as `HFMNT015`.
    Putting that under a later check was considered and rejected: `mount_point`
    would then fail for a path whose problem is not its mount, and the check
    that actually looked at the root would have reported `pass`. Row 2 is now
    "exists and is a directory" with both codes, which is what it always
    verified. `docs/cli.md` §2 updated in this commit.

35. **A skipped check has three meanings, and the gate reads them differently**
    (2026-07-25, STO-001). `docs/cli.md` §2 described `skipped` for two
    situations — `--read-only`, and an archive that is not initialized — and
    plan §19 requires the same checks to be a *hard* preflight for every
    mutating command. Those two cannot both be satisfied by one boolean: an
    uninitialized archive is a fine answer for `doctor`, which reports it and
    exits `0`, and an impossible one for a command that is about to write.

    A third case appeared while implementing rows 2–5. `mount_problems`
    short-circuits, so with an absent root nothing is known about its filesystem
    type; reporting `pass` there would be the one wrong answer, and reporting
    `fail` would invent a failure that was never observed.

    So a check carries the reason it did not run, and only the "not initialized"
    reason blocks a mutating command — as `HFMNT008`, which `docs/cli.md` §5.2
    already defines as a required directory being missing, which is exactly the
    condition. A precondition skip adds nothing, because the failure that caused
    it is already its own entry in the same report; restating it three times
    would make a single missing directory look like four problems.
    `require_storage_safety` deliberately takes no `--read-only` option: a
    command about to write has no business asking for one, and an option that
    silences a check is an option that lets one through. `docs/cli.md` §2
    updated in this commit.

36. **`archive.py` split out of `storage.py`** (2026-07-25, STO-002). The
    `STO-001` sizing note said to do this before adding to a 973-line module,
    and the cut turned out to be a real boundary rather than a line count.
    `storage.py` is now what a command must *prove about the mount* and the
    primitives that *act on it durably* — the mount table, atomic writes, the
    write probe, the same-filesystem proof, and reading the sentinel.
    `archive.py` is the one command that brings an archive into being: the
    known-empty-layout walk, `published/` adoption, `--inspect`, and
    `initialize_archive`. Each is now under 550 lines and neither imports the
    other's concerns.

    `_read_sentinel` became `storage.read_sentinel` in the move, because both
    sides need it: `archive.py` to tell an initialized archive from unknown
    content, and `preflight.py` for check 6. It reads the archive's identity off
    the mount, which is a storage question; deciding what a mismatch *means* is
    still the caller's. `tests/unit/test_storage.py` split the same way, into
    `test_archive.py` for the module and `test_archive_init.py` — which already
    existed — for the command. Plan §7 updated in this commit.

37. **The `sentinel` check owns "the archive is not initialized"** (2026-07-25,
    STO-002). `docs/cli.md` §2 puts checks 6-12 behind an initialized archive
    and has each report `skipped` with that as the reason, which is right for
    `doctor`. It is not enough for the gate: `STO-001` had checks 7 and 8 each
    carry `HFMNT008` for the condition, so a mutating command against an
    uninitialized archive would have reported two problems, and every later
    package would have added another.

    Check 6 is the one that actually observes it — the sentinel's absence *is*
    the condition, and the sentinel is written last, so nothing below it can be
    said either (`FS-23`). It therefore carries `HFMNT005` for the gate and the
    checks beneath it skip silently. One missing archive is one problem, with
    the code `docs/cli.md` §5.2 already assigns to exactly that condition.

38. **`HFWRN005` fires at a tenth of the reserve** (2026-07-25, STO-003).
    `docs/cli.md` §5.6 defines the warning as "free space approaching the
    configured reserve" and fixes no threshold, so the application has to choose
    one. It is expressed as a percentage *of the reserve* rather than as an
    absolute figure, because a deployment that reserved 100 GiB and one that
    reserved 1 TiB want to hear about it at different points, and the reserve is
    the only number that already scales with the deployment.

    A reserve of zero therefore never warns. That is the right reading of an
    operator who set both minimums to zero: they turned the reserve off, and a
    warning about a reserve that does not exist has nothing to say.

    The margin is also measured after `needed_bytes`, not before, so a run that
    is about to consume most of the headroom warns even when the archive looked
    comfortable before it started.

39. **`free_space` does not need an initialized archive** (2026-07-25, STO-003).
    `docs/cli.md` §2 put checks 6-12 behind an initialized archive in one
    sentence covering a range. It is right for 6-11, which all read or write
    archive-owned paths, and wrong for 12, which calls `statvfs` on the mount
    point. Reporting it as `skipped` would withhold a real answer from the
    operator most likely to want it — someone sizing the dataset *before*
    running `archive init` — and would do so for no reason, since nothing about
    the measurement depends on the layout existing. The sentence now reads 6-11,
    with check 12 called out separately. `docs/cli.md` §2 updated in this commit.

40. **`locking.py` added to the plan §7 module list** (2026-07-25, STO-004).
    The lock is neither archive storage nor a `doctor` check: it lives on local
    tmpfs under `/run/hfcache` (`AD-17`), it is never reported by `doctor` —
    which does not mutate and must not take it — and it is *held* for the
    duration of a command rather than checked once. `storage.py` is about
    proving and writing the NFS mount and `preflight.py` is about the check
    table, so it belongs in neither. Plan §7 updated in this commit.

    Two implementation points are worth recording. `flock(2)` rather than a pid
    file, because the lock lives on the open file description and the kernel
    drops it when the process dies — including under `SIGKILL` or an OOM kill —
    so a crashed sync cannot leave a lock that an operator has to clear by hand.
    And the holder record inside the file is diagnostic only: nothing reads it
    to decide anything, it exists so a command that gives up waiting can say
    *who* it waited for. It is cleared on release so a later refusal never names
    a process that has already finished.

41. **The capability probes stay inside `.store/health/`** (2026-07-25,
    STO-007). Plan §14.2 asks `doctor` to prove "a regular file can be
    hardlinked between private and published test directories", which reads as
    an instruction to create a test directory under `published/`. The probes do
    not do that, for two reasons.

    The first is that it does not match what publication actually does. A
    hardlink is made from a cache blob into `.store/staging` (§14.1 step 4), and
    what reaches `published/` is the *tree*, by rename (§13.2 step 15). Nothing
    is ever hardlinked into `published/`, so a probe that linked into it would be
    proving something the application never does.

    The second is that `doctor` takes no lock. A transient probe directory under
    `published/repos/` would be visible to a concurrent catalog rebuild or
    `verify`, and would be reported by `archive init --inspect` as content the
    application did not create. `docs/architecture.md` §5.1 designates exactly
    one probe area — `.store/health/probe-<probe-id>/` — and every probe stays
    inside it. Check 8 has already proven the whole layout is one filesystem, so
    a hardlink and a rename demonstrated there hold for the dataset.

    `_remove_probe` now removes the area with `rmtree` rather than entry by
    entry, since the capability probes build subdirectories in it. That stays
    inside `FS-19`: `probe-<16 random hex>` was created by this process moments
    earlier and cannot contain anything the application did not put there.

42. **Checkpoint evidence names paths by key suffix** (2026-07-25, STO-010).
    `TX-03` requires each checkpoint to carry re-observable evidence and
    requires recovery to confirm it by looking at the filesystem rather than by
    trusting the record. `docs/architecture.md` §7.3-§7.7 describe that evidence
    in prose — "published tree path, file count", "`.store/trash/<txn>/` absent"
    — which is enough for a human and not enough for code.

    The convention that makes it mechanical: an evidence key ending `_path`
    names an archive-relative path that must still exist, `_paths` a list of
    them, and `_absent` a path that must *not* exist. Everything else is left to
    the package that knows how to interpret it, because a file count or a digest
    means nothing without the artifact it describes.

    Suffixes rather than a fixed key list, because the same checkpoint carries
    different paths in different operations and a list would have to be extended
    every time one is added — which is exactly the kind of table that goes stale.
    The suffix travels with the key, so a caller that names a path correctly gets
    it checked for free. Evidence keys are durable, so this is a format decision
    and not only an implementation one.

43. **The recovery report is a run report** (2026-07-25, STO-011).
    `docs/architecture.md` §7.7 requires `recover --apply` to record a
    `recovery_report_written` checkpoint, but no document said what that report
    is. Three options were considered. Reusing the §6 run report unchanged does
    not fit — its body is per-repository sync results, and a recovery resolves
    transactions rather than repositories. Treating the journal itself as the
    report is a dodge: the journal is evidence of what happened, not a report an
    operator reads. Inventing a separate location would put a third kind of file
    somewhere `list` and `status` do not look.

    So it is `RecoveryReport`, the §6 envelope with a `remediations[]` body,
    written to the same `runs/` path — exactly the relationship the verification
    report already has to the run report, and for the same reason: one operator
    reads all three, so the shared part is one class rather than three that
    drift. Documented as `docs/schemas.md` §12 in this commit.

    `outcome: "pending"` is recorded for a remediation deliberately left alone —
    staging too young to be certainly abandoned. That is a real answer and worth
    persisting: an operator reading the report should see that recovery
    considered the directory and chose to wait, not that it missed it.

44. **`projected_publication_bytes` is measured under the configured mode, not
    hypothetically under copy** (2026-07-26, HUB-004). `docs/cli.md` §2 asked
    `plan` for "the projected publication bytes in copy mode", which reads two
    ways: the field means something only in copy mode, or the field always
    reports what copy mode *would* cost. The second was rejected. `plan` is the
    command the dataset quota is sized from, so the number it reports has to be
    the number the archive will actually consume — and under the default
    `hardlink` mode that is zero, because a hardlink points at a cache blob
    already on the dataset (`AD-11`).

    Nothing is lost by not reporting the hypothetical: copy mode's cost is
    exactly `logical_bytes`, which is in the same payload. A deployment weighing
    the switch reads it off the field beside it. `publication_mode` is reported
    with it so the zero is explicable rather than looking like a missing
    measurement. `docs/cli.md` §2 and §4.1 updated in this commit; §4.1 now names
    every field of the payload rather than summarizing it, since automation keys
    on them.

    The cost model itself is `publication.projected_publication_bytes` rather
    than a conditional at the call site, because plan §19 item 9 makes the same
    number part of a sync's free-space gate. An estimate an operator reads and a
    reserve a sync enforces that disagreed about what publication costs would be
    a capacity failure discovered mid-download.

45. **An empty tree listing is reported; an entry with no path is refused**
    (2026-07-26, HUB-004). `HFHUB008` is "repository tree metadata missing or
    incomplete", and two conditions could claim it. A revision containing no
    files is *not* one: it is a truthful answer to what the metadata call asked,
    `plan` reports it as `0 files`, and whether an empty revision is worth
    publishing — and consuming a retention slot — is a decision for the package
    that publishes one, not for the call that reads the metadata.

    A file entry with no path is the other, and it is refused. The listing is
    what plan §13.2 step 7 calls the exact repository path set, and every later
    step joins those names onto a filesystem path; an empty one would arrive at
    that join looking like a legitimate name for the tree's own root. The
    previous code coerced it to `""` and carried on. This is narrower than the
    path grammar in `hfcache.paths`, deliberately: the grammar answers "is this
    name safe to join", and this answers "did the response contain a name at
    all", which is a question about the library's shape and belongs at the seam.

46. **A hashing failure's error class must match its code's family** (2026-07-26,
    HUB-007). `sha256_file` took the caller's `code` and always raised
    `IntegrityError`, so `publication.stage_file`'s three calls — which correctly
    pass `HFSYN005` — would have exited `40` for a condition `docs/cli.md` §5.3
    classifies as `30`. Nothing had surfaced it yet, because publication is not
    reachable from a command until `HUB-009`; it would have arrived as an
    operator being told the archive is corrupt when a download failed.

    Two ways an exit is determined coexist in this codebase: `HfcacheError`
    subclasses carry one as a class attribute, and `taxonomy.classify` derives
    one from the code's family. They are not redundant — the first is what a
    raise site produces and the second is what the published tables promise — so
    they have to agree, and nothing was making them. `sha256_file` now takes
    `error` alongside `code`, which is exactly the shape decision 19 settled for
    reading a durable artifact, and `tests/unit/test_hashing.py` asserts
    `caught.value.exit_code == classify(code)` for every pairing used in `src/`.

    A single `error_for(code)` factory was considered and rejected: it would let
    a raise site name a code from a family it has no business raising and get a
    plausible-looking error back. Passing both makes the pairing visible at the
    call site, which is where a mistake is legible.

47. **`HFSYN009` added for content that cannot be read while hashing**
    (2026-07-26, HUB-007). Plan §13.2 step 9 hashes newly introduced objects and
    §16.1 requires a hash failure to prevent publication, but the taxonomy had no
    code for the failure itself. The nearby ones are all wrong: `HFSYN001` is the
    local-only completeness check specifically, `HFSYN003` is a size mismatch,
    `HFSYN004` is an unsafe path, `HFSYN005` is staging construction — which has
    not started yet at step 9.

    `HFVER006` ("object could not be read") describes the condition exactly and
    is still wrong, because it exits `40`. Nothing has been published when step 9
    runs, so no archive content is wrong; the run failed and the next one will
    retry. That is a `30`, which is what put the code in the `HFSYN` family.

    Added to `docs/cli.md` §5.3 in this commit. `tests/unit/test_taxonomy.py`
    reads that table, so the code is covered in both directions the moment it is
    published.

48. **`hfcache list` lands at `SYNC-002`** (2026-07-26). Plan §11 requires the
    command and plan §28 gives it no work package — the only v1 CLI command with
    no home. Three placements were considered. `CFG-006` implemented the
    read-only command surface and would have been the natural place, except that
    at Phase 2 there was nothing published to list, so the command could only
    have been written against a layout that did not exist yet. Phase 8 is
    documentation and release; adding a command there would mean shipping a
    runbook before the thing it documents. `SYNC-002` is where the archive first
    holds revisions an operator would want an inventory of, and where the sibling
    read commands — `status` reporting the same references — are being completed.

    `list` deliberately reads manifests and references and never the catalog,
    which `docs/cli.md` §2 already required and which is the reason it belongs
    beside `status` rather than beside the catalog rebuild: an operator taking
    inventory during an incident is exactly the person who cannot rely on derived
    state (`FS-16`). Selectors restrict the *configured* set, so naming one
    repository never hides an unmanaged one the operator did not ask about.

49. **A verification finding may name no publication instance, and `HFARG004`
    now covers a revision or a run this archive does not hold** (2026-07-26,
    `VER-001`). Two small contract amendments, both forced by the same thing:
    `verify` is the command an operator runs when the archive is *already* known
    to be wrong (`docs/architecture.md` §7.9), so it has to keep answering about
    artifacts it cannot read.

    `docs/schemas.md` §7 typed `finding.publication_id` as required. A reference
    that will not parse names no publication instance, so there is nothing to
    put there — and attributing the finding to whichever instance directory the
    filesystem happens to hold would assert exactly what the unreadable
    reference failed to say. The alternative was to raise instead of reporting,
    which would abandon every other repository in the run because one reference
    file is corrupt. The field is now nullable, `docs/schemas.md` §7 says the
    single case it is null for, and every other finding still carries it.

    `docs/cli.md` §5.1 defined `HFARG004` as a selector naming a repository
    absent from configuration. `verify --revision TYPE:ID@SHA` and
    `verify --new --run-id ID` can both name something that is not there, and
    neither is an integrity failure: a mistyped SHA reported as exit `40` would
    tell a scheduler the archive is corrupt because somebody typed one wrong
    character. The row now reads "an argument names something the archive does
    not hold", which is one condition with three instances rather than three
    codes for one mistake. `tests/unit/test_taxonomy.py` parses that table, so
    the widened row is checked in both directions.
