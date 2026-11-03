# WEB-032: Accessible job availability reasons, bounded GET-only recovery, clear refusals/results, advanced diagnostics and preserved schema-1 handles

| Field | Value |
| --- | --- |
| Status | complete |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | API-019 |
| Execution | `gpt-6.1-sol` / `medium`; explicit task-agent setting required |

## Scope and acceptance

Accessible job availability reasons, bounded GET-only recovery, clear refusals/results, advanced diagnostics and preserved schema-1 handles; use the accepted protocol rather than redesigning it.

The parent plan's applicable scope, acceptance criteria and safety prerequisites
are binding. No remote pushes, image publication, release tags, automatic
schedules, unrelated permissions, archive initialization, manual archive writes,
reboots, NFS disconnection or other-host effects are authorized.

## Contracts, invariants, and ADRs

Review the parent plan's affected contract and decision list progressively.
Reviewed INV013/014/018–023, existing FS02/19/21–23 and AD16/17, and
ADR114/115/118/141/145/146/150/154/164 progressively against the affected owners.
ADR164, INV023, the recovery/API/schema contracts and Operations guide record
browser implementation and causal refusal qualification. No new architecture,
runtime dependency, privilege, receipt/result format or writer capability.
Writer ADR165 and INV003 remain with the downstream protected profile work.

## Validation

| Changed requirement | Finite meaningful check | Result |
| --- | --- | --- |
| Closed readiness/intent transport | Generated registry, strict decoder and authenticated bounded transport cases | Pass in focused12:179 definitions, exact route inventory and generated request body |
| Atomic schema-1 migration and causal dispositions | Registry restore/failure/cross-tab/scoped disposition cases; exact c23abba reader drill | Pass in focused12; complete exact predecessor reader accepts1/refuses empty/populated2 with zero writes |
| Visible authenticated GET-only reconciliation | Controller initial/reconnect/visibility/late-generation cases and exact mutation counts | Pass in focused12:2785 affected tests across16 files; no automatic POST or protected confirmation |
| Accessible readiness and recovery | Component cases plus built Chromium keyboard, narrow viewport and actual 200% zoom | Pass:16 final built browser cases, keyboard/accessibility/390px and1440px, actual200% zoom/320CSS |
| Frozen integrated source | `rtk scripts/check.sh --require-web`, full failure log preserved | Pass:gate3 exits0;1279 source names/hashes unchanged; both earlier failed gates preserved |

The optional instrumented functional runner remains untouched and uninvoked.

## Execution notes and handoff

Actual task-agent setting: `gpt-6.1-sol` / `medium`. Source and owned browser
fixtures only; no production changes.

Activated 2026-11-03 by the user's explicit end-to-end implementation instruction.
Protected deployment, controlled writable transition, selected Sync and refresh
pilots and bounded metadata backfill are authorized after the reviewed safety
prerequisites. Scope is this host/current boot with fail-closed manual startup
permitted; unattended boot acceptance remains separate.

## Completion evidence

Focused12 passes2785 affected controller/transport/registry/component/oracle
checks across16 files in18.15s. The generated registry has179 precise definitions,
including closed raw response authorities and the fixed explicit review request.
The exact c23abba complete browser source graph is extracted/bundled and executed:
schema1 is readable, empty and populated schema2 refuse with zero writes and
exact original bytes. Reader source SHA256
`e8019eadc51b78e3df958d833c8f3afe1a8ac442731c0e7b867b3e8baad09b11`;
`.scratch/web032-validation/predecessor-reader-result.json` retains bindings.
Raw focused failures remain in `/var/tmp/web032-*.log`; initial broad frontend
contention/browser setup failures and strict source-oracle refusals are retained,
with expected new GETs and179-definition coverage explicitly accounted rather
than hidden. The first predecessor extraction exceeded Node's default1MiB pipe
buffer; a bounded8MiB buffer executes the same exact source successfully.

Root's independent capacity work retired only proven completed disposable
fixtures after complete manifests/no-owner proofs: OPS024 gate2 receipt
`dd05c16dcc1e26e82eb4636e73f30864eca7ac1791d1329e24bffc3279b91cb7`
and the fully archived WEB021 profile3 disposable venv children (archive
`6d0deea530da4de210b0f3fca444db21b0c9a8f7ef7c9418232fc1e4c0a1c37f`).
Original logs/reports/requirements remain. Reported available root1.908GB/
home73.1MB clears the unchanged gate resource floor. No production state,
permission, service, lock, mount or archive content changed in this package.

