# Serve a bounded authenticated UI artifact with an independent bootstrap

- Decision identity: 147.
- Status: Amended; product conformance uses the acceptance method below.
- Date: 2026-10-20.
- Introducing evidence: this commit; source and isolated acceptance remain separate.

This decision fixes the concrete asset, bootstrap and routing contracts. It
establishes no installed release or production availability by itself.
The acceptance-method amendment at the end supersedes earlier mandatory
instrumented-runner statements; all product, resource and security requirements
remain in force.

## Decision scope and relationships

Serve an explicitly enabled, indexed immutable artifact from the existing API
application. The existing Caddy remains the sole public TLS proxy to the existing
Unix upstream. Every UI request, including assets, errors, the slash alias and
bootstrap, requires the protected Basic administrator. REST keeps its current
Basic-or-appropriate-bearer policy and MCP remains its separate bearer-only app.
No global Caddy Basic gate, public asset exception, browser token, second frontend
server, runtime Node process or archive file-serving surface is introduced.

Amend decision112 (restart-only optional configuration),113 (lifespan/bounds),123
(one projection plus explicit prefix migration),140 (implemented static detail),
143 (artifact/gate detail) and146 (Basic-only UI clarification). Review124 for
unchanged MCP mount/alias behavior. Extend INV-013/019/021, server/API/security,
schemas, deployment/container, development/script and human UI guides together.
Do not change archive schemas, publication identity, /capabilities, old receipts,
operation handles, native transport proof or no-replay recovery rules.

## Strict DTO conventions

All objects below are strict, frozen, extra-forbid Pydantic models. All output
fields are required on the wire; null is explicit and never filled from a Python
default by a browser decoder. Reject duplicate JSON keys, coercion, unsupported
versions, lone surrogates and bounds before constructing trusted values. Integer
fields are actual integers, never bool/decimal/exponent spellings at the browser
boundary. SHA256 is exactly64 lowercase hexadecimal characters; commit SHA is
exactly40. UUID is the current canonical lowercase hyphenated archive UUID.
Use the existing application canonical serializer (sorted keys, indent2,
UTF-8/ensure_ascii=False, standard separators and exactly one final newline) for
the disk manifest; canonical bytes are checked independently in Python/Node.

Model names are UiAssetManifest, UiBuildMetadata, UiToolchain,
UiHtmlMetaIdentity, UiAssetMember, UiBootstrap, UiPaths, UiUser,
UiAdminPermission and UiBuildIdentity. No arbitrary JSON or dict[str,Any] is
needed in these models. The names/keys below are concrete schema1.

## Optional server configuration

The `[web]` fields are `enabled: bool=false`, `asset_root: AbsolutePath|null`,
`manifest_sha256: Sha256|null`. With enabled=false, nulls are accepted and no
asset path is opened or scanned. With enabled=true, both nonnull values and a
configured Basic provider are required. UI-enabled startup additionally requires
the canonical Basic origin <=4096ASCII bytes and configured root_path <=1024UTF-8
bytes, so bootstrap and rendered metadata fit their explicit schema limits. These
new byte ceilings do not apply to backend-only web-disabled deployments. The
global leading-double-slash safety migration below remains separate. The digest pins the exact canonical
manifest bytes, not a self-referential field in that manifest. Config remains
restart-only. Existing server schema1 deployments with no web table stay valid.

The configured root must be lexically and physically disjoint in both directions
from startup archive root, archive configuration, credential source files and
directories, API writable state, sockets and protected helper authority. Validate
before opening any asset member. File and every ancestor must satisfy the
documented protected root/current-service-owner, no group/other write, no-follow
policy; no symlink, hardlink alias, special file, mount escape or changed inode
is accepted. An enabled unsafe/missing/mismatched artifact refuses startup with a
sanitized configuration diagnostic; it does not silently disable the UI.

Capture and hash the indexed bytes once under pinned no-follow descriptors at
startup (maximum67108864bytes total), then serve those immutable captured bytes.
Retain the root descriptor and file identity evidence through lifespan; close on
every partial-startup/shutdown path. This bounds captured memory and avoids4096
live file descriptors and per-request rehashing. No request reopens an unpinned
checked pathname or builds assets. Pre-render only the public and corroborated
native shell variants, each <=8388608bytes after marker replacement; refuse a
larger rendered variant at startup. Release-switch testing uses separate immutable
captures, never a mutable mixture of indexed files.

