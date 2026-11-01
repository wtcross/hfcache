# Testing strategy and required gates

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `8d5d44ace8851f765db49061d0681d8f353c859fe4000617fb52073edbcba560`,
original content SHA-256 `6516d150180d8308957acadbcc2b1209853c259e14e73af57caa1dd14c4986aa`.
Historical proof hashes identify the original artifacts, not this edited record.

Testing is part of every work package, not an end-of-project phase. A screen backed only by mocked HTTP responses is not functional acceptance. A green test count does not prove host/NAS safety or deployment. Requirements and planned checks are not passing evidence; completion records must identify what actually ran.

## WEB-023–026: bounded product testing and effort

Test the actual product workflow first. Add no new harness, proof schema,
framework or binder. Reuse retained artifacts, fixtures and passing evidence only
where source/artifact/profile/assertion scope still matches, recording the reason.
Repair existing machinery only for a concrete missing product assertion; retain
its failed result, make the smallest supported fix and return to the workflow.
Stop a machinery-only loop and record the specific unblock condition. Never repeat
an accepted mutation or unresolved operation to replace missing observation.
Rerun for a relevant source/artifact change, failure/contradiction, uncovered clause
or required gate, with the reason and affected scope recorded.

Use `gpt-6.1-sol`: WEB-023 high, WEB-024 medium, WEB-025 high, WEB-026 medium.
Use low for routine edits/commands. Raise medium to high only for a concrete
unresolved safety, compatibility or implementation contradiction. Consider
xhigh/max only after naming the unresolved issue and expected benefit; neither
is a default or permission to expand infrastructure/repeat accepted effects.

## 1. Layers and ownership

| Layer | What runs | What it proves and does not prove |
| --- | --- | --- |
| Python unit | Existing pytest fixtures plus new auth, schema, config, card and helper protocol tests | Deterministic validation, invariants, refusal and crash-state classification; no live installation proof. |
| TypeScript unit/component | Vitest or an explicitly justified equivalent, React Testing Library, user-event; exact runtime decoders and state machines | Real React interactions, strict types, URLs, scope, errors, keyboard/focus and mutation intent. MSW/fixtures may isolate components but are labelled mocked. |
| Backend integration | Real ASGI application/operation runner, real HTTP/Unix sockets, actual persistence; injectable fake Hub and owned storage fixtures | Service interaction, receipts, metadata and config boundaries, no replay; never replaces authorization/business services with fake JSON responses. |
| Application functional | Production-built SPA in real browsers -> real Caddy TLS -> installed hfcache app -> existing service layer/private worker and narrow helper fixtures | Actual routing/auth/header/asset/browser/API interaction. Only external Hub/storage boundaries may be deterministic test doubles. This is not proof of live NFS or production SELinux. |
| Platform functional | Disposable, isolated CentOS-compatible guests with actual systemd/rootless runtime/helper/Caddy, private test PKI and owned local fixture state | Effective manager/peer/mount-policy/cgroup/permission behavior, supported native positive paths and guarded rootless denials. Never uses the production writer's managers or archive. |
| Human workflow acceptance | The same built test deployment, following published operator/user guides | Discoverability, explanations, safe task completion and screenshot accuracy; manual records supplement, not replace, automated tests. |

## 2. Provider-neutral execution interface

The existing contract intentionally avoids CI-provider-specific configuration. Extend `scripts/check.sh`; do not introduce GitHub Actions or another CI platform merely for this feature.

WEB-002 introduces the strict web gate and a documented `web/package.json` script contract:

```bash
pnpm --dir web install --frozen-lockfile
pnpm --dir web run lint
pnpm --dir web run typecheck
pnpm --dir web run test:unit
pnpm --dir web run test:component
pnpm --dir web run build
scripts/check.sh --require-web
```

These commands define the existing web source gate. `--require-web` refuses missing toolchain, generated schemas, browser prerequisites for selected component tests, failed tests, and skipped checks. It runs the existing backend gate too. Legacy plugin validation is outside the remaining scope.

### Required source gate and direct installed acceptance

The required full source gate remains:

```bash
scripts/check.sh --require-web --with-build
```

Keep its web, build and backend checks strict.
Source checks and installed product acceptance are separate requirements. Account
for all 85 scenarios owned through WEB-022 and all 95 at final acceptance, including
every required clause and the existing `minimum_layers` in
`acceptance-cases.json`. Use appropriate unit/component, integration and direct
installed workflow evidence; every case need not run in every browser/profile
cell. A source review, intended test name or mocked response is not an executed
product observation.

