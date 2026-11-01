# WEB-023: Verify old clients, durable formats and evidence-preserving rollback

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P5 |
| Depends on | [WEB-022](web-022-installed-functional-acceptance.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-023: verify old clients and evidence-preserving rollback` |
| Model / effort | `gpt-6.1-sol` / high |

## Execution approach

Apply the [shared bounded-testing policy](../support/web-ui/testing-strategy.md#web-023026-bounded-product-testing-and-effort).
Effort rationale: Old-client behavior, durable-state compatibility and safe rollback/drain decisions require joint safety reasoning.
Reuse retained old clients, indexed artifacts and owned fixture copies. Add only missing assertions at existing seams. Escalate for a concrete compatibility, unresolved-state or drain contradiction; preserve evidence instead of retrying effects.

## Read before implementation

docs/agents/release.md format drill; old retained Git source/install targets; new cards/helper/config receipts; migration-and-compatibility.md.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Build/install exact supported old clients from retained Git objects with locked offline closure, then exercise new server's unchanged routes and schemas through Caddy for reader/writer/MCP. Verify old literal config validate/plan, no-Origin bearer auth, operation public fields/canonical idempotency and fourteen-tool behavior. Do not 'fix' compatibility by allowing unknown unsafe schema fields globally.

Drill old binaries against copied fixture state containing new card directories/private helper application kinds and curation records. Determine real compatibility/refusal; record target-specific backup/config/observation requirements. Preserve all unknown/new records and original handles. Test UI-disabled backend-only operation and browser schema/version drift.

Rehearse native/rootless/frontend/application rollback using immutable indexed artifacts on disposable targets only. Prove actual executor drain, common locks, candidate/backup/store retention, coherent UI/backend selection, password/subject continuity and original-op observation. A target unable to observe unresolved state blocks rollback; no force kill, record deletion, auto-replay or overwrite of old artifacts/tags.

## Unit and component validation

Tests cover strict legacy response fixtures, unknown new formats, missing asset behavior, compatibility metadata and rollback refusal paths with preserved state.

## Integration validation

Execute actual old installed clients/binaries, not only serializers, against new server/state fixture copies. Record source/wheel hashes and exact success/refusal classifications.

## Functional validation

In disposable installed targets complete upgrade/open-browser/rollback/reconnect scenarios through Caddy, prove REST/MCP and safe original handles still usable where compatible, and verify incompatible target refuses without data loss.

## Human documentation deliverables

Write human migration/rollback compatibility tables, prerequisites and stop conditions in migration-from-cockpit.md, deployment.md, schemas/discovery/release notes. No production deployment-status claim.

## Acceptance

Compatibility is observed with real target artifacts; rollback either safely works under documented preconditions or explicitly refuses preserving evidence. New durable state is never deleted to manufacture compatibility.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

2026-11-01: WEB-022 is committed as9d11738. Before starting this task, Root
refreshes and applies all13 related bounded-testing/effort amendments against the
adopted product-focused criteria (prepared patch3 SHA
`dccc0d96987c5ee341fecb64a0232831c3c0e5e8a7d95c3b3bca5851fdbf406c`).
The old patch2 and original bundle remain preserved; no mandatory runner matrix
returns. This task uses GPT-6.1-sol/high; routine commands use low effort.

Read-only preparation found the exact previous1c68501/0.2.2 wheel and installed
environment, with90 module bytes equal retained Git and wheel SHA
`b88ffd0f8605d2410a16aa17379eb8a31362310f7143ca07dfab8ebf17bb6503`,
also equal the recorded deployed-source artifact. Native/rootless77/78 indexed
artifacts remain retained. These observations are prerequisites, not compatibility
or rollback acceptance. Root alone coordinates guest/protected/browser effects;
source/local-copy work may be delegated with disjoint ownership. Preserve the
original native SDK pending inode95048553, rootless guard1790 and every original
Apply/unknown record. No new build/download or production change is indicated.

### Checkpoint 2026-11-01: Real old copied-state drill; expired fixture TLS

All13 testing/effort amendments apply after WEB-022/9d11738; cheap docs/plan/diff
checks pass0 (222 human docs/29 helpers,9 plan tests). The retained old-wheel
runtime1c68501/0.2.2 reads the exact owned copied state in
`.scratch/web-023-local-copy-inputs/`:136 source files/two manifests stay byte
identical. Ninety installed modules equal old Git; wheel SHA remainsb88ffd0f.
Actual probe exits0 in~0.9s; result SHA
`84fcb7f0723a4ea3434f3b2bed27f3d3368e1540d6315cc1e0bbdfc2bfd94d41`
at `.scratch/web-023-old-copy-readers1-result.json`. Its95 raw reader observations
are a finite file inventory, not the95 acceptance scenarios. Old readers accept
44 TOMLs, curation/six observations,12 generic receipts/results and the original
scheduled handle (parse only, no replay/lookup/termination inference). Card and
private helper readers are unavailable; new server settings refuse strictly.
The independent mode-restored local archive copy gives HFMNT014/unusable with
15 unknown paths, preserved without deletion; storage here is simulated.

Root's read-only exports preserve native pending inode95048553/288B/hash efffcf4b
and every original guest record. First export attempts refuse before effects on
a text-mode TOML stream and wrong host-outcome basename; corrected bounded
exports retain exact raw bytes and source maps. New human migration guide records
actual classifications; old-client TLS/installed rollback acceptance stays pending.

Actual old-client TLS attempt1 creates no forward because the inherited SSH
ClearAllForwardings option suppresses the explicit loopback tunnel; no request
or Plan is submitted. The narrow corrected transport2 closes normally after the
first native old-reader GET refuses20/HFAPI019. A single strict TLS diagnostic
proves the fixture CA/leaf have expired; no Plan/MCP is submitted or retried.
All original failed results/private keys/transport records remain retained under
`.scratch/web-023-old-tls1/`, `web-023-old-tls2/` and
`web-023-native-tls-diagnostic1/`; all created SSH transports are terminal/-15.

Public X509 metadata independently proves BOTH native/rootless retained fixture
CAs expired2026-11-01T11:19:14Z. No accept-expired, insecure TLS, clock change or
production certificate change is permitted. Root is preparing owned-fixture PKI
renewal preserving original material/inodes and exact role/operation/lock state.
Native can use new credential donors while retaining its old unit; rootless needs
full engine quiescence, a complete metadata-preserving COW secret-store checkpoint
before supported TLS-only replacement, and retained old Caddy container. Existing
manager cache/lock and file-driver paths must be proved first; unsupported clone
or unknown executor refuses. Browser Chromium NSS/Firefox policy trust can reuse
existing public-anchor paths; WebKit additionally needs a separately prepared
public OS bundle and actual strict handshake. These are preparation constraints,
not executed renewal/rollback proof. No guest credential/service change yet.

## Completion evidence

Completed2026-11-01, WEB-023, this commit. All three owned compatibility cases
have executed unit, integration and actual functional evidence. Required Gate1
passes before final ledger/status adoption; closure documents are checked again.
The existing95-case ledger now has88 completed and seven later-owner cases pending.
No optional matrix-runner pass is claimed and no required minimum layer is reduced.

### Exact artifacts and old clients

- Previous deployed-source binary is1c685018803a365bbb8b0c1aad4b94709f60e7d7 /
  0.2.2, wheelSHA
  `b88ffd0f8605d2410a16aa17379eb8a31362310f7143ca07dfab8ebf17bb6503`.
  The retained locked environment has90 installed Python modules equal old Git
  and wheel. No replacement build/download or version-only identity is used.
- Actual old native CLI7 calls and MCP28 calls (all14 tools at root and
  /management) pass in `.scratch/web-023-native-old-tls3/`.
  Rootless status at both aliases and literal validation pass. Its first Plan
  correctly returns10/HFARG002 for disabled-token policy with an explicit Hub
  credential; original lookup proves the failed receipt. A separate all29-disabled
  optional-token candidate validates then returns10/HFAPI007 at installed-authority
  assessment. Both raw aggregates/keys remain preserved; no policy change or
  further Plan manufactures success. Native supplies the positive literal Plan.
  Rootless MCP-only remainder passes28 calls, client result SHA
  `cd003cc31bc7bd8790ac62c085c4e17efc604f92789cd4228d2e403cd3bf53b8`.
  Its inaccurate raw “no POST” label is corrected in an adjacent retained note:
  MCP uses read-only JSON-RPC POST, with no domain job/replay. Native reads existing
  genuine75 reports; rootless reads labelled synthetic report seeds.
- After BOTH77 selection and restored78, actual old CLI original-key lookups
  return the entire unchanged original records: native0dcbe97e succeeded,
  rootlessf302dad7 failed. Retained host entrypoints/results are
  `.scratch/web-023-old-original-lookups77-1.prepared.py`,
  `web-023-old-original-lookups78-1.sealed.py` and their same-name result directories.
  Every narrow owned forward normally closes/-15; no key/token value or hash
  becomes public evidence. The original native SDK handle is never looked up.

### Copied state and release coherence

- The actual old installed runtime reads private exported state and preserves all
  136 source files/two manifests byte-for-byte. Result
  `.scratch/web-023-old-copy-readers1-result.json` SHA
  `84fcb7f0723a4ea3434f3b2bed27f3d3368e1540d6315cc1e0bbdfc2bfd94d41`:
  44 TOMLs, curation/six observations,12 generic receipts/results and scheduled
  handle parsing succeed. Card/private helper readers are unavailable; old server
  configuration strictly rejects host_helper/basic/web. The95 raw reader
  observations are not95 acceptance scenarios. The independent mode-restored
  copied archive gives HFMNT014/unusable and15 unknown paths under a simulated
  NFS mount table; the no-cards control also refuses. Nothing is removed and no
  universal old-daemon-startup or production/NAS claim follows.
- Real native77/78 installed interpreters and rootless77/78 indexed-image parser
  containers validate119 modules each and target-specific UI/server copies.
  Source77 is004ea9e270ef1d17b021e41ded5468eaa7d1e74e; source78 is
  f829857ec045ce4616055e357e7d6aa7047287ca. Their indexed immutable artifacts
  are reused, never relabelled or overwritten. Eight observer/operation/server/
  switch modules are byte-identical, and three helper bootstrap leaves require
  coherent selection. Separate finite no-network/read-only/no-mount/no-secret
  image probes remain stopped and retained. Main package metadata stays0.2.2.
- UI-disabled checks use real ASGI lifespan/Unix HTTP plus separate installed
  base/server/MCP wheel profiles; no guest daemon was switched to that profile.
  Current schema/build drift unit/component checks join earlier actual native
  three-engine dirty-document upgrade evidence through unchanged validators;
  historical native evidence is not a new rootless open-page drift claim.

### Actual native/rootless78→77→78

- Root normally drains actual API/private-worker/helper/Caddy executors, verifies
  pidfd/cgroup/manager/socket closure and hands the original noncreating common
  locks to the stock installers. Native original1722/owned RW disposition and
  rootless original1790/NFSRO/independent guard remain correct for their respective
  fixtures. Retained bootstrap/server/policy/deployment originals precede matching
  publication; the six grants, original keys, both stores, candidates/predecessors,
  scheduled evidence, labels, kernel policy and stronger masks are preserved.
  No forced kill, job replay, archive write, timer enablement or unknown cleanup.
- Native all three stages in both directions pass0. Both actual Chromium/root
  rollback77 and restored78 Library/bootstrap/reload checks pass, same persistent
  profile and stable Basic subject, strict TLS and actual unprivileged sandbox.
  Browser result SHAs621412bf… and47226e81…; the full records and exact retained
  sources are in the ledger. Rootless77 and restored78 browser checks pass0,
  SHAs108e2b37… and55b7f0de… . Exact same-origin read ERR_ABORTED events are retained
  separately; other request errors/5xx/page errors/external requests/domain writes
  remain strict. Contexts, containers and browser cgroups close normally.
- Original rootless77 publish aggregate remains1: duplicate exclusive reload
  evidence filename after binding publication, before any startup. A read-only
  precheck proves exact published/retained bytes and not-yet-invoked starts; only
  the remaining unique reload/helper/bridge starts run. That continuation remains1
  on literal cross-release worker SecurityOpt pathname comparison. Independent
  read-only qualification observes the SAME once-started roles, all UID/GID983,
  allcaps0/NNP1/seccomp2/SELinux, and the same indexed08f97ffb… seccomp bytes at each
  physical release path. API/Caddy options remain exact. Qualification SHA
  `097c66148cbd6eaf3177fc4e23e3d77a59942e6e885fdf55de8bee9e278ebcc4`.
  No publication/start is repeated. Return78 stages all pass0, final stage SHA
  `6489803635b1399c5ac8c71b639874ce5042a12d42dd6527db4a8a0785b6da95`.
  Fresh current78 kernel/TLS capture7 SHA
  `f492ea90440b38e4cc63905411ccbfc9990147891c6f80a5c1bf9cc8ff222e4b`
  confirms all three actual role identities, worker IP denial and exact renewed
  leaf/TLS1.3. Known77 configuration-read503 remains a rollback limitation;
  no unresolved helper-outcome compatibility is inferred.
- Fixture CA expiry is repaired with separate seven-day test PKI and normal
  CA/IP verification, not a TLS bypass or clock change. Native retains original
  Caddy unit and803 state/PKI pins with only two credential donor paths changed.
  Rootless quiesces its engine, checkpoints the complete six-entry secret store
  with metadata-preserving FICLONE and retains original files/inodes; only two TLS
  names change in the canonical copy. Checkpoint/rotation performs no Python
  read/hash of cryptographic private-key bodies or secret-store payloads. Earlier expired TLS, immediate post-stop/start assertions, first missing
  optional Secrets-field qualification and native current78 request-counting
  browser failures remain failed. Later read-only qualification and precisely
  scoped passing flows supply separate evidence, not rewritten aggregates.

### Records, contracts and required gate

The user's latest2026-11-01 instruction excludes further Cockpit plugin work and
validation. The only gate implementation change makes legacy plugin checks
explicit opt-in; strict web/backend/docs/build remain required. Gate-control
regressions cover default omission and retained explicit legacy flag semantics;
no plugin source/dependencies/tests/build are maintained or executed. This
supersedes earlier applicable-Cockpit conditions for current validation.

The [human migration guide](../../../web-ui/migration-from-cockpit.md) records
observed target-specific support/refusal, backups, coherent selection, original
namespaces and stop conditions. Deployment, discovery, schemas, release guidance
and web navigation link it. Reviewed INV001/002/018/021/022 and related existing
ADR140/143/145/153/154/156/158/159 constraints: no runtime dependency, durable
schema or privilege change is introduced by this observed drill. Decision160
records the separate user-directed validation-scope amendment.

Real default test bindings are in the unchanged layer structure of
acceptance-cases/evidence.json: strict client versions/unknown fields, unsupported
private/scheduled schemas, UI-disabled/missing assets, drift, immutable indexes,
coherent stock rollback and unsafe observer/accounting refusal. The required `rtk proxy scripts/check.sh --require-web --with-build` passes0 in 1649.060s:9650 backend tests,4051 combined frontend checks,16 wheel smoke tests, three locked installation profiles, two built browsers and real API read fixture. Frontend coverage is95.02% lines/90.13% branches. All1547 frozen inputs stay unchanged. Legacy plugin checks are excluded per user direction. Exact source freeze SHA `08f7ac8951c9c8ff3053af2da0506b9ec9abe91f7153f03370e06924e56e9828`, gate result SHA `be2257a63bb2bd3cd48c6f1f0d3b9837bee9bbb1f1b853f7b27c1e55d043b29c`, log SHA `7bd994794cc58ad68f1dbb55e6f189e26fed750ad6ce96a8c55e2582604e2352`; outer shadow exit0. Logs/results live under `.scratch/web-023-validation/`.

All88 completed scenarios retain their required layers; seven later-owner cases stay pending. Final ledger, public summary, plan/current and progress/handoff adoption are documentation-only changes after the source freeze and receive focused docs/plan/diff validation. Post-adoption closure1 passes0:224 human documents/29 helpers, all9 plan tests and git diff --check. Exact output is `.scratch/web-023-validation/closure1-shadow.log`, SHA `b6f837918b7c1a2f1b9f24460dfae0bba7be7d2404e1830e73deccfd14b1eae1`. Only eight documentation/evidence files differ from the source freeze; gate/runtime code stays unchanged. WEB-024 is next. Original failures, unknown native pending handle, locks/stores and production/NAS/remote/live-installation restrictions remain.
