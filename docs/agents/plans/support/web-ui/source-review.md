# Pinned source review and external references

Reviewed October 20, 2026. Repository baseline: `wtcross/hfcache` **`6b8fae2e0997403ae5c716a2e92148af0a972af9`** (main when checked), titled `OPS-023: deploy and accept the guarded Cockpit repair release`. Prior UI research used application source `1c685018803a365bbb8b0c1aad4b94709f60e7d7`; the later commit records guarded 0.2.2 deployment and packaging/evidence changes. These are repository-recorded facts, not a new inspection of the live host. Reconcile HEAD before implementation; do not reset the checkout to this SHA.

## Observed repository facts

| Finding | Primary source at the review baseline |
| --- | --- |
| Current selector is inactive after guarded rollout; browser/NAS/workload holds remain separate. | [Current plan](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/docs/agents/plans/current.md) |
| Plans now live under docs/agents/plans; tasks own status; one work package per commit; drafting is not activation. | [Planning](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/docs/agents/planning.md), [workflow](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/docs/agents/workflow.md), [AGENTS](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/AGENTS.md) |
| Caddy proxies HTTPS :8443 to the API Unix socket with no file server, ACME, or admin endpoint. | [Caddyfile](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/packaging/containers/Caddyfile.in), [container contract](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/docs/containers.md) |
| Default gate is provider-neutral and includes docs plus locked base/server/MCP installation checks; frontend strict mode currently means require-cockpit. | [Gate](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/scripts/check.sh), [development](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/docs/development.md) |
| Existing REST has search/facets/details/variants, metadata refresh, inventory, references/manifests, jobs, reports and maintenance. It has no generic payload endpoint or remote configuration installer. | [REST contract](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/docs/api.md), [app](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/src/hfcache/api/app.py), [catalog routes](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/src/hfcache/api/catalog.py) |
| Tags live in config; operational fingerprint excludes them; last-observed labels are not current curation. README extraction currently retains declarations, not a renderable body. | [Discovery](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/docs/discovery.md), [records](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/src/hfcache/catalog_models.py) |
| Principal currently carries credential class; bearer-only auth and strict public schemas must be preserved. | [Auth](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/src/hfcache/api/auth.py), [wire models](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/src/hfcache/api/models.py) |
| Cockpit still performs guarded config I/O, host profile inspection, system manager and timer/drop-in operations, and optional journal diagnostics outside REST. | [Cockpit contract](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/docs/cockpit.md), [config adapter](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/cockpit/src/api/config.ts), [schedule adapter](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/cockpit/src/api/schedule.ts) |
| Rootless API policy mount is read-only and old system timer/observer permissions are effectively denied; the worker is separately confined. | [Rootless contract](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/docs/containers.md), [invariants](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/docs/invariants.md) |
| Nested Envelope data is generic in OpenAPI; catalog exposes specific x-catalog-payload schemas. | [Wire models](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/src/hfcache/api/models.py), [catalog schema hooks](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/src/hfcache/api/catalog.py) |
| Frontend uses pnpm 11.18.0, Node constraint ^24.18.1, React 18.3.1, TypeScript 6.0.3 at this review. New selections must be compatibility-verified, not copied blindly. | [Cockpit package](https://github.com/wtcross/hfcache/blob/6b8fae2e0997403ae5c716a2e92148af0a972af9/cockpit/package.json) |

The imported mockup uses fictional repositories and values and is not evidence of endpoint availability or production state. HuggingFaceModelDownloader organizational inspiration was reviewed at `20f4be12d05012afbefbf54ad13dcfc12c6560b9`; no code or feature list from it is required by this plan.

## Primary external references consulted

Use these for implementation details, verify against pinned dependency versions, and cite relevant sections in new ADRs/operator guides. Do not copy documentation wholesale.

- [Caddy application and proxy patterns](https://caddyserver.com/docs/caddyfile/patterns): isolate SPA fallback from API routes; prefix semantics are application-specific.
- [Caddy basic_auth](https://caddyserver.com/docs/caddyfile/directives/basic_auth): edge-wide Basic is deliberately not selected for the shared bearer-protected application.
- [FastAPI HTTP Basic](https://fastapi.tiangolo.com/advanced/security/http-basic-auth/): browser challenge and authentication mechanics; password storage must use a stronger verifier than its demonstration comparison.
- [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) and [password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html): browser mutation policy and maintained password hashing.
- [TypeScript strict](https://www.typescriptlang.org/tsconfig/strict.html), [Vite production and base paths](https://vite.dev/guide/build): strict frontend and static asset deployment.
- [react-markdown security guidance](https://github.com/remarkjs/react-markdown#security): renderer extensions must preserve URL and sanitization protections.
- [Playwright continuous integration](https://playwright.dev/docs/ci): real browsers, finite suite timeouts and reproducible execution; use the repository's provider-neutral scripts rather than introducing a CI-provider workflow.

## Remaining implementation decisions

The architecture is selected; WEB-001 resolves concrete DTO names/limits, host-helper private protocol, config patch representation, release asset manifest integration, dependency versions and ADR identifiers against the live checkout. Any necessary adjustment must preserve user scope and have explicit contract/test consequences. This is not permission to defer basic security, functional testing, host parity, or documentation until after the UI ships.

## Execution reconciliation (2026-10-20, WEB-001)

Actual initial HEAD is exactly the baseline above, with inactive plan selector,
no existing WEB work-package family or feature branch, and only the intended
untracked extraction. No drift/reset/rebase or unrelated-work disposition is
needed. Created `feat/web-ui`; activated the plan under the new explicit
instruction. Prior rollout authority is not reused. No production manager, API,
archive or credential inspection supplies this audit.

Re-audited `api/app.py`, `auth.py`, `command_models.py`, catalog adapters and
capture/storage, configuration models, Caddy template and Cockpit's fixed
candidate/host boundaries. Concrete changes required before implementation:

- Current interface classification recognizes REST/MCP only; UI needs a separate
  recognized prefix path without weakening corroborated Unix scope.
- Current public principals/capability/receipt schemas are strict credential
  classes. Browser subject/admin permissions and key scoping need independent
  internal identities/projections, not additional fields on old wrappers.
- Authentication currently precedes cheap request limits. Bounded expensive
  Argon2 admission needs cheap limits first while preserving authenticate-before-
  disclosure/body parsing.
- Current operational fingerprint omits tags. Configuration CAS needs a separate
  full-byte opaque revision; fixed original config lock/candidate/backup remain.
- Existing observations omit README presentation. Bounded README source digest
  comparison is an explicit narrow amendment of the old refresh no-hashing rule;
  GET remains metadata-only and confidence unchanged.
- Existing rootless schedule/observer proofs deny those actions. Preserve that
  result and prove positive native controls separately; create no scheduler.

The [execution contract](execution-contract.md) fixes exact managed DTOs, route
delta, permissions, helper lock/outcome protocol, card states/budgets and immutable
assets. Decisions 140–143 accept design with implementation gaps; decision 144
retirement remains proposed. WEB-002/004/014 own compatible dependency selection
and locked, benchmarked verification rather than copying unverified versions.
See [prerequisites](prerequisites.md) for actual available infrastructure and
unperformed provisioning. Original bundle/reference hashes remain extraction
provenance, not current mutable execution-file hashes.

### Baseline gate correction

The exact detached baseline passes 5299 Python tests and wheel/installation
checks but exposes an intermittent Cockpit confirmation failure. Focused runs,
actual rendered-helper xtrace and an independent shell-only reproduction locate
a builtin-only process-substitution wait returning `-1` after complete line
reads, before configuration/lock effects. This is distinct from earlier NUL
transport, PID1 output and uninspected installed-host symptoms.

WEB-001 includes the necessary narrow baseline correction: constant anchored
base64-line matching/capture in memory, exact frame reconstruction and unchanged
external reader/decoder completion and byte/content guards. A tentative shell
parameter splitter was rejected for maximum-frame cost before acceptance. The
final maximum 2,796,210-byte parse measured about 0.415 seconds in the owned
fixture. Deterministic old-source failure/new-source pass and malformed/maximal/
empty-base regressions accompany the corrected full gate; exact results live in
the task evidence. No production source or service was replaced.