On both installed native and rootless profiles, exercise Chromium, Firefox and
WebKit at the root and `/management` Caddy entrypoints with fresh browser
contexts and the existing browser installations. Cover authentication/routing,
Library/filter/detail/README/Files, configuration forms and representative
request/error handling. Run deeper domain and fault combinations at the actual
boundary where they matter, once where equivalent and repeated where a runtime
difference requires it. Supported native controls and maintenance/Repair remain
required, as do rootless schedule/observer denials. Real CLI and all 14 MCP tools
must traverse the trusted shared Caddy at both aliases, including actual
browser/client overlap; distinguish protocol checks from genuine worker reports.

Reuse existing scripts, fixtures and passing unchanged-subsystem evidence with
an explicit scope and unchanged-source/artifact justification. Repeat work for
changed behavior, unresolved failures or uncovered required clauses. Preserve
original failures, accepted-operation identities and uncertainty; never replay
an accepted effect to manufacture a passing aggregate. Missing clauses block
completion. This acceptance path requires no new framework, schema, proof model,
binder, run-ID join or fresh instrumented lifecycle expansion.

### Existing optional instrumented-runner contract

The existing provider-neutral `scripts/check-web-functional.py` runner remains
an optional diagnostic, with its current profiles, owned workspace and strict
validators unchanged. Its safe help command does not inspect runtimes or
credentials. The following composition is optional:

```bash
scripts/check.sh --require-web --with-build --with-web-functional
```

When explicitly invoked, `--with-web-functional` still requires **both** completed
application and platform profiles with its existing final selector. Missing
Caddy, browsers, immutable images, certificate tooling, guest support,
private-worker support or offline dependency closure exits nonzero; 'SKIP' never
passes. Its reports retain source/artifact/fixture identities, nonsecret command
arguments, exits, test node IDs, browser versions and pending/blocked cases.
Neither this flag nor the runner's `--require-through`/`--final` path is required
for direct installed acceptance, and direct evidence must not be reported as a
passing runner invocation. All private fixture/proof requirements below apply
only when that optional instrumented runner is used.

Historical 2026-10-31 optional-runner execution correction: run canonical native/application and rootless
profiles on their explicitly owned, boot-bound guests without moving or mixing
`/opt/hfcache/current` layouts. Application may use canonical native confinement,
with distinct fresh executions. Explicit local `--profile
application|native|rootless` keeps the existing exact3 manifest profile keys,
validating complete common source/wheel/UI/toolchain authority and only selected
bindings. Rootless additionally requires root-owned immutable unselected
`installed.tooling={prefix,python:{path,sha256}}` with actual interpreter/import and
complete same-indexed-wheel verification; this SDK never substitutes for live
container/actor/selected-image evidence.

One fresh32hex `--run-id` binds the three local invocations. Before any role
admission, persist exclusive fsynced schema1 `RUN-INTENT.json`: run_id, profile,
fixture_id, guest{identity,boot_id}, manifest{path,sha256}, original workspace.
Runtime/browser report/role RESULT/SUMMARY repeat run_id; SUMMARY retains the intent
record and original context. Use existing `run_profile(browser_engine=...)` for each
profile/prefix/engine:18 fresh fixtures and paired ready/stopped lifecycles, never
one mutated fixture shared by three engines. The fixed helper stays identical within
each pair; reviewed canonical preparation/rebinding between pairs preserves prior
state. Browser-launcher parsers and driver/runner exact-key validators must bind
run_id/browser_engine and expect only that selected engine. No new engine CLI,
skipped prerequisite or changed45s callback/navigation/locator/launcher budget
follows.

After all close, the same runner joins exactly three fresh normal SUMMARYs using
`--profile all --run-id ID --manifest ABSOLUTE_PROTECTED_JSON --join-summary PATH
SHA256` (three summary arguments), plus `--require-through WEB-022` or `--final`.
The explicit manifest validates common source/indexed wheel/UI/toolchain bytes only;
no wrong-host boot, selected-native, service-account or live rootless checks run
offline. Original profile manifests/intents/proofs supply guest/boot/selected-role
authority. Common runtime artifacts and complete test-source/toolchain snapshots
match; profile-specific fixture, boot and installation descriptors remain distinct.

