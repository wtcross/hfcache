# Testing strategy and required gates

Testing is part of every work package, not an end-of-project phase. A screen backed only by mocked HTTP responses is not functional acceptance. A green test count does not prove host/NAS safety or deployment. All tests and evidence are **planned, not executed**, at bundle creation.

## 1. Layers and ownership

| Layer | What runs | What it proves and does not prove |
| --- | --- | --- |
| Python unit | Existing pytest fixtures plus new auth, schema, config, card and helper protocol tests | Deterministic validation, invariants, refusal and crash-state classification; no live installation proof. |
| TypeScript unit/component | Vitest or an explicitly justified equivalent, React Testing Library, user-event; exact runtime decoders and state machines | Real React interactions, strict types, URLs, scope, errors, keyboard/focus and mutation intent. MSW/fixtures may isolate components but are labelled mocked. |
| Backend integration | Real ASGI application/operation runner, real HTTP/Unix sockets, actual persistence; injectable fake Hub and owned storage fixtures | Service interaction, receipts, metadata and config boundaries, no replay; never replaces authorization/business services with fake JSON responses. |
| Application functional | Production-built SPA in real browsers -> real Caddy TLS -> installed hfcache app -> existing service layer/private worker and narrow helper fixtures | Actual routing/auth/header/asset/browser/API interaction. Only external Hub/storage boundaries may be deterministic test doubles. This is not proof of live NFS or production SELinux. |
| Platform functional | Disposable, isolated CentOS-compatible guests with actual systemd/rootless runtime/helper/Caddy, private test PKI and owned local fixture state | Effective manager/peer/mount-policy/cgroup/permission behavior, supported native positive paths and guarded rootless denials. Never uses the production writer's managers or archive. |
| Human workflow acceptance | The same built test deployment, following published operator/user guides | Discoverability, explanations, safe task completion and screenshot accuracy; manual records supplement, not replace, automated tests. |

Preserve existing backend/CLI/MCP/worker regressions and real-browser Cockpit tests until the retirement task explicitly ports or retires each test with rationale. Do not delete difficult tests to obtain a green gate. New host/config/card behavior must have unit **and** integration **and** functional coverage where observable. Pure utility cases may use unit coverage, while their callers still need functional proof.

## 2. Provider-neutral execution interface

The existing contract intentionally avoids CI-provider-specific configuration. Extend `scripts/check.sh`; do not introduce GitHub Actions or another CI platform merely for this feature.

Baseline commands already exist:

```bash
scripts/check.sh --require-cockpit
scripts/check.sh --with-build --require-cockpit
```

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

These are **target commands to implement**, not commands present in the reviewed baseline. `--require-web` refuses missing toolchain, generated schemas, browser prerequisites for selected component tests, failed tests, and skipped checks. It runs the existing backend gate too. Continue requiring Cockpit while its code/integration is affected.

WEB-005 introduces a provider-neutral functional runner, for example `scripts/check-web-functional.py`, with explicit `application`, `platform`, and `all` profiles and a validated owned workspace. Its safe help command does not inspect runtimes/credentials. The strict release gate becomes:

```bash
scripts/check.sh --require-web --with-build --with-web-functional
```

`--with-web-functional` requires **both** completed application and platform profiles at final acceptance. Missing Caddy, browsers, immutable images, certificate tooling, guest support, private-worker support or offline dependency closure exits nonzero with an unblock instruction. It never marks 'SKIP' as successful functional acceptance. Early tasks run the real subset their functionality introduces; WEB-026 requires every applicable matrix case and all supported release profiles. The runner must report source/artifact/fixture identities, command arguments excluding secrets, return codes, test node IDs, browser versions and pending/blocked cases.

Where the execution host cannot provision isolated guests safely, retain the task as blocked and run independent source work that is genuinely ready. Do not weaken acceptance, run production host operations, or retire Cockpit based on component fixtures alone.

## 3. Hermetic fixtures and safe environment

