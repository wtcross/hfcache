# Acceptance evidence

**State: baseline revalidated; implementation active.** Cases below remain
unpassed until their actual evidence is recorded. Source investigation is not
installed or disposable runtime acceptance.

## Source and environment identity

| Item | Actual evidence |
| --- | --- |
| Implementation branch / commit | `fix/cockpit-rest-api-alignment`; reviewed HEAD `dcc2c562b52304541d0cb85d20fc046072038e79` |
| Browser build checksum / source | Baseline production JS (decompressed index.js.gz) SHA256 `b414e92f01a316ffec9a45528fa676899ee842b0c44526599e30be90d15026f0`; source dcc2c562 |
| Application / CLI source | Same reviewed baseline; no source drift at activation |
| Physical launcher and rendered profile identity | Not inspected: production inspection forbidden; no disposable target supplied |
| Rootless image digest | Not inspected; immutable fixture image required for V54 |
| Cockpit / systemd / Podman versions | Installed versions not inspected; source Cockpit pin 47108e2f8ecac3cd71fb3372193dd0f9c0fba7b3 |
| Node / pnpm / Python / uv versions | v24.18.1 / 11.18.0 / 3.14.6 / 0.11.32 |
| Fixture location and no-live-archive proof | Repository-only Node fixture uses injected process/ports and synthetic strings; no host/archive commands |
| Original reported failure stage/problem | Unverified |

## Work packages

Each task owns its status/evidence; link it here without duplicating mutable status.
For each completed package record its real commit and test/gate artifact reference.
An uncommitted result says `<CPR-ID>, this commit`, never a made-up hash.

## Validation evidence

For V01–V60, record the case ID, test name or runtime procedure, command,
fixture/source identity, observed outcome, pass/fail/blocker and evidence location.
Group cases only when the cited test actually covers every named expectation.

Baseline command: `rtk node --experimental-strip-types docs/agents/plans/support/cockpit-rest-repair/baseline-reproduce.ts`, exit 0.
[Observed source defects and environment inventory](baseline-evidence.md).
V01/V11/V24/V27 baseline defects observed; repaired expectations remain unpassed.

| Case | Evidence / command / result |
| --- | --- |
| V01 | Not executed; owning repair and regression pending. |
| V02 | Not executed; owning repair and regression pending. |
| V03 | Not executed; owning repair and regression pending. |
| V04 | Not executed; owning repair and regression pending. |
| V05 | Not executed; owning repair and regression pending. |
| V06 | Not executed; owning repair and regression pending. |
| V07 | Not executed; owning repair and regression pending. |
| V08 | Not executed; owning repair and regression pending. |
| V09 | Not executed; owning repair and regression pending. |
| V10 | Not executed; owning repair and regression pending. |
| V11 | Not executed; owning repair and regression pending. |
| V12 | Not executed; owning repair and regression pending. |
| V13 | Not executed; owning repair and regression pending. |
| V14 | Not executed; owning repair and regression pending. |
| V15 | Not executed; owning repair and regression pending. |
| V16 | Not executed; owning repair and regression pending. |
| V17 | Not executed; owning repair and regression pending. |
| V18 | Not executed; owning repair and regression pending. |
| V19 | Not executed; owning repair and regression pending. |
| V20 | Not executed; owning repair and regression pending. |
| V21 | Not executed; owning repair and regression pending. |
| V22 | Not executed; owning repair and regression pending. |
| V23 | Not executed; owning repair and regression pending. |
| V24 | Not executed; owning repair and regression pending. |
| V25 | Not executed; owning repair and regression pending. |
| V26 | Not executed; owning repair and regression pending. |
| V27 | Not executed; owning repair and regression pending. |
| V28 | Not executed; owning repair and regression pending. |
| V29 | Not executed; owning repair and regression pending. |
| V30 | Not executed; owning repair and regression pending. |
| V31 | Not executed; owning repair and regression pending. |
| V32 | Not executed; owning repair and regression pending. |
| V33 | Not executed; owning repair and regression pending. |
| V34 | Not executed; owning repair and regression pending. |
| V35 | Not executed; owning repair and regression pending. |
| V36 | Not executed; owning repair and regression pending. |
| V37 | Not executed; owning repair and regression pending. |
| V38 | Not executed; owning repair and regression pending. |
| V39 | Not executed; owning repair and regression pending. |
| V40 | Not executed; owning repair and regression pending. |
| V41 | Not executed; owning repair and regression pending. |
| V42 | Not executed; owning repair and regression pending. |
| V43 | Not executed; owning repair and regression pending. |
| V44 | Not executed; owning repair and regression pending. |
| V45 | Not executed; owning repair and regression pending. |
| V46 | Not executed; owning repair and regression pending. |
| V47 | Not executed; owning repair and regression pending. |
| V48 | Not executed; owning repair and regression pending. |
| V49 | Not executed; owning repair and regression pending. |
| V50 | Not executed; owning repair and regression pending. |
| V51 | Not executed; owning repair and regression pending. |
| V52 | Not executed; owning repair and regression pending. |
| V53 | Not executed; owning repair and regression pending. |
| V54 | UNPASSED: local development now authorized. Provision isolated local KVM guest with QEMU, verified guest image, offline RPM/image inputs, synthetic protected credentials and no live/NAS archive; then execute exact bridge/launcher chain. Missing prerequisites are not a mocked pass. |
| V55 | Not executed; owning repair and regression pending. |
| V56 | Not executed; owning repair and regression pending. |
| V57 | Not executed; owning repair and regression pending. |
| V58 | Not executed; owning repair and regression pending. |
| V59 | Not executed; owning repair and regression pending. |
| V60 | Not executed; owning repair and regression pending. |

