# WEB-004: Add one Basic administrator through a replaceable principal boundary

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `5014fde960263f9ecd64f5f5b337e4f929beacaa90fffd73a0e7d34496cd772c`,
original content SHA-256 `c71b8be5de4429838415d6148b0ce1a211a71033960c1ddf476c296a1496dbdd`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P1 |
| Depends on | [WEB-003](web-003-typed-wire-contracts.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-004: add bounded Basic administrator authentication` |

## Read before implementation

api/auth.py, api/app.py outer middleware, server_config.py, server credential delivery; architecture security section and api-contracts.md; auth and CSRF acceptance rows.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement the configured single human identity and protected Argon2id hash/provider in the optional server closure. Keep stable subject/authentication-method metadata separate from legacy wire credential classes. Preserve REST bearer writer/reader and MCP bearer-only separation. Keep new administrative permission policy internal or in the independent UI/host projection; do not append unknown capability strings to the existing strict response.

Extend outer pre-routing authentication, body/capability checks and error/challenge handling, not only a route-level FastAPI dependency. Implement bounded credential parsing, verification concurrency, failed-attempt throttling, startup hash source validation and protected file/named credential delivery. No raw password in arguments, storage, logs, traces, fixtures or browser code. Do not accumulate attacker-supplied failed passwords in a global secret-redaction registry; scrub Authorization independently.

Require exact same-origin, JSON and a non-simple header for unsafe Basic browser calls; reject missing/null/foreign origins. Retain no-Origin nonbrowser bearer clients. Explicitly gate new admin capabilities separately from old writer capability; host proof integrates in WEB-006. Authentication failure must not invoke body parsing, domain work or credential-source fallback. Define native browser challenge and truthful logout limitations.

## Unit and component validation

Test wrong user/password equivalence, malformed/duplicate/oversized headers, corrupted/symlinked/hash sources, password-hash resource ceilings, credential class matrix, admin denial, CSRF media/header/origin cases, and unconditional credential redaction.

## Integration validation

Exercise real middleware on HTTP and Unix sockets with each credential class, both methods/prefix modes, errors/unknown routes/schema and MCP. Test concurrent bad-password requests while original operation reads remain bounded/available.

## Functional validation

Add real browser Basic challenge and authorized same-origin fetch tests, with no injected per-request Authorization shortcut for the positive browser flow. Exercise foreign-origin form/fetch refusal through an owned real origin; complete Caddy-specific proof in WEB-005.

## Human documentation deliverables

Create human deployment/login/security/troubleshooting sections with protected password provisioning, rotation effects, TLS requirement, single whole-archive account and no reliable app logout. Update server examples/strict schemas and security ADRs.

## Acceptance

One configured Basic administrator works without exposing a bearer; existing CLI/MCP authentication remains compatible; server-side admin/CSRF policies are enforced; missing or unsafe credential sources fail closed.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

Started after WEB-003 commit `2050d59`, its complete strict gate and clean status.
The user implementation authorization remains the active authority. Decision146
records the concrete provider/dependency/admission contract before source work.
Root owns server schema, dependency/packaging, contracts/docs/evidence and isolated
environment provisioning. Collaborators own protected record/provider/pool,
outer middleware/principal/key binding, and independent HTTP/browser acceptance.
They share this one work-package commit; no later task is activated.

Use the already locked cryptography50.0.2 Argon2id implementation as a direct
optional-server dependency, retaining base-reader independence. The immutable
single record is schema1 subject/username/password_hash, at most8192bytes, read
through the existing descriptor protection. Restart-only optional `[basic]`
contains exact canonical HTTPS `origin` and `[basic.administrator]` explicit
file/named source; the origin must also be in listener.allowed_origins. Fixed
parameters and budgets remain those accepted in the execution contract. Separate
internal administrative capability values retain the frozen route vocabulary;
legacy `.capabilities` and public credential classes remain unchanged.

No private attribution store is needed: version the Basic subject/key digest
preimage, preserve exact old bearer digests and strict receipts, and make no
individual-attribution claim for historical class labels. Bad Basic credentials
never fall back to another provider or register supplied passwords. Authentication
capacity/throttle refusal receives new HFAPI021/429/exit20, separate from existing
authentication401 and capability403; malformed startup sources retain HFAPI003.

Read-only prerequisites are preserved at
`.scratch/web-004-browser-survey-gn1uhg9_/` (public metadata only). Pin the official
Playwright1.64.1 Linux/amd64 test-image manifest
`sha256:bdfda2a8fdf48707c5e50a49bd3e06d8d0c759153dc8ee057d8a81c3450bb3e9`;
seven compressed layers total986271382bytes. The verified offline OCI archive is
now acquired at `.scratch/web-004-browser-image-9lgtjer0/`,986306560bytes,
SHA256 `9c01db924c8e888a235aa52f6ea7996bad19ca014ec363694787922077192f0b`.
Its explicit acquisition verifies each layer/config/manifest through system-CA
HTTPS; the initial unsupported-host-Python invocation failed before download and
is retained separately from the successful pinned-Python acquisition. Use only a NEW
owned CentOS guest and non-root sandboxed browsers with a private CA, never host
trust/runtimes or the five historical guests. Required real three-engine native
challenge and CSRF tests cannot be replaced by injected Authorization or TLS
bypass. Generate test passwords in memory and deliver them once over an owned
pipe to native httpCredentials; no password files/argv/env/traces/page scripts.
Shared-Caddy/static serving belongs to WEB-005. No production/NAS effects,
security weakening, publication, replay or cleanup is authorized.

The user's additional UBI10 requirement is recorded in the plan, resolved
execution contract, container contract and WEB-021 task: ship static UI assets
inside the existing pinned UBI10micro API image. No separate frontend image or
runtime Node/package manager is introduced. Noble browser dependencies are
unshipped isolated test tooling, not a product image base.

New guest `.scratch/web-004-guest-7iw3mnkg` has independent fixture identity
`web-004-83a4380d0c82465fa225c00bba53359c`, QEMU PID2146481/start399114947,
fresh overlay/seed/keys and only SSH loopback forward45419. Rechecked immutable
CentOS base SHA/backing chain; no gateway/DNS/external network/host share/NAS.
Actual guest CentOS10 kernel6.12.0-275, SELinuxEnforcing, rootlessPodman6.1 import
and image/config/ordered layers match the offline input. A finite non-root tool
probe timed out; subsequent inspection found no registered container. Preserve
its exact invocation/evidence. Default-overlay image preparation also timed out;
read-only inspection found a tree-walk stall, with no established underlying
cause. A separately owned VFS store imported and built the pinned browser inputs
successfully without changing SELinux, seccomp or host services. This is not
successful browser acceptance.
No historical guest is contacted or cleaned.

Installed-wheel browser attempts remain incomplete. The first refused fixture
directory permissions before API startup. The second stopped before container
registration because Podman6.1 rejected a tmpfs uid/gid option. The third uses
the documented tmpfs `U` ownership option with private mode0700; its exact owned
container started and drained, but Chromium launch and Firefox context setup
failed. WebKit passed seven cases and failed the version/challenge assertion.
The failure path closed the three listener sockets but did not prove Uvicorn
task/lifespan shutdown or authentication-worker joins; correct the fixture's
cleanup ordering and prove failure-path drain before accepting a rerun.
Keep the bounded reports at `.scratch/web-004-guest-auth-progress-third.log` and
the guest's private `evidence/web-auth-w68ujfeb`; no required browser case is
accepted by this failed run. Investigate these failures with normal sandbox and
certificate validation retained, then rerun both prefixes and all three engines.
The first complete strict source gate exited0 (5896 Python tests). At that point
a fresh gate was running against updated fixture guards. Neither of those source
gates supplies the then-missing functional proof.

The fourth installed run uses corrected real version fields, reviewed lifecycle
cleanup, and a new browser-only seccomp profile. The latter permits Chromium's
mandatory namespaced `chroot` while retaining zero outer capabilities,
no-new-privileges, enforcing SELinux and all unrelated filter rules; product and
worker profiles are untouched. A separate credential-free Chromium diagnostic
proves namespace/PID/network/seccomp sandbox protection and exact process drain.
In the authentication run, Firefox and WebKit each pass8/8 root-profile cases.
Chromium's sandbox page reports adequate protection, but descendant inventory
refuses an empty command line. Investigate corroborated zombie/exit state without
relaxing live-process checks. This fourth run remains failed and never reaches
the prefixed profile. Its three API lifespans/listeners drain cleanly, all exact
authentication workers join, and the configured archive remains absent. Keep
the original evidence at guest `evidence/web-auth-lt0l_h0g` and
`.scratch/web-004-guest-auth-progress-fourth.log`.

The fifth run correctly retains observed zombie identities and proves their
reaping. It still fails Chromium verification because Chromium156 flattens its
child argv into one lossy process-title string; exact `--type=renderer` detection
therefore missed live renderers. Keep `evidence/web-auth-jh84gop5` and
`.scratch/web-004-native-fifth-postverify.log`: both other engines again pass8/8,
all three API lifespans/listeners and exact authentication workers drain, and
the source/wheel/installed inputs revalidate. The corrected parser distinguishes
normal argv from the exact pinned Chromium title, scans unsafe flags in both,
and preserves the title's unrecoverable boundaries/truncation limitation. It
does not replace kernel/namespace/seccomp proof. Independent review and actual
process-title/zombie tests pass; credential-free exact-verifier and full
authentication reruns remain required. The second complete strict gate also
exits0 (5927 Python tests), but later fixture corrections supersede its source
identity. Keep both earlier successful gates and every failed browser attempt.

The sixth run passes all24 root-profile browser cases and verifies three live
Chromium renderers, but its Firefox process cleanup inventory cannot classify a
rewritten child title. It remains failed. Separate bounded PID/start/parent/state
cleanup identities now cover those children without granting them command or
sandbox authority; exact Chromium renderer checks remain mandatory. Actual
process-title/zombie/reaping tests and independent review pass. Keep
`evidence/web-auth-xunhevwn` and
`.scratch/web-004-native-sixth-postverify.log`; all three API lifespans/listeners
and authentication workers drained. The seventh run then passes Chromium8/8 and
Firefox8/8, but WebKit's untrusted-certificate navigation fails without matching
the strict expected certificate diagnostic. Its original inner exception was not
retained, so the cause is unknown; no broader network-error classification is
accepted. Keep `evidence/web-auth-n1oc4ub1` and
`.scratch/web-004-native-seventh-postverify.log`.

The eighth run adds bounded scrubbed navigation diagnostics without changing
certificate acceptance. All24 root-profile browser cases pass, all engines
report explicit unknown-CA errors for the untrusted endpoint, three live Chromium
renderers have sandbox proof, and all observed processes/containers/API lifespans/
listeners/authentication workers drain. Independent HTTP acceptance still refuses
the run: Firefox and WebKit produce actual foreign-origin OPTIONS401 responses,
but Chromium produces no observed OPTIONS. A generic browser fetch refusal is
insufficient proof. Investigate that missing request before rerunning both
prefixes; the prefixed profile has not run. Keep
`evidence/web-auth-c19jab7z`,
`.scratch/web-004-guest-auth-progress-eighth-diagnostics.log` and the safe HTTP
observations in `.scratch/web-004-native-eighth-observations.json`.

Independent eighth-run postverification at
`.scratch/web-004-native-eighth-postverify.log` (SHA256
`7036b82a368ba303d099a84d8125df77999b9d414eaded8dd09920860a6e385d`)
revalidates all1278 source,183 browser and97 installed/wheel files, matching
canonical driver copies and exact process/container drain. Three independent
reviews identify the missing-preflight cause in the
[pinned Playwright source](https://raw.githubusercontent.com/microsoft/playwright/v1.64.1/packages/playwright-core/src/server/chromium/crNetworkManager.ts):
user request interception auto-fulfills Chromium OPTIONS with synthetic204 CORS
responses. The actual foreign JSON POST still receives API403, but that does not
replace required real OPTIONS proof. Remove request interception from this
native CORS fixture; use bounded nonintercepting origin observations inside the
already independently network-isolated guest, retaining all API-side proof and
native browser authentication. No product CORS or authentication change follows.

The reviewed correction passes87 Python helper/lifecycle checks and21 actual
process/metadata checks with no skips; format/lint/types pass. The ninth real run
then exits0 in57.487s against the installed wheel: all48 browser checks pass
(three engines, eight cases, root and `/management`, zero failed/skipped). The
independent parent and postverifier both require actual trusted AND foreign
initial401/native Basic200 ordering, same-origin JSON200, authenticated foreign
simple/form403, one real API OPTIONS401/403 per engine/prefix, explicit unknown-CA
rejection with zero untrusted HTTP, and bounded passive origin observations with
request interception disabled. Chromium has three live verified renderers per
prefix; all50 observed descendant identities close. All six API task/lifespan/
listener records drain, exact authentication workers join with counters0, both
owned containers exit0/Pid0 and their init/launcher/client identities disappear.
The three provisioned ports are no longer listening; the configured archive
remains absent. This proves installed API authentication inside the owned guest,
not built UI/Caddy, installed systemd/native/rootless application roles or NAS.

Retain guest `evidence/web-auth-lp47kqw4` and
`.scratch/web-004-native-ninth-postverify.log` (SHA256
`53756288095aa0be93ac2c9632f5fd07288c44d1ebe0c0886110108092c30619`).
Its complete original manifest validation and both `accept_evidence` calls pass;
all1278 source,183 browser and97 installed/wheel files match. Manifest9 SHA256 is
`19fdeb4feac00e0a822aa04f77a670667aff5993a534c883fd1df1296b311d7c`,
source-inputs-v8 is
`bbc194e8995b6f9cc6f81a64d6ada3726c90c56756703bfea896242773eb2a9c`,
and the source snapshot is
`efbae890cd84358374875f84eb7c6250c0965b745e71dd352c17f4fc24179ae5`.
The wheel SHA256 is
`847d852da501ab23e6b23f13ca0e2eeb4134ce033788ce8c45b917232b47cd90`;
its application version remains0.2.2, a source-test artifact rather than a claim
that the existing production0.2.2 has this feature. Exact actual arguments,
per-profile browser/API/container artifact hashes, dependency and tool identities
are retained in the postverify log. All earlier failed attempts stay failed.

After this independent verification the fourth strict source gate runs with
Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.
source snapshot and exits0; complete results are recorded below. Preserve
`.scratch/web-004-fourth-gate-command.json`,
`.scratch/web-004-fourth-source-before-gate.json` and
`.scratch/web-004-fourth-strict-gate.log`. Only this task, the dated plan, current
selector and progress bookkeeping are excluded from the frozen source inventory;
runtime, tests, human docs, ADRs and acceptance ledger stay frozen.

The required fixed-profile benchmark is real local work, separate from guest or
production performance claims: `.scratch/web-004-argon2-benchmark.json` SHA256
`01becbfa7cd1a4293c551d3517cd37aef1f153118cc5508381e81db84560b6d7`.
Python3.14.6/cryptography50.0.2 on four logical CPUs measures derivation331.79ms;
eight serial verifications per class have medians344.269ms(correct),
344.498ms(wrong user),345.461ms(wrong password). Four concurrent pairs take
478.333–536.564ms, maximum event-loop heartbeat gap8.084ms and peak process
RSS175128KiB. Actual active/waiting/reservations end0 and all exact workers join.
This supports the accepted64MiB/t3/p1, two-worker/eight-waiter profile without
claiming universal latency or installed workload/NAS performance.

A third source gate stops with exit1 at human-documentation validation because
ADR146 contained agent-task links/identifiers; no Python or browser tests ran in
that invocation. The narrow prose correction passes the documentation check
(199 human documents/23 helpers). Preserve
`.scratch/web-004-verified-final-strict-gate.log` and
`.scratch/web-004-adr-link-corrected-docs.log`. That refusal left a complete new
gate required after functional acceptance; the fourth gate below supplies it.
No earlier gate or failed browser attempt is relabeled as final acceptance.

## Completion evidence

Completed2026-10-20, `WEB-004, this commit`, parent
`2050d59cdd204cdecdcd438275cbb44b92e67314`. The optional protected Basic provider,
strict canonical schema1 provisioning, independent administrative grants,
stable-subject original-key namespace, bounded off-loop verification, CSRF and
unconditional credential redaction are implemented. Legacy bearer digests,
public capability/class vocabulary, receipts and read-only MCP remain compatible.

The final installed-API functional command is:

```text
/home/webfixture/hfcache/.scratch/provisioning/installed-env-v2/bin/python /home/webfixture/hfcache/scripts/check-web-auth-fixture.py --manifest /home/webfixture/hfcache/.scratch/provisioning/auth-manifest-v9.json
```

Actual exit0 in57.487s, Chromium156.0.8078.4/Firefox157.0/WebKit27.2,
root and `/management`, eight cases each:48pass,0fail/skip. Exact evidence,
unchanged source/wheel/tools, sandbox and complete cleanup are recorded above
and independently verified in postcheck SHA256
`53756288095aa0be93ac2c9632f5fd07288c44d1ebe0c0886110108092c30619`.

Actual final source gate `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)`
exits0 in1107.599s. All1278 inventoried files remain unchanged, with the same
`efbae890cd84358374875f84eb7c6250c0965b745e71dd352c17f4fc24179ae5`
snapshot used by the real guest. Python:5940pass/52default marker deselections,
858.43s; base/server/server+MCP clean wheel installations pass. historical frontend572unit
and110mountedFirefox pass. Web21sandbox/process,2722unit/2748combined component,
two built-shell and14real-API React read checks pass with no required skip,
retry or omitted execution. Combined component repeats units; counts are not
summed as distinct scenarios. Coverage95.85%lines/92.94%branches/93.93%functions/
94.83%statements. The required22 stages and six positive reports are independently
audited; owned read-fixture browser/API/listener/pool drains and built hashes match.

| Final evidence | SHA256 |
| --- | --- |
| `.scratch/web-004-fourth-strict-gate.log` | `f8a8641d59e66327c86ce04715518ba2d0501141a573b65ad30862f4585252a0` |
| `.scratch/web-004-fourth-gate-result.json` | `f81ac7d4afa3c6b36b244dc4798a62432db8f934754e2f077176c12f2a0d6ef0` |
| `.scratch/web-004-fourth-gate-independent-audit.json` | `b5f07eded18dcd4351e75a14b54a577f5c35088b47c5942ca1cdec8aad1bbf84` |
| `web/.artifacts/auth-sandbox-9vltj1/report.tap` | `6fabbb1a1072251334c3beface83f44261d8fb67509b41abddad841a0790c867` |
| `web/.artifacts/unit-FQuqOe/report.json` | `c030c797bf09370266a082d18bb9d15b6a0229d0304aa72e64942d2cc4f83f84` |
| `web/.artifacts/component-ZOja1n/report.json` | `f3d0e0c92294196b152456b4c84251d32c46887c1bc6f1f0487d2530e9af7a05` |
| `web/.artifacts/component-ZOja1n/coverage/coverage-summary.json` | `48099df325c8822cb07ebb8b89b653018220dc21dc26c39866daa8203eaa1ba3` |
| `web/.artifacts/browser-UIOd2V/report.json` | `773473d733298ee131a3ffb0d9e4a282e944cd2acd1db0f292f7fe19086f0071` |
| `.scratch/web-read-fixture-c4p0puyq/root/browser/run-3xm1bn/report.json` | `a0dab2e140820291b076629ebc8ff8d441f33f2a7907af286741780b3b17a4cd` |
| `.scratch/web-read-fixture-c4p0puyq/prefixed/browser/run-O7HFGu/report.json` | `a78dcc3d9e522e44092421f3b3526e93b1653c8855dca28540ca853f5334f295` |

Task-level native mapping: AUTH-01 uses `native-challenge-version`,
`same-origin-capabilities`, `same-origin-json-post`; AUTH-05 uses `foreign-text`,
`foreign-multipart`, `foreign-form`, `foreign-preflight`, each in all six
engine/prefix combinations. `untrusted-ca-refused` supplements AUTH-09 without
claiming its future Caddy layer. Basic class projection supplements AUTH-04;
wrong/malformed credentials, protected-source/rotation, bearer/MCP separation,
no-Origin clients and flood/cancellation bounds retain their actual source-hashed
unit/real TLS/Unix integration mappings for AUTH-01–07 in the
[acceptance ledger](../support/web-ui/acceptance-evidence.json), SHA256
`fa8f3d8bba5aa028b2c76b70c9616e6dbe7131236490eb03565cab8b04167bda`.
All95 feature-case completion statuses and required built-UI/shared-Caddy layers
remain pending. Neither the direct-TLS guest nor temporary read fixture proves
Caddy/static serving, installed native/rootless application-role confinement,
host controls, production/NAS acceptance or historical frontend retirement.

Human deployment/provisioning/login/rotation/TLS/logout/troubleshooting guides,
navigation, server examples, API/server/security/schema/CLI/development/script
references and container/deployment boundaries are synchronized. The final gate
validates199human documents/23helpers. Decision146 and amendments112/113/114/140,
FW-03/04 and INV-001/002/003/013/014/019/021 are reviewed; archive/publication/
locking AD-15/16/17/18 and original operation/no-replay rules are unchanged. No
new archive durable format or legacy capability is introduced. Cryptography is
the already locked maintained dependency, made direct only for the server extra;
base-reader independence passes actual installation checks. The user's UBI10
requirement remains allocated to the existing pinned micro API image in WEB-021.

Original failed/superseded gates, all eight unsuccessful native attempts and
unrelated earlier guests/stores/handles remain preserved. Progress records this
completion and Operator handoff33 retains the deployment limits. Current selects
WEB-005 after this one work-package commit; no production or remote action follows.

After the four bookkeeping records were completed, documentation alignment again
passes199human documents/23helpers (log SHA256
`e814f92a1e9ac51b3871b3bbfe977eddc2915316e962bb61847ab1f2fae87e46`).
Actual `uv run --locked --extra server --extra mcp pytest
tests/unit/test_web_plan.py tests/unit/test_docs_migration.py
tests/unit/test_docs_alignment.py -q
--junitxml=.scratch/web-004-post-bookkeeping.xml` passes53tests in7.13s,
zero skips; XML SHA256
`d05f2a0ddf7a96e9462acb8d1e69abb5214225b64d99f71380727e91bc7f74e0`.
Whitespace checks pass; complete git source-path inventory and all1278 frozen
hashes still match, with only the four declared bookkeeping exclusions.