The sequential built Chromium retry passes all15 cases in46.6s, including
390px/1440px availability/refusal/reload counts, explicit unknown retirement,
schema1 migration and original failed admission. Browser fixture correction seeds
the actual existing localStorage surface; it changes no runtime storage choice.
Raw failures and15-case report/screenshots remain in the owned browser artifacts.
The final ordinary-message refinement additionally exposes the closed reason,
retires old advisory readiness and points to explicit Recheck. Registry144 cases
include exact terminal-summary/legacy-handle migration and concurrent readback
preservation. Actual browser200% zoom passes with innerWidth320, CSS zoom1 and the existing
extension's independently confirmed tab zoom2. Jobs uses keyboard-opened narrow
navigation, keyboard Recheck, an accessible archive-denial description, no POST,
no horizontal document overflow and zero axe/CSP/page/unexpected-request issues.
Evidence remains in `web/.artifacts/library-zoom-InlT1W/`; the first attempt's
hidden narrow-navigation lookup failure remains in `library-zoom-lMOdZ4/`.
No timeout or product assertion changed; the existing Open navigation control
is exercised with the keyboard. Final typecheck, targeted lint, ruff and pyrefly
pass. Strict frozen `rtk proxy scripts/check.sh --require-web` is next. Source and unit tests alone do not establish installed acceptance.


### First strict gate and named follow-up

Gate1 completes its normal backend summary:9641 passed/3 failed/52 deselected
in1239.51s; wrapper1269.706s, source names/hashes unchanged. Full log SHA256
`0a2ea9a8a69b543a3229c23d34606e0e6f5b27733e308db4993537ff183b49ef`.
The three failures are exact source-derived corpus/mode pins:374 cases,
179 definitions and60 modes now replace366/175/57. Inventory equality,
serializer validation, no-network/no-archive factories and2000 original-authority
negative cases remain strict. This first gate remains failed, not acceptance.

While it was frozen, an owned actual-source repro found reviewed retirement
incorrectly conflicting with a preserved original ID. The parent reviewed it as
an in-scope preserving-history defect. After gate completion, the narrow fix
retains original ID/identity/summary under retired_unknown, keeps contradictory
not-admitted admission operator-only, requires ephemeral fresh own-key unknown
proof for retained-ID Review and fences old record callbacks by disposition.
No conflict-recovery authorization lane or protocol redesign is added. This
named evidence justifies the final changed-source strict gate.

Root preserves the complete failed temporary payload before retiring its exact
owned root:162848 entries, full archive SHA256
`7cc88598a48e44e4d02d8d47561681d90202e605284bab968627ec0e5961783a`,
manifest `8c99b692deebcc9b589f87482829f4e7064b8d49f76b140d220d814dd2f4c6b6`,
retirement receipt
`9ce167220a7af4a28d96a3f7e4d3debb0337a167f97d33dc158676fdd75d6747`.
Fresh335-process/all-UID proofs,161494 inode joins, matched inventories and
archive/metadata/status fsync precede retirement. All failed evidence remains at
`/var/tmp/hfcache-web032-gate1-retirement-evidence/`. Root reports1.727GB root/
43.3MB home available; the1.1GB floor is unchanged.


The narrow follow-up passes210 registry/controller/recovery tests and63 lifecycle/
component tests, including real cross-tab invalidation, retained identities and
summaries across reload, exact GET/POST counts, old-token rejection and a newer
deliberate observation surviving an older automatic unknown response. All44
Python corpus/wire checks pass with strict source-derived pins. The existing
built browser matrix now passes16 cases in48.1s, including the retained-ID
schema1 migration/review/retirement/reload variant with no job replay. All browser
and API fixtures remain source-owned; this is not installed acceptance.
The final changed-source strict gate remains required.


The affected protected-outcome regressions additionally identified idle observer
allocation during unknown reconciliation. Pause only an actually observing
original owner; retain unchanged private-slot accounting and idle presentation.
No pool limit, metadata charge or assertion is relaxed. The final required gate
will rebuild and rerun all16 browser cases and actual200% zoom on frozen inputs;
no redundant standalone layout run is claimed for this pause-only refinement.


### Second strict gate and final read-fixture pin

Gate2 preserves1279 source names/hashes unchanged through1583.785s. It passes
9644 backend checks, three locked wheel profiles,3809 web unit/4169 combined
checks (94.89% lines/89.83% branches), all16 built browser cases and actual200%
zoom. It then fails the final real-API fixture's sole outdated model-count text
pin:380 independently validated originals replace372 after the same8 corpus
additions. Seven other root-prefix API/browser cases pass, with API lifespan
and listener drained and owned Chromium2797696 closed. The expected four
independent incorrect wires remain refused; only the exact positive count changes.
This gate remains failed. Full log SHA256
`fb64343b54da836656b956096636afd94d97c5e4c043f52ff7ab9d14e123bbae`;
shadow log `7f94238701d35a339a0754a43c6e0995d84565c6e94c76d24c8d1051dfec1f75`.