Launchers retain finite required public proof copies inside their workspaces, with
originals/recorded metadata preserved. The offline resolver only strips the exact
recorded original workspace prefix into supplied SUMMARY.parent; reject
outside-workspace imports, symlink ancestry, `..`, arbitrary rewrites and
missing/hash-mismatched bytes. Preserve original records/guest paths: copied
device/inode/timestamps never claim remote re-observation, and finalization performs
no remote/protected-selector/network/credential work. Reject old one-offs, status
stamps, retries, missing/duplicate cells/generations, unknown drains and pending
assertions. Recompute existing acceptance_executions→case_summary and unchanged
require_cells/through/final:85×18 through WEB-022,95×18 final. An explicitly
requested final instrumented-runner invocation must use this same strict path.
These historical private protocol corrections do not require that optional path
for current acceptance and grant no runtime or invariant change.

Where the execution host cannot provision isolated guests safely, retain the task as blocked and run independent source work that is genuinely ready. Do not weaken new-web acceptance, run production host operations or claim installed independence from component fixtures alone. Legacy deprecation follows the explicit user amendment, with no plugin removal or further plugin validation.

## 3. Hermetic fixtures and safe environment

Use deterministic synthetic repository fixtures (fictional model and dataset identities), tiny complete manifests/ordinary files, bounded card examples, retained/current publications and known verification reports. Include enabled, disabled, unpublished, unmanaged, empty tags, last-observed tags, unknown metadata, multiple quantizations, incomplete shards, adapters/projectors, dataset declarations, changed current pointers, repaired publication IDs and malformed supplemental records. No large model download or real account is needed.

Inject the fake Hub at the supported adapter boundary. Unit/integration and application functional tests may inject a clearly labelled storage/mount-table fixture at the existing test seam; **do not** add a production environment flag that disables archive preflight, authentication, symlink checks, or locking. Test HTTP still reaches the actual production routes/services, not a fake `/api/v1` fixture server. Verify installed module bytes against the selected wheel for artifact functional tests. Mark storage-simulation evidence as such; it cannot close an NFS acceptance hold.

Platform tests use actual isolated managers and rootless identities. Positive native schedule/config paths must run against real guest systemd; rootless tests prove fixed denied schedule/observer behavior unless a supported binding already exists. Root-capable test code runs only inside an owned isolated guest with explicit fixture identity. No host rootful container, privileged fallback on the writer, broad bus/socket bind, container security disablement or global policy edits. All scratch paths must be local, outside `/srv/hfcache`, release selection, production config and control stores. Do not run `hfcache archive init`, including 'just for testing' on the host; construct synthetic archives through owned test fixture builders. Any genuinely real NFS fixture requires a separately authorized disposable export; lack of it never justifies touching the live archive.

Generate test-only credentials and TLS certificates in mode-restricted workspaces. Trust the test CA in browser contexts/OS trust inside the guest. `ignoreHTTPSErrors`, curl `-k`, wildcard host allowances or permissive CORS do not count as a positive TLS/auth test. Negative untrusted-certificate tests explicitly prove refusal. No external requests are allowed during test execution except isolated fixture services. Build dependency provisioning occurs separately, from pinned/hashed inputs, and never pulls images automatically during runtime/gates.

Isolation tests inspect actual processes/peer credentials and bind visibility, not only rendered command strings. Worker cannot read Basic/bearer/Hub credentials or contact IP networks; Caddy cannot read archive/policy/host-helper state; UI assets contain no secret values; API remains non-root. Do not erase failed containers/workspaces/uncertain operation evidence automatically. Cleanup owns only positively identified fixture resources and runs only after observed process termination; failed drain is a retained blocker.

### Existing optional instrumented proof details

The following private metadata protocols remain strict if the instrumented runner
is invoked; they do not require new proof machinery for direct installed
acceptance. Actual installed confinement and denials remain required above.

Retain actual rootless `cap_drop` inspection entries without normalization. Test
both literal `ALL` and the exact unique11-name encoding in the
[execution contract](execution-contract.md); reject missing, extra, duplicate,
nonstring and arbitrary lists. Require the unchanged original create request to
drop ALL with no capability addition and actual role `CapEff`/`CapBnd` zero;
either metadata encoding with live nonzero capabilities must refuse. This is a
private proof correction, not a weaker policy. New canonical validator bytes
require a new source/gate and fresh installed all-six acceptance; old failed or
unknown records remain unchanged.

