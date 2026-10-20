# Resolved execution contract

WEB-001 accepts these design boundaries against exact baseline
`6b8fae2e0997403ae5c716a2e92148af0a972af9`. They are implementation requirements,
not implemented feature claims. Standing contracts/ADRs state their conformance
gaps. Changes during implementation require explicit amendments and evidence.

## Baseline and decisions

No source drift exists. Initial checkout was `main`, with only this intended
bundle untracked. No WEB IDs or `feat/web-ui` branch existed and the selector was
inactive. Activation preserves every historical task, rollout restriction and
original unknown operation/candidate. The source audit reconfirmed existing
catalog/maintenance/job routes; none needs a duplicate UI endpoint.

Allocated decisions: 140 authentication/static serving, 141 protected host and
configuration administration, 142 card adjuncts, 143 frontend/tool gates, and
144 conditional Cockpit retirement. Decision 144 remains proposed until parity.
Dependency versions are selected and verified in WEB-002/004/014, as required by
their tasks; this package adds no runtime dependency.

## Frozen route delta

Paths below are relative to `/api/v1`, except `/ui/`. Existing route DTOs,
capabilities, Envelopes, credential classes and MCP's fourteen tools stay strict.

| Method | Path | New authority |
| --- | --- | --- |
| GET | `/config` | `config-read` plus protected helper policy |
| POST | `/config/applications` | `config-write` plus protected helper policy; keyed |
| GET | `/repositories/{type}/{namespace}/{name}/publications/{sha}/{publication_id}/card` | existing REST read |
| GET | `/host/status` | `host-read` plus protected helper policy |
| POST | `/host/sync-schedule/validations` | `host-read` plus schedule policy |
| POST | `/host/sync-schedule/changes` | `schedule-write` plus schedule policy; keyed |
| POST | `/host/sync-observer/stops` | `observer-stop` plus observer policy; keyed |
| GET | `/host/journal` | `host-read` plus diagnostic policy |
| GET/HEAD | `/ui/`, recognized navigation, indexed assets | Basic administrator |
| GET | `/ui/bootstrap.json` | Basic administrator; independent schema 1 |

Extend `/config/validate` and `/plans` with one mutually exclusive `managed`
alternative; do not change omitted or literal `candidate` canonicalization.
Unknown, mixed, null and coerced alternatives refuse. New versioned assessment
payloads apply only to the managed form. No tag CRUD, cancel, payload, card
refresh, scheduler, generic shell or arbitrary systemd endpoint is authorized.

## Managed configuration

`ManagedEditRequest` is `{base_revision, edits}`; schema version is conveyed by
the versioned containing projection. `base_revision` is an opaque authenticated
binding to schema, archive UUID, fixed target and **complete exact bytes**,
using a protected stable random HMAC key. It is not a raw configuration hash.
Maximum installed/candidate text is 1 MiB UTF-8. Maximum edits is 256. Reject
repeated repository identities and allow at most one settings-replace, rather than
making ordering significant. The closed edit union is:

- `{kind: "repository-upsert", repository: <existing RepositoryConfig fields>}`.
- `{kind: "repository-remove", repository_type, repository_id}`.
- `{kind: "settings-replace", settings: <nonempty closed nested object>}`. Its
  optional children are `storage`, `sync`, `verification`, `repair`, each a
  nonempty object of supported field replacements; dotted keys refuse.

Editable settings are `storage.publication_mode`, `storage.minimum_free_space_gib`,
`storage.minimum_free_space_percent`, `storage.maximum_revisions`, the existing
`sync` fields, `verification.lock_wait_seconds` and
`repair.retired_instance_grace_hours`. Every value uses its current strict
configuration constraint. All Hub fields, root/UUID, schema version, required
hashing/algorithm, server/auth/helper/listener and filesystem paths are protected.
Read projection contains only editable values, constraints and fixed protected-field
explanations. No secret/redaction placeholder can be round-tripped as a value.

Reconstruct one deterministic TOML candidate on the server from the fresh full
base; preserve protected values, repository order for existing entries and
canonical order for additions. Show any serialization/comment changes in review;
the preserved predecessor contains original bytes. Validation, sizing and Apply
use that same reconstruction and opaque candidate binding. Upsert replaces all
supported repository fields, including normalized tags and declared dependencies.
Remove changes configuration only. Read never creates locks or adopts candidates.

