# Capture publication-bound inert README presentation records

- Decision identity: 142.
- Status: Accepted; writer capture implemented in unreleased source; card API and rendering pending.
- Date: 2026-10-20.

## Context and decision

Existing catalog observations retain declarations from README front matter but
no safely renderable body. Rich publication pages require an exact archived card,
without opening payloads from HTTP or treating upstream Markdown as executable.
Add independent schema-1 `RepositoryCard` records under
`published/metadata/cards/<type>/<namespace>/<name>/<sha>/<publication_id>.json`,
using plural type path grammar and existing validated identity builders.

Writer-owned joined sync/repair capture and existing `technical=true` offline
refresh may read only the exact manifest-listed root `README.md`. Limit source
to 1 MiB. Compare its bounded freshly computed SHA-256 with the manifest's
expected source digest before retaining presentation. This is a narrow metadata
source-copy check, not publication verification; it cannot change manifest,
verification catalog, confidence, publication identity or domain success.
Keep sanitized Markdown's raw UTF-8 bytes and its serialized JSON string each
within 1 MiB; whole canonical card records fit 2 MiB. Charge failed reads and
suppression/parser work to existing shared extraction and writer budgets.

The card binds archive, repository, SHA, publication ID/generation, manifest
locator/digest, source path/expected digest, presentation version/time and fixed
diagnostics. Durable states distinguish present, absent, unsupported, oversize,
unsafe and failed. Missing adjunct for an authorized exact retained publication
is read state `not_captured`. A vanished exact publication returns HTTP 404;
neither orphan adjuncts nor a repaired/current instance supply fallback identity.
Preserve old manifests, references, observations and catalogs byte-for-byte.

Card GET is an authenticated bounded metadata read from the adjunct only. It
has no source path/URL selector, payload/Hub/credential capability or refresh
side effect. Retention/reference and manifest checks authorize exact identity;
invalid/mismatched adjuncts are errors, never empty success. There is no general
payload endpoint, raw unsanitized download, HTML response or image proxy.

Sanitize recognized secrets before retaining any presentation. Parse/render
bounded inert Markdown through React components with a reviewed allowlist and
GFM. Disable raw HTML/MDX, scripts, SVG, forms, iframes, handlers, unsafe protocols,
automatic images/fonts, remote plugins, and executable code. External assets
become placeholders. Safe relative links resolve against the pinned upstream
repository/commit, never a same-origin API/UI path; external links use
`noopener noreferrer`. Prefix heading IDs against DOM clobbering. A source
toggle shows only the labelled sanitized presentation source.

## Rationale and alternatives

A separately versioned adjunct extends the established independent atomic
metadata boundary without rewriting immutable publication evidence or widening
old observation schemas. API payload reads or live Hub fetch would move writer
capabilities into read requests and detach cards from selected publication.
Raw HTML rendering and arbitrary image proxying would introduce active content
or remote request authority. Bounded source digest comparison prevents silently
copying changed README bytes under an old manifest claim without pretending to
verify the rest of the publication.

## Consequences and conformance

Refresh request/result wrappers remain unchanged; `technical=true` additionally
captures cards and existing bounded supplemental warnings expose failures.
No extra refresh endpoint is added. Source/body/serialized-record/work exhaustion,
unsupported structures, invalid UTF-8 and secret suppression yield explicit
non-success card states while preserving valid publication success. Current
curation, source-attributed declarations and integrity confidence remain separate.

At baseline `6b8fae2e0997403ae5c716a2e92148af0a972af9`, card records,
capture and card API are absent. This commit accepts their design; adversarial
capture/read/render, exact retained/noncurrent/pruned/repaired identity, byte
expansion, failure/crash and old-format compatibility evidence remains pending.

## Evidence and relationships

Amends [133](decision-133.md), [AD-12](ad-12.md), [AD-14](ad-14.md),
[AD-15](ad-15.md), [AD-17](ad-17.md) and their detailed
[discovery contract](../discovery.md#repository-card-design).
See [schema](../schemas.md#181-repositorycard-schema-1),
[API](../api.md#web-ui-and-administration-design),
[security](../security.md#browser-administration-design),
[web UI status](../web-ui/README.md). Introducing design is this commit;
implementation evidence remains pending.

## Writer capture amendment (2026-10-25)

The preceding baseline and pending statements record the design's introduction.
The independent card model, bounded no-follow source capture and atomic writer
path are implemented in unreleased source. Joined sync/repair and existing
`technical=true` refresh request card capture without adding an endpoint, flag
or field to old strict results. Observation rows and counts retain their original
meanings. Card failures use bounded `HFWRN011`; normal absent README does not
warn. Card work cannot undo publication success or change integrity confidence.

Capture checks the complete original source for registered/recognized secrets
before omissions; a match withholds the whole presentation. Leading YAML front
matter is omitted, Markdown images become fixed placeholders, and raw HTML/MDX
outside supported code is unsupported. Ordinary safe Markdown links,
relative/fragment targets and HTTP(S) URLs remain inert source for the later
pinned renderer; capture never follows them. Ambiguous/unsafe syntax refuses
rather than falling back to a looser parser. The detailed subset and independent
source, UTF-8, JSON-string, whole-record and shared-work ceilings are recorded in
the [capture guide](../web-ui/readme-cards.md) and
[discovery contract](../discovery.md#repository-card-design).

Each replacement revalidates exact retained publication/manifest/source identity
and preserves unknown or unsafe prior state under the original supplemental
writer/preflight/journal guards. It widens no old observation, manifest, reference
or public refresh schema. Source implementation alone does not establish
old-binary rollback or installed acceptance; the actual compatibility drill and
functional evidence must be recorded before acceptance. Exact card API reads
and React rendering remain separate later work, with all originally accepted
identity, no-payload and inert-rendering controls still required.