Caddy INET proof tests retain raw listener rows without normalization and cover
both closed rootless families in the [execution contract](execution-contract.md):
IPv4 `tcp` with optional `udp` at `0.0.0.0:8443`, or IPv6 `tcp6` with optional
`udp6` at `[::]:8443`. Require TCP, at most two rows, exact closed row types/keys,
unique protocols and positive unique kernel inodes. Reject mixed families,
UDP-only, wrong addresses/ports, aliases, mapped addresses, booleans, unknown
fields/protocols and duplicate/extra listeners. Application/native loopback rows
and rootless outer `127.0.0.1` publication/strict TLS are unchanged. The proof must
join actual socket FDs to the bound process/namespace and retain original normal
drains; a corrected metadata predicate supplies no historical missing observation.
New canonical proof bytes require a new source/gate and fresh installed all-six
acceptance, even when packages, images and Caddy configuration are unchanged.

## 4. Core regression families

**Authentication/routing:** native Basic browser challenge; valid and invalid credentials; missing/unusable hash; rate/concurrency bounds; wrong credential class; TLS/Origin/CSRF; repeated/malformed auth headers; direct Unix auth; spoofed proxy/user headers; unsupported methods; SPA versus API/MCP route precedence; deep links/assets/base prefixes; missing asset 404; no secret leakage; no HTML rewrite of API failures. Use the same Caddy endpoint for authenticated REST bearer and MCP tool calls while the browser is active.

**Configuration:** hidden/protected field preservation; exact-byte CAS including tags; deterministic managed-edit reconstruction; validation/preview/apply correspondence; blocked authority changes; filesystem ownership/modes; persistent original lock inode; stale base/queued policy; service identity; two browser tabs; existing candidate and backup preservation; incomplete helper/API response; every backup/install/fsync/result boundary; exact read-only reconciliation; no new key after uncertainty; unchanged old literal-candidate CLI behavior.

**Cards:** exact publication provenance; successful/absent/not-captured/oversize/invalid UTF-8/redacted cases; hostile paths/symlinks/special files/replaced inode; nested and expensive Markdown; JSON encoding expansion; capture failure warning without corrupting publication outcome; unsupported records preserved; no GET payload access, Hub calls, lock acquisition or write; pruned/current-race behavior; source digest mismatch; no raw secret exposure; no scripts/iframes/SVG/forms/external assets/unsafe protocols/DOM clobbering. Test the actual browser's request log and DOM, not only sanitizer output strings.

**Catalog/presentation:** identity-safe join of paged catalog and status, known totals and coverage; zero known matches with partial coverage; same-variant filter semantics; datasets rejecting model-only filters; unmanaged provenance; literal ID/tag search; safe-range/lossless integers; stale cursors/limits; exact detail switching; manifest budgets and virtualization; metadata coverage separate from integrity; query races and auth/archive changes.

**Operations:** original-key persistence before POST; response lost before/after acceptance; route unmount/reload/tab/storage corruption; quota before and after transmission; event gap/overflow; expired/missing receipts; no replay/cancel; restored terminal metadata revalidation; 202 versus completed results; failed HTTP-200 Envelopes; busy/partial/integrity outcomes; observer stop versus actual executor; no payload or credential persistence in browser storage.

**Maintenance/host:** fresh preview/apply scope, exact-SHA repair, protected current and unmanaged-only purge, quarantine IDs, lock conflict, recovery unknown preservation, supported schedule calendar/reset/timer operation, verification timer read-only, no target stop, release-policy drift/unknown host helper, service manager mismatch, bounded logs and evidence separation.

**Packaging/documentation:** asset/wheel/index matching, enabled UI missing assets refusal, base reader without Node, same app lifespan, immutable rootless assets, production prefix, real installed old CLI/MCP compatibility, durable-format downgrade refusal and preservation, no default production effects, protected deployment/rollback examples, operator procedures matching current labels and behavior.

### Static stream interruption evidence

Finite streaming deadlines, disconnect handling and resource-lease release remain
required at the appropriate real integration and installed boundary. Retain
actual browser behavior, source/artifact identity and normal process/resource
closure; source review alone cannot establish an exercised runtime outcome.
Client zero-DATA or a later reset must not be relabelled as proof of an upstream
paused send or cancellation.