## Required gate record

| Gate | Command / result / evidence |
| --- | --- |
| Package repository gate | CPR-001: `rtk proxy scripts/check.sh` exit 0; 5008 passed/42 deselected, three wheel profiles, actual frontend lint/types/170 tests/build. [Evidence](gates/cpr-001.txt) |
| Explicit frontend gate | Pending — make -C cockpit check |
| Extended final gate | Pending — scripts/check.sh --with-build |
| Component/lifecycle regressions | Pending |
| Actual CLI / private Unix socket | Pending |
| Actual disposable Cockpit / PAM / rootless chain | Pending; provisioned isolated environment required |
| Documentation, schema and CLI parity | Pending |
| Existing durable/operation compatibility | Pending |

## Separate acceptance decisions

| Milestone | Evidence / disposition |
| --- | --- |
| Source remediation and mandatory automated gates | Not accepted |
| Actual disposable runtime chain | Not accepted |
| Installed production artifact parity | Not inspected; separate authorization required |
| Original installed candidate symptom resolved | Not demonstrated |
| Existing NAS/workload holds cleared | Not requested; remain in force |
| Deployment, registry publication, push/merge/tag | Not requested; not performed |

## Operator handoff and rollback

Record the remaining installed checks and the exact safe prerequisites before
any proposed deployment or original-flow test. Preserve source/bundle/image/profile
identities, backups, original keys/IDs, old receipts/results and unknown execution.
No rollback, source change or observer stop proves actual jobs drained. Link the
existing executor-drain and deployment procedures rather than inventing a shortcut.

## Contract review

List amended or unaffected invariant sections and ADRs, with real decision numbers,
status/amendment links, human docs changed and progress/current consistency checks.
Keep CP-04/09 changes explicit and all surviving configuration, credential,
read-only guard and no-cancellation boundaries intact.


Baseline contract review: CP-01–14, INV-006, workflow INV-011 and decisions
118–122/127/133 reviewed. Decision 134 adds presentation/recovery requirements;
CP-04/09 current exceptions remain until their explicit replacement packages.
Existing API/client/config/security/container/deployment contracts retain their
authority. No durable format, dependency or production control was changed.
The imported bundle manifest retains original import hashes, not mutable task
completion hashes; its original source-review evidence is preserved.


Later user steering permits local-host development, necessary service outage and
backed-up/restored installation changes without NAS impact. Disposable fixture
provisioning is now being investigated on this host; V54 remains unpassed until
actual isolated bridge/launcher proof exists. Preserve pending operations, original
guards/lock inodes, masks, hardening and credentials. No host mutation yet.


First baseline full gate failed: 1 failed/5007 passed/42 deselected in 600.24s;
`test_predecessor_commits_and_plan_selector_preserve_the_execution_record`
incorrectly required the live selector inactive forever. Corrected to inspect the
actual CAT-016 commit selector; focused file 2 passed in 1.07s. Full retry pending.
Frontend was not reached in that failed run, so it is not frontend acceptance.


### Mounted baseline investigation

`rtk node docs/agents/plans/support/cockpit-rest-repair/baseline-browser.mjs`
exited 0 in Firefox 140.13.0esr, using actual Maintenance/QueryError/hooks/API
adapter/runner with only the Cockpit process boundary controlled. Bounded artifact:
[baseline-browser-evidence.json](baseline-browser-evidence.json).
Actual DOM clicks dry-run -> Apply -> confirmation produced exactly one synthetic
Apply; after its key/ID and `reconnected` failure, Apply was enabled again.
The mounted validation QueryError lost problem/stage and showed generic guidance.
Unmount/remount lost local handles and issued zero new calls. This is a real
component root lifecycle reproduction, not the Application tab acceptance test,
real API/PAM/launcher proof, or satisfaction of repaired V01/V24/V27 expectations.
The owned loopback server/browser exited; no application command, production
credential, host configuration, NAS or live archive was accessed. No sandbox was
weakened. The private temporary browser profile is retained as fixture evidence.


CPR-001, this commit: full retry passed (5008 Python tests, 42 deselected,
593.55s; all three locked wheel installation profiles; actual Cockpit lint,
stylelint, typecheck, 170 tests with 0 failures/skips and production build).
[Gate summary](gates/cpr-001.txt). This records baseline coverage, not repaired
V01–V60 acceptance. Baseline source remains unchanged except the historical
selector regression test correction. Mounted reproduction and pure investigation
commands both exited 0; documentation alignment passed (183 documents/19 helpers).