Apply body is `{managed: ManagedEditRequest, preview_operation_id}`. Preserve the
existing `selectorsNeedingPreview` rule from `cockpit/src/lib/config.ts`: derive
the exact **newly added, newly enabled or revision-retargeted enabled repository
set** server-side. The managed form requires selectors omitted or empty, never
a caller-selected subset. A nonempty required set needs successful complete
Hub sizing for that exact set/resolved revisions/candidate/base/archive and
independent Hub permission. Tag-only, settings-only, removal-only and other
empty-required-set edits retain the existing no-Hub rule. After syntax/authority
validation they receive an explicit successful no-Hub managed assessment; the
bound assessment operation is still required. This preserves an existing class
rule rather than inventing a tag exemption, and lets configuration-only guarded
profiles edit tags without granting Hub authority. Mere HTTP 200 or client
assertion grants nothing.
Helper checks that bound managed assessment against
the fixed local receipt/result store read-only, not an arbitrary posted result.
No raw configuration is persisted in generic receipt/event/result data.

## Privileged boundary and uncertainty

The application remains unprivileged. Helper protocol schema 1 uses finite
length-prefixed UTF-8 JSON over one protected AF_UNIX socket, at most 2 MiB per
frame (independent of the 1 MiB decoded candidate/base limits), one request per
connection and finite deadlines. Preparation sends managed edits and an opaque
base binding; base and candidate are reconstructed in the protected workspace,
never sent together as raw documents. A candidate-only response must also fit
the encoded frame bound; excessive JSON expansion refuses. No descriptor
passing, shell command, caller path, unit, manager,
credential or archive selector is accepted. Requests have `schema_version`,
`request_id`, `operation`, and strict operation-specific `body`; responses bind
the same identity and a closed outcome. Operations are `status`, `config-read`,
`config-prepare`, `config-apply`, `outcome-read`, `schedule-validate`,
`schedule-change`, `observer-stop`, `journal-read`. Unknown keys/versions refuse.

Socket owner/mode and actual SO_PEERCRED mapping are pinned to protected
deployment configuration. Rootless mapping needs real process/namespace proof;
a supplied principal/UID is not that proof. Helper independently checks indexed
physical release/config/profile and six-category host policy before effects.
Bearer writers receive no new administrative capabilities. API authentication
and permission checks precede body parsing; helper policy grants no browser login.
Helper never contacts Hub, opens archive payloads or gains archive-write authority.

Preserve `/etc/hfcache/.configuration.lock`, `.candidate.toml` and `config.toml.bak`
semantics from the legacy pipeline. A conflicting candidate or unexplained backup
refuses; no automatic adoption/deletion. A prior backup positively bound to a
confirmed helper outcome is copied durably to that operation's protected evidence
and exact-checked before replacing the fixed backup with the new predecessor.
Preserve unknown/legacy backups for explicit reconciliation rather than silently
overwriting them. This allows subsequent confirmed applications without deleting
the earlier predecessor. Preparation holds the existing flock only while
snapshotting exact bytes. All validation/Hub sizing runs outside it. Apply tries
the same noncreating original lock nonblocking, rechecks base/candidate/preview,
durably preserves predecessor, atomically installs 0640 root:hfcache, fsyncs and
checks exact content plus operational fingerprint before confirmed success.

API receipt-store/admission locks are released before helper calls. Helper local
outcome-store lock may precede its nonblocking config flock; neither crosses a
network/API call or archive lock. Read-only assessment lookup is bounded and
does not acquire API writer locks. No API path holds a config lock while waiting
for domain work. This avoids a legacy client holding the config lock while its
preview waits in the same mutation lane. Busy refuses rather than waiting in a
lock cycle. Already admitted domain jobs keep their immutable policies.

Independently version helper outcomes under a protected local 0700 workspace,
0600 records. Persist intent before effects and retain candidate/predecessor
material associated with uncertainty. Resource ceilings refuse admissions, never
evict unresolved records. API restart does not dispatch helper mutations again.
Original-key/ID lookup uses outcome-read and exact guarded reads only. Outcomes
are `unchanged`, `confirmed`, `installed-unconfirmed`, `conflict`, `unknown`;
missing history never becomes unchanged. No rollback/cleanup/replay route.

## Fixed host controls

Native positive controls require a proven indexed system-manager binding.
Selected rootless schedule/observer permissions stay false; never substitute
same-named user units. Status includes bounded six-category effective permission
reasons, fixed unit facts, schedule and opaque schedule revision; helper failure
is unknown/unavailable, not inactive. Verification timer is display-only.

Schedule validation accepts `on_calendar` (1–4096 printable ASCII bytes without
backslashes) and `randomized_delay` (1–256 printable ASCII bytes without
backslashes), invokes fixed systemd-analyze
argv with bounded output/deadline, and writes nothing. Change is a discriminated
union `pause|resume|replace|reset`, always with `expected_revision`; replace alone
carries validated calendar/delay. Observer stop requires exact expected invocation
ID and fixed scheduled-observer identity. It never cancels accepted work.
Journal source enum is `sync|verification|api|worker`, limit 1–200, opaque cursor,
maximum 64 KiB projected page. No arbitrary journal predicates or paths.

## Authenticated assets and principal