The retained failure is nested at
`.scratch/web-read-fixture-eylabbt1/root/browser.log`, with `browser_exit=1`,
`api_lifespan_drained=true` and `api_listener_closed=true`. The top-level
BLOCKED message is not evidence of a missing nested log or disk failure;
no ENOSPC is observed in that browser log. Actual9.1MB home free is a separate
prerequisite for the direct affected read-fixture retry and final strict gate.
Root owns capacity recovery; no safety floor is lowered and no product change
is attributed to this exact-count correction.


The existing direct real-API read fixture passes all8 cases for both root and
management prefixes after the exact380 positive-model count correction;
`.scratch/web032-read-count-retry/SUMMARY.json` retains each service/browser
lifecycle and independent refusal check. This is source-owned React/API evidence,
not Caddy/Basic/installed acceptance. The final full frozen gate remains required.

Root restores capacity without lowering the1.1GB floor: gate2's complete164269-
entry TMP payload is archived and verified before exact retirement; the separate
completed527-pass WEB022 owned pytest TMP preserves24910 entries, archive SHA256
`855b9b93c6babfe4f40f930b41eb2f80402e5eac9074ff9e6f7839f18849ee75`,
manifest `a87186d149e1034f23c5885647dd516b59b08b7f6997c856cff02e308815469f`
and retirement receipt
`c384d37058d44d8a8d3e9bc5b9cd31e582c5ce0d301546282ce9d0387d85489c`.
Fresh335-process/all-UID proofs find zero owners before retirement; archive,
metadata and receipts are fsynced and original successful check records remain.
Root reports1.485GB root/149.4MB home available before the direct fixture.
Profile4's exact disposable venvs are fully preserved; profile8 is prepared only.
No product/production/historical-cache deletion or safety-floor waiver occurs.


### Final strict gate and completed source scope

Gate3 passes `rtk proxy scripts/check.sh --require-web` in1602.732s with all1279
source names and SHA256 values unchanged. It passes9644 backend checks/52
deselected, package build and three locked wheel profiles,179 generated transport
authorities, web lint/types/strict/auth/metadata checks,3809 unit and4169 combined
checks,94.89% line/89.83% branch coverage, all16 built Chromium cases in48.8s,
actual200% zoom and both prefixes of the real-API React read fixture.
No skipped/retried browser case, source pin waiver or optional functional-runner
invocation is used. Entire-log failure scanning is clean. Full inner log SHA256
`9d46b39dfb8ad04116b60c23b7b3f573a2a7e77abd7aeb6bb4d3f0fcdbfda216`;
shadow `cb99c33176485244d2636e0ea7f0cc723c908a1d8f13d87d1c2baccd56542eff`.
The owned built browser2819494 and actual-zoom browser2820100 close; zoom evidence
is `web/.artifacts/library-zoom-SQ9QlA/`, real API summary is
`.scratch/web-read-fixture-jqhh53dx/SUMMARY.json`. Both source API lifespans and
listeners drain. The loginUID1000/nice10 gate uses only its private empty readonly
archive shadow; no live archive/service/mount/permission state changes.

Completion records are written after this frozen gate and receive focused
repository documentation checks separately. Both failed strict gates, focused
failures and full resource-preservation evidence remain honestly failed/scoped.
Affected invariants/ADR164 and API/browser/schema/recovery contracts are current;
no new runtime dependency or architectural decision. OPS-027 is selected next.
Installed Caddy/native/rootless workflows, actual executor drain/confinement,
protected writable transition, production pilots/backfill and independent
boot/NAS/workload holds remain with OPS-027/WEB-033 and later packages. This source
completion does not claim them. No tag, push, deployment or production write.


Final completion metadata passes69 focused documentation checks and standalone
alignment (216 human documents/29 helpers). Only the task, active selector,
parent-plan lifecycle and progress Markdown records differ after gate3; no product
source or test input changes. Root retires only the successful gate3 TMP after
matched164269-entry inventories,162913 inode joins and fresh334-process/all-UID
zero-owner proof. Manifest SHA256
`0c72573f87c03141815c9e2938c91957f244ac9667a16a095f78607e15295df2`;
retirement receipt
`0272608656e12ee9dde2d1bc88102b1634cb7d2281d407960026358f83736c47`
at `/var/tmp/hfcache-web032-gate3-retirement/`. Logs, reports, manifests and full
failed archives remain fsynced/preserved. Root reports1,479,913,472B root/
119,279,616B home available; no safety floor changes or other cleanup.
