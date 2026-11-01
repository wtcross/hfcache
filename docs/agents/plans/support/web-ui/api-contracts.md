# API and authority requirements

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `aad1622ed3632b0d4fdf4b6c6bb2c2e54a14291dee9e815d43a480eda50ba98c`,
original content SHA-256 `c137ef685b841915076bde2cebf5a8cbd31887aeb92c39a8e09a14d5a3558cbb`.
Historical proof hashes identify the original artifacts, not this edited record.

All proposed paths are relative to `/api/v1`, except `/ui/*`. Finalize the exact names in WEB-001 against current code, then amend `docs/api.md` and schemas before implementation. Do not create endpoints already present at execution time. Existing routes retain method/body/query/permission/error/size constraints and stable wrappers.

## Reuse existing routes

| Requirement | Existing route family |
| --- | --- |
| Catalog search, tags/formats/quantization facets | GET `/catalog/search`, `/catalog/facets` |
| Type-aware detail and exact model variants | GET `/catalog/repositories/{type}/{namespace}/{name}` and `/variants` |
| Refresh offline technical metadata, including planned card capture | POST `/catalog/refreshes` with existing `technical=true` semantics amended narrowly |
| Status/inventory/revisions | GET `/status`, `/repositories`, `/repositories/revisions` |
| Current/exact references and manifests | Existing repository `/references/{revision}` and `/manifests/{sha}/{publication_id}` |
| Validation/sizing | POST `/config/validate`, `/plans` |
| Sync/verification/diagnostics | POST `/syncs`, `/verifications`, `/diagnostics`; GET `/verification/estimate` |
| Maintenance | Existing prune/purge/recovery/quarantine preview/apply and `/repairs` |
| Operation observation/history/reports | GET `/operations`, `/operations/lookup`, original ID/result/events, `/runs`, `/runs/{id}` |
| Connection/version/current wire capabilities | GET `/health`, `/version`, `/capabilities` |

No generic `/models`, `/datasets`, `/dashboard`, `/tags` CRUD, global search, cancellation, SSE, or WebSocket endpoints are needed. Do not add a per-repository operation-history filter without proving existing bounded report/operation reads cannot meet the stated presentation. Showing 'recent loaded history' is acceptable; claiming a complete repository audit from one page is not.

## Necessary additions

| Proposed endpoint/surface | Why it is necessary | Authority and effects |
| --- | --- | --- |
| GET `/config` | UI needs editable installed configuration and exact-byte concurrency identity; validation output is not the installed document. | Explicit config-administration read permission; protected host proof; no archive/Hub effects. |
| POST `/config/applications` | historical frontend's privileged atomic configuration installer has no REST equivalent. | Explicit config-write permission plus protected helper policy; keyed durable admission; root helper performs exact guarded local write/backup/confirmation, never arbitrary host/archive changes. |
| GET `/repositories/{type}/{namespace}/{name}/publications/{sha}/{publication_id}/card` | Existing observations omit the README body. | REST metadata read; exact retained publication, bounded adjunct read only; no payload/Hub/refresh effects. |
| GET `/host/status` | Host policy/binding, fixed unit/timer states and safe effective-action reasons are not archive readiness. | Explicit administration read permission; narrow helper; no arbitrary unit query. |
| POST `/host/sync-schedule/validations` | Preserve authoritative systemd calendar/timespan validation before edits. | Admin policy; synchronous bounded fixed validation process; no write/lock creation. |
| POST `/host/sync-schedule/changes` | Preserve timer pause/resume, drop-in apply and reset. | Typed closed action union; keyed outcome record; exact expected schedule revision and protected supported-profile proof. |
| POST `/host/sync-observer/stops` | Existing stop-observer operation is not job cancellation and needs exact binding checks. | Keyed fixed action; explicit expected observer/service invocation identity and host policy; never stops API/worker/target. |
| GET `/host/journal` | Preserve optional bounded host diagnostics, not invent job outcomes. | Admin read policy; fixed enumerated source, bounded opaque cursor/limit, redaction; no arbitrary filters, paths or shell. |
| Authenticated `/ui/` shell/assets and optional `/ui/bootstrap.json` | Serve the SPA with safe deployment base and independently versioned UI context. | App-owned Basic/appropriate REST auth; static non-archive assets; no new listener or user-management API. |

`/host/status` includes the bounded sync schedule view/revision and read-only verification timer facts, avoiding a redundant schedule GET. Adopt a single consistent change envelope; do not expose both PUT and action-specific POST routes for the same mutation. A deployment may deny host actions, but implementation must preserve positive supported-profile paths and prove them in isolated tests.

## Config read and managed edits

GET `/config` returns a strict, versioned **nonsecret editable projection**, a strong opaque `base_revision` tied to the complete installed bytes (including tags), supported editable field metadata, and safe descriptions of protected fields. It is not a browser-selectable path. The revision must not disclose secret-dependent content hashes: use an opaque server binding/HMAC with a protected stable key or equivalent token-to-digest record. Bind archive, installed target, full base bytes, and schema. A tag-only edit invalidates the base revision even though the operational fingerprint is unchanged. Reads never recreate missing locks/files or delete an existing candidate.