Use deterministic synthetic repository fixtures (fictional model and dataset identities), tiny complete manifests/ordinary files, bounded card examples, retained/current publications and known verification reports. Include enabled, disabled, unpublished, unmanaged, empty tags, last-observed tags, unknown metadata, multiple quantizations, incomplete shards, adapters/projectors, dataset declarations, changed current pointers, repaired publication IDs and malformed supplemental records. No large model download or real account is needed.

Inject the fake Hub at the supported adapter boundary. Unit/integration and application functional tests may inject a clearly labelled storage/mount-table fixture at the existing test seam; **do not** add a production environment flag that disables archive preflight, authentication, symlink checks, or locking. Test HTTP still reaches the actual production routes/services, not a fake `/api/v1` fixture server. Verify installed module bytes against the selected wheel for artifact functional tests. Mark storage-simulation evidence as such; it cannot close an NFS acceptance hold.

Platform tests use actual isolated managers and rootless identities. Positive native schedule/config paths must run against real guest systemd; rootless tests prove fixed denied schedule/observer behavior unless a supported binding already exists. Root-capable test code runs only inside an owned isolated guest with explicit fixture identity. No host rootful container, privileged fallback on the writer, broad bus/socket bind, container security disablement or global policy edits. All scratch paths must be local, outside `/srv/hfcache`, release selection, production config and control stores. Do not run `hfcache archive init`, including 'just for testing' on the host; construct synthetic archives through owned test fixture builders. Any genuinely real NFS fixture requires a separately authorized disposable export; lack of it never justifies touching the live archive.

Generate test-only credentials and TLS certificates in mode-restricted workspaces. Trust the test CA in browser contexts/OS trust inside the guest. `ignoreHTTPSErrors`, curl `-k`, wildcard host allowances or permissive CORS do not count as a positive TLS/auth test. Negative untrusted-certificate tests explicitly prove refusal. No external requests are allowed during test execution except isolated fixture services. Build dependency provisioning occurs separately, from pinned/hashed inputs, and never pulls images automatically during runtime/gates.

Isolation tests inspect actual processes/peer credentials and bind visibility, not only rendered command strings. Worker cannot read Basic/bearer/Hub credentials or contact IP networks; Caddy cannot read archive/policy/host-helper state; UI assets contain no secret values; API remains non-root. Do not erase failed containers/workspaces/uncertain operation evidence automatically. Cleanup owns only positively identified fixture resources and runs only after observed process termination; failed drain is a retained blocker.

## 4. Core regression families

**Authentication/routing:** native Basic browser challenge; valid and invalid credentials; missing/unusable hash; rate/concurrency bounds; wrong credential class; TLS/Origin/CSRF; repeated/malformed auth headers; direct Unix auth; spoofed proxy/user headers; unsupported methods; SPA versus API/MCP route precedence; deep links/assets/base prefixes; missing asset 404; no secret leakage; no HTML rewrite of API failures. Use the same Caddy endpoint for authenticated REST bearer and MCP tool calls while the browser is active.

**Configuration:** hidden/protected field preservation; exact-byte CAS including tags; deterministic managed-edit reconstruction; validation/preview/apply correspondence; blocked authority changes; filesystem ownership/modes; persistent original lock inode; stale base/queued policy; service identity; two browser tabs; existing candidate and backup preservation; incomplete helper/API response; every backup/install/fsync/result boundary; exact read-only reconciliation; no new key after uncertainty; unchanged old literal-candidate CLI behavior.

**Cards:** exact publication provenance; successful/absent/not-captured/oversize/invalid UTF-8/redacted cases; hostile paths/symlinks/special files/replaced inode; nested and expensive Markdown; JSON encoding expansion; capture failure warning without corrupting publication outcome; unsupported records preserved; no GET payload access, Hub calls, lock acquisition or write; pruned/current-race behavior; source digest mismatch; no raw secret exposure; no scripts/iframes/SVG/forms/external assets/unsafe protocols/DOM clobbering. Test the actual browser's request log and DOM, not only sanitizer output strings.

**Catalog/presentation:** identity-safe join of paged catalog and status, known totals and coverage; zero known matches with partial coverage; same-variant filter semantics; datasets rejecting model-only filters; unmanaged provenance; literal ID/tag search; safe-range/lossless integers; stale cursors/limits; exact detail switching; manifest budgets and virtualization; metadata coverage separate from integrity; query races and auth/archive changes.

