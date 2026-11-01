# WEB-009: Capture publication-pinned README presentation records safely

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `be7a15f7e55a0a8996403f4c8b8f7dfefd32a248e751f2e072329b156ca7909b`,
original content SHA-256 `1c6c97306a2a6593f8d3a39f4d84b4814a4e336f286bc33f94bb42bc0b7b1c3f`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P2 |
| Depends on | [WEB-008](web-008-atomic-configuration-application.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-009: capture bounded publication-pinned README cards` |

## Read before implementation

catalog_capture/extractors/models/read/write budgets; sync/repair lifecycle; publication manifests; discovery and adjunct schema contract; card specification.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Add the independently versioned card adjunct and central layout builders under the approved supplemental namespace. Capture root manifest-listed README.md in existing writer-owned post-publication sync/repair and technical=true offline refresh work. Read no code, loaders, remote URL, arbitrary path or tensor payload. Enforce no-follow regular-file/descriptor stability, source identity, source/presentation byte bounds and shared aggregate work limits before allocations.

Retain sanitized inert Markdown separately from structured declarations. Record source expected digest and presentation identity without conflating them; implement and document bounded README source-digest comparison as a narrow metadata check where selected. Capture failure/mismatch/unsupported/oversize states warn without undoing valid publication integrity. Missing README is normal. Redact registered/recognized credentials before durable presentation; do not alter immutable source/manifests or structured observations to hold the body.

Keep old sync/refresh request and result shapes: technical=true now additionally captures presentation under a documented adjunct contract. No redundant refresh endpoint or cards flag unless actual compatibility forces a separately recorded adjustment. Whole-record atomic writes follow existing initialized archive/preflight/writer-lock/journal-safe rules, preserve unknown records, and never use GET as refresh. Bound serialized record and aggregate count/storage; no new global index or automatic garbage collector.

## Unit and component validation

Test safe/hostile paths, symlinks/special files, descriptor changes, manifest mismatch, invalid UTF-8, exact limits/Unicode/JSON expansion, secrets, unsupported versions, atomic write failures and stale adjunct membership. Assert immutable evidence byte stability.

## Integration validation

Run real sync/repair/refresh service fixtures for model/dataset/absent README and retained-SHA recapture. Inject card failures after successful publication and verify existing outcome/warning classification and old response validation.

## Functional validation

In the Caddy/API fixture run the existing metadata-refresh workflow over owned retained publications, then inspect the resulting adjunct through test evidence. Confirm no Hub contact and no altered verification confidence; UI display arrives in WEB-010/014.

## Human documentation deliverables

Write readme-cards provenance/refresh/limitations guide sections; update discovery, schemas, security, invariant adjunct exception and compatibility notes with precise bounds and capture effects.

## Acceptance

Cards are bounded derived records tied to exact publications; capture executes no repo code/network; old evidence/results remain compatible; partial capture is explicit and never turns into archive corruption or silent success.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

Started2026-10-25 after WEB-008 `ad3275a` and a clean checkout. Completed the
accepted ADR142/schema18.1 design: independent strict card model and paths,
bounded source/presentation grammar and secret suppression, guarded atomic
storage, joined sync/repair and existing technical refresh. Old public requests,
results, observation fields/counts and immutable publication evidence remain
unchanged. The existing wire audit was reviewed and regenerated after additive
internal model/path changes; its161 public definitions remain unchanged.

The installed acceptance uses the application profile: real built SPA, trusted
TLS and real Caddy, installed wheel and actual API/operation runner. Its only
storage substitutions are the existing owned mount-table/local-lock seam, labelled
`LOCAL_NFS_METADATA_SIMULATION`. This is not platform/NAS acceptance. Existing
native/rootless/helper platform evidence remains scoped to its original tasks.
No production/NAS/installed predecessor interface, deployment, merge, push or tag action occurred.
No new runtime dependency was added. Exact card GET and rendering remain
WEB-010/014; configuration-backed tags and original operation handles are retained.

## Completion evidence

2026-10-25, WEB-009, this commit; parent `ad3275a`.

- **Strict source gate:** `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)`
  exits0 in1413.458s:8500 Python tests,52 unrelated opt-in deselections,581
  historical frontend unit/110 mounted Firefox,2834 web unit/2894 combined component,
  strict lint/types/negative fixtures, two built-shell browser tests, real API
  React reads and all three locked wheel-install profiles. Web coverage is
  95.16% lines/92.59% branches/92.36% functions. No required skip. Human docs211
  and helpers27 pass. Evidence directory
  `/var/tmp/web-009-validation-xv0sm3nn/gate1/`; result records1383 unchanged
  source inputs at snapshot
  `741fe59cc7ac4edc0248d594f35bc53a064c3707d9e43b9403e841f369441e59`.
  Gate log SHA256
  `918f7b5a6670b05d6fd84619501c3d72f982281e551522517056bd905dadd18b`.
  Only five explicitly recorded plan/task/progress/acceptance bookkeeping files
  are excluded; final preservation proof rechecks every other hash and mode.
- **Capture/schema/storage units:** `test_catalog_cards.py` and
  `test_repository_cards.py` cover exact source/root identity, full original
  source secret checks, inert code/links, frontmatter/image omissions, invalid
  UTF-8, raw/Unicode/JSON/record ceilings, shared attempts/read/work/write budgets,
  no-follow regular sources, descriptor/path changes and fresh SHA mismatch.
  Existing/future/unsafe/malformed cards refuse preservation-safe replacement;
  actual temporary/fsync/replace fault cuts leave a whole old/new record.
  Golden old schemas remain unchanged; the new card golden is independent.
  All named nodes are mapped in `support/web-ui/acceptance-evidence.json`.
- **Lifecycle/API integration:** real joined sync and repair capture model,
  dataset and absent README with exact replacement identity; retained recapture
  does not download. Extractor/storage failures preserve successful publication
  and structured observations. Existing technical refresh executes once under
  its original key; card failures use HFWRN011/partial without inventing failed
  observation counts or verification confidence. Focused394 model/storage,
  181 capture/extractor/logging/adversarial and156 lifecycle/API tests passed;
  the frozen full gate covers them all. Source fixtures are not installed proof.
- **Artifacts:** build exits0 in63.703s; directory
  `/var/tmp/web-009-artifacts-source1-c5e4551dc460/stock.json` records exact
  sources and artifact hashes. Wheel0.2.12 SHA256
  `8e4b202768ee55a34e1d1b018eceef61c36a81615e115afa981eb81b4b3296ff`;
  UI manifest `c682f8ce3d98a6b44c49bd70d09299666d79264dfe8b1a5b499bd14b7dbaa84e`;
  UI tar `fcc1da1a8cc5b1462bec4790a74282f9f94b912b410929339047f808803fcf33`.
  Shared stock API/UI image
  `sha256:01ef3ffc67d3aa84d7447c0a911c59c3b9fcee3b7b1a150b248a674d2aaa176c`
  passes the pinned UBI10 micro/no-runtime-Node foundation audit. Version0.2.12
  is disclosed disposable fixture metadata projected in two TOML fields,
  not a release; the builder's rootless0.2.13 intention was not installed.
  Installed112 Python package files match this wheel.
- **Real application functional:**
  `rtk python3 .scratch/web-008-call-guest.py --script /home/webfixture/web009-inputs/web-009-run-owned-functional.py --log /var/tmp/web-009-validation-xv0sm3nn/functional-capture3.log`
  exits0 in21.287s. Three one-attempt Chromium156.0.8078.4 cases load the built
  Basic-authenticated UI, submit one existing writer technical refresh and
  reobserve its original result. Refresh uses a real REST writer credential in
  browser memory; this does not claim the later job UX. Original operation
  `fded74737798e5474483fdae0e90acb5` is never replayed. Seven owned publications
  produce model/dataset present, absent, secret-unsafe, oversize and digest-failed
  states; a preexisting schema999 card keeps its original bytes/inode. Result
  remains partial with7 observation writes,0 failed records and1 incomplete
  technical observation; card warnings do not change those meanings.
  Independent inspection proves full publication bytes/metadata unchanged,
  no repository-code canary, and a real subsequent catalog GET does not capture
  or rewrite metadata. API runs non-root in an actual distinct private network
  namespace with only loopback and AF_UNIX-only service restrictions; no Hub
  contact is possible. All14 browser requests stay at the exact trusted origin,
  with no interception, invalid request or observer overflow. Actual Chromium
  sandbox/renderers are verified. Browser/container/API/Caddy all exit normally;
  original PIDs/cgroups/endpoints close and five original infrastructure pairs
  remain unchanged. No storage/platform/production acceptance is inferred.
  Local evidence copy `functional-capture3-evidence.json` SHA256
  `4eebd0d29731731ed6a7b86c1fa73d0022d629dcf58fc8632cb03f1d895ca373`
  is under `/var/tmp/web-009-validation-xv0sm3nn/`. Original guest result
  `/home/webfixture/web009-runtime/RESULT-71c865837e274513a3fea29db1205edb.json`
  SHA256 `c97bb817114bf73dc28bfa0a0d88897eed54dc72a970c6b6fa67797e74a2b6df`;
  browser report `058c75d9c32cb7e801e92d9e1f600018f71c982574a610e0514e2eacb16b2eaf`;
  independent inspection `755634618cc19cea48928aea05bd56b47c1f87c7d6ec5c4983ff365b9474ce17`.
  Private fixture/browser/coordinator SHAs are respectively
  `bbc211e4287690bc13bd2d4220878dcf07e2ebf96ddca31fa7b962d636ac2739`,
  `a3427686a9b1deb0b31a7ebffa9ef445e399f3d725051c6cf746cf1c6c97f662`,
  `c6644d1be5dc7ea46a39036d2850d5465394991b588f6327819de629b985b505`.
- **Retained failed attempts:** capture1 exits1/3.038s before API execution
  because systemd cannot execute the home-directory interpreter. Independent
  closure proves no API process/cgroup. Code was copied to a normal root-owned
  `/opt` prefix with existing default labels, preserving the original install.
  Capture2 exits1/32.418s: the API starts but the private Caddyfile's inline
  log stanza fails parsing; no browser or refresh occurs. Original cleanup
  stops at that failure and leaves the API active. A separate positively joined
  normal stop proves original API/cgroup closure; both original false/unknown
  results stay unchanged. Multiline Caddy grammar and complete-role cleanup
  are corrected only in ignored fixture code. No SELinux/systemd restriction is
  weakened. Logs/results and independent diagnosis/drain proofs remain in the
  same evidence directory; successful capture3 is a fresh owned cohort.
- **Previous-release drill:** reconstructed binary from exact released source
  `1c685018803a365bbb8b0c1aad4b94709f60e7d7` (not the deployed artifact), wheel
  `b88ffd0f8605d2410a16aa17379eb8a31362310f7143ca07dfab8ebf17bb6503`,90
  installed modules match. Actual old status/inventory/catalog succeed before
  cards; with the new adjunct, status/inventory still succeed but catalog
  refuses exit40/HFVER007. Every archive file's bytes/full identity remain
  unchanged. Initial missing writer-credential startup failure is retained;
  corrected real old authenticated API/CLI completes and drains normally.
  An independent init-inspection check already refused this populated fixture;
  do not attribute that prior refusal to cards. No archive-init command ran.
  Raw `/var/tmp/hfcache-web009-format-_h1hjuvg/RESULT.json` SHA256
  `b4c2e6d525f6060aea6e6fb8e92ccd2d1cd8706705388d0b749557f5cf7453d2`.
  Rollback guidance preserves cards and requires a compatible catalog reader;
  it never deletes metadata to force old startup.
- **Contracts/humans:** new `docs/web-ui/readme-cards.md` and navigation explain
  provenance, fixed unavailable states, exact limits/grammar, refresh effects
  and rollback. Discovery/schemas/security/API/CLI/operations/deployment align.
  INV002/005/018 and AD12/14/15/17/133/142 reviewed; ADR142 and affected older
  decisions carry explicit implementation amendments. No unrelated invariant
  or new dependency is introduced. CARD01–06 are complete; CARD07–12 remain
  with WEB-010/014. See completed progress entry and Operator handoff.
  Next: WEB-010 through the current selector. All production holds remain.

Final bookkeeping validation:78 focused plan/docs tests pass in8.87s; human
documentation211/helpers27 and `git diff --check` pass. Final precommit proof
confirms all1383 regular source hashes/modes match the original green gate
(the listed CLAUDE.md symlink is excluded consistently). Both independent
source-only final reviews report no CARD01–06 gap; they introduce no new
execution claim. Only the five declared bookkeeping files changed after gate.