Prefer a typed managed-edit representation, such as validated repository upsert/remove and supported global field replacements; never accept arbitrary JSON pointers/filesystem paths. Resolve edits against fresh installed content **server-side**, preserving hidden/protected fields. No redaction placeholder is valid replacement data. Client-side JSON/TOML serialization cannot establish exact candidate identity. Changes to root/UUID/Hub endpoint/credential source/restart-only server policy are shown as unsupported/manual authority changes; do not hot-switch them. Provide safe operator instructions rather than a generic permission bypass. Where full nonsecret TOML editing remains supported, preserve strict exact-byte candidate semantics and reject embedded secrets rather than round-trip masked placeholders.

Extend existing `/config/validate` and `/plans` request models with a mutually exclusive managed-edit form (`base_revision` plus typed edits), while retaining existing installed and literal `candidate` forms unchanged. Unknown keys, mixed forms and coercion refuse. The server reconstructs one exact candidate using the same service in validation, preview and apply; plan result identity binds candidate digest/base and archive. Use independent new response projection/schema for managed-edit assessments where needed; old request forms keep old response shapes. Preserve read-only installed-plan authority versus writer candidate authority. Token/path controls remain separate from body input.

POST `/config/applications` supplies the same managed edit, base revision and the exact required successful preview handle/assessment reference. A preview reference is evidence to validate, not a transferable authorization token. The server/helper must revalidate capability, protected host policy, candidate compatibility, base bytes, preview correspondence, and exact selected scope before effect. If preview is not required for a class of changes by the current documented rule, preserve that rule explicitly; do not invent an exemption for tags merely for speed. Failed or stale preview/assessment invalidates Apply. Do not submit a hidden second preview/Apply on reconnection.

Define canonical admission bytes so idempotency is deterministic and existing job canonicalization is not changed. Persist no credential values or raw configuration in generic operation receipts/events/results. Retain private candidate material only in the documented protected configuration workspace where needed; do not use a world-readable or browser-provided temporary pathname. Bound lifetime/size and retain material associated with unresolved effects. A resource limit refuses new work; it never removes uncertain evidence to make room.

## Configuration atomicity and reconciliation

Implement the existing sequence with explicit outcome evidence: base and candidate prepared; validation/required preview observed; base rechecked under the **same existing** configuration lock; predecessor durably preserved; candidate atomically installed with `0640 root:hfcache`; installed exact bytes and expected operational fingerprint confirmed. Keep admitted policy immutable and all archive/Hub authority checks intact. Never hold a root helper or config lock across unbounded network work. Defined lock order must exclude cycles with API admission/store locks and the archive flock.

Crash boundaries include receipt-before-helper, candidate stage, backup fsync/rename, installed rename, parent fsync, confirmation, and result persistence. A restart does not replay an uncertain host mutation. Reconcile only by authenticated original key/ID plus guarded exact-content/binding reads. Classify installed-unconfirmed, unchanged, conflict and unknown; do not convert an API timeout into 'not applied'. Helper disagreement/missing history blocks another apply. No new rollback/cleanup route is necessary; operator-guided reconciliation preserves candidate/backup evidence.

## Card contract

The card payload has an independent schema with archive/repository/commit/publication identity, manifest locator/digest, source path and expected source digest, capture/presentation version and time, state, bounded sanitized Markdown or null, and fixed diagnostics. Final state vocabulary must distinguish present, absent README, not captured, unsupported/oversize, failed/unsafe and unavailable exact publication. HTTP 404 for a vanished publication never falls back. Invalid adjunct schemas/identity/bounds return classified errors, not successful empty content. Missing adjunct for a retained publication is a normal explicit unavailable state. Do not treat schema absence as permission to inspect payloads.

API JSON is no-store, nosniff and fully authenticated. Do not expose text/html or an unsanitized raw download. Every path component uses existing identity grammars; no file-path or URL parameter. Metadata reads obey the bounded pool/lease lifecycle through slow-client/disconnect completion. Preserve byte budgets across encoded Markdown and JSON, including multi-byte characters. Schema generation and runtime validators cover the entire payload, not a free-form dict.

## Host protocol and compatibility

Helper protocol grammar, socket permissions/peer checks, operations and limits must be fixed and independently versioned. Host write requests specify only validated domain values and exact expected revisions/identities. Helper status must remain distinguishable from daemon readiness. Prove role isolation with actual process/namespace identity; don't pass root authority through a browser session claim. Generic bearer writer access does not imply config or host administration. Recheck permissions when work leaves the queue, not only on admission.

Keep operation public credential-class grammar and legacy REST/MCP request/response schemas unchanged unless a concrete versioned transition is necessary. Test the actual old installed clients against the new server. New private helper/control/card state can make binary rollback incompatible; document and drill it, preserve unknown records and do not delete state to force old startup. API routing contracts are versioned separately from internal durable schemas.