**Operations:** original-key persistence before POST; response lost before/after acceptance; route unmount/reload/tab/storage corruption; quota before and after transmission; event gap/overflow; expired/missing receipts; no replay/cancel; restored terminal metadata revalidation; 202 versus completed results; failed HTTP-200 Envelopes; busy/partial/integrity outcomes; observer stop versus actual executor; no payload or credential persistence in browser storage.

**Maintenance/host:** fresh preview/apply scope, exact-SHA repair, protected current and unmanaged-only purge, quarantine IDs, lock conflict, recovery unknown preservation, supported schedule calendar/reset/timer operation, verification timer read-only, no target stop, release-policy drift/unknown host helper, service manager mismatch, bounded logs and evidence separation.

**Packaging/documentation:** asset/wheel/index matching, enabled UI missing assets refusal, base reader without Node, same app lifespan, immutable rootless assets, production prefix, real installed old CLI/MCP compatibility, durable-format downgrade refusal and preservation, no default production effects, protected deployment/rollback examples, operator procedures matching current labels and behavior.

## 5. Browser, accessibility and performance gates

Application functional tests run in Chromium, Firefox and WebKit, pinned with the test tool version. Full critical workflows run in all three; use a documented representative deeper matrix only for expensive fault combinations, never to omit browser authentication/prefix/read/write paths. Use auto-waiting assertions, semantic role/name locators and explicit bounded timeouts; no arbitrary sleeps as correctness conditions. Record retry counts: a test that passes only on retry is flaky evidence to resolve, not a silently clean run.

Exercise keyboard-only navigation, visible focus, dialog focus trap/restoration, form labels and validation announcements, accessible status/error regions, table headings, reduced motion, contrast, and responsive layout at representative 1440px and 390px widths plus 200% zoom. Use automated axe checks with zero serious/critical violations in covered screens and manual keyboard/screen-reader smoke records; automation alone is not a claim of full accessibility conformance. Keep external fonts and network assets disabled.

Measure with a fixed declared fixture/hardware/browser profile. Initial target budgets: <=350 KiB gzip initial application JavaScript, lazy-load Markdown/large detail tools, first usable Library <=2 seconds on the recorded local fixture after authentication, no unbounded catalog/manifest DOM, and stable retained memory/registry bounds across 100 route/refresh cycles. These are engineering acceptance targets, not performance claims about the user's NAS. Record baselines, p95 results and any justified amendment; do not inflate the fixture speed by bypassing real Caddy/API. Large manifests must virtualize and remain keyboard accessible. Polling should pause/back off appropriately when hidden/disconnected and must never become a mutation retry loop.

New frontend code target: >=90% line and >=85% branch coverage, enforced for the new source subtree. Critical auth/permission/operation/config/card paths require all named decision outcomes in the scenario matrix regardless of aggregate percentages. New backend security/administration/card modules have branch-targeted coverage with an initial >=90% target where measurable, plus explicit adversarial outcomes. Add coverage tooling only to locked development dependencies with rationale. Existing global coverage is not silently redefined. Independent fixtures and wire expectations must test generated schemas rather than regenerating the expectations from the same output under test.

## 6. Evidence and release rule

Each task records actual test commands, exits, relevant test node IDs, artifact hashes, fixture scope, invariant/ADR review, documentation changes and unresolved limitations in its completion evidence. Keep raw traces/screenshots/results in ignored or release-evidence artifacts and put safe summaries/locators in task records. Traces must never contain production credentials; even test Authorization headers are scrubbed before publishing. Do not commit giant test-output directories or passwords disguised as fixtures.

The [acceptance matrix](acceptance-matrix.md) is a minimum, not a ceiling. WEB-001 assigns exact executable tests; each implementing task updates coverage and evidence. WEB-026 checks every row has an actual covering passing test, or an explicitly blocked status that prevents completion. Platform availability is not grounds to mark rows not applicable. Human-doc tasks require proof that examples/links pass checks and representative workflows were exercised. Source completeness, disposable installed acceptance and actual production rollout are three separate statuses.
