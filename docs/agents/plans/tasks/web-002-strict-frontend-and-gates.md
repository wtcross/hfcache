# WEB-002: Create the strict React workspace and mandatory local gates

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P0 |
| Depends on | [WEB-001](web-001-baseline-and-contracts.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-002: add strict React workspace and required gates` |

## Read before implementation

cockpit/package.json and reusable license notices; scripts/check.sh; docs/development.md; architecture.md sections 3 and 5; testing-strategy.md.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Create web/ with React, Vite, strict TypeScript, pinned compatible Node/pnpm and frozen lockfile. Add type-aware linting, no unsafe any propagation, no unchecked casts at network boundaries, accessible UI primitives and a minimal route shell. Select React tooling deliberately; reuse licensed pure components/helpers only after removing Cockpit transport assumptions. Audit bundled/transitive licenses. Keep production dependencies in the browser bundle or optional server closure, never Node in runtime.

Implement documented lint/typecheck/test:unit/test:component/build scripts. Use a maintained component-testing stack, deterministic fixture network mocks only at component level, and coverage reporting for new code. Add --require-web to the provider-neutral scripts/check.sh, without removing existing Python, docs, build/install or Cockpit checks. Strict mode must fail if prerequisites are missing; default backend-only mode may have an explicit loud frontend omission, but it cannot satisfy this plan's gate. Add safe help and script inventory entries. Establish ignored artifact locations.

## Unit and component validation

Test helper functions and framework setup; prove deliberately invalid strict TypeScript/unsafe decoder fixtures fail the gate. Test script argument parsing and missing-tool refusal without touching runtime state.

## Integration validation

Run frozen install twice, deterministic production build, lint/typecheck/component suite, and scripts/check.sh --require-web. Assert no source mocks, credentials or external CDN references in the production output.

## Functional validation

Run the real-browser empty shell and keyboard-navigation smoke on an owned loopback fixture, explicitly labelled preliminary rather than Caddy/backend acceptance. Confirm a missing required browser exits nonzero.

## Human documentation deliverables

Update docs/development.md and docs/scripts.md with exact new commands, versions, dependency provisioning and no-skip rule; document that Node is build-time only. Start the human UI navigation explanation.

## Acceptance

Reproducible locked React workspace exists; strict checks are enforced, not merely configured; production bundle is buildable; no new CI-provider dependency or runtime Node requirement; baseline gates remain intact.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Started after completed WEB-001 commit `c4dd806` and its corrected strict gate.
Node 24.18.1/pnpm 11.18.0 are present; public registry/primary-documentation review
identified compatible pinned Vite/Vitest/Playwright/type-aware lint candidates.
The selected workspace uses maintained ESLint 10 with compatible strict peers;
see the [tooling amendment](../../../adr/decision-143.md#selected-workspace-tooling-and-preliminary-gate-amendment-2026-10-20)
and exact package/lock files. No release-age/peer override or type-check weakening
is accepted. Collaborators share this work-package boundary: frontend workspace,
gate/tests, and human documentation. No later task is activated or production
action allowed.

Gate controls: 39 existing/new isolated refusal/order tests pass; the additional
29 cover web prerequisites, all failed stages, late tool/source disappearance,
safe help and the still-unimplemented functional flag. These use fake tools and
establish gate behavior only. Docs discovery/migration: all 44 tests pass and the
validator reports 194 human documents/19 helpers. An earlier concurrent authoring
run had 85 passing tests and one link failure while the three license/notices
targets were not yet created; that is not final acceptance evidence.

The initial real Chromium run exposed text contrast failures, corrected before
the later passing run. Fixed report/output paths overwrote its screenshots on
rerun; those original failure artifacts cannot be claimed as retained. The runner
now retains unique per-run evidence; the independent disposable-copy failure/
retention check passes. Review also demonstrated
that Playwright detaches Chromium separately from its CLI; killing only the CLI
group cannot establish browser drain. The corrected wrapper owns and awaits the
actual sandboxed browser, with bounded cleanup. Both browser and unit/component
timeouts fail independently of a positive report or a child exit 0. Final source,
failure proofs and the complete strict gate pass below.

## Completion evidence

Post-check correction before advancing: the extra staged whitespace check
reported one generator-added blank line at the end of the license notices.
The commit was made before that nonzero result was inspected. Preserve the
upstream license text, remove only the final generated separator and amend the
unpublished work-package commit after the complete strict gate passes again.
Offline all-lock license verification, lint and whitespace checks already pass
for that correction. The complete corrected gate now exits 0; the final source
and run below supersede the earlier gate for acceptance. Earlier successful and
failed logs remain retained evidence. The unpublished commit is amended within
this same work package, with no remote publication.

Completed after the restarted full strict gate and independent refusal/retention
proofs. Source: WEB-002, this commit, parent `c4dd806`; local date 2026-10-20.

### Required final gate

`rtk proxy scripts/check.sh --require-web --require-cockpit` exits 0.
`.scratch/web-002-amended-gate.log` SHA256:
`795a5efc9cb35c5b4affbe41953452ebbd12e802ba32f86b71cfeac2df22f3cc`.
All 5337 Python tests pass, 52 opt-in tests deselected, 708.97 s; three locked
base/server/server+MCP wheel installation profiles pass. Existing Cockpit:
572 unit tests, zero skips/cancellations, 110 mounted Firefox tests and production
build pass. Web frozen install, lint, types, actual negative strictness fixtures,
45 unit/50 combined component tests, build and 2 sandboxed Chromium tests pass;
zero required skips or retries. Coverage: 98.46% lines, 98% branches, 97.14%
statements and 100% functions. The independent complete source/test Pyrefly check
with `--use-ignore-files=false` also exits 0.

Final gate reports:

- `web/.artifacts/unit-6zwRcW/report.json` SHA256
  `1fa723411576e68be829a5d253af323bb4bd127c947ac1a6edf413895697054b`.
- `web/.artifacts/component-e5zwNR/report.json` SHA256
  `11702d8a59c6d654eb39994a0eb8286aefe24f4323565c68f4564cd74caea1ca`.
- `web/.artifacts/browser-dO7PpS/report.json` SHA256
  `3edb6b9533b50d354395e1a956a75e3e2f9f018200b52b1439978a62caf13b13`.
  Exact owned browser PID 2099137 and HTTP listener closure observed.
- `web/coverage/coverage-summary.json` SHA256
  `e9334c6e9fbaf3d6f51e6d1c654dff6ea39ff8eb3845d584025d4dfba2bb4090`.
- Backend wheel SHA256
  `7ba81b14b1d36dc6648cb37404d46dee5abf8978a548d0fe350005d900f22274`;
  sdist SHA256
  `59f2416e321d24aaedb1b92bbd77b8de154ceddf3492a3e1044ad19d8d5a0514`.
  They remain Node-independent; no deployed asset artifact is claimed.

The preceding passing gate remains at `.scratch/web-002-final-gate.log`,
SHA256 `a4ede008ba95bac80a570b80e165c2ddb0db435982b11872baa73d5ae88ce336`
(5337 Python tests, 703.58 s). Its original 44-file manifest remains at
`.scratch/web-002-source-inputs.json`, SHA256
`b480a92abc9311e6d96e0445ea8e41a2a8b23e4add39e6af97913f774e5cd302`,
source-set `24faaa9e441fa5ea39f0cc7685b192bf6e20d3615d75de8ea849f3b85e832803`.
Only the notice generator and its final separator changed before the final
strict rerun. The inventory, lock, output assets and upstream license text remain
unchanged. Final license-script SHA256:
`dfc301a158069f971e84ba71485f440aeb91e102e05e25b429aa485438f9ed8f`.

### Source and artifact identity

- `.scratch/web-002-amended-source-inputs.json` records 44 reviewed source files,
  excluding mutable execution records and ignored artifacts. Source-set SHA256:
  `429a50c01273715b5b0e28d115cb57e98d98be79d41fc08fda37403724272907`;
  manifest SHA256:
  `2bcf4e9cd1962abded42ca59c247dca21912cceba7ea8f3b3597c95f99e7cb69`.
- Frozen web lock SHA256:
  `1727489872278b8eb62b6fa42a4abb0c8f97f88096d3a687f9368aa271aa664b`.
  License inventory binds all 274 exact locked packages, including optional
  platforms; production dependency closure is React/React DOM 18.3.1,
  scheduler 0.23.2, loose-envify 1.4.0 and js-tokens 4.0.0. Actual MIT license
  texts are retained. Inventory SHA256:
  `bd02ee8b5bbbe553188f57389511fa8c8f3214455cadb854a2317122d8f8ba39`;
  notices SHA256:
  `be8cd5da0eee660b6b7eb7a8bfee0c014f287543041f53f1d97f005b5398f927`.
  No Cockpit implementation is reused or relicensed.
- Two consecutive production builds have identical manifests at
  `web/.artifacts/build-{first,second}.json`, each SHA256
  `5226fdaebe7bf02070dabe64b6bdc64d4935cba00a5eefae4208c58aae59bd28`.
  JS SHA256 `4928f2ee133f0f46dffeb0ea1b2fe2b9bd2ddb6178070dd4f6c20951b62cc814`;
  CSS SHA256 `7e02fb71adc7e7a3b9b0496d67261c49d1950d9324448579516b7348cf6de826`;
  index SHA256 `b40b5576bcc00a23b1dffeb057773ee9ae276396b10ec6ebf72c57d2006860e2`.
  Static output: 155361 bytes, gzip JavaScript: 47654 bytes, below 350 KiB.
  Production checks reject prohibited credential/mock/CDN references and maps.

### Executed validation and retained limits

- `rtk pnpm --dir web install --frozen-lockfile` ran twice, both exit 0
  (166 ms, 56 ms). These outputs remain in the tool transcript; no standalone
  per-install logs or per-install lock snapshots were saved. The final lock
  digest is recorded above. Build commands and actual artifact comparisons,
  browser versions/binary hashes and provenance are recorded in
  `web/.artifacts/WEB-002-evidence.json`, SHA256
  `40e329be9fa1ba977103b28e45695fca90f2301fa4ff936355ea63ea034a2d2d`.
- Real Vitest unit run: 45 passed; combined unit/component run: 50 passed,
  98.46% lines and 98% branches. Strict type/lint, actual inherited negative
  TypeScript/unsafe-assertion fixtures and offline license checks pass.
  Covering files: `web/test/navigation.unit.test.ts`, `report.unit.test.ts`
  and `App.component.test.tsx`. Reports and coverage are under ignored
  `web/.artifacts/` and `web/coverage/`; the full gate repeats these checks.
- Preliminary built-shell functional tests in
  `web/test/browser/shell.spec.ts`: desktop keyboard workspaces/deep reload/
  exact missing routes, and mobile labelled navigation/no horizontal overflow;
  both include axe scans with no serious/critical violations. Actual sandboxed
  Chromium 156.0.8078.4, Playwright 1.64.1/revision 1248: 2 passed, zero skips
  or retries. Report `web/.artifacts/browser-C9Cy50/report.json` SHA256
  `ecd305c068a4c6293b1703db60abf94996c4c01a9a72a230efbcdbe01a4cec06`.
  The installer used its Ubuntu 24.04 fallback on this unsupported host;
  execution passed without host package installation or security weakening.
- Explicit empty-cache invocation of `node web/scripts/browser-smoke.ts`
  exits 1 before opening a listener; no browser is downloaded at runtime.
  `web/.artifacts/missing-browser-proof.log` SHA256
  `e32c7d11e4d6f817e27c29a89eecb8ce8f2a2493c5794dc70ca433bc69c0df7e`.
- Independent real-browser retention proof: copied assertion fails with exit 1,
  one passing/one failing test and a retained screenshot/report; restoring the
  copied test passes 2/2, preserving all four failure artifacts byte-for-byte.
  A separate copied CLI shim runs the actual passing tests, then hangs and
  deliberately exits 0 on SIGTERM. The shortened copied outer deadline still
  forces wrapper exit 1. Exact owned Chromium processes and HTTP listeners
  close; PIDs are absent afterward. Source wrapper SHA256
  `1c6768739c1a957dbfe6710925b41c719f910c31d8bc529b751b23e563c20ef8`.
  `.scratch/web-002-retention-proof/SUMMARY.json` SHA256
  `4425df79785adc1e6572198bd7071bea67d11b32b16317288734b1c0cb2833ee`.
- Independent unit/component wrapper timeout injection uses synthetic positive
  reports only: actual child status 0/signal null/error ETIMEDOUT correctly
  gives wrapper exit 1 in both modes. It does not establish frontend acceptance.
  Children exit and evidence remains. Final test-suite source SHA256
  `e887a205003f42f76b64b70209ec969c1f709ee9f597f6251d331693d8c2f086`;
  `.scratch/web-002-vitest-timeout-proof/SUMMARY.json` SHA256
  `437db6e51d55e038776a71e17a144413f8a4729508ef58424b7eb945af1a5132`.
- Focused Python gate/docs/matrix/plan checks: 104 passed in 6.88 s.
  Independent matrix parser review: 18 passed. All eleven injection points,
  exact set/count and existing mapped tests remain enforced. Full first gate
  stopped with 5336 passed/1 failed/52 opt-in deselected in 722.19 s because
  its matrix parser collected the new unrelated version table. Failed log
  `.scratch/web-002-gate.log` SHA256
  `efc1bfe0dfd7eb0b775045daf02319bb07a9ae8d306e43aa9df66246e4789eae`
  remains; the corrected gate restarts from the beginning.

### Contracts, documentation and scope

Reviewed INV-003/010/019, FW-01–04, AD-01/15, retained CP-01–14 and decisions
88/113/138/143. Decision 143's tooling/conformance amendment records the maintained
tool choice and strict preliminary gate; no new runtime Python dependency,
archive/durable format, permission, service, Caddy or MCP behavior changes.
Existing Cockpit remains shipped and required. The source preview is disconnected
and contains no fictional repository facts.

Human changes: `docs/development.md`, `docs/scripts.md`, `docs/web-ui/README.md`;
source metadata and ADR links align. Documentation discovery excludes only exact
generated web roots while checking source guides. Full documentation alignment:
194 human documents/19 helpers; all 44 documentation alignment/migration tests
pass. Logs: `.scratch/web-002-docs-{focused,alignment,suite}.log`.

All 95 feature scenarios remain pending; WEB-002 owns none. This package proves
the local workspace/gate and preliminary shell only. No Caddy/API/Basic/installed
native/rootless/NAS/production acceptance or Cockpit retirement is claimed.
The initial overwritten contrast evidence remains an explicit historical gap,
not reconstructed proof. Existing production holds, original files/stores/handles,
five prior guests and unknown attempts remain untouched. Completed evidence is
also in [progress](../../progress.md#web-ui-replacement-2026-10-20), with Operator
handoff 33 amended. The [current selector](../current.md) advances to
[WEB-003](web-003-typed-wire-contracts.md); no older backlog is activated.
