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
| V01 | Boundary normalization/runner and mounted QueryError pass all known stages; exact baseline loses problem/stage. `rtk node --test cockpit/test/failure.test.ts cockpit/test/runner.test.ts`; `rtk node cockpit/test/browser.mjs`. Higher pipeline-stage retention/reconciliation remains partial until CPR-003. |
| V02 | `cockpit/test/failure.test.ts`: Error/plain objects, malformed values, unknown problem contents, getter/proxy defenses, bounded validated fields; focused 24 passed. No arbitrary rejection prose retained. |
| V03 | `runner.test.ts` launcher/process/access facts and `failure.test.ts` finite status/signals distinguish categories without raw stderr. Mounted API adapter remains fixed. Actual real launcher cause remains pending isolated runtime. |
| V04 | `runner.test.ts` exact nonzero HFAPI/domain Envelopes survive rejected process; installed-confirmation postcheck remains stricter. Focused runner/failure/stream/container selection passed. |
| V05 | Existing runner/stream UTF-8/line/terminal bounds plus late handle/abort/callback regressions passed. Raw terminal bodies/unknown diagnostics withheld from browser activity. |
| V06 | `connection.test.ts` close/listener/retry/disposal cases and mounted D-Bus tests pass; at most two read attempts/one delay; no mutation replay. Real PAM/runtime layer remains V54. |
| V07 | Mounted real hooks reject prior read/unit generations and clear healthy evidence on refresh/failure; sequential polls. Exact baseline mounted stale-clear cases fail. |
| V08 | Mounted privilege/reconnect invalidation and pure mutation-generation tests pass. Portal actions individually gated. Higher Configuration pipeline phase/evidence tests remain CPR-003; actual PAM layer remains V54. |
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
| V34 | `runner.test.ts` page closure, callback failure, late handles and abort tests pass without process-close/cancellation capability. D-Bus channel disposal does not stop application execution. |
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
| V49 | Shared read/unit hooks now remove stale healthy evidence and reject old generations; mounted regressions pass. Per-surface full read rendering audit remains CPR-007. |
| V50 | Not executed; owning repair and regression pending. |
| V51 | Failure/runner and mounted QueryError synthetic secret tests pass; only safe validated problem/status/signal/handle fields retained. Registry/storage and all read surfaces remain CPR-004/007 scope. |
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
| Explicit frontend gate | CPR-002 `rtk make -C cockpit check` exit 0; current full gate confirms 221 unit + 12 mounted cases, lint/style/types/build |
| Extended final gate | Pending — scripts/check.sh --with-build |
| Component/lifecycle regressions | CPR-002: 12 mounted cases passed in actual Firefox; [bounded results](gates/cpr-002-mounted.json). No real PAM/API claims |
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


CPR-001 commit `b40b443`: full retry passed (5008 Python tests, 42 deselected,
593.55s; all three locked wheel installation profiles; actual Cockpit lint,
stylelint, typecheck, 170 tests with 0 failures/skips and production build).
[Gate summary](gates/cpr-001.txt). This records baseline coverage, not repaired
V01–V60 acceptance. Baseline source remains unchanged except the historical
selector regression test correction. Mounted reproduction and pure investigation
commands both exited 0; documentation alignment passed (183 documents/19 helpers).


CPR-002 mounted fail-before evidence:
`rtk node cockpit/test/browser.mjs dcc2c562b52304541d0cb85d20fc046072038e79`
exit 1, 3 passed/6 failed (lost bridge problem, stale read/unit evidence, closed
cached client, finite pending read recovery, privilege invalidation). Working tree
mounted harness: 9 passed/exit 0 before final schedule regression additions.
These are actual React roots/hooks/adapters with controlled Cockpit boundaries,
not real PAM/API/host commands. Existing old-generation/no-replay cases already
passed baseline and are retained. Full gate and final expanded counts pending.


Final CPR-002 additions: expanded mounted browser harness failed before schedule
freshness fix (10/12 passed, 2 failed) and passed all 12 afterward. Actual mounted
Maintenance modal portal privilege loss produced zero Apply calls. Runner negative
confirmation regression failed before fix, then exact HFAPI003 Envelope preserved;
apparent successful stdout with failed process still rejects. Focused runner/
failure/connection suite: 63 passed, exit 0.

Local runtime preparation reached boot/SSH, then paused; see
[runtime-setup](runtime-setup.md). Actual twelve signed prerequisite RPM additions,
zero upgrades/removals. Isolated guest has no default/NAS route or host directory
binds; no production configuration/secret/application change. V54 is still unpassed,
not blocked on user approval. Next prerequisites: guest-local application fixture,
synthetic REST sources, real bridge/launcher/browser exercises and exact identities.


CPR-002, this commit: `rtk proxy scripts/check.sh` exit 0: 5008 Python passed,
42 deselected in 656.48s; all three locked wheel profiles; actual Cockpit frozen
install, lint/style/types, 221 unit tests (0 failures/skips), 12 mounted Firefox
cases, production build. [Gate summary](gates/cpr-002.txt),
[bounded mounted results](gates/cpr-002-mounted.json). Explicit frontend gate also
exited 0. Documentation alignment: 183 documents/19 helpers. No application
runtime dependency, archive format, new REST route or credential boundary change.
Successful confirmation remains stricter; failed confirmation retains classified
negative evidence. CP-01–14, INV-006, decisions122/127/133/134 reviewed and current.

Production JS (decompressed index.js.gz) SHA256 at CPR-002: `b6995b709b0be8f63b97b81d908986bb85f94680c9d4783fd4b6af174f6628f0`.