One protected schema-1 administrator record supplies stable subject, username
and Argon2id hash. Initial verification target is m=65536 KiB, t=3, p=1,
salt=16/hash=32 bytes; WEB-004 benchmarks this before acceptance. Header <=8192
bytes; decoded username <=128 and password <=1024 UTF-8 bytes; record <=8192.
Admission permits two active verifications/eight waiting, with a bounded global
30-failure/60-second window; throttled work does not perform Argon2. Cheap limits
precede verification. Use a dedicated bounded executor off the ASGI event loop,
independent of metadata/operation observation pools. Recheck the failure window
when queued work starts; request cancellation releases capacity only after the
actual hash work completes. Validate protected PHC algorithm/version and exact
selected m/t/p/salt/hash parameters at startup before any verification, so an
otherwise syntactically valid record cannot choose unbounded hash work.
Wrong-user verification performs equivalent hash work.

Principal includes stable subject, method, credential class and internal capability
set. Existing public class values remain unchanged. Basic maps original keys
through a domain-separated stable-subject digest before store lookup; include a
NUL/domain and length-framed subject/key in the hash preimage, outside the legacy
printable raw-key grammar. Do not translate to a printable raw key that a bearer
could submit to collide with the Basic namespace. Bearer key digests remain
byte-identical. Private human attribution is separately
versioned; old receipts are never retroactively attributed to a person. UI schema-1
bootstrap exposes only safe subject/display, effective capabilities/reasons,
archive and UI/server contract/build identity and configured relative paths.

Unsafe Basic requests require one exact configured HTTPS Origin, JSON and
`X-Hfcache-Request: 1`. No-Origin bearer compatibility remains. Basic never
authenticates MCP. Every UI route authenticates; SPA fallback is recognized
GET/HEAD navigation only. Public prefix is server configuration, never headers.
No new Caddy instance/listener/file-server/global Basic gate is introduced.

Static release manifest schema 1 pins source commit, contract version, lock and
toolchain digests, licenses and each member's path/size/SHA256/MIME. Limits:
4096 members, 64 MiB total, 8 MiB/member and 2 MiB manifest. Initial MIME allowlist:
HTML, CSS, JavaScript, JSON, PNG, WebP and WOFF2. No SVG, source maps, unindexed
members, symlinks or special files. Enabled missing/mismatched assets fail startup;
disabled UI leaves backend-only installation independent. Validate immutable
members once at startup, retain pinned descriptors/identity for bounded reads.

## Cards

RepositoryCard schema 1 is a new adjunct at
`published/metadata/cards/{models|datasets}/{namespace}/{name}/{sha}/{publication_id}.json`.
Fields: `schema_version`, `kind="repository_card"`, `archive_id`, `repository_type`,
`repository_id`, `commit_sha`, `publication_id`, `publication_generation`,
`manifest_path`, `manifest_digest`, `source_path`, `expected_source_sha256`,
`captured_at`, `presentation_version="markdown-1"`, `state`, `markdown`,
`presentation_sha256`, `diagnostics`. Source is root manifest-listed `README.md`
or null for absence. Durable states: `present|absent|unsupported|oversize|unsafe|failed`.
Only present has Markdown/presentation digest. Read projection adds explicit
`not_captured` for missing adjunct; vanished exact publication is HTTP 404.
Diagnostics are fixed codes, never source fragments or arbitrary exception text:
`readme_absent`, `source_oversize`, `presentation_oversize`,
`source_digest_mismatch`, `source_changed`, `invalid_utf8`,
`unsupported_markdown`, `unsafe_content`, `secret_suppressed`, `work_limit`,
`read_failed`. Non-absent states retain source identity even when presentation
fails; absent alone has null source path/expected digest.

Raw source <=1 MiB; UTF-8 **and JSON-encoded presentation body** each <=1 MiB;
whole durable record <=2 MiB. Charge existing shared source-read/work/attempt
budgets and bound aggregate serialized adjunct writes to 128 MiB per invocation.
Failure stops capture with explicit classification and preserves publication
success/evidence. Source SHA256 comparison is bounded README-only provenance,
never a verification result. No other payload hashing expansion is authorized.
Sanitize before output/hashing; GET opens only adjunct/authoritative metadata,
never payload/Hub/credentials/locks, never captures or resurrects removed content.

## Evidence delivery

`acceptance-evidence.json` names planned exact layer tests for all 95 scenarios;
every row starts pending with no executions. Implementing owners must create
covering tests and record real source/artifact/profile/command/node/outcome facts.
Plan tests validate allocation and reject a completed row with only planned tests.
They establish no AUTH/ROUTE/CONFIG/CARD/host/UI functional acceptance.
WEB-002 proves the preliminary shell in a real browser; WEB-004/005 introduce
native challenge and real Caddy/installed API coverage, with later tasks extending
that harness continuously. Required missing prerequisites block their task.