Fixed initial output bounds: at most16 active UI body streams,
no queued stream waiters, maximum65536bytes per send chunk, and one absolute
30second whole-body send deadline. Acquire after authentication/route validation;
saturation refuses with the existing typed HFAPI009/503 unavailable response,
not an HTML success or unbounded wait. A refused small error is independently
bounded. HEAD sends no body and requires no body-stream slot. Disconnect,
OSError, deadline and request cancellation always release the exact lease in
finally. Send from shared captured bytes without a per-request full-member copy.
Bootstrap retains its separate32768byte body ceiling. Test actual stalled sends
and disconnects alongside concurrent REST/MCP observation. These accepted bounds
require actual stalled-send/disconnect proof and make no availability claim by
themselves.

## Asset manifest schema1

The manifest filename is exactly `manifest.json` at the immutable asset root.
It is not a served member and cannot list itself. Maximum encoded file size is
2097152bytes. Top-level exact keys:

| Key | Exact type/constraint |
| --- | --- |
| schema_version | literal integer1 |
| kind | literal `hfcache_web_assets` |
| build | UiBuildMetadata below |
| entrypoint | literal `index.html` |
| meta_identity | UiHtmlMetaIdentity below |
| members | tuple1..4096 UiAssetMember, strictly sorted by ASCII path and unique |

UiBuildMetadata exact keys:

| Key | Exact type/constraint |
| --- | --- |
| application_version | printableASCII string1..128bytes; exact backend build target |
| source_commit | commitSHA of the actual build base, never a fabricated future hash |
| source_snapshot_sha256 | SHA256 of the explicit source input inventory |
| source_dirty | bool; actual build source differs from source_commit |
| ui_contract_version | literal integer1 |
| rest_api_schema_version | literal integer1 |
| wire_source_digest | current source-audited wire IR source_digest |
| pnpm_lock_sha256 | SHA256 of exact web/pnpm-lock.yaml bytes |
| toolchain | UiToolchain exact object below |
| toolchain_sha256 | SHA256 of canonical UiToolchain bytes |
| licenses_sha256 | exact bytes SHA256 of served licenses.json |
| notices_sha256 | exact bytes SHA256 of served THIRD_PARTY_NOTICES.txt |

UiToolchain exact keys are `node`, `pnpm`, `typescript`, `vite`, each a
printableASCII string1..64bytes. Values come from the installed pinned tools and
are checked against the selected lock/package contract, rather than arbitrary
environment variables. React/runtime closure is already bound by the exact lock
and license inventory. No generated timestamp, machine pathname or credential
source appears in build metadata.

