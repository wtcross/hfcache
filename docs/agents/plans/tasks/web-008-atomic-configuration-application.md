# WEB-008: Implement guarded atomic configuration application and recovery

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `183496e5baa8b20348725211ef7320da21d037b90b8cdd4f9013cf42a57727ef`,
original content SHA-256 `2d7e19bdc7b57bdcdad49fadc4dde11028b1e9e273bbe16f43615ee53a4b2d5b`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P1 |
| Depends on | [WEB-007](web-007-configuration-read-and-preview.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-008: implement guarded atomic configuration application` (this commit) |

## Read before implementation

Existing persistent root configuration lock/candidate scripts; operation store/runner; config application contract; host private protocol; config crash cases.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement keyed POST /config/applications and the helper's fixed apply operation. Revalidate internal capability, independent host policy, exact base/candidate, compatible authority and required successful matching preview at execution. Persist safe admission before transmission to the helper and preserve unresolved outcome evidence. No TOML/credentials/raw logs in generic receipts, events, browser registry or public results.

Implement read-only original-operation reconciliation after API/helper crash or lost response. Capture staged/installed/confirmed/unknown evidence in independently versioned private state. No auto-replay, automatic rollback or cleanup after ambiguity; another Apply is blocked until authenticated reconciliation resolves it. Bounded private candidate retention cannot delete unresolved work when full. The helper cannot redirect target/source/path or acquire broader archive rights.

## Unit and component validation

Exhaustively test apply state transitions and failures at candidate stage, backup/fsync, rename, parent fsync, confirmation and result persistence. Check lock inode, mode/owner, base/preview mismatch, permission drift and redaction.

## Integration validation

Use real local helper/API operation stores with injected process/socket failures and racing legacy/new clients. Verify exact on-disk candidate/base/predecessor outcomes, no stale queued execution and only read reconciliation after restart.

## Functional validation

In isolated guest through browser/Caddy, apply a valid edit, observe actual installed bytes, induce response loss after install and reconnect to the original operation without another apply. Exercise failed preview, stale tag edit, quota and helper-denied cases.

## Human documentation deliverables

Document full apply workflow, expected confirmations, backup retention, conflicts, interrupted apply and safe operator reconciliation. Update security/config/schema/API contracts and relevant ADR amendments in the same package.

## Acceptance

A successful UI apply means exact installed confirmation, not only a 202 or valid syntax. Every interruption class preserves evidence and blocks unsafe replay; legacy/shared lock and file permissions are retained.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Completion evidence (2026-10-25)

Implemented ADR154's keyed application/original-outcome API, fixed stdlib helper
writer, wire bindings, shared legacy guard and confinement packaging. The helper
uses the original flock and makes its sealed minimal pending intent durable
before private staging. Candidate/base/predecessor/backup retention, atomic
exchange/fsync and exact independent confirmation distinguish confirmed from
staged/installed-unconfirmed/unknown without replay, rollback or deletion.
Unknown paths/history and full retention quotas refuse. Generic records contain
no TOML, credentials or raw logs. The new configuration editor UX remains
WEB-015; these tests exercise the real API/helper through the built UI's Caddy.

Acceptance found and corrected early-intent ordering and a repeated full-runtime
confirmation inspection. Confirmation now copies the pinned capture with only
its installed configuration leaf updated, preserving all other authority checks
under the unchanged64MiB budget. Unexpected daemon errors retain only bounded
protected classes/frames. Legacy preview releases the common flock across the
network, then reacquires its original inode and rechecks exact bytes before
returning bounded output. The fifth bootstrap module and three fixed SELinux
roles enable only the reviewed configuration effects; archive/credential/network
rights and service hardening are not broadened.

### Source gate, artifacts and scope

Evidence root `E=/var/tmp/web-008-validation-4d8__00f`; relative locators below
are inside that retained directory. Source is `WEB-008, this commit`, parent
`7a86fc2d20eccf18dc1615a764f88283e91f1aab`.

`historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` passes1647.627s, exit0:
1378 inputs unchanged at
`93681822b682a6d14d383bccf4b8cc91c7a9432ee43be03371d5382e353756f9`.
`gate5/strict-gate-result.json`/`gate5/strict-gate.log` record8363 backend passes,
581 historical frontend unit passes, all strict frontend/mounted-component/wheel/read-API
checks and documentation210 human/27 helpers. The52 unrelated opt-in
deselections are not required skips. Accepted installed cases have one attempt and no required skips; earlier failed
cohorts remain recorded below. Final bookkeeping is within the gate's recorded exclusions; runtime
source and installed artifacts remain unchanged. Final
`precommit-source-preservation-proof.json` rejoins all1378 inputs to that same
93681822… snapshot after the private test/evidence work.

Actual-filesystem tests discover and cut all114 first-apply/120 previous-backup
durability checkpoint names, retaining the original22 independent expectations.
Final writer/real-Unix validation passes279/48.33s and factory/Unix smoke3/5.09s.
A real Unix disconnect before first host intent proves one handoff, same-key202/
createdfalse after API restart, new-key409 and unknown/pendingfalse without any
host ledger/effect. These labelled source fixtures do not claim installed MAC
proof. Coverage retained in `corrected-confirmation-*`: API93.58% lines/81.03%
branches, writer97.10% lines/89.02% branches;336 coupled tests87.475s plus20
managed tests20.54s.

Build5 passes65.728s under
`/var/tmp/web-008-artifacts-source3-5f88b83e878c`:

- Stock pinned UBI10-micro/no-Node image `241b49a647772f780bf0d85d99b43e72116800f5f74e3e7923b040a9024c0649`; `stock-foundation/proof.json` retains the foundation proof.
- Wheel `fb21d6875b6563aa8c913a751f82a8c1d8ab6f37611da60b02f0ba33a2bd0d24`; UI manifest `6be5570a8594eb3646d55103c421b3e373e366fbaa831e0cb0512ae09cdb499e`.
- Disclosed native0.2.10/rootless0.2.11 fixture projections:1383 inputs, snapshot `1fe6569f4029f369370b065789939c059e919e853e272470965143e2c11de0b8`, inventory `02d01f34a835f45e50f532c164f46470bbd2823596b63b13c42f23c4634bbb84`.

`source3-runtime-reuse-proof.json` independently proves that exhaustive-test
adoption changes only two tests/bookkeeping after this stock build. Artifact
reuse is explicit; fixture versions are not product releases.

### Installed acceptance:125 clean browser cases

Owned CentOS10/Enforcing, real read-only loopback NFS, strict verified TLS,
shared Caddy and actual installed API/helper are used. Full critical normal
paths pass in Chromium156.0.8078.4, Firefox157.0 and WebKit27.2. Expensive fault
combinations use the documented representative deeper matrix (testing strategy136),
not a power-loss simulation. All125 cases pass once: normal78 + helper crashes12
+ API crash3 + both legacy orders6 + tag race3 + final negatives23.

| Evidence | Original generation | Result and safe exact locator |
| --- | --- | --- |
| Native normal | `72aff191e2744f5d90384b678ae5f1e9` |39 cases/3 browsers,731.813s; `native-source3d-summary.json`, SHA256 `2ec875f419615542b134f7bba678c86c6da4a0b78c468b963f141a96319ccb9d`. |
| Rootless normal | `f5d30200d9d5429f905dfde8892b8499` |39 cases/3 browsers,964.94s; `rootless-source3e-summary.json`, SHA256 `99b45f64d25e0562e7f28ddd930d3644c4a357f79721ee84b0a9a0977e3056d6`. |
| Helper after pending parent fsync | `55ad849809c84a429deb90fc129fcf2c` |81.001s, unknown/pendingtrue; `deep-native-marker2-summary.log`. |
| Helper after staged rename | `d60ed7f705c647c39201f2f65bc12e22` |80.124s, staged/pendingtrue; `deep-native-staged-summary.json`. |
| Helper after exchange rename | `60040e5740474b0ca98709e2ea229b60` |81.581s, installed_unconfirmed/pendingtrue; `deep-native-exchanged-summary.json`. |
| Rootless helper after pending clear | `263aaa16759147b0aa67f14b25222337` |95.233s, confirmed/pendingfalse; `deep-rootless-confirmed-summary.json`. |
| API loss after effect | `48763d06fd4345369183cadeb705187c` |93.747s, actual API/helper SIGKILL, confirmed/no pending; restart has new API instance while Caddy/worker pairs remain; original-key recovery/no replay. `deep-native-api-crash2-summary.json`, SHA256 `897f4b380d9d8d09f9b12ca4c01ea5061db1d99dc811b915b3b0c442116171a2`. |
| Helper-first legacy contention | `89f5e6cc11204c9894cce5ca1fed8b23` |86.607s, actual `/proc/locks` holder+waiter FD9 on original inode92486144, fixed pending refusal exit1; staged/pendingtrue unchanged. `deep-native-legacy-helper-first-summary.json`, SHA256 `a289b9dcca7f77c3f3411fad231e19c251e09a55cfea0e5c3a3f21b8319dba47`. |
| Legacy-first publication/refusal | `e6b20d3db6e54f849454fe1642d2a7e3` |76.981s, genuine write exits0; one Apply is interrupted/unknownpendingfalse/no workspace, exact candidate retained. `deep-native-legacy-first-summary.json`, SHA256 `9b37b8f28b053218064d4caf0fce3e640d6f6c644cb4a38f7d2ef3852fef0e5b`. |
| External tag-only stale base | `02c91da72e3d49209ed5dc8b1038e28a` |71.381s, real legacy install changes disabled-model tags with the same operational fingerprint; staleApply409/zero new receipts, transmission or history effects. `deep-native-tag-race-summary.json`, SHA256 `f9f456ba16c177f400e78a9b8b870b87360dd181929291238c036607276de9c5`. |
| Final negative/quota suite | `b080429b817b49f18142ca784e7df78a` |23 cases,553.269s, passed/cleanupfalse; `native-negatives-phased-summary.json`, SHA256 `1c68a5232ac86aea6e5b01f604e550f212821991164fb039e9c200c4a963bb58`. |

Both normal profiles confirm nine actual applications with exact final candidate,
backup/predecessor/original-lock inodes,0640 root:hfcache/fullSID and unchanged
prior history/read-only archive metadata. Original role/browser processes,
cgroups and endpoints drain. Rootless retains original CID wait/exists proofs
and exact-six-ID opaque backup/sync/nonforce retirement. Original operations and
private phases remain unchanged through explicit disposable teardown; no Apply
is replayed and no product rollback or automatic ambiguity cleanup is introduced.

The final negative suite proves a failed preview against the actually stopped
owned TLS Hub cannot apply; an original successful preview is refused403 under
independent configuration-policy false without admission; and a genuine held Hub
request occupies the lane while a queued Apply loses permission and fails with
HFAPI002/zero transmission. Native's public test CA is inherited through a
scoped manager-client environment setting, verified in the actual API process,
then restored; indexed unit/empty drop-in paths and TLS checks stay unchanged.

Eight real quota cycles produce seven confirmed histories before the next
original application `e6a421052c2cddf60d4976ff5c71384b` is refused. Independent
root accounting finds15,517,860 used +2,558,664 reserve > unchanged16,777,216
bytes and joins the actual confined quota-guard frame at writer line678. Its
original outcome is unknown/pendingfalse; no limits or records are seeded or
patched. All457 browser requests are captured in nine ordered buckets
`[82,50,47,47,46,47,46,47,45]`, each retaining the canonical256-request bound and
exact closed-origin checks. One uninterrupted listener rotates synchronously;
root validates every prefix/final bucket and actual cycle order. The earlier
overflow failure is not promoted. Final original-role drain and whole-state/API/
credential retirement pass1.276s; installed573809-byte config, key and original
lock remain exact (`native-negatives-phased-owned-retirement.*`).

CONFIG06–11 have actual source/unit, real Unix/filesystem/Bash integration and
installed functional bindings in
[acceptance evidence](../support/web-ui/acceptance-evidence.json). Source and
installed proof are separate; no source adapter substitutes for a guest result.

### Retained failed attempts and fixes

Every original false flag remains. JSON result records below retain original
exits/durations and their raw log locators; gate2 was cancelled for the real
pending-before-workspace correction, not accepted. Intentional process-crash
assertions in passing cases above are separate from these failed test runs.

| Locator | Exit | Seconds |
| --- | --- | --- |
| `artifact-stock-result.json` | 1 | 0.168 |
| `artifact-stock2-result.json` | 1 | 35.127 |
| `deep-native-api-crash.result.json` | 1 | 90.94 |
| `deep-native-marker-owned-retirement.result.json` | 1 | 0.622 |
| `deep-native-pending-marker.result.json` | 1 | 91.331 |
| `gate1/strict-gate-result.json` | 1 | 1137.856 |
| `gate3/strict-gate-result.json` | 2 | 1368.915 |
| `native-negatives.result.json` | 1 | 583.528 |
| `native-functional-source2-result.json` | 1 | 370.814 |
| `native-functional-source3.result.json` | 1 | 2.221 |
| `native-functional-source3b.result.json` | 1 | 20.959 |
| `native-functional-source3c.result.json` | 1 | 294.82 |
| `native-offline-completion-result.json` | 1 | 2.246 |
| `native-offline-completion2-result.json` | 1 | 0.897 |
| `rootless-functional-source3d.result.json` | 1 | 6.453 |
| `source-native-staging-result.json` | 1 | 1.024 |
| `source-native-staging2-result.json` | 1 | 4.035 |
| `ui-rootless-staging-result.json` | 1 | 0.651 |

Additional original locators retained: `gate2/strict-gate.log`,
`browser-cache-relocation.json`, `native-failed-report.log`,
`native-first-effect-diagnosis.log`, `native-duplicate-load-diagnosis.log`,
`native-source2-credential-retirement.log`,
`native-source2-disposable-state-retirement.log`,
`native-source3c-result-summary.log`, `rootless-source3d-start-diagnosis.log`,
`rootless-source3d-prestart-credential-retirement.log`,
`deep-native-marker-journal-diagnosis.log`,
`deep-native-marker-fixed-journal-check.log`,
`deep-native-api-crash-failure-summary.log`,
`api-crash-original-application-diagnosis.log`,
`api-crash-original-host-outcome2.log`,
`api-crash-original-receipt-diagnosis.log`,
`api-crash-failed-owned-retirement.log`,
`native-negatives-original-summary.json`,
`native-negatives-original-diagnosis.log`,
`native-negatives-browser-infrastructure-diagnosis.log`,
`native-negatives-original-owned-retirement.log`.

Source2 generation `45ea660111f4475daf06818f436edd66` retains installed phase/
application `d31bd1d08466d98cacc160727191e935`; its swallowed historical exception
is unavailable. Independent root reads prove repeated full native inspections
exceed64MiB, not that the old exception was retrospectively captured. Source3c
`d4fc0cf83ae341aea4612673a2c64336` stays failed despite three confirmed host
outcomes: its aggregate browser case timed out and was split. Rootless pre-start
`90fa9d7d4ea940dc90559d8c36ec8525` stays false/cleanup-unknown; independent
drain/exact-ID proof precedes fresh correctly labelled empty Podman state,
without a new grant. Helper-fault `8f5f706adc624cbab74de7d0cfeb3351` reaches
exit91 but fails private journal boot parsing; the corrected test is fresh.
First API attempt `8a2d3aee0b9540718bd0aebb821a4a6d` fails its5s fixture wait
before host intent; operation `74da0cd545dc465036de08451713b545` stays interrupted,
unknown/pendingfalse. The abort check also needed exit-readiness/reaping
separation. That failed run supplies no API-crash acceptance; original state/API
store and result remain after explicit owned retirement1.097s.

First negative generation `1453e4d129d84f649144eebc7b894aba` fails583.528s even
though all25 application assertions pass: its passive recorder overflows at257
against limit256 and omits the tail. Copied summary SHA256
`581becdb19e554160a35cb4cf98e0747d982fbb8c43a31adb773f4a6992e62e5` stays
failed. Original refused operation `92fba6f0a25bb643a93fcdcd827912d9` remains
unknown/pendingfalse. Owned retirement1.312s preserves all original history/API
receipts/credentials and installed config/key/lock. Only private bounded
recording is corrected for the fresh passing generation, with the same per-bucket limit
and closed-origin checks. Early artifact/bootstrap/staging/pin failures, old
0.2.6–.9 releases and source1/source2 directories are retained.

### Contracts, documentation and operator handoff

ADR154 and amended ADR122/141/150/153, related ADR119/138/139, and affected
INV001/002/018/020/021 are reviewed together. API/configuration/security,
schema/server/host-administration, containers/deployment, historical frontend and web
configuration guides describe exact guards, first-lock provisioning, retained
0640 predecessors inside0700 state, stale conflicts and original-key recovery.
Gate5 validates210 human docs/27 helpers; final plan/evidence checks accompany
bookkeeping. [Progress and operator handoff](../../progress.md#operator-handoff)
and [current selector](../current.md) record completion and next WEB-009.

No production writer/NAS/archive initialization/installed predecessor interface, rollout, release,
merge, push or tag action is claimed. The owned guest, source/artifacts, original
failures and private evidence remain retained.