The following is the existing optional instrumented-runner protocol, not a
required new collector or lifecycle-proof expansion for direct acceptance. Use [execution-proof schema2](execution-contract.md#static-streaming-execution-proof-schema2)
for the private six-probe transfer inventory. Preserve raw ASGI normal-return and
exception counters; they are not protocol-submission or client-delivery counters.
Capture passive before/after states from the exact pinned original bound H11
cycle/flow/transport, and independently derive submitted, disconnected-noop and
raised outcomes. Join the original accepted-socket inode/buffer/source sidecar;
never override send/receive/write/scope/body behavior to manufacture a failure.
Inner API PID1 is valid when the independent namespace/host mapping proves it.

Cancel proof needs a real paused/non-disconnected original await spanning the
client's cancellation and ending disconnected/incomplete, plus original Node
TLS/HTTP2 zero-DATA/RST and actual http.disconnect. Deadline proof separately
needs actual CancelledError at>=29s in that paused original await, with the
client holding>=35s. Both require incomplete protocol submission, final=false,
zero before/after stream/task counts and all original role/browser drains.
Generic network exceptions anywhere make the transfer unknown/refused. A later
RST, instant pre-disconnected no-op or completed response cannot stand in for
stalled-send proof. Actual normal ASGI returns remain normal returns.

Exercise real original-cycle Unix transports, connected completion, paused
disconnect, genuine cancellation and closed/socket reuse boundaries; cover
wrong method/cycle/flow/protocol/source/identity, copied boolean numerics,
missing/extra fields, result/counter disagreement and generic/early failures.
Keep all failed schema1 reports unchanged. This corrects private evidence only;
it changes no product behavior, declared resource bound or public wire format.
Within that optional protocol, new source/gate identities and all six installed
profile/prefix generations remain required; old failures cannot supply them.
Direct acceptance instead uses the appropriate required layers and installed
observations above, without fabricating the private runtime counters.

## 5. Browser, accessibility and performance gates

Installed browser acceptance covers native and rootless profiles in Chromium, Firefox and WebKit, pinned with the test tool version, at both prefixes. Cover core authentication, routing, reads/writes and workflows in those cells; use a documented representative deeper matrix for domain/fault boundaries rather than every case in every cell. Use auto-waiting assertions, semantic role/name locators and explicit bounded timeouts; no arbitrary sleeps as correctness conditions. Record retry counts: a test that passes only on retry is flaky evidence to resolve, not a silently clean run.

Exercise keyboard-only navigation, visible focus, dialog focus trap/restoration, form labels and validation announcements, accessible status/error regions, table headings, reduced motion, contrast, and responsive layout at representative 1440px and 390px widths plus 200% zoom. Use automated axe checks with zero serious/critical violations in covered screens and manual keyboard/screen-reader smoke records; automation alone is not a claim of full accessibility conformance. Keep external fonts and network assets disabled.

Measure with a fixed declared fixture/hardware/browser profile. Initial target budgets: <=350 KiB gzip initial application JavaScript, lazy-load Markdown/large detail tools, first usable Library <=2 seconds on the recorded local fixture after authentication, no unbounded catalog/manifest DOM, and stable retained memory/registry bounds across 100 route/refresh cycles. These are engineering acceptance targets, not performance claims about the user's NAS. Record baselines, p95 results and any justified amendment; do not inflate the fixture speed by bypassing real Caddy/API. Large manifests must virtualize and remain keyboard accessible. Polling should pause/back off appropriately when hidden/disconnected and must never become a mutation retry loop.

New frontend code target: >=90% line and >=85% branch coverage, enforced for the new source subtree. Critical auth/permission/operation/config/card paths require all named decision outcomes in the scenario matrix regardless of aggregate percentages. New backend security/administration/card modules have branch-targeted coverage with an initial >=90% target where measurable, plus explicit adversarial outcomes. Add coverage tooling only to locked development dependencies with rationale. Existing global coverage is not silently redefined. Independent fixtures and wire expectations must test generated schemas rather than regenerating the expectations from the same output under test.

## 6. Evidence and release rule

Each task records actual test commands, exits, relevant test node IDs, artifact hashes, fixture scope, invariant/ADR review, documentation changes and unresolved limitations in its existing completion evidence. Map case clauses to those records without introducing another evidence schema. Earlier passing evidence may be reused only with its original result and a stated unchanged-subsystem justification; a failed aggregate remains failed even when a separate continuation establishes a narrower outcome. Keep raw traces/screenshots/results in ignored or release-evidence artifacts and put safe summaries/locators in task records. Traces must never contain production credentials; even test Authorization headers are scrubbed before publishing. Do not commit giant test-output directories or passwords disguised as fixtures.

The [acceptance matrix](acceptance-matrix.md) is a minimum, not a ceiling. WEB-001 assigns exact executable tests; each implementing task updates coverage and evidence. WEB-026 checks every row has an actual covering passing test, or an explicitly blocked status that prevents completion. Platform availability is not grounds to mark rows not applicable. Human-doc tasks require proof that examples/links pass checks and representative workflows were exercised. Source completeness, disposable installed acceptance and actual production rollout are three separate statuses.
