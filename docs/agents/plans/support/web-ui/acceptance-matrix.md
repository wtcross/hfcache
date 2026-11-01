# Acceptance scenario matrix

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `bf8ee2ef3ea9658dedebafa423f294f25a2d8b4299de997fd7474636b3775a95`,
original content SHA-256 `4c2669fccb8c12ac7fec25757ea684af6ae7f0d447e2bef515ed7d48aeaea7d4`.
Historical proof hashes identify the original artifacts, not this edited record.

This matrix contains **95 required scenarios**: 85 are owned through WEB-022 and
all 95 remain required at final acceptance. These are assertions, not passing test
claims. Every scenario and its clauses retain the existing `minimum_layers` in
`acceptance-cases.json`; use appropriate unit/component, integration and direct
installed workflow evidence. There is no requirement to execute every case in
every application/native/rootless × prefix × browser cell.

Record case/clause coverage in the existing acceptance records with real test
node IDs, commands/exits, source/artifact identities, fixture/browser/profile
scope, evidence locators and observed outcomes. Reuse passing unchanged-subsystem
evidence only with an explicit justification. Preserve original failures and
accepted effects; never replay an operation to obtain a clean aggregate. Missing
required assertions block completion, and a test name or source review alone is
not a pass. No new framework, schema, proof model or binder is required.

The existing instrumented runner and its `acceptance-evidence.json`, run IDs,
fresh-fixture joins and exact private proofs remain optional diagnostics. Their
validators and `--require-through`/`--final` requirements stay strict if invoked;
direct installed evidence does not claim those commands passed. See the
[testing strategy](testing-strategy.md) for the required acceptance path, unchanged
scenario clauses and optional-runner contract.