The deterministic source inventory is canonical JSON mapping relative path to
SHA256 for the exact build inputs: web/package.json, web/pnpm-lock.yaml,
web/index.html, web/vite.config.ts, web/tsconfig.json, web/tsconfig.node.json,
web/dependencies/licenses.json, web/THIRD_PARTY_NOTICES.txt and all regular
web/src/** and web/scripts/** files. Include exact package-manager configuration
only if the
artifact build actually consumes it; do not claim an inventory of inputs that
omits consumed notices/license bytes. Paths are sorted; no node_modules/dist/cache/artifacts or
browser material enters it. Include generator source and generated IR/Unicode
data. The inventory itself is an out-of-root build evidence artifact, not a
served member. `source_snapshot_sha256` hashes its canonical bytes. Refuse a
changed input during capture/build and record the actual git commit/dirty state.
Dirty local artifacts may be used in owned source tests, with dirty=true plainly
recorded. They never establish a clean release. Release packaging must require clean release
inputs and bind the independently verified backend wheel to this metadata.

UiHtmlMetaIdentity exact keys and literal values:

| Key | Literal token |
| --- | --- |
| ui_base | `__HFCACHE_UI_BASE_V1__` |
| bootstrap_path | `__HFCACHE_UI_BOOTSTRAP_V1__` |
| asset_fingerprint | `__HFCACHE_UI_FINGERPRINT_V1__` |
| ui_contract | `__HFCACHE_UI_CONTRACT_V1__` |

The raw indexed index.html must contain precisely one base element and exactly
one inert meta element for each name hfcache-ui-base, hfcache-ui-bootstrap,
hfcache-ui-fingerprint and hfcache-ui-contract. The base href and ui-base content
contain the ui_base token (exactly two byte occurrences); the other three meta
content attributes contain their corresponding token once each. No token is in
script text, event attributes, URLs other than those declared attributes or
comments. Validate both exact byte occurrence counts and element/attribute
placement at startup; blind text replacement is insufficient. No inline scripts,
inline styles, executable JSON, event attributes, CSP meta override or external
runtime URL is accepted. Deployment rendering replaces only these validated
slots with HTML-escaped, application-derived text. A per-request nonce is not
needed because every executable script remains an indexed external module.

UiAssetMember exact keys are `path`, `bytes`, `sha256`, `mime`:

- path: ASCII relative POSIX path1..1024bytes, components1..255bytes; each
  component begins with an ASCII alphanumeric character and otherwise contains
  only ASCII alphanumerics, dot, underscore and hyphen. No empty/dot/dotdot/hidden
  component, absolute path, slash alias, backslash, percent escape, query/fragment
  or control byte. Maximum path depth8. Strict sorted unique paths.
- bytes: integer0..8388608; sum of all members <=67108864. Entrypoint must be
  nonempty. Counts and bytes are enforced before and during capture.
- sha256: exact SHA256 of captured raw bytes, not a filename token.
- mime: one of `text/html`, `text/css`, `text/javascript`, `application/json`,
  `image/png`, `image/webp`, `font/woff2`, or the fixed-filename text/plain
  exception below. Extension must exactly agree:
  .html/.css/.js/.json/.png/.webp/.woff2, respectively. Exactly one HTML member,
  index.html. No .svg, .map, compressed sidecar or unsupported type.

Required members: index.html, licenses.json (MIMEapplication/json) and
THIRD_PARTY_NOTICES.txt. Amend the initial MIME allowlist narrowly to permit
`text/plain` only for the exact root filename THIRD_PARTY_NOTICES.txt; no other
.txt path or general text/plain member is allowed. Its body is the pinned shipped
notices text, with no executable rendering. All other members live below assets/.
Reserve bootstrap.json and every navigation path; no file can shadow dynamic
bootstrap or fallback routes. The inventory must exactly match the bounded root
tree apart from the manifest itself and directory entries. Enforce at most4096
member files,4096 directories and8193 total entries including manifest, depth8;
count unknown files and directories before descending and stop at the first
exceeded bound. Unknown/unindexed files refuse startup and are never served.

Asset fingerprint is SHA256 of the exact canonical manifest bytes. It is not
stored inside that manifest, avoiding self-reference. Server configuration,
UiBuildIdentity and inert HTML fingerprint meta all use that same value.

## Nonsecret bootstrap schema1

Authenticated GET/HEAD `effective-prefix/ui/bootstrap.json` returns plain typed
JSON, not an Envelope or changed /capabilities payload. No query/body fields.
Maximum encoded response32768bytes, depth16,2048 JSON tokens,128 aggregate object
keys. Use existing strict native-number parser and bounded read with these lower
explicit limits. Reject missing/extra fields, unknown permission/contract values,
duplicates, unsafe numeric tokens and identity/path contradictions.

UiBootstrap exact keys:

| Key | Exact type/constraint |
| --- | --- |
| schema_version | literal integer1 |
| kind | literal `hfcache_ui_bootstrap` |
| ui_contract_version | literal integer1 |
| rest_api_schema_version | literal integer1 |
| wire_source_digest | SHA256; exact match with served build and compiled decoder IR |
| instance_id | exact32 lowercasehex from the existing application lifespan |
| authority_epoch | exact32 lowercasehex, initially equal to instance_id |
| configured_archive_id | canonical UUID from startup InstalledPolicy.archive_id |
| archive_identity_source | literal `installed_policy` |
| config_fingerprint | null initially; bootstrap does not reread archive/policy for health |
| configured_origin | exact canonical HTTPS Basic origin from configuration; ASCII<=4096bytes for UI-enabled deployment |
| paths | UiPaths below |
| user | UiUser below |
| build | UiBuildIdentity below |

The configured archive identity is explicitly not a verified sentinel, health,
writability, content, mount or NAS observation. Obtaining bootstrap never opens
archive storage or probes the Hub, helper or manager. Snapshot-backed reads still
validate their own archive/fingerprint and status. Original operation observations
remain bound to their receipts, not the current bootstrap fingerprint.

UiPaths exact keys:

- public_prefix: raw canonical configured root_path (empty or normalized path),
  UTF-8<=1024bytes under the UI-enabled startup constraint; not from Host/Forwarded
  headers. It introduces no global backend-only prefix byte ceiling.
- effective_prefix: raw trusted request projection, exactly public_prefix on
  public transport or empty only under the preserved corroborated Unix exception.
- ui_base: canonical percent-encoded absolute-path reference for
  effective_prefix + `/ui/`, with trailing slash; ASCII<=3076bytes.
- bootstrap: similarly encoded effective_prefix + `/ui/bootstrap.json`; ASCII<=3090bytes.
- api_base: similarly encoded effective_prefix + `/api/v1`, no trailing slash; ASCII<=3079bytes.
- mcp_base: encoded effective_prefix + `/mcp/` when enabled (ASCII<=3077bytes), else explicit null.

The encoded spelling uses the single URI-path encoder described below. Bootstrap
semantics bind each path to the effective/configured prefix and fixed suffix, so
no response-supplied arbitrary network endpoint is followed. Browser checks
configured_origin against window.location.origin and uses same-origin relative
paths with credentials:same-origin, cache:no-store and redirect:error. Request
headers cannot choose any endpoint. The API client scope retains the raw trusted
effective prefix; UI navigation/history uses the encoded ui_base to agree with
window.location.pathname for Unicode. Direct Unix tools can read their empty-root
bootstrap but cannot manufacture browser-origin proof.

UiUser exact keys:

- subject: exact principal stable ASCII subject, existing grammar
  `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}` with true fullmatch.
- display_name: string equal to subject initially; no username/password/hash or
  credential-source path. Future separately configured human display metadata
  requires its own exact bounds/escaping contract.
- authentication_method: literal basic.
- credential_class: literal rest-writer (compatibility label, not attribution).
- rest_capabilities: exact sorted array [read,write], derived from Principal.
- admin_permissions: exactly five UiAdminPermission records, sorted by capability:
  config-read, config-write, host-read, observer-stop, schedule-write.

UiAdminPermission exact keys are capability, granted(bool), effective(bool),
reason(enum allowed/not_granted/feature_unavailable). granted reflects the internal
principal grant, never generic bearer write. effective is true exactly when granted
and the corresponding UI feature/server authority is implemented and enabled;
reason is allowed iff effective, not_granted iff !granted, otherwise
feature_unavailable. No helper/network probe is made to produce this projection.
Initially all five are granted to the one administrator but effective=false and
reason=feature_unavailable: host/config/observer controls have not been implemented
yet. Later owning features update exact availability and independent enforcement.
Disabled controls explain this fixed reason; they do not imply authorization.

UiBuildIdentity exact keys are `asset_manifest_sha256` (the pinned fingerprint)
and `metadata` (exact UiBuildMetadata from the validated manifest). Validate build
and bootstrap ui/rest/wire contract equality and application target compatibility
before showing connected state or making domain calls. Build identity comes from
the artifact, not fictional prototype data or arbitrary request metadata.

## Mechanical generation and semantic audit

For enabled UI, compute the expected wire source digest once from
`hfcache.wire_schema.installed_source_digest()`, the existing pure registry/schema/
audited-source digest of the actual installed backend. It reads installed Python
authorities, not a frontend IR file or the supplied manifest, and runs before
accepting the capture. It needs no optional transport import, archive/policy/Hub
access, subprocess or network. Disabled UI does not invoke it. No generated
self-referential backend digest constant is introduced.

Derived cryptographic coherence is checked in its owning context with platform
implementations: Python hashlib during capture, Node crypto during the build,
and asynchronous browser WebCrypto SHA-256 before a trusted bootstrap scope or
mount exists. Synchronous generated DTO semantics retain structural/order/sum/
path coherence. No handwritten hash, skipped model hook or unavailable-crypto
fallback substitutes for these context checks.

Register the strict DTO authorities in the existing Python wire registry/export
path. UiAssetManifest is a named disk/artifact model, without a fake API route.
Add the fixed /ui/bootstrap.json row with a new explicit response_kind
`ui_bootstrap`; it is a typed plain object rather than a normal read Envelope.
Update the generator's closed response-kind grammar and client binding switch
exhaustively. Do not cast bootstrap JSON to a network interface or add any/unknown
identity accept hooks. Reuse the current Node IR, required-on-wire reconstruction,
runtime helpers and source pin manifests; every new model/context validator has a
stable semantic ID and manually reviewed Python+TypeScript source hash. Changes
to model/path/member-sum/permission coherence must fail export/generation until
their semantic ports are reviewed. HTML marker placement itself is a server
byte-content/context check: manifest token literals do not contain the HTML and
cannot prove placement. Source-audit the static HTML parser as a context authority
and independently check actual generated index bytes in Node/build tests. Browser
DOM bootstrap validation proves only the exact inert slots it can observe. Do
not attach a DTO hook that pretends to validate absent HTML bytes.

Add canonical disk golden and source-derived positive corpus entries; use
independent malformed/extra/missing/boundary literals and original Python oracle
negative classification. The manifest has a separate independent schema1 like
the protected administrator record, not the archive VersionedModel vocabulary.
Generated outputs remain checked source, not timestamp/HEAD-dependent output.

## Paths, fallback and explicit prefix migration

One trusted Boundary projection recognizes /api/v1, /mcp and /ui and selects the
effective root. Prefer configured-prefixed interface spelling, including prefixes
that overlap these names; corroborated native Unix may use the original unprefixed
interface spelling. Forwarded headers never establish locality or rewrite roots.

Reject configured root_path starting `//` as an explicit server-config migration.
Retain existing normalization/printable/no-whitespace/no?#percent/backslash rules
and ordinary accepted Unicode/punctuation/length when web serving is disabled.
Only UI-enabled startup applies the additional1024UTF-8-byte prefix and4096ASCII-
byte origin limits. No global backend-only byte ceiling or spelling normalization
is added. Operator guidance must explain how to choose a single-slash
prefix and restart the isolated deployment; no production change is authorized.

Define `uri_path(raw)` with urllib.parse.quote and exactly the safe ASCII set
`/:@[]!$&'()*+,;=` (RFC3986 unreserved characters are always safe). This preserves
the current printable ASCII path spellings used by ordinary native/REST/MCP
clients while UTF-8-encoding nonASCII and escaping quote/angle/control characters.
Never use urljoin/new URL with a possibly protocol-relative caller path.

Keep existing JSON operation links as the raw canonical application path; encode
only Location with uri_path(raw status). Update BOTH the browser acknowledgment
validator and the Python API client submit validator to compare Location with
the exact encoded expected status, while separately comparing raw JSON links
to the exact original route/ID. Python retains its exact one-Location-header
requirement. No origin/route/operation/principal identity check is relaxed, no
arbitrary Location is followed, and malformed acknowledgments retain the original
key/route as uncertain without resubmission.

Ordinary client-supported ASCII prefixes (alphanumeric/underscore/hyphen path
segments) and corroborated native unprefixed acknowledgments remain byte-identical
in both Location and JSON links. Existing standard Python ClientConfig already
limits public prefixes to that narrow ASCII grammar; this change does not silently
broaden it. Old clients that assume raw Location equality cannot be promised
compatibility for the previously server-accepted but non-URI-safe ASCII quote/
angle-bracket prefixes or Unicode prefixes. Those header spellings now become
canonical percent-encoded ASCII; JSON links retain raw text. Document this explicit
header migration and require compatible client validation or an ordinary ASCII
prefix. A valid admission observed by an incompatible old client remains uncertain
and must be recovered by its original handle/key, never retried as new work. Apply the same safe
path encoder to MCP slash redirect and UI alias; no Host/query reflection.

GET/HEAD `/ui` is an authenticated307 to the trusted encoded `/ui/` (no query).
GET/HEAD `/ui/` and the current exact workspace paths library, operations,
maintenance and administration receive rendered index.html. WEB013 also explicitly
recognizes `/ui/repositories/{model|dataset}/{namespace}/{name}` using the existing
repository component grammar. No additional segments, traversal or encoded
separators are accepted. The browser-only bounded fragment chooses a paired full
SHA/publication and one closed detail tab; it cannot choose request authority or
an arbitrary path. Query strings remain refused. Unknown UI routes receive
a typed404, not a successful catch-all shell. Indexed assets receive exact bytes.
Missing .js/.css, unknown/unindexed files, API typos, MCP errors, non-GET/HEAD and
traversal never receive HTML fallback. A GET/HEAD with a body or unexpected query
retains bounded explicit refusal. HEAD shares GET status/headers with no body.
No suffix guessing, arbitrary filesystem traversal, directory listing, Range,
service-worker route or on-demand build/rehash occurs.

## Exact security and cache policy

Choose one application-owned response class after authentication and validated
resource selection: ui_document, ui_bootstrap, ui_asset_private, ui_error or
legacy_api. Boundary owns and emits exactly one copy of each protected header;
strip preexisting copies only for these known protected names and then insert
the selected policy. Do not use an untrusted response header or request path alone
as permission to relax no-store. Legacy REST/MCP retain their existing no-store,
nosniff and frame-ancestors-none policy and byte/status/body behavior.

All UI responses, including redirects/errors/HEAD, receive exactly:

- X-Content-Type-Options: nosniff
- Referrer-Policy: no-referrer
- Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self';
  img-src 'self'; font-src 'self'; connect-src 'self'; base-uri 'self';
  object-src 'none'; frame-ancestors 'none'; form-action 'none'; worker-src 'none'
- Permissions-Policy: camera=(), microphone=(), geolocation=()

No inline/eval/data/blob/CDN allowances, CORS credential allowances, crossorigin
credential reflection or new global Caddy auth/security translation. Existing
Caddy TLS configuration remains authority for transport; do not add application
HSTS that would change unrelated native/HTTP test/deployment behavior.

Cache-Control exact values:

- ui_document, ui_bootstrap, ui_error, UI aliases, index/notices/license metadata:
  `no-store`.
- Only indexed, validated hashed assets below assets/ with a build-generated
  basename `<stem>-<token>.<allowed-extension>` with token grammar
  `[A-Za-z0-9_-]{8,64}`:
  `private, max-age=3600, immutable`.
- Every API/card/config response retains `no-store` under its own contract.

No public/s-maxage cache, Set-Cookie, Vary:Authorization trick, unversioned private
asset caching or user-specific static body. Initial implementation may omit
ETag/304/Range support; do not claim conditional or partial responses. MIME is
selected from the verified member record, never guessed from an untrusted suffix.
Content-Length is the exact rendered/body byte length; no Content-Encoding
sidecar; bounded send/disconnect cleanup must be tested.

## Runtime bootstrap and release-switch behavior

The indexed HTML contains a small inert fallback inside `#root`: a static
loading/start-failure explanation and an ordinary `href="./"` link labelled
Reload interface. The validated base element resolves that link to the trusted
UI root even on a deep link. No inline event handler, script or style is needed.
No extra metadata or token is introduced: the contract stays exactly two base
token occurrences and one occurrence for each of the three other meta tokens.
If the main JavaScript member is404, blocked or otherwise unavailable, no React
code can render an error; this existing HTML fallback remains visible and usable.
Do not claim a JavaScript-generated recovery message for a missing entry module.

The inert HTML exposes only the encoded base/bootstrap paths, UI contract1 and
asset fingerprint. Module startup checks exact DOM slot counts/attributes and
canonical values before one bounded authenticated bootstrap read. It validates
schema/source audit/origin/prefix/build bindings, constructs the trusted scope and
only then mounts the real application, replacing the fallback after successful
bootstrap validation and mount. Before that point, a bootstrap/startup failure
leaves the inert explanation and reload link intact; it must not clear #root and
leave an empty page. A failure may add only a fixed safe text diagnostic without
removing fallback recovery. Credentials remain entirely in native browser
authentication. No localStorage/sessionStorage credential, fake successful
bootstrap, silent Bearer translation or automatic Basic password handling is
added. Authentication expiration/refusal remains explicit.

The compiled JavaScript does NOT embed the final asset manifest SHA256: hashing
an output that contains its own fingerprint would be circular. Instead compiled
code binds UI contract1, the audited wire source digest and a non-self-referential
build source identity. Compute that source identity from the explicit consumed
source inventory before bundling and inject it as a build-only constant, without
writing a checked source file that contains its own digest. Build output,
manifest bytes and deployment-rendered HTML are excluded from that source input
inventory. After bundling, member hashes determine the canonical manifest bytes
and their fingerprint. The application inserts that validated manifest fingerprint
into the existing inert DOM slot and bootstrap; browser startup requires those
two separately delivered values to agree and requires bootstrap build metadata
to match the compiled contract/wire/source identity. It never compares a manifest
fingerprint against a fabricated self-referential compiled constant.

An already running page retains its validated DOM/bootstrap fingerprint in memory.
If a later bounded bootstrap read observes a different release fingerprint or an
incompatible contract/source identity, show an explicit update-required state
and a user-controlled reload action. A later lazy-chunk load failure can be
reported by the already loaded runtime in that state. These runtime messages are
separate from the inert fallback needed when the entry module never loaded.
Never reload automatically, clear unsaved drafts or discard/replay original
operation handles. All errors retain safe original IDs and uncertainty.
Feature-owned future draft and handle registries remain required; static-serving
acceptance alone cannot claim their later acceptance.

## Protected capture and finite response ownership

Use a new bounded mount-identity parser, preserving existing archive mount
classification. A snapshot is at most1048576bytes and8192entries. Retain mount ID,
parent ID, major:minor, root, mountpoint and filesystem type; decode only the
kernel mountinfo escapes. Reject malformed, duplicate or ambiguous deepest
stacked records. Map known lexical paths to device plus mount-root-relative
identity, detecting same-filesystem bind aliases without opening, statting or
resolving archive contents. Corroborate every opened asset descriptor's mount ID
and device against the selected snapshot. Ascending through system mounts is
normal; descendants must remain inside the selected asset mount. Require the
snapshot to remain unchanged through capture. Unsupported proof refuses enabled
UI only; disabled UI reads no mount or asset information.

Initially accept asset mounts on ext4, xfs, btrfs, tmpfs or overlay. Network and
unknown filesystems refuse enabled UI. This asset policy does not change existing
credential delivery: map protected credential mounts for exclusion without
forcing their pseudo filesystems through the asset allowlist.

Forbidden authorities are actual startup policy.root and policy.path, effective
injected OperationStore.root or configured state directory, resolved bearer and
Basic source files plus their delivery directories, explicit Hub token source,
effective listener/verification sockets and instance lock, and configured direct
application TLS private key/certificate paths and their containing directories.
Use real supplied values; do not invent a server-TOML source pathname, Caddy key
pathname or future helper authority. Add helper exclusions when such authority
actually exists. Never contact a manager, helper, archive or Hub to find them.

Every pinned root/ancestor/directory and member must be root/current-service-owned
and not group/other writable. Traverse under no-follow descriptors and verify
linked-name versus descriptor identity. Members must be ordinary single-link
files with stable device/inode/type/owner/mode/link-count/size/mtime/ctime around
bounded read; exclude atime. Retain a finite traversal stack and one root FD,
not all member descriptors. Count all descendant entries, including manifest but
excluding the root directory itself, before descent. Check directory mutation
and the unchanged mount snapshot before committing the capture.

Retain bounded ancestor identity metadata and perform a final no-follow rewalk
with at most two ascent descriptors, checking original device/inode/type/mode/
UID/GID/link count and each linked name before accepting capture. This detects
higher-ancestor rename/replacement without requiring unrelated shared ancestors
such as `/opt` or the fixture parent to keep their directory mtime/ctime unchanged.
The captured root/descendant directory mutation checks and member-read identity
checks still include size/mtime/ctime. No archive target is opened for this proof.

Capture after protected credentials and installed-policy configuration load,
before OperationStore construction/reconciliation or runner admission. Close the
capture/root FD on every later startup failure. Shutdown stops static admission,
drains finite active sends under cancellation protection, then closes capture
before releasing the instance lock. No request reopens an asset pathname.

The64MiB raw member budget, two rendered variants of at most8MiB each, and2MiB
encoded manifest give an82MiB upper bound for these byte payloads; this is not a
process RSS or parser-overhead promise. The stream deadline covers response.start
and every body send. Refused small errors have a finite send deadline too. Every
UI HEAD response, including authentication errors,404 and503, sends no body while
preserving the corresponding GET status, headers and declared body length. HEAD
requires no body-stream lease. Actual send failure/disconnect/cancellation must
retire each exact lease once; saturation has no waiting queue.

Disabled web preserves existing REST Basic/bearer authentication and typed404
behavior without static reads or new UI grants. Enabled web makes the entire UI
namespace Basic-only, including assets, aliases, missing resources and errors;
REST/MCP remain independent. Authentication precedes resource disclosure. No
private cache policy applies until an indexed hashed member is selected by trusted
application state after authentication and route validation.

## Rationale, alternatives and consequences

Captured immutable bytes use bounded memory and avoid4096 retained leaf FDs or
request-time pathname races and rehashing. Mount identity protects against bind
aliases while keeping archive storage outside static initialization. Exact
navigation routes protect REST/MCP from history fallback. Independent bootstrap
and artifact schemas preserve old capabilities and receipts. Application Basic
retains REST/MCP authentication without a proxy-wide gate or another server.
A source identity computed before bundling avoids a self-referential manifest.

Enabled UI adds the explicit protected-root, Linux mount-proof and bounded-memory
requirements above. Backend-only installations remain independent. Global prefix
migration is limited to rejecting leading double slash and encoding Location;
UI-specific origin/prefix size ceilings do not change disabled-UI configuration.
There is no new production runtime dependency, Node process or frontend image.
The shipped assets remain in the existing pinned UBI10 micro API image. Actual
installed native/rootless and browser conformance is required separately from
this decision; no production availability or rollout follows from acceptance.

## Required conformance evidence

The provider-neutral runner exposes application, platform and all profiles with
one explicit protected manifest. Early feature execution requires all currently
implemented cases and reports remaining case IDs as pending. It accepts no
arbitrary caller case filter. A final mode refuses any pending or omitted case
among the95 required scenarios. The repository's `--with-web-functional` gate
always selects all profiles and final mode, requiring an explicit
`HFCACHE_WEB_FUNCTIONAL_MANIFEST` pathname; it cannot report partial coverage as
the final gate. Credentials never enter that environment variable. Missing
prerequisites or bindings fail instead of producing skipped acceptance.

Unit: strict DTO/golden, full marker placement/occurrence, MIME/path/count/bytes,
metadata/hash mismatch/TOCTOU, enabled/disabled cold startup and partial cleanup,
prefix collisions/migration/Unicode header quoting, Basic-only UI matrix,
no-history-fallback errors, exact deduplicated headers/cache and HEAD/disconnect.
Component: bounded bootstrap failure/permission/build binding and release mismatch
with no silent reload or fake domain facts. Retain strict90line/85branch gate.

Integration/functional: built artifact -> the same real Caddy trusted TLS -> the
installed API Unix upstream, one lifespan/store/runner/auth pool, three native
engines root and nonroot, deep-link refresh, missingJS404, API/MCP neverHTML,
Basic plus simultaneous appropriate REST/MCP bearers, plaintext/untrustedCA
refusal, no external requests, finite owned process/worker/listener drain. Add
provider-neutral application/platform runner with later95-case coverage explicitly
pending; no placeholder success. Native/rootless platform profile needs actual
installed behavior, not source-ASGI or existing direct-TLS browser substitution.

The selected capture design, fixed notices MIME exception and honest dirty
fixture versus clean release identity are deliberate parts of this decision.
The fixed concurrent-stream/deadline bounds require meaningful actual
backpressure/disconnect validation before conformance can be claimed. Implementation conformance requires the preceding executable evidence and
synchronized contracts; the accepted design alone establishes no conformance.

## Product acceptance method amendment (2026-11-01)

The [acceptance-method amendment to decision143](decision-143.md#product-acceptance-method-amendment-2026-11-01)
retains every required behavior while assigning its executable evidence to the
appropriate test layer. Real built-UI/Caddy/installed native and rootless browser
checks remain required, alongside actual boundary tests for stream limits,
stalled sends, disconnects, deadlines and lease release. Source review or a
downstream cancellation alone does not prove an unobserved upstream outcome.

Direct installed workflow evidence and the complete source/build gate now form
the acceptance path. Mandatory use of the normal instrumented runner and its
full scenario/profile/browser/prefix cross product is superseded. The existing
runner and final flag retain their strict protocol when explicitly selected;
this amendment neither invents a new evidence schema nor reports that optional
command as passed. A required missing clause still blocks conformance, and all
failed or uncertain observations and original operation handles are preserved.