For WEB-023–026 apply the [bounded-testing policy](testing-strategy.md#web-023026-bounded-product-testing-and-effort).
Reuse matching executed evidence with explicit scope; no case/clause is omitted,
no failed aggregate becomes passed and no mandatory runner cross-product returns.

## AUTH

| ID / owner | Scenario | Required observable assertions |
| --- | --- | --- |
| `AUTH-01` / [WEB-004](../../tasks/web-004-basic-auth-and-permissions.md) | Native Basic browser authentication | Real browser receives the challenge, authenticates the configured user and makes same-origin reads/writes without JavaScript receiving a password or a per-request test Authorization override. |
| `AUTH-02` / [WEB-004](../../tasks/web-004-basic-auth-and-permissions.md) | Wrong or malformed credentials | Wrong user/password, duplicate schemes/headers, invalid encodings, over-limit values and missing credentials produce uniform bounded refusal before effects; secrets are absent from responses/logs. |
| `AUTH-03` / [WEB-004](../../tasks/web-004-basic-auth-and-permissions.md) | Protected hash provisioning and rotation | Unsafe or changed inode, wrong ownership/mode, symlink and invalid hash refuse startup; protected rotation preserves stable subject and does not change legacy bearer sources. |
| `AUTH-04` / [WEB-004](../../tasks/web-004-basic-auth-and-permissions.md) | Credential-class isolation | REST writer/reader capabilities remain distinct; MCP bearer is not REST/UI authority; Basic and REST bearer never become MCP authority; no anonymous fallback. |
| `AUTH-05` / [WEB-004](../../tasks/web-004-basic-auth-and-permissions.md) | CSRF on ambient Basic writes | Cross-origin/simple form/text/multipart, absent/null/duplicate Origin and missing non-simple header refuse all unsafe Basic routes, including new host/config routes. |
| `AUTH-06` / [WEB-004](../../tasks/web-004-basic-auth-and-permissions.md) | Nonbrowser bearer compatibility | Existing no-Origin CLI/REST bearer requests still succeed where authorized and never redirect to a UI or Basic-only login layer. |
| `AUTH-07` / [WEB-004](../../tasks/web-004-basic-auth-and-permissions.md) | Authentication work budgets | Bad-password flood and oversized headers cannot create unbounded work/storage; bounded concurrency/refusal leaves operation observation correctly classified. |
| `AUTH-08` / [WEB-006](../../tasks/web-006-guarded-host-adapter.md) | Backend administrative enforcement | Forged UI capability/user headers and direct POST cannot bypass protected host policy; old writer token does not implicitly gain config/host admin authority. |
| `AUTH-09` / [WEB-005](../../tasks/web-005-shared-caddy-spa-serving.md) | Basic credentials over TLS only off-host | Trusted test CA positive path succeeds; plaintext and untrusted certificate paths refuse; no ignoreHTTPSErrors/-k/wildcard TLS workaround counts. |
| `AUTH-10` / [WEB-020](../../tasks/web-020-cross-browser-accessibility-and-load.md) | Authentication lifecycle and privacy | Auth/authority change clears private query data, never silently rebinds unresolved handles; no fake logout or passwords/tokens in storage, bundles or URLs. |

## ROUTE

| ID / owner | Scenario | Required observable assertions |
| --- | --- | --- |
| `ROUTE-01` / [WEB-005](../../tasks/web-005-shared-caddy-spa-serving.md) | One Caddy endpoint for three interfaces | Browser SPA, REST bearer and all allowed MCP tools traverse the same existing Caddy configuration/port/upstream; no second frontend server or global Basic gate. |
| `ROUTE-02` / [WEB-005](../../tasks/web-005-shared-caddy-spa-serving.md) | Empty and nonempty public prefix | P/ui, P/api/v1 and P/mcp links, redirects, assets and pagination work for empty prefix and /management; request headers cannot choose P. |
| `ROUTE-03` / [WEB-005](../../tasks/web-005-shared-caddy-spa-serving.md) | Deep-link navigation and refresh | Direct entry/refresh/back-forward on Library and exact detail routes loads authenticated assets and correct client state in all three browser engines. |
| `ROUTE-04` / [WEB-005](../../tasks/web-005-shared-caddy-spa-serving.md) | Fallback isolation | API/MCP unknown routes/errors, non-GET methods and missing JS/CSS assets retain classified HTTP errors and never return SPA index HTML. |
| `ROUTE-05` / [WEB-005](../../tasks/web-005-shared-caddy-spa-serving.md) | Asset safety and startup identity | Enabled UI missing/wrong manifest refuses; symlink/traversal/encoded escape/directory/special-file requests never serve unindexed filesystem content. |
| `ROUTE-06` / [WEB-005](../../tasks/web-005-shared-caddy-spa-serving.md) | Static/UI data security headers | HTML/bootstrap/API/cards are no-store, assets use private policy; CSP/nosniff/referrer/frame rules apply on success/error without breaking app operation. |
| `ROUTE-07` / [WEB-005](../../tasks/web-005-shared-caddy-spa-serving.md) | Existing Caddy and worker boundaries | Caddy retains no archive/helper/Hub/password access and existing TLS/admin/ACME/log/stream settings; one application lifespan/pool/worker is retained. |
| `ROUTE-08` / [WEB-021](../../tasks/web-021-immutable-ui-release-packaging.md) | Old open page after release selection | Stale asset/UI schema mismatch is explicit; reload invitation preserves unsaved drafts/original handles instead of auto-reload/replay. |

## CONFIG

| ID / owner | Scenario | Required observable assertions |
| --- | --- | --- |
| `CONFIG-01` / [WEB-007](../../tasks/web-007-configuration-read-and-preview.md) | Safe installed editable projection | GET config is permission-gated, nonsecret, full-byte-revision-bound and read-only; protected/hidden fields cannot be overwritten by redaction placeholders. |
| `CONFIG-02` / [WEB-007](../../tasks/web-007-configuration-read-and-preview.md) | Typed candidate reconstruction | Managed edits reconstruct deterministic exact candidate bytes server-side; mixed/unknown/coercive fields and arbitrary pointers/paths are rejected. |
| `CONFIG-03` / [WEB-007](../../tasks/web-007-configuration-read-and-preview.md) | Tag-only concurrency | Two tag edits with unchanged operational fingerprint still conflict using full-byte base identity; no silent lost update or fake policy change. |
| `CONFIG-04` / [WEB-007](../../tasks/web-007-configuration-read-and-preview.md) | Validation versus authority compatibility | Valid incompatible candidate remains distinguishable from invalid syntax; root/UUID/Hub/credential source changes cannot redirect authority or get auto-installed. |
| `CONFIG-05` / [WEB-007](../../tasks/web-007-configuration-read-and-preview.md) | Existing candidate clients | Installed/literal TOML CLI validation and sizing keep old request/response contracts and capability requirements; no new hidden install effect. |
| `CONFIG-06` / [WEB-008](../../tasks/web-008-atomic-configuration-application.md) | Preview and Apply exact correspondence | Failed/stale/mismatched preview or modified draft cannot apply; required successful preview and same exact base/candidate are revalidated server-side. |
| `CONFIG-07` / [WEB-008](../../tasks/web-008-atomic-configuration-application.md) | Atomic replacement and permissions | Apply retains predecessor, original common lock inode, 0640 root:hfcache and exact installed bytes/fingerprint; configured-only removal does not delete archive content. |
| `CONFIG-08` / [WEB-008](../../tasks/web-008-atomic-configuration-application.md) | Crash at each configuration boundary | Faults before/after staging/backup/fsync/rename/confirmation/result yield correct unchanged/installed-unconfirmed/unknown evidence and never erase candidate/backups. |
| `CONFIG-09` / [WEB-008](../../tasks/web-008-atomic-configuration-application.md) | Lost helper/API response after effect | Original key/ID reconciles by safe exact reads; no automatic helper replay/new key/rollback or a false not-applied inference after disconnect/restart. |
| `CONFIG-10` / [WEB-008](../../tasks/web-008-atomic-configuration-application.md) | Legacy and new writer concurrency | Actual legacy/new fixed config clients use the same lock/target and cannot race into inconsistent installed content or overwrite unknown candidates. |
| `CONFIG-11` / [WEB-008](../../tasks/web-008-atomic-configuration-application.md) | Fresh policy and queue semantics | Permission/base/authority drift during queue wait refuses; old admitted domain policy remains immutable; stale queued archive mutations retain existing refusal. |
| `CONFIG-12` / [WEB-015](../../tasks/web-015-configuration-and-tag-ui.md) | Human configuration workflow | Browser add model/dataset/tags, validation, preview, reviewed apply and confirmation matches guide; dirty navigation, historical labels, protected fields and concurrent conflicts are clear. |

## CARD

| ID / owner | Scenario | Required observable assertions |
| --- | --- | --- |
| `CARD-01` / [WEB-009](../../tasks/web-009-repository-card-capture.md) | Exact writer-owned capture | Sync/repair/technical refresh captures only root manifest-listed README with exact archive/repository/SHA/publication provenance; GET never triggers capture. |
| `CARD-02` / [WEB-009](../../tasks/web-009-repository-card-capture.md) | No payload execution or remote work | Hostile card names/content cannot invoke loaders, code, unpickle, URL fetch or tensor inspection; missing README does not cause implicit download. |
| `CARD-03` / [WEB-009](../../tasks/web-009-repository-card-capture.md) | Source and encoded size/work bounds | Oversize raw/Unicode-expanded/JSON output, deep parsing and aggregate capture work stop before exceeding finite budgets or partial-record success. |
| `CARD-04` / [WEB-009](../../tasks/web-009-repository-card-capture.md) | Unsafe filesystem and content identity | Symlink/special/replaced inode and source digest mismatch refuse safe presentation; immutable manifest/ref/observation bytes are unchanged. |
| `CARD-05` / [WEB-009](../../tasks/web-009-repository-card-capture.md) | Failure classification without integrity inflation | Absent/not-captured/unsupported/failed/redacted card states remain explicit; failed optional capture warns without undoing successful publication or increasing verification confidence. |
| `CARD-06` / [WEB-009](../../tasks/web-009-repository-card-capture.md) | Adjunct atomicity and unknown preservation | Faults around temporary file/fsync/replace leave whole records; unsupported existing records and unknown siblings are preserved, not deleted or overwritten blindly. |
| `CARD-07` / [WEB-010](../../tasks/web-010-repository-card-read-api.md) | Exact retained card read | Requested publication pair is validated against authoritative retained identity; stale card cannot resurrect purged entry; vanished pair never falls forward to current. |
| `CARD-08` / [WEB-010](../../tasks/web-010-repository-card-read-api.md) | Read has no payload/Hub/lock/write effects | Instrumented real GET reads adjunct/allowed metadata only, uses bounded lease/pool through disconnect and never resolves credentials or acquires archive lock. |
| `CARD-09` / [WEB-010](../../tasks/web-010-repository-card-read-api.md) | Wire state and body limits | Valid/invalid schema states, UTF-8/JSON expansion, slow clients and missing/corrupt adjuncts produce precise bounded authenticated JSON/no-store responses. |
| `CARD-10` / [WEB-014](../../tasks/web-014-safe-markdown-rendering.md) | Executable markup and unsafe URLs blocked | Actual browser DOM/network proves no script/MDX/raw HTML/iframe/form/SVG/event/style/unsafe-protocol execution, including encoded/control-character variants. |
| `CARD-11` / [WEB-014](../../tasks/web-014-safe-markdown-rendering.md) | No external assets or URL proxy | Image/font/script references cause no external requests; placeholders are clear; safe relative links resolve against pinned upstream identity with no opener/referrer. |
| `CARD-12` / [WEB-014](../../tasks/web-014-safe-markdown-rendering.md) | Safe source and pathological Markdown | Source toggle is sanitized derivative; secrets never appear; hostile headings cannot clobber app IDs; nested/table/code cases remain bounded and accessible. |

## CATALOG

| ID / owner | Scenario | Required observable assertions |
| --- | --- | --- |
| `CATALOG-01` / [WEB-012](../../tasks/web-012-library-and-discovery.md) | Type/scope and ID/tag search | All/models/datasets, configured/archived/all and current/retained scopes work with literal ID/tag text, not README full-text or live Hub search. |
| `CATALOG-02` / [WEB-012](../../tasks/web-012-library-and-discovery.md) | Tag normalization and provenance | All/any filters and current-only/last-observed semantics match server; canonical limits and disabled/unpublished/unmanaged distinctions stay visible. |
| `CATALOG-03` / [WEB-012](../../tasks/web-012-library-and-discovery.md) | Technical predicates match one eligible variant | Format/method/scheme/bits/max bytes all match the same supported primary complete variant; unknown/adapters/projectors cannot become false positives. |
| `CATALOG-04` / [WEB-012](../../tasks/web-012-library-and-discovery.md) | Coverage and zero-known-match state | Partial/missing/unsupported metadata qualifies counts and zero matches; one page never becomes an archive-wide total or proof of absence. |
| `CATALOG-05` / [WEB-012](../../tasks/web-012-library-and-discovery.md) | Pagination and identity-safe joins | Cursors/limits/curation-only invalidation and malformed pages refuse/restart finitely; status/catalog rows join by type/ID/authority, not list position. |
| `CATALOG-06` / [WEB-013](../../tasks/web-013-publication-detail-pages.md) | Publication-pinned detail switching | Current moves/repair same SHA/new publication/racing responses do not mix README/variants/integrity; exact vanished publication is unavailable. |
| `CATALOG-07` / [WEB-013](../../tasks/web-013-publication-detail-pages.md) | Model and dataset evidence semantics | Models expose supported variant sources/completeness; datasets expose static declarations only, no inferred row counts, GPU fit or model fields. |
| `CATALOG-08` / [WEB-013](../../tasks/web-013-publication-detail-pages.md) | Manifest and consumer locators | Files/bytes/digests/paths are bounded metadata with correct locator bases and no raw weight-file serving; missing catalog does not erase authoritative inventory. |
| `CATALOG-09` / [WEB-020](../../tasks/web-020-cross-browser-accessibility-and-load.md) | Large integer and read-race safety | Unsafe JS integers do not silently round; route/auth/archive changes cancel stale reads; large tables and errors remain usable without unbounded fetch/DOM. |

## OPS

| ID / owner | Scenario | Required observable assertions |
| --- | --- | --- |
| `OPS-01` / [WEB-011](../../tasks/web-011-query-and-operation-state.md) | Original handle before submission | Registry stores a validated original key before any POST; storage failure before transmission prevents the effect. |
| `OPS-02` / [WEB-011](../../tasks/web-011-query-and-operation-state.md) | No retry after uncertain admission | Drop connection before/after backend admission; exactly one original operation/effect exists; original lookup is used and no new-key replay occurs. |
| `OPS-03` / [WEB-011](../../tasks/web-011-query-and-operation-state.md) | Navigation/reload and restored state | Tabs/unmount/reload preserve bounded handles; restored terminal summary does not unblock until authenticated original observation verifies it. |
| `OPS-04` / [WEB-011](../../tasks/web-011-query-and-operation-state.md) | Storage corruption/quota and scope drift | Malformed/out-of-scope restored entries refuse; unresolved records are never evicted; post-transmit storage loss retains handle in memory and blocks submissions. |
| `OPS-05` / [WEB-011](../../tasks/web-011-query-and-operation-state.md) | Missing/expired history remains unknown | 404/expired/interrupted/ambiguous result never proves nonexecution or enables automatic cleanup/recovery/replay. |
| `OPS-06` / [WEB-016](../../tasks/web-016-operations-and-reports-ui.md) | Admission versus domain outcome | 202, queued/waiting/running and HTTP-200 failed Envelopes preserve exact classification; no fake terminal success/byte percentage from observer state. |
| `OPS-07` / [WEB-016](../../tasks/web-016-operations-and-reports-ui.md) | Busy, partial and integrity outcomes | HFMNT010 is busy; warning/per-repo partial/10/20/30/40/50 classes retain useful data and safe human guidance; no blind repair/sync/prune suggestion. |
| `OPS-08` / [WEB-016](../../tasks/web-016-operations-and-reports-ui.md) | Events and reports are bounded | Gap/overflow/large result/slow observer/history pagination retain explicit limits; request/operation/run IDs and loaded history extent are not conflated. |
| `OPS-09` / [WEB-016](../../tasks/web-016-operations-and-reports-ui.md) | All existing manual job types | Full/selected sync, sizing, new/full/revision verify/estimate, diagnostics and refresh run through existing real services/worker and yield exact reports. |
| `OPS-10` / [WEB-019](../../tasks/web-019-administration-and-diagnostics-ui.md) | Observer and journal semantics | Stop observing/journal activity never claims executor cancellation or domain completion; original recovery panel remains available in Administration. |

## HOST

| ID / owner | Scenario | Required observable assertions |
| --- | --- | --- |
| `HOST-01` / [WEB-006](../../tasks/web-006-guarded-host-adapter.md) | Actual helper peer and isolation | Real unprivileged native/rootless peer mapping succeeds only for intended API caller; Caddy/worker/forged user header cannot gain helper rights. |
| `HOST-02` / [WEB-006](../../tasks/web-006-guarded-host-adapter.md) | Fixed protocol and protected policy | Unknown command/version/unit/manager/path/schema, unsafe policy or release index drift refuses before host effects; no generic shell/DBus/engine access. |
| `HOST-03` / [WEB-006](../../tasks/web-006-guarded-host-adapter.md) | Status unknown versus allowed | Missing/helper timeout/unproved guard or binding is visibly unknown/denied, not inactive/healthy/authorized; absence of a guard is not permission. |
| `HOST-04` / [WEB-018](../../tasks/web-018-schedule-observer-and-journal.md) | Calendar/timespan validation | Real systemd-analyze validates fixed strict argv; injection/control/oversize/timeout cases refuse without creating/modifying drop-ins. |
| `HOST-05` / [WEB-018](../../tasks/web-018-schedule-observer-and-journal.md) | Schedule apply/reset with concurrency | Expected revision, managed drop-in ownership, backup/outcome and explicit manager reload rules hold; stale/concurrent edits do not silently overwrite. |
| `HOST-06` / [WEB-018](../../tasks/web-018-schedule-observer-and-journal.md) | Pause/resume and forbidden units | Only fixed supported sync timer is controlled; verification timer remains disabled/read-only and hfcache.target/API/worker never stop or change. |
| `HOST-07` / [WEB-018](../../tasks/web-018-schedule-observer-and-journal.md) | Exact observer stop is not cancellation | Actual matching observer invocation may stop under explicit policy while accepted backend work continues; wrong invocation/unproven binding refuses. |
| `HOST-08` / [WEB-018](../../tasks/web-018-schedule-observer-and-journal.md) | Guarded rootless and permitted native | Positive supported native behavior is proven; selected rootless profile denies unproved system schedule/observer controls without user-manager substitution. |
| `HOST-09` / [WEB-018](../../tasks/web-018-schedule-observer-and-journal.md) | Bounded journal evidence | Only enumerated sources/cursors/limits, bounded time/bytes/redaction; logs cannot trigger commands or establish an operation result. |
| `HOST-10` / [WEB-022](../../tasks/web-022-installed-functional-acceptance.md) | Installed role hardening | Actual installed process/cgroup/socket/secret/mount observations match protected roles; no root API, worker IP/credential access, Caddy archive/helper mount or security weakening. |

## MAINT

| ID / owner | Scenario | Required observable assertions |
| --- | --- | --- |
| `MAINT-01` / [WEB-017](../../tasks/web-017-maintenance-ui.md) | Fresh preview/apply authority | All maintenance applies recheck exact current scope/policy/locks rather than trusting browser preview or posted plan bodies. |
| `MAINT-02` / [WEB-017](../../tasks/web-017-maintenance-ui.md) | Prune current protection and one-round policy | Protected current survives and lower retention obeys existing single-round/over-retention semantics; no silent delete on config edit. |
| `MAINT-03` / [WEB-017](../../tasks/web-017-maintenance-ui.md) | Unmanaged-only explicit purge | Configured repositories and empty/invalid scopes refuse; whole unmanaged fixture purge retains required audits/evidence. |
| `MAINT-04` / [WEB-017](../../tasks/web-017-maintenance-ui.md) | Ambiguous recovery and quarantine | Unknown journals/files are preserved; quarantine uses explicit bounded valid IDs and full batch proof, never filesystem paths. |
| `MAINT-05` / [WEB-017](../../tasks/web-017-maintenance-ui.md) | Same-SHA exact repair | Repair preserves original manifest/generation and expected bytes, uses new publication ID/grace behavior and presents findings without self-authorized mutation. |
| `MAINT-06` / [WEB-017](../../tasks/web-017-maintenance-ui.md) | Interrupted destructive apply | Lost response/restart retains original operation evidence and no replay/automatic cleanup; real fixture outcomes/audits are checked. |

## RELEASE

| ID / owner | Scenario | Required observable assertions |
| --- | --- | --- |
| `RELEASE-01` / [WEB-021](../../tasks/web-021-immutable-ui-release-packaging.md) | Separate reproducible asset artifact | Source/lock/toolchain/UI contract and per-file hashes identify native/rootless assets; mismatched/missing artifact fails without untracked dist fallback. |
| `RELEASE-02` / [WEB-021](../../tasks/web-021-immutable-ui-release-packaging.md) | Base Python installs remain independent | Base/server/server+MCP wheel profiles remain valid without runtime Node or forced frontend source build; optional UI enablement is explicit. |
| `RELEASE-03` / [WEB-021](../../tasks/web-021-immutable-ui-release-packaging.md) | No new edge deployment surface | One existing Caddy instance/port/TLS/upstream serves all; no extra proxy/frontend service/CDN/runtime dependency or secret exposure. |
| `RELEASE-04` / [WEB-022](../../tasks/web-022-installed-functional-acceptance.md) | Installed artifacts not only source fixtures | Browser/Caddy/API/worker/helper execute selected installed bytes on native/rootless guests; identities, actual permissions and isolation are recorded. |
| `RELEASE-05` / [WEB-023](../../tasks/web-023-compatibility-and-rollback-drill.md) | Actual legacy client compatibility | Pinned installed old CLI reader/writer and MCP clients validate actual new server envelopes/capabilities/receipts and literal candidate behavior. |
| `RELEASE-06` / [WEB-023](../../tasks/web-023-compatibility-and-rollback-drill.md) | Durable format downgrade drill | Old binaries inspect copied new cards/helper/config operation state and either work or refuse as documented, preserving all unknown/new evidence. |
| `RELEASE-07` / [WEB-023](../../tasks/web-023-compatibility-and-rollback-drill.md) | Evidence-preserving rollback | Actual isolated upgrade/rollback drains executors, retains original locks/stores/handles/candidates and refuses unsafe target observation; no forced kill/delete/replay. |
| `RELEASE-08` / [WEB-025](../../tasks/web-025-independent-web-handoff.md) | Independent indexed web interface | Built/staged release and browser workflows use indexed application assets independently; current web safety coverage, generic host/client helpers and required attribution remain. |
| `RELEASE-09` / [WEB-026](../../tasks/web-026-final-gate-and-handoff.md) | No production or remote publication claims | Final evidence separates source/fixture acceptance from unperformed live deployment, Caddy reload, NAS, push, tag and production historical frontend removal. |

## DOC

| ID / owner | Scenario | Required observable assertions |
| --- | --- | --- |
| `DOC-01` / [WEB-024](../../tasks/web-024-human-documentation-acceptance.md) | Human navigation and complete guides | Root README/docs index lead to usable user/operator guides for all workflows without requiring agent plan knowledge or placeholder pages. |
| `DOC-02` / [WEB-024](../../tasks/web-024-human-documentation-acceptance.md) | Docs match actual contracts | Links/anchors/images/examples, route permissions/effects, strict config/defaults/bounds and helper inventory are independently validated against code. |
| `DOC-03` / [WEB-024](../../tasks/web-024-human-documentation-acceptance.md) | Safe actionable troubleshooting | Guides explain Basic lifetime, unknown execution, exact config conflicts, missing cards and denied host actions without secret literals/security bypass/replay. |
| `DOC-04` / [WEB-024](../../tasks/web-024-human-documentation-acceptance.md) | Real guide walkthrough and screenshots | Login/filter/detail/card/tags/apply/reconnect/maintenance/admin guides run on actual synthetic installed fixture; screenshot alt text/version/fake-data labels are correct. |
| `DOC-05` / [WEB-026](../../tasks/web-026-final-gate-and-handoff.md) | Continuous docs and evidence | Each implementation package includes its human docs and test evidence; final gate checks no deferred documentation or fabricated production status. |

## UX

| ID / owner | Scenario | Required observable assertions |
| --- | --- | --- |
| `UX-01` / [WEB-020](../../tasks/web-020-cross-browser-accessibility-and-load.md) | Three browser engines | Chromium/Firefox/WebKit prove native Basic, prefixes, reads/writes and core workflows through real Caddy/API; mocked-only or preinjected auth is not sufficient. |
| `UX-02` / [WEB-020](../../tasks/web-020-cross-browser-accessibility-and-load.md) | Keyboard and assistive interaction | Focus order/trap/restoration, field labels/errors, status announcements and tables work with keyboard and screen-reader smoke; serious/critical automated violations resolved. |
| `UX-03` / [WEB-020](../../tasks/web-020-cross-browser-accessibility-and-load.md) | Responsive and zoom behavior | 1440px/390px and 200% zoom preserve controls/readability/recovery panel, no clipped actions, with reduced-motion support and no external fonts. |
| `UX-04` / [WEB-020](../../tasks/web-020-cross-browser-accessibility-and-load.md) | Finite performance and memory | Recorded fixture meets approved initial JS/usability/memory/poll/DOM targets or explicit reviewed amendments; 100 route/refresh cycles stay bounded without mutation retries. |
